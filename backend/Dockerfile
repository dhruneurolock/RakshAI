FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    golang \
    git \
    nmap \
    hydra \
    sqlmap \
    wget \
    curl \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up Go environment
ENV GOPATH=/go
ENV PATH=$GOPATH/bin:$PATH

# Install Go-based security tools
RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest && \
    go install -v github.com/projectdiscovery/katana/cmd/katana@latest && \
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && \
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/hahwul/dalfox/v2@latest && \
    go install -v github.com/jaeles-project/gospider@latest || true

# Important: tool_sandbox.py expects tools strictly at /usr/local/bin/...
RUN ln -s $GOPATH/bin/httpx /usr/local/bin/httpx && \
    ln -s $GOPATH/bin/katana /usr/local/bin/katana && \
    ln -s $GOPATH/bin/nuclei /usr/local/bin/nuclei && \
    ln -s $GOPATH/bin/subfinder /usr/local/bin/subfinder && \
    ln -s $GOPATH/bin/dalfox /usr/local/bin/dalfox && \
    ln -s $GOPATH/bin/gospider /usr/local/bin/gospider || true

# Map sqlmap to expected directory if it isn't there
RUN ln -s /usr/bin/sqlmap /usr/local/bin/sqlmap || true

# Set up working directory
WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/reports /app/logs /app/tools/custom

# Note: The code itself will be volume-mounted via docker-compose for live editing,
# but we'll copy it here just in case standard docker run is used.
COPY . .

# Expose backend port
EXPOSE 8000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
