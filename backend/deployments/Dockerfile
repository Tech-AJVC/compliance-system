# Dockerfile for Compliance Reminder Cron Job
# Build from deployments/ directory to access all backend files
FROM python:3.12-slim as builder

WORKDIR /app

# Copy minimal requirements for reminder service only
COPY deployments/reminder_cron_job/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Copy the entire app directory (for models, utils, database)
COPY app ./app
COPY config.py ./config.py
COPY __init__.py ./__init__.py

# Copy the entire reminder_cron_job folder
COPY deployments/reminder_cron_job ./reminder_cron_job

# Set working directory to reminder_cron_job and run from there
WORKDIR /app/reminder_cron_job
CMD ["python", "reminder_service.py"]