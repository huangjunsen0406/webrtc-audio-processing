# WebRTC Audio Processing Python Bindings

This directory contains Python bindings for the WebRTC Audio Processing library using pybind11.

## Features

- **Echo Cancellation (AEC3)**: Advanced echo cancellation
- **Noise Suppression**: Reduces background noise
- **Automatic Gain Control**: Maintains consistent audio levels
- **High-pass Filter**: Removes low-frequency noise
- **Residual Echo Detection**: Detects remaining echo after cancellation
- **Statistics**: Real-time processing statistics

## Quick Start

### 1. Build the C++ Library

```bash
# From project root
meson setup build_cpp -Dcpp_std=c++17 -Ddefault_library=static -Dbuildtype=release
meson compile -C build_cpp
```

### 2. Install Python Dependencies

```bash
pip install pybind11[global] numpy wheel setuptools
```

### 3. Build and Install Python Package

```bash
# Build wheel
python setup.py bdist_wheel

# Install
pip install dist/webrtc_audio_processing-*.whl
```

### 4. Basic Usage

```python
import webrtc_audio_processing as wapm
import numpy as np

# Create audio processor
apm = wapm.AudioProcessing()

# Configure features
apm.apply_config(
    echo_cancellation=True,
    noise_suppression=True,
    gain_control=True
)

# Process audio (16-bit, 16kHz)
audio_data = np.random.randint(-1000, 1000, 1600, dtype=np.int16)  # 100ms
processed = apm.process_stream(audio_data, sample_rate=16000)

print(f"Processed {len(processed)} samples")
```

## API Reference

### AudioProcessing Class

#### Constructor
```python
apm = wapm.AudioProcessing()
```

#### Configuration
```python
apm.apply_config(
    echo_cancellation=True,      # Enable AEC3
    noise_suppression=True,      # Enable noise suppression
    gain_control=True,           # Enable AGC
    high_pass_filter=True,       # Enable high-pass filter
    residual_echo_detector=False # Enable echo detection
)
```

#### Audio Processing
```python
# Process capture stream (microphone)
processed = apm.process_stream(
    input,                       # numpy int16 array
    sample_rate=16000,          # 8000, 16000, 32000, or 48000 Hz
    num_channels=1              # 1-8 channels
)

# Process render stream (speaker, for echo cancellation)
processed = apm.process_reverse_stream(
    input,                       # numpy int16 array
    sample_rate=16000,          # 8000, 16000, 32000, or 48000 Hz
    num_channels=1              # 1-8 channels
)
```

#### Gain Control
```python
# Set analog level (0-255)
apm.set_stream_analog_level(128)

# Get recommended level
level = apm.recommended_stream_analog_level()
```

#### Delay and Statistics
```python
# Set known delay (0-500 ms)
apm.set_stream_delay_ms(100)

# Check for echo
has_echo = apm.stream_has_echo()

# Get processing statistics
stats = apm.get_statistics()
```

## Examples

### Real-time Audio Processing

```python
import webrtc_audio_processing as wapm
import numpy as np

apm = wapm.AudioProcessing()
apm.apply_config(echo_cancellation=True, noise_suppression=True)

# Simulate real-time processing (10ms frames at 16kHz)
frame_size = 160
for i in range(100):  # Process 1 second
    # Get audio frame from microphone
    mic_frame = get_microphone_frame()  # Your audio input function
    
    # Get speaker frame (for echo cancellation)
    speaker_frame = get_speaker_frame()  # Your audio output function
    
    # Process render stream first
    apm.process_reverse_stream(speaker_frame)
    
    # Process capture stream
    processed_frame = apm.process_stream(mic_frame)
    
    # Send to output
    send_to_output(processed_frame)  # Your audio output function
```

### Echo Cancellation with Delay

```python
import webrtc_audio_processing as wapm
import numpy as np

apm = wapm.AudioProcessing()
apm.apply_config(echo_cancellation=True)

# Set known audio delay (e.g., speaker-to-microphone delay)
apm.set_stream_delay_ms(50)

# Process audio with echo reference
while True:
    # Audio from speaker (reference for echo cancellation)
    speaker_audio = get_speaker_audio()
    apm.process_reverse_stream(speaker_audio)
    
    # Audio from microphone (with potential echo)
    mic_audio = get_microphone_audio()
    processed = apm.process_stream(mic_audio)
    
    # Use processed audio
    output_clean_audio(processed)
```

### Automatic Gain Control

```python
import webrtc_audio_processing as wapm
import numpy as np

apm = wapm.AudioProcessing()
apm.apply_config(gain_control=True)

# Initialize gain level
analog_level = 128
apm.set_stream_analog_level(analog_level)

while True:
    # Get audio frame
    audio_frame = get_audio_frame()
    
    # Process audio
    processed = apm.process_stream(audio_frame)
    
    # Update gain level based on recommendation
    recommended_level = apm.recommended_stream_analog_level()
    apm.set_stream_analog_level(recommended_level)
    
    # Output processed audio
    output_audio(processed)
```

## Testing

Run the test suite:

```bash
cd python
python test_bindings.py
```

Run usage examples:

```bash
cd python
python example_usage.py
```

## Supported Platforms

- **Linux**: x86_64, ARM64
- **Windows**: x86_64
- **macOS**: x86_64, ARM64 (Apple Silicon)

## Supported Python Versions

- Python 3.8+
- NumPy 1.19.0+

## Performance Notes

- Use 10ms audio frames (160 samples at 16kHz) for optimal performance
- Process render stream before capture stream for best echo cancellation
- Set stream delay if known for improved echo cancellation
- Use appropriate sample rates: 8kHz, 16kHz, 32kHz, or 48kHz

## Troubleshooting

### Import Error
```
ImportError: No module named 'webrtc_audio_processing'
```
**Solution**: Make sure you've built and installed the wheel package.

### Build Error
```
error: Microsoft Visual C++ 14.0 is required
```
**Solution**: On Windows, install Visual Studio Build Tools.

### Runtime Error: Invalid sample rate
```
RuntimeError: Sample rate must be 8000, 16000, 32000, or 48000 Hz
```
**Solution**: Use one of the supported sample rates.

### Poor Echo Cancellation
- Ensure render stream is processed before capture stream
- Set accurate stream delay with `set_stream_delay_ms()`
- Use appropriate frame sizes (10ms recommended)
- Ensure audio synchronization between render and capture

## License

This Python binding follows the same license as the main WebRTC Audio Processing library.