.PHONY: help

help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help

copy-rabbit-to-harvester:
	@echo "Copying rabbit to harvester"
	@cp -R rabbit harvester/

copy-rabbit-to-injector:
	@echo "Copying rabbit to injector"
	@cp -R rabbit injector/

copy-poetry-to-harvester:
	@echo "Copying poetry to harvester"
	@cp -R poetry.lock harvester/
	@cp -R pyproject.toml harvester/

copy-poetry-to-injector:
	@echo "Copying poetry to injector"
	@cp -R poetry.lock injector/
	@cp -R pyproject.toml injector/

copy-config-to-harvester:
	@echo "Copying config to harvester"
	@cp config.py harvester/

copy-config-to-injector:
	@echo "Copying config to injector"
	@cp config.py injector/

preapre-harvester: copy-rabbit-to-harvester copy-poetry-to-harvester copy-config-to-harvester

preapre-injector: copy-rabbit-to-injector copy-poetry-to-injector copy-config-to-injector

build-harvester-image: copy-rabbit-to-harvester copy-poetry-to-harvester copy-config-to-harvester
	@echo "Building harvester image"
	@docker build -t harvester:latest --env_file harvester/local.env harvester/

build-injector-image: copy-rabbit-to-injector copy-poetry-to-injector copy-config-to-injector
	@echo "Building injector image"
	@docker build -t injector:latest injector/

run-docker-compose: preapre-harvester preapre-injector
	@echo "Running docker-compose"
	@docker-compose up -d


start-rabbit:
	@echo "Starting rabbit"
	@docker run -p 5672:5672 -p 15672:15672 -e RABBITMQ_DEFAULT_USER=guest -e RABBITMQ_DEFAULT_PASS=guest rabbitmq:management

start-mongo:
	@echo "Starting mongo"
	@docker run -p 27017:27017 mongo:6-jammy
