#include "export.h"
#include <iostream>

AudioProcessingHandle::AudioProcessingHandle()
    : apm_(webrtc::AudioProcessingBuilder().Create()) {}

void AudioProcessingHandle::ApplyConfig(const webrtc::AudioProcessing::Config* config) {
    apm_->ApplyConfig(*config);
}

int AudioProcessingHandle::ProcessReverseStream(const int16_t* const src, const webrtc::StreamConfig* input_config,
    const webrtc::StreamConfig* output_config, int16_t* const dest) {
    return apm_->ProcessReverseStream(src, *input_config, *output_config, dest);
}

int AudioProcessingHandle::ProcessStream(const int16_t* const src, const webrtc::StreamConfig* input_config,
    const webrtc::StreamConfig* output_config, int16_t* const dest) {
    apm_->set_stream_analog_level(analog_level_);
    auto result = apm_->ProcessStream(src, *input_config, *output_config, dest);
    analog_level_ = apm_->recommended_stream_analog_level();
    return result;
}

void AudioProcessingHandle::SetStreamDelayMs(int delay_ms) {
    apm_->set_stream_delay_ms(delay_ms);
}

// -------------------- Export functions ------------------ //

AudioProcessingHandle* WebRTC_APM_Create() {
    return new AudioProcessingHandle();
}

void WebRTC_APM_Destroy(AudioProcessingHandle* handle) {
    if (!handle) return;
    delete handle;
}

webrtc::StreamConfig* WebRTC_APM_CreateStreamConfig(int sample_rate, size_t num_channels) {
    return new webrtc::StreamConfig(sample_rate, num_channels);
}

void WebRTC_APM_DestroyStreamConfig(webrtc::StreamConfig* handle) {
    if (!handle) return;
    delete handle;
}

void WebRTC_APM_ApplyConfig(AudioProcessingHandle* handle, const webrtc::AudioProcessing::Config* config) {
    if (!handle) return;
    handle->ApplyConfig(config);
}

int WebRTC_APM_ProcessReverseStream(AudioProcessingHandle* handle, const int16_t* const src, const webrtc::StreamConfig* input_config,
    const webrtc::StreamConfig* output_config, int16_t* const dest) {
    if (!handle || !src || !dest || !input_config || !output_config) return -1;
    return handle->ProcessReverseStream(src, input_config, output_config, dest);
}

int WebRTC_APM_ProcessStream(AudioProcessingHandle* handle, const int16_t* const src, const webrtc::StreamConfig* input_config,
    const webrtc::StreamConfig* output_config, int16_t* const dest) {
    if (!handle || !src || !dest || !input_config || !output_config) return -1;
    return handle->ProcessStream(src, input_config, output_config, dest);
}

void WebRTC_APM_SetStreamDelayMs(AudioProcessingHandle* handle, int delay_ms) {
    if (!handle) return;
    handle->SetStreamDelayMs(delay_ms);
}