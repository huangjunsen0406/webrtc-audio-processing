#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <memory>
#include <stdexcept>

#include "webrtc/modules/audio_processing/include/audio_processing.h"
#include "webrtc/api/audio/audio_frame.h"
#include "webrtc/api/audio/echo_canceller3_config.h"

namespace py = pybind11;

class PyAudioProcessing {
public:
    PyAudioProcessing() {
        apm_ = webrtc::AudioProcessingBuilder().Create();
        if (!apm_) {
            throw std::runtime_error("Failed to create AudioProcessing instance");
        }
    }
    
    void apply_config(bool echo_cancellation = true, 
                     bool noise_suppression = true,
                     bool gain_control = true,
                     bool high_pass_filter = true) {
        webrtc::AudioProcessing::Config config;
        
        // Echo Cancellation
        config.echo_canceller.enabled = echo_cancellation;
        config.echo_canceller.mobile_mode = false;  // Use AEC3 (desktop mode)
        
        // Noise Suppression
        config.noise_suppression.enabled = noise_suppression;
        config.noise_suppression.level = webrtc::AudioProcessing::Config::NoiseSuppression::kHigh;
        
        // Gain Control
        config.gain_controller1.enabled = gain_control;
        config.gain_controller1.mode = 
            webrtc::AudioProcessing::Config::GainController1::kAdaptiveAnalog;
        config.gain_controller1.target_level_dbfs = 3;
        config.gain_controller1.compression_gain_db = 9;
        config.gain_controller1.enable_limiter = true;
        config.gain_controller1.analog_gain_controller.enabled = true;
        config.gain_controller1.analog_gain_controller.clipped_level_min = 0;
        
        // Additional gain controller (AGC2)
        config.gain_controller2.enabled = gain_control;
        
        // High-pass filter
        config.high_pass_filter.enabled = high_pass_filter;
        
        apm_->ApplyConfig(config);
    }
    
    py::array_t<int16_t> process_stream(py::array_t<int16_t> input, 
                                       int sample_rate = 16000, 
                                       int num_channels = 1) {
        auto buf = input.request();
        
        if (buf.ndim != 1) {
            throw std::runtime_error("Input array must be 1-dimensional");
        }
        
        size_t samples = buf.shape[0];
        if (samples == 0) {
            throw std::runtime_error("Input array cannot be empty");
        }
        
        // Validate sample rate
        if (sample_rate != 8000 && sample_rate != 16000 && 
            sample_rate != 32000 && sample_rate != 48000) {
            throw std::runtime_error("Sample rate must be 8000, 16000, 32000, or 48000 Hz");
        }
        
        // Validate number of channels
        if (num_channels < 1 || num_channels > 8) {
            throw std::runtime_error("Number of channels must be between 1 and 8");
        }
        
        // Create output array
        auto output = py::array_t<int16_t>(samples);
        auto output_buf = output.request();
        
        // Get pointers to data
        int16_t* input_ptr = static_cast<int16_t*>(buf.ptr);
        int16_t* output_ptr = static_cast<int16_t*>(output_buf.ptr);
        
        // Copy input to output (in-place processing)
        std::memcpy(output_ptr, input_ptr, samples * sizeof(int16_t));
        
        // Create stream configuration
        webrtc::StreamConfig config(sample_rate, num_channels);
        
        // Process the audio stream
        int result = apm_->ProcessStream(output_ptr, config, config, output_ptr);
        
        if (result != 0) {
            throw std::runtime_error("Audio processing failed with code: " + std::to_string(result));
        }
        
        return output;
    }
    
    py::array_t<int16_t> process_reverse_stream(py::array_t<int16_t> input, 
                                               int sample_rate = 16000, 
                                               int num_channels = 1) {
        auto buf = input.request();
        
        if (buf.ndim != 1) {
            throw std::runtime_error("Input array must be 1-dimensional");
        }
        
        size_t samples = buf.shape[0];
        if (samples == 0) {
            throw std::runtime_error("Input array cannot be empty");
        }
        
        // Create output array
        auto output = py::array_t<int16_t>(samples);
        auto output_buf = output.request();
        
        // Get pointers to data
        int16_t* input_ptr = static_cast<int16_t*>(buf.ptr);
        int16_t* output_ptr = static_cast<int16_t*>(output_buf.ptr);
        
        // Copy input to output
        std::memcpy(output_ptr, input_ptr, samples * sizeof(int16_t));
        
        // Create stream configuration
        webrtc::StreamConfig config(sample_rate, num_channels);
        
        // Process the reverse stream (render/speaker audio)
        int result = apm_->ProcessReverseStream(output_ptr, config, config, output_ptr);
        
        if (result != 0) {
            throw std::runtime_error("Reverse stream processing failed with code: " + std::to_string(result));
        }
        
        return output;
    }
    
