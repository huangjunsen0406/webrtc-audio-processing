# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Linux packaging-friendly copy of the AudioProcessing module from the WebRTC project. The primary goal is to provide a reusable audio processing library while maintaining compatibility with upstream WebRTC code.

## Build System

The project uses Meson as the build system. Key commands:

### Basic Build
```bash
# Initialize build directory with prefix
meson . build -Dprefix=$PWD/install

# Build the project
ninja -C build

# Install locally
ninja -C build install
```

### Cross-compilation
```bash
# Android ARM v7a build
meson setup --wipe build --cross-file android_armv7a.txt
meson compile -C build

# Windows build (using Visual Studio)
cmd.exe /c "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" -arch=amd64 && bash
```

### Build Options
- `gnustl`: Use gnustl for C++ library implementation (Android only)
- `neon`: Enable NEON optimizations (auto-detected)
- `inline-sse`: Enable inline SSE/SSE2 optimizations (default: true)

## Code Architecture

### Core Components

1. **AudioProcessing Module** (`webrtc/api/audio/audio_processing.h`):
   - Main API entry point for audio processing
   - Provides echo cancellation, noise suppression, and gain control
   - Operates on ~10ms audio frames

2. **AudioProcessingImpl** (`webrtc/modules/audio_processing/audio_processing_impl.h`):
   - Primary implementation of the AudioProcessing interface
   - Handles component initialization and stream processing

3. **Key Processing Components**:
   - **AEC3** (`webrtc/modules/audio_processing/aec3/`): Echo Canceller 3 implementation
   - **AGC** (`webrtc/modules/audio_processing/agc/`): Automatic Gain Control
   - **NS** (`webrtc/modules/audio_processing/ns/`): Noise Suppression
   - **AECM** (`webrtc/modules/audio_processing/aecm/`): Acoustic Echo Canceller for Mobile

### Directory Structure

- `webrtc/api/audio/`: Public API headers
- `webrtc/modules/audio_processing/`: Core audio processing implementation
- `webrtc/common_audio/`: Common audio utilities and signal processing
- `webrtc/rtc_base/`: Base utilities and system abstractions
- `webrtc/system_wrappers/`: System-specific wrappers
- `webrtc/third_party/`: Third-party dependencies (pffft, rnnoise)
- `examples/`: Example usage code
- `export/`: Export functionality

### Platform Support

The build system supports multiple platforms with specific optimizations:
- Linux: Uses threads and rt library
- Android: Includes logging support and optional gnustl
- Windows: MinGW and MSVC support with Windows-specific definitions
- macOS/iOS: Platform-specific optimizations
- BSD systems: FreeBSD, OpenBSD, NetBSD support

### Architecture-Specific Features

- **x86/x86_64**: AVX2 and optional inline SSE support
- **ARM/ARM64**: NEON optimizations
- **MIPS**: MIPS-specific optimizations

## Development Workflow

### Testing PulseAudio Integration
```bash
# Install with prefix
meson build -Dprefix=$(pwd)/install
ninja -C build install

# Configure PulseAudio to use prefixed install
meson build -Dpkg_config_path=/path/to/webrtc-audio-processing/install/lib64/pkgconfig/
ninja -C build
```

### Updating from Upstream
1. Check the current WebRTC revision used by Chromium
2. Use tools like Meld to diff `webrtc-audio-processing/webrtc` against `chromium/third_party/webrtc`
3. Copy new changes while preserving local modifications
4. Update `meson.build` files for any new dependencies
5. Test build and functionality

## Key Files

- `webrtc/api/audio/audio_processing.h`: Main public API
- `webrtc/modules/audio_processing/audio_processing_impl.h`: Core implementation
- `meson.build`: Root build configuration
- `meson_options.txt`: Build options
- `UPDATING.md`: Instructions for maintaining upstream sync