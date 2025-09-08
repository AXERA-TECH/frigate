#!/bin/bash

if [[ "${TARGETARCH}" == "arm64" ]]; then
    #ffmpeg ax
    mkdir -p /usr/lib/ffmpeg/ax
    wget -qO ffmpeg.tar.gz "https://github.com/ivanshi1108/assets/releases/download/3.6.2/ffmpeg-ax-7.1-121cbba3a-yuv420p.tar.gz"
    tar -xzf ffmpeg.tar.gz -C /usr/lib/ffmpeg/ax bin/
    rm -f ffmpeg.tar.gz

    # #axera lib
    # wget -qO lib.tar.gz "https://github.com/ivanshi1108/assets/releases/download/3.6.2/lib.tar.gz"
    # tar -xzf lib.tar.gz -C /usr/lib/ --strip-components 1
    # rm -f lib.tar.gz
    # wget -P /usr/lib/ "https://github.com/ivanshi1108/assets/releases/download/3.6.2/libexif.so"
fi