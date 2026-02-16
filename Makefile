IMAGE_NAME := mcp-search-agent
IMAGE_NAME_LOCAL := mcp-search-agent-local

# Load .env file if it exists
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Map lowercase variable from .env to uppercase if needed
TAVILY_API_KEY ?= $(tavily_api_key)

# Cloud deployment settings
CLOUD_IP ?= 44.249.244.232
MCP_PORT ?= 8080

.PHONY: build build-local run run-local run-cloud deploy stop stop-cloud clean

# ── Local (stdio) ────────────────────────────────────────────

build-local:
	docker build -f Dockerfile.local -t $(IMAGE_NAME_LOCAL) .

run-local:
	@if [ -z "$(TAVILY_API_KEY)" ]; then \
		echo "Error: TAVILY_API_KEY is not set. Create a .env file or set it in your environment."; \
		exit 1; \
	fi
	docker run -i --rm -e TAVILY_API_KEY=$(TAVILY_API_KEY) $(IMAGE_NAME_LOCAL)

# ── Cloud / Streamable HTTP ─────────────────────────────────

build:
	docker build --platform linux/amd64 -t $(IMAGE_NAME) .

run:
	@if [ -z "$(TAVILY_API_KEY)" ]; then \
		echo "Error: TAVILY_API_KEY is not set. Create a .env file or set it in your environment."; \
		exit 1; \
	fi
	docker run -i --rm -e TAVILY_API_KEY=$(TAVILY_API_KEY) $(IMAGE_NAME)

# Run in SSE mode for cloud/remote access
run-cloud:
	@if [ -z "$(TAVILY_API_KEY)" ]; then \
		echo "Error: TAVILY_API_KEY is not set. Create a .env file or set it in your environment."; \
		exit 1; \
	fi
	docker run -d --name $(IMAGE_NAME) --restart unless-stopped \
		-p $(MCP_PORT):8000 \
		-e TAVILY_API_KEY=$(TAVILY_API_KEY) \
		$(IMAGE_NAME) --transport streamable-http

# Deploy to cloud VM via SSH + Docker
deploy:
	@if [ -z "$(CLOUD_IP)" ] || [ "$(CLOUD_IP)" = "your-cloud-ip" ]; then \
		echo "Error: Set CLOUD_IP (e.g., make deploy CLOUD_IP=1.2.3.4)"; \
		exit 1; \
	fi
	@echo "==> Saving Docker image..."
	docker save $(IMAGE_NAME) | gzip > /tmp/$(IMAGE_NAME).tar.gz
	@echo "==> Uploading to $(CLOUD_IP)..."
	scp /tmp/$(IMAGE_NAME).tar.gz $(CLOUD_IP):/tmp/
	@echo "==> Loading image and starting container on VM..."
	ssh $(CLOUD_IP) "\
		docker load < /tmp/$(IMAGE_NAME).tar.gz && \
		docker stop $(IMAGE_NAME) 2>/dev/null; \
		docker rm $(IMAGE_NAME) 2>/dev/null; \
		docker run -d --name $(IMAGE_NAME) --restart unless-stopped \
			-p $(MCP_PORT):8000 \
			-e TAVILY_API_KEY=$(TAVILY_API_KEY) \
			$(IMAGE_NAME) --transport streamable-http && \
		echo 'Server running at http://$(CLOUD_IP):$(MCP_PORT)/mcp'"
	@rm -f /tmp/$(IMAGE_NAME).tar.gz

stop:
	docker stop $(IMAGE_NAME) 2>/dev/null; docker rm $(IMAGE_NAME) 2>/dev/null || true

stop-cloud:
	docker stop $(IMAGE_NAME) && docker rm $(IMAGE_NAME)

clean:
	docker rmi $(IMAGE_NAME) 2>/dev/null || true
	docker rmi $(IMAGE_NAME_LOCAL) 2>/dev/null || true
