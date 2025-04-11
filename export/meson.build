export_sources = [
  'export.cc'
]

export_headers = [
  'export.h'
]

install_headers(export_headers,
  subdir: 'export'
)

top_incdir = include_directories('..')

host_system = host_machine.system()

if host_system = 'ios'
  libwebrtc_apm = static_library('webrtc_apm',
    export_sources,
    name_prefix: 'lib',
    c_args : common_cflags,
    cpp_args : common_cxxflags,
    dependencies: [audio_processing_dep, absl_dep],
    include_directories: top_incdir,
    link_with: [libwebrtc_audio_processing],
    install: true
  )
else
  libwebrtc_apm = shared_library('webrtc_apm',
    export_sources,
    name_prefix: 'lib',
    c_args : common_cflags,
    cpp_args : common_cxxflags,
    dependencies: [audio_processing_dep, absl_dep],
    include_directories: top_incdir,
    link_with: [libwebrtc_audio_processing],
    install: true
  )
endif