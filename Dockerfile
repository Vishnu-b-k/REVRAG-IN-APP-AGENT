FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY orchestrator/ ./orchestrator/
# Copy viewer if we want to serve it statically from the backend (optional, but harmless)
COPY viewer/ ./viewer/

# Environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=False

EXPOSE 8000

CMD ["uvicorn", "orchestrator.main:app", "--host", "0.0.0.0", "--port", "8000"]
