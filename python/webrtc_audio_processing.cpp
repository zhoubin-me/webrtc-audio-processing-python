#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <api/audio/audio_processing.h>
#include <api/scoped_refptr.h>

// Include VAD header directly from source tree
extern "C" {
    #include "../webrtc/common_audio/vad/include/webrtc_vad.h"
}

namespace py = pybind11;

// C++ wrapper class for WebRTC VAD
class WebRTCVAD {
private:
    VadInst* vad_;

public:
    WebRTCVAD() : vad_(nullptr) {
        vad_ = WebRtcVad_Create();
        if (!vad_ || WebRtcVad_Init(vad_) != 0) {
            if (vad_) WebRtcVad_Free(vad_);
            throw std::runtime_error("Failed to create and initialize VAD instance");
        }
    }

    ~WebRTCVAD() {
        if (vad_) {
            WebRtcVad_Free(vad_);
        }
    }

    bool set_mode(int mode) {
        return WebRtcVad_set_mode(vad_, mode) == 0;
    }

    int is_speech(py::array_t<int16_t> audio_frame, int sample_rate = 16000) {
        auto buf = audio_frame.request();
        if (buf.ndim != 1) {
            throw std::runtime_error("Input array must be 1-dimensional");
        }
        return WebRtcVad_Process(vad_, sample_rate, 
                               static_cast<const int16_t*>(buf.ptr), 
                               buf.shape[0]);
    }

    static bool is_valid_config(int sample_rate, size_t frame_length) {
        return WebRtcVad_ValidRateAndFrameLength(sample_rate, frame_length) == 0;
    }
};

