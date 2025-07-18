"""
WebRTC Audio Processing Python Bindings

This package provides Python bindings for the WebRTC Audio Processing library,
enabling real-time audio processing including echo cancellation, noise suppression,
and automatic gain control.

Basic usage:
    >>> import webrtc_apm
    >>> processor = webrtc_apm.AudioProcessor()
    >>> processor.set_echo_cancellation_enabled(True)
    >>> processor.set_noise_suppression_enabled(True)
    >>> processed_audio = processor.process_stream(audio_data, sample_rate=16000)
"""

# 导入C++绑定模块
try:
    from .webrtc_apm import *
except ImportError as e:
    # 如果导入失败，提供更友好的错误信息
    raise ImportError(
        "Failed to import WebRTC Audio Processing bindings. "
        "Please ensure the package was installed correctly. "
        f"Original error: {e}"
    )

# 版本信息
__version__ = "2.1.0"

# 导出主要类和函数
__all__ = [
    "AudioProcessor",
    "Config",
    "EchoCanceller", 
    "NoiseSuppressor",
    "GainController",
    "SAMPLE_RATE_8000",
    "SAMPLE_RATE_16000", 
    "SAMPLE_RATE_32000",
    "SAMPLE_RATE_48000",
]