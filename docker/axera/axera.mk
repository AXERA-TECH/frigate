BOARDS += axera

IMAGE_REPO = frigate

build-ax650: version
	@echo "IMAGE_REPO is: $(IMAGE_REPO)"
	docker buildx bake --file=docker/axera/ax650.hcl ax650 \
		--set ax650.tags=$(IMAGE_REPO):ax650-$(COMMIT_HASH)