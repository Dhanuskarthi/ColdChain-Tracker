# ColdChain-Tracker

# 🚛 ColdChain Tracker — Perishable Goods Integrity Monitor

> Real-time cold chain monitoring for last-mile delivery in India.
> Logistics · IoT · FastAPI · WebSocket · Leaflet.js

---

## 📊 The Problem

India loses **₹92,000 crore** (USD ~11 billion) worth of food annually due to broken cold chains.
Nearly **40% of all perishable produce** — vegetables, dairy, fish, fruits, and pharmaceuticals — is lost in transit.
Small distributors, vegetable mandis, and dairy co-operatives have **zero affordable real-time visibility**.

---

## 💡 Our Solution

ColdChain Tracker monitors temperature and humidity across last-mile delivery routes, predicts spoilage risk per shipment, and automatically alerts the nearest depot to reroute — **before goods go bad**.

| Feature | Description |
|---|---|
| 🗺️ Live Map Dashboard | 6 truck routes across Tamil Nadu. Color-coded markers (green / amber / red) update in real time via WebSocket |
| 📡 IoT Sensor Simulation | Realistic temp + humidity fluctuations with SLA boundary detection, running in FastAPI |
| 🧪 Spoilage Prediction | Q10 microbial growth coefficient model calculates % spoilage risk per cargo type |
| 🚨 Auto-Alert Engine | WhatsApp alert via Twilio + nearest cold depot reroute on SLA breach |

---

## 🧪 Spoilage Prediction Model

Based on the **Q10 microbial growth coefficient** — microbial growth rate doubles every 10°C above threshold.
```
Spoilage Delta = cargo_sensitivity × 2^(excess_temp / 10) × tick_weight

Where:
  excess_temp       = max(0, current_temp - sla_max)
  tick_weight       = 0.5  (per 4-second sensor tick)
  cargo_sensitivity = per-cargo multiplier (see table)
```

| Cargo | Multiplier | SLA Range | Reason |
|---|---|---|---|
| 🐟 Fish | 0.8 | -2°C to +2°C | Spoils within hours above threshold |
| 🥛 Dairy | 0.5 | +1°C to +5°C | Pasteurized but fragile to heat |
| 💊 Pharmaceuticals | 0.6 | +2°C to +8°C | Efficacy degrades fast |
| 🥦 Vegetables | 0.3 | +2°C to +8°C | Relatively tolerant |
| 🍅 Fruits | 0.25 | +4°C to +12°C | Ethylene-controlled, slower spoilage |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5 + CSS3 + Vanilla JS (no build step) |
| Map | Leaflet.js with CartoDB Dark basemap |
| Charts | Chart.js 4 — temperature line chart + analytics |
| Backend | FastAPI (Python) — REST API + WebSocket server |
| Real-time Feed | WebSocket — sensor data pushed every 4 seconds |
| Spoilage Model | Pure Python — Q10 coefficient, no ML library needed |
| Alert Engine | Twilio API — WhatsApp message on SLA breach |
| Deployment | Ngrok — instant public URL from localhost |

---

## 📁 Project Structure
```
coldchain/
├── main.py           ← FastAPI backend — WebSocket, sensor sim, spoilage model, Twilio alert
├── index.html        ← Frontend — Leaflet map, Chart.js, real-time WS client, alert feed
├── requirements.txt  ← Python dependencies
└── README.md
```

---

## 🚀 Setup & Running

### Prerequisites
- Python 3.9+
- pip
- A modern browser (Chrome / Firefox)

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Start the backend
```bash
uvicorn main:app --reload --port 8000
```

Expected output:
```
[ColdChain] Sensor loop started ✅
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3 — Open the frontend

Double-click `index.html` or drag it into Chrome.
The **WS** indicator in the header turns green when connected.

### Step 4 — Optional: Real WhatsApp alerts (Twilio)

1. Sign up at [twilio.com](https://twilio.com) (free trial)
2. Get a WhatsApp sandbox number
3. Uncomment the Twilio lines at the top of `main.py`
4. Add your `TWILIO_SID`, `TWILIO_TOKEN`, and phone number

### Step 5 — Optional: Public URL with Ngrok
```bash
ngrok http 8000
```

Then update these two lines in `index.html`:
```js
const WS_URL    = 'wss://xxxx.ngrok.io/ws';
const SPIKE_URL = 'https://xxxx.ngrok.io/spike';
```
---
![WhatsApp Image 2026-03-20 at 12 56 33 AM](https://github.com/user-attachments/assets/132201a2-172d-4637-865f-07befc2af132)
![WhatsApp Image 2026-03-20 at 12 56 35 AM](https://github.com/user-attachments/assets/2cb0bf22-f57f-42a1-8987-3d83527a1cf2)
![WhatsApp Image 2026-03-20 at 12 57 48 AM](https://github.com/user-attachments/assets/acd612bb-b2e4-456f-84bb-be9c8b793eeb)

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/trucks` | All truck states (snapshot) |
| GET | `/trucks/{id}` | Single truck details |
| POST | `/spike/{id}?delta=8` | Manually spike temperature (demo) |
| WS | `/ws` | Live sensor stream — 4s interval |

---

## 🎯 Demo Script (On Stage)

> *"India loses ₹92,000 crore annually to broken cold chains. Small distributors can't afford enterprise IoT. So we built ColdChain Tracker — watch this."*

1. Click **SIMULATE BREACH** button
2. Watch a truck turn red on the live map
3. WhatsApp alert slides in from top right
4. Reroute to Koyambedu Cold Hub triggers automatically
5. Alert feed populates with breach + reroute events

**Total time: under 30 seconds. Judges will remember this.**

---

## 🏆 competitive advantage

- **Niche problem** — most teams pick generic route optimization. We own cold chain.
- **Live demo** — color-coded trucks on a real map, understandable in 10 seconds.
- **Real business case** — applicable to mandis, dairy co-ops, and pharma across Tamil Nadu.
- **WebSocket real-time depth** — technical sophistication visible during the demo.
- **Q10 spoilage model** — grounded in food science, not a random threshold.

---
> ⚠️ Note: Sensor data is simulated. WhatsApp alerts require Twilio credentials (free trial sufficient). All coordinates are real Tamil Nadu locations.
