from setuptools import setup, find_packages, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext
import pybind11
import os
import sys
import platform
import glob
import subprocess

def get_platform_specific_flags():
    """Get platform-specific compiler flags and definitions"""
    flags = []
    definitions = []
    libraries = []
    
    # Common definitions
    definitions.extend([
        'WEBRTC_LIBRARY_IMPL',
        'WEBRTC_ENABLE_SYMBOL_EXPORT',
        'WEBRTC_APM_DEBUG_DUMP=0',
        'NDEBUG',
        '_WINSOCKAPI_',
    ])
    
    # Platform-specific flags
    if platform.system() == 'Darwin':  # macOS
        definitions.extend(['WEBRTC_MAC', 'WEBRTC_POSIX'])
        flags.extend(['-stdlib=libc++', '-mmacosx-version-min=10.9'])
    elif platform.system() == 'Linux':
        definitions.extend(['WEBRTC_LINUX', 'WEBRTC_POSIX'])
        libraries.extend(['rt', 'pthread'])
    elif platform.system() == 'Windows':
        definitions.extend(['WEBRTC_WIN', '_WIN32', 'NOMINMAX', '_USE_MATH_DEFINES'])
        libraries.extend(['winmm'])
    
    # Architecture-specific flags
    machine = platform.machine().lower()
    if machine in ['x86_64', 'amd64']:
        definitions.append('WEBRTC_ENABLE_AVX2')
        flags.extend(['-mavx2', '-mfma', '-msse2'])
    elif machine in ['arm64', 'aarch64']:
        definitions.extend(['WEBRTC_ARCH_ARM64', 'WEBRTC_HAS_NEON'])
    elif machine.startswith('arm'):
        definitions.extend(['WEBRTC_ARCH_ARM', 'WEBRTC_ARCH_ARM_V7', 'WEBRTC_HAS_NEON'])
        flags.extend(['-mfpu=neon'])
    
    return flags, definitions, libraries

