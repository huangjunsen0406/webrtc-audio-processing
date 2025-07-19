#!/usr/bin/env python3
"""
Example usage of WebRTC Audio Processing Python bindings.

This example demonstrates:
1. Basic audio processing setup
2. Real-time audio processing simulation
3. Echo cancellation with render stream
4. Automatic gain control
5. Statistics monitoring
"""

import numpy as np
import matplotlib.pyplot as plt
import time

def generate_audio_with_echo(duration_ms=1000, sample_rate=16000, echo_delay_ms=100):
    """Generate test audio with simulated echo."""
    samples = int(duration_ms * sample_rate / 1000)
    
    # Generate original signal (sine wave + noise)
    t = np.linspace(0, duration_ms/1000, samples)
    original = (1000 * np.sin(2 * np.pi * 440 * t) +  # 440Hz tone
                200 * np.random.randn(samples))  # noise
    
    # Add echo
    echo_delay_samples = int(echo_delay_ms * sample_rate / 1000)
    echo = np.zeros_like(original)
    if echo_delay_samples < len(original):
        echo[echo_delay_samples:] = 0.3 * original[:-echo_delay_samples]
    
    # Combine original + echo
    combined = original + echo
    
    # Convert to int16
    combined = np.clip(combined, -32767, 32767).astype(np.int16)
    original = np.clip(original, -32767, 32767).astype(np.int16)
    
    return original, combined

def basic_audio_processing_example():
    """Basic audio processing example."""
    print("=== Basic Audio Processing Example ===")
    
    try:
        import webrtc_audio_processing as wapm
        
        # Create audio processor
        apm = wapm.AudioProcessing()
        
        # Configure features
        apm.apply_config(
            echo_cancellation=True,
            noise_suppression=True,
            gain_control=True,
            high_pass_filter=True
        )
        print("✓ Audio processor configured")
        
        # Generate test audio (noisy signal)
        sample_rate = 16000
        duration_ms = 500
        samples = int(duration_ms * sample_rate / 1000)
        
        # Create noisy audio signal
        t = np.linspace(0, duration_ms/1000, samples)
        clean_signal = 2000 * np.sin(2 * np.pi * 800 * t)  # 800Hz tone
        noise = 500 * np.random.randn(samples)  # noise
        noisy_audio = (clean_signal + noise).astype(np.int16)
        
        # Process audio
        processed_audio = apm.process_stream(noisy_audio, sample_rate=sample_rate)
        
        # Calculate noise reduction
        original_power = np.mean(noisy_audio.astype(float) ** 2)
        processed_power = np.mean(processed_audio.astype(float) ** 2)
        
        print(f"Original signal power: {original_power:.2f}")
        print(f"Processed signal power: {processed_power:.2f}")
        print(f"Power ratio: {processed_power/original_power:.3f}")
        
        return noisy_audio, processed_audio
        
    except ImportError:
        print("✗ webrtc_audio_processing module not found. Please install it first.")
        return None, None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None, None

def echo_cancellation_example():
    """Echo cancellation example with render stream."""
    print("\n=== Echo Cancellation Example ===")
    
    try:
        import webrtc_audio_processing as wapm
        
        # Create audio processor
        apm = wapm.AudioProcessing()
        apm.apply_config(echo_cancellation=True)
        
        # Generate audio with echo
        original, with_echo = generate_audio_with_echo(duration_ms=1000, echo_delay_ms=100)
        
        print(f"Generated {len(with_echo)} samples with simulated echo")
        
        # Process in chunks (simulate real-time processing)
        chunk_size = 160  # 10ms at 16kHz
        processed_chunks = []
        
        for i in range(0, len(with_echo), chunk_size):
            chunk = with_echo[i:i+chunk_size]
            if len(chunk) < chunk_size:
                # Pad last chunk
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)), 'constant')
            
            # Process render stream (what speaker plays)
            render_chunk = original[i:i+chunk_size]
            if len(render_chunk) < chunk_size:
                render_chunk = np.pad(render_chunk, (0, chunk_size - len(render_chunk)), 'constant')
            
            apm.process_reverse_stream(render_chunk)
            
            # Process capture stream (what microphone records)
            processed_chunk = apm.process_stream(chunk)
            processed_chunks.append(processed_chunk)
        
        # Combine processed chunks
        processed_audio = np.concatenate(processed_chunks)[:len(with_echo)]
        
        # Calculate echo reduction
        echo_power_original = np.mean((with_echo - original).astype(float) ** 2)
        echo_power_processed = np.mean((processed_audio - original).astype(float) ** 2)
        
        print(f"Echo power before processing: {echo_power_original:.2f}")
        print(f"Echo power after processing: {echo_power_processed:.2f}")
        print(f"Echo reduction: {echo_power_original/echo_power_processed:.2f}x")
        
        return original, with_echo, processed_audio
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return None, None, None

