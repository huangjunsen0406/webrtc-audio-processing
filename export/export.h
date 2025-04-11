#ifndef WEBRTC_EXPORT_H
#define WEBRTC_EXPORT_H

#include <memory>
#include <stdint.h>
#include <stddef.h>
#include <webrtc/rtc_base/system/rtc_export.h>
#include <webrtc/modules/audio_processing/include/audio_processing.h>

#ifdef __cplusplus
extern "C" {
#endif

class AudioProcessingHandle {
  public:
    AudioProcessingHandle();
    void ApplyConfig(const webrtc::AudioProcessing::Config* config);
    int ProcessReverseStream(const int16_t* const src, const webrtc::StreamConfig* input_config,
      const webrtc::StreamConfig* output_config, int16_t* const dest);
    int ProcessStream(const int16_t* const src, const webrtc::StreamConfig* input_config,
      const webrtc::StreamConfig* output_config, int16_t* const dest);
    void SetStreamDelayMs(int delay_ms);
    webrtc::StreamConfig CreateStreamConfig(int sample_rate, size_t num_channels);
  private:
    rtc::scoped_refptr<webrtc::AudioProcessing> apm_;
    int analog_level_ = 255;
};

RTC_EXPORT AudioProcessingHandle* WebRTC_APM_Create();

RTC_EXPORT void WebRTC_APM_Destroy(AudioProcessingHandle* handle);

RTC_EXPORT webrtc::StreamConfig* WebRTC_APM_CreateStreamConfig(int sample_rate, size_t num_channels);

RTC_EXPORT void WebRTC_APM_DestroyStreamConfig(webrtc::StreamConfig* handle);

RTC_EXPORT void WebRTC_APM_ApplyConfig(AudioProcessingHandle* handle, const webrtc::AudioProcessing::Config* config);

RTC_EXPORT int WebRTC_APM_ProcessReverseStream(AudioProcessingHandle* handle, const int16_t* const src, const webrtc::StreamConfig* input_config,
  const webrtc::StreamConfig* output_config,  int16_t* const dest);

RTC_EXPORT int WebRTC_APM_ProcessStream(AudioProcessingHandle* handle, const int16_t* const src, const webrtc::StreamConfig* input_config,
  const webrtc::StreamConfig* output_config, int16_t* const dest);

RTC_EXPORT void WebRTC_APM_SetStreamDelayMs(AudioProcessingHandle* handle, int delay_ms);

#ifdef __cplusplus
}
#endif

#endif // WEBRTC_EXPORT_H