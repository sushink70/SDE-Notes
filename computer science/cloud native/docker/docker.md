# Comprehensive Guide to Docker

## Table of Contents
1. Introduction to Docker
2. Core Concepts & Architecture
3. Installation & Setup
4. Docker Images
5. Docker Containers
6. Docker Volumes & Data Management
7. Docker Networking
8. Docker Compose
9. Dockerfile Best Practices
10. Docker Registry & Distribution
11. Docker Security
12. Orchestration & Scaling
13. Monitoring & Logging
14. Troubleshooting & Debugging

---

## 1. Introduction to Docker

### What is Docker?

Docker is an open-source platform that automates the deployment, scaling, and management of applications using containerization. It packages applications and their dependencies into standardized units called containers that can run consistently across different computing environments.

### Why Docker?

**Traditional Challenges:**
- "It works on my machine" syndrome
- Environment inconsistencies between development, staging, and production
- Complex dependency management
- Slow deployment cycles
- Resource inefficiency with virtual machines

**Docker Solutions:**
- Consistent environments across the entire software lifecycle
- Lightweight compared to VMs (shares host OS kernel)
- Fast startup times (seconds vs minutes)
- Efficient resource utilization
- Simplified dependency management
- Easy scaling and orchestration

### Docker vs Virtual Machines

**Virtual Machines:**
- Include full OS copy
- Heavyweight (GBs)
- Slow boot time (minutes)
- Hardware-level virtualization
- Strong isolation

**Docker Containers:**
- Share host OS kernel
- Lightweight (MBs)
- Fast startup (seconds)
- OS-level virtualization
- Process-level isolation

---

## 2. Core Concepts & Architecture

### Docker Architecture

Docker uses a client-server architecture with three main components:

**Docker Client:**
- Command-line interface (CLI) or GUI
- Communicates with Docker daemon via REST API
- Commands: `docker run`, `docker build`, `docker pull`, etc.

**Docker Daemon (dockerd):**
- Background service running on host
- Manages Docker objects (images, containers, networks, volumes)
- Listens for Docker API requests
- Can communicate with other daemons

**Docker Registry:**
- Stores Docker images
- Docker Hub is the default public registry
- Private registries can be self-hosted

### Key Concepts

**Images:**
- Read-only templates containing application code, libraries, dependencies, and tools
- Built from Dockerfile instructions
- Composed of layers (each instruction creates a layer)
- Immutable once created

**Containers:**
- Runnable instances of images
- Isolated processes with their own filesystem, networking, and process space
- Ephemeral by default (changes lost when stopped)
- Can be started, stopped, moved, and deleted

**Dockerfile:**
- Text file with instructions to build Docker images
- Defines base image, dependencies, configuration, and commands
- Version-controlled and reproducible

**Volumes:**
- Persistent data storage mechanism
- Exist outside container lifecycle
- Shared between containers
- Managed by Docker

**Networks:**
- Virtual networks for container communication
- Multiple network drivers (bridge, host, overlay, macvlan)
- Isolated communication channels

---

## 3. Installation & Setup

### Installing Docker

**Linux (Ubuntu/Debian):**
```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
sudo docker run hello-world
```

**macOS:**
- Download Docker Desktop from Docker's website
- Install the .dmg file
- Start Docker Desktop from Applications

**Windows:**
- Download Docker Desktop for Windows
- Enable WSL 2 (Windows Subsystem for Linux)
- Install and configure Docker Desktop

### Post-Installation Steps

**Add user to docker group (Linux):**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**Configure Docker daemon:**
Edit `/etc/docker/daemon.json`:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
```

**Verify installation:**
```bash
docker version
docker info
docker run hello-world
```

---

## 4. Docker Images

### Understanding Images

Images are built in layers using a union filesystem. Each instruction in a Dockerfile creates a new layer. Layers are cached and reused, making builds efficient.

### Basic Image Commands

```bash
# List local images
docker images
docker image ls

# Search for images
docker search nginx

# Pull image from registry
docker pull nginx
docker pull nginx:1.21

# Remove image
docker rmi nginx
docker image rm nginx

# Remove unused images
docker image prune

# Inspect image details
docker inspect nginx

# View image history
docker history nginx

# Tag an image
docker tag nginx:latest myregistry/nginx:v1
```

### Building Images

**Simple Dockerfile example:**
```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python3", "app.py"]
```

**Build image:**
```bash
# Build with tag
docker build -t myapp:1.0 .

# Build with build arguments
docker build --build-arg VERSION=1.0 -t myapp .