def gain_control_example():
    """Automatic gain control example."""
    print("\n=== Automatic Gain Control Example ===")
    
    try:
        import webrtc_audio_processing as wapm
        
        # Create audio processor
        apm = wapm.AudioProcessing()
        apm.apply_config(gain_control=True, echo_cancellation=False, noise_suppression=False)
        
        # Generate quiet audio signal
        sample_rate = 16000
        frame_size = 160  # 10ms frames
        num_frames = 50
        
        # Very quiet signal that should be amplified
        quiet_level = 200
        audio_frame = np.full(frame_size, quiet_level, dtype=np.int16)
        
        # Set initial analog level
        analog_level = 50  # Start with low level
        apm.set_stream_analog_level(analog_level)
        
        levels = []
        max_values = []
        
        print("Processing frames and monitoring gain control...")
        for frame_num in range(num_frames):
            # Process frame
            processed_frame = apm.process_stream(audio_frame)
            
            # Get recommended level
            recommended_level = apm.recommended_stream_analog_level()
            
            # Update analog level
            apm.set_stream_analog_level(recommended_level)
            
            # Track statistics
            levels.append(recommended_level)
            max_values.append(np.max(np.abs(processed_frame)))
            
            if frame_num % 10 == 0:
                print(f"Frame {frame_num:2d}: Level={recommended_level:3d}, Max={max_values[-1]:5d}")
        
        print(f"\nLevel progression: {min(levels)} → {max(levels)}")
        print(f"Output amplitude: {min(max_values)} → {max(max_values)}")
        
        return levels, max_values
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return None, None

def statistics_monitoring_example():
    """Statistics monitoring example."""
    print("\n=== Statistics Monitoring Example ===")
    
    try:
        import webrtc_audio_processing as wapm
        
        # Create audio processor with all features
        apm = wapm.AudioProcessing()
        apm.apply_config(
            echo_cancellation=True,
            noise_suppression=True,
            gain_control=True,
            residual_echo_detector=True
        )
        
        # Set stream delay (simulate known delay)
        apm.set_stream_delay_ms(50)
        
        # Generate test audio with varying characteristics
        sample_rate = 16000
        frame_size = 160
        
        for frame_type in ["quiet", "normal", "loud"]:
            print(f"\nTesting with {frame_type} audio...")
            
            if frame_type == "quiet":
                audio_frame = np.random.randint(-100, 100, frame_size, dtype=np.int16)
            elif frame_type == "normal":
                audio_frame = np.random.randint(-1000, 1000, frame_size, dtype=np.int16)
            else:  # loud
                audio_frame = np.random.randint(-5000, 5000, frame_size, dtype=np.int16)
            
            # Process several frames
            for _ in range(10):
                apm.process_stream(audio_frame)
            
            # Get statistics
            stats = apm.get_statistics()
            has_echo = apm.stream_has_echo()
            
            print(f"  Statistics: {stats}")
            print(f"  Echo detected: {has_echo}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def plot_results(original, noisy, processed, title="Audio Processing Results"):
    """Plot audio processing results."""
    try:
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(12, 8))
        
        time_axis = np.arange(len(original)) / 16000 * 1000  # Convert to ms
        
        plt.subplot(3, 1, 1)
        plt.plot(time_axis, original)
        plt.title("Original Signal")
        plt.ylabel("Amplitude")
        plt.grid(True)
        
        plt.subplot(3, 1, 2)
        plt.plot(time_axis, noisy)
        plt.title("Noisy/Echo Signal")
        plt.ylabel("Amplitude")
        plt.grid(True)
        
        plt.subplot(3, 1, 3)
        plt.plot(time_axis, processed)
        plt.title("Processed Signal")
        plt.xlabel("Time (ms)")
        plt.ylabel("Amplitude")
        plt.grid(True)
        
        plt.tight_layout()
        plt.suptitle(title, y=0.98)
        plt.show()
        
    except ImportError:
        print("matplotlib not available, skipping plots")

def main():
    """Run all examples."""
    print("WebRTC Audio Processing Python Examples")
    print("=" * 50)
    
    # Basic processing
    noisy, processed = basic_audio_processing_example()
    
    # Echo cancellation
    original, with_echo, echo_cancelled = echo_cancellation_example()
    
    # Gain control
    levels, max_values = gain_control_example()
    
    # Statistics monitoring
    statistics_monitoring_example()
    
    # Plot results if possible
    if processed is not None and noisy is not None:
        plot_results(noisy, noisy, processed, "Noise Suppression")
    
    if echo_cancelled is not None:
        plot_results(original, with_echo, echo_cancelled, "Echo Cancellation")
    
    print("\n" + "=" * 50)
    print("Examples completed!")

if __name__ == "__main__":
    main()