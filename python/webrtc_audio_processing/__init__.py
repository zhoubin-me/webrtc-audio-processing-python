"""
WebRTC Audio Processing Python Bindings

This package provides Python bindings for the WebRTC Audio Processing library,
enabling real-time audio processing including echo cancellation, noise suppression,
automatic gain control, and other audio enhancement features.

Example usage:
    import webrtc_audio_processing as webrtc_apm
    import numpy as np
    
    # Create audio processing instance
    builder = webrtc_apm.AudioProcessingBuilder()
    config = webrtc_apm.Config()
    config.echo_canceller.enabled = True
    config.gain_controller1.enabled = True
    config.high_pass_filter.enabled = True
    
    builder.SetConfig(config)
    apm = builder.Create()
    
    # Configure stream
    stream_config = webrtc_apm.StreamConfig(32000, 1)  # 32kHz, mono
    
    # Process audio frames
    # ... (see examples for full usage)
"""

try:
    from .webrtc_audio_processing import *
except ImportError:
    # Try importing from parent directory (when built in-place)
    import sys
    import os
    import importlib.util
    
    # Look for the compiled module in the parent directory
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    module_path = None
    for file in os.listdir(parent_dir):
        if file.startswith('webrtc_audio_processing') and file.endswith('.so'):
            module_path = os.path.join(parent_dir, file)
            break
    
    if module_path:
        spec = importlib.util.spec_from_file_location('webrtc_audio_processing', module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Import all public symbols
        globals().update({name: getattr(module, name) for name in dir(module) if not name.startswith('_')})

__version__ = "2.1.0"
__all__ = [
    "AudioProcessing",
    "AudioProcessingBuilder", 
    "Config",
    "StreamConfig",
    "HighPassFilter",
    "EchoCanceller", 
    "NoiseSuppression",
    "NoiseSuppressionLevel",
    "GainController1",
    "GainController1Mode",
    "GainController2",
    "Error",
    "GetFrameSize",
    "VAD",
    "StandaloneVad",
    "VoiceActivityDetector",
    "RmsLevel",
    "Resampler",
    "DEFAULT_SAMPLE_RATE",
    "DEFAULT_CHANNELS", 
    "DEFAULT_BLOCK_MS",
]
