CURRENT_DIRECTORY := $(shell pwd)

SERVICE = web-api

ifndef DC_FILE
	DC_FILE := docker-compose.yml
endif

DC_CMD = docker-compose -f ${DC_FILE}


.PHONY: start stop status restart cli tail build run test pip-compile


help:
	@echo ""
	@echo "Please use \`make <target>' where <target> is one of"
	@echo ""
	@echo "  build              to make all docker assembly images"
	@echo "  test               to run tests"
	@echo "  pip-compile        to make pip-compile"
	@echo ""
	@echo "See contents of Makefile for more targets."

start:
	$(DC_CMD) up -d

up:
	$(DC_CMD) run -p 8800:8000 $(SERVICE) uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

stop:
	$(DC_CMD) down

status:
	$(DC_CMD) ps

restart: stop start

cli:
	$(DC_CMD) exec $(SERVICE) bash

migrate:
	$(DC_CMD) run --rm $(SERVICE) python app/migrate.py

tail:
	$(DC_CMD) logs -f $(SERVICE)

build:
	$(DC_CMD) build

test:
	$(DC_CMD) exec $(SERVICE) pytest -q app/tests/
