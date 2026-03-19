"""
ColdChain Tracker — FastAPI Backend
Step 1: WebSocket server + spoilage model + Twilio WhatsApp alert
Run: uvicorn main:app --reload --port 8000
"""

import asyncio
import json
import math
import random
from datetime import datetime
from typing import Dict, List, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Optional: Twilio (comment out if not using)
# from twilio.rest import Client
# TWILIO_SID = "your_account_sid"
# TWILIO_TOKEN = "your_auth_token"
# TWILIO_FROM = "whatsapp:+14155238886"  # Twilio sandbox number
# TWILIO_TO   = "whatsapp:+91XXXXXXXXXX"  # Your number

app = FastAPI(title="ColdChain Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# TRUCK DATA MODEL
# ──────────────────────────────────────────────

CARGO_SENSITIVITY = {
    "Fish":           0.8,
    "Dairy":          0.5,
    "Pharmaceuticals": 0.6,
    "Vegetables":     0.3,
    "Fruits":         0.25,
}

TRUCKS: Dict[str, dict] = {
    "TN-01": {
        "id": "TN-01", "name": "TN-01 Chennai–Vellore",
        "cargo": "Vegetables", "emoji": "🥦",
        "sla_min": 2, "sla_max": 8,
        "lat": 13.08, "lng": 80.27,
        "dest_lat": 12.91, "dest_lng": 79.13,
        "temp": 5.2, "humidity": 82,
        "spoilage": 3.0, "status": "green",
        "eta": "2h 14m", "history": [],
        "breach_alerted": False,
    },
    "TN-02": {
        "id": "TN-02", "name": "TN-02 Coimbatore–Salem",
        "cargo": "Dairy", "emoji": "🥛",
        "sla_min": 1, "sla_max": 5,
        "lat": 11.01, "lng": 77.01,
        "dest_lat": 11.66, "dest_lng": 78.15,
        "temp": 3.8, "humidity": 88,
        "spoilage": 5.0, "status": "green",
        "eta": "1h 42m", "history": [],
        "breach_alerted": False,
    },
    "TN-03": {
        "id": "TN-03", "name": "TN-03 Madurai–Trichy",
        "cargo": "Pharmaceuticals", "emoji": "💊",
        "sla_min": 2, "sla_max": 8,
        "lat": 9.93, "lng": 78.12,
        "dest_lat": 10.80, "dest_lng": 78.69,
        "temp": 9.4, "humidity": 71,
        "spoilage": 18.0, "status": "amber",
        "eta": "55m", "history": [],
        "breach_alerted": False,
    },
    "TN-04": {
        "id": "TN-04", "name": "TN-04 Tirunelveli–Nagercoil",
        "cargo": "Fish", "emoji": "🐟",
        "sla_min": -2, "sla_max": 2,
        "lat": 8.73, "lng": 77.70,
        "dest_lat": 8.17, "dest_lng": 77.43,
        "temp": 0.9, "humidity": 95,
        "spoilage": 7.0, "status": "green",
        "eta": "38m", "history": [],
        "breach_alerted": False,
    },
    "TN-05": {
        "id": "TN-05", "name": "TN-05 Chennai–Puducherry",
        "cargo": "Fruits", "emoji": "🍅",
        "sla_min": 4, "sla_max": 12,
        "lat": 12.82, "lng": 80.22,
        "dest_lat": 11.93, "dest_lng": 79.83,
        "temp": 13.1, "humidity": 76,
        "spoilage": 22.0, "status": "amber",
        "eta": "1h 10m", "history": [],
        "breach_alerted": False,
    },
    "TN-06": {
        "id": "TN-06", "name": "TN-06 Erode–Ooty",
        "cargo": "Vegetables", "emoji": "🥦",
        "sla_min": 2, "sla_max": 8,
        "lat": 11.34, "lng": 77.72,
        "dest_lat": 11.41, "dest_lng": 76.69,
        "temp": 6.7, "humidity": 79,
        "spoilage": 9.0, "status": "green",
        "eta": "2h 30m", "history": [],
        "breach_alerted": False,
    },
}

# Seed history (30 readings per truck)
for t in TRUCKS.values():
    for i in range(30):
        noise = (random.random() - 0.5) * 1.5
        t["history"].append(round(t["temp"] + noise, 1))


# ──────────────────────────────────────────────
# Q10 SPOILAGE MODEL
# ──────────────────────────────────────────────

def calculate_spoilage_delta(truck: dict) -> float:
    """
    Q10-based spoilage model.
    Spoilage rate doubles every 10°C above threshold.
    delta = sensitivity × 2^(excess/10) per tick
    """
    excess = max(0.0, truck["temp"] - truck["sla_max"])
    if excess == 0:
        return 0.0
    sensitivity = CARGO_SENSITIVITY.get(truck["cargo"], 0.3)
    q10_factor = math.pow(2, excess / 10)
    return round(sensitivity * q10_factor * 0.5, 3)  # 0.5 = tick weight


def determine_status(truck: dict) -> str:
    temp = truck["temp"]
    sla_min = truck["sla_min"]
    sla_max = truck["sla_max"]
    if temp > sla_max or temp < sla_min:
        return "red"
    elif temp > sla_max - 1.5 or temp < sla_min + 0.5:
        return "amber"
    return "green"


# ──────────────────────────────────────────────
# SENSOR SIMULATION
# ──────────────────────────────────────────────

def simulate_tick(truck: dict) -> None:
    """Advance one sensor tick with realistic temp fluctuation."""
    mid = (truck["sla_min"] + truck["sla_max"]) / 2
    noise = (random.random() - 0.5) * 0.8
    pull = (mid - truck["temp"]) * 0.05   # gentle mean-reversion
    truck["temp"] = round(truck["temp"] + noise + pull, 1)

    # Humidity slight drift
    hum_drift = (random.random() - 0.5) * 1.5
    truck["humidity"] = max(40, min(100, round(truck["humidity"] + hum_drift, 1)))

    # Update spoilage
    delta = calculate_spoilage_delta(truck)
    truck["spoilage"] = round(min(100.0, truck["spoilage"] + delta), 1)

    # Update history ring buffer (keep last 30)
    truck["history"].append(truck["temp"])
    if len(truck["history"]) > 30:
        truck["history"].pop(0)

    # Update status
    truck["status"] = determine_status(truck)


# ──────────────────────────────────────────────
# WHATSAPP ALERT (Twilio)
# ──────────────────────────────────────────────

def send_whatsapp_alert(truck: dict) -> None:
    """
    Send WhatsApp alert via Twilio when SLA is breached.
    Uncomment the Twilio imports + credentials above to enable.
    """
    msg = (
        f"🚨 *COLD CHAIN BREACH*\n\n"
        f"Truck: *{truck['id']}*\n"
        f"Cargo: {truck['emoji']} {truck['cargo']}\n"
        f"Temp: *{truck['temp']}°C* (SLA max: {truck['sla_max']}°C)\n"
        f"Spoilage Risk: *{truck['spoilage']}%*\n\n"
        f"✅ Action: Rerouted to *Koyambedu Cold Hub*\n"
        f"Distance: 12.4 km | ETA: 18 min\n\n"
        f"Please acknowledge immediately."
    )
    print(f"[ALERT] WhatsApp → {truck['id']}: {msg}")

    # Uncomment below to send real WhatsApp message:
    # client = Client(TWILIO_SID, TWILIO_TOKEN)
    # client.messages.create(body=msg, from_=TWILIO_FROM, to=TWILIO_TO)


# ──────────────────────────────────────────────
# WEBSOCKET MANAGER
# ──────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)
        print(f"[WS] Client connected. Total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)
        print(f"[WS] Client disconnected. Total: {len(self.active)}")

    async def broadcast(self, data: dict):
        msg = json.dumps(data)
        dead = set()
        for ws in self.active:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.add(ws)
        self.active -= dead


manager = ConnectionManager()


# ──────────────────────────────────────────────
# BACKGROUND SENSOR LOOP
# ──────────────────────────────────────────────

async def sensor_loop():
    """Runs every 4 seconds — simulates all trucks and broadcasts."""
    while True:
        await asyncio.sleep(4)
        for truck in TRUCKS.values():
            simulate_tick(truck)

            # Fire WhatsApp alert once per breach
            if truck["status"] == "red" and not truck["breach_alerted"]:
                truck["breach_alerted"] = True
                send_whatsapp_alert(truck)
            elif truck["status"] != "red":
                truck["breach_alerted"] = False  # reset on recovery

        payload = {
            "type": "sensor_update",
            "timestamp": datetime.now().isoformat(),
            "trucks": {k: _truck_payload(v) for k, v in TRUCKS.items()},
        }
        await manager.broadcast(payload)


def _truck_payload(t: dict) -> dict:
    """Strip internal fields before sending to frontend."""
    return {
        "id": t["id"],
        "name": t["name"],
        "cargo": t["cargo"],
        "emoji": t["emoji"],
        "sla_min": t["sla_min"],
        "sla_max": t["sla_max"],
        "lat": t["lat"],
        "lng": t["lng"],
        "dest_lat": t["dest_lat"],
        "dest_lng": t["dest_lng"],
        "temp": t["temp"],
        "humidity": t["humidity"],
        "spoilage": t["spoilage"],
        "status": t["status"],
        "eta": t["eta"],
        "history": t["history"],
    }


# ──────────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    asyncio.create_task(sensor_loop())
    print("[ColdChain] Sensor loop started ✅")


@app.get("/")
def root():
    return {"status": "ColdChain Tracker API running", "trucks": len(TRUCKS)}


@app.get("/trucks")
def get_trucks():
    """REST endpoint — returns current state of all trucks."""
    return {k: _truck_payload(v) for k, v in TRUCKS.items()}


@app.get("/trucks/{truck_id}")
def get_truck(truck_id: str):
    if truck_id not in TRUCKS:
        return {"error": "Truck not found"}
    return _truck_payload(TRUCKS[truck_id])


@app.post("/spike/{truck_id}")
def spike_temperature(truck_id: str, delta: float = 8.0):
    """
    Demo endpoint — manually spike a truck's temperature.
    POST /spike/TN-01?delta=10
    This is what the frontend 'SIMULATE BREACH' button calls.
    """
    if truck_id not in TRUCKS:
        return {"error": "Truck not found"}
    truck = TRUCKS[truck_id]
    truck["temp"] = round(truck["sla_max"] + delta, 1)
    truck["status"] = "red"
    truck["breach_alerted"] = False  # force re-alert
    return {"ok": True, "truck_id": truck_id, "temp": truck["temp"]}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    # Send initial snapshot immediately on connect
    await ws.send_text(json.dumps({
        "type": "snapshot",
        "trucks": {k: _truck_payload(v) for k, v in TRUCKS.items()},
    }))
    try:
        while True:
            # Keep connection alive, accept any client messages
            data = await ws.receive_text()
            msg = json.loads(data)
            # Handle spike command from frontend
            if msg.get("action") == "spike" and "truck_id" in msg:
                tid = msg["truck_id"]
                delta = msg.get("delta", 8.0)
                if tid in TRUCKS:
                    TRUCKS[tid]["temp"] = round(TRUCKS[tid]["sla_max"] + delta, 1)
                    TRUCKS[tid]["status"] = "red"
                    TRUCKS[tid]["breach_alerted"] = False
    except WebSocketDisconnect:
        manager.disconnect(ws)
