import getpass
import importlib
import os
import subprocess
import sys
from urllib.parse import urlparse


def ensure_dependencies() -> None:
    """Проверяет библиотеки и при отсутствии автоматически скачивает через pip."""
    packages = {
        "wsdiscovery": "WSDiscovery",
        "onvif": "onvif-zeep",
    }
    missing = []

    for module_name, pip_name in packages.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print(f"[INFO] Устанавливаю недостающие пакеты: {', '.join(missing)}...")
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", *missing]
        subprocess.check_call(cmd)
        print("[OK] Зависимости установлены.\n")


ensure_dependencies()

from onvif import ONVIFCamera  # noqa: E402
from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery  # noqa: E402


def configure_windows_terminal() -> None:
    """Настраивает UTF-8 и поддержку ANSI-последовательностей в терминале Windows."""
    if os.name == "nt":
        os.system("")
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def copy_to_windows_clipboard(text: str) -> bool:
    """Копирует строку в буфер обмена Windows через clip."""
    if os.name != "nt":
        return False
    try:
        proc = subprocess.run(
            ["clip"],
            input=text.encode("utf-16le"),
            check=True,
        )
        return proc.returncode == 0
    except Exception:
        return False


def discover_cameras(timeout: int = 3) -> list[dict]:
    """Ищет ONVIF-камеры в локальной сети через WS-Discovery."""
    found: list[dict] = []
    wsd = WSDiscovery()
    try:
        wsd.start()
        services = wsd.searchServices(timeout=timeout)
        for service in services:
            types_str = " ".join(str(t) for t in service.getTypes())
            if "NetworkVideoTransmitter" in types_str or "onvif" in types_str.lower():
                xaddrs = service.getXAddrs()
                if not xaddrs:
                    continue
                xaddr = xaddrs[0]
                parsed = urlparse(xaddr)
                ip = parsed.hostname
                port = parsed.port or 80
                if ip and not any(cam["ip"] == ip for cam in found):
                    found.append({"ip": ip, "port": port, "xaddr": xaddr})
    finally:
        try:
            wsd.stop()
        except Exception:
            pass
    return found


def build_rtsp_with_auth(raw_uri: str, username: str, password: str) -> str:
    """Добавляет логин и пароль в RTSP URL, если они ещё не указаны."""
    if not username:
        return raw_uri
    parsed = urlparse(raw_uri)
    if parsed.username:
        return raw_uri
    host = parsed.hostname or ""
    netloc = f"{username}:{password}@{host}"
    if parsed.port:
        netloc += f":{parsed.port}"
    return parsed._replace(netloc=netloc).geturl()


def get_rtsp_url(ip: str, port: int, username: str, password: str) -> str:
    """Подключается к камере по ONVIF и запрашивает RTSP-поток первого профиля."""
    cam = ONVIFCamera(ip, port, username, password)
    media = cam.create_media_service()
    profiles = media.GetProfiles()
    if not profiles:
        raise RuntimeError("У камеры не найдено ни одного медиапрофиля.")

    profile_token = profiles[0].token
    stream_setup = {
        "Stream": "RTP-Unicast",
        "Transport": {"Protocol": "RTSP"},
    }
    uri_response = media.GetStreamUri(
        {"StreamSetup": stream_setup, "ProfileToken": profile_token}
    )
    return build_rtsp_with_auth(uri_response.Uri, username, password)


def main() -> None:
    configure_windows_terminal()
    print("=== Поиск локальных ONVIF-камер ===")
    print("Сканирую локальную сеть (3 сек)...")

    cameras = discover_cameras(timeout=3)
    if not cameras:
        print("\n[!] Камеры в локальной сети не найдены.")
        print("Проверьте, что ПК и камера в одной подсети и ONVIF включён в настройках камеры.")
        return

    print(f"\nНайдено камер: {len(cameras)}")
    for idx, cam in enumerate(cameras, start=1):
        print(f"  [{idx}] {cam['ip']}:{cam['port']}  ({cam['xaddr']})")

    choice = input("\nВведите номер камеры (или Enter для выхода): ").strip()
    if not choice:
        return

    if not choice.isdigit() or not (1 <= int(choice) <= len(cameras)):
        print("[!] Неверный номер камеры.")
        return

    selected = cameras[int(choice) - 1]
    username = input(f"Логин для {selected['ip']} [admin]: ").strip() or "admin"
    password = getpass.getpass(f"Пароль для {selected['ip']}: ")

    print("\nЗапрашиваю RTSP-ссылку у камеры...")
    try:
        rtsp_url = get_rtsp_url(selected["ip"], selected["port"], username, password)
    except Exception as exc:
        print(f"[Ошибка] Не удалось получить RTSP: {exc}")
        return

    print("\nГотово! RTSP-ссылка:")
    print(rtsp_url)

    if copy_to_windows_clipboard(rtsp_url):
        print("[OK] Ссылка скопирована в буфер обмена Windows.")


if __name__ == "__main__":
    main()