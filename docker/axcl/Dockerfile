# syntax=docker/dockerfile:1.6

# https://askubuntu.com/questions/972516/debian-frontend-environment-variable
ARG DEBIAN_FRONTEND=noninteractive

# Globally set pip break-system-packages option to avoid having to specify it every time
ARG PIP_BREAK_SYSTEM_PACKAGES=1

FROM frigate AS frigate-axcl
ARG TARGETARCH
ARG PIP_BREAK_SYSTEM_PACKAGES

# Install axpyengine
RUN wget https://github.com/AXERA-TECH/pyaxengine/releases/download/0.1.3.rc1/axengine-0.1.3-py3-none-any.whl -O /axengine-0.1.3-py3-none-any.whl
RUN pip3 install -i https://mirrors.aliyun.com/pypi/simple/ /axengine-0.1.3-py3-none-any.whl \
    && rm /axengine-0.1.3-py3-none-any.whl

# Set ldconfig path
RUN echo "/usr/lib/axcl" > /etc/ld.so.conf.d/ax.conf

# Set env
ENV PATH="$PATH:/usr/bin/axcl"
ENV LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/lib/axcl"

ENTRYPOINT ["sh", "-c", "ldconfig && exec /init"]