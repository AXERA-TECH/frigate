BOARDS += ax650

ax650:
	docker buildx bake --file=docker/axera/ax650.hcl ax650 \
		--set ax650.tags=frigate:latest-ax650

build-ax650: version
	docker buildx bake --file=docker/axera/ax650.hcl ax650 \
		--set ax650.tags=$(IMAGE_REPO):${GITHUB_REF_NAME}-$(COMMIT_HASH)-ax650

push-ax650: build-ax650
	docker buildx bake --file=docker/axera/ax650.hcl ax650 \
		--set ax650.tags=$(IMAGE_REPO):${GITHUB_REF_NAME}-$(COMMIT_HASH)-ax650 \
		--push
