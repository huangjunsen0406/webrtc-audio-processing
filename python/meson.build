# Python绑定的meson.build文件

# 查找Python和pybind11
python = import('python').find_installation()
pybind11_dep = dependency('pybind11', required: true, fallback: ['pybind11', 'pybind11_dep'])

# 包含路径
python_inc = include_directories('.')
webrtc_inc = include_directories('..')

# Python绑定模块
python_module = python.extension_module(
    'webrtc_apm',
    'webrtc_apm_bindings.cpp',
    include_directories: [webrtc_inc, python_inc],
    dependencies: [pybind11_dep, audio_processing_dep],
    cpp_args: ['-DVERSION_INFO="' + meson.project_version() + '"'],
    install: true,
    subdir: 'webrtc_apm'
)

# 安装Python包文件
python.install_sources(
    '__init__.py',
    subdir: 'webrtc_apm'
)