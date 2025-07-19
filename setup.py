from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext
import pybind11
import os
import platform
import subprocess

# Determine the library name and build directory
# For sdist builds, we don't need the build directory
import sys
building_sdist = 'sdist' in sys.argv or 'egg_info' in sys.argv

if building_sdist:
    build_dir = "build_cpp"  # Default for sdist
    library_dirs = []
    libraries = []
else:
    if os.path.exists("build_cpp"):
        build_dir = "build_cpp"
    elif os.path.exists("build"):
        build_dir = "build"
    else:
        raise RuntimeError(
            "No build directory found. Please run 'meson setup build_cpp' first."
        )
    library_dirs = [f"./{build_dir}"]
    libraries = ["webrtc_audio_processing"]

# Function to get pkg-config information
def get_pkg_config(library, option):
    try:
        result = subprocess.run(['pkg-config', option, library], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

# Get Abseil dependencies via pkg-config
absl_include_dirs = []
absl_library_dirs = []
absl_libraries = []

for lib in ['absl_base', 'absl_flags', 'absl_strings', 'absl_numeric', 
            'absl_synchronization', 'absl_bad_optional_access']:
    inc_flags = get_pkg_config(lib, '--cflags-only-I')
    absl_include_dirs.extend([flag[2:] for flag in inc_flags if flag.startswith('-I')])
    
    lib_flags = get_pkg_config(lib, '--libs')
    for flag in lib_flags:
        if flag.startswith('-L'):
            absl_library_dirs.append(flag[2:])
        elif flag.startswith('-l'):
            absl_libraries.append(flag[2:])

# Platform-specific library settings
if platform.system() == "Windows":
    extra_link_args = []
    extra_compile_args = ["/std:c++17"]
    # Windows vcpkg paths (common locations)
    if not absl_include_dirs:
        # Check current directory first (GitHub Actions)
        current_vcpkg_path = "./vcpkg/installed/x64-windows/include"
        if os.path.exists(current_vcpkg_path):
            absl_include_dirs.append(current_vcpkg_path)
            # Also add library path
            lib_path = "./vcpkg/installed/x64-windows/lib"
            if os.path.exists(lib_path):
                absl_library_dirs.append(lib_path)
            # Add required Abseil libraries for Windows vcpkg
            absl_libraries.extend([
                'absl_base', 'absl_flags', 'absl_strings', 'absl_numeric',
                'absl_synchronization', 'absl_bad_optional_access', 'absl_time'
            ])
        else:
            # Fallback to system vcpkg paths
            possible_vcpkg_paths = [
                "C:/vcpkg/installed/x64-windows/include",
                "C:/vcpkg/installed/x86-windows/include"
            ]
            for path in possible_vcpkg_paths:
                if os.path.exists(path):
                    absl_include_dirs.append(path)
                    # Also add corresponding library path
                    lib_path = path.replace("/include", "/lib")
                    if os.path.exists(lib_path):
                        absl_library_dirs.append(lib_path)
                    # Add required Abseil libraries for Windows vcpkg
                    absl_libraries.extend([
                        'absl_base', 'absl_flags', 'absl_strings', 'absl_numeric',
                        'absl_synchronization', 'absl_bad_optional_access', 'absl_time'
                    ])
                    break
else:
    extra_link_args = ["-std=c++17"]
    extra_compile_args = ["-std=c++17"]
    # Fallback include paths for Unix systems
    if not absl_include_dirs:
        possible_paths = [
            "/usr/include",
            "/usr/local/include", 
            "/opt/homebrew/include",  # Apple Silicon Homebrew
            "/usr/local/opt/abseil/include"  # Intel Homebrew
        ]
        for path in possible_paths:
            if os.path.exists(os.path.join(path, "absl")):
                absl_include_dirs.append(path)
                # Add corresponding library paths for macOS homebrew
                if "/opt/homebrew" in path:
                    absl_library_dirs.append("/opt/homebrew/lib")
                elif "/usr/local/opt/abseil" in path:
                    absl_library_dirs.append("/usr/local/opt/abseil/lib")
                elif "/usr/local" in path:
                    absl_library_dirs.append("/usr/local/lib")
                # Add required Abseil libraries if not found via pkg-config
                if not absl_libraries:
                    absl_libraries.extend([
                        'absl_base', 'absl_flags', 'absl_strings', 'absl_numeric',
                        'absl_synchronization', 'absl_bad_optional_access', 'absl_time'
                    ])
                break

# Combine include directories
all_include_dirs = [
    ".",
    "webrtc",
    pybind11.get_include(),
] + absl_include_dirs

# Combine library directories and libraries
all_library_dirs = library_dirs + absl_library_dirs
all_libraries = libraries + absl_libraries

ext_modules = [
    Pybind11Extension(
        "webrtc_audio_processing",
        [
            "python/bindings.cpp",
        ],
        include_dirs=all_include_dirs,
        libraries=all_libraries,
        library_dirs=all_library_dirs,
        language="c++",
        cxx_std=17,
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        define_macros=[("VERSION_INFO", '"2.1.0"')],
    ),
]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="webrtc-audio-processing",
    version="2.1.0",
    author="WebRTC Audio Processing Team",
    author_email="",
    description="Python bindings for WebRTC Audio Processing library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/huangjunsen0406/webrtc-audio-processing",
    project_urls={
        "Bug Tracker": "https://github.com/huangjunsen0406/webrtc-audio-processing/issues",
        "Documentation": "https://github.com/huangjunsen0406/webrtc-audio-processing",
        "Source Code": "https://github.com/huangjunsen0406/webrtc-audio-processing",
    },
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.19.0",
    ],
    extras_require={
        "test": ["pytest>=6.0", "numpy"],
        "dev": ["pytest>=6.0", "numpy", "pybind11[global]"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C++",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="webrtc audio processing echo cancellation noise suppression gain control",
)