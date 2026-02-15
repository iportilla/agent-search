# Use a slim Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server script
COPY mcp_search_server.py .

# Expose SSE port (used in cloud/remote mode)
EXPOSE 8000

# Entry point
ENTRYPOINT ["python", "mcp_search_server.py"]
CMD []
