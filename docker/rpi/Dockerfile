# syntax=docker/dockerfile:1.4

# https://askubuntu.com/questions/972516/debian-frontend-environment-variable
ARG DEBIAN_FRONTEND=noninteractive

FROM deps AS rpi-deps
ARG TARGETARCH

# Install dependencies
RUN --mount=type=bind,source=docker/rpi/install_deps.sh,target=/deps/install_deps.sh \
    /deps/install_deps.sh

ENV DEFAULT_FFMPEG_VERSION="rpi"
ENV INCLUDED_FFMPEG_VERSIONS="${DEFAULT_FFMPEG_VERSION}:${INCLUDED_FFMPEG_VERSIONS}"

WORKDIR /opt/frigate/
COPY --from=rootfs / /

# Install axmodels
COPY docker/axera/axmodels /axmodels

# Install axpyengine
COPY docker/axera/pyaxengine/axengine-0.1.3-py3-none-any.whl /axengine-0.1.3-py3-none-any.whl
RUN pip3 install -i https://mirrors.aliyun.com/pypi/simple/ /axengine-0.1.3-py3-none-any.whl --break-system-packages \
    && rm /axengine-0.1.3-py3-none-any.whl

# Install axcl
COPY docker/rpi/axcl/3.6.5/axcl_host_aarch64_V3.6.5_20250908154509_NO4973.deb /axcl_host_aarch64_V3.6.5_20250908154509_NO4973.deb
RUN mkdir /unpack_axcl && \
    dpkg-deb -x /axcl_host_aarch64_V3.6.5_20250908154509_NO4973.deb /unpack_axcl
RUN cp -R /unpack_axcl/usr/bin/axcl /usr/bin/
RUN cp -R /unpack_axcl/usr/lib/axcl /usr/lib/
RUN rm -rf /unpack_axcl /axcl_host_aarch64_V3.6.5_20250908154509_NO4973.deb

# Install axcl ffmpeg
RUN mkdir /usr/lib/ffmpeg/axcl
COPY docker/rpi/axcl/3.6.5/ffmpeg /usr/lib/ffmpeg/axcl/ffmpeg
COPY docker/rpi/axcl/3.6.5/ffprobe /usr/lib/ffmpeg/axcl/ffprobe

# Set ldconfig path
RUN echo "/usr/lib/axcl" > /etc/ld.so.conf.d/ax.conf

# Set env
ENV PATH="$PATH:/usr/bin/axcl"
ENV LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/lib/axcl"

ENTRYPOINT ["sh", "-c", "ldconfig && exec /init"]