def find_source_files():
    """Find all source files needed for compilation"""
    base_path = "webrtc"
    source_files = []
    
    # Core audio processing sources
    audio_processing_sources = [
        "modules/audio_processing/audio_buffer.cc",
        "modules/audio_processing/audio_processing_impl.cc",
        "modules/audio_processing/audio_processing_statistics.cc",
        "modules/audio_processing/echo_control_mobile_impl.cc",
        "modules/audio_processing/gain_control_impl.cc",
        "modules/audio_processing/high_pass_filter.cc",
        "modules/audio_processing/level_estimator.cc",
        "modules/audio_processing/noise_suppression_impl.cc",
        "modules/audio_processing/residual_echo_detector.cc",
        "modules/audio_processing/rms_level.cc",
        "modules/audio_processing/splitting_filter.cc",
        "modules/audio_processing/three_band_filter_bank.cc",
        "modules/audio_processing/voice_detection_impl.cc",
        
        # AEC3 (Echo Cancellation)
        "modules/audio_processing/aec3/adaptive_fir_filter.cc",
        "modules/audio_processing/aec3/aec3_common.cc",
        "modules/audio_processing/aec3/aec3_fft.cc",
        "modules/audio_processing/aec3/aec_state.cc",
        "modules/audio_processing/aec3/api_call_jitter_metrics.cc",
        "modules/audio_processing/aec3/block_framer.cc",
        "modules/audio_processing/aec3/block_processor.cc",
        "modules/audio_processing/aec3/cascaded_biquad_filter.cc",
        "modules/audio_processing/aec3/comfort_noise_generator.cc",
        "modules/audio_processing/aec3/decimator.cc",
        "modules/audio_processing/aec3/echo_audibility.cc",
        "modules/audio_processing/aec3/echo_canceller3.cc",
        "modules/audio_processing/aec3/echo_path_delay_estimator.cc",
        "modules/audio_processing/aec3/echo_path_variability.cc",
        "modules/audio_processing/aec3/echo_remover.cc",
        "modules/audio_processing/aec3/echo_remover_metrics.cc",
        "modules/audio_processing/aec3/erle_estimator.cc",
        "modules/audio_processing/aec3/fft_data.cc",
        "modules/audio_processing/aec3/filter_analyzer.cc",
        "modules/audio_processing/aec3/frame_blocker.cc",
        "modules/audio_processing/aec3/fullband_erle_estimator.cc",
        "modules/audio_processing/aec3/matched_filter.cc",
        "modules/audio_processing/aec3/matched_filter_lag_aggregator.cc",
        "modules/audio_processing/aec3/moving_average.cc",
        "modules/audio_processing/aec3/render_buffer.cc",
        "modules/audio_processing/aec3/render_delay_buffer.cc",
        "modules/audio_processing/aec3/render_delay_controller.cc",
        "modules/audio_processing/aec3/render_delay_controller_metrics.cc",
        "modules/audio_processing/aec3/render_reverb_model.cc",
        "modules/audio_processing/aec3/render_signal_analyzer.cc",
        "modules/audio_processing/aec3/residual_echo_estimator.cc",
        "modules/audio_processing/aec3/reverb_decay_estimator.cc",
        "modules/audio_processing/aec3/reverb_frequency_response.cc",
        "modules/audio_processing/aec3/reverb_model.cc",
        "modules/audio_processing/aec3/reverb_model_estimator.cc",
        "modules/audio_processing/aec3/shadow_filter_update_gain.cc",
        "modules/audio_processing/aec3/spectrum_buffer.cc",
        "modules/audio_processing/aec3/stationarity_estimator.cc",
        "modules/audio_processing/aec3/subband_erle_estimator.cc",
        "modules/audio_processing/aec3/subtractor.cc",
        "modules/audio_processing/aec3/subtractor_output.cc",
        "modules/audio_processing/aec3/subtractor_output_analyzer.cc",
        "modules/audio_processing/aec3/suppression_filter.cc",
        "modules/audio_processing/aec3/suppression_gain.cc",
        "modules/audio_processing/aec3/transparent_mode.cc",
        "modules/audio_processing/aec3/vector_math.cc",
        
        # AECM (Echo Control Mobile)
        "modules/audio_processing/aecm/aecm_core.cc",
        "modules/audio_processing/aecm/aecm_core_c.cc",
        "modules/audio_processing/aecm/echo_control_mobile.cc",
        
        # AGC (Automatic Gain Control)
        "modules/audio_processing/agc/agc.cc",
        "modules/audio_processing/agc/agc_manager_direct.cc",
        "modules/audio_processing/agc/loudness_histogram.cc",
        "modules/audio_processing/agc/utility.cc",
        
        # AGC2 (Advanced AGC)
        "modules/audio_processing/agc2/adaptive_agc.cc",
        "modules/audio_processing/agc2/adaptive_digital_gain_applier.cc",
        "modules/audio_processing/agc2/adaptive_mode_level_estimator.cc",
        "modules/audio_processing/agc2/adaptive_mode_level_estimator_agc.cc",
        "modules/audio_processing/agc2/agc2_common.cc",
        "modules/audio_processing/agc2/biquad_filter.cc",
        "modules/audio_processing/agc2/compute_interpolated_gain_curve.cc",
        "modules/audio_processing/agc2/down_sampler.cc",
        "modules/audio_processing/agc2/fixed_digital_level_estimator.cc",
        "modules/audio_processing/agc2/fixed_gain_controller.cc",
        "modules/audio_processing/agc2/gain_applier.cc",
        "modules/audio_processing/agc2/gain_controller2.cc",
        "modules/audio_processing/agc2/interpolated_gain_curve.cc",
        "modules/audio_processing/agc2/limiter.cc",
        "modules/audio_processing/agc2/limiter_db_gain_curve.cc",
        "modules/audio_processing/agc2/noise_level_estimator.cc",
        "modules/audio_processing/agc2/noise_spectrum_estimator.cc",
        "modules/audio_processing/agc2/saturation_protector.cc",
        "modules/audio_processing/agc2/signal_classifier.cc",
        "modules/audio_processing/agc2/vad_with_level.cc",
        "modules/audio_processing/agc2/vector_float_frame.cc",
        
        # NS (Noise Suppression)
        "modules/audio_processing/ns/fast_math.cc",
        "modules/audio_processing/ns/histograms.cc",
        "modules/audio_processing/ns/noise_estimator.cc",
        "modules/audio_processing/ns/noise_suppressor.cc",
        "modules/audio_processing/ns/ns_fft.cc",
        "modules/audio_processing/ns/prior_signal_model.cc",
        "modules/audio_processing/ns/prior_signal_model_estimator.cc",
        "modules/audio_processing/ns/quantile_noise_estimator.cc",
        "modules/audio_processing/ns/signal_model.cc",
        "modules/audio_processing/ns/signal_model_estimator.cc",
        "modules/audio_processing/ns/speech_probability_estimator.cc",
        "modules/audio_processing/ns/suppression_params.cc",
        "modules/audio_processing/ns/wiener_filter.cc",
        
        # VAD (Voice Activity Detection)
        "modules/audio_processing/vad/vad_audio_proc.cc",
        "modules/audio_processing/vad/vad_circular_buffer.cc",
        "modules/audio_processing/vad/voice_activity_detector.cc",
        
        # Utility
        "modules/audio_processing/utility/cascaded_biquad_filter.cc",
        "modules/audio_processing/utility/delay_estimator.cc",
        "modules/audio_processing/utility/delay_estimator_wrapper.cc",
        "modules/audio_processing/utility/ooura_fft.cc",
        "modules/audio_processing/utility/ooura_fft_tables_common.cc",
        "modules/audio_processing/utility/ooura_fft_tables_neon_sse2.cc",
    ]
    
    # Common audio sources
    common_audio_sources = [
        "common_audio/audio_converter.cc",
        "common_audio/audio_util.cc",
        "common_audio/channel_buffer.cc",
        "common_audio/fir_filter_c.cc",
        "common_audio/fir_filter_factory.cc",
        "common_audio/ring_buffer.cc",
        "common_audio/wav_file.cc",
        "common_audio/wav_header.cc",
        "common_audio/window_generator.cc",
        
        # Resampler
        "common_audio/resampler/push_resampler.cc",
        "common_audio/resampler/push_sinc_resampler.cc",
        "common_audio/resampler/resampler.cc",
        "common_audio/resampler/sinc_resampler.cc",
        "common_audio/resampler/sinusoidal_linear_chirp_source.cc",
        
        # Signal processing
        "common_audio/signal_processing/auto_correlation.cc",
        "common_audio/signal_processing/auto_corr_to_refl_coef.cc",
        "common_audio/signal_processing/copy_set_operations.cc",
        "common_audio/signal_processing/cross_correlation.cc",
        "common_audio/signal_processing/division_operations.cc",
        "common_audio/signal_processing/dot_product_with_scale.cc",
        "common_audio/signal_processing/downsample_fast.cc",
        "common_audio/signal_processing/energy.cc",
        "common_audio/signal_processing/filter_ar.cc",
        "common_audio/signal_processing/filter_ma_fast_q12.cc",
        "common_audio/signal_processing/get_hanning_window.cc",
        "common_audio/signal_processing/get_scaling_square.cc",
        "common_audio/signal_processing/ilbc_specific_functions.cc",
        "common_audio/signal_processing/levinson_durbin.cc",
        "common_audio/signal_processing/lpc_to_refl_coef.cc",
        "common_audio/signal_processing/min_max_operations.cc",
        "common_audio/signal_processing/randomization_functions.cc",
        "common_audio/signal_processing/real_fft.cc",
        "common_audio/signal_processing/refl_coef_to_lpc.cc",
        "common_audio/signal_processing/resample.cc",
        "common_audio/signal_processing/resample_48khz.cc",
        "common_audio/signal_processing/resample_by_2.cc",
        "common_audio/signal_processing/resample_by_2_internal.cc",
        "common_audio/signal_processing/resample_fractional.cc",
        "common_audio/signal_processing/spl_init.cc",
        "common_audio/signal_processing/spl_inl.cc",
        "common_audio/signal_processing/spl_sqrt.cc",
        "common_audio/signal_processing/spl_sqrt_floor.cc",
        "common_audio/signal_processing/splitting_filter.cc",
        "common_audio/signal_processing/sqrt_of_one_minus_x_squared.cc",
        "common_audio/signal_processing/vector_scaling_operations.cc",
        
        # Third-party
        "common_audio/third_party/ooura/fft_size_128/ooura_fft.cc",
        "common_audio/third_party/ooura/fft_size_256/ooura_fft.cc",
        "common_audio/third_party/spl_sqrt_floor/spl_sqrt_floor.c",
        
        # VAD
        "common_audio/vad/vad.cc",
        "common_audio/vad/vad_core.cc",
        "common_audio/vad/vad_filterbank.cc",
        "common_audio/vad/vad_gmm.cc",
        "common_audio/vad/vad_sp.cc",
        "common_audio/vad/webrtc_vad.cc",
    ]
    
    # API sources
    api_sources = [
        "api/audio/audio_frame.cc",
        "api/audio/audio_processing.cc",
        "api/audio/channel_layout.cc",
        "api/audio/echo_canceller3_config.cc",
        "api/audio/echo_canceller3_factory.cc",
        "api/rtp_headers.cc",
        "api/rtp_packet_info.cc",
        "api/task_queue/task_queue_base.cc",
        "api/units/frequency.cc",
        "api/units/time_delta.cc",
        "api/units/timestamp.cc",
    ]
    
    # RTC Base sources
    rtc_base_sources = [
        "rtc_base/checks.cc",
        "rtc_base/logging.cc",
        "rtc_base/platform_thread.cc",
        "rtc_base/race_checker.cc",
        "rtc_base/string_encode.cc",
        "rtc_base/string_to_number.cc",
        "rtc_base/string_utils.cc",
        "rtc_base/strings/string_builder.cc",
        "rtc_base/synchronization/mutex.cc",
        "rtc_base/synchronization/yield_policy.cc",
        "rtc_base/time_utils.cc",
        "rtc_base/containers/flat_tree.cc",
        "rtc_base/memory/aligned_malloc.cc",
        "rtc_base/system/file_wrapper.cc",
        "rtc_base/system/rtc_export.cc",
    ]
    
    # System wrappers
    system_wrappers_sources = [
        "system_wrappers/source/cpu_features.cc",
        "system_wrappers/source/field_trial.cc",
        "system_wrappers/source/metrics.cc",
        "system_wrappers/source/sleep.cc",
        "system_wrappers/source/denormal_disabler.cc",
    ]
    
    # Third-party sources
    third_party_sources = [
        "third_party/pffft/src/pffft.c",
        "third_party/rnnoise/src/rnn_vad_weights.cc",
        "modules/third_party/fft/fft.c",
    ]
    
    # Combine all sources
    all_sources = (audio_processing_sources + common_audio_sources + 
                  api_sources + rtc_base_sources + system_wrappers_sources +
                  third_party_sources)
    
    # Convert to full paths and check existence
    for source in all_sources:
        full_path = os.path.join(base_path, source)
        if os.path.exists(full_path):
            source_files.append(full_path)
        else:
            print(f"Warning: Source file not found: {full_path}")
    
    # Add export wrapper
    export_sources = ["export/export.cc"]
    for source in export_sources:
        if os.path.exists(source):
            source_files.append(source)
    
    return source_files