# Build without cache
docker build --no-cache -t myapp .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t myapp .
```

### Dockerfile Instructions

**FROM:** Base image
```dockerfile
FROM python:3.9-slim
```

**RUN:** Execute commands during build
```dockerfile
RUN apt-get update && apt-get install -y curl
```

**COPY:** Copy files from host to image
```dockerfile
COPY app.py /app/
COPY . /app/
```

**ADD:** Similar to COPY but can extract archives and download from URLs
```dockerfile
ADD https://example.com/file.tar.gz /tmp/
```

**WORKDIR:** Set working directory
```dockerfile
WORKDIR /app
```

**ENV:** Set environment variables
```dockerfile
ENV APP_ENV=production
ENV DATABASE_URL=postgres://db:5432
```

**EXPOSE:** Document which ports the container listens on
```dockerfile
EXPOSE 8000
```

**CMD:** Default command when container starts (can be overridden)
```dockerfile
CMD ["python", "app.py"]
```

**ENTRYPOINT:** Configure container as executable (harder to override)
```dockerfile
ENTRYPOINT ["python"]
CMD ["app.py"]
```

**VOLUME:** Create mount point for volumes
```dockerfile
VOLUME /data
```

**USER:** Set user for subsequent instructions
```dockerfile
USER appuser
```

**ARG:** Define build-time variables
```dockerfile
ARG VERSION=1.0
```

**LABEL:** Add metadata
```dockerfile
LABEL maintainer="user@example.com"
LABEL version="1.0"
```

**HEALTHCHECK:** Define health check command
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost/ || exit 1
```

### Multi-stage Builds

Reduce image size by using multiple FROM statements:

```dockerfile
# Build stage
FROM node:16 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM node:16-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### Image Optimization Techniques

1. **Use specific base image tags** (not `latest`)
2. **Choose minimal base images** (alpine, slim variants)
3. **Combine RUN commands** to reduce layers
4. **Order instructions by change frequency** (least to most)
5. **Use .dockerignore** to exclude unnecessary files
6. **Clean up in the same layer** (remove cache, temp files)
7. **Use multi-stage builds**
8. **Leverage build cache effectively**

**.dockerignore example:**
```
.git
.gitignore
node_modules
npm-debug.log
Dockerfile
.dockerignore
.env
*.md
tests/
```

---

## 5. Docker Containers

### Container Lifecycle

1. **Created:** Container created but not started
2. **Running:** Container is executing
3. **Paused:** Container processes are paused
4. **Stopped:** Container stopped gracefully
5. **Killed:** Container forcefully terminated
6. **Removed:** Container deleted

### Basic Container Commands

```bash
# Run container
docker run nginx
docker run -d nginx  # detached mode
docker run -d --name webserver nginx
docker run -d -p 8080:80 nginx  # port mapping
docker run -d -e ENV_VAR=value nginx  # environment variable

# List containers
docker ps  # running containers
docker ps -a  # all containers

# Stop container
docker stop webserver
docker stop $(docker ps -q)  # stop all

# Start stopped container
docker start webserver

# Restart container
docker restart webserver

# Pause/unpause container
docker pause webserver
docker unpause webserver

# Remove container
docker rm webserver
docker rm -f webserver  # force remove running container

# Remove all stopped containers
docker container prune

# View container logs
docker logs webserver
docker logs -f webserver  # follow logs
docker logs --tail 100 webserver

# Execute command in running container
docker exec -it webserver bash
docker exec webserver ls /etc

# View container stats
docker stats
docker stats webserver

# Inspect container details
docker inspect webserver

# View processes in container
docker top webserver

# Copy files to/from container
docker cp file.txt webserver:/tmp/
docker cp webserver:/tmp/file.txt .

# Export/Import containers
docker export webserver > webserver.tar
docker import webserver.tar myimage:latest

# Save/Load images
docker save -o nginx.tar nginx
docker load -i nginx.tar

# Commit container changes to new image
docker commit webserver mynginx:v2
```

### Advanced Run Options

```bash
# Resource constraints
docker run -d --cpus=2 --memory=512m nginx

# Set hostname
docker run -d --hostname=web01 nginx

# Network mode
docker run -d --network=host nginx
docker run -d --network=mynetwork nginx

# Volume mounting
docker run -d -v /host/path:/container/path nginx
docker run -d -v myvolume:/data nginx

# Read-only filesystem
docker run -d --read-only nginx

# Auto-restart policy
docker run -d --restart=always nginx
docker run -d --restart=on-failure:5 nginx

# Set user
docker run -d --user 1000:1000 nginx

# Add capabilities
docker run -d --cap-add=NET_ADMIN nginx

# Set working directory
docker run -d -w /app nginx

# Interactive terminal
docker run -it ubuntu bash

# Remove container after exit
docker run --rm ubuntu echo "Hello"

# Set container labels
docker run -d --label env=prod nginx
```

---

## 6. Docker Volumes & Data Management

### Volume Types

**Named Volumes:** Managed by Docker
```bash
docker volume create myvolume
docker run -d -v myvolume:/data nginx
```

**Bind Mounts:** Direct host filesystem mapping
```bash
docker run -d -v /host/path:/container/path nginx
docker run -d -v $(pwd):/app nginx  # current directory
```

**tmpfs Mounts:** Temporary filesystem in memory (Linux only)
```bash
docker run -d --tmpfs /tmp nginx
```

### Volume Commands

```bash
# Create volume
docker volume create myvolume

# List volumes
docker volume ls

# Inspect volume
docker volume inspect myvolume

# Remove volume
docker volume rm myvolume

# Remove unused volumes
docker volume prune

# Backup volume
docker run --rm -v myvolume:/source -v $(pwd):/backup ubuntu tar czf /backup/backup.tar.gz /source

