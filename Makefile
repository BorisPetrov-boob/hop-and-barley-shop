.DEFAULT_GOAL := help
PY := uv run

.PHONY: help install lint fmt type test cov run migrate makemigrations seed \
        superuser shell up down logs build

help: ## Список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости (uv)
	uv sync --extra dev

lint: ## Проверка кода (ruff)
	$(PY) ruff check .

fmt: ## Автоформат (ruff)
	$(PY) ruff format .
	$(PY) ruff check --fix .

type: ## Проверка типов (mypy)
	$(PY) mypy .

test: ## Тесты
	$(PY) pytest -q

cov: ## Тесты с отчётом покрытия
	$(PY) pytest --cov --cov-report=term-missing --cov-report=html

run: ## Локальный сервер разработки
	$(PY) python manage.py runserver

migrate: ## Применить миграции
	$(PY) python manage.py migrate

makemigrations: ## Сгенерировать миграции
	$(PY) python manage.py makemigrations

seed: ## Демо-данные
	$(PY) python manage.py seed_demo

superuser: ## Создать суперпользователя
	$(PY) python manage.py createsuperuser

shell: ## Django shell
	$(PY) python manage.py shell

up: ## Поднять стек в Docker
	docker compose up --build

down: ## Остановить стек
	docker compose down

logs: ## Логи web-контейнера
	docker compose logs -f web

build: ## Собрать образ
	docker compose build