def get_include_directories():
    """Get all include directories"""
    includes = [
        ".",
        "webrtc",
        "webrtc/modules/audio_processing/include",
        "webrtc/api",
        "webrtc/rtc_base",
        "webrtc/common_audio/include",
        "webrtc/system_wrappers/include",
        "webrtc/third_party/pffft/src",
        "webrtc/modules/third_party/fft",
    ]
    return includes

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        # Check if abseil-cpp is available
        import pkg_config
        try:
            pkg_config.parse('absl_base')
            return True
        except:
            pass
    except ImportError:
        pass
    
    # Try to find abseil headers manually
    potential_paths = [
        "/usr/include/absl",
        "/usr/local/include/absl",
        "/opt/homebrew/include/absl",
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            return True
    
    print("Warning: Abseil-cpp not found. Some features may not work.")
    return False

# Get platform-specific configuration
compile_flags, definitions, libraries = get_platform_specific_flags()

# Find source files
source_files = find_source_files()

# Add Python binding source
source_files.append("python/webrtc_apm_full.cpp")

print(f"Found {len(source_files)} source files")
print(f"Compile flags: {compile_flags}")
print(f"Definitions: {definitions}")
print(f"Libraries: {libraries}")

# Check dependencies
check_dependencies()

# Define extension module
ext_modules = [
    Pybind11Extension(
        "webrtc_apm.webrtc_apm",
        source_files,
        include_dirs=[
            pybind11.get_include(),
        ] + get_include_directories(),
        define_macros=[(d.split('=')[0], d.split('=')[1] if '=' in d else None) for d in definitions],
        libraries=libraries,
        language='c++',
        cxx_std=17,
        extra_compile_args=compile_flags + ['-O3', '-ffast-math'],
        extra_link_args=['-O3'],
    ),
]

setup(
    name="webrtc_audio_processing",
    version="2.1.0",
    author="WebRTC Audio Processing Contributors",
    author_email="",
    description="WebRTC Audio Processing Python Bindings - Full Implementation",
    long_description="Complete WebRTC Audio Processing Python Bindings with echo cancellation, noise suppression, and automatic gain control",
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
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
)