#!/usr/bin/env python3
"""
Real-time echo cancellation example using WebRTC Audio Processing

This example demonstrates real-time audio processing with microphone input
and speaker output, applying echo cancellation and other audio processing
features from the WebRTC Audio Processing library.

Requirements:
    pip install pyaudio numpy webrtc-audio-processing

Usage:
    python realtime_echo_cancellation.py

The script will:
1. Capture audio from your default microphone
2. Play audio through your default speakers
3. Apply echo cancellation to remove acoustic feedback
4. Apply noise suppression and automatic gain control
5. Output the processed audio in real-time
"""

import sys
import numpy as np
import threading
import queue
import time
from collections import deque

try:
    import pyaudio
except ImportError:
    print("Error: pyaudio not found. Install with: pip install pyaudio")
    sys.exit(1)

try:
    import webrtc_audio_processing as webrtc_apm
except ImportError:
    print("Error: webrtc_audio_processing module not found.")
    print("Please build and install the Python bindings first:")
    print("  cd python")
    print("  pip install .")
    sys.exit(1)


# Audio configuration
SAMPLE_RATE = 24000  # WebRTC Audio Processing works best at 32kHz
CHANNELS = 1         # Mono audio
FRAME_SIZE_MS = 10   # 10ms frames (WebRTC standard)
FRAME_SIZE = SAMPLE_RATE * FRAME_SIZE_MS // 1000  # 320 samples per frame
CHUNK_SIZE = FRAME_SIZE  # PyAudio chunk size

# Buffer configuration
BUFFER_SIZE = 10  # Number of frames to buffer


