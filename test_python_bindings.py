#!/usr/bin/env python3
"""
测试WebRTC Audio Processing Python绑定的简单脚本
"""

import numpy as np
import webrtc_apm

def test_basic_functionality():
    """测试基本功能"""
    print("Testing WebRTC Audio Processing Python bindings...")
    
    # 创建音频处理器
    processor = webrtc_apm.AudioProcessor()
    print("✓ AudioProcessor created successfully")
    
    # 启用各种功能
    processor.set_echo_cancellation_enabled(True)
    processor.set_noise_suppression_enabled(True)
    processor.set_gain_control_enabled(True)
    print("✓ Audio processing features enabled")
    
    # 创建测试音频数据
    sample_rate = 16000
    duration = 1.0  # 1秒
    samples = int(sample_rate * duration)
    
    # 生成测试音频：正弦波 + 噪声
    t = np.linspace(0, duration, samples)
    frequency = 440  # A4音符
    audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    audio_data += 0.1 * np.random.normal(0, 1, samples).astype(np.float32)
    
    print(f"✓ Generated test audio: {samples} samples at {sample_rate}Hz")
    
    # 处理音频
    processed_audio = processor.process_stream(audio_data, sample_rate)
    print(f"✓ Audio processed successfully: {len(processed_audio)} samples")
    
    # 验证输出
    assert len(processed_audio) == len(audio_data), "Output length mismatch"
    assert processed_audio.dtype == np.float32, "Output dtype mismatch"
    
    print("✓ All tests passed!")
    
    return True

def test_config_class():
    """测试配置类"""
    print("\nTesting Config class...")
    
    config = webrtc_apm.Config()
    
    # 配置回声消除
    config.echo_canceller.enabled = True
    config.echo_canceller.mobile_mode = False
    
    # 配置噪声抑制
    config.noise_suppressor.enabled = True
    config.noise_suppressor.level = 2
    
    # 配置增益控制
    config.gain_controller.enabled = True
    config.gain_controller.mode = 1
    
    print("✓ Config class works correctly")
    
    return True

def test_multichannel_audio():
    """测试多声道音频"""
    print("\nTesting multichannel audio processing...")
    
    processor = webrtc_apm.AudioProcessor()
    
    # 创建立体声测试数据
    sample_rate = 16000
    duration = 0.5
    samples = int(sample_rate * duration)
    channels = 2
    
    # 生成立体声音频
    audio_data = np.random.normal(0, 0.1, (samples, channels)).astype(np.float32)
    
    # 处理立体声音频
    processed_audio = processor.process_stream(audio_data, sample_rate, channels)
    
    assert processed_audio.shape == audio_data.shape, "Multichannel shape mismatch"
    print("✓ Multichannel audio processing works")
    
    return True

def main():
    """主函数"""
    try:
        print(f"WebRTC Audio Processing Python bindings v{webrtc_apm.__version__}")
        print("=" * 60)
        
        test_basic_functionality()
        test_config_class()
        test_multichannel_audio()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        print("\nExample usage:")
        print("  import webrtc_apm")
        print("  processor = webrtc_apm.AudioProcessor()")
        print("  processor.set_echo_cancellation_enabled(True)")
        print("  processed = processor.process_stream(audio_data, 16000)")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)