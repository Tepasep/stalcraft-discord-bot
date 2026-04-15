ARG PYTHON_BASE=3.13-slim

FROM python:$PYTHON_BASE

# Устанавливаем инструменты для healthcheck
RUN apt-get update \
	&& apt-get install -y --no-install-recommends curl ca-certificates \
	&& rm -rf /var/lib/apt/lists/*

# Устанавливаем PDM
RUN pip install -U pdm
ENV PDM_CHECK_UPDATE=false

# Создаем и переходим в рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей (для кэширования слоя установки)
COPY pyproject.toml pdm.lock ./

# Устанавливаем зависимости
RUN pdm install --check --prod --no-editable

# Копируем весь код проекта (включая src/ и любые другие файлы)
COPY . .

# Добавляем виртуальное окружение PDM в PATH
ENV PATH="/app/.venv/bin:$PATH"

# ЗАПУСК
CMD ["python", "-m", "src.main"]