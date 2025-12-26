FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src ./src

EXPOSE 8000

# Run the FastAPI app defined in backend/src/main.py
# The app must be exposed as variable `app` inside that module.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]