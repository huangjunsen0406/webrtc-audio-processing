from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext
import pybind11
import os
import platform

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

# Platform-specific library settings
if platform.system() == "Windows":
    extra_link_args = []
    extra_compile_args = ["/std:c++17"]
else:
    extra_link_args = ["-std=c++17"]
    extra_compile_args = ["-std=c++17"]

ext_modules = [
    Pybind11Extension(
        "webrtc_audio_processing",
        [
            "python/bindings.cpp",
        ],
        include_dirs=[
            ".",
            "webrtc",
            pybind11.get_include(),
        ],
        libraries=libraries,
        library_dirs=library_dirs,
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