#!/usr/bin/env python3
"""
WebRTC Voice Activity Detection (VAD) Example

This example demonstrates how to use the WebRTC VAD for detecting voice activity
in audio files or generated test audio.

Usage:
    python vad_example.py [audio_file.wav]
    
If no audio file is provided, it will generate test audio with speech and silence.
"""

import sys
import numpy as np
import argparse

try:
    import webrtc_audio_processing as webrtc_vad
except ImportError:
    print("webrtc_audio_processing module not found. Please build and install the module first.")
    sys.exit(1)

def load_audio_file(filename):
    """Load audio file (simple WAV loader for demonstration)"""
    try:
        import wave
        with wave.open(filename, 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(-1)
            audio = np.frombuffer(frames, dtype=np.int16)
            return audio, sample_rate
    except ImportError:
        print("Wave module not available")
        return None, None
    except Exception as e:
        print(f"Error loading audio file {filename}: {e}")
        return None, None

def generate_test_audio(duration_sec=5, sample_rate=16000):
    """Generate test audio with alternating speech and silence"""
    print("Generating test audio with alternating speech/silence pattern...")
    
    total_samples = duration_sec * sample_rate
    audio = np.zeros(total_samples, dtype=np.int16)
    
    # Generate pattern: 1 second speech, 1 second silence, repeat
    t = np.linspace(0, duration_sec, total_samples, False)
    
    # Create speech segments (sine waves with varying frequency)
    for i in range(0, duration_sec, 2):  # Every 2 seconds
        start_idx = i * sample_rate
        end_idx = min((i + 1) * sample_rate, total_samples)
        
        if start_idx < total_samples:
            # Generate speech-like signal (multiple sine waves)
            segment_t = t[start_idx:end_idx]
            speech_signal = (
                0.3 * np.sin(2 * np.pi * 200 * segment_t) +  # Fundamental
                0.2 * np.sin(2 * np.pi * 400 * segment_t) +  # Harmonic
                0.1 * np.sin(2 * np.pi * 800 * segment_t) +  # Harmonic
                0.05 * np.random.randn(len(segment_t))        # Noise
            )
            
            # Apply envelope
            envelope = np.sin(np.pi * np.arange(len(segment_t)) / len(segment_t))
            speech_signal *= envelope
            
            # Convert to int16
            audio[start_idx:end_idx] = (speech_signal * 16384).astype(np.int16)
    
    print(f"Generated {duration_sec} seconds of test audio at {sample_rate} Hz")
    return audio, sample_rate

def analyze_with_vad(audio, sample_rate, vad_mode=2, frame_duration_ms=30):
    """Analyze audio with WebRTC VAD"""
    
    # Initialize VAD
    vad = webrtc_vad.VAD()
    success = vad.set_mode(vad_mode)
    if not success:
        print(f"Failed to set VAD mode {vad_mode}")
        return None
    
    # Calculate frame size
    frame_size = int(sample_rate * frame_duration_ms / 1000)
    
    # Validate configuration
    if not webrtc_vad.VAD.is_valid_config(sample_rate, frame_size):
        print(f"Invalid VAD configuration: {sample_rate}Hz, {frame_size} samples")
        print("Supported configurations:")
        print("  Sample rates: 8000, 16000, 32000 Hz")
        print("  Frame durations: 10, 20, 30 ms")
        return None
    
    print(f"VAD Configuration:")
    print(f"  Sample Rate: {sample_rate} Hz")
    print(f"  Frame Duration: {frame_duration_ms} ms") 
    print(f"  Frame Size: {frame_size} samples")
    print(f"  VAD Mode: {vad_mode} (0=least aggressive, 3=most aggressive)")
    print()
    
    # Process audio in frames
    results = []
    speech_frames = 0
    total_frames = 0
    
    print("Processing audio frames:")
    print("Time(s)  | VAD | Status")
    print("-" * 25)
    
    for i in range(0, len(audio), frame_size):
        frame = audio[i:i+frame_size]
        
        # Pad frame if necessary
        if len(frame) < frame_size:
            frame = np.pad(frame, (0, frame_size - len(frame)), 'constant')
        
        # Run VAD
        vad_result = vad.is_speech(frame, sample_rate)
        
        if vad_result == -1:
            print(f"VAD Error at frame {total_frames}")
            continue
        
        # Record result
        time_sec = i / sample_rate
        status = "SPEECH" if vad_result == 1 else "SILENCE"
        results.append((time_sec, vad_result, status))
        
        if vad_result == 1:
            speech_frames += 1
        total_frames += 1
        
        # Print every few frames to avoid spam
        if total_frames % 10 == 0 or total_frames <= 20:
            print(f"{time_sec:6.2f}   |  {vad_result}  | {status}")
    
    # Summary
    speech_percentage = (speech_frames / total_frames * 100) if total_frames > 0 else 0
    print(f"\nSummary:")
    print(f"  Total frames: {total_frames}")
    print(f"  Speech frames: {speech_frames} ({speech_percentage:.1f}%)")
    print(f"  Silence frames: {total_frames - speech_frames} ({100 - speech_percentage:.1f}%)")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="WebRTC VAD Example")
    parser.add_argument("audio_file", nargs='?', 
                        help="Audio file to analyze (optional)")
    parser.add_argument("--vad-mode", type=int, default=2,
                        choices=[0, 1, 2, 3],
                        help="VAD aggressiveness (0=least, 3=most aggressive)")
    parser.add_argument("--frame-duration", type=int, default=30,
                        choices=[10, 20, 30],
                        help="Frame duration in milliseconds")
    parser.add_argument("--generate-duration", type=int, default=10,
                        help="Duration in seconds for generated test audio")
    
    args = parser.parse_args()
    
    # Load or generate audio
    if args.audio_file:
        print(f"Loading audio file: {args.audio_file}")
        audio, sample_rate = load_audio_file(args.audio_file)
        if audio is None:
            print("Failed to load audio file")
            return
    else:
        audio, sample_rate = generate_test_audio(args.generate_duration)
    
    print(f"Audio length: {len(audio)} samples ({len(audio) / sample_rate:.2f} seconds)")
    print()
    
    # Analyze with VAD
    results = analyze_with_vad(
        audio, 
        sample_rate, 
        vad_mode=args.vad_mode,
        frame_duration_ms=args.frame_duration
    )
    
    if results:
        print("\nAnalysis complete!")
    
    # Optional: Save results to file
    if len(sys.argv) > 1 and results:
        output_file = args.audio_file.replace('.wav', '_vad_results.txt')
        try:
            with open(output_file, 'w') as f:
                f.write("Time(s)\tVAD\tStatus\n")
                for time_sec, vad_result, status in results:
                    f.write(f"{time_sec:.2f}\t{vad_result}\t{status}\n")
            print(f"Results saved to: {output_file}")
        except Exception as e:
            print(f"Could not save results: {e}")

if __name__ == "__main__":
    main()