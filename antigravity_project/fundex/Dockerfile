FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
RUN pip install flask gunicorn

# Copiar código
COPY webhook_server.py .

# Puerto
ENV PORT=8080
EXPOSE 8080

# Ejecutar
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "webhook_server:app"]
