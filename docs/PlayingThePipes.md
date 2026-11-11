# Playing the Pipes

The Element growing out of the base of the TreeHouse. Pipes and conduit with valves and switches; Visitors operate the controls to **steer** a Max music engine via **Tiller Control** (not direct note triggering).

**Host:** `pipes` · 192.168.1.13 (**Windows**) · **Health:** http://192.168.1.13:8767/health · **Services:** `pipes-health` (NSSM), Max patch (manual or scheduled)

---

## Architecture summary

Two Pi Pico microcontrollers (ADR-0014) read rotary encoders mounted on physical valves and switches. They enumerate as Windows COM ports and stream encoder deltas as text frames. The Max patch (`Lamplight2026.maxpat`) reads those ports through `serial` objects, maps the deltas to granulator + loop-player parameters, and renders audio.

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

## Max patch

`ShowControl\PlayingThePipes\Lamplight2026\patchers\Lamplight2026.maxpat`, part of the Max 9 project `Lamplight2026\Lamplight2026.maxproj`.

Audio engine. Open manually after boot, or configure Max to auto-launch on login.

It needs two things beyond stock Max:

- **The Grainflow package** (`grainflow~`, `grainflow.util.stereopan~`) — install it from Max's Package Manager.
- **Max 9's ABL device objects** (`abl.device.reverb~`, `abl.device.spectraltime~`).

If either is missing, Max prints "no such object" in its console when the patch opens and that part of the engine is silent.

`EncoderTester.maxpat` is a side patch for verifying encoder Pico connectivity without the full audio engine. `fake_encoder` objects in the show patch stand in for the encoders when no Pico is attached.

The patch is not running as a service. If audio stops, check Max is open (or auto-launched) — health endpoint can be green while Max is closed.

---

## COM port assignment

Two Picos, plugged via USB. COM numbers are unstable by default — pin them in Device Manager during [bootstrap](bootstrap.md#4-com-port-pinning).

Max does not name COM ports directly. It gives each serial port a letter, and the patch's `encoderin` object takes the two letters as its arguments: `encoderin c d` in `Lamplight2026.maxpat` opens ports `c` and `d`. To see which letter is which COM port, send the message `print` to a `serial` object; the list appears in the Max console. If the letters differ on this machine, change the two arguments of `encoderin` and save the patch.

Which Pico is on which port does not matter: every line a Pico sends carries its own board ID.

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
| Encoders feel dead in Max | Wrong port letters on `encoderin`, or Pico unplugged | List COMs; reseat USB; check the letters (see [COM port assignment](#com-port-assignment)); verify in `EncoderTester.maxpat` |
| No audio | Max not running, or a missing external | Open `Lamplight2026.maxpat`; audio output device selected; look for "no such object" in the Max console |
| One Pico works, one doesn't | COM port number changed | Check Device Manager; re-pin COMs; update the `encoderin` arguments |
| Patch silent after deploy | Patch needs manual reload | Reopen patch in Max |

---

## Open items

- `/pipes/activity` is not implemented — TreeHouse `GardenState.pipes_activity` is currently always 0. Hooking this up requires a Max → OSC bridge that summarises encoder activity each second and emits over the Fabric.
- Max patch auto-launch on login is not yet configured by default.
