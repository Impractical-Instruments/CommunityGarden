# Show Dashboard

Browser-based monitoring for The Community Garden, with controls for the TreeHouse and Playing the Pipes. Runs on the TreeHouse host alongside the `treehouse` service.

**URL:** http://192.168.1.10:9000 · **Host:** `treehouse` · **Service:** `cg-dashboard`

## Code

### Architecture summary

FastAPI + Uvicorn (`serve.py`). Static HTML pages per Element and a health endpoint. No login, no auth — closed show LAN only.

Per-Element pages (`flowerbeds.html`, `treehouse.html`, `fundingcaptcha.html`, `playingthepipes.html`) ping each Element's own monitoring port (visualizer or health endpoint) and reflect status.

**Which host a page asks.** Every page gets an Element's base URL from `elementBase(id)` in `network.js`, and no page builds one itself (a test fails if a page reads its own hostname). `elementBase` picks, in order:

1. `?<id>=host:port` in the page's URL, where `<id>` is the Element's key in `network.json`: `?pipes=127.0.0.1:<port>` is what `make pipes-surface` prints.
2. If the Dashboard was opened on `localhost`, `127.0.0.1` or `[::1]`: that host with the Element's `http_port`. A development machine runs its Elements beside the Dashboard.
3. Otherwise the Element's own `ip` and `http_port`. On the Show Network the Dashboard is on the `treehouse` host and the other Elements are not.

The Dashboard server never talks to Elements: everything is browser → Element directly. Two Elements have controls:

- **TreeHouse:** the page posts to the TreeHouse visualizer's `/control/*` routes (show mode, Looking Glass scene, Blow-Up trigger).
- **Playing the Pipes:** a virtual encoder surface posts `/enc BOARD ENC DELTA` lines to the encoder bridge's `/control/enc`, turning the knobs the way the Picos do, and draws the bridge's `/state` (knob levels and positions, loop levels, mix state). It loads **disarmed**; arm it on the page. It disarms itself when the tab is hidden or loses focus, and after 5 min without a turn. Add `?pipes=host:port` to the URL to reach a bridge other than the one `elementBase` would pick (`make pipes-surface` prints such a URL).

The other pages are status and logs only.

The log panel on the Element pages is one script, `log-panel.js` (`connectLogs(host, port)`); each page includes it and supplies the `log-panel`, `log-lines` and `log-conn` elements. The `/logs` socket it reads is served by `ShowWeb.LiveServer`.

Files in `ShowControl/Dashboard/`: `serve.py`, `index.html`, the four Element pages, `network.js` (reads `/api/network`; `elementBase(id)`), `log-panel.js`, `dashboard.css`.

### Endpoints

| Method | Path | Notes |
|---|---|---|
| `GET` | `/health` | `{"ok": true}` |
| `GET` | `/api/network` | `{"elements": {...}}` — the `elements` block of `network.json`. The pages read each Element's `ip` and `http_port` from it (via `network.js`); none holds an address of its own |
| `GET` | anything else | Static files from `ShowControl/Dashboard/`; `/` is `index.html` |

### CLI

```bash
python serve.py           # port 9000 (default)
python serve.py 9001      # custom port
python serve.py --verbose # DEBUG logging
```

The service unit (`deploy/dashboard.service`, installed as `cg-dashboard`) runs `python3 serve.py 9000`.

### Addresses

The pages get each Element's IP and monitoring port from `/api/network`, which serves the `elements` block of `ShowControl/network.json` ([keys](osc-fabric.md#networkjson)). If venue addressing changes, edit that file and re-deploy.

## Operations

For whoever is running the Element at a show. A code change rarely needs it.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Dashboard unreachable | `cg-dashboard` down or host network down | `sudo systemctl status cg-dashboard` on the treehouse host |
| Element shows offline though running | The Element's `ip` or `http_port` in `network.json` is not where it is listening, or that address is unreachable from the browser. A Dashboard opened on `localhost` asks `localhost`, not the Element's IP (see "Which host a page asks") | Open the Element's own monitoring URL directly (`http://<element ip>:<http_port>/health`). If that answers, fix the Element's entry in `network.json` and re-deploy; open the Dashboard by the `treehouse` host's IP, not `localhost` |
| Pipes surface turns nothing | Not armed, or the bridge is unreachable | Arm it on the page (it disarms when the tab loses focus); check the bridge's `/health` and the note beside the arm button |
| TreeHouse mode buttons do nothing | TreeHouse visualizer unreachable from the browser | The page posts to `http://<treehouse ip>:8766/control/show/mode`; check the `treehouse` service is up |
