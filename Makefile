.PHONY: test test-fast test-fundingcaptcha test-firmware build-firmware

CONTROLLERS := Firmware/TreeHouse_Controllers

# Everything. pytest exits 5 when it collects no tests; that is not a failure.
test:
	python3 -m pytest || test $$? -eq 5

# Everything except FundingCAPTCHA. Seconds; needs no OpenGL.
test-fast:
	python3 -m pytest --ignore=ShowControl/FundingCAPTCHA || test $$? -eq 5

# FundingCAPTCHA only. The shader tests need a headless OpenGL context and
# take minutes on software Mesa; without one they skip (locally) or fail (CI).
# Lists the 25 slowest, so a slow new test shows up (#203).
test-fundingcaptcha:
	python3 -m pytest ShowControl/FundingCAPTCHA --durations=25 || test $$? -eq 5

# TreeHouse controller host tests (Unity, on this machine). Needs PlatformIO:
# pip install platformio. Not part of `make test`.
test-firmware:
	cd $(CONTROLLERS) && pio test -e native

# Compile one environment of each kind: signs of life, a location, and its
# self-test. A location build needs include/secrets.h. If there is none, the
# example stands in for the compile and is removed afterwards, so it can never
# be flashed by mistake.
build-firmware:
	cd $(CONTROLLERS) && { \
	    if [ ! -f include/secrets.h ]; then \
	        cp include/secrets.h.example include/secrets.h; \
	        trap 'rm -f include/secrets.h' EXIT; \
	    fi; \
	    pio run -e signsoflife-uart -e signsoflife-usb -e swannatopia -e swannatopia-selftest; \
	}
