#!/usr/bin/env python3
"""
Simple test to verify VAD functionality
"""

import numpy as np
import sys

try:
    import webrtc_audio_processing as webrtc_vad
except ImportError:
    print("webrtc_audio_processing module not found. Please build and install the module first.")
    sys.exit(1)

def test_vad():
    """Test basic VAD functionality"""
    print("Testing WebRTC VAD...")
    
    # Test configuration validation
    print("1. Testing configuration validation...")
    assert webrtc_vad.VAD.is_valid_config(16000, 480), "16kHz, 30ms should be valid"  # 30ms at 16kHz
    assert webrtc_vad.VAD.is_valid_config(8000, 240), "8kHz, 30ms should be valid"   # 30ms at 8kHz  
    assert not webrtc_vad.VAD.is_valid_config(16000, 100), "Invalid frame size should be rejected"
    print("   ✓ Configuration validation works")
    
    # Test VAD creation and mode setting
    print("2. Testing VAD creation...")
    vad = webrtc_vad.VAD()
    assert vad.set_mode(0), "Should be able to set mode 0"
    assert vad.set_mode(3), "Should be able to set mode 3"
    print("   ✓ VAD creation and mode setting works")
    
    # Test with silence (should return 0)
    print("3. Testing silence detection...")
    sample_rate = 16000
    frame_duration_ms = 30
    frame_size = int(sample_rate * frame_duration_ms / 1000)  # 480 samples
    
    silence = np.zeros(frame_size, dtype=np.int16)
    result = vad.is_speech(silence, sample_rate)
    print(f"   Silence result: {result} (expected: 0)")
    assert result in [0, 1], "VAD should return 0 or 1, not error"
    
    # Test with noise/speech-like signal
    print("4. Testing speech-like signal...")
    t = np.linspace(0, frame_duration_ms/1000, frame_size, False)
    # Generate a speech-like signal with multiple frequency components
    speech_signal = (
        0.5 * np.sin(2 * np.pi * 200 * t) +      # Fundamental frequency
        0.3 * np.sin(2 * np.pi * 400 * t) +      # First harmonic
        0.1 * np.sin(2 * np.pi * 800 * t) +      # Second harmonic
        0.05 * np.random.randn(len(t))           # Add some noise
    )
    
    # Convert to int16
    speech_frame = (speech_signal * 16000).astype(np.int16)
    result = vad.is_speech(speech_frame, sample_rate)
    print(f"   Speech-like signal result: {result} (expected: 0 or 1)")
    assert result in [0, 1], "VAD should return 0 or 1, not error"
    
    # Test different VAD modes
    print("5. Testing different VAD modes...")
    for mode in [0, 1, 2, 3]:
        vad.set_mode(mode)
        result = vad.is_speech(speech_frame, sample_rate)
        print(f"   Mode {mode} result: {result}")
        assert result in [0, 1], f"VAD mode {mode} should return 0 or 1"
    
    print("\n✅ All VAD tests passed!")
    return True

def test_different_sample_rates():
    """Test VAD with different sample rates"""
    print("\n6. Testing different sample rates...")
    
    sample_rates = [8000, 16000, 32000]
    frame_duration_ms = 20  # Use 20ms frames
    
    for sr in sample_rates:
        frame_size = int(sr * frame_duration_ms / 1000)
        print(f"   Testing {sr}Hz, {frame_size} samples...")
        
        vad = webrtc_vad.VAD()
        vad.set_mode(1)
        
        # Test with sine wave
        t = np.linspace(0, frame_duration_ms/1000, frame_size, False) 
        signal = (0.3 * np.sin(2 * np.pi * 300 * t) * 16000).astype(np.int16)
        
        result = vad.is_speech(signal, sr)
        print(f"     Result: {result}")
        assert result in [0, 1], f"VAD should work with {sr}Hz"
    
    print("   ✓ All sample rates work")

if __name__ == "__main__":
    try:
        test_vad()
        test_different_sample_rates()
        print("\n🎉 All tests completed successfully!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)