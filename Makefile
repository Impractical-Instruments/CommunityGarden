.PHONY: setup test test-fast test-fundingcaptcha test-firmware build-firmware uv cargo reuben validate-instruments

CONTROLLERS := Firmware/TreeHouse_Controllers

# Every Python command runs through uv, from uv.lock: the same Python and packages on
# every machine, in .venv, created or updated on first use. Run anything else the same
# way, from inside the Element: `cd ShowControl/FlowerBeds && uv run python main.py ...`.
RUN := uv run
# PlatformIO, the version CI uses, run by uv without installing it anywhere.
PIO := uvx --from platformio==6.2.0 pio

# reuben, the audio engine Playing the Pipes runs on: a submodule, built from source
# (#177). vendor/reuben/rust-toolchain.toml pins the Rust version; rustup installs it.
REUBEN_DIR := vendor/reuben
REUBEN := $(REUBEN_DIR)/target/release/reuben
# Instruments CI validates. A device profile beside them (*.profile.json) is not one.
REUBEN_INSTRUMENTS := $(filter-out %.profile.json,$(wildcard ShowControl/PlayingThePipes/reuben/*.json))

uv:
	@command -v uv >/dev/null 2>&1 || { \
	    echo "This repo runs Python through uv, which is not installed. Install it with:"; \
	    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
	    echo "then open a new terminal and run make again."; \
	    exit 1; }

cargo:
	@command -v cargo >/dev/null 2>&1 || { \
	    echo "Building reuben needs Rust, which is not installed. Install it with:"; \
	    echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"; \
	    echo "and on Linux the ALSA headers: sudo apt-get install libasound2-dev"; \
	    echo "then open a new terminal and run make again."; \
	    exit 1; }

# First time in a new clone: the reuben submodule, the Python environment, and the
# pre-commit hook that guards ShowControl/FundingCAPTCHA/images/private/.
setup: uv
	git submodule update --init --recursive
	uv sync
	bash scripts/install-git-hooks.sh

# Everything. pytest exits 5 when it collects no tests; that is not a failure.
test: uv
	$(RUN) pytest || test $$? -eq 5

# Everything except FundingCAPTCHA. Seconds; needs no OpenGL.
test-fast: uv
	$(RUN) pytest --ignore=ShowControl/FundingCAPTCHA || test $$? -eq 5

# FundingCAPTCHA only. The shader tests need a headless OpenGL context and
# take minutes on software Mesa; without one they skip (locally) or fail (CI).
# Lists the 25 slowest, so a slow new test shows up (#203).
test-fundingcaptcha: uv
	$(RUN) pytest ShowControl/FundingCAPTCHA --durations=25 || test $$? -eq 5

# TreeHouse controller host tests (Unity, on this machine). Not part of `make test`.
test-firmware: uv
	cd $(CONTROLLERS) && $(PIO) test -e native

# Compile one environment of each kind: signs of life, a location, and its
# self-test. A location build needs include/secrets.h. If there is none, the
# example stands in for the compile and is removed afterwards, so it can never
# be flashed by mistake.
build-firmware: uv
	cd $(CONTROLLERS) && { \
	    if [ ! -f include/secrets.h ]; then \
	        cp include/secrets.h.example include/secrets.h; \
	        trap 'rm -f include/secrets.h' EXIT; \
	    fi; \
	    $(PIO) run -e signsoflife-uart -e signsoflife-usb -e swannatopia -e swannatopia-selftest; \
	}

# The reuben CLI, from the vendor/reuben submodule. Edit reuben there and rebuild.
reuben: cargo
	@test -f $(REUBEN_DIR)/Cargo.toml || { \
	    echo "vendor/reuben is empty. Run: git submodule update --init --recursive"; exit 1; }
	cd $(REUBEN_DIR) && cargo build --release -p reuben-native --bin reuben

# Load-check every Playing the Pipes instrument against the pinned reuben. A
# warning (such as a missing sample) fails too.
validate-instruments: reuben
	@bash scripts/validate-instruments.sh $(REUBEN) $(REUBEN_INSTRUMENTS)
