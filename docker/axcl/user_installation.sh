#!/bin/bash
set -euo pipefail

deb_file="axcl.deb"

cleanup() {
    echo "清理临时文件"
    rm -f "${deb_file}"
}

trap cleanup ERR
trap 'echo "用户中断脚本"; cleanup; exit 130' INT

echo "安装 AXCL 驱动依赖"
sudo apt-get update
sudo apt-get install -y build-essential cmake git wget pciutils kmod udev

echo "检查 GCC 版本"
current_gcc_version=$(gcc --version | head -n1 | awk '{print $NF}')
if ! dpkg --compare-versions "${current_gcc_version}" ge "12" 2>/dev/null; then
    echo "当前 GCC 版本 ${current_gcc_version} 低于 12，安装 gcc-12"
    sudo apt-get install -y gcc-12
    sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 12
fi

arch=$(uname -m)
case "${arch}" in
    x86_64)
        download_url="https://github.com/ivanshi1108/assets/releases/download/v0.17/axcl_host_x86_64_V3.10.2_20251111020143_NO5046.deb"
        ;;
    aarch64)
        download_url="https://github.com/ivanshi1108/assets/releases/download/v0.17/axcl_host_aarch64_V3.10.2_20251111020143_NO5046.deb"
        ;;
    *)
        echo "不支持的架构：${arch}"
        exit 1
        ;;
esac

kernel_version=$(uname -r)
if dpkg -l | grep -q "linux-headers-${kernel_version}" || [[ -d "/lib/modules/${kernel_version}/build" ]]; then
    echo "已找到 ${kernel_version} 对应的 Linux headers 或内核模块构建目录"
else
    echo "缺少 Linux headers：请先执行 sudo apt-get install linux-headers-${kernel_version}"
    exit 1
fi

echo "下载 AXCL 驱动：${arch}"
wget --timeout=30 --tries=3 "${download_url}" -O "${deb_file}"

echo "安装 AXCL 驱动"
if ! sudo dpkg -i "${deb_file}"; then
    echo "驱动安装失败，尝试修复依赖后重试"
    sudo apt-get install -f -y
    sudo dpkg -i "${deb_file}"
fi

# shellcheck disable=SC1091
source /etc/profile || true

echo "验证 AXCL 驱动"
if command -v axcl-smi >/dev/null 2>&1; then
    set +e
    axcl_output=$(axcl-smi 2>&1)
    axcl_exit_code=$?
    set -e
    echo "${axcl_output}"
    if [[ ${axcl_exit_code} -ne 0 ]]; then
        echo "AXCL 驱动已安装，但未检测到可用算力卡或通信失败"
        exit 1
    fi
else
    echo "未找到 axcl-smi，AXCL 驱动安装可能失败"
    exit 1
fi

cleanup
echo "AXCL 驱动安装完成"
