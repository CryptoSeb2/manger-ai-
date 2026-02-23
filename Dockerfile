# Manager AI – run on Google Cloud Run, Render, or any container host
FROM python:3.11-slim

WORKDIR /app

# Copy project (assume repo root has manager_ai/ and requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY manager_ai/ ./manager_ai/
# Optional: add a .env file for secrets, or set env vars in Cloud Run / Render dashboard

# Cloud Run and Render set PORT
ENV PORT=8080
EXPOSE 8080

# Run from project root so "manager_ai" package is importable
CMD ["sh", "-c", "python -m manager_ai.app"]
