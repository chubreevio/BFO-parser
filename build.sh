#!/bin/bash -xe
export COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1

docker-compose -f "docker-compose.yml" -p bfo-parser down --remove-orphans
docker-compose -f "docker-compose.yml" -p bfo-parser build
docker-compose -f "docker-compose.yml" -p bfo-parser up -d
