from threading import RLock
from urllib.parse import urlsplit
from app.db.repository import all_cameras
from app.services.rtsp_stream import RTSPStream

class StreamManager:
    def __init__(self):
        self.streams = {}
        self.lock = RLock()

    def sync(self):
        rows = all_cameras()
        with self.lock:
            active = {r["id"]: r for r in rows if r["enabled"]}
            for cid in list(self.streams):
                if cid not in active:
                    self.streams[cid].stop()
                    del self.streams[cid]
                elif self.streams[cid].url != active[cid]["rtsp_url"]:
                    self.streams[cid].stop()
                    del self.streams[cid]
            for cid, row in active.items():
                if cid not in self.streams:
                    stream = RTSPStream(cid, row["rtsp_url"])
                    self.streams[cid] = stream
                    stream.start()

    def get(self, cid):
        self.sync()
        with self.lock: return self.streams.get(cid)

    def statuses(self):
        self.sync()
        result = []
        with self.lock:
            for row in all_cameras():
                s = self.streams.get(row["id"])
                state = s.status() if s else {"online": False, "error": "Отключена"}
                try:
                    host = urlsplit(row["rtsp_url"]).hostname
                except ValueError:
                    host = None
                result.append({"id": row["id"], "name": row["name"],
                    "vendor": row["vendor"], "enabled": bool(row["enabled"]),
                    "host": host if row["vendor"] == "onvif" else None, **state})
        return result

    def stop_all(self):
        with self.lock:
            for s in self.streams.values(): s.stop()
            self.streams.clear()

manager = StreamManager()
