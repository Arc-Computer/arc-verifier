#!/bin/bash

# Docker setup script for Arc-Verifier
# Ensures Docker is properly configured for production use

set -e

echo "🐳 Setting up Docker for Arc-Verifier production use..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo ""
    echo "Please install Docker first:"
    echo "macOS: Download Docker Desktop from https://docker.com/products/docker-desktop"
    echo "Linux: Follow installation guide at https://docs.docker.com/engine/install/"
    echo "Windows: Download Docker Desktop from https://docker.com/products/docker-desktop"
    exit 1
fi

echo "✅ Docker is installed: $(docker --version)"

# Check if Docker daemon is running
echo "🔍 Checking Docker daemon status..."
if docker info >/dev/null 2>&1; then
    echo "✅ Docker daemon is running"
else
    echo "❌ Docker daemon is not running"
    echo ""
    echo "Please start Docker:"
    echo "macOS/Windows: Open Docker Desktop application"
    echo "Linux: sudo systemctl start docker"
    echo ""
    echo "For Linux, you may also need to enable Docker to start on boot:"
    echo "sudo systemctl enable docker"
    exit 1
fi

# Check Docker permissions
echo "🔐 Checking Docker permissions..."
if docker ps >/dev/null 2>&1; then
    echo "✅ Docker permissions are correct"
else
    echo "❌ Docker permission denied"
    echo ""
    echo "On Linux, you may need to add your user to the docker group:"
    echo "sudo usermod -aG docker \$USER"
    echo "Then log out and log back in, or run: newgrp docker"
    exit 1
fi

# Check available disk space
echo "💾 Checking available disk space..."
AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
if [ "$AVAILABLE_SPACE" -gt 5242880 ]; then  # 5GB in KB
    echo "✅ Sufficient disk space available"
else
    echo "⚠️  Low disk space. Docker may fail to pull large images."
    echo "   Available: $(df -h / | awk 'NR==2 {print $4}')"
    echo "   Recommended: At least 5GB free space"
fi

# Test Docker functionality
echo "🧪 Testing Docker functionality..."
if docker run --rm hello-world >/dev/null 2>&1; then
    echo "✅ Docker is working correctly"
else
    echo "❌ Docker test failed"
    echo "Please check your Docker installation and try again"
    exit 1
fi

# Optimize Docker for Arc-Verifier
echo "⚙️  Optimizing Docker configuration for Arc-Verifier..."

# Create or update Docker daemon configuration
DOCKER_CONFIG_DIR=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    DOCKER_CONFIG_DIR="$HOME/.docker"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    DOCKER_CONFIG_DIR="/etc/docker"
else
    echo "⚠️  Unknown OS type, skipping Docker optimization"
fi

if [ -n "$DOCKER_CONFIG_DIR" ] && [ -w "$DOCKER_CONFIG_DIR" ] || [ -w "$(dirname "$DOCKER_CONFIG_DIR")" ]; then
    echo "Optimizing Docker daemon configuration..."
    
    # On macOS, create user config
    if [[ "$OSTYPE" == "darwin"* ]]; then
        mkdir -p "$DOCKER_CONFIG_DIR"
        cat > "$DOCKER_CONFIG_DIR/daemon.json" << 'EOF'
{
  "experimental": false,
  "features": {
    "buildkit": true
  }
}
EOF
        echo "✅ Docker Desktop configuration optimized"
    fi
    
    # On Linux, suggest system-wide optimization
    if [[ "$OSTYPE" == "linux-gnu"* ]] && [ -w "/etc/docker" ]; then
        echo "Creating optimized daemon.json for production use..."
        sudo mkdir -p /etc/docker
        sudo tee /etc/docker/daemon.json > /dev/null << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "experimental": false,
  "features": {
    "buildkit": true
  }
}
EOF
        echo "✅ Docker daemon configuration optimized"
        echo "⚠️  You may need to restart Docker daemon: sudo systemctl restart docker"
    fi
fi

# Pull commonly used images for Arc-Verifier
echo "📥 Pre-pulling common images for Arc-Verifier testing..."
COMMON_IMAGES=(
    "alpine:latest"
    "nginx:latest"
    "node:18-alpine"
    "ubuntu:20.04"
)

for image in "${COMMON_IMAGES[@]}"; do
    echo "Pulling $image..."
    if docker pull "$image" >/dev/null 2>&1; then
        echo "✅ $image pulled successfully"
    else
        echo "⚠️  Failed to pull $image (this is not critical)"
    fi
done

echo ""
echo "🎉 Docker setup complete!"
echo ""
echo "Docker is now optimized for Arc-Verifier production use."
echo ""
echo "Next steps:"
echo "1. Install Trivy: ./scripts/install_trivy.sh"
echo "2. Test Arc-Verifier: arc-verifier scan nginx:latest"
echo ""
echo "For troubleshooting:"
echo "- Check Docker status: docker info"
echo "- View Docker logs: docker system events"
echo "- Arc-Verifier help: arc-verifier --help"