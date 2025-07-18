#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <memory>
#include <stdexcept>

// WebRTC Audio Processing includes
#include "api/audio/audio_processing.h"
#include "api/audio/audio_processing_statistics.h"
#include "rtc_base/ref_counted_object.h"
#include "modules/audio_processing/include/audio_processing.h"

namespace py = pybind11;

class AudioProcessor {
public:
    AudioProcessor() {
        // Create WebRTC AudioProcessing instance
        webrtc::AudioProcessingBuilder builder;
        apm_ = builder.Create();
        
        if (!apm_) {
            throw std::runtime_error("Failed to create WebRTC Audio Processing instance");
        }
        
        // Default configuration
        webrtc::AudioProcessing::Config config;
        config.echo_canceller.enabled = true;
        config.echo_canceller.mobile_mode = false;
        config.gain_controller1.enabled = true;
        config.gain_controller1.mode = webrtc::AudioProcessing::Config::GainController1::kAdaptiveAnalog;
        config.gain_controller2.enabled = true;
        config.high_pass_filter.enabled = true;
        config.noise_suppression.enabled = true;
        config.noise_suppression.level = webrtc::AudioProcessing::Config::NoiseSuppression::kHigh;
        
        apm_->ApplyConfig(config);
        
        // Initialize default stream configuration
        sample_rate_ = 16000;
        channels_ = 1;
        
        // Initialize the audio processing
        int result = apm_->Initialize();
        if (result != webrtc::AudioProcessing::kNoError) {
            throw std::runtime_error("Failed to initialize WebRTC Audio Processing");
        }
    }
    
    ~AudioProcessor() = default;
    
    // Configuration methods
    void set_echo_cancellation_enabled(bool enabled) {
        webrtc::AudioProcessing::Config config = apm_->GetConfig();
        config.echo_canceller.enabled = enabled;
        apm_->ApplyConfig(config);
    }
    
    void set_noise_suppression_enabled(bool enabled) {
        webrtc::AudioProcessing::Config config = apm_->GetConfig();
        config.noise_suppression.enabled = enabled;
        apm_->ApplyConfig(config);
    }
    
    void set_noise_suppression_level(int level) {
        webrtc::AudioProcessing::Config config = apm_->GetConfig();
        config.noise_suppression.enabled = true;
        switch (level) {
            case 0:
                config.noise_suppression.level = webrtc::AudioProcessing::Config::NoiseSuppression::kLow;
                break;
            case 1:
                config.noise_suppression.level = webrtc::AudioProcessing::Config::NoiseSuppression::kModerate;
                break;
            case 2:
                config.noise_suppression.level = webrtc::AudioProcessing::Config::NoiseSuppression::kHigh;
                break;
            case 3:
                config.noise_suppression.level = webrtc::AudioProcessing::Config::NoiseSuppression::kVeryHigh;
                break;
            default:
                config.noise_suppression.level = webrtc::AudioProcessing::Config::NoiseSuppression::kHigh;
        }
        apm_->ApplyConfig(config);
    }
    
    void set_gain_control_enabled(bool enabled) {
        webrtc::AudioProcessing::Config config = apm_->GetConfig();
        config.gain_controller1.enabled = enabled;
        apm_->ApplyConfig(config);
    }
    
