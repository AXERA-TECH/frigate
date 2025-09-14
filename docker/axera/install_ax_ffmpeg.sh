#!/bin/bash

if [[ "${TARGETARCH}" == "arm64" ]]; then
    #ffmpeg ax
    mkdir -p /usr/lib/ffmpeg/ax
    wget -qO ffmpeg.tar.gz "https://github.com/ivanshi1108/assets/releases/download/3.6.2/ffmpeg-ax-7.1-e463d11f1-yuv420p.tar.gz"
    tar -xzf ffmpeg.tar.gz -C /usr/lib/ffmpeg/ax bin/
    rm -f ffmpeg.tar.gz
fi