PROJECT_NAME ?= disk_app
VERSION = $(shell python3 setup.py --version | tr '+' '-')
PROJECT_NAMESPACE ?= theantialex
REGISTRY_IMAGE ?= $(PROJECT_NAMESPACE)/$(PROJECT_NAME)

clean:
	rm -fr *.egg-info dist __pycache__ .pytest_cache

devenv: clean
	rm -rf env
	# создаем новое окружение
	python3 -m venv env
	# обновляем pip
	env/bin/pip install -U pip
	# устанавливаем основные + dev зависимости
	env/bin/pip install -Ue '.[dev]'

postgres:
	docker stop disk-db || true
	docker run --rm --detach --name=disk-db \
		--env POSTGRES_USER=db_user \
		--env POSTGRES_PASSWORD=12345 \
		--env POSTGRES_DB=disk \
		--publish 5432:5432 postgres
