# WebRTC Audio Processing Python Bindings

Python bindings for the [WebRTC Audio Processing](https://gitlab.freedesktop.org/pulseaudio/webrtc-audio-processing) library, providing real-time audio processing capabilities including echo cancellation, noise suppression, and automatic gain control.

## Features

- **Echo Cancellation**: Removes acoustic echo from audio streams
- **Noise Suppression**: Reduces background noise in captured audio  
- **Automatic Gain Control (AGC)**: Maintains consistent audio levels
- **High-pass Filtering**: Removes low-frequency noise
- **Voice Activity Detection**: Detects speech presence

## Installation

### Prerequisites

First, you need to build and install the WebRTC Audio Processing C++ library:

```bash
# Build the C++ library
meson . build -Dprefix=$PWD/install
ninja -C build
ninja -C build install

# Add to pkg-config path (if needed)
export PKG_CONFIG_PATH=$PWD/install/lib/pkgconfig:$PKG_CONFIG_PATH
```

### Install Python Package

```bash
# Install from source
pip install .

# Or for development
pip install -e .
```

## Quick Start

```python
import webrtc_audio_processing as webrtc_apm
import numpy as np

# Create and configure audio processing
builder = webrtc_apm.AudioProcessingBuilder()
config = webrtc_apm.Config()

# Enable echo cancellation
config.echo_canceller.enabled = True
config.echo_canceller.mobile_mode = False

# Enable automatic gain control
config.gain_controller1.enabled = True
config.gain_controller1.mode = webrtc_apm.GainController1Mode.ADAPTIVE_ANALOG

# Enable noise suppression
config.noise_suppression.enabled = True
config.noise_suppression.level = webrtc_apm.NoiseSuppressionLevel.MODERATE

# Enable high-pass filter
config.high_pass_filter.enabled = True

# Apply configuration and create processor
builder.SetConfig(config)
apm = builder.Create()

# Configure audio streams (32kHz, mono)
stream_config = webrtc_apm.StreamConfig(32000, 1)

# Process audio frames
# render_frame: far-end audio (what the user hears)
# capture_frame: near-end audio (microphone input)

render_frame = np.array([...], dtype=np.int16)  # Your render audio data
capture_frame = np.array([...], dtype=np.int16)  # Your capture audio data

# Process reverse stream (render/playback audio)
apm.ProcessReverseStream(render_frame, stream_config, stream_config, render_frame)

# Process forward stream (capture/microphone audio) 
apm.ProcessStream(capture_frame, stream_config, stream_config, capture_frame)

# The capture_frame now contains the processed audio
```

## Examples

See the `examples/` directory for complete working examples:

- `offline_processing.py` - Process audio files offline (equivalent to C++ run-offline example)
- `realtime_processing.py` - Real-time audio processing with microphone/speakers

## Additional APIs

### Standalone VAD (modules/audio_processing/vad)

```python
import webrtc_audio_processing as webrtc_apm
import numpy as np

vad = webrtc_apm.StandaloneVad()
vad.set_mode(2)  # 0..3

# 10 ms @ 16 kHz = 160 samples
frame = np.zeros(160, dtype=np.int16)
vad.add_audio(frame)
probs = vad.get_activity(1)
```

### Voice Activity Detector (combined VAD + RMS)

```python
vad = webrtc_apm.VoiceActivityDetector()
audio = np.zeros(320, dtype=np.int16)  # 10 ms @ 32 kHz
vad.process_chunk(audio, 32000)
probs = vad.chunkwise_voice_probabilities()
rms = vad.chunkwise_rms()
last = vad.last_voice_probability()
```

### RMS Level

```python
rms = webrtc_apm.RmsLevel()
rms.Analyze(np.zeros(160, dtype=np.int16))
avg = rms.Average()
avg, peak = rms.AverageAndPeak()
```

### Resampler

```python
resampler = webrtc_apm.Resampler(48000, 16000, 1)
input_audio = np.zeros(480, dtype=np.int16)  # 10 ms @ 48 kHz
output_audio = resampler.process(input_audio)
```

## API Reference

### AudioProcessing

Main audio processing class:

- `Initialize()` - Initialize the audio processor
- `ApplyConfig(config)` - Apply configuration settings
- `ProcessStream(data, input_config, output_config, output)` - Process capture stream
- `ProcessReverseStream(data, input_config, output_config, output)` - Process render stream
- `set_stream_delay_ms(delay)` - Set stream delay in milliseconds

### Config

Configuration structure with the following components:

- `echo_canceller` - Echo cancellation settings
- `noise_suppression` - Noise suppression settings  
- `gain_controller1` - AGC1 settings
- `gain_controller2` - AGC2 settings
- `high_pass_filter` - High-pass filter settings

### StreamConfig

Audio stream configuration:

```python
config = webrtc_apm.StreamConfig(sample_rate_hz, num_channels)
```

## Requirements

- Python 3.8+
- NumPy
- WebRTC Audio Processing C++ library (built separately)

## License

BSD 3-Clause License (same as WebRTC Audio Processing library)

## Contributing

Contributions are welcome! Please see the main WebRTC Audio Processing project for contribution guidelines.