    void set_stream_delay_ms(int delay_ms) {
        if (delay_ms < 0 || delay_ms > 500) {
            throw std::runtime_error("Stream delay must be between 0 and 500 ms");
        }
        apm_->set_stream_delay_ms(delay_ms);
    }
    
    void set_stream_analog_level(int level) {
        if (level < 0 || level > 255) {
            throw std::runtime_error("Analog level must be between 0 and 255");
        }
        apm_->set_stream_analog_level(level);
    }
    
    int recommended_stream_analog_level() const {
        return apm_->recommended_stream_analog_level();
    }
    
    bool stream_has_echo() const {
        return apm_->GetStatistics().echo_return_loss_enhancement.has_value();
    }
    
    py::dict get_statistics() const {
        auto stats = apm_->GetStatistics();
        py::dict result;
        
        if (stats.echo_return_loss_enhancement.has_value()) {
            result["echo_return_loss_enhancement"] = *stats.echo_return_loss_enhancement;
        }
        
        if (stats.echo_return_loss.has_value()) {
            result["echo_return_loss"] = *stats.echo_return_loss;
        }
        
        if (stats.delay_median_ms.has_value()) {
            result["delay_median_ms"] = *stats.delay_median_ms;
        }
        
        if (stats.delay_standard_deviation_ms.has_value()) {
            result["delay_standard_deviation_ms"] = *stats.delay_standard_deviation_ms;
        }
        
        return result;
    }

private:
    rtc::scoped_refptr<webrtc::AudioProcessing> apm_;
};

PYBIND11_MODULE(webrtc_audio_processing, m) {
    m.doc() = "WebRTC Audio Processing Python bindings";
    
    py::class_<PyAudioProcessing>(m, "AudioProcessing")
        .def(py::init<>(), "Create AudioProcessing instance")
        .def("apply_config", &PyAudioProcessing::apply_config,
             py::arg("echo_cancellation") = true,
             py::arg("noise_suppression") = true,
             py::arg("gain_control") = true,
             py::arg("high_pass_filter") = true,
             R"pbdoc(
             Configure audio processing features.
             
             Args:
                 echo_cancellation (bool): Enable echo cancellation (AEC3)
                 noise_suppression (bool): Enable noise suppression
                 gain_control (bool): Enable automatic gain control
                 high_pass_filter (bool): Enable high-pass filter
             )pbdoc")
        .def("process_stream", &PyAudioProcessing::process_stream,
             py::arg("input"), py::arg("sample_rate") = 16000, py::arg("num_channels") = 1,
             R"pbdoc(
             Process capture audio stream (microphone input).
             
             Args:
                 input: Input audio data as int16 numpy array
                 sample_rate: Sample rate in Hz (8000, 16000, 32000, or 48000)
                 num_channels: Number of audio channels (1-8)
                 
             Returns:
                 Processed audio data as int16 numpy array
             )pbdoc")
        .def("process_reverse_stream", &PyAudioProcessing::process_reverse_stream,
             py::arg("input"), py::arg("sample_rate") = 16000, py::arg("num_channels") = 1,
             R"pbdoc(
             Process render audio stream (speaker output).
             This is used for echo cancellation reference.
             
             Args:
                 input: Input audio data as int16 numpy array
                 sample_rate: Sample rate in Hz (8000, 16000, 32000, or 48000)
                 num_channels: Number of audio channels (1-8)
                 
             Returns:
                 Processed audio data as int16 numpy array
             )pbdoc")
        .def("set_stream_delay_ms", &PyAudioProcessing::set_stream_delay_ms,
             py::arg("delay_ms"),
             "Set stream delay in milliseconds (0-500)")
        .def("set_stream_analog_level", &PyAudioProcessing::set_stream_analog_level,
             py::arg("level"),
             "Set analog level for gain control (0-255)")
        .def("recommended_stream_analog_level", &PyAudioProcessing::recommended_stream_analog_level,
             "Get recommended analog level from gain control")
        .def("stream_has_echo", &PyAudioProcessing::stream_has_echo,
             "Check if echo is detected in the stream")
        .def("get_statistics", &PyAudioProcessing::get_statistics,
             "Get audio processing statistics");
             
    // Module-level constants
    m.attr("__version__") = "2.1.0";
    m.attr("SAMPLE_RATE_8KHZ") = 8000;
    m.attr("SAMPLE_RATE_16KHZ") = 16000;
    m.attr("SAMPLE_RATE_32KHZ") = 32000;
    m.attr("SAMPLE_RATE_48KHZ") = 48000;
}