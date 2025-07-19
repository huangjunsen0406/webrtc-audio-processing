# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a C/C++ audio processing library that provides a Linux packaging-friendly version of WebRTC's AudioProcessing module. The project offers echo cancellation, noise suppression, automatic gain control, and other audio processing features as a standalone library.

**Key Facts:**
- Language: C/C++ (C++17 standard)
- Build system: Meson
- Version: 2.1
- Purpose: Standalone WebRTC audio processing for easy integration

## Common Commands

### Building
```bash
# Initialize build directory with local install prefix
meson . build -Dprefix=$PWD/install

# Build the library
ninja -C build

# Install locally
ninja -C build install
```

### Build Options
```bash
# Enable NEON optimizations (auto-detected)
meson . build -Dneon=enabled

# Disable inline SSE optimizations
meson . build -Dinline-sse=false

# Android builds with gnustl
meson . build -Dgnustl=enabled
```

### Running Examples
```bash
# Build examples (included in main build)
ninja -C build

# Run offline processing example
./build/examples/run-offline <play_file> <rec_file> <out_file>
```

### Testing and Validation
**Note: This project has minimal testing infrastructure as it's primarily a packaging fork of upstream WebRTC.**

```bash
# Validate pkg-config files work correctly
pkg-config --cflags --libs webrtc-audio-processing-2

# CI validation commands (from .gitlab-ci.yml)
ninja -C build
pkg-config --cflags --libs webrtc-audio-processing-2
```

### Field Trial Management
```bash
# Validate WebRTC field trial configurations
python3 webrtc/experiments/field_trials.py <field_trial_config>
```

## Code Architecture

### Core Structure
- `/webrtc/` - Main WebRTC source code (mirrors upstream structure)
- `/export/` - C API wrapper for easier integration
- `/examples/` - Sample usage demonstrating the library

### Key Components
- `/webrtc/modules/audio_processing/` - Main audio processing algorithms
  - `aec3/` - Echo Canceller 3 (primary echo cancellation)
  - `agc/` and `agc2/` - Automatic Gain Control implementations
  - `ns/` - Noise Suppression
  - `aecm/` - Mobile Echo Canceller (simpler version)
- `/webrtc/common_audio/` - Signal processing utilities and audio format handling
- `/webrtc/rtc_base/` - Platform abstractions and base utilities
- `/webrtc/api/` - Public API definitions

### Dependencies
- **Abseil C++** - Google's C++ common libraries (required, version >=20240722)
- Platform-specific libraries automatically detected (threads, rt, winmm, etc.)

### Platform Support
The build system automatically detects and configures for:
- Linux (primary target) - requires rt library and threads
- macOS/Darwin/iOS - uses platform-specific audio frameworks  
- Windows - MinGW and MSVC support with winmm
- Android - supports gnustl C++ library
- BSD variants (FreeBSD, OpenBSD, NetBSD, DragonFly)
- ARM/ARM64 with NEON optimizations
- x86/x86_64 with SSE/AVX2 optimizations

### API Layers
1. **C++ API** - Native WebRTC AudioProcessing interface in `/webrtc/modules/audio_processing/include/`
2. **C API** - Wrapper in `/export/` for easier language bindings
3. **Python bindings** - Work in progress (untracked files suggest active development)

## Development Notes

### Testing Philosophy
This project has minimal testing infrastructure as it's primarily a packaging fork of upstream WebRTC. Testing of core functionality happens in the upstream WebRTC project. Local validation focuses on:
- Build system functionality across platforms
- pkg-config file generation and usability
- Library linkage verification

### Upstream Sync Process
This project tracks upstream WebRTC from Chromium. The sync process involves:
1. Check DEPS file in Chromium tree for current WebRTC commit hash
2. Use Meld to diff directories between this repo and upstream
3. Preserve hand-modified files while updating others
4. BUILD.gn files are copied for reference but Meson is the actual build system

### Code Conventions
- Follow WebRTC upstream code style and patterns
- Minimal changes to core WebRTC code for easy upstream tracking
- Platform-specific adaptations handled through build system configuration
- C++17 standard used throughout

### Architecture Optimizations
- SIMD optimizations automatically enabled based on target architecture
- AVX2 code compiled separately with runtime detection
- NEON support for ARM platforms with automatic detection
- SSE code can be disabled via build options for older x86 systems

The library is designed for production use and provides comprehensive audio processing capabilities while maintaining compatibility with the upstream WebRTC project.