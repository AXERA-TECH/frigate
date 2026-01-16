#!/bin/bash

if [[ "${TARGETARCH}" == "arm64" ]]; then
    #ffmpeg ax
    mkdir -p /usr/lib/ffmpeg/ax/bin
    wget -qO /usr/lib/ffmpeg/ax/bin/ffprobe "https://github.com/ivanshi1108/assets/releases/download/v0.17/ffprobe"
    wget -qO /usr/lib/ffmpeg/ax/bin/ffmpeg "https://github.com/ivanshi1108/assets/releases/download/v0.17/ffmpeg"
    chmod 755 /usr/lib/ffmpeg/ax/bin/ffprobe
    chmod 755 /usr/lib/ffmpeg/ax/bin/ffmpeg
fi