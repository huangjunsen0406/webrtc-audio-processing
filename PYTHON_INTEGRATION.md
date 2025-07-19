# Python Integration Guide

This document describes how to use the WebRTC Audio Processing library in Python applications.

## Overview

There are two main approaches to integrate this library with Python:

1. **ctypes + Dynamic Library** - Direct C API usage
2. **pybind11 + Python Extension** - Native Python module

## Method 1: ctypes + Dynamic Library

### Description
Use the existing C API in `/export/` directory through Python's ctypes module with pre-compiled dynamic libraries.

### Advantages
- ✅ Uses existing build artifacts directly
- ✅ No additional compilation required
- ✅ Simple Python implementation
- ✅ Cross-platform compatible

### Disadvantages
- ❌ Manual memory and pointer management
- ❌ Error-prone type conversions
- ❌ Difficult debugging
- ❌ Need to distribute library files

### Implementation

#### Step 1: Build Dynamic Library
```bash
# Use existing CI/CD or build locally
meson setup build -Ddefault_library=shared -Dbuildtype=release
ninja -C build
```

#### Step 2: Python Wrapper
```python
import ctypes
import numpy as np
import platform

# Load platform-specific library
if platform.system() == "Windows":
    lib = ctypes.CDLL("./webrtc_audio_processing.dll")
elif platform.system() == "Darwin":
    lib = ctypes.CDLL("./libwebrtc_audio_processing.dylib")
else:
    lib = ctypes.CDLL("./libwebrtc_audio_processing.so")

# Define function prototypes
lib.WebRTC_APM_Create.restype = ctypes.c_void_p
lib.WebRTC_APM_CreateStreamConfig.argtypes = [ctypes.c_int, ctypes.c_size_t]
lib.WebRTC_APM_CreateStreamConfig.restype = ctypes.c_void_p
lib.WebRTC_APM_ProcessStream.argtypes = [
    ctypes.c_void_p,  # handle
    ctypes.POINTER(ctypes.c_int16),  # src
    ctypes.c_void_p,  # input_config
    ctypes.c_void_p,  # output_config
    ctypes.POINTER(ctypes.c_int16)   # dest
]
lib.WebRTC_APM_ProcessStream.restype = ctypes.c_int

class WebRTCAudioProcessing:
    def __init__(self):
        self.apm = lib.WebRTC_APM_Create()
        
    def create_stream_config(self, sample_rate, channels):
        return lib.WebRTC_APM_CreateStreamConfig(sample_rate, channels)
    
    def process_stream(self, audio_data, input_config, output_config):
        audio_array = np.array(audio_data, dtype=np.int16)
        output = np.zeros_like(audio_array)
        
        result = lib.WebRTC_APM_ProcessStream(
            self.apm,
            audio_array.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
            input_config,
            output_config,
            output.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))
        )
        return output if result == 0 else None
    
    def __del__(self):
        if hasattr(self, 'apm'):
            lib.WebRTC_APM_Destroy(self.apm)
```

#### Step 3: Usage Example
```python
# Create audio processing instance
apm = WebRTCAudioProcessing()

# Create stream configuration (16kHz, mono)
config = apm.create_stream_config(16000, 1)

# Process audio data
audio_in = np.random.randint(-32768, 32767, 1600, dtype=np.int16)  # 100ms audio
processed = apm.process_stream(audio_in, config, config)

print(f"Processed {len(processed)} samples")
```

## Method 2: pybind11 + Python Extension (Recommended)

### Description
Create a native Python extension module using pybind11 that wraps the C++ AudioProcessing API directly.

### Advantages
- ✅ Native Python experience
- ✅ Automatic type conversion
- ✅ Excellent performance
- ✅ Easy debugging
- ✅ Standard wheel distribution
- ✅ Memory management handled automatically

### Disadvantages
- ❌ Higher implementation complexity
- ❌ Requires C++ compilation knowledge
- ❌ More complex build setup

### Implementation

#### Step 1: Install Dependencies
```bash
pip install pybind11[global] numpy
```

