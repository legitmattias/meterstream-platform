FROM python:3.12-slim

WORKDIR /app
# Create a non-root user for running the application
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
RUN chown -R appuser:appuser /app

# Create non-root user for security
RUN addgroup --gid 1001 appgroup && \
    adduser --uid 1001 --gid 1001 --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000
USER appuser
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
