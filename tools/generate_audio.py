#!/usr/bin/env python3
"""
Generate placeholder WAV audio files using Python stdlib only.
No external dependencies required.

Run from the wash_game/ directory:
    python tools/generate_audio.py

Then replace the generated files with real audio later.
"""
import wave
import struct
import math
import os

SAMPLE_RATE = 44100


def write_wav(path: str, samples: list):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)          # 16-bit
        wf.setframerate(SAMPLE_RATE)
        for s in samples:
            s = max(-32768, min(32767, int(s)))
            wf.writeframes(struct.pack("<h", s))
    print(f"  created: {path}")


def sine_tone(frequency: float, duration: float, volume: float = 0.4,
              fade_out: bool = True, sweep_to: float = None) -> list:
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        freq = frequency if sweep_to is None else (
            frequency + (sweep_to - frequency) * progress
        )
        env = (1.0 - progress) ** 0.6 if fade_out else 1.0
        samples.append(32767 * volume * env * math.sin(2 * math.pi * freq * t))
    return samples


def chord(freqs: list, duration: float, volume: float = 0.35,
          fade_out: bool = True) -> list:
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        progress = i / n
        env = (1.0 - progress) ** 0.5 if fade_out else 1.0
        val = sum(math.sin(2 * math.pi * f * t) for f in freqs)
        samples.append(32767 * volume * env * val / len(freqs))
    return samples


def main():
    base = "assets/audio"
    print("Generating placeholder audio files...")

    # click.wav — short high tick
    write_wav(f"{base}/click.wav",
              sine_tone(900, 0.055, volume=0.28, fade_out=True))

    # collect.wav — ascending sweep (reward feel)
    write_wav(f"{base}/collect.wav",
              sine_tone(440, 0.38, volume=0.38, fade_out=True, sweep_to=880))

    # open_stop.wav — soft warm tone
    write_wav(f"{base}/open_stop.wav",
              chord([330, 415, 495], 0.22, volume=0.30))

    # transition.wav — brief rising ding
    write_wav(f"{base}/transition.wav",
              sine_tone(220, 0.18, volume=0.25, fade_out=True, sweep_to=440))

    print(f"\nDone. Replace these files in {base}/ with real .wav or .ogg audio later.")
    print("For pygbag/browser builds, use .ogg format (rename and re-encode with ffmpeg).")


if __name__ == "__main__":
    main()