PYBIND11_MODULE(webrtc_audio_processing, m) {
    m.doc() = "Python bindings for WebRTC Audio Processing";

    // StreamConfig class
    py::class_<webrtc::StreamConfig>(m, "StreamConfig")
        .def(py::init<int, size_t>(), 
             py::arg("sample_rate_hz") = 0, 
             py::arg("num_channels") = 0)
        .def("set_sample_rate_hz", &webrtc::StreamConfig::set_sample_rate_hz)
        .def("set_num_channels", &webrtc::StreamConfig::set_num_channels)
        .def("sample_rate_hz", &webrtc::StreamConfig::sample_rate_hz)
        .def("num_channels", &webrtc::StreamConfig::num_channels)
        .def("num_frames", &webrtc::StreamConfig::num_frames)
        .def("num_samples", &webrtc::StreamConfig::num_samples);

    // AudioProcessing Config structures
    py::class_<webrtc::AudioProcessing::Config>(m, "Config")
        .def(py::init<>())
        .def_readwrite("high_pass_filter", &webrtc::AudioProcessing::Config::high_pass_filter)
        .def_readwrite("echo_canceller", &webrtc::AudioProcessing::Config::echo_canceller)
        .def_readwrite("noise_suppression", &webrtc::AudioProcessing::Config::noise_suppression)
        .def_readwrite("gain_controller1", &webrtc::AudioProcessing::Config::gain_controller1)
        .def_readwrite("gain_controller2", &webrtc::AudioProcessing::Config::gain_controller2);

    // Config sub-structures
    py::class_<webrtc::AudioProcessing::Config::HighPassFilter>(m, "HighPassFilter")
        .def(py::init<>())
        .def_readwrite("enabled", &webrtc::AudioProcessing::Config::HighPassFilter::enabled)
        .def_readwrite("apply_in_full_band", &webrtc::AudioProcessing::Config::HighPassFilter::apply_in_full_band);

    py::class_<webrtc::AudioProcessing::Config::EchoCanceller>(m, "EchoCanceller")
        .def(py::init<>())
        .def_readwrite("enabled", &webrtc::AudioProcessing::Config::EchoCanceller::enabled)
        .def_readwrite("mobile_mode", &webrtc::AudioProcessing::Config::EchoCanceller::mobile_mode)
        .def_readwrite("export_linear_aec_output", &webrtc::AudioProcessing::Config::EchoCanceller::export_linear_aec_output)
        .def_readwrite("enforce_high_pass_filtering", &webrtc::AudioProcessing::Config::EchoCanceller::enforce_high_pass_filtering);

    py::class_<webrtc::AudioProcessing::Config::NoiseSuppression>(m, "NoiseSuppression")
        .def(py::init<>())
        .def_readwrite("enabled", &webrtc::AudioProcessing::Config::NoiseSuppression::enabled)
        .def_readwrite("level", &webrtc::AudioProcessing::Config::NoiseSuppression::level)
        .def_readwrite("analyze_linear_aec_output_when_available", 
                      &webrtc::AudioProcessing::Config::NoiseSuppression::analyze_linear_aec_output_when_available);

    // NoiseSuppression Level enum
    py::enum_<webrtc::AudioProcessing::Config::NoiseSuppression::Level>(m, "NoiseSuppressionLevel")
        .value("LOW", webrtc::AudioProcessing::Config::NoiseSuppression::kLow)
        .value("MODERATE", webrtc::AudioProcessing::Config::NoiseSuppression::kModerate)
        .value("HIGH", webrtc::AudioProcessing::Config::NoiseSuppression::kHigh)
        .value("VERY_HIGH", webrtc::AudioProcessing::Config::NoiseSuppression::kVeryHigh);

    py::class_<webrtc::AudioProcessing::Config::GainController1>(m, "GainController1")
        .def(py::init<>())
        .def_readwrite("enabled", &webrtc::AudioProcessing::Config::GainController1::enabled)
        .def_readwrite("mode", &webrtc::AudioProcessing::Config::GainController1::mode)
        .def_readwrite("target_level_dbfs", &webrtc::AudioProcessing::Config::GainController1::target_level_dbfs)
        .def_readwrite("compression_gain_db", &webrtc::AudioProcessing::Config::GainController1::compression_gain_db)
        .def_readwrite("enable_limiter", &webrtc::AudioProcessing::Config::GainController1::enable_limiter);

    // GainController1 Mode enum
    py::enum_<webrtc::AudioProcessing::Config::GainController1::Mode>(m, "GainController1Mode")
        .value("ADAPTIVE_ANALOG", webrtc::AudioProcessing::Config::GainController1::kAdaptiveAnalog)
        .value("ADAPTIVE_DIGITAL", webrtc::AudioProcessing::Config::GainController1::kAdaptiveDigital)
        .value("FIXED_DIGITAL", webrtc::AudioProcessing::Config::GainController1::kFixedDigital);

    py::class_<webrtc::AudioProcessing::Config::GainController2>(m, "GainController2")
        .def(py::init<>())
        .def_readwrite("enabled", &webrtc::AudioProcessing::Config::GainController2::enabled);

    // AudioProcessing class
    py::class_<webrtc::AudioProcessing>(m, "AudioProcessing")
        .def("Initialize", py::overload_cast<>(&webrtc::AudioProcessing::Initialize))
        .def("ApplyConfig", &webrtc::AudioProcessing::ApplyConfig)
        .def("ProcessStream", 
             [](webrtc::AudioProcessing& self, 
                py::array_t<int16_t> src,
                const webrtc::StreamConfig& input_config,
                const webrtc::StreamConfig& output_config,
                py::array_t<int16_t> dest) -> int {
                 auto src_buf = src.request();
                 auto dest_buf = dest.request();
                 return self.ProcessStream(
                     static_cast<const int16_t*>(src_buf.ptr),
                     input_config,
                     output_config,
                     static_cast<int16_t*>(dest_buf.ptr));
             })
        .def("ProcessReverseStream",
             [](webrtc::AudioProcessing& self,
                py::array_t<int16_t> src,
                const webrtc::StreamConfig& input_config,
                const webrtc::StreamConfig& output_config,
                py::array_t<int16_t> dest) -> int {
                 auto src_buf = src.request();
                 auto dest_buf = dest.request();
                 return self.ProcessReverseStream(
                     static_cast<const int16_t*>(src_buf.ptr),
                     input_config,
                     output_config,
                     static_cast<int16_t*>(dest_buf.ptr));
             })
        .def("set_stream_delay_ms", &webrtc::AudioProcessing::set_stream_delay_ms)
        .def("stream_delay_ms", &webrtc::AudioProcessing::stream_delay_ms)
        .def("set_stream_analog_level", &webrtc::AudioProcessing::set_stream_analog_level)
        .def("recommended_stream_analog_level", &webrtc::AudioProcessing::recommended_stream_analog_level)
        .def("set_stream_key_pressed", &webrtc::AudioProcessing::set_stream_key_pressed)
        .def("GetConfig", &webrtc::AudioProcessing::GetConfig);

    // AudioProcessingBuilder class
    py::class_<webrtc::AudioProcessingBuilder>(m, "AudioProcessingBuilder")
        .def(py::init<>())
        .def("SetConfig", 
             [](webrtc::AudioProcessingBuilder& self, const webrtc::AudioProcessing::Config& config) -> webrtc::AudioProcessingBuilder& {
                 return self.SetConfig(config);
             },
             py::return_value_policy::reference_internal)
        .def("Create", 
             [](webrtc::AudioProcessingBuilder& self) -> webrtc::AudioProcessing* {
                 auto scoped_ptr = self.Create();
                 // Note: This transfers ownership to Python - be careful with memory management
                 scoped_ptr->AddRef();
                 return scoped_ptr.get();
             },
             py::return_value_policy::take_ownership);

    // Constants
    m.attr("DEFAULT_SAMPLE_RATE") = 32000;
    m.attr("DEFAULT_CHANNELS") = 1;
    m.attr("DEFAULT_BLOCK_MS") = 10;

    // Error codes
    py::enum_<webrtc::AudioProcessing::Error>(m, "Error")
        .value("NO_ERROR", webrtc::AudioProcessing::kNoError)
        .value("UNSPECIFIED_ERROR", webrtc::AudioProcessing::kUnspecifiedError)
        .value("CREATION_FAILED_ERROR", webrtc::AudioProcessing::kCreationFailedError)
        .value("UNSUPPORTED_COMPONENT_ERROR", webrtc::AudioProcessing::kUnsupportedComponentError)
        .value("UNSUPPORTED_FUNCTION_ERROR", webrtc::AudioProcessing::kUnsupportedFunctionError)
        .value("NULL_POINTER_ERROR", webrtc::AudioProcessing::kNullPointerError)
        .value("BAD_PARAMETER_ERROR", webrtc::AudioProcessing::kBadParameterError)
        .value("BAD_SAMPLE_RATE_ERROR", webrtc::AudioProcessing::kBadSampleRateError)
        .value("BAD_DATA_LENGTH_ERROR", webrtc::AudioProcessing::kBadDataLengthError)
        .value("BAD_NUMBER_CHANNELS_ERROR", webrtc::AudioProcessing::kBadNumberChannelsError)
        .value("FILE_ERROR", webrtc::AudioProcessing::kFileError)
        .value("STREAM_PARAMETER_NOT_SET_ERROR", webrtc::AudioProcessing::kStreamParameterNotSetError)
        .value("NOT_ENABLED_ERROR", webrtc::AudioProcessing::kNotEnabledError)
        .value("BAD_STREAM_PARAMETER_WARNING", webrtc::AudioProcessing::kBadStreamParameterWarning);

    // Utility functions
    m.def("GetFrameSize", &webrtc::AudioProcessing::GetFrameSize, "Get frame size for given sample rate");

    // WebRTC VAD (Voice Activity Detection) wrapper class
    py::class_<WebRTCVAD>(m, "VAD")
        .def(py::init<>(), "Create and initialize a new VAD instance")
        .def("set_mode", &WebRTCVAD::set_mode,
             py::arg("mode"),
             "Set VAD aggressiveness mode (0=least aggressive, 3=most aggressive)")
        .def("is_speech", &WebRTCVAD::is_speech,
             py::arg("audio_frame"), py::arg("sample_rate") = 16000,
             "Check if audio frame contains speech (returns 1=speech, 0=silence, -1=error)")
        .def_static("is_valid_config", &WebRTCVAD::is_valid_config,
             py::arg("sample_rate"), py::arg("frame_length"),
             "Check if sample rate and frame length combination is valid");
}