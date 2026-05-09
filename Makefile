

next:
	poetry version patch
	poetry build
	docker build -t cloudkeep/aws-clutter-meter:$$(poetry version -s) --build-arg PKG_VER=$$(poetry version -s) .

publish:
	@echo $$DOCKERHUB_ACCESS_TOKEN | docker login -u $$DOCKERHUB_USER --password-stdin
	docker tag cloudkeep/aws-clutter-meter:$$(poetry version -s) cloudkeep/aws-clutter-meter:latest
	docker push cloudkeep/aws-clutter-meter:$$(poetry version -s)
	docker push cloudkeep/aws-clutter-meter:latest

