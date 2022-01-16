
# local deployment
.PHONY: deploy
deploy:
	poetry build
	poetry run pip uninstall aws-clutter -y
	poetry install

# convenience target
.PHONY: next
next:
	poetry version patch
	$(MAKE) deploy

# push a Lambda runnable container image to docker hub
.PHONY: publish
publish:
	docker build -t cloudkeep/aws-clutter:$$(poetry version -s) --build-arg PKG_VER=$$(poetry version -s) .
	docker tag cloudkeep/aws-clutter:$$(poetry version -s) cloudkeep/aws-clutter:latest
	@echo $$DOCKERHUB_ACCESS_TOKEN | docker login -u $$DOCKERHUB_USER --password-stdin
	docker push cloudkeep/aws-clutter:$$(poetry version -s)
	docker push cloudkeep/aws-clutter:latest

.PHONY: update-pricing
update-pricing:
	curl https://cloudkeep-io.github.io/ebs-pricing/ebs_pricing.json -o aws_clutter/data/ebs_pricing.json
