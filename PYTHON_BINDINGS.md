# WebRTC Audio Processing Python Bindings

这个项目提供了WebRTC音频处理库的Python绑定，支持实时音频处理功能包括回声消除、噪声抑制和自动增益控制。

## 安装

### 方法1: 从GitHub Releases安装预构建的wheels

1. 访问 [Releases页面](https://github.com/your-username/webrtc-audio-processing/releases)
2. 下载适合您平台的wheel文件
3. 安装：
```bash
pip install webrtc_audio_processing-2.1.0-cp39-cp39-win_amd64.whl
```

### 方法2: 直接从GitHub安装

```bash
pip install git+https://github.com/your-username/webrtc-audio-processing.git
```

### 方法3: 从源码构建

```bash
git clone https://github.com/your-username/webrtc-audio-processing.git
cd webrtc-audio-processing
pip install .
```

## 快速开始

### 基本用法

```python
import webrtc_apm
import numpy as np

# 创建音频处理器
processor = webrtc_apm.AudioProcessor()

# 启用音频处理功能
processor.set_echo_cancellation_enabled(True)
processor.set_noise_suppression_enabled(True)
processor.set_gain_control_enabled(True)

# 处理音频流
# audio_data 应该是numpy数组，dtype为float32
sample_rate = 16000
processed_audio = processor.process_stream(audio_data, sample_rate)
```

### 使用配置类

```python
import webrtc_apm

# 创建配置对象
config = webrtc_apm.Config()

# 配置回声消除
config.echo_canceller.enabled = True
config.echo_canceller.mobile_mode = False

# 配置噪声抑制
config.noise_suppressor.enabled = True
config.noise_suppressor.level = 2  # 0-3, 数值越大抑制越强

# 配置自动增益控制
config.gain_controller.enabled = True
config.gain_controller.mode = 1  # 0: adaptive analog, 1: adaptive digital

# 应用配置（注意：这个功能需要在C++绑定中实现）
# processor.apply_config(config)
```

### 实时音频处理示例

```python
import webrtc_apm
import numpy as np
import pyaudio
import threading
import queue

class RealTimeAudioProcessor:
    def __init__(self):
        self.processor = webrtc_apm.AudioProcessor()
        self.processor.set_echo_cancellation_enabled(True)
        self.processor.set_noise_suppression_enabled(True)
        
        # 音频参数
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        
        # PyAudio设置
        self.p = pyaudio.PyAudio()
        self.audio_queue = queue.Queue()
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        """音频输入回调"""
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        
        # 处理音频
        processed_audio = self.processor.process_stream(audio_data, self.sample_rate)
        
        # 返回处理后的音频
        return (processed_audio.tobytes(), pyaudio.paContinue)
    
    def start_processing(self):
        """开始实时处理"""
        stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            output=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self.audio_callback
        )
        
        stream.start_stream()
        return stream

# 使用示例
processor = RealTimeAudioProcessor()
stream = processor.start_processing()

try:
    input("按Enter键停止处理...")
finally:
    stream.stop_stream()
    stream.close()
    processor.p.terminate()
```

## 支持的功能

### 音频处理功能

- **回声消除 (Echo Cancellation)**: 消除远端音频在本地的回声
- **噪声抑制 (Noise Suppression)**: 抑制背景噪声，提高语音清晰度
- **自动增益控制 (Automatic Gain Control)**: 自动调整音频音量

### 支持的音频格式

- **采样率**: 8kHz, 16kHz, 32kHz, 48kHz
- **声道数**: 1 (单声道), 2 (立体声)
- **数据类型**: 32位浮点数 (numpy.float32)

### 支持的平台

- **Windows**: x64 (Python 3.8-3.12)
- **macOS**: x64 & ARM64 (Python 3.8-3.12)
- **Linux**: x64 & ARM64 (Python 3.8-3.12)

## API 参考

### AudioProcessor类

#### 方法

- `AudioProcessor()`: 创建音频处理器实例
- `set_echo_cancellation_enabled(enabled: bool)`: 启用/禁用回声消除
- `set_noise_suppression_enabled(enabled: bool)`: 启用/禁用噪声抑制
- `set_gain_control_enabled(enabled: bool)`: 启用/禁用自动增益控制
- `process_stream(audio_data, sample_rate=16000, channels=1)`: 处理音频流
- `process_reverse_stream(audio_data, sample_rate=16000, channels=1)`: 处理反向音频流

### Config类

配置音频处理参数的类。

#### 属性

- `echo_canceller`: 回声消除配置
  - `enabled: bool`: 是否启用
  - `mobile_mode: bool`: 是否使用移动模式
- `noise_suppressor`: 噪声抑制配置
  - `enabled: bool`: 是否启用
  - `level: int`: 抑制级别 (0-3)
- `gain_controller`: 增益控制配置
  - `enabled: bool`: 是否启用
  - `mode: int`: 控制模式 (0: 自适应模拟, 1: 自适应数字)

### 常量

- `SAMPLE_RATE_8000`: 8kHz采样率
- `SAMPLE_RATE_16000`: 16kHz采样率
- `SAMPLE_RATE_32000`: 32kHz采样率
- `SAMPLE_RATE_48000`: 48kHz采样率

## 测试

运行测试脚本：

```bash
python test_python_bindings.py
```

## 开发

### 构建依赖

- Python 3.8+
- numpy
- pybind11
- meson
- ninja
- C++17编译器

### 从源码构建

```bash
git clone https://github.com/your-username/webrtc-audio-processing.git
cd webrtc-audio-processing

# 安装构建依赖
pip install meson ninja pybind11 numpy

# 构建
meson setup build -Dpython_bindings=true
ninja -C build

# 安装
pip install -e .
```

## 许可证

这个项目基于BSD-3-Clause许可证。详细信息请参考LICENSE文件。

## 贡献

欢迎贡献代码！请提交Pull Request或创建Issue。

## 支持

如果您遇到问题，请在GitHub上创建Issue。