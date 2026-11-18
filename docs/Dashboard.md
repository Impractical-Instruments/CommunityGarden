# Show Dashboard

Browser-based monitoring for The Community Garden, with controls for the TreeHouse and Playing the Pipes. Runs on the TreeHouse host alongside the `treehouse` service.

**URL:** http://192.168.1.10:9000 · **Host:** `treehouse` · **Service:** `cg-dashboard`

---

## Architecture summary

FastAPI + Uvicorn (`serve.py`). Static HTML pages per Element and a health endpoint. No login, no auth — closed show LAN only.

Per-Element pages (`flowerbeds.html`, `treehouse.html`, `fundingcaptcha.html`, `playingthepipes.html`) ping each Element's own monitoring port (visualizer or health endpoint) and reflect status.

**Which host a page asks.** The index and the FlowerBeds, TreeHouse and FundingCAPTCHA pages take only each Element's `http_port` from `network.json` and use the hostname the Dashboard itself was loaded from. Only the Pipes page uses the Element's `ip`. So with the Dashboard on the `treehouse` host, the index can reach the TreeHouse and nothing else by that route.

The Dashboard server never talks to Elements: everything is browser → Element directly. Two Elements have controls:

- **TreeHouse:** the page posts to the TreeHouse visualizer's `/control/*` routes (show mode, Looking Glass scene, Blow-Up trigger).
- **Playing the Pipes:** a virtual encoder surface posts `/enc BOARD ENC DELTA` lines to the encoder bridge's `/control/enc`, turning the knobs the way the Picos do, and draws the bridge's `/state` (knob levels and positions, loop levels, mix state). It loads **disarmed**; arm it on the page. It disarms itself when the tab is hidden or loses focus, and after 5 min without a turn. Add `?pipes=host:port` to the URL to reach a bridge other than the one in `network.json` (a laptop running `make pipes-surface`).

The other pages are status and logs only.

The log panel on the Element pages is one script, `log-panel.js` (`connectLogs(host, port)`); each page includes it and supplies the `log-panel`, `log-lines` and `log-conn` elements. The `/logs` socket it reads is served by `ShowWeb.LiveServer`.

Files in `ShowControl/Dashboard/`: `serve.py`, `index.html`, the four Element pages, `network.js` (reads `/api/network`), `log-panel.js`, `dashboard.css`.

---

## Endpoints

| Method | Path | Notes |
|---|---|---|
| `GET` | `/health` | `{"ok": true}` |
| `GET` | `/api/network` | `{"elements": {...}}` — the `elements` block of `network.json`. The pages read each Element's `http_port` from it (via `network.js`); none holds a port of its own |
| `GET` | anything else | Static files from `ShowControl/Dashboard/`; `/` is `index.html` |

---

## CLI

```bash
python serve.py           # port 9000 (default)
python serve.py 9001      # custom port
python serve.py --verbose # DEBUG logging
```

The service unit (`deploy/dashboard.service`, installed as `cg-dashboard`) runs `python3 serve.py 9000`. In a dev clone: `uv run python serve.py`.

---

## Addresses

The pages get each Element's monitoring port (and, for Pipes, its IP) from `/api/network`, which serves the `elements` block of `ShowControl/network.json` ([keys](osc-fabric.md#networkjson)). If venue addressing changes, edit that file and re-deploy.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Dashboard unreachable | `cg-dashboard` down or host network down | `sudo systemctl status cg-dashboard` on the treehouse host |
| Element shows offline though running | The page asked the Dashboard's host, not the Element's (see "Which host a page asks"), or the Element's port is unreachable from the browser | Open the Element's own monitoring URL directly (`http://<element ip>:<http_port>/health`) |
| Pipes surface turns nothing | Not armed, or the bridge is unreachable | Arm it on the page (it disarms when the tab loses focus); check the bridge's `/health` and the note beside the arm button |
| TreeHouse mode buttons do nothing | TreeHouse visualizer unreachable from the browser | The page posts to `http://<dashboard host>:8766/control/show/mode`; check the `treehouse` service is up |
