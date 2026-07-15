#!/bin/bash
set -euo pipefail

if [[ "${TARGETARCH:-}" != "arm64" ]]; then
    echo "跳过 Axera FFmpeg 安装：AX650 镜像仅支持 arm64，当前为 ${TARGETARCH:-unknown}"
    exit 0
fi

AX_FFMPEG_BASE_URL="${AX_FFMPEG_BASE_URL:-https://github.com/ivanshi1108/assets/releases/download/v0.17}"
AX_FFMPEG_DIR="/usr/lib/ffmpeg/ax/bin"

mkdir -p "${AX_FFMPEG_DIR}"
wget -qO "${AX_FFMPEG_DIR}/ffprobe" "${AX_FFMPEG_BASE_URL}/ffprobe"
wget -qO "${AX_FFMPEG_DIR}/ffmpeg" "${AX_FFMPEG_BASE_URL}/ffmpeg"
chmod 755 "${AX_FFMPEG_DIR}/ffprobe" "${AX_FFMPEG_DIR}/ffmpeg"
