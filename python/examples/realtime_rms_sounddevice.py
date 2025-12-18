#!/usr/bin/env python3
"""
Real-time RMS Level example using sounddevice.

Captures audio from the default microphone, plays it back to the default
speaker (loopback), and prints average and peak RMS values.

Requirements:
  pip install sounddevice numpy webrtc-audio-processing
"""

import sys
import time
import threading

import numpy as np

import sounddevice as sd
import webrtc_audio_processing as webrtc_apm



SAMPLE_RATE = 32000
CHANNELS = 1
BLOCK_MS = 10
BLOCK_SIZE = SAMPLE_RATE * BLOCK_MS // 1000


class RmsMetrics:
    def __init__(self):
        self._lock = threading.Lock()
        self._avg = 0.0
        self._peak = 0.0
        self._status = None

    def update(self, avg, peak, status):
        with self._lock:
            self._avg = avg
            self._peak = peak
            if status:
                self._status = str(status)

    def snapshot(self):
        with self._lock:
            status = self._status
            self._status = None
            return self._avg, self._peak, status


def main():
    print("WebRTC RMS Level (sounddevice)")
    print(f"Sample Rate: {SAMPLE_RATE} Hz")
    print(f"Block Size: {BLOCK_SIZE} samples ({BLOCK_MS} ms)")
    print("Press Ctrl+C to stop.")

    rms = webrtc_apm.RmsLevel()
    metrics = RmsMetrics()

    def callback(indata, outdata, frames, time_info, status):
        if frames != BLOCK_SIZE:
            indata = indata[:BLOCK_SIZE]
        audio = np.ascontiguousarray(indata[:, 0], dtype=np.int16)
        rms.Analyze(audio)
        avg, peak = rms.AverageAndPeak()
        metrics.update(float(avg), float(peak), status)
        outdata[:] = indata

    with sd.Stream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=CHANNELS,
        dtype="int16",
        callback=callback,
    ):
        try:
            while True:
                time.sleep(0.5)
                avg, peak, status = metrics.snapshot()
                if status:
                    print(f"Status: {status}")
                print(f"RMS average: {avg:.1f} | RMS peak: {peak:.1f}")
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
