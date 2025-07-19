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
        definitions.extend(['WEBRTC_WIN', '_WIN32', 'NOMINMAX', '_USE_MATH_DEFINES'])
        libraries.extend(['winmm'])
        # Windows specific flags
        flags.extend(['/std:c++17', '/EHsc'])
    
    # Architecture-specific flags
    machine = platform.machine().lower()
    if machine in ['x86_64', 'amd64']:
        definitions.append('WEBRTC_ENABLE_AVX2')
        if platform.system() != 'Windows':
            flags.extend(['-mavx2', '-msse2'])
        else:
            # Windows 64-bit specific flags
            flags.extend(['/arch:AVX2'])
    elif machine in ['i386', 'i686', 'x86']:
        # Windows 32-bit support
        definitions.append('WEBRTC_ARCH_X86')
        if platform.system() == 'Windows':
            flags.extend(['/arch:SSE2'])
        else:
            flags.extend(['-msse2'])
    elif machine in ['arm64', 'aarch64']:
        definitions.extend(['WEBRTC_ARCH_ARM64', 'WEBRTC_HAS_NEON'])
    elif machine.startswith('arm'):
        definitions.extend(['WEBRTC_ARCH_ARM', 'WEBRTC_HAS_NEON'])
    
    return flags, definitions, libraries

# Simplified standalone implementation - no external WebRTC sources needed
def get_core_sources():
    """Get minimal sources for standalone implementation"""
    return []

def get_include_directories():
    """Get minimal include directories"""
    includes = [
        ".",
    ]
    return includes

# Get platform-specific configuration
compile_flags, definitions, libraries = get_platform_specific_flags()

# Use standalone implementation - no external sources needed
source_files = []

# Add Python binding source (standalone implementation)
source_files.append("python/webrtc_apm_standalone.cpp")

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