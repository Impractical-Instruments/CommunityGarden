# Playing the Pipes

The Element growing out of the base of the TreeHouse. Pipes and conduit with valves and switches; Visitors operate the controls to **steer** a Max/RNBO music engine via **Tiller Control** (not direct note triggering).

**Host:** `pipes` · 192.168.1.13 (**Windows**) · **Health:** http://192.168.1.13:8767/health · **Services:** `pipes-health` (NSSM), Max patch (manual or scheduled)

---

## Architecture summary

Two Pi Pico microcontrollers (ADR-0014) read rotary encoders mounted on physical valves and switches. They enumerate as Windows COM ports and stream encoder deltas as text frames. The Max/RNBO patch (`PlayingThePipes.maxpat`) reads those COMs through `serial` objects, maps the deltas to granulator + loop-player parameters, and renders audio.

A separate Python health server (`health_server.py`) runs under NSSM and serves `GET /health` on port 8767 so the Dashboard can confirm the host is up. The Pipes element does not (yet) join the OSC Fabric — `/pipes/activity` is planned but not wired.

Key references:
- ADR-0014 — Playing the Pipes encoder Picos
- `health_server.py` (FastAPI + uvicorn, ~50 lines)
- `Firmware/PlayingThePipes_EncoderPico/` — Pico-side firmware

---

## Health server (`health_server.py`)

```powershell
python health_server.py           # port 8767
python health_server.py 8768      # custom
```

Just `GET /health → {"ok": true}`. Run under NSSM (see [bootstrap.md → Install NSSM](bootstrap.md#5-install-nssm--register-health-server-service)).

Service management:

```powershell
nssm status pipes-health
nssm restart pipes-health
Get-Content C:\logs\pipes-health.log -Tail 50
```

---

## Max/RNBO patch

`ShowControl\PlayingThePipes\PlayingThePipes.maxpat`.

Audio engine. Open manually after boot, or configure Max to auto-launch on login.

`EncoderTester.maxpat` is a side patch for verifying encoder Pico connectivity without the full audio engine.

The patch is not running as a service. If audio stops, check Max is open (or auto-launched) — health endpoint can be green while Max is closed.

---

## COM port assignment

Two Picos, plugged via USB. Numbers are unstable by default — pinned in Device Manager during [bootstrap](bootstrap.md#4-com-port-pinning). Record the assigned COM here once known:

| Pico | Board ID | COM port |
|------|----------|----------|
| Board 0 | 0 | TBD |
| Board 1 | 1 | TBD |

The patch's `serial` objects reference these COM names directly. Edit the patch if the numbers change.

List active COM ports:

```powershell
[System.IO.Ports.SerialPort]::GetPortNames()
# or Device Manager → Ports (COM & LPT)
```

---

## Deploying code updates

`deploy.sh` doesn't handle Pipes. Python changes are rare:

```bash
# From laptop:
git push --force-with-lease pipes:CommunityGarden $(git branch --show-current):$(git branch --show-current)
ssh pipes "cd C:/CommunityGarden && git checkout <branch> && nssm restart pipes-health"
```

Max patch reload — manual; the patch is owned by Max, not by Python.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Dashboard shows Pipes offline | `pipes-health` not running | `nssm status pipes-health` / `nssm restart pipes-health` |
| Encoders feel dead in Max | Wrong COM in `serial` object, or Pico unplugged | List COMs; reseat USB; verify in `EncoderTester.maxpat` |
| No audio | Max not running | Open `PlayingThePipes.maxpat`; audio output device selected |
| One Pico works, one doesn't | COM port number changed | Check Device Manager; re-pin COMs; update patch |
| Patch silent after deploy | Patch needs manual reload | Reopen patch in Max |

---

## Open items

- `/pipes/activity` is not implemented — TreeHouse `GardenState.pipes_activity` is currently always 0. Hooking this up requires a Max → OSC bridge that summarises encoder activity each second and emits over the Fabric.
- Max patch auto-launch on login is not yet configured by default.
