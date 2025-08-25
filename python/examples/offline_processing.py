#!/usr/bin/env python3
"""
Offline audio processing example - Python equivalent of run-offline.cpp

This example demonstrates how to process audio files offline using the WebRTC
Audio Processing library. It reads playback and recorded audio files, applies
echo cancellation and other processing, and writes the processed output.

Usage:
    python offline_processing.py <play_file> <rec_file> <out_file>

Arguments:
    play_file: Raw 16-bit PCM audio file (far-end/render audio)
    rec_file: Raw 16-bit PCM audio file (near-end/capture audio) 
    out_file: Output file for processed audio

The audio files should be:
- 16-bit signed PCM format
- 32 kHz sample rate
- Mono (1 channel)
- Raw format (no headers)
"""

import sys
import os
import struct
import numpy as np

try:
    # Try importing from package
    import webrtc_audio_processing as webrtc_apm
except ImportError:
    try:
        # Try importing the compiled module directly (for development)
        import importlib.util
        import sys
        import os
        spec = importlib.util.spec_from_file_location('webrtc_audio_processing', 
                                                    os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                                               'webrtc_audio_processing.cpython-310-darwin.so'))
        webrtc_apm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(webrtc_apm)
        print("Using compiled module directly for development")
    except ImportError:
        print("Error: webrtc_audio_processing module not found.")
        print("Please build and install the Python bindings first:")
        print("  cd python")
        print("  pip install .")
        sys.exit(1)


DEFAULT_BLOCK_MS = 10
DEFAULT_RATE = 32000  
DEFAULT_CHANNELS = 1


def read_audio_file(filename):
    """Read raw 16-bit PCM audio file and return as numpy array."""
    try:
        with open(filename, 'rb') as f:
            data = f.read()
            # Convert bytes to 16-bit signed integers
            samples = struct.unpack(f'<{len(data)//2}h', data)
            return np.array(samples, dtype=np.int16)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{filename}': {e}")
        sys.exit(1)


def write_audio_file(filename, audio_data):
    """Write numpy array as raw 16-bit PCM audio file."""
    try:
        with open(filename, 'wb') as f:
            # Convert numpy array to bytes
            data = struct.pack(f'<{len(audio_data)}h', *audio_data)
            f.write(data)
    except Exception as e:
        print(f"Error writing file '{filename}': {e}")
        sys.exit(1)


def create_audio_processor():
    """Create and configure the audio processor."""
    # Create audio processing builder
    builder = webrtc_apm.AudioProcessingBuilder()
    
    # Create configuration
    config = webrtc_apm.Config()
    
    # Enable echo cancellation
    config.echo_canceller.enabled = True
    config.echo_canceller.mobile_mode = False  # Use full AEC, not mobile
    
    # Enable automatic gain control
    config.gain_controller1.enabled = True
    config.gain_controller1.mode = webrtc_apm.GainController1Mode.ADAPTIVE_ANALOG
    
    # Enable AGC2 as well
    config.gain_controller2.enabled = True
    
    # Enable high-pass filter
    config.high_pass_filter.enabled = True
    
    # Apply configuration
    builder.SetConfig(config)
    
    # Create the audio processor
    apm = builder.Create()
    
    return apm


def process_audio_files(play_file, rec_file, out_file):
    """Process the audio files using WebRTC Audio Processing."""
    print(f"Processing audio files:")
    print(f"  Play file: {play_file}")
    print(f"  Record file: {rec_file}")
    print(f"  Output file: {out_file}")
    
    # Read input files
    print("Reading input files...")
    play_audio = read_audio_file(play_file)
    rec_audio = read_audio_file(rec_file)
    
    print(f"Play audio: {len(play_audio)} samples")
    print(f"Record audio: {len(rec_audio)} samples") 
    
    # Create audio processor
    print("Creating audio processor...")
    apm = create_audio_processor()
    
    # Configure stream parameters
    stream_config = webrtc_apm.StreamConfig(DEFAULT_RATE, DEFAULT_CHANNELS)
    
    # Calculate frame size
    frame_size = DEFAULT_RATE * DEFAULT_BLOCK_MS // 1000 * DEFAULT_CHANNELS
    print(f"Frame size: {frame_size} samples ({DEFAULT_BLOCK_MS}ms)")
    
    # Determine number of frames to process
    max_frames = min(len(play_audio), len(rec_audio)) // frame_size
    print(f"Processing {max_frames} frames...")
    
    # Initialize output array
    processed_audio = np.zeros(max_frames * frame_size, dtype=np.int16)
    
    # Process frame by frame
    for i in range(max_frames):
        start_idx = i * frame_size
        end_idx = start_idx + frame_size
        
        # Extract frames
        play_frame = play_audio[start_idx:end_idx].copy()
        rec_frame = rec_audio[start_idx:end_idx].copy()
        
        # Ensure frames are the right size and contiguous
        play_frame = np.ascontiguousarray(play_frame, dtype=np.int16)
        rec_frame = np.ascontiguousarray(rec_frame, dtype=np.int16)
        
        # Process reverse stream (playback/far-end audio)
        result = apm.ProcessReverseStream(
            play_frame, stream_config, stream_config, play_frame
        )
        if result != webrtc_apm.Error.NO_ERROR:
            print(f"Warning: ProcessReverseStream returned error {result} at frame {i}")
        
        # Process forward stream (capture/near-end audio)
        result = apm.ProcessStream(
            rec_frame, stream_config, stream_config, rec_frame
        )
        if result != webrtc_apm.Error.NO_ERROR:
            print(f"Warning: ProcessStream returned error {result} at frame {i}")
        
        # Store processed frame
        processed_audio[start_idx:end_idx] = rec_frame
        
        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"  Processed {i + 1}/{max_frames} frames...")
    
    # Write output file
    print(f"Writing output file: {out_file}")
    write_audio_file(out_file, processed_audio)
    
    print("Processing complete!")
    print(f"Processed {max_frames} frames ({max_frames * DEFAULT_BLOCK_MS / 1000:.2f} seconds)")


def main():
    """Main function."""
    if len(sys.argv) != 4:
        print("Usage: python offline_processing.py <play_file> <rec_file> <out_file>")
        print("")
        print("Arguments:")
        print("  play_file: Raw 16-bit PCM audio file (far-end/render audio)")
        print("  rec_file: Raw 16-bit PCM audio file (near-end/capture audio)")
        print("  out_file: Output file for processed audio")
        print("")
        print("Audio files should be:")
        print("  - 16-bit signed PCM format")
        print("  - 32 kHz sample rate") 
        print("  - Mono (1 channel)")
        print("  - Raw format (no headers)")
        sys.exit(1)
    
    play_file, rec_file, out_file = sys.argv[1:4]
    
    # Verify input files exist
    if not os.path.exists(play_file):
        print(f"Error: Play file '{play_file}' does not exist.")
        sys.exit(1)
    
    if not os.path.exists(rec_file):
        print(f"Error: Record file '{rec_file}' does not exist.")
        sys.exit(1)
    
    # Process the files
    try:
        process_audio_files(play_file, rec_file, out_file)
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()