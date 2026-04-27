FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files AND source code
COPY pyproject.toml ./
COPY src ./src
COPY conf ./conf
COPY entrypoints ./entrypoints
COPY data ./data

# Create venv, upgrade pip and install dependencies
RUN python -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"
RUN pip install --upgrade pip && pip install -e .

# Expose UI port
EXPOSE 8050

CMD ["python", "entrypoints/training.py"]