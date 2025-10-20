target rpi-axcl {
  dockerfile = "docker/axcl/Dockerfile"
  contexts = {
    frigate = "target:rpi",
  }
  platforms = ["linux/arm64"]
}