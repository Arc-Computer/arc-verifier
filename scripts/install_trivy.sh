#!/bin/bash

# Install Trivy vulnerability scanner for Arc-Verifier
# Supports macOS, Linux, and detects WSL for Windows

set -e

echo "🔧 Installing Trivy vulnerability scanner for Arc-Verifier..."

# Detect operating system
OS=""
case "$(uname -s)" in
    Darwin*)
        OS="darwin"
        echo "Detected: macOS"
        ;;
    Linux*)
        if grep -q Microsoft /proc/version 2>/dev/null; then
            OS="wsl"
            echo "Detected: Windows WSL"
        else
            OS="linux"
            echo "Detected: Linux"
        fi
        ;;
    *)
        echo "❌ Unsupported operating system: $(uname -s)"
        exit 1
        ;;
esac

# Check if Trivy is already installed
if command -v trivy &> /dev/null; then
    CURRENT_VERSION=$(trivy --version | grep -oE "v[0-9]+\.[0-9]+\.[0-9]+" | head -1)
    echo "✅ Trivy is already installed: $CURRENT_VERSION"
    echo "Checking for updates..."
fi

# Install Trivy based on OS
case "$OS" in
    darwin)
        echo "Installing Trivy via Homebrew..."
        if ! command -v brew &> /dev/null; then
            echo "❌ Homebrew not found. Please install Homebrew first:"
            echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
        
        # Update brew and install/upgrade trivy
        brew update
        if command -v trivy &> /dev/null; then
            brew upgrade aquasecurity/trivy/trivy || echo "Trivy is already up to date"
        else
            brew install aquasecurity/trivy/trivy
        fi
        ;;
    
    linux|wsl)
        echo "Installing Trivy via package manager..."
        
        # Detect package manager
        if command -v apt-get &> /dev/null; then
            # Debian/Ubuntu
            echo "Using apt package manager..."
            
            # Install prerequisites
            sudo apt-get update
            sudo apt-get install -y wget apt-transport-https gnupg lsb-release curl
            
            # Add Trivy repository
            wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
            echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
            
            # Install Trivy
            sudo apt-get update
            sudo apt-get install -y trivy
            
        elif command -v yum &> /dev/null; then
            # RHEL/CentOS/Fedora
            echo "Using yum package manager..."
            
            # Add repository
            cat << EOF | sudo tee /etc/yum.repos.d/trivy.repo
[trivy]
name=Trivy repository
baseurl=https://aquasecurity.github.io/trivy-repo/rpm/releases/\$basearch/
gpgcheck=1
enabled=1
gpgkey=https://aquasecurity.github.io/trivy-repo/rpm/public.key
EOF
            
            # Install Trivy
            sudo yum install -y trivy
            
        elif command -v pacman &> /dev/null; then
            # Arch Linux
            echo "Using pacman package manager..."
            sudo pacman -Sy trivy
            
        else
            echo "⚠️  No supported package manager found. Installing via binary..."
            
            # Fallback: Install binary directly
            TRIVY_VERSION=$(curl -s https://api.github.com/repos/aquasecurity/trivy/releases/latest | grep '"tag_name"' | cut -d '"' -f 4)
            ARCH=$(uname -m)
            
            # Map architecture
            case "$ARCH" in
                x86_64) ARCH="64bit" ;;
                aarch64|arm64) ARCH="ARM64" ;;
                *) echo "❌ Unsupported architecture: $ARCH"; exit 1 ;;
            esac
            
            # Download and install
            DOWNLOAD_URL="https://github.com/aquasecurity/trivy/releases/download/${TRIVY_VERSION}/trivy_${TRIVY_VERSION#v}_Linux-${ARCH}.tar.gz"
            
            echo "Downloading Trivy ${TRIVY_VERSION} for Linux-${ARCH}..."
            curl -L "$DOWNLOAD_URL" | tar xz -C /tmp
            sudo mv /tmp/trivy /usr/local/bin/
            sudo chmod +x /usr/local/bin/trivy
        fi
        ;;
esac

# Verify installation
echo ""
echo "🔍 Verifying Trivy installation..."
if command -v trivy &> /dev/null; then
    INSTALLED_VERSION=$(trivy --version | grep -oE "v[0-9]+\.[0-9]+\.[0-9]+" | head -1)
    echo "✅ Trivy successfully installed: $INSTALLED_VERSION"
    
    # Test with a simple scan
    echo ""
    echo "🧪 Testing Trivy with a quick scan..."
    if trivy image --quiet --format table alpine:latest | head -5; then
        echo "✅ Trivy is working correctly!"
    else
        echo "⚠️  Trivy installed but test scan failed. This may be normal for some environments."
    fi
else
    echo "❌ Trivy installation failed"
    exit 1
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Arc-Verifier is now ready to use. Try:"
echo "  arc-verifier scan nginx:latest"
echo "  arc-verifier verify your-agent:latest"
echo ""
echo "For more information:"
echo "  arc-verifier --help"
echo "  Trivy documentation: https://aquasecurity.github.io/trivy/"