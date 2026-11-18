# Show Dashboard

Browser-based monitoring + mode control for The Community Garden. Runs on the TreeHouse host alongside the `treehouse` service.

**URL:** http://192.168.1.10:9000 · **Host:** `treehouse` · **Service:** `cg-dashboard`

---

## Architecture summary

FastAPI + Uvicorn (`serve.py`). Static HTML pages per Element and a health endpoint. No login, no auth — closed show LAN only.

Per-Element pages (`flowerbeds.html`, `treehouse.html`, `fundingcaptcha.html`, `playingthepipes.html`) ping each Element's own monitoring port (visualizer or health endpoint) and reflect status.

The Dashboard server never talks to Elements: everything is browser → Element directly. Two Elements have controls:

- **TreeHouse:** the page posts to the TreeHouse visualizer's `/control/*` routes (show mode, Looking Glass scene, Blow-Up trigger).
- **Playing the Pipes:** a virtual encoder surface posts `/enc BOARD ENC DELTA` lines to the encoder bridge's `/control/enc`, turning the knobs the way the Picos do, and draws the bridge's `/state` (knob levels and positions, loop levels, mix state). It loads **disarmed**; arm it on the page. It disarms itself when the tab is hidden or loses focus, and after 5 min without a turn. Add `?pipes=host:port` to the URL to reach a bridge other than the one in `network.json` (a laptop running `make pipes-surface`).

The other pages are status and logs only.

The log panel on the Element pages is one script, `log-panel.js` (`connectLogs(host, port)`); each page includes it and supplies the `log-panel`, `log-lines` and `log-conn` elements. The `/logs` socket it reads is served by `ShowWeb.LiveServer`.

Key references:
- ADR-0007 — OSC Fabric schema (mode control is TreeHouse-only); the addresses and `network.json` keys are in [`osc-fabric.md`](osc-fabric.md)
- `serve.py`, `index.html`, per-element HTML pages

---

## Endpoints

| Method | Path | Notes |
|---|---|---|
| `GET` | `/health` | `{"ok": true}` |
| `GET` | `/api/network` | `{"elements": {...}}` — the `elements` block of `network.json`. The pages read each Element's `http_port` from it (via `network.js`); none holds a port of its own |
| `GET` | `/` | Static HTML — see `index.html` |
| `GET` | `/<element>.html` | Per-element status page |

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

Single source of truth for show addressing. Same file consumed by every Element via `OSCFabric.load_network_config()`, and by the Dashboard pages via `/api/network`.

Its keys are listed in [`osc-fabric.md`](osc-fabric.md#networkjson).

If venue addressing changes — edit this file (on whichever host you're deploying from) and re-deploy.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Dashboard unreachable | `cg-dashboard` down or host network down | `sudo systemctl status cg-dashboard` on the treehouse host |
| Element shows offline though running | Element's HTTP port unreachable from the browser, or wrong IP in `network.json` | Curl the element's monitoring URL directly; fix `network.json` if needed |
| Pipes surface turns nothing | Not armed, or the bridge is unreachable | Arm it on the page (it disarms when the tab loses focus); check the bridge's `/health` and the note beside the arm button |
| TreeHouse mode buttons do nothing | TreeHouse visualizer unreachable from the browser | The page posts to `http://<dashboard host>:8766/control/show/mode`; check the `treehouse` service is up |