class RealTimeEchoCanceller:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.apm = None
        self.stream_config = None

        # Queues for audio data
        self.mic_queue = queue.Queue(maxsize=BUFFER_SIZE)
        self.speaker_queue = queue.Queue(maxsize=BUFFER_SIZE)
        self.output_queue = queue.Queue(maxsize=BUFFER_SIZE)

        # Streams
        self.input_stream = None
        self.output_stream = None

        # Control flags
        self.running = False
        self.processing_thread = None

        # Statistics
        self.frames_processed = 0
        self.start_time = None

    def setup_webrtc_processor(self):
        """Initialize and configure the WebRTC Audio Processor."""
        print("Setting up WebRTC Audio Processor...")

        # Create audio processing builder
        builder = webrtc_apm.AudioProcessingBuilder()

        # Create configuration
        config = webrtc_apm.Config()

        # Enable echo cancellation (most important for real-time)
        config.echo_canceller.enabled = True
        config.echo_canceller.mobile_mode = False  # Use full AEC for better quality

        # Enable noise suppression
        config.noise_suppression.enabled = True
        config.noise_suppression.level = webrtc_apm.NoiseSuppressionLevel.MODERATE

        # Enable automatic gain control
        config.gain_controller1.enabled = True
        config.gain_controller1.mode = webrtc_apm.GainController1Mode.ADAPTIVE_ANALOG

        # Enable high-pass filter to remove low-frequency noise
        config.high_pass_filter.enabled = True

        # Apply configuration and create processor
        builder.SetConfig(config)
        self.apm = builder.Create()

        # Configure stream parameters
        self.stream_config = webrtc_apm.StreamConfig(SAMPLE_RATE, CHANNELS)

        print("WebRTC Audio Processor configured successfully")

    def audio_input_callback(self, in_data, frame_count, time_info, status):
        """Callback for microphone input."""
        if status:
            print(f"Input callback status: {status}")

        # Convert bytes to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)

        try:
            # Add to microphone queue (non-blocking)
            self.mic_queue.put_nowait(audio_data.copy())
        except queue.Full:
            # Drop frame if queue is full
            pass

        return (None, pyaudio.paContinue)

    def audio_output_callback(self, in_data, frame_count, time_info, status):
        """Callback for speaker output."""
        if status:
            print(f"Output callback status: {status}")

        try:
            # Get processed audio from output queue
            audio_data = self.output_queue.get_nowait()

            # Also add to speaker queue for echo cancellation reference
            self.speaker_queue.put_nowait(audio_data.copy())

            return (audio_data.tobytes(), pyaudio.paContinue)
        except queue.Empty:
            # Return silence if no processed audio available
            silence = np.zeros(frame_count, dtype=np.int16)
            return (silence.tobytes(), pyaudio.paContinue)

    def process_audio(self):
        """Audio processing thread - applies WebRTC processing."""
        print("Starting audio processing thread...")

        while self.running:
            try:
                # Get microphone input (with timeout)
                mic_frame = self.mic_queue.get(timeout=0.1)

                # Get speaker reference (use zeros if not available)
                try:
                    speaker_frame = self.speaker_queue.get_nowait()
                except queue.Empty:
                    speaker_frame = np.zeros(FRAME_SIZE, dtype=np.int16)

                # Ensure frames are the correct size and contiguous
                if len(mic_frame) != FRAME_SIZE:
                    # Pad or truncate to correct size
                    if len(mic_frame) < FRAME_SIZE:
                        mic_frame = np.pad(mic_frame, (0, FRAME_SIZE - len(mic_frame)))
                    else:
                        mic_frame = mic_frame[:FRAME_SIZE]

                if len(speaker_frame) != FRAME_SIZE:
                    if len(speaker_frame) < FRAME_SIZE:
                        speaker_frame = np.pad(speaker_frame, (0, FRAME_SIZE - len(speaker_frame)))
                    else:
                        speaker_frame = speaker_frame[:FRAME_SIZE]

                # Make arrays contiguous
                mic_frame = np.ascontiguousarray(mic_frame, dtype=np.int16)
                speaker_frame = np.ascontiguousarray(speaker_frame, dtype=np.int16)

                # Process reverse stream (speaker/playback audio for echo reference)
                result = self.apm.ProcessReverseStream(
                    speaker_frame, self.stream_config, self.stream_config, speaker_frame
                )
                if result != webrtc_apm.Error.NO_ERROR:
                    print(f"ProcessReverseStream error: {result}")

                # Process forward stream (microphone audio)
                processed_frame = mic_frame.copy()
                result = self.apm.ProcessStream(
                    mic_frame, self.stream_config, self.stream_config, processed_frame
                )
                if result != webrtc_apm.Error.NO_ERROR:
                    print(f"ProcessStream error: {result}")

                # Add processed audio to output queue
                try:
                    self.output_queue.put_nowait(processed_frame)
                except queue.Full:
                    # Drop frame if queue is full
                    pass

                self.frames_processed += 1

                # Print statistics every 5 seconds
                if self.frames_processed % (5 * SAMPLE_RATE // FRAME_SIZE) == 0:
                    elapsed = time.time() - self.start_time
                    fps = self.frames_processed / elapsed
                    print(f"Processed {self.frames_processed} frames in {elapsed:.1f}s ({fps:.1f} fps)")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in processing thread: {e}")
                continue

    def start(self):
        """Start real-time audio processing."""
        print("Starting real-time echo cancellation...")

        # Setup WebRTC processor
        self.setup_webrtc_processor()

        # Open audio streams
        print(f"Opening audio streams (sample rate: {SAMPLE_RATE}Hz, frame size: {FRAME_SIZE})")

        try:
            # Input stream (microphone)
            self.input_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
                stream_callback=self.audio_input_callback
            )

            # Output stream (speakers)
            self.output_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                output=True,
                frames_per_buffer=CHUNK_SIZE,
                stream_callback=self.audio_output_callback
            )

            # Start streams
            self.input_stream.start_stream()
            self.output_stream.start_stream()

            # Start processing thread
            self.running = True
            self.start_time = time.time()
            self.processing_thread = threading.Thread(target=self.process_audio)
            self.processing_thread.start()

            print("Real-time processing started!")
            print("Speak into your microphone - the processed audio will play through speakers")
            print("Echo cancellation is active to prevent feedback")
            print("Press Ctrl+C to stop")

            # Keep main thread alive
            while self.running:
                time.sleep(0.1)

        except Exception as e:
            print(f"Error starting audio streams: {e}")
            self.stop()

    def stop(self):
        """Stop audio processing."""
        print("Stopping real-time echo cancellation...")

        self.running = False

        # Wait for processing thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)

        # Stop and close streams
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()

        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()

        # Close PyAudio
        self.audio.terminate()

        print("Stopped successfully")

        # Print final statistics
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"Total frames processed: {self.frames_processed}")
            print(f"Processing time: {elapsed:.1f}s")
            print(f"Average frame rate: {self.frames_processed / elapsed:.1f} fps")


def list_audio_devices():
    """List available audio input and output devices."""
    audio = pyaudio.PyAudio()

    print("Available audio devices:")
    print("=" * 50)

    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        print(f"Device {i}: {info['name']}")
        print(f"  Channels: {info['maxInputChannels']} in, {info['maxOutputChannels']} out")
        print(f"  Sample Rate: {info['defaultSampleRate']}")
        print(f"  Host API: {audio.get_host_api_info_by_index(info['hostApi'])['name']}")
        print()

    audio.terminate()


def main():
    """Main function."""
    print("WebRTC Real-Time Echo Cancellation Example")
    print("=" * 50)

    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--list-devices":
        list_audio_devices()
        return

    print(f"Audio Configuration:")
    print(f"  Sample Rate: {SAMPLE_RATE} Hz")
    print(f"  Channels: {CHANNELS}")
    print(f"  Frame Size: {FRAME_SIZE} samples ({FRAME_SIZE_MS}ms)")
    print()

    # Create and start echo canceller
    canceller = RealTimeEchoCanceller()

    try:
        canceller.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        canceller.stop()


if __name__ == "__main__":
    main()
