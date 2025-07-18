from setuptools import setup, find_packages
from pybind11.setup_helpers import Pybind11Extension, build_ext
import pybind11
import os
import platform

def get_platform_specific_flags():
    """Get platform-specific compiler flags and definitions"""
    flags = []
    definitions = []
    libraries = []
    
    # Common definitions
    definitions.extend([
        'WEBRTC_LIBRARY_IMPL',
        'WEBRTC_ENABLE_SYMBOL_EXPORT',
        'WEBRTC_APM_DEBUG_DUMP=0',
        'NDEBUG',
    ])
    
    # Platform-specific flags
    if platform.system() == 'Darwin':  # macOS
        definitions.extend(['WEBRTC_MAC', 'WEBRTC_POSIX'])
        flags.extend(['-stdlib=libc++'])
    elif platform.system() == 'Linux':
        definitions.extend(['WEBRTC_LINUX', 'WEBRTC_POSIX'])
        libraries.extend(['rt', 'pthread'])
    elif platform.system() == 'Windows':
        definitions.extend(['WEBRTC_WIN', '_WIN32', 'NOMINMAX'])
        libraries.extend(['winmm'])
    
    # Architecture-specific flags
    machine = platform.machine().lower()
    if machine in ['x86_64', 'amd64']:
        definitions.append('WEBRTC_ENABLE_AVX2')
        if platform.system() != 'Windows':
            flags.extend(['-mavx2', '-msse2'])
    elif machine in ['arm64', 'aarch64']:
        definitions.extend(['WEBRTC_ARCH_ARM64', 'WEBRTC_HAS_NEON'])
    
    return flags, definitions, libraries

def get_core_sources():
    """Get core WebRTC sources for compilation"""
    base_path = "webrtc"
    
    # Core sources needed for basic functionality
    core_sources = [
        # Main audio processing
        "modules/audio_processing/audio_buffer.cc",
        "modules/audio_processing/audio_processing_impl.cc",
        "modules/audio_processing/high_pass_filter.cc",
        "modules/audio_processing/splitting_filter.cc",
        "modules/audio_processing/three_band_filter_bank.cc",
        
        # Basic echo cancellation
        "modules/audio_processing/aec3/echo_canceller3.cc",
        "modules/audio_processing/aec3/aec3_common.cc",
        "modules/audio_processing/aec3/aec3_fft.cc",
        "modules/audio_processing/aec3/block_processor.cc",
        "modules/audio_processing/aec3/echo_remover.cc",
        "modules/audio_processing/aec3/render_delay_buffer.cc",
        "modules/audio_processing/aec3/render_delay_controller.cc",
        "modules/audio_processing/aec3/subtractor.cc",
        "modules/audio_processing/aec3/suppression_filter.cc",
        
        # Noise suppression
        "modules/audio_processing/ns/noise_suppressor.cc",
        "modules/audio_processing/ns/ns_fft.cc",
        "modules/audio_processing/ns/prior_signal_model.cc",
        "modules/audio_processing/ns/wiener_filter.cc",
        
        # Gain control
        "modules/audio_processing/agc/agc.cc",
        "modules/audio_processing/agc2/gain_controller2.cc",
        "modules/audio_processing/agc2/adaptive_digital_gain_applier.cc",
        "modules/audio_processing/agc2/gain_applier.cc",
        
        # Common audio utilities
        "common_audio/audio_util.cc",
        "common_audio/channel_buffer.cc",
        "common_audio/fir_filter_c.cc",
        "common_audio/fir_filter_factory.cc",
        "common_audio/ring_buffer.cc",
        
        # Signal processing
        "common_audio/signal_processing/real_fft.cc",
        "common_audio/signal_processing/spl_init.cc",
        "common_audio/signal_processing/splitting_filter.cc",
        "common_audio/signal_processing/cross_correlation.cc",
        
        # API
        "api/audio/audio_frame.cc",
        "api/audio/audio_processing.cc",
        "api/audio/echo_canceller3_config.cc",
        "api/audio/echo_canceller3_factory.cc",
        
        # RTC Base
        "rtc_base/checks.cc",
        "rtc_base/logging.cc",
        "rtc_base/string_utils.cc",
        "rtc_base/time_utils.cc",
        "rtc_base/memory/aligned_malloc.cc",
        
        # System wrappers
        "system_wrappers/source/cpu_features.cc",
        "system_wrappers/source/field_trial.cc",
        "system_wrappers/source/metrics.cc",
        
        # Third-party
        "third_party/pffft/src/pffft.c",
        "modules/third_party/fft/fft.c",
    ]
    
    # Convert to full paths and check existence
    source_files = []
    for source in core_sources:
        full_path = os.path.join(base_path, source)
        if os.path.exists(full_path):
            source_files.append(full_path)
        else:
            print(f"Warning: Source file not found: {full_path}")
    
    # Add export wrapper if it exists
    if os.path.exists("export/export.cc"):
        source_files.append("export/export.cc")
    
    return source_files

def get_include_directories():
    """Get all include directories"""
    includes = [
        ".",
        "webrtc",
        "webrtc/modules/audio_processing/include",
        "webrtc/api",
        "webrtc/rtc_base",
        "webrtc/common_audio/include",
        "webrtc/system_wrappers/include",
        "webrtc/third_party/pffft/src",
        "webrtc/modules/third_party/fft",
    ]
    return includes

# Get platform-specific configuration
compile_flags, definitions, libraries = get_platform_specific_flags()

# Get source files
source_files = get_core_sources()

# Add Python binding source
source_files.append("python/webrtc_apm_simple.cpp")

print(f"Found {len(source_files)} source files")
print(f"Compile flags: {compile_flags}")
print(f"Definitions: {definitions}")

# 定义扩展模块
ext_modules = [
    Pybind11Extension(
        "webrtc_apm.webrtc_apm",  # 包名.模块名
        source_files,
        include_dirs=[
            pybind11.get_include(),
        ] + get_include_directories(),
        define_macros=[(d.split('=')[0], d.split('=')[1] if '=' in d else None) for d in definitions],
        libraries=libraries,
        language='c++',
        cxx_std=17,
        extra_compile_args=compile_flags + ['-O2', '-ffast-math'],
        extra_link_args=['-O2'],
    ),
]

setup(
    name="webrtc_audio_processing",
    version="2.1.0",
    author="WebRTC Audio Processing Contributors",
    author_email="",
    description="WebRTC Audio Processing Python Bindings",
    long_description="WebRTC Audio Processing Python Bindings for real-time audio processing",
    packages=find_packages(),
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.19.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: C++",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)