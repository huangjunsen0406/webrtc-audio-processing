#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <memory>
#include <stdexcept>

// Use the C API for simplicity
#include "export/export.h"

namespace py = pybind11;

class AudioProcessor {
public:
    AudioProcessor() {
        // Create WebRTC Audio Processing instance using C API
        handle_ = WebRTC_APM_Create();
        
        if (!handle_) {
            throw std::runtime_error("Failed to create WebRTC Audio Processing instance");
        }
        
        // Set default configuration
        WebRTC_APM_Config config;
        config.aec_enabled = true;
        config.aec_delay_agnostic_enabled = true;
        config.aec_drift_compensation_enabled = false;
        config.aec_extended_filter_enabled = true;
        config.aec_refined_adaptive_filter_enabled = false;
        config.aec_suppression_level = 2;  // High suppression
        
        config.aecm_enabled = false;
        config.aecm_comfort_noise_enabled = true;
        config.aecm_routing_mode = 4;  // Speakerphone
        
        config.agc_enabled = true;
        config.agc_mode = 1;  // Adaptive analog
        config.agc_limiter_enabled = true;
        config.agc_target_level_dbfs = 3;
        config.agc_compression_gain_db = 9;
        
        config.ns_enabled = true;
        config.ns_level = 3;  // Very high
        
        config.vad_enabled = true;
        config.vad_likelihood = 1;  // Low likelihood
        
        config.hpf_enabled = true;
        
        // Apply configuration
        int result = WebRTC_APM_ApplyConfig(handle_, &config);
        if (result != 0) {
            WebRTC_APM_Destroy(handle_);
            throw std::runtime_error("Failed to apply default configuration");
        }
        
        // Initialize default stream configuration
        sample_rate_ = 16000;
        channels_ = 1;
        
        // Set up stream config
        input_config_ = WebRTC_APM_CreateStreamConfig(sample_rate_, channels_);
        output_config_ = WebRTC_APM_CreateStreamConfig(sample_rate_, channels_);
        
        if (!input_config_ || !output_config_) {
            WebRTC_APM_Destroy(handle_);
            throw std::runtime_error("Failed to create stream configuration");
        }
    }
    
    ~AudioProcessor() {
        if (handle_) {
            if (input_config_) {
                WebRTC_APM_DestroyStreamConfig(input_config_);
            }
            if (output_config_) {
                WebRTC_APM_DestroyStreamConfig(output_config_);
            }
            WebRTC_APM_Destroy(handle_);
        }
    }
    
    // Configuration methods
    void set_echo_cancellation_enabled(bool enabled) {
        WebRTC_APM_Config config;
        WebRTC_APM_GetConfig(handle_, &config);
        config.aec_enabled = enabled;
        WebRTC_APM_ApplyConfig(handle_, &config);
    }
    
    void set_noise_suppression_enabled(bool enabled) {
        WebRTC_APM_Config config;
        WebRTC_APM_GetConfig(handle_, &config);
        config.ns_enabled = enabled;
        WebRTC_APM_ApplyConfig(handle_, &config);
    }
    
    void set_noise_suppression_level(int level) {
        WebRTC_APM_Config config;
        WebRTC_APM_GetConfig(handle_, &config);
        config.ns_enabled = true;
        config.ns_level = std::max(0, std::min(3, level));
        WebRTC_APM_ApplyConfig(handle_, &config);
    }
    
    void set_gain_control_enabled(bool enabled) {
        WebRTC_APM_Config config;
        WebRTC_APM_GetConfig(handle_, &config);
        config.agc_enabled = enabled;
        WebRTC_APM_ApplyConfig(handle_, &config);
    }
    
    void set_high_pass_filter_enabled(bool enabled) {
        WebRTC_APM_Config config;
        WebRTC_APM_GetConfig(handle_, &config);
        config.hpf_enabled = enabled;
        WebRTC_APM_ApplyConfig(handle_, &config);
    }
    
    // Stream processing methods
    py::array_t<float> process_stream(py::array_t<float> input_audio, int sample_rate = 16000, int channels = 1) {
        auto buf = input_audio.request();
        
        if (buf.ndim != 1 && buf.ndim != 2) {
            throw std::runtime_error("Input audio must be 1D or 2D array");
        }
        
        // Update configuration if needed
        if (sample_rate_ != sample_rate || channels_ != channels) {
            sample_rate_ = sample_rate;
            channels_ = channels;
            
            // Recreate stream configs
            if (input_config_) {
                WebRTC_APM_DestroyStreamConfig(input_config_);
            }
            if (output_config_) {
                WebRTC_APM_DestroyStreamConfig(output_config_);
            }
            
            input_config_ = WebRTC_APM_CreateStreamConfig(sample_rate, channels);
            output_config_ = WebRTC_APM_CreateStreamConfig(sample_rate, channels);
            
            if (!input_config_ || !output_config_) {
                throw std::runtime_error("Failed to recreate stream configuration");
            }
        }
        
        // Get input data
        float* input_data = static_cast<float*>(buf.ptr);
        size_t num_samples = buf.shape[0];
        
        if (buf.ndim == 2) {
            channels = buf.shape[1];
            num_samples = buf.shape[0];
        }
        
        // Create output array
        auto output_audio = py::array_t<float>(buf.size);
        auto output_buf = output_audio.request();
        float* output_data = static_cast<float*>(output_buf.ptr);
        
        // Copy input to output initially
        std::memcpy(output_data, input_data, buf.size * sizeof(float));
        
        // Process audio using WebRTC C API
        int result = WebRTC_APM_ProcessStream(
            handle_,
            input_config_,
            output_config_,
            input_data,
            output_data,
            num_samples
        );
        
        if (result != 0) {
            throw std::runtime_error("Audio processing failed with error: " + std::to_string(result));
        }
        
        // Set output array shape
        if (buf.ndim == 2) {
            output_audio.resize({static_cast<py::ssize_t>(num_samples), static_cast<py::ssize_t>(channels)});
        } else {
            output_audio.resize({static_cast<py::ssize_t>(num_samples)});
        }
        
        return output_audio;
    }
    
