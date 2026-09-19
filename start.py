"""一键启动：后端 FastAPI(8000) + 前端 Vite(5173) + 自动打开浏览器。

用法：python start.py
"""
import socket
import subprocess
import sys
import time
import webbrowser
import urllib.request
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_for(url, timeout=40):
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False


def stream(proc, prefix):
    for line in iter(proc.stdout.readline, ""):
        sys.stdout.write(f"[{prefix}] {line}")
        sys.stdout.flush()


def main():
    print("=" * 55)
    print("       万能估值器一键启动")
    print("=" * 55)

    for port, name in [(8000, "后端"), (5173, "前端")]:
        if port_in_use(port):
            print(f"  x 端口 {port} 已被占用({name})，请先释放")
            return

    if not (BACKEND_DIR / "app" / "api" / "main.py").exists():
        print("  x 找不到后端代码 backend/app/api/main.py")
        return
    if not (FRONTEND_DIR / "node_modules").exists():
        print("  -> 前端依赖未安装，正在安装...")
        subprocess.run(["npm", "install"], cwd=str(FRONTEND_DIR), shell=True, check=True)

    procs = []
    try:
        print("\n  [1/3] 启动后端 FastAPI :8000")
        backend = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.api.main:app", "--port", "8000", "--host", "127.0.0.1", "--reload"],
            cwd=str(BACKEND_DIR),

            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
            encoding="utf-8", errors="replace",
        )
        procs.append(("backend", backend))
        Thread(target=stream, args=(backend, "BE"), daemon=True).start()

        print("  [2/3] 启动前端 Vite :5173")
        frontend = subprocess.Popen(
            "npm run dev",
            cwd=str(FRONTEND_DIR),
            shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
            encoding="utf-8", errors="replace",
        )
        procs.append(("frontend", frontend))
        Thread(target=stream, args=(frontend, "FE"), daemon=True).start()

        print("  [3/3] 等待服务就绪...")
        b_ok = wait_for("http://127.0.0.1:8000/api/health")
        f_ok = wait_for("http://127.0.0.1:5173")

        if not b_ok:
            print("  x 后端未就绪，请查看上方 [BE] 日志")
        if not f_ok:
            print("  x 前端未就绪，请查看上方 [FE] 日志")
        if not (b_ok and f_ok):
            print("\n  启动失败。按回车退出。")
            input()
            return

        webbrowser.open("http://127.0.0.1:5173")
        print("\n" + "=" * 55)
        print("  OK 启动成功，浏览器已打开")
        print("  前端  http://127.0.0.1:5173")
        print("  后端  http://127.0.0.1:8000")
        print("  按 Ctrl+C 退出")
        print("=" * 55 + "\n")

        while True:
            for name, p in procs:
                if p.poll() is not None:
                    print(f"\n  {name} 已退出 (code={p.returncode})")
                    return
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n  正在退出...")
    finally:
        for name, p in procs:
            if p.poll() is None:
                p.terminate()
        time.sleep(1)
        for name, p in procs:
            if p.poll() is None:
                p.kill()
        print("  已清理，再见。")


if __name__ == "__main__":
    main()