    void set_high_pass_filter_enabled(bool enabled) {
        webrtc::AudioProcessing::Config config = apm_->GetConfig();
        config.high_pass_filter.enabled = enabled;
        apm_->ApplyConfig(config);
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
            
            // Reinitialize with new parameters
            int result = apm_->Initialize();
            if (result != webrtc::AudioProcessing::kNoError) {
                throw std::runtime_error("Failed to reinitialize Audio Processing with new parameters");
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
        
        // Process audio in chunks (WebRTC expects ~10ms frames)
        size_t frame_size = sample_rate / 100;  // 10ms frame
        size_t total_frames = num_samples / frame_size;
        
        // Configure streams
        webrtc::StreamConfig input_config(sample_rate, channels);
        webrtc::StreamConfig output_config(sample_rate, channels);
        
        // Process each frame
        for (size_t frame = 0; frame < total_frames; ++frame) {
            size_t offset = frame * frame_size * channels;
            
            // Create audio frame
            webrtc::AudioFrame audio_frame;
            audio_frame.UpdateFrame(
                0, // timestamp
                reinterpret_cast<const int16_t*>(input_data + offset),
                frame_size,
                sample_rate,
                webrtc::AudioFrame::kNormalSpeech,
                webrtc::AudioFrame::kVadUnknown,
                channels
            );
            
            // Process the frame
            int result = apm_->ProcessStream(&audio_frame);
            if (result != webrtc::AudioProcessing::kNoError) {
                throw std::runtime_error("Audio processing failed with error: " + std::to_string(result));
            }
            
            // Copy processed data back to output
            const int16_t* processed_data = audio_frame.data();
            for (size_t i = 0; i < frame_size * channels; ++i) {
                output_data[offset + i] = static_cast<float>(processed_data[i]) / 32768.0f;
            }
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
        
        // Process audio in chunks
        size_t frame_size = sample_rate / 100;  // 10ms frame
        size_t total_frames = num_samples / frame_size;
        
        // Configure streams
        webrtc::StreamConfig input_config(sample_rate, channels);
        webrtc::StreamConfig output_config(sample_rate, channels);
        
        // Process each frame
        for (size_t frame = 0; frame < total_frames; ++frame) {
            size_t offset = frame * frame_size * channels;
            
            // Create audio frame
            webrtc::AudioFrame audio_frame;
            audio_frame.UpdateFrame(
                0, // timestamp
                reinterpret_cast<const int16_t*>(input_data + offset),
                frame_size,
                sample_rate,
                webrtc::AudioFrame::kNormalSpeech,
                webrtc::AudioFrame::kVadUnknown,
                channels
            );
            
            // Process reverse stream
            int result = apm_->ProcessReverseStream(&audio_frame);
            if (result != webrtc::AudioProcessing::kNoError) {
                throw std::runtime_error("Reverse stream processing failed with error: " + std::to_string(result));
            }
            
            // Copy processed data back to output
            const int16_t* processed_data = audio_frame.data();
            for (size_t i = 0; i < frame_size * channels; ++i) {
                output_data[offset + i] = static_cast<float>(processed_data[i]) / 32768.0f;
            }
        }
        
        // Set output array shape
        output_audio.resize(buf.shape);
        
        return output_audio;
    }
    
    // Statistics and monitoring
    py::dict get_statistics() {
        webrtc::AudioProcessingStats stats = apm_->GetStatistics();
        
        py::dict result;
        
        if (stats.echo_return_loss) {
            result["echo_return_loss"] = stats.echo_return_loss.value();
        }
        
        if (stats.echo_return_loss_enhancement) {
            result["echo_return_loss_enhancement"] = stats.echo_return_loss_enhancement.value();
        }
        
        if (stats.delay_median_ms) {
            result["delay_median_ms"] = stats.delay_median_ms.value();
        }
        
        if (stats.residual_echo_likelihood) {
            result["residual_echo_likelihood"] = stats.residual_echo_likelihood.value();
        }
        
        return result;
    }
    
    // Stream delay management
    void set_stream_delay_ms(int delay_ms) {
        apm_->set_stream_delay_ms(delay_ms);
    }
    
    // Analog level management for AGC
    void set_stream_analog_level(int level) {
        apm_->set_stream_analog_level(level);
    }
    
    int recommended_stream_analog_level() {
        return apm_->recommended_stream_analog_level();
    }
    
    // Get version information
    std::string get_version() {
        return "2.1.0-full";
    }
    
private:
    rtc::scoped_refptr<webrtc::AudioProcessing> apm_;
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
    m.doc() = "WebRTC Audio Processing Python Bindings - Full Implementation";
    
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
             "Get version information");
    
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