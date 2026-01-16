FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install flask twilio google-cloud-aiplatform requests gunicorn

# Copy webhook
COPY webhook.py .

# Run with gunicorn
ENV PORT=8080
EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "webhook:app"]
