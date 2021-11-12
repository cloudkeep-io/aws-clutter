
# local deployment
.PHONY: deploy
deploy:
	poetry build
	poetry run pip uninstall aws-clutter-meter -y
	poetry install

# convenience target
.PHONY: next
next:
	poetry version patch
	$(MAKE) deploy

# push a Lambda runnable container image to docker hub
.PHONY: publish
publish:
	docker build -t cloudkeep/aws-clutter-meter:$$(poetry version -s) --build-arg PKG_VER=$$(poetry version -s) .
	docker tag cloudkeep/aws-clutter-meter:$$(poetry version -s) cloudkeep/aws-clutter-meter:latest
	@echo $$DOCKERHUB_ACCESS_TOKEN | docker login -u $$DOCKERHUB_USER --password-stdin
	docker push cloudkeep/aws-clutter-meter:$$(poetry version -s)
	docker push cloudkeep/aws-clutter-meter:latest

