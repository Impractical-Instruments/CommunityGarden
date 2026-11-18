# ADR 0010 — TreeHouse LED driver: two MicroPython Picos with PIO

**Status:** Superseded by [ADR-0020](0020-treehouse-esp32s3-location-controllers.md)

**Decided:** Two MicroPython Picos in the garage drove every TreeHouse LED strip as pixel sinks. The Pi computed each frame and sent it as JSON lines over USB serial at 30 fps.

**Replaced by:** ADR-0020 put one ESP32-S3 at each location; each animates itself from Garden State sent over WiFi. The Pico firmware, `pico_driver.py` and the Pi's LED classes were removed on 2026-11-11 (#192).

The full text is in git history.
