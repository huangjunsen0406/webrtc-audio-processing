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
    # WebRTC library directories and libraries
    if platform.system() == "Windows":
        # Windows uses shared libraries
        library_dirs = [f"./{build_dir}/webrtc/modules/audio_processing"]
        libraries = ["webrtc-audio-processing-2"]
    else:
        # Unix uses static libraries with all components
        library_dirs = [
            f"./{build_dir}/webrtc/modules/audio_processing",
            f"./{build_dir}/webrtc/api", 
            f"./{build_dir}/webrtc/common_audio",
            f"./{build_dir}/webrtc/rtc_base",
            f"./{build_dir}/webrtc/modules/third_party/fft",
            f"./{build_dir}/webrtc/third_party/pffft",
            f"./{build_dir}/webrtc/third_party/rnnoise"
        ]
        libraries = [
            "webrtc-audio-processing-2",
            "libapi", 
            "common_audio",
            "libbase",
            "libfft",
            "libpffft", 
            "librnnoise"
        ]

# Function to get pkg-config information
def get_pkg_config(library, option):
    try:
        result = subprocess.run(['pkg-config', option, library], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip().split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

# Get Abseil dependencies via pkg-config or use built-in static libraries
absl_include_dirs = []
absl_library_dirs = []
absl_libraries = []

# Try pkg-config first
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

# If pkg-config didn't find libraries, use built-in static libraries
if not absl_libraries and not building_sdist:
    absl_subproj_dir = f"./{build_dir}/subprojects"
    if os.path.exists(absl_subproj_dir):
        # Find abseil subproject directory
        for item in os.listdir(absl_subproj_dir):
            if item.startswith("abseil-cpp"):
                absl_dir = os.path.join(absl_subproj_dir, item)
                if os.path.exists(absl_dir):
                    absl_library_dirs.append(absl_dir)
                    # Add required Abseil libraries
                    absl_libraries.extend([
                        'absl_base', 'absl_flags', 'absl_strings', 'absl_numeric',
                        'absl_synchronization', 'absl_bad_optional_access', 'absl_time',
                        'absl_civil_time', 'absl_time_zone', 'absl_int128', 
                        'absl_throw_delegate', 'absl_raw_logging_internal', 'absl_log_severity',
                        'absl_spinlock_wait', 'absl_strings_internal', 'absl_string_view'
                    ])
                break

# Platform-specific library settings
if platform.system() == "Windows":
    extra_link_args = []
    extra_compile_args = ["/std:c++20"]
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
                # For Windows, don't add Abseil libraries here - they will be linked dynamically
                # or included in the WebRTC DLL
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
                    break
else:
    extra_link_args = ["-std=c++20"]
    extra_compile_args = ["-std=c++20"]
    # Fallback include paths for Unix systems
    if not absl_include_dirs:
        possible_paths = [
            "/usr/local/include",  # Prioritize /usr/local for newer versions
            "/usr/include",
            "/opt/homebrew/include",  # Apple Silicon Homebrew
            "/usr/local/opt/abseil/include"  # Intel Homebrew
        ]
        for path in possible_paths:
            absl_path = os.path.join(path, "absl")
            if os.path.exists(absl_path):
                # Check for a specific header that should exist in newer versions
                nullability_header = os.path.join(absl_path, "base", "nullability.h")
                if os.path.exists(nullability_header):
                    absl_include_dirs.append(path)
                    # Add corresponding library paths
                    if "/opt/homebrew" in path:
                        absl_library_dirs.append("/opt/homebrew/lib")
                    elif "/usr/local/opt/abseil" in path:
                        absl_library_dirs.append("/usr/local/opt/abseil/lib")
                    elif "/usr/local" in path:
                        absl_library_dirs.append("/usr/local/lib")
                    elif "/usr" in path:
                        absl_library_dirs.append("/usr/lib")
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
if platform.system() == "Windows":
    # On Windows with shared library, Abseil should be included in the WebRTC DLL
    all_libraries = libraries
else:
    # On Unix with static libraries, need to link Abseil separately
    all_libraries = libraries + absl_libraries

# Setup for packaging DLLs on Windows
package_data = {}
if platform.system() == "Windows" and not building_sdist:
    import glob
    dll_pattern = f"./{build_dir}/webrtc/modules/audio_processing/*.dll"
    dll_files = glob.glob(dll_pattern)
    if dll_files:
        package_data["webrtc_audio_processing"] = [os.path.basename(f) for f in dll_files]
        # Copy DLLs to package directory
        import shutil
        os.makedirs("webrtc_audio_processing", exist_ok=True)
        for dll_file in dll_files:
            shutil.copy2(dll_file, "webrtc_audio_processing/")

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
        cxx_std=20,
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
    package_data=package_data,
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