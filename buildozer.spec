[app]

# (str) Title of your application
title = 学习监督助手

# (str) Package name
package.name = studymonitor

# (str) Package domain (needed for android/ios packaging)
package.domain = org.study

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning
version = 0.1.0

# (list) Application requirements
requirements = python3,kivy==2.3.0,kivymd,pillow,requests,plyer,pyjnius==1.7.0,android

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/icon.png

# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE,WAKE_LOCK

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk
android.skip_update = False

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (str) The Android arch to build for
android.archs = armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The Android logcat filters to use
#android.logcat_filters = *:S python:D

# (bool) enables Android fullscreen (no title bar)
android.windowsoftinputmode = adjustResize

# (list) Android additional libraries to copy
#android.add_libs = libs/armeabi-v7a/*.so

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# Use domestic mirrors for faster downloads in China
p4a.source_url = https://github.com/kivy/python-for-android.git
p4a.bootstrap = sdl2

# 简化构建：禁用不需要的功能
p4a.android_gradle_daemon = false
p4a.no-compile-pyo = true

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