# Restore volume
docker run --rm -v myvolume:/target -v $(pwd):/backup ubuntu tar xzf /backup/backup.tar.gz -C /target
```

### Volume Mount Options

```bash
# Read-only mount
docker run -d -v myvolume:/data:ro nginx

# Bind propagation
docker run -d -v /host:/container:shared nginx

# Named volume with driver options
docker volume create --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.1.1,rw \
  --opt device=:/path/to/dir \
  nfsvolume
```

### Best Practices

1. Use named volumes for persistent data
2. Use bind mounts for development (live code reloading)
3. Never store sensitive data in images
4. Regular backup important volumes
5. Use volume drivers for advanced storage needs
6. Set appropriate permissions on mounted directories

---

## 7. Docker Networking

### Network Drivers

**Bridge (default):** Private internal network on host
```bash
docker network create mybridge
docker run -d --network=mybridge nginx
```

**Host:** Container uses host's network directly
```bash
docker run -d --network=host nginx
```

**None:** No networking
```bash
docker run -d --network=none nginx
```

**Overlay:** Multi-host networking (Docker Swarm)
```bash
docker network create -d overlay myoverlay
```

**Macvlan:** Assign MAC addresses to containers
```bash
docker network create -d macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  -o parent=eth0 mymacvlan
```

### Network Commands

```bash
# Create network
docker network create mynetwork

# List networks
docker network ls

# Inspect network
docker network inspect mynetwork

# Connect container to network
docker network connect mynetwork webserver

# Disconnect container from network
docker network disconnect mynetwork webserver

# Remove network
docker network rm mynetwork

# Remove unused networks
docker network prune
```

### Container Communication

Containers on the same network can communicate using container names:

```bash
# Create network
docker network create appnet

# Run database
docker run -d --name db --network=appnet postgres

# Run application (can connect to db using hostname "db")
docker run -d --name app --network=appnet myapp
```

### Port Mapping

```bash
# Map single port
docker run -d -p 8080:80 nginx

# Map to specific host IP
docker run -d -p 127.0.0.1:8080:80 nginx

# Map UDP port
docker run -d -p 53:53/udp dns-server

# Map multiple ports
docker run -d -p 80:80 -p 443:443 nginx

# Map random port
docker run -d -P nginx  # maps all EXPOSE ports to random host ports

# View port mappings
docker port webserver
```

### DNS and Service Discovery

Docker provides automatic DNS resolution for container names within custom networks:

```bash
# Containers can resolve each other by name
docker run -d --name web --network=mynet nginx
docker run -d --name app --network=mynet myapp
# app can reach web at http://web:80
```

### Network Aliases

```bash
# Add network alias
docker network connect --alias web1 mynetwork webserver

# Multiple containers can share same alias
docker run -d --network=mynet --network-alias=api api-v1
docker run -d --network=mynet --network-alias=api api-v2
# Load balanced access to "api"
```

---

## 8. Docker Compose

Docker Compose is a tool for defining and running multi-container applications using YAML files.

### Installation

Docker Compose comes with Docker Desktop. For Linux:
```bash
sudo apt-get install docker-compose-plugin
```

### Basic docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    image: nginx:latest
    ports:
      - "8080:80"
    volumes:
      - ./html:/usr/share/nginx/html
    networks:
      - webnet
    depends_on:
      - api
    environment:
      - NGINX_HOST=localhost
      - NGINX_PORT=80
    restart: unless-stopped

  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./api:/app
      - /app/node_modules
    networks:
      - webnet
      - dbnet
    environment:
      DATABASE_URL: postgres://db:5432/mydb
    depends_on:
      - db
    command: npm run dev

  db:
    image: postgres:14
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - dbnet
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  webnet:
  dbnet:

volumes:
  pgdata:
```

### Compose Commands

```bash
# Start services
docker compose up
docker compose up -d  # detached mode
docker compose up --build  # rebuild images

# Stop services
docker compose stop

# Stop and remove containers
docker compose down
docker compose down -v  # also remove volumes

# View logs
docker compose logs
docker compose logs -f web  # follow specific service

# List containers
docker compose ps

# Execute command in service
docker compose exec web bash

# Scale services
docker compose up -d --scale api=3

# View service configuration
docker compose config

# Pull images
docker compose pull

# Build images
docker compose build
docker compose build --no-cache

# Restart services
docker compose restart

# Pause/unpause services
docker compose pause
docker compose unpause

# View events
docker compose events
```

### Advanced Compose Features

**Environment files:**
```yaml
services:
  web:
    env_file:
      - .env
      - .env.production
```

**Extends and overrides:**
```yaml
# docker-compose.override.yml
services:
  web:
    ports:
      - "9090:80"
    environment:
      DEBUG: "true"
```

**Profiles:**
```yaml
services:
  debug-tool:
    image: debug-container
    profiles:
      - debug
```

```bash
docker compose --profile debug up
```

**Resource limits:**
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

