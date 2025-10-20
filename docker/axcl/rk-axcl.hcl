target rk-axcl {
  dockerfile = "docker/axcl/Dockerfile"
  contexts = {
    frigate = "target:rk",
  }
  platforms = ["linux/arm64"]
}