# syntax=docker/dockerfile:1.6

# https://askubuntu.com/questions/972516/debian-frontend-environment-variable
ARG DEBIAN_FRONTEND=noninteractive

# Globally set pip break-system-packages option to avoid having to specify it every time
ARG PIP_BREAK_SYSTEM_PACKAGES=1

FROM wheels as rk-wheels
COPY docker/main/requirements-wheels.txt /requirements-wheels.txt
COPY docker/rockchip/requirements-wheels-rk.txt /requirements-wheels-rk.txt
RUN sed -i "/https:\/\//d" /requirements-wheels.txt
RUN sed -i "/onnxruntime/d" /requirements-wheels.txt
RUN pip3 wheel --wheel-dir=/rk-wheels -c /requirements-wheels.txt -r /requirements-wheels-rk.txt
RUN rm -rf /rk-wheels/opencv_python-*
RUN rm -rf /rk-wheels/torch-*

FROM deps AS rk-frigate
ARG TARGETARCH
ARG PIP_BREAK_SYSTEM_PACKAGES

RUN --mount=type=bind,from=rk-wheels,source=/rk-wheels,target=/deps/rk-wheels \
    pip3 install --no-deps -U /deps/rk-wheels/*.whl

WORKDIR /opt/frigate/
COPY --from=rootfs / /
COPY docker/rockchip/COCO /COCO
COPY docker/rockchip/conv2rknn.py /opt/conv2rknn.py

ADD https://github.com/MarcA711/rknn-toolkit2/releases/download/v2.3.2/librknnrt.so /usr/lib/

ADD --chmod=111 https://github.com/MarcA711/Rockchip-FFmpeg-Builds/releases/download/6.1-11/ffmpeg /usr/lib/ffmpeg/6.0/bin/
ADD --chmod=111 https://github.com/MarcA711/Rockchip-FFmpeg-Builds/releases/download/6.1-11/ffprobe /usr/lib/ffmpeg/6.0/bin/
ADD --chmod=111 https://github.com/MarcA711/Rockchip-FFmpeg-Builds/releases/download/7.1-1/ffmpeg /usr/lib/ffmpeg/7.0/bin/
ADD --chmod=111 https://github.com/MarcA711/Rockchip-FFmpeg-Builds/releases/download/7.1-1/ffprobe /usr/lib/ffmpeg/7.0/bin/
ENV DEFAULT_FFMPEG_VERSION="6.0"
ENV INCLUDED_FFMPEG_VERSIONS="${DEFAULT_FFMPEG_VERSION}:${INCLUDED_FFMPEG_VERSIONS}"

# Install axmodels
RUN mkdir -p /axmodels \
    && wget https://github.com/ivanshi1108/assets/releases/download/v0.16.2/yolov5s_320.axmodel -O /axmodels/yolov5s_320.axmodel

# Install axpyengine
RUN wget https://github.com/AXERA-TECH/pyaxengine/releases/download/0.1.3.rc1/axengine-0.1.3-py3-none-any.whl -O /axengine-0.1.3-py3-none-any.whl
RUN pip3 install -i https://mirrors.aliyun.com/pypi/simple/ /axengine-0.1.3-py3-none-any.whl \
    && rm /axengine-0.1.3-py3-none-any.whl

# Install axcl
RUN wget https://github.com/ivanshi1108/assets/releases/download/v0.16.2/axcl_host_aarch64_V3.6.5_20250908154509_NO4973.deb -O /axcl_host_aarch64_V3.6.5_20250908154509_NO4973.deb
RUN mkdir /unpack_axcl && \
    dpkg-deb -x /axcl_host_aarch64_V3.6.5_20250908154509_NO4973.deb /unpack_axcl
RUN cp -R /unpack_axcl/usr/bin/axcl /usr/bin/
RUN cp -R /unpack_axcl/usr/lib/axcl /usr/lib/
RUN rm -rf /unpack_axcl /axcl_host_aarch64_V3.6.5_20250908154509_NO4973.deb

# Install axcl ffmpeg
RUN mkdir /usr/lib/ffmpeg/axcl
RUN wget https://github.com/ivanshi1108/assets/releases/download/v0.16.2/ffmpeg -O /usr/lib/ffmpeg/axcl/ffmpeg
RUN wget https://github.com/ivanshi1108/assets/releases/download/v0.16.2/ffprobe -O /usr/lib/ffmpeg/axcl/ffprobe
RUN chmod +x /usr/lib/ffmpeg/axcl/ffmpeg
RUN chmod +x /usr/lib/ffmpeg/axcl/ffprobe

# Set ldconfig path
RUN echo "/usr/lib/axcl" > /etc/ld.so.conf.d/ax.conf

# Set env
ENV PATH="$PATH:/usr/bin/axcl"
ENV LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/lib/axcl"

ENTRYPOINT ["sh", "-c", "ldconfig && exec /init"]
