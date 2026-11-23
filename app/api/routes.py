import os
import time
import cv2
from urllib.parse import urlsplit
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.db.repository import add_camera, all_cameras, remove_camera, update_camera
from app.services.onvif_discovery import discover_onvif_cameras
from app.services.stream_manager import manager

router = APIRouter()


class CameraInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    rtsp_url: str = Field(min_length=1, max_length=1500)
    vendor: str = "generic"


def is_valid_source(url: str) -> bool:
    u = url.strip().lower()
    if u.isdigit():
        return True
    if u.startswith("local://") and u[8:].strip().isdigit():
        return True
    return u.startswith(("rtsp://", "rtsps://", "http://", "https://"))


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/local-cameras")
def detect_local_cameras():
    """Сканирует индексы 0..3 на наличие локальных веб-камер ноутбука."""
    found = []
    # Проверяем уже активные локальные потоки, чтобы не конфликтовать за устройство
    active_local = {}
    for st in manager.statuses():
        pass
    with manager.lock:
        for cid, stream in manager.streams.items():
            u = stream.url.strip().lower()
            if u.startswith("local://") and u[8:].isdigit():
                active_local[int(u[8:])] = True
            elif u.isdigit():
                active_local[int(u)] = True

    for idx in range(4):
        if idx in active_local:
            found.append({"index": idx, "url": f"local://{idx}", "label": f"Камера ноутбука #{idx} (активна)"})
            continue
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW) if os.name == "nt" else cv2.VideoCapture(idx)
        if cap is not None and cap.isOpened():
            ok, _ = cap.read()
            if ok:
                label = "Встроенная камера ноутбука (0)" if idx == 0 else f"USB / Внешняя камера ({idx})"
                found.append({"index": idx, "url": f"local://{idx}", "label": label})
            cap.release()
    return {"cameras": found}


@router.post("/network-cameras")
def detect_network_cameras():
    try:
        found = discover_onvif_cameras()
    except OSError as exc:
        raise HTTPException(503, f"Не удалось выполнить поиск в локальной сети: {exc}") from exc

    existing_by_host = {}
    for row in all_cameras():
        try:
            host = urlsplit(row["rtsp_url"]).hostname
        except ValueError:
            host = None
        if host:
            existing_by_host.setdefault(host.lower(), row)

    results = []
    added = 0
    for camera in found:
        ip = camera["ip"]
        existing = existing_by_host.get(ip.lower())
        if existing:
            results.append({
                "id": existing["id"],
                "ip": ip,
                "name": existing["name"],
                "added": False,
            })
            continue

        name = (camera.get("name") or "ONVIF-камера")[:80]
        cid = add_camera(name, f"rtsp://{ip}:554/", "onvif", enabled=False)
        row = {"id": cid, "name": name}
        existing_by_host[ip.lower()] = row
        results.append({"id": cid, "ip": ip, "name": name, "added": True})
        added += 1

    if added:
        manager.sync()
    return {"cameras": results, "added": added}


@router.get("/cameras")
def cameras():
    return manager.statuses()


@router.post("/cameras")
def create_camera(item: CameraInput):
    url = item.rtsp_url.strip()
    if not is_valid_source(url):
        raise HTTPException(400, "Нужен RTSP URL (rtsp://...) или локальная камера (local://0)")
    cid = add_camera(item.name.strip(), url, item.vendor)
    manager.sync()
    return {"ok": True, "id": cid}


@router.put("/cameras/{cid}")
def edit_camera(cid: str, item: CameraInput):
    url = item.rtsp_url.strip()
    if not is_valid_source(url):
        raise HTTPException(400, "Нужен RTSP URL (rtsp://...) или локальная камера (local://0)")
    if not update_camera(cid, item.name.strip(), url, item.vendor):
        raise HTTPException(404, "Камера не найдена")
    manager.sync()
    return {"ok": True}


@router.delete("/cameras/{cid}")
def delete_camera(cid: str):
    if not remove_camera(cid):
        raise HTTPException(404, "Камера не найдена")
    manager.sync()
    return {"ok": True}


@router.get("/video/{cid}")
def video(cid: str):
    stream = manager.get(cid)
    if not stream:
        raise HTTPException(404, "Поток не найден")

    def frames():
        while not stream.stop_event.is_set():
            jpg = stream.jpeg()
            if jpg:
                yield (
                    b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                    + str(len(jpg)).encode()
                    + b"\r\n\r\n"
                    + jpg
                    + b"\r\n"
                )
            time.sleep(0.05)

    return StreamingResponse(frames(), media_type="multipart/x-mixed-replace; boundary=frame")
