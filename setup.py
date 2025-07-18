from setuptools import setup, find_packages
from pybind11.setup_helpers import Pybind11Extension, build_ext
import pybind11

# 定义扩展模块
ext_modules = [
    Pybind11Extension(
        "webrtc_apm.webrtc_apm",  # 包名.模块名
        [
            "python/simple_test.cpp",
        ],
        include_dirs=[
            pybind11.get_include(),
        ],
        language='c++',
        cxx_std=17,
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