import os
import threading
import time
import cv2
from app.core.config import MAX_WIDTH, JPEG_QUALITY


def parse_source(url: str):
    """Преобразует local://0 или '0' в целочисленный индекс веб-камеры, иначе возвращает URL."""
    clean = url.strip()
    if clean.lower().startswith("local://"):
        idx_str = clean[8:].strip()
        if idx_str.isdigit():
            return int(idx_str), True
    if clean.isdigit():
        return int(clean), True
    return clean, False


class RTSPStream:
    def __init__(self, cid, url):
        self.id, self.url = cid, url
        self.frame, self.online, self.error = None, False, "Инициализация потока..."
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._read, daemon=True)

    def start(self):
        self.thread.start()

    def _open_capture(self):
        source, is_local = parse_source(self.url)
        if is_local:
            # На Windows CAP_DSHOW открывает веб-камеру ноутбука намного быстрее и стабильнее
            if os.name == "nt":
                cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    cap.release()
                    cap = cv2.VideoCapture(source)
            else:
                cap = cv2.VideoCapture(source)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            return cap, True
        else:
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return cap, False

    def _read(self):
        cap = None
        is_local = False
        while not self.stop_event.is_set():
            try:
                if cap is None or not cap.isOpened():
                    if cap:
                        cap.release()
                    cap, is_local = self._open_capture()
                    if not cap.isOpened():
                        msg = "Веб-камера не найдена или занята" if is_local else "Не удалось подключиться к RTSP"
                        with self.lock:
                            self.online, self.error = False, msg
                        time.sleep(2)
                        cap.release()
                        cap = None
                        continue

                ok, frame = cap.read()
                if ok and frame is not None:
                    h, w = frame.shape[:2]
                    if w > MAX_WIDTH:
                        frame = cv2.resize(frame, (MAX_WIDTH, int(h * MAX_WIDTH / w)))
                    with self.lock:
                        self.frame, self.online, self.error = frame, True, ""
                    if is_local:
                        time.sleep(0.02)  # ~30-50 FPS без перегрузки CPU
                else:
                    msg = "Нет кадра с веб-камеры" if is_local else "Нет видеопотока"
                    with self.lock:
                        self.online, self.error = False, msg
                    time.sleep(1.5)
                    if cap:
                        cap.release()
                    cap = None
            except Exception as exc:
                with self.lock:
                    self.online, self.error = False, str(exc)[:160]
                time.sleep(2.5)
                if cap:
                    cap.release()
                cap = None
        if cap:
            cap.release()

    def jpeg(self):
        with self.lock:
            if self.frame is None:
                return None
            ok, buf = cv2.imencode(".jpg", self.frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
            return buf.tobytes() if ok else None

    def status(self):
        with self.lock:
            return {"online": self.online, "error": self.error}

    def stop(self):
        self.stop_event.set()