    py::array_t<float> process_reverse_stream(py::array_t<float> input_audio, int sample_rate = 16000, int channels = 1) {
        auto buf = input_audio.request();
        
        // Create output array
        auto output_audio = py::array_t<float>(buf.size);
        auto output_buf = output_audio.request();
        
        float* input_data = static_cast<float*>(buf.ptr);
        float* output_data = static_cast<float*>(output_buf.ptr);
        
        // Copy input to output initially
        std::memcpy(output_data, input_data, buf.size * sizeof(float));
        
        size_t num_samples = buf.shape[0];
        if (buf.ndim == 2) {
            channels = buf.shape[1];
            num_samples = buf.shape[0];
        }
        
        // Process reverse stream using WebRTC C API
        int result = WebRTC_APM_ProcessReverseStream(
            handle_,
            input_config_,
            output_config_,
            input_data,
            output_data,
            num_samples
        );
        
        if (result != 0) {
            throw std::runtime_error("Reverse stream processing failed with error: " + std::to_string(result));
        }
        
        // Set output array shape
        output_audio.resize(buf.shape);
        
        return output_audio;
    }
    
    // Statistics and monitoring
    py::dict get_statistics() {
        WebRTC_APM_Statistics stats;
        int result = WebRTC_APM_GetStatistics(handle_, &stats);
        
        py::dict result_dict;
        
        if (result == 0) {
            result_dict["echo_return_loss"] = stats.echo_return_loss;
            result_dict["echo_return_loss_enhancement"] = stats.echo_return_loss_enhancement;
            result_dict["delay_median_ms"] = stats.delay_median_ms;
            result_dict["residual_echo_likelihood"] = stats.residual_echo_likelihood;
            result_dict["has_echo"] = stats.has_echo;
            result_dict["divergent_filter_fraction"] = stats.divergent_filter_fraction;
            result_dict["delay_standard_deviation_ms"] = stats.delay_standard_deviation_ms;
        }
        
        return result_dict;
    }
    
    // Stream delay management
    void set_stream_delay_ms(int delay_ms) {
        WebRTC_APM_SetStreamDelayMs(handle_, delay_ms);
    }
    
    // Analog level management for AGC
    void set_stream_analog_level(int level) {
        WebRTC_APM_SetStreamAnalogLevel(handle_, level);
    }
    
    int recommended_stream_analog_level() {
        return WebRTC_APM_RecommendedStreamAnalogLevel(handle_);
    }
    
    // Get version information
    std::string get_version() {
        return "2.1.0-webrtc-full";
    }
    
    // Check if echo cancellation is enabled
    bool is_echo_cancellation_enabled() {
        WebRTC_APM_Config config;
        WebRTC_APM_GetConfig(handle_, &config);
        return config.aec_enabled;
    }
    
    // Check if noise suppression is enabled
    bool is_noise_suppression_enabled() {
        WebRTC_APM_Config config;
        WebRTC_APM_GetConfig(handle_, &config);
        return config.ns_enabled;
    }
    
    // Check if gain control is enabled
    bool is_gain_control_enabled() {
        WebRTC_APM_Config config;
        WebRTC_APM_GetConfig(handle_, &config);
        return config.agc_enabled;
    }
    
private:
    WebRTC_APM_Handle* handle_;
    WebRTC_APM_StreamConfig* input_config_;
    WebRTC_APM_StreamConfig* output_config_;
    int sample_rate_;
    int channels_;
};

// Configuration class
class Config {
public:
    Config() = default;
    
    void apply_to_processor(AudioProcessor& processor) {
        processor.set_echo_cancellation_enabled(echo_canceller.enabled);
        processor.set_noise_suppression_enabled(noise_suppression.enabled);
        processor.set_noise_suppression_level(noise_suppression.level);
        processor.set_gain_control_enabled(gain_controller.enabled);
        processor.set_high_pass_filter_enabled(high_pass_filter.enabled);
    }
    
    struct EchoCanceller {
        bool enabled = true;
        bool mobile_mode = false;
    } echo_canceller;
    
    struct NoiseSuppression {
        bool enabled = true;
        int level = 2;  // 0: Low, 1: Moderate, 2: High, 3: VeryHigh
    } noise_suppression;
    
