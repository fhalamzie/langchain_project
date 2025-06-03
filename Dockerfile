# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    firebird3.0-dev \
    libfbclient2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./
COPY *.sh ./
COPY *.md ./
COPY output/ ./output/
COPY lib/ ./lib/

# Create directories for logs and data
RUN mkdir -p logs output

# Make shell scripts executable
RUN chmod +x *.sh

# Set environment variables
ENV PYTHONPATH="/app"
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Expose ports
EXPOSE 8501 6006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command
CMD ["streamlit", "run", "enhanced_qa_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]