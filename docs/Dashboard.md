# Show Dashboard

Browser-based monitoring + mode control for The Community Garden. Runs on the TreeHouse host alongside the `treehouse` service.

**URL:** http://192.168.1.10:9000 · **Host:** `treehouse` · **Service:** `cg-dashboard`

---

## Architecture summary

FastAPI + Uvicorn (`serve.py`). Static HTML pages per Element plus a single mode-relay endpoint. No login, no auth — closed show LAN only.

Per-Element pages (`flowerbeds.html`, `treehouse.html`, `fundingcaptcha.html`, `playingthepipes.html`) ping each Element's own monitoring port (visualizer or health endpoint) and reflect status.

`POST /api/mode` relays show mode (`active` / `dim` / `inactive`) to a specific Element over OSC, using the IP + OSC port from `ShowControl/network.json` (ADR-0007). The Dashboard never talks to Elements outside of this endpoint — everything else is browser → Element directly.

Key references:
- ADR-0007 — OSC Fabric schema (defines `network.json` schema + mode addresses)
- `serve.py`, `index.html`, per-element HTML pages

---

## Endpoints

| Method | Path | Notes |
|---|---|---|
| `GET` | `/health` | `{"ok": true}` |
| `POST` | `/api/mode` | Relays show mode over OSC. Body: `{"element": "<name>", "mode": "active|dim|inactive"}`. Sends `/<element>/mode <mode>` to the IP + OSC port from `network.json`. |
| `GET` | `/` | Static HTML — see `index.html` |
| `GET` | `/<element>.html` | Per-element status page |

Valid elements: `treehouse`, `flowerbeds`, `captcha`, `pipes`. Valid modes: `active`, `dim`, `inactive`.

---

## CLI

```bash
python serve.py           # port 9000 (default)
python serve.py 9001      # custom port
python serve.py --verbose # DEBUG logging
```

Service unit runs `python3 serve.py 9000`.

---

## `network.json`

Single source of truth for show addressing. Same file consumed by every Element via `OSCFabric/load_network_config()`.

```json
{
  "elements": {
    "treehouse":  { "ip": "192.168.1.10", "osc_port": 9001, "http_port": 8766 },
    "flowerbeds": { "ip": "192.168.1.11", "osc_port": 9002, "http_port": 8765 },
    "captcha":    { "ip": "192.168.1.12", "osc_port": 9003, "http_port": 8080 },
    "pipes":      { "ip": "192.168.1.13", "osc_port": 9004, "http_port": 8767 }
  },
  "firmware": {
    "flowerbeds_controller_1": { "ip": "192.168.1.50", "osc_port": 9000 },
    "flowerbeds_controller_2": { "ip": "192.168.1.51", "osc_port": 9000 }
  }
}
```

If venue addressing changes — edit this file (on whichever host you're deploying from) and re-deploy.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Dashboard unreachable | `cg-dashboard` down or host network down | `sudo systemctl status cg-dashboard` on the treehouse host |
| Element shows offline though running | Element's HTTP port unreachable from the browser, or wrong IP in `network.json` | Curl the element's monitoring URL directly; fix `network.json` if needed |
| `POST /api/mode` returns 503 | `network.json` missing or element entry incomplete | Check the file; ensure `ip` + `osc_port` are set for that element |
| Mode flip has no effect | Element doesn't listen for `/<element>/mode` | Check that element's OSC server; relay arrives but element ignores it |
