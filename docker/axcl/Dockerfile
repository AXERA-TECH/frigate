# syntax=docker/dockerfile:1.6

ARG DEBIAN_FRONTEND=noninteractive
ARG PIP_BREAK_SYSTEM_PACKAGES=1

FROM frigate AS frigate-axcl
ARG TARGETARCH
ARG PIP_BREAK_SYSTEM_PACKAGES

RUN echo "/usr/lib/axcl" > /etc/ld.so.conf.d/ax.conf

ENV FRIGATE_AXERA_TARGET="axcl"
ENV PATH="${PATH}:/usr/bin/axcl"
ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/usr/lib/axcl"

ENTRYPOINT ["sh", "-c", "ldconfig && exec /init"]
