#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <string>

namespace py = pybind11;

// 简单的测试类
class SimpleAudioProcessor {
public:
    SimpleAudioProcessor() : enabled_(false) {}
    
    void set_enabled(bool enabled) {
        enabled_ = enabled;
    }
    
    bool is_enabled() const {
        return enabled_;
    }
    
    std::string get_version() const {
        return "2.1.0-test";
    }
    
    py::array_t<float> process_audio(py::array_t<float> input) {
        auto buf = input.request();
        auto output = py::array_t<float>(buf.size);
        auto output_buf = output.request();
        
        // 简单的复制操作（测试用）
        std::memcpy(output_buf.ptr, buf.ptr, buf.size * sizeof(float));
        
        output.resize(buf.shape);
        return output;
    }
    
private:
    bool enabled_;
};

PYBIND11_MODULE(webrtc_apm, m) {
    m.doc() = "WebRTC Audio Processing Test Module";
    
    py::class_<SimpleAudioProcessor>(m, "AudioProcessor")
        .def(py::init<>())
        .def("set_enabled", &SimpleAudioProcessor::set_enabled)
        .def("is_enabled", &SimpleAudioProcessor::is_enabled)
        .def("get_version", &SimpleAudioProcessor::get_version)
        .def("process_audio", &SimpleAudioProcessor::process_audio);
    
    m.attr("__version__") = "2.1.0-test";
}