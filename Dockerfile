# Multi-stage build for minimal image size
FROM python:3.11-alpine AS builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev linux-headers

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage - minimal image
FROM python:3.11-alpine

# Create non-root user
RUN adduser -D appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY app.py ./
COPY templates ./templates

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

# Change ownership to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Run the application
ENTRYPOINT ["python"]
CMD ["app.py"]