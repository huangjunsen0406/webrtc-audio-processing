"""
WebRTC Audio Processing Python Bindings

This package provides Python bindings for WebRTC audio processing functionality.
"""

try:
    # 导入C++扩展模块
    from .webrtc_apm import *
    __version__ = "2.1.0-test"
except ImportError:
    # 如果C++模块导入失败，提供一个纯Python的替代品用于测试
    class AudioProcessor:
        def __init__(self):
            self._enabled = False
            
        def set_enabled(self, enabled):
            self._enabled = enabled
            
        def is_enabled(self):
            return self._enabled
            
        def get_version(self):
            return "2.1.0-test-fallback"
            
        def process_audio(self, audio_data):
            return audio_data
    
    __version__ = "2.1.0-test-fallback"

__all__ = ["AudioProcessor", "__version__"]