**Health checks:**
```yaml
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## 9. Dockerfile Best Practices

### 1. Use Specific Base Image Tags

**Bad:**
```dockerfile
FROM node
```

**Good:**
```dockerfile
FROM node:16.14-alpine3.15
```

### 2. Order Instructions by Change Frequency

**Bad:**
```dockerfile
FROM python:3.9
COPY . /app
RUN pip install -r requirements.txt
```

**Good:**
```dockerfile
FROM python:3.9
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt
COPY . /app
```

### 3. Minimize Layers

**Bad:**
```dockerfile
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y vim
RUN apt-get clean
```

**Good:**
```dockerfile
RUN apt-get update && apt-get install -y \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*
```

### 4. Use Multi-stage Builds

```dockerfile
# Build stage
FROM golang:1.19 AS builder
WORKDIR /app
COPY go.* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o app

# Runtime stage
FROM alpine:3.16
RUN apk --no-cache add ca-certificates
COPY --from=builder /app/app /app
ENTRYPOINT ["/app"]
```

### 5. Don't Run as Root

```dockerfile
FROM node:16-alpine

RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

WORKDIR /app
COPY --chown=nodejs:nodejs . .

USER nodejs
CMD ["node", "server.js"]
```

### 6. Use .dockerignore

```
.git
.gitignore
README.md
node_modules
npm-debug.log
.env
.DS_Store
*/temp*
*/*/temp*
tests/
```

### 7. Scan for Vulnerabilities

```bash
docker scan myimage:latest
docker scout cves myimage:latest
```

### 8. Use HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
```

### 9. Leverage Build Cache

```dockerfile
# Cache dependencies separately from code
COPY package*.json ./
RUN npm ci --only=production
COPY . .
```

### 10. Use ARG for Build-time Variables

```dockerfile
ARG NODE_ENV=production
ENV NODE_ENV=$NODE_ENV

ARG VERSION
LABEL version=$VERSION
```

---

## 10. Docker Registry & Distribution

### Docker Hub

**Login:**
```bash
docker login
docker login -u username -p password
```

**Push image:**
```bash
docker tag myapp:latest username/myapp:latest
docker push username/myapp:latest
```

**Pull image:**
```bash
docker pull username/myapp:latest
```

### Private Registry

**Run local registry:**
```bash
docker run -d -p 5000:5000 --name registry registry:2
```

**Push to private registry:**
```bash
docker tag myapp:latest localhost:5000/myapp:latest
docker push localhost:5000/myapp:latest
```

**Secure registry with TLS:**
```bash
docker run -d -p 5000:5000 \
  -v $(pwd)/certs:/certs \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \
  --name registry registry:2
```

**Registry with authentication:**
```bash
# Create htpasswd file
docker run --rm --entrypoint htpasswd \
  httpd:2 -Bbn username password > htpasswd

# Run registry with auth
docker run -d -p 5000:5000 \
  -v $(pwd)/htpasswd:/auth/htpasswd \
  -e REGISTRY_AUTH=htpasswd \
  -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
  -e REGISTRY_AUTH_HTPASSWD_REALM="Registry Realm" \
  --name registry registry:2
```

### Cloud Registries

**Amazon ECR:**
```bash
aws ecr get-login-password --region region | docker login --username AWS --password-stdin aws_account_id.dkr.ecr.region.amazonaws.com
docker tag myapp:latest aws_account_id.dkr.ecr.region.amazonaws.com/myapp:latest
docker push aws_account_id.dkr.ecr.region.amazonaws.com/myapp:latest
```

**Google Container Registry (GCR):**
```bash
gcloud auth configure-docker
docker tag myapp:latest gcr.io/project-id/myapp:latest
docker push gcr.io/project-id/myapp:latest
```

**Azure Container Registry:**
```bash
az acr login --name myregistry
docker tag myapp:latest myregistry.azurecr.io/myapp:latest
docker push myregistry.azurecr.io/myapp:latest
```

### Registry API

```bash
# List repositories
curl -X GET http://localhost:5000/v2/_catalog

# List tags
curl -X GET http://localhost:5000/v2/myapp/tags/list

# Get manifest
curl -X GET http://localhost:5000/v2/myapp/manifests/latest
```

---

## 11. Docker Security

### Container Security Principles

1. **Least Privilege:** Run containers with minimal permissions
2. **Defense in Depth:** Multiple security layers
3. **Immutability:** Treat containers as immutable
4. **Isolation:** Properly isolate containers and networks
5. **Minimal Attack Surface:** Use minimal base images

### Image Security

**1. Use Official and Verified Images**
```bash
docker pull nginx  # official image
docker pull docker/trusted-image  # verified publisher
```

**2. Scan Images for Vulnerabilities**
```bash
# Docker Scout (built-in)
docker scout cves nginx:latest

# Trivy
trivy image nginx:latest

# Snyk
snyk container test nginx:latest

# Clair
clairctl analyze nginx:latest
```

**3. Use Minimal Base Images**
```dockerfile
# Instead of full Ubuntu (78MB)
FROM ubuntu:22.04

# Use Alpine (5MB) or distroless
FROM alpine:3.18
# or
FROM gcr.io/distroless/python3
```

**4. Don't Store Secrets in Images**
```dockerfile
# BAD - hardcoded secrets
ENV API_KEY=12345

# GOOD - use runtime secrets
# Pass via environment or secrets management
```

**5. Keep Images Updated**
```bash
# Regularly rebuild images with latest patches
docker build --no-cache -t myapp:latest .

# Automate scanning in CI/CD
```

### Container Runtime Security

**1. Run as Non-Root User**
```dockerfile
FROM node:16-alpine

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup

USER appuser
```

Or at runtime:
```bash
docker run --user 1001:1001 myapp
```

**2. Use Read-Only Filesystem**
```bash
docker run --read-only --tmpfs /tmp myapp
```

**3. Drop Capabilities**
```bash
# Drop all and add only needed
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE nginx

# Drop specific capabilities
docker run --cap-drop=CHOWN --cap-drop=DAC_OVERRIDE myapp
```

**4. Limit Resources**
```bash
# CPU and memory limits
docker run --cpus=1 --memory=512m myapp

# PIDs limit (prevent fork bombs)
docker run --pids-limit=100 myapp

# Ulimits
docker run --ulimit nofile=1024:1024 myapp
```

**5. Use Security Options**
```bash
# AppArmor profile
docker run --security-opt apparmor=docker-default nginx

# SELinux label
docker run --security-opt label=type:svirt_apache_t nginx

# Seccomp profile
docker run --security-opt seccomp=profile.json myapp

# No new privileges
docker run --security-opt no-new-privileges:true myapp
```

**6. Disable Inter-Container Communication**
```bash
# Create isolated network
docker network create --internal isolated-net
docker run --network=isolated-net myapp
```

**7. Set Container to Drop Privileges**
```dockerfile
FROM alpine
RUN apk add --no-cache libcap
RUN setcap cap_net_bind_service=+ep /app
USER nobody
```

### Docker Daemon Security

**1. Enable TLS for Docker Daemon**
```bash
# Generate certificates
openssl genrsa -aes256 -out ca-key.pem 4096
openssl req -new -x509 -days 365 -key ca-key.pem -sha256 -out ca.pem

# Configure daemon
dockerd --tlsverify \
  --tlscacert=ca.pem \
  --tlscert=server-cert.pem \
  --tlskey=server-key.pem \
  -H=0.0.0.0:2376
```

**2. Use User Namespaces**

Edit `/etc/docker/daemon.json`:
```json
{
  "userns-remap": "default"
}
```

This maps container root to unprivileged host user.

**3. Enable Content Trust**
```bash
export DOCKER_CONTENT_TRUST=1
docker pull nginx  # will verify signatures
```

**4. Audit Docker Daemon**
```bash
# Enable auditd for Docker
auditctl -w /usr/bin/docker -k docker
auditctl -w /var/lib/docker -k docker
```

**5. Limit Daemon Access**
```bash
# Only allow specific users in docker group
sudo usermod -aG docker username

# Use socket activation instead of exposing TCP
```

### Network Security

**1. Use Custom Networks**
```bash
# Create isolated network
docker network create --driver bridge app-network

# Run containers on custom network
docker run --network=app-network myapp
```

**2. Encrypt Overlay Networks**
```bash
docker network create --driver overlay --opt encrypted overlay-network
```

**3. Use Network Policies**
```bash
# Deny inter-container communication by default
docker network create --internal secure-net
```

**4. Limit Port Exposure**
```bash
# Bind to localhost only
docker run -p 127.0.0.1:8080:80 nginx

# Don't expose unnecessary ports
```

### Secrets Management

**1. Docker Secrets (Swarm)**
```bash
# Create secret
echo "mysecretpassword" | docker secret create db_password -

# Use in service
docker service create \
  --name myapp \
  --secret db_password \
  myimage
```

Access in container at `/run/secrets/db_password`

**2. Environment Variables (Less Secure)**
```bash
# Use .env files
docker run --env-file .env myapp

# Or runtime variables
docker run -e DB_PASSWORD=secret myapp
```

**3. Vault Integration**
```dockerfile
# Use HashiCorp Vault
RUN wget -O /usr/local/bin/vault https://releases.hashicorp.com/vault/...
CMD vault kv get secret/myapp
```

**4. AWS Secrets Manager / Azure Key Vault**
```python
# Fetch secrets at runtime from cloud provider
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='my-secret')
```

### Security Scanning & Compliance

**1. CIS Docker Benchmark**
```bash
# Run Docker Bench Security
docker run --rm --net host --pid host --userns host --cap-add audit_control \
  -v /var/lib:/var/lib \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /etc:/etc \
  --label docker_bench_security \
  docker/docker-bench-security
```

**2. Regular Vulnerability Scanning**
```bash
# Integrate into CI/CD
trivy image --severity HIGH,CRITICAL myapp:latest
```

**3. Runtime Security Monitoring**
```bash
# Use Falco for runtime security
docker run --rm -i -t \
  --privileged \
  -v /var/run/docker.sock:/host/var/run/docker.sock \
  -v /dev:/host/dev \
  -v /proc:/host/proc:ro \
  -v /boot:/host/boot:ro \
  -v /lib/modules:/host/lib/modules:ro \
  -v /usr:/host/usr:ro \
  falcosecurity/falco
```

**4. Image Signing**
```bash
# Enable Docker Content Trust
export DOCKER_CONTENT_TRUST=1

# Sign images
docker trust sign myregistry/myapp:v1

# Verify signatures
docker trust inspect --pretty myregistry/myapp:v1
```

### Security Best Practices Checklist

**Image Security:**
- ✓ Use official/verified base images
- ✓ Scan images for vulnerabilities
- ✓ Use minimal base images (Alpine, distroless)
- ✓ Don't store secrets in images
- ✓ Keep images updated
- ✓ Use specific image tags, not 'latest'
- ✓ Sign and verify images

**Container Runtime:**
- ✓ Run as non-root user
- ✓ Use read-only filesystem where possible
- ✓ Drop unnecessary capabilities
- ✓ Set resource limits (CPU, memory, PIDs)
- ✓ Use security options (AppArmor, SELinux, Seccomp)
- ✓ Enable no-new-privileges flag

**Network Security:**
- ✓ Use custom networks
- ✓ Encrypt overlay networks
- ✓ Limit port exposure
- ✓ Bind to localhost when possible
- ✓ Use network segmentation

**Daemon Security:**
- ✓ Enable TLS for remote access
- ✓ Use user namespaces
- ✓ Enable content trust
- ✓ Audit daemon activity
- ✓ Limit daemon socket access

**Secrets Management:**
- ✓ Use Docker secrets or external vault
- ✓ Never hardcode secrets
- ✓ Rotate secrets regularly
- ✓ Use least privilege access

**Compliance & Monitoring:**
- ✓ Run CIS Docker Benchmark
- ✓ Implement vulnerability scanning
- ✓ Use runtime security monitoring
- ✓ Enable logging and auditing
- ✓ Regular security reviews

---

## 12. Orchestration & Scaling

### Docker Swarm

Docker Swarm is Docker's native orchestration tool for managing clusters of Docker engines.

**Initialize Swarm:**
```bash
# On manager node
docker swarm init --advertise-addr 192.168.1.100

# Join workers
docker swarm join --token <token> 192.168.1.100:2377

# View nodes
docker node ls

# Promote worker to manager
docker node promote worker-node
```

**Deploy Services:**
```bash
# Create service
docker service create --name web --replicas 3 -p 8080:80 nginx

# List services
docker service ls

# Inspect service
docker service ps web

# Scale service
docker service scale web=5

# Update service
docker service update --image nginx:1.21 web

# Remove service
docker service rm web
```

**Stack Deployment:**
```yaml
# docker-stack.yml
version: '3.8'

services:
  web:
    image: nginx:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    ports:
      - "8080:80"
    networks:
      - webnet

  redis:
    image: redis:alpine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
    networks:
      - webnet

networks:
  webnet:
    driver: overlay
```

```bash
# Deploy stack
docker stack deploy -c docker-stack.yml myapp

# List stacks
docker stack ls

# View services in stack
docker stack services myapp

# Remove stack
docker stack rm myapp
```

**Swarm Features:**
- Load balancing
- Service discovery
- Rolling updates
- Secret management
- Config management
- Health checks

### Kubernetes Overview

While Docker Swarm is native, Kubernetes is the industry-standard orchestration platform.

**Key Concepts:**
- **Pods:** Smallest deployable units containing one or more containers
- **Services:** Stable network endpoints for pods
- **Deployments:** Declarative updates for pods
- **ReplicaSets:** Maintain desired number of pod replicas
- **Namespaces:** Virtual clusters within physical cluster
- **ConfigMaps/Secrets:** Configuration and sensitive data management

**Basic Kubernetes Commands:**
```bash
# Deploy application
kubectl create deployment nginx --image=nginx

# Expose deployment
kubectl expose deployment nginx --port=80 --type=LoadBalancer

# Scale deployment
kubectl scale deployment nginx --replicas=3

# View resources
kubectl get pods
kubectl get services
kubectl get deployments

# Describe resource
kubectl describe pod nginx-pod

# View logs
kubectl logs nginx-pod

# Execute command in pod
kubectl exec -it nginx-pod -- bash

# Delete resources
kubectl delete deployment nginx
```

**Kubernetes Deployment YAML:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "250m"
            memory: "256Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: LoadBalancer
```

### Scaling Strategies

**1. Horizontal Scaling:**
```bash
# Docker Swarm
docker service scale web=10

# Kubernetes
kubectl scale deployment web --replicas=10
```

**2. Auto-scaling (Kubernetes):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**3. Load Balancing:**
```bash
# Built-in with Swarm and Kubernetes
# External load balancers: NGINX, HAProxy, Traefik
```

**4. Rolling Updates:**
```bash
# Docker Swarm
docker service update --image nginx:1.22 web

# Kubernetes
kubectl set image deployment/web nginx=nginx:1.22
kubectl rollout status deployment/web
kubectl rollout history deployment/web
kubectl rollout undo deployment/web
```

---

## 13. Monitoring & Logging

### Container Logs

**Basic Logging:**
```bash
# View logs
docker logs container_name

# Follow logs
docker logs -f container_name

# Tail last 100 lines
docker logs --tail 100 container_name

# Show timestamps
docker logs -t container_name

# Logs since specific time
docker logs --since 2024-01-01T00:00:00 container_name

# Until specific time
docker logs --until 2024-01-01T23:59:59 container_name
```

**Logging Drivers:**
```bash
# JSON file (default)
docker run --log-driver json-file --log-opt max-size=10m --log-opt max-file=3 nginx

# Syslog
docker run --log-driver syslog --log-opt syslog-address=tcp://192.168.1.100:514 nginx

# Journald
docker run --log-driver journald nginx

# Fluentd
docker run --log-driver fluentd --log-opt fluentd-address=192.168.1.100:24224 nginx

# Splunk
docker run --log-driver splunk --log-opt splunk-token=token --log-opt splunk-url=http://splunk:8088 nginx

# AWS CloudWatch
docker run --log-driver awslogs --log-opt awslogs-region=us-east-1 --log-opt awslogs-group=mygroup nginx
```

**Configure Default Logging Driver:**
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3",
    "labels": "production_status",
    "env": "os,customer"
  }
}
```

### Monitoring Solutions

**1. Docker Stats:**
```bash
# Real-time stats
docker stats

# Specific containers
docker stats container1 container2

# No streaming (single snapshot)
docker stats --no-stream

# Format output
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

**2. cAdvisor (Container Advisor):**
```bash
docker run \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --publish=8080:8080 \
  --detach=true \
  --name=cadvisor \
  google/cadvisor:latest
```

**3. Prometheus + Grafana Stack:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro

volumes:
  prometheus-data:
  grafana-data:
```

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
```

**4. ELK Stack (Elasticsearch, Logstash, Kibana):**

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    ports:
      - "5000:5000"
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch-data:
```

**5. Datadog:**
```bash
docker run -d --name datadog-agent \
  -e DD_API_KEY=<your-api-key> \
  -e DD_SITE="datadoghq.com" \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /proc/:/host/proc/:ro \
  -v /sys/fs/cgroup/:/host/sys/fs/cgroup:ro \
  datadog/agent:latest
```

### Health Checks

**Dockerfile HEALTHCHECK:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
```

**Docker Compose:**
```yaml
services:
  web:
    image: nginx
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Check health status:**
```bash
docker inspect --format='{{.State.Health.Status}}' container_name
```

### Alerting

**Prometheus Alertmanager:**
```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'email'

receivers:
  - name: 'email'
    email_configs:
      - to: 'admin@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'password'
```

**Alert Rules:**
```yaml
# alert.rules.yml
groups:
  - name: container_alerts
    interval: 30s
    rules:
      - alert: ContainerDown
        expr: up{job="docker"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Container {{ $labels.instance }} is down"
          description: "Container has been down for more than 1 minute"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.name }}"
```

---

## 14. Troubleshooting & Debugging

### Common Issues and Solutions

**1. Container Won't Start**
```bash
# Check container logs
docker logs container_name

# Inspect container
docker inspect container_name

# Check exit code
docker inspect container_name --format='{{.State.ExitCode}}'

# Common exit codes:
# 0 - Successful exit
# 1 - Application error
# 125 - Docker daemon error
# 126 - Command cannot execute
# 127 - Command not found
# 137 - Container killed (SIGKILL)
# 139 - Segmentation fault
# 143 - Graceful termination (SIGTERM)
```

**2. Port Binding Issues**
```bash
# Check if port is already in use
netstat -tuln | grep 8080
lsof -i :8080

# Use different port
docker run -p 8081:80 nginx

# Check container port mappings
docker port container_name
```

**3. Permission Denied Errors**
```bash
# Fix docker socket permissions
sudo chmod 666 /var/run/docker.sock

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Run as root (not recommended)
sudo docker run nginx
```

**4. Out of Disk Space**
```bash
# Check disk usage
docker system df

# Clean up
docker system prune -a  # Remove all unused images, containers, networks
docker volume prune     # Remove unused volumes
docker image prune -a   # Remove unused images
docker container prune  # Remove stopped containers

# Check specific resource usage
docker system df -v
```

**5. Network Issues**
```bash
# Check container network
docker inspect container_name | grep -A 10 NetworkSettings

# Test connectivity
docker exec container_name ping google.com
docker exec container_name curl http://other-container

# Restart networking
docker network disconnect bridge container_name
docker network connect bridge container_name

# Check DNS
docker exec container_name cat /etc/resolv.conf
docker exec container_name nslookup google.com
```

**6. Image Build Failures**
```bash
# Build with verbose output
docker build --progress=plain -t myapp .

# Build without cache
docker build --no-cache -t myapp .

# Check build context size
du -sh .

# Use .dockerignore to reduce context
echo "node_modules" >> .dockerignore
```

### Debugging Techniques

**1. Interactive Shell Access:**
```bash
# Start container with shell
docker run -it ubuntu bash

# Execute shell in running container
docker exec -it container_name bash

# Start shell as root
docker exec -it -u root container_name bash

# If bash not available, use sh
docker exec -it container_name sh
```

**2. Inspect Container Filesystem:**
```bash
# Copy files from container
docker cp container_name:/app/logs/error.log ./

# View filesystem changes
docker diff container_name

# Export entire filesystem
docker export container_name > container.tar
tar -xvf container.tar
```

**3. Debug Running Processes:**
```bash
# View running processes
docker top container_name

# Check resource usage
docker stats container_name

# Attach to container output
docker attach container_name
```

**4. Network Debugging:**
```bash
# Create debug container with network tools
docker run -it --rm --network=container:myapp nicolaka/netshoot

# Inside netshoot container
ping other-container
curl http://other-container:8080
nslookup other-container
netstat -tuln
tcpdump -i any port 8080
```

**5. Volume Debugging:**
```bash
# Inspect volume
docker volume inspect myvolume

# Access volume data
docker run --rm -v myvolume:/data alpine ls -la /data

# Backup volume
docker run --rm -v myvolume:/source -v $(pwd):/backup alpine tar czf /backup/volume-backup.tar.gz -C /source .
```

**6. Event Monitoring:**
```bash
# Watch Docker events
docker events

# Filter events
docker events --filter type=container
docker events --filter event=start
docker events --filter container=myapp

# Events since specific time
docker events --since '2024-01-01T00:00:00'
```

**7. Debug Multi-stage Builds:**
```dockerfile
# Build specific stage
docker build --target builder -t myapp:debug .

# Access intermediate stage
docker run -it myapp:debug bash
```

**8. Analyze Image Layers:**
```bash
# View image history
docker history myapp:latest

# Use dive to explore layers
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive:latest myapp:latest
```

### Performance Troubleshooting

**1. CPU Issues:**
```bash
# Monitor CPU usage
docker stats --format "table {{.Name}}\t{{.CPUPerc}}"

# Limit CPU
docker run --cpus=2 myapp

# Set CPU shares (relative weight)
docker run --cpu-shares=512 myapp
```

**2. Memory Issues:**
```bash
# Monitor memory
docker stats --format "table {{.Name}}\t{{.MemUsage}}"

# Set memory limit
docker run -m 512m myapp

# Set memory reservation
docker run --memory-reservation=256m -m 512m myapp

# Monitor OOM kills
dmesg | grep -i oom
```

**3. I/O Issues:**
```bash
# Monitor I/O
docker stats --format "table {{.Name}}\t{{.BlockIO}}"

# Limit I/O
docker run --device-read-bps /dev/sda:1mb myapp
docker run --device-write-bps /dev/sda:1mb myapp
```

**4. Slow Image Builds:**
```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker build -t myapp .

# Parallel builds
docker buildx build --load -t myapp .

# Use layer caching effectively
# Order Dockerfile instructions by change frequency
```

### Logging and Diagnostics

**1. Enable Debug Mode:**
```bash
# Edit daemon.json
{
  "debug": true,
  "log-level": "debug"
}

# Restart daemon
sudo systemctl restart docker

# View daemon logs
journalctl -u docker -f
```

**2. Container Diagnostics:**
```bash
# Full container inspection
docker inspect container_name | jq

# Check specific property
docker inspect --format='{{.State.Status}}' container_name
docker inspect --format='{{.NetworkSettings.IPAddress}}' container_name

# Export diagnostics
docker inspect container_name > diagnostics.json
```

**3. System-Wide Diagnostics:**
```bash
# Docker info
docker info

# Check for errors
docker system events --filter type=container --filter event=die

# Generate diagnostic bundle
docker system info > system-info.txt
docker version >> system-info.txt
```

### Best Practices for Troubleshooting

1. **Check logs first** - Most issues are logged
2. **Use verbose output** - Enable debug mode when needed
3. **Isolate the problem** - Test components individually
4. **Verify networking** - Many issues are network-related
5. **Check resources** - Ensure adequate CPU, memory, disk
6. **Read documentation** - Consult official Docker docs
7. **Search for errors** - Use Docker forums and Stack Overflow
8. **Keep Docker updated** - Latest version has bug fixes
9. **Use healthchecks** - Detect problems early
10. **Monitor continuously** - Don't wait for issues to occur

---

## Conclusion

This comprehensive guide covers Docker from basics to advanced topics including security, orchestration, monitoring, and troubleshooting. Docker is a powerful platform that has revolutionized application deployment and management.

### Key Takeaways

1. **Containerization** provides consistency across environments
2. **Images** are immutable templates, **containers** are running instances
3. **Security** should be built in from the start, not added later
4. **Orchestration** enables scaling and high availability
5. **Monitoring** is essential for production environments
6. **Best practices** evolve - stay updated with the community

### Next Steps

- **Practice** with real projects
- **Join** the Docker community
- **Stay updated** with Docker releases
- **Explore** advanced topics like Kubernetes
- **Automate** with CI/CD pipelines
- **Contribute** to open-source Docker projects

### Additional Resources

- Official Docker Documentation: https://docs.docker.com
- Docker Hub: https://hub.docker.com
- Docker Blog: https://www.docker.com/blog
- Play with Docker: https://labs.play-with-docker.com
- Docker Samples: https://github.com/docker/awesome-compose

Docker continues to evolve, so keep learning and experimenting!