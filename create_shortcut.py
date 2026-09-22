import os
import sys
from pathlib import Path
import pythoncom
from win32com.client import Dispatch

def create_desktop_shortcut():
    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
    shortcut_path = desktop / "万能估值终端.lnk"
    target_dir = Path(__file__).resolve().parent / "dist" / "万能估值终端"
    target_exe = target_dir / "万能估值终端.exe"
    icon_path = target_dir / "_internal" / "app_icon.ico"
    if not icon_path.exists():
        icon_path = Path(__file__).resolve().parent / "app_icon.ico"

    if not target_exe.exists():
        print(f"Target exe not found: {target_exe}")
        return False

    pythoncom.CoInitialize()
    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.Targetpath = str(target_exe)
    shortcut.WorkingDirectory = str(target_dir)
    shortcut.IconLocation = str(icon_path)
    shortcut.Description = "万能估值终端 - Universal Valuation Pro"
    shortcut.save()
    print(f"Desktop shortcut created successfully at: {shortcut_path}")
    return True

if __name__ == "__main__":
    create_desktop_shortcut()
