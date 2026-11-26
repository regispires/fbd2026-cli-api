# Imagem da aplicação: sobe a API e também traz a CLI (comando empresa).
FROM python:3.12-slim

# o uv vem da imagem oficial, na mesma versão usada no desenvolvimento
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# dependências primeiro: esta camada só é refeita quando o uv.lock muda
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

# depois o código da aplicação
COPY README.md ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

EXPOSE 8000
CMD ["fastapi", "run", "src/empresa/api.py", "--port", "8000"]
