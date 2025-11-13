from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import PlainTextResponse, HTMLResponse, FileResponse, Response, JSONResponse
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

# ---------- DATABASE INIT ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

# ---------- STATIC SERVE ----------
app.mount("/uploads", StaticFiles(directory=BASE_DIR), name="uploads")

# ---------- HELPERS ----------
def make_dirs_for_today() -> str:
    """Create subfolders: uploads/YYYY-MM/DD and return that day's path."""
    now = datetime.now()
    month_folder = os.path.join(BASE_DIR, now.strftime("%Y-%m"))
    day_folder = os.path.join(month_folder, now.strftime("%d"))
    os.makedirs(day_folder, exist_ok=True)
    return day_folder

def build_filename() -> str:
    """Return a readable filename like 2025-11-05_22-47-12.jpg"""
    return datetime.now().strftime("%Y-%m-%d_%H:%M.jpg")

# ---------- UPLOAD ----------
@app.post("/upload", response_class=PlainTextResponse)
async def upload(file: UploadFile = File(None), request: Request = None):
    # Get current target directory and file name
    save_dir = make_dirs_for_today()
    filename = build_filename()
    path = os.path.join(save_dir, filename)

    # Read data
    data = await (file.read() if file else request.body())
    if not data:
        return PlainTextResponse("No data", status_code=400)

    # Save to disk
    with open(path, "wb") as f:
        f.write(data)

    size_bytes = len(data)
    timestamp = int(time.time())
    print(f"[+] Saved: {path} ({size_bytes} bytes)")

    # Save metadata to database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO captures (filename, timestamp, path, size_bytes) VALUES (?, ?, ?, ?)",
        (filename, timestamp, path, size_bytes)
    )
    conn.commit()
    conn.close()

    return "OK"

# ---------- PING ----------
@app.post("/ping")
async def ping():
    print("ESP32 reached server")
    return {"status": "ok"}

# ---------- LIST IMAGES ----------
@app.get("/images")
def list_images():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, filename, timestamp, path, size_bytes, analysis_status FROM captures ORDER BY timestamp DESC LIMIT 50")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.get("/get_last_image")
def get_latest_image():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT path FROM captures ORDER BY timestamp DESC LIMIT 1
              """)
    row = c.fetchone()
    conn.close()

    if not row:
        return "ERROR no db answer"
    
    path = row["path"]
    ans = f"https://192.168.2.109:445/{path}"
    return JSONResponse(content={"url": ans})

@app.get("/get_last_image/{offset}")
def get_latest_image(offset: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT path FROM captures ORDER BY timestamp DESC LIMIT 1 OFFSET ?
              """,(offset,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "ERROR no db answer"
    
    path = row["path"]
    ans = f"https://192.168.2.109:445/{path}"
    return JSONResponse(content={"url": ans})
    
@app.get("/get_latest", response_class=HTMLResponse)
def get_latest():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT filename, path, timestamp
        FROM captures
        ORDER BY timestamp DESC LIMIT 1
    """)
    row = c.fetchone()
    conn.close()

    if not row:
        return "<h3>No images yet</h3>"

    filename = row["filename"]
    full_path = row["path"]
    url_path = "/" + full_path  # path usable in browser
    timestamp = datetime.fromtimestamp(row["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <html>
    <head>
        <title>Latest Image</title>
        <meta http-equiv="refresh" content="60"> <!-- auto-refresh every 60s -->
        <style>
            body {{
                background: #111;
                color: #ddd;
                text-align: center;
                font-family: sans-serif;
            }}
            img {{
                max-width: 90%;
                height: auto;
                margin-top: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(255,255,255,0.2);
            }}
        </style>
    </head>
    <body>
        <h2>Latest capture</h2>
        <p>{timestamp}</p>
        <img src="{url_path}" alt="{filename}">
    </body>
    </html>
    """
    return HTMLResponse(content=html)