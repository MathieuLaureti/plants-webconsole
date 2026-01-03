from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import time
from datetime import datetime

BASE_DIR = "uploads"
DB_PATH = "database.db"

os.makedirs(BASE_DIR, exist_ok=True)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            path TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            analysis_status TEXT DEFAULT 'pending',
            result_json TEXT
        );
    """)
    conn.commit()
    conn.close()

init_db()

app.mount("/uploads", StaticFiles(directory=BASE_DIR), name="uploads")

def make_dirs_for_today(camera_id) -> str:
    """Create subfolders: uploads/{camera_id}/YYYY-MM/DD and return that day's path."""
    now = datetime.now()
    camera_folder = os.path.join(BASE_DIR, str(camera_id))
    month_folder = os.path.join(camera_folder, now.strftime("%Y-%m"))
    day_folder = os.path.join(month_folder, now.strftime("%d"))
    os.makedirs(day_folder, exist_ok=True)
    return day_folder

def build_filename() -> str:
    """Return a readable filename like 2025-11-05_22-47-12.jpg"""
    return f"{datetime.now().strftime('%Y-%m-%d_%H:%M')}.jpg"

@app.post("/upload/{camera_id}", response_class=PlainTextResponse)
async def upload(camera_id: int, file: UploadFile = File(None), request: Request = None):
    save_dir = make_dirs_for_today(camera_id)
    filename = build_filename()
    path = os.path.join(save_dir, filename)

    data = await (file.read() if file else request.body())
    if not data:
        return PlainTextResponse("No data", status_code=400)
    
    with open(path, "wb") as f:
        f.write(data)

    size_bytes = len(data)
    timestamp = int(time.time())
    print(f"[+] Saved: {path} ({size_bytes} bytes)")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO captures (filename, timestamp, path, size_bytes, camera_id) VALUES (?, ?, ?, ?, ?)",
        (filename, timestamp, path, size_bytes, camera_id)
    )
    conn.commit()
    conn.close()

    return "OK"

@app.get("/ping")
async def ping():
    print("ESP32 reached server")
    return {"status": "ok"}

@app.get("/get_last_image/{offset}/{camera_id}")
def get_latest_image(camera_id: int,offset: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT path,timestamp FROM captures WHERE camera_id = ? ORDER BY timestamp DESC LIMIT 1 OFFSET ?
              """,(camera_id,offset))
    row = c.fetchone()
    conn.close()
    print("test")
    if not row:
        return "ERROR no db answer"
    
    path = row["path"]
    
    dt_object = datetime.fromtimestamp(row["timestamp"])
    timestamp = dt_object.strftime("%Y-%m-%d %H:%M:%S")
    ans = f"https://homelabdu204.ca/plants/api/{path}"
    print(ans)
    return JSONResponse(content={
        "url": ans,
        "timestamp": timestamp
        })

@app.get("/slideshow/{mode}/{camera_id}")
def slideshow(mode: str):
    if mode not in ["day", "week", "month"]:
        return JSONResponse(content={"error": "Invalid mode"}, status_code=400)
    
    if mode == "day":
        limit = 28
    elif mode == "week":    
        limit = 196
    elif mode == "month":
        limit = 5880
    
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT path,timestamp FROM captures ORDER BY timestamp ASC LIMIT ?
                """,(limit,))
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return "ERROR no db answer"
    
    data = []
    for i in rows:
        path = i["path"]
    
        dt_object = datetime.fromtimestamp(i["timestamp"])
        timestamp = dt_object.strftime("%Y-%m-%d %H:%M:%S")
        
        data.append({"url": f"https://192.168.2.109:445/{path}", "timestamp": timestamp})
    
    print(rows)
    return JSONResponse(content={
        "images": data
        })
     
@app.get("/get_TH/")
def get_th():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT temperature,humidity,battery,timestamp FROM sensor_data ORDER BY timestamp DESC LIMIT 1
              """)
    row = c.fetchone()
    conn.close()

    if not row:
        return "ERROR no db answer"
    
    return JSONResponse(content={
        "temperature": row["temperature"],
        "humidity": row["humidity"],
        "battery": row["battery"],
        "timestamp": row["timestamp"]
        })

@app.get("/get_THs")
def get_THs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT temperature,humidity,battery,timestamp FROM sensor_data ORDER BY timestamp DESC
              """)
    rows = c.fetchall()
    conn.close()    
    return rows