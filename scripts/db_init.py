#!/usr/bin/env python3
"""JSON data store helpers for AI Datacenter Investment Landscape."""
import json, os
from datetime import date, datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def data_path(name):
    return os.path.join(DATA_DIR, f"{name}.json")

def load(name, default=None):
    p = data_path(name)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}

def save(name, data):
    ensure_data_dir()
    p = data_path(name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return p

def today():
    return date.today().isoformat()

def now():
    """Current timestamp in US Eastern, e.g. '2026-05-11 14:35 ET'."""
    tz = ZoneInfo("America/New_York") if ZoneInfo else None
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M ET")

def list_data_files():
    ensure_data_dir()
    return [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]

if __name__ == "__main__":
    ensure_data_dir()
    print(f"Data directory: {DATA_DIR}")
    print(f"Files: {list_data_files()}")
