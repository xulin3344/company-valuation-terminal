"""万能估值终端 - 桌面端独立启动器 (支持 PyInstaller 打包与原生窗口运行)。

特性：
1. 自动挂载前端 dist 静态构建文件与 /api 路由。
2. 动态检测空闲端口，杜绝端口冲突。
3. 后台极速拉起 Uvicorn 服务，启动 Edge App 窗口。
4. 关闭桌面窗口时自动清理后台服务与退出。
"""
import os
import sys
import time
import socket
import threading
import subprocess
from pathlib import Path

# 在打包模式下立即隐藏控制台窗口（使用 --console 构建以保证兼容性，再通过 API 隐藏）
if getattr(sys, "frozen", False) and sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

# 确定资源基准路径（适配 PyInstaller 单目录的 _internal 模式与开发源码模式）
if getattr(sys, "frozen", False):
    if hasattr(sys, "_MEIPASS"):
        BASE_DIR = Path(sys._MEIPASS)
    else:
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "_internal").exists():
            BASE_DIR = exe_dir / "_internal"
        else:
            BASE_DIR = exe_dir
    APP_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent
    APP_DIR = BASE_DIR

# 日志输出以便排查
LOG_FILE = APP_DIR / "app_runtime.log"

def log_msg(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

log_msg(f"Application starting. frozen={getattr(sys, 'frozen', False)}, BASE_DIR={BASE_DIR}, APP_DIR={APP_DIR}")

# 将 backend 加入 sys.path
backend_path = BASE_DIR / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 引入原有 FastAPI 路由
from app.api.routes import router as api_router


def find_free_port(start_port=28188):
    """获取可用本地端口"""
    for port in range(start_port, start_port + 200):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


def create_desktop_app():
    """创建融合静态页面与API的FastAPI应用"""
    app = FastAPI(title="万能估值终端", version="0.4.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册核心 API 路由
    app.include_router(api_router)

    # 注册健康检查
    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": "desktop", "version": "0.4.0"}

    # 挂载前端静态文件
    frontend_dist = BASE_DIR / "frontend" / "dist"
    if frontend_dist.exists():
        # 挂载 assets 静态资源目录
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        # SPA 页面回退
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            if full_path.startswith("api/"):
                return {"error": "Not Found"}
            file_path = frontend_dist / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(frontend_dist / "index.html"))

    return app


def run_server(app, host, port):
    """启动本地 Uvicorn 服务"""
    config = uvicorn.Config(app=app, host=host, port=port, log_level="warning", access_log=False)
    server = uvicorn.Server(config)
    server.run()


def wait_for_server(host, port, timeout=15):
    """等待服务端口就绪"""
    for _ in range(timeout * 10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.1)
    return False


def find_edge():
    """查找系统中的 Edge 浏览器路径"""
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    return next((p for p in edge_paths if os.path.exists(p)), None)


def launch_edge_app(edge_exe, url, user_data_dir):
    """启动 Edge --app 模式窗口，返回进程对象"""
    cmd = [
        edge_exe,
        f"--app={url}",
        "--window-size=1440,920",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=TranslateUI",
    ]
    log_msg(f"Edge launch cmd: {' '.join(cmd)}")

    # 使用 CREATE_NEW_PROCESS_GROUP 确保 Edge 作为独立进程组启动
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(cmd, creationflags=creation_flags)
    log_msg(f"Edge process PID: {proc.pid}")
    return proc


def monitor_edge_process(proc, user_data_dir):
    """监控 Edge 进程，Edge 关闭后返回。

    处理 Edge 的两种行为：
    A) --user-data-dir 是全新的 → Edge 以独立进程运行，proc.poll() 可以正常等待。
    B) Edge 将请求委托给已有实例 → proc 立即退出 (exit code 0)。
       此时通过检查 user_data_dir 里的 lockfile 来判断 Edge 是否仍在运行。
    """
    # 给 Edge 一点启动时间
    time.sleep(2)

    exit_code = proc.poll()
    if exit_code is None:
        # 情况 A：Edge 进程还在运行，正常等待它结束
        log_msg("Edge running as independent process, waiting for exit...")
        proc.wait()
        log_msg(f"Edge process exited with code: {proc.returncode}")
        return

    # 情况 B：Edge 立即退出了（委托给已有实例）
    log_msg(f"Edge process exited immediately (code={exit_code}). Monitoring via lockfile...")
    lock_file = Path(user_data_dir) / "lockfile"

    # 等待 lockfile 出现（最多 10 秒）
    for _ in range(100):
        if lock_file.exists():
            break
        time.sleep(0.1)

    if lock_file.exists():
        log_msg("Lockfile found, monitoring Edge session via lockfile...")
        # 当 Edge 使用这个 user-data-dir 时，lockfile 会被锁定
        # 当 Edge 窗口关闭后，lockfile 会被释放/删除
        while lock_file.exists():
            # 尝试独占打开文件，如果失败说明 Edge 仍在使用
            try:
                # 尝试重命名来检测文件是否被锁定
                # 如果文件被 Edge 锁定，rename 会失败
                test_path = lock_file.parent / "lockfile_test"
                lock_file.rename(test_path)
                # 如果成功了，说明 Edge 已经释放了锁，恢复文件名
                test_path.rename(lock_file)
                log_msg("Lockfile no longer locked, Edge session ended.")
                break
            except (PermissionError, OSError):
                # 文件被锁定，Edge 仍在运行
                pass
            time.sleep(1)
        log_msg("Edge session ended (lockfile monitoring).")
    else:
        log_msg("No lockfile found. Falling back to keep-alive loop.")
        # 最终回退：保持运行直到用户手动关闭（通过任务管理器或关机等）
        keep_alive_loop()


def keep_alive_loop():
    """保持主进程存活，直到手动终止。"""
    log_msg("Entering keep-alive loop (press Ctrl+C or close the process to exit)...")
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        log_msg("Keep-alive loop interrupted.")


def main():
    try:
        host = "127.0.0.1"
        port = find_free_port()
        log_msg(f"Initializing app on {host}:{port}...")
        app = create_desktop_app()

        # 后台线程运行后端（daemon=True 使其随主线程退出）
        server_thread = threading.Thread(target=run_server, args=(app, host, port), daemon=True)
        server_thread.start()

        # 等待服务端口就绪
        url = f"http://{host}:{port}"
        ready = wait_for_server(host, port)
        log_msg(f"Server ready state: {ready}, URL: {url}")

        if not ready:
            log_msg("ERROR: Server failed to start within timeout. Exiting.")
            return

        # 尝试启动 Edge App 窗口
        edge_exe = find_edge()

        if edge_exe:
            # 使用独立的 user-data-dir 来确保 Edge 以独立进程运行
            user_data_dir = str(APP_DIR / "edge_app_data")
            log_msg(f"Using Edge user-data-dir: {user_data_dir}")

            proc = launch_edge_app(edge_exe, url, user_data_dir)
            monitor_edge_process(proc, user_data_dir)
        else:
            # 回退到默认浏览器
            import webbrowser
            log_msg(f"Edge not found, fallback to default browser: {url}")
            webbrowser.open(url)
            keep_alive_loop()

        log_msg("Application shutting down.")

    except Exception as fatal:
        import traceback
        log_msg(f"FATAL ERROR in main: {fatal}\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
