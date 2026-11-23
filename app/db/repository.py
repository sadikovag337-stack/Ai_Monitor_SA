import uuid
from app.db.database import connect

def all_cameras():
    with connect() as db:
        return db.execute("SELECT * FROM cameras ORDER BY created_at DESC").fetchall()

def add_camera(name, url, vendor, enabled=True):
    cid = uuid.uuid4().hex[:12]
    with connect() as db:
        db.execute("INSERT INTO cameras(id,name,rtsp_url,vendor,enabled) VALUES(?,?,?,?,?)",
                   (cid, name, url, vendor, int(enabled)))
    return cid


def update_camera(cid, name, url, vendor):
    with connect() as db:
        cur = db.execute(
            "UPDATE cameras SET name=?,rtsp_url=?,vendor=?,enabled=1 WHERE id=?",
            (name, url, vendor, cid),
        )
        return cur.rowcount > 0


def remove_camera(cid):
    with connect() as db:
        cur = db.execute("DELETE FROM cameras WHERE id=?", (cid,))
        return cur.rowcount > 0
