#!/usr/bin/env python3
"""
Real-time Voice Activity Detection (VAD) Example

This example demonstrates real-time voice activity detection using the WebRTC VAD
algorithm. It captures audio from the microphone and detects voice activity in
real-time, displaying the results.

Requirements:
    pip install numpy sounddevice matplotlib

Usage:
    python realtime_vad.py

Controls:
    - Press Ctrl+C to stop
    - Adjust VAD_MODE for different sensitivity levels
"""

import sys
import time
import threading
import queue
import numpy as np
import argparse
from collections import deque

try:
    import sounddevice as sd
except ImportError:
    print("sounddevice is required. Install with: pip install sounddevice")
    sys.exit(1)

try:
    import webrtc_audio_processing as webrtc_vad
except ImportError:
    print("webrtc_audio_processing module not found. Please build and install the module first.")
    sys.exit(1)

# VAD Configuration
VAD_MODE = 2  # 0=least aggressive, 3=most aggressive
SAMPLE_RATE = 16000  # WebRTC VAD supports 8000, 16000, 32000 Hz
FRAME_DURATION_MS = 30  # 10, 20, or 30 ms frames supported
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # samples per frame

class RealTimeVAD:
    def __init__(self, sample_rate=SAMPLE_RATE, frame_size=FRAME_SIZE, vad_mode=VAD_MODE):
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self.vad_mode = vad_mode
        
        # Initialize VAD
        try:
            self.vad = webrtc_vad.VAD()
            success = self.vad.set_mode(vad_mode)
            if not success:
                raise RuntimeError(f"Failed to set VAD mode {vad_mode}")
        except Exception as e:
            print(f"Failed to initialize VAD: {e}")
            sys.exit(1)
        
        # Validate configuration
        if not webrtc_vad.VAD.is_valid_config(sample_rate, frame_size):
            print(f"Invalid VAD configuration: {sample_rate}Hz, {frame_size} samples")
            print("Supported: 8000/16000/32000 Hz with 10/20/30ms frames")
            sys.exit(1)
        
        # Audio processing
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.audio_buffer = np.array([], dtype=np.int16)
        
        # Statistics
        self.speech_frames = 0
        self.total_frames = 0
        self.speech_history = deque(maxlen=100)  # Last 100 decisions for smoothing
        
    def audio_callback(self, indata, frames, time, status):
        """Audio input callback function"""
        if status:
            print(f"Audio callback status: {status}")
        
        # Convert float32 to int16
        audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
        self.audio_queue.put(audio_int16.copy())
    
    def process_audio(self):
        """Process audio frames for VAD"""
        print(f"VAD Configuration:")
        print(f"  Sample Rate: {self.sample_rate} Hz")
        print(f"  Frame Duration: {FRAME_DURATION_MS} ms")
        print(f"  Frame Size: {self.frame_size} samples")
        print(f"  VAD Mode: {self.vad_mode} (0=least aggressive, 3=most aggressive)")
        print(f"Starting real-time VAD... Press Ctrl+C to stop")
        print("-" * 60)
        
        while self.is_running:
            try:
                # Get audio data from queue
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Add to buffer
                self.audio_buffer = np.concatenate([self.audio_buffer, audio_chunk])
                
                # Process complete frames
                while len(self.audio_buffer) >= self.frame_size:
                    # Extract one frame
                    frame = self.audio_buffer[:self.frame_size]
                    self.audio_buffer = self.audio_buffer[self.frame_size:]
                    
                    # Run VAD
                    vad_result = self.vad.is_speech(frame, self.sample_rate)
                    
                    # Update statistics
                    self.total_frames += 1
                    if vad_result == 1:
                        self.speech_frames += 1
                        self.speech_history.append(1)
                    elif vad_result == 0:
                        self.speech_history.append(0)
                    else:
                        print(f"VAD Error: {vad_result}")
                        continue
                    
                    # Calculate recent speech activity (last 1 second)
                    recent_frames = min(len(self.speech_history), 
                                      int(1000 / FRAME_DURATION_MS))  # 1 second worth
                    recent_speech = sum(list(self.speech_history)[-recent_frames:])
                    recent_ratio = recent_speech / recent_frames if recent_frames > 0 else 0
                    
                    # Display results
                    if self.total_frames % 10 == 0:  # Update every ~300ms
                        overall_ratio = self.speech_frames / self.total_frames
                        status = "SPEECH" if vad_result == 1 else "SILENCE"
                        activity_bar = "█" * int(recent_ratio * 20) + "░" * (20 - int(recent_ratio * 20))
                        
                        print(f"\r{status:7} | "
                              f"Current: {vad_result} | "
                              f"Recent: [{activity_bar}] {recent_ratio:.2f} | "
                              f"Overall: {overall_ratio:.3f} "
                              f"({self.speech_frames}/{self.total_frames})", 
                              end="", flush=True)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"\nError processing audio: {e}")
                break
    
    def start(self):
        """Start real-time VAD"""
        self.is_running = True
        
        # Start audio processing thread
        processing_thread = threading.Thread(target=self.process_audio)
        processing_thread.daemon = True
        processing_thread.start()
        
        # Start audio stream
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                blocksize=self.frame_size,
                callback=self.audio_callback
            ):
                processing_thread.join()
        except KeyboardInterrupt:
            print("\n\nStopping VAD...")
        except Exception as e:
            print(f"\nAudio stream error: {e}")
        finally:
            self.is_running = False
    
    def stop(self):
        """Stop VAD processing"""
        self.is_running = False


def main():
    parser = argparse.ArgumentParser(description="Real-time Voice Activity Detection")
    parser.add_argument("--sample-rate", type=int, default=16000,
                        choices=[8000, 16000, 32000],
                        help="Audio sample rate (Hz)")
    parser.add_argument("--frame-duration", type=int, default=30,
                        choices=[10, 20, 30],
                        help="Frame duration (ms)")
    parser.add_argument("--vad-mode", type=int, default=2,
                        choices=[0, 1, 2, 3],
                        help="VAD aggressiveness (0=least, 3=most aggressive)")
    parser.add_argument("--list-devices", action="store_true",
                        help="List available audio devices")
    
    args = parser.parse_args()
    
    if args.list_devices:
        print("Available audio devices:")
        print(sd.query_devices())
        return
    
    # Calculate frame size
    frame_size = int(args.sample_rate * args.frame_duration / 1000)
    
    # Create and start VAD
    try:
        vad = RealTimeVAD(
            sample_rate=args.sample_rate,
            frame_size=frame_size,
            vad_mode=args.vad_mode
        )
        vad.start()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()