# Python绑定的meson.build文件

# 查找Python和pybind11
python = import('python').find_installation()

# 尝试查找pybind11
pybind11_dep = dependency('pybind11', required: false)
if not pybind11_dep.found()
  # 如果没有找到pybind11，使用Python模块方式
  pybind11_dep = python.dependency('pybind11', required: true)
endif

# 包含路径
python_inc = include_directories('.')
webrtc_inc = include_directories('..')

# Python绑定模块（使用简化的测试版本）
python_module = python.extension_module(
    'webrtc_apm',
    'simple_test.cpp',
    include_directories: [python_inc],
    dependencies: [pybind11_dep],
    cpp_args: ['-DVERSION_INFO="' + meson.project_version() + '"'],
    install: true,
    subdir: 'webrtc_apm'
)

# 安装Python包文件
python.install_sources(
    '__init__.py',
    subdir: 'webrtc_apm'
)