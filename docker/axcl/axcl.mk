BOARDS += x86-axcl rk-axcl rpi-axcl

x86-axcl:
	docker buildx bake --file=docker/axcl/x86-axcl.hcl x86-axcl \
		--set x86-axcl.tags=frigate:latest-x86-axcl

build-x86-axcl: version
	docker buildx bake --file=docker/axcl/x86-axcl.hcl x86-axcl \
		--set x86-axcl.tags=$(IMAGE_REPO):${GITHUB_REF_NAME}-$(COMMIT_HASH)-x86-axcl

push-x86-axcl: build-x86-axcl
	docker buildx bake --file=docker/axcl/x86-axcl.hcl x86-axcl \
		--set x86-axcl.tags=$(IMAGE_REPO):${GITHUB_REF_NAME}-$(COMMIT_HASH)-x86-axcl \
		--push

rk-axcl:
	docker buildx bake --file=docker/rockchip/rk.hcl --file=docker/axcl/rk-axcl.hcl rk-axcl \
		--set rk-axcl.tags=frigate:latest-rk-axcl

build-rk-axcl: version
	docker buildx bake --file=docker/rockchip/rk.hcl --file=docker/axcl/rk-axcl.hcl rk-axcl \
		--set rk-axcl.tags=$(IMAGE_REPO):${GITHUB_REF_NAME}-$(COMMIT_HASH)-rk-axcl

push-rk-axcl: build-rk-axcl
	docker buildx bake --file=docker/rockchip/rk.hcl --file=docker/axcl/rk-axcl.hcl rk-axcl \
		--set rk-axcl.tags=$(IMAGE_REPO):${GITHUB_REF_NAME}-$(COMMIT_HASH)-rk-axcl \
		--push

rpi-axcl:
	docker buildx bake --file=docker/rpi/rpi.hcl --file=docker/axcl/rpi-axcl.hcl rpi-axcl \
		--set rpi-axcl.tags=frigate:latest-rpi-axcl

build-rpi-axcl: version
	docker buildx bake --file=docker/rpi/rpi.hcl --file=docker/axcl/rpi-axcl.hcl rpi-axcl \
		--set rpi-axcl.tags=$(IMAGE_REPO):${GITHUB_REF_NAME}-$(COMMIT_HASH)-rpi-axcl

push-rpi-axcl: build-rpi-axcl
	docker buildx bake --file=docker/rpi/rpi.hcl --file=docker/axcl/rpi-axcl.hcl rpi-axcl \
		--set rpi-axcl.tags=$(IMAGE_REPO):${GITHUB_REF_NAME}-$(COMMIT_HASH)-rpi-axcl \
		--push
