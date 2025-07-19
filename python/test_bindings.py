#!/usr/bin/env python3
"""
Test script for WebRTC Audio Processing Python bindings.
"""

import numpy as np
import sys
import traceback

def test_basic_functionality():
    """Test basic audio processing functionality."""
    print("Testing basic functionality...")
    
    try:
        import webrtc_audio_processing as wapm
        print(f"✓ Module imported successfully, version: {wapm.__version__}")
        
        # Create AudioProcessing instance
        apm = wapm.AudioProcessing()
        print("✓ AudioProcessing instance created")
        
        # Apply configuration
        apm.apply_config(
            echo_cancellation=True,
            noise_suppression=True,
            gain_control=True,
            high_pass_filter=True
        )
        print("✓ Configuration applied")
        
        # Test with different sample rates
        for sample_rate in [8000, 16000, 32000, 48000]:
            # Generate test audio (100ms of random audio)
            samples = sample_rate // 10  # 100ms
            audio_in = np.random.randint(-1000, 1000, samples, dtype=np.int16)
            
            # Process audio
            result = apm.process_stream(audio_in, sample_rate=sample_rate)
            
            # Verify result
            assert len(result) == len(audio_in), f"Output length mismatch for {sample_rate}Hz"
            assert result.dtype == np.int16, f"Output dtype mismatch for {sample_rate}Hz"
            print(f"✓ Processed {sample_rate}Hz audio successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_reverse_stream():
    """Test reverse stream processing."""
    print("\nTesting reverse stream processing...")
    
    try:
        import webrtc_audio_processing as wapm
        
        apm = wapm.AudioProcessing()
        apm.apply_config(echo_cancellation=True)
        
        # Generate test audio
        audio_data = np.random.randint(-500, 500, 1600, dtype=np.int16)  # 100ms at 16kHz
        
        # Process reverse stream (speaker audio)
        result = apm.process_reverse_stream(audio_data)
        
        assert len(result) == len(audio_data), "Reverse stream output length mismatch"
        assert result.dtype == np.int16, "Reverse stream output dtype mismatch"
        print("✓ Reverse stream processing successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Reverse stream test failed: {e}")
        traceback.print_exc()
        return False

def test_gain_control():
    """Test automatic gain control functionality."""
    print("\nTesting gain control...")
    
    try:
        import webrtc_audio_processing as wapm
        
        apm = wapm.AudioProcessing()
        apm.apply_config(gain_control=True)
        
        # Set initial analog level
        apm.set_stream_analog_level(128)
        
        # Generate quiet audio
        quiet_audio = np.full(1600, 100, dtype=np.int16)  # Very quiet signal
        
        # Process multiple frames
        for i in range(5):
            result = apm.process_stream(quiet_audio)
            recommended_level = apm.recommended_stream_analog_level()
            print(f"  Frame {i+1}: Recommended level = {recommended_level}")
            apm.set_stream_analog_level(recommended_level)
        
        print("✓ Gain control test successful")
        return True
        
    except Exception as e:
        print(f"✗ Gain control test failed: {e}")
        traceback.print_exc()
        return False

def test_statistics():
    """Test statistics reporting."""
    print("\nTesting statistics...")
    
    try:
        import webrtc_audio_processing as wapm
        
        apm = wapm.AudioProcessing()
        apm.apply_config(echo_cancellation=True, residual_echo_detector=True)
        
        # Generate some audio
        audio_data = np.random.randint(-1000, 1000, 1600, dtype=np.int16)
        
        # Process a few frames
        for _ in range(3):
            apm.process_stream(audio_data)
        
        # Get statistics
        stats = apm.get_statistics()
        print(f"✓ Statistics retrieved: {stats}")
        
        # Check echo detection
        has_echo = apm.stream_has_echo()
        print(f"✓ Echo detection status: {has_echo}")
        
        return True
        
    except Exception as e:
        print(f"✗ Statistics test failed: {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling."""
    print("\nTesting error handling...")
    
    try:
        import webrtc_audio_processing as wapm
        
        apm = wapm.AudioProcessing()
        
        # Test invalid sample rate
        try:
            audio_data = np.random.randint(-1000, 1000, 1000, dtype=np.int16)
            apm.process_stream(audio_data, sample_rate=44100)  # Invalid sample rate
            print("✗ Should have raised error for invalid sample rate")
            return False
        except RuntimeError:
            print("✓ Correctly caught invalid sample rate error")
        
        # Test invalid array dimension
        try:
            audio_2d = np.random.randint(-1000, 1000, (100, 2), dtype=np.int16)
            apm.process_stream(audio_2d)
            print("✗ Should have raised error for 2D array")
            return False
        except RuntimeError:
            print("✓ Correctly caught 2D array error")
        
        # Test invalid delay
        try:
            apm.set_stream_delay_ms(1000)  # Too high
            print("✗ Should have raised error for invalid delay")
            return False
        except RuntimeError:
            print("✓ Correctly caught invalid delay error")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("WebRTC Audio Processing Python Bindings Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_functionality,
        test_reverse_stream,
        test_gain_control,
        test_statistics,
        test_error_handling,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())