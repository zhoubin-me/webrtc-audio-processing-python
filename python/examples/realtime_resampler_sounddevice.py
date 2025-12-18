#!/usr/bin/env python3
"""
Real-time Resampler example using sounddevice.

Captures audio at 48 kHz, resamples down to 16 kHz and back up to 48 kHz,
then plays it to the default speaker (loopback).

Requirements:
  pip install sounddevice numpy webrtc-audio-processing
"""

import sys
import time
import threading

import numpy as np
import sounddevice as sd
import webrtc_audio_processing as webrtc_apm



INPUT_RATE = 48000
INTERMEDIATE_RATE = 16000
CHANNELS = 1
BLOCK_MS = 10
BLOCK_SIZE = INPUT_RATE * BLOCK_MS // 1000


class ResampleMetrics:
    def __init__(self):
        self._lock = threading.Lock()
        self._down = 0
        self._up = 0
        self._status = None

    def update(self, down_len, up_len, status):
        with self._lock:
            self._down = down_len
            self._up = up_len
            if status:
                self._status = str(status)

    def snapshot(self):
        with self._lock:
            status = self._status
            self._status = None
            return self._down, self._up, status


def main():
    print("WebRTC Resampler (sounddevice)")
    print(f"Input/Output Rate: {INPUT_RATE} Hz")
    print(f"Intermediate Rate: {INTERMEDIATE_RATE} Hz")
    print(f"Block Size: {BLOCK_SIZE} samples ({BLOCK_MS} ms)")
    print("Press Ctrl+C to stop.")

    down = webrtc_apm.Resampler(INPUT_RATE, INTERMEDIATE_RATE, CHANNELS)
    up = webrtc_apm.Resampler(INTERMEDIATE_RATE, INPUT_RATE, CHANNELS)
    metrics = ResampleMetrics()

    def callback(indata, outdata, frames, time_info, status):
        if frames != BLOCK_SIZE:
            indata = indata[:BLOCK_SIZE]
        audio = np.ascontiguousarray(indata[:, 0], dtype=np.int16)
        downsampled = down.process(audio)
        upsampled = up.process(downsampled)

        out_frame = upsampled
        if len(out_frame) < frames:
            out_frame = np.pad(out_frame, (0, frames - len(out_frame)))
        elif len(out_frame) > frames:
            out_frame = out_frame[:frames]

        metrics.update(len(downsampled), len(upsampled), status)
        outdata[:, 0] = out_frame

    with sd.Stream(
        samplerate=INPUT_RATE,
        blocksize=BLOCK_SIZE,
        channels=CHANNELS,
        dtype="int16",
        callback=callback,
    ):
        try:
            while True:
                time.sleep(0.5)
                down_len, up_len, status = metrics.snapshot()
                if status:
                    print(f"Status: {status}")
                print(f"Downsampled: {down_len} samples | Upsampled: {up_len} samples")
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
