[app]

# (str) Title of your application
title = ROM Downloader

# (str) Package name
package.name = romsdownloader

# (str) Package domain (needed for android/ios packaging)
package.domain = org.example

# (str) Source code where the main.py live
source.dir = .

# (str) Main script name
main.py = src/index.py

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,ttf,json

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,*.json

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,pygame
requirements = python3,pygame,requests,nsz

# (str) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.pygame = ../../pygame

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/assets/images/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/assets/images/icon.png

# (str) Supported orientation (landscape, portrait or all)
orientation = landscape

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 23c

# (int) Android SDK version to use
android.sdk = 31

# (str) Android SDK build tools version
android.sdk_build_tools = 31.0.0

# (str) Android entry point, default is ok for pygame
android.entrypoint = org.renpy.android.PythonActivity

# (str) Full name including package path of the Java class that implements Android Activity
android.activity_class_name = org.renpy.android.PythonActivity

# (str) python-for-android branch to use, defaults to master
#p4a.branch = master

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk).
android.release_artifact = apk

# (str) Bootstrap to use for android builds
# Run "buildozer android list_bootstraps" to see available options
p4a.bootstrap = pygame

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1