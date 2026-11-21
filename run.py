import ctypes
import os
import socket
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)


def setup_console():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if os.name == "nt":
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass


G = "\033[92m"
DG = "\033[32m"
C = "\033[96m"
W = "\033[97m"
Y = "\033[93m"
R = "\033[91m"
DIM = "\033[2m"
BOLD = "\033[1m"
RST = "\033[0m"


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def ensure_dependencies():
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
        import cv2  # noqa: F401
    except ImportError:
        print(f"{Y}[!] Installing packages from requirements.txt...{RST}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def hacker_boot_sequence(local_ip: str):
    os.system("cls" if os.name == "nt" else "clear")
    banner = f"""{G}{BOLD}
    +-------------------------------------------------------------------------+
    |   █████╗ ██╗    ███╗   ███╗ ██████╗ ███╗   ██╗██╗████████╗ ██████╗ ██████╗  |
    |  ██╔══██╗██║    ████╗ ████║██╔═══██╗████╗  ██║██║╚══██╔══╝██╔═══██╗██╔══██╗ |
    |  ███████║██║    ██╔████╔██║██║   ██║██╔██╗ ██║██║   ██║   ██║   ██║██████╔╝ |
    |  ██╔══██║██║    ██║╚██╔╝██║██║   ██║██║╚██╗██║██║   ██║   ██║   ██║██╔══██╗ |
    |  ██║  ██║██║    ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║██║   ██║   ╚██████╔╝██║  ██║ |
    |  ╚═╝  ╚═╝╚═╝    ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝ |
    +-------------------------------------------------------------------------+
{C}    :: NEURAL VIDEO INTERCEPT & OPTICS CONTROL :: BUILD 2026.11 // ROOT_ACCESS ::
    ==========================================================================={RST}"""
    print(banner)
    time.sleep(0.1)

    steps = [
        ("KERNEL_INIT", "FastAPI core & async router"),
        ("OPTICS_DRIVER", "OpenCV / DirectShow / FFMPEG capture"),
        ("WEBCAM_PROBE", "Laptop webcam support (local://0..3)"),
        ("NET_BINDING", f"Network interface 0.0.0.0:8000 [{local_ip}]"),
        ("SQLITE_VAULT", "Camera database storage"),
    ]

    for code, desc in steps:
        sys.stdout.write(f"  {DG}[{G}*{DG}]{RST} {C}{code:<14}{RST} {DIM}->{RST} {desc} ")
        sys.stdout.flush()
        for _ in range(3):
            time.sleep(0.05)
            sys.stdout.write(f"{G}.{RST}")
            sys.stdout.flush()
        print(f" {G}{BOLD}[OK]{RST}")

    print()
    bar_len = 40
    for i in range(bar_len + 1):
        pct = int((i / bar_len) * 100)
        filled = "#" * i
        empty = "-" * (bar_len - i)
        sys.stdout.write(f"\r  {G}SYSTEM_LOAD [{filled}{DIM}{empty}{RST}{G}] {BOLD}{pct:3d}%{RST}")
        sys.stdout.flush()
        time.sleep(0.012)
    print("\n")

    print(f"  {C}+--------------------------------------------------------------------+")
    print(f"  | {G}{BOLD}STATUS: ONLINE{RST}                                                     {C}|")
    print(f"  | {W}LOCAL URL  :{RST} {G}{BOLD}http://127.0.0.1:8000{RST}                              {C}|")
    print(f"  | {W}LAN / PHONE:{RST} {C}http://{local_ip}:8000{RST}{' ' * max(0, 31 - len(local_ip))}{C}|")
    print(f"  | {W}LAPTOP CAM :{RST} {Y}Use 'local://0' or button in web UI{RST}                  {C}|")
    print(f"  +--------------------------------------------------------------------+{RST}")
    print(f"  {DIM}[Press Ctrl+C in this window to stop the server]{RST}\n")


def open_browser():
    time.sleep(1.5)
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass


def main():
    setup_console()
    ensure_dependencies()
    import uvicorn

    ip = get_local_ip()
    hacker_boot_sequence(ip)
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False, log_level="warning")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Y}[!] Server stopped by user.{RST}")
    except Exception:
        print(f"\n{R}[CRITICAL ERROR]{RST}")
        traceback.print_exc()
        if os.name == "nt":
            os.system("pause")
