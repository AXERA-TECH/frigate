# Axera 统一分支维护说明

## 分支模型

- `axera-dev` 是唯一长期维护分支，基线来自上游 `origin/dev`。
- 平台差异通过 Docker target、CI 矩阵、release 镜像标签和运行时环境表达，不再为 AX650、AXCL、RK-AXCL、RPi-AXCL 分别维护长期代码分支。
- 无迁移，直接替换旧的多分支维护方式。

## 允许长期存在的 Axera 增量

Axera 补丁应尽量集中在以下范围：

- `docker/axera/**`：AX650 SoC 镜像构建。
- `docker/axcl/**`：AXCL 算力卡镜像构建与 host 驱动安装脚本。
- `.github/workflows/ci.yml`：Axera 镜像构建任务。
- `.github/workflows/release.yml`：Axera release 镜像标签。
- `.github/workflows/ax.yml`：手动构建 tar 与 Hugging Face 上传入口。
- `frigate/ffmpeg_presets.py`：`preset-axera-*` 相关 preset。
- `frigate/config/camera/ffmpeg.py`：仅保留 AX650 镜像通过 `FRIGATE_AXERA_TARGET=ax650` 启用的默认值。
- `frigate/test/test_ffmpeg_presets.py`：Axera preset 测试。
- 文档中 Axera 镜像、部署、preset 和维护说明。

不要整体覆盖以下上游文件：

- `frigate/detectors/plugins/axengine.py`
- `docker/main/Dockerfile`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `web/src/**`

如必须修改这些区域，应以最小补丁方式接入，不回退上游逻辑。

## 同步上游流程

日常同步：

```bash
git checkout axera-dev
git fetch origin --tags
git merge origin/dev
```

冲突处理原则：

1. 默认保留上游新逻辑。
2. 重新应用 Axera 最小增量。
3. 不从旧 Axera 分支整文件覆盖。
4. 确认 Axera delta 仍集中在允许范围内。

同步后审计：

```bash
git diff --stat origin/dev...HEAD
git diff --name-only origin/dev...HEAD
```

如果差异突然扩散到 `frigate/api/**`、`frigate/config/**`、`frigate/video.py`、`web/src/**` 等大范围上游核心文件，需要重新检查是否误合入旧代码。

## Release 流程

推荐使用 `vX.Y.Z-axera` 作为 Git tag，release workflow 会将末尾的 `-axera` 从 Docker 版本号中去掉。例如：

- Git tag：`v0.19.0-axera`
- Docker tags：
  - `0.19.0-ax650`
  - `0.19.0-x86-axcl`
  - `0.19.0-rk-axcl`
  - `0.19.0-rpi-axcl`

稳定版本还会发布：

- `stable-ax650`
- `stable-x86-axcl`
- `stable-rk-axcl`
- `stable-rpi-axcl`

## 验证清单

每次同步上游或发布前至少执行：

```bash
python3 -u -m unittest frigate.test.test_ffmpeg_presets
python3 -u -m unittest frigate.test.test_config
python3 -u -m unittest frigate.test.test_object_detector
```

如本机具备 Docker buildx 环境，执行 smoke build：

```bash
docker buildx bake --file=docker/axera/ax650.hcl ax650
docker buildx bake --file=docker/axcl/x86-axcl.hcl x86-axcl
docker buildx bake --file=docker/rockchip/rk.hcl --file=docker/axcl/rk-axcl.hcl rk-axcl
docker buildx bake --file=docker/rpi/rpi.hcl --file=docker/axcl/rpi-axcl.hcl rpi-axcl
```