#### Step 2: Create Python Bindings
Create `python/bindings.cpp`:
```cpp
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "webrtc/modules/audio_processing/include/audio_processing.h"

namespace py = pybind11;

class PyAudioProcessing {
public:
    PyAudioProcessing() {
        apm_ = webrtc::AudioProcessingBuilder().Create();
    }
    
    void apply_config(bool echo_cancellation = true, 
                     bool noise_suppression = true,
                     bool gain_control = true) {
        webrtc::AudioProcessing::Config config;
        config.echo_canceller.enabled = echo_cancellation;
        config.noise_suppression.enabled = noise_suppression;
        config.gain_controller1.enabled = gain_control;
        config.gain_controller1.mode = 
            webrtc::AudioProcessing::Config::GainController1::kAdaptiveAnalog;
        config.high_pass_filter.enabled = true;
        apm_->ApplyConfig(config);
    }
    
    py::array_t<int16_t> process_stream(py::array_t<int16_t> input, 
                                       int sample_rate = 16000, 
                                       int num_channels = 1) {
        auto buf = input.request();
        if (buf.ndim != 1) {
            throw std::runtime_error("Input array must be 1-dimensional");
        }
        
        size_t samples = buf.shape[0];
        auto output = py::array_t<int16_t>(samples);
        auto output_buf = output.request();
        
        int16_t* input_ptr = static_cast<int16_t*>(buf.ptr);
        int16_t* output_ptr = static_cast<int16_t*>(output_buf.ptr);
        
        webrtc::StreamConfig config(sample_rate, num_channels);
        apm_->ProcessStream(input_ptr, config, config, output_ptr);
        
        return output;
    }
    
    void set_stream_delay_ms(int delay_ms) {
        apm_->set_stream_delay_ms(delay_ms);
    }

private:
    rtc::scoped_refptr<webrtc::AudioProcessing> apm_;
};

PYBIND11_MODULE(webrtc_audio_processing, m) {
    m.doc() = "WebRTC Audio Processing Python bindings";
    
    py::class_<PyAudioProcessing>(m, "AudioProcessing")
        .def(py::init<>(), "Create AudioProcessing instance")
        .def("apply_config", &PyAudioProcessing::apply_config,
             py::arg("echo_cancellation") = true,
             py::arg("noise_suppression") = true,
             py::arg("gain_control") = true,
             "Configure audio processing features")
        .def("process_stream", &PyAudioProcessing::process_stream,
             py::arg("input"), py::arg("sample_rate") = 16000, py::arg("num_channels") = 1,
             "Process audio stream")
        .def("set_stream_delay_ms", &PyAudioProcessing::set_stream_delay_ms,
             py::arg("delay_ms"),
             "Set stream delay in milliseconds");
}
```

#### Step 3: Setup Configuration
Create `setup.py`:
```python
from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext
from pybind11 import get_cmake_dir
import pybind11

ext_modules = [
    Pybind11Extension(
        "webrtc_audio_processing",
        [
            "python/bindings.cpp",
        ],
        include_dirs=[
            ".",
            "webrtc",
        ],
        libraries=["webrtc_audio_processing"],
        library_dirs=["./build"],
        cxx_std=17,
        define_macros=[("VERSION_INFO", '"dev"')],
    ),
]

setup(
    name="webrtc-audio-processing",
    version="2.1.0",
    author="WebRTC Audio Processing Team",
    description="Python bindings for WebRTC Audio Processing",
    long_description="",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.7",
    install_requires=["numpy"],
)
```

#### Step 4: Build and Install
```bash
# Build C++ library first
meson setup build -Ddefault_library=static -Dbuildtype=release
ninja -C build

# Build Python extension
python setup.py build_ext --inplace

# Create wheel package
python setup.py bdist_wheel

# Install
pip install dist/webrtc_audio_processing-*.whl
```

#### Step 5: Usage Example
```python
import webrtc_audio_processing
import numpy as np

# Create audio processing instance
apm = webrtc_audio_processing.AudioProcessing()

# Configure features
apm.apply_config(
    echo_cancellation=True,
    noise_suppression=True,
    gain_control=True
)

# Set stream delay if known
apm.set_stream_delay_ms(100)

# Process audio data
audio_data = np.random.randint(-1000, 1000, 1600, dtype=np.int16)  # 100ms at 16kHz
processed = apm.process_stream(audio_data, sample_rate=16000, num_channels=1)

print(f"Input: {len(audio_data)} samples")
print(f"Output: {len(processed)} samples")
print(f"Max value: {np.max(np.abs(processed))}")
```

## Integration with Existing Build System

### Adding to meson.build
```meson
# Add to main meson.build
python = import('python').find_installation()

if python.found()
  pybind11_dep = dependency('pybind11', required: false)
  
  if pybind11_dep.found()
    python_module = python.extension_module(
      'webrtc_audio_processing',
      sources: ['python/bindings.cpp'],
      dependencies: [audio_processing_dep, pybind11_dep],
      install: true
    )
  endif
endif
```

## Comparison

| Feature | Method 1 (ctypes) | Method 2 (pybind11) |
|---------|-------------------|---------------------|
| **Development Complexity** | Medium | High |
| **User Experience** | Manual management | Native Python |
| **Performance** | Good | Excellent |
| **Distribution** | Library + Python files | Standard wheel |
| **Maintenance** | Low | Medium |
| **Debugging** | Difficult | Easy |
| **Type Safety** | Manual | Automatic |
| **Memory Management** | Manual | Automatic |

## Recommendation

- **For quick prototyping**: Use Method 1 (ctypes)
- **For production applications**: Use Method 2 (pybind11)
- **For open source distribution**: Use Method 2 (pybind11) with wheel packaging

## CI/CD Integration

Both methods can be integrated with the existing `build-multiplatform.yml`:

```yaml
# Add to existing workflow
- name: Build Python Package
  if: matrix.config.name == 'linux/dll/x64'  # Build only once
  run: |
    pip install pybind11[global] wheel numpy
    python setup.py bdist_wheel
    
- name: Upload Python Package
  if: matrix.config.name == 'linux/dll/x64'
  uses: actions/upload-artifact@v4.6.2
  with:
    name: python-wheel
    path: dist/*.whl
```

This enables automatic Python package building alongside the existing multi-platform library builds.