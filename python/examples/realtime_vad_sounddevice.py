#!/usr/bin/env python3
"""
Real-time Voice Activity Detector example using sounddevice.

Captures audio from the default microphone, plays it back to the default
speaker (loopback), and prints VAD probabilities and RMS values.

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


class VadMetrics:
    def __init__(self):
        self._lock = threading.Lock()
        self._last_prob = 0.0
        self._last_rms = 0.0
        self._status = None

    def update(self, prob, rms, status):
        with self._lock:
            self._last_prob = prob
            self._last_rms = rms
            if status:
                self._status = str(status)

    def snapshot(self):
        with self._lock:
            status = self._status
            self._status = None
            return self._last_prob, self._last_rms, status


def main():
    print("WebRTC Voice Activity Detector (sounddevice)")
    print(f"Sample Rate: {SAMPLE_RATE} Hz")
    print(f"Block Size: {BLOCK_SIZE} samples ({BLOCK_MS} ms)")
    print("Press Ctrl+C to stop.")

    vad = webrtc_apm.VoiceActivityDetector()
    metrics = VadMetrics()

    def callback(indata, outdata, frames, time_info, status):
        if frames != BLOCK_SIZE:
            indata = indata[:BLOCK_SIZE]
        audio = np.ascontiguousarray(indata[:, 0], dtype=np.int16)
        vad.process_chunk(audio, SAMPLE_RATE)

        probs = vad.chunkwise_voice_probabilities()
        rms_values = vad.chunkwise_rms()
        prob = float(probs[-1]) if probs else vad.last_voice_probability()
        rms = float(rms_values[-1]) if rms_values else 0.0

        metrics.update(prob, rms, status)
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
                prob, rms, status = metrics.snapshot()
                if status:
                    print(f"Status: {status}")
                print(f"Voice probability: {prob:.3f} | RMS: {rms:.1f}")
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
