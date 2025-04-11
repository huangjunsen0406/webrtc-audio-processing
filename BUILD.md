`cmd.exe /c "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" -arch=amd64 && bash`
`meson setup --wipe build --cross-file android_armv7a.txt`
`meson compile -C build`

## 修改

1. 增加了导出目录export
2. 根目录meson.build文件最后增加了一行`subdir('export')`