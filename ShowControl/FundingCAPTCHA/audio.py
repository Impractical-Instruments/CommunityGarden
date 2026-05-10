"""
Triangle-wave note synthesiser for pygame.

Pre-generates Sound objects for each frequency at init time.
play_note(freq) is non-blocking; multiple notes can overlap.
"""
from __future__ import annotations

import numpy as np
import pygame

SAMPLE_RATE = 44100
NOTE_DUR    = 0.18   # seconds — matches original JS Web Audio timing
AMPLITUDE   = 0.30   # 0–1


def _make_note(freq: float, dur: float = NOTE_DUR) -> pygame.mixer.Sound:
    n      = int(SAMPLE_RATE * dur)
    t      = np.linspace(0, dur, n, endpoint=False)
    # Triangle wave: 2*|2*(t*f - floor(t*f + 0.5))| - 1
    phase  = t * freq
    wave   = 2.0 * np.abs(2.0 * (phase - np.floor(phase + 0.5))) - 1.0
    # Exponential decay envelope
    env    = np.exp(-5.0 * t / dur)
    signal = (wave * env * AMPLITUDE * 32767).astype(np.int16)
    stereo = np.column_stack([signal, signal])
    return pygame.sndarray.make_sound(stereo)


class Synth:
    """Pre-baked note cache. Call play(freq_or_index) anywhere."""

    def __init__(self, freqs: list[float]) -> None:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
        self._notes = {f: _make_note(f) for f in freqs}

    def play(self, freq: float) -> None:
        snd = self._notes.get(freq)
        if snd:
            snd.play()


# C D E G pentatonic — matches RhythmGame.NOTES
RHYTHM_SYNTH_FREQS = [261.6, 293.7, 329.6, 392.0]