    struct GainController {
        bool enabled = true;
        int mode = 0;  // 0: Adaptive analog, 1: Adaptive digital, 2: Fixed digital
    } gain_controller;
    
    struct HighPassFilter {
        bool enabled = true;
    } high_pass_filter;
};

PYBIND11_MODULE(webrtc_apm, m) {
    m.doc() = "WebRTC Audio Processing Python Bindings - WebRTC Implementation";
    
    // Main AudioProcessor class
    py::class_<AudioProcessor>(m, "AudioProcessor")
        .def(py::init<>())
        .def("set_echo_cancellation_enabled", &AudioProcessor::set_echo_cancellation_enabled,
             "Enable or disable echo cancellation")
        .def("set_noise_suppression_enabled", &AudioProcessor::set_noise_suppression_enabled,
             "Enable or disable noise suppression")
        .def("set_noise_suppression_level", &AudioProcessor::set_noise_suppression_level,
             "Set noise suppression level (0: Low, 1: Moderate, 2: High, 3: VeryHigh)")
        .def("set_gain_control_enabled", &AudioProcessor::set_gain_control_enabled,
             "Enable or disable automatic gain control")
        .def("set_high_pass_filter_enabled", &AudioProcessor::set_high_pass_filter_enabled,
             "Enable or disable high-pass filter")
        .def("process_stream", &AudioProcessor::process_stream,
             "Process audio stream for noise suppression and gain control",
             py::arg("input_audio"), py::arg("sample_rate") = 16000, py::arg("channels") = 1)
        .def("process_reverse_stream", &AudioProcessor::process_reverse_stream,
             "Process reverse audio stream for echo cancellation",
             py::arg("input_audio"), py::arg("sample_rate") = 16000, py::arg("channels") = 1)
        .def("get_statistics", &AudioProcessor::get_statistics,
             "Get audio processing statistics")
        .def("set_stream_delay_ms", &AudioProcessor::set_stream_delay_ms,
             "Set stream delay in milliseconds")
        .def("set_stream_analog_level", &AudioProcessor::set_stream_analog_level,
             "Set analog level for AGC")
        .def("recommended_stream_analog_level", &AudioProcessor::recommended_stream_analog_level,
             "Get recommended analog level from AGC")
        .def("get_version", &AudioProcessor::get_version,
             "Get version information")
        .def("is_echo_cancellation_enabled", &AudioProcessor::is_echo_cancellation_enabled,
             "Check if echo cancellation is enabled")
        .def("is_noise_suppression_enabled", &AudioProcessor::is_noise_suppression_enabled,
             "Check if noise suppression is enabled")
        .def("is_gain_control_enabled", &AudioProcessor::is_gain_control_enabled,
             "Check if gain control is enabled");
    
    // Configuration class
    py::class_<Config>(m, "Config")
        .def(py::init<>())
        .def("apply_to_processor", &Config::apply_to_processor,
             "Apply configuration to AudioProcessor")
        .def_readwrite("echo_canceller", &Config::echo_canceller)
        .def_readwrite("noise_suppression", &Config::noise_suppression)
        .def_readwrite("gain_controller", &Config::gain_controller)
        .def_readwrite("high_pass_filter", &Config::high_pass_filter);
    
    // Nested configuration structures
    py::class_<Config::EchoCanceller>(m, "EchoCanceller")
        .def(py::init<>())
        .def_readwrite("enabled", &Config::EchoCanceller::enabled)
        .def_readwrite("mobile_mode", &Config::EchoCanceller::mobile_mode);
    
    py::class_<Config::NoiseSuppression>(m, "NoiseSuppression")
        .def(py::init<>())
        .def_readwrite("enabled", &Config::NoiseSuppression::enabled)
        .def_readwrite("level", &Config::NoiseSuppression::level);
    
    py::class_<Config::GainController>(m, "GainController")
        .def(py::init<>())
        .def_readwrite("enabled", &Config::GainController::enabled)
        .def_readwrite("mode", &Config::GainController::mode);
    
    py::class_<Config::HighPassFilter>(m, "HighPassFilter")
        .def(py::init<>())
        .def_readwrite("enabled", &Config::HighPassFilter::enabled);
    
    // Constants
    m.attr("__version__") = "2.1.0";
    m.attr("SAMPLE_RATE_8000") = 8000;
    m.attr("SAMPLE_RATE_16000") = 16000;
    m.attr("SAMPLE_RATE_32000") = 32000;
    m.attr("SAMPLE_RATE_48000") = 48000;
    
    // Noise suppression levels
    m.attr("NS_LEVEL_LOW") = 0;
    m.attr("NS_LEVEL_MODERATE") = 1;
    m.attr("NS_LEVEL_HIGH") = 2;
    m.attr("NS_LEVEL_VERY_HIGH") = 3;
    
    // AGC modes
    m.attr("AGC_MODE_ADAPTIVE_ANALOG") = 0;
    m.attr("AGC_MODE_ADAPTIVE_DIGITAL") = 1;
    m.attr("AGC_MODE_FIXED_DIGITAL") = 2;
}