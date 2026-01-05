target wheels {
  dockerfile = "docker/axera/Dockerfile_ubuntu"
  platforms = ["linux/arm64"]
  target = "wheels"
}

target deps {
  dockerfile = "docker/axera/Dockerfile_ubuntu"
  platforms = ["linux/arm64"]
  target = "deps"
}

target rootfs {
  dockerfile = "docker/axera/Dockerfile_ubuntu"
  platforms = ["linux/arm64"]
  target = "rootfs"
}

target ax650 {
  dockerfile = "docker/axera/Dockerfile_ax650"
  contexts = {
    wheels = "target:wheels",
    deps = "target:deps",
    rootfs = "target:rootfs"
  }
  platforms = ["linux/arm64"]
}