# Building Python Bindings for WebRTC Audio Processing

This document describes how to build and install the Python bindings for the WebRTC Audio Processing library.

## Overview

The Python bindings provide access to the core WebRTC Audio Processing functionality including:

- Echo cancellation (AEC3)
- Noise suppression
- Automatic gain control (AGC1/AGC2) 
- High-pass filtering
- Voice activity detection

## Prerequisites

### System Requirements

- Python 3.8 or later
- C++17 compatible compiler
- CMake 3.12+
- Ninja (recommended) or Make

### Dependencies

- NumPy
- pybind11 (automatically installed during build)
- WebRTC Audio Processing C++ library (must be built first)

## Building the C++ Library

First, build and install the WebRTC Audio Processing library:

```bash
# From the repository root
meson . build -Dprefix=$PWD/install
ninja -C build
ninja -C build install

# Make the library discoverable
export PKG_CONFIG_PATH=$PWD/install/lib/pkgconfig:$PKG_CONFIG_PATH
export LD_LIBRARY_PATH=$PWD/install/lib:$LD_LIBRARY_PATH  # Linux
export DYLD_LIBRARY_PATH=$PWD/install/lib:$DYLD_LIBRARY_PATH  # macOS
```

## Building Python Bindings

### Option 1: Using pip (Recommended)

```bash
cd python
pip install .

# For development (editable install)
pip install -e .
```

### Option 2: Using setup.py directly

```bash
cd python
python setup.py build_ext --inplace
python setup.py install
```

### Option 3: Build with specific library paths

If the C++ library is installed in a non-standard location:

```bash
cd python

# Set library paths explicitly
export CPPFLAGS="-I/path/to/webrtc/headers"
export LDFLAGS="-L/path/to/webrtc/lib"

pip install .
```

## Testing the Installation

### Basic Import Test

```python
import webrtc_audio_processing as webrtc_apm
print("WebRTC Audio Processing version:", webrtc_apm.__version__)

# Create a simple configuration
config = webrtc_apm.Config()
config.echo_canceller.enabled = True
print("Echo canceller enabled:", config.echo_canceller.enabled)
```

### Running Examples

```bash
cd python/examples

# Generate test audio files
python generate_test_audio.py

# Run offline processing example
python offline_processing.py play_test.raw rec_test.raw output_test.raw
```

## Troubleshooting

### Common Issues

1. **"webrtc-audio-processing library not found"**
   - Ensure the C++ library is built and installed
   - Check PKG_CONFIG_PATH includes the library's .pc file
   - Verify LD_LIBRARY_PATH (Linux) or DYLD_LIBRARY_PATH (macOS)

2. **Import errors**
   - Make sure all dependencies are installed: `pip install numpy`
   - Try reinstalling: `pip uninstall webrtc-audio-processing && pip install .`

3. **Compilation errors**
   - Ensure you have a C++17 compatible compiler
   - On macOS, you may need to install Xcode command line tools: `xcode-select --install`
   - On Ubuntu/Debian: `sudo apt install build-essential cmake ninja-build`

4. **Runtime segfaults**
   - Check that the C++ library version matches the bindings
   - Ensure proper memory management in audio data handling

### Debug Build

For debugging, build with debug symbols:

```bash
export CXXFLAGS="-g -O0"
pip install . --force-reinstall
```

### Verbose Build

To see detailed compilation output:

```bash
pip install . -v
```

## Development

### Setting up Development Environment

```bash
# Clone repository and navigate to python bindings
cd python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest black flake8
```

### Running Tests

```bash
# Run basic import test
python -c "import webrtc_audio_processing; print('OK')"

# Run example scripts
cd examples
python generate_test_audio.py
python offline_processing.py play_test.raw rec_test.raw output.raw
```

### Code Formatting

```bash
black webrtc_audio_processing/ examples/
flake8 webrtc_audio_processing/ examples/
```

## Package Structure

```
python/
├── webrtc_audio_processing.cpp     # pybind11 binding code
├── webrtc_audio_processing/        # Python package
│   └── __init__.py
├── examples/                       # Example scripts  
│   ├── offline_processing.py       # Main example (equivalent to C++ version)
│   └── generate_test_audio.py      # Test data generation
├── setup.py                        # Build configuration
├── pyproject.toml                  # Package metadata
├── README.md                       # Package documentation
└── MANIFEST.in                     # Package file inclusion rules
```

## API Overview

The Python API closely mirrors the C++ API:

```python
import webrtc_audio_processing as webrtc_apm

# Create processor
builder = webrtc_apm.AudioProcessingBuilder()
config = webrtc_apm.Config()

# Configure processing modules
config.echo_canceller.enabled = True
config.gain_controller1.enabled = True
config.noise_suppression.enabled = True
config.high_pass_filter.enabled = True

# Apply configuration
builder.SetConfig(config)
apm = builder.Create()

# Process audio
stream_config = webrtc_apm.StreamConfig(32000, 1)  # 32kHz mono
apm.ProcessReverseStream(far_end_audio, stream_config, stream_config, far_end_audio)
apm.ProcessStream(near_end_audio, stream_config, stream_config, near_end_audio)
```

## Performance Considerations

- Audio processing is CPU intensive; consider using appropriate thread priorities
- Minimize memory allocations in the audio processing loop
- Use contiguous NumPy arrays for best performance
- Consider processing audio in separate threads from UI/main application logic

## Contributing

When contributing to the Python bindings:

1. Ensure all examples work correctly
2. Add appropriate error handling
3. Follow Python naming conventions where possible while maintaining API consistency
4. Update documentation for any API changes
5. Test on multiple platforms if possible