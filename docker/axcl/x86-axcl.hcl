target frigate {
  dockerfile = "docker/main/Dockerfile"
  platforms = ["linux/amd64"]
  target = "frigate"
}

target x86-axcl {
  dockerfile = "docker/axcl/Dockerfile"
  contexts = {
    frigate = "target:frigate",
  }
  platforms = ["linux/amd64"]
}