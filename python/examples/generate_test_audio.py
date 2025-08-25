#!/usr/bin/env python3
"""
Generate test audio files for offline processing example.

This script creates simple test audio files that can be used with the
offline_processing.py example to demonstrate the WebRTC Audio Processing
functionality.

Usage:
    python generate_test_audio.py
    
This will create:
    - play_test.raw: Far-end audio (sine wave)
    - rec_test.raw: Near-end audio (sine wave + echo simulation)
"""

import numpy as np
import struct


def generate_test_files(duration_seconds=5.0):
    """Generate test audio files."""
    sample_rate = 32000
    channels = 1
    num_samples = int(duration_seconds * sample_rate * channels)
    
    print(f"Generating {duration_seconds}s test audio files...")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Channels: {channels}")
    print(f"Samples: {num_samples}")
    
    # Time vector
    t = np.linspace(0, duration_seconds, num_samples, False)
    
    # Generate far-end audio (playback) - sine wave at 440 Hz
    play_freq = 440  # A4 note
    play_audio = 0.3 * np.sin(2 * np.pi * play_freq * t)
    
    # Add some variation to make it more realistic
    play_audio += 0.1 * np.sin(2 * np.pi * 880 * t)  # Higher harmonic
    play_audio += 0.05 * np.sin(2 * np.pi * 220 * t)  # Lower harmonic
    
    # Generate near-end audio (microphone) - different frequency + echo
    rec_freq = 660  # E5 note  
    rec_audio = 0.4 * np.sin(2 * np.pi * rec_freq * t)
    
    # Add simulated echo from far-end (delayed and attenuated)
    echo_delay_samples = int(0.05 * sample_rate)  # 50ms delay
    echo_attenuation = 0.2
    
    # Add echo to recorded audio (simulate acoustic coupling)
    if len(play_audio) > echo_delay_samples:
        for i in range(echo_delay_samples, len(rec_audio)):
            rec_audio[i] += echo_attenuation * play_audio[i - echo_delay_samples]
    
    # Add some background noise to make it more realistic
    noise_level = 0.02
    play_audio += noise_level * np.random.normal(0, 1, len(play_audio))
    rec_audio += noise_level * np.random.normal(0, 1, len(rec_audio))
    
    # Convert to 16-bit integers
    play_audio_int16 = (play_audio * 32767).astype(np.int16)
    rec_audio_int16 = (rec_audio * 32767).astype(np.int16)
    
    # Write files
    print("Writing play_test.raw...")
    with open("play_test.raw", "wb") as f:
        data = struct.pack(f'<{len(play_audio_int16)}h', *play_audio_int16)
        f.write(data)
    
    print("Writing rec_test.raw...")
    with open("rec_test.raw", "wb") as f:
        data = struct.pack(f'<{len(rec_audio_int16)}h', *rec_audio_int16)
        f.write(data)
    
    print("Test files generated successfully!")
    print("\nTo test the processing:")
    print("  python offline_processing.py play_test.raw rec_test.raw output_test.raw")
    print("\nFiles created:")
    print(f"  play_test.raw: {len(play_audio_int16) * 2} bytes")
    print(f"  rec_test.raw: {len(rec_audio_int16) * 2} bytes")


def main():
    """Main function."""
    try:
        generate_test_files()
    except Exception as e:
        print(f"Error generating test files: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())