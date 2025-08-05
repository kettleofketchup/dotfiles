#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/usr/local/bin"

uname_os=$(uname | tr '[:upper:]' '[:lower:]')
arch=$(uname -m)
case "$arch" in
  x86_64) arch="x86_64" ;;
  arm64|aarch64) arch="aarch64" ;;
  *) echo "Unsupported arch: $arch"; exit 1 ;;
esac

echo "Fetching latest bat release info..."
latest_json=$(curl -sL https://api.github.com/repos/sharkdp/bat/releases/latest)

version=$(echo "$latest_json" | grep -Po '"tag_name":\s*"\K.*?(?=")')
echo "Latest version: $version"

if [[ "$uname_os" == "darwin" ]]; then
    asset_pattern="bat-${version}-${arch}-apple-darwin.tar.gz"
else
    asset_pattern="bat-${version}-${arch}-unknown-linux-gnu.tar.gz"
fi

download_url=$(echo "$latest_json" |
    grep "browser_download_url" |
    grep "$asset_pattern" |
    cut -d '"' -f 4)

if [[ -z "$download_url" ]]; then
    echo "Could not find suitable release asset for OS=$uname_os, ARCH=$arch"
    exit 1
fi

echo "Downloading $asset_pattern..."
curl -L "$download_url" -o "/tmp/$asset_pattern"

echo "Extracting..."
tar -xzf "/tmp/$asset_pattern" -C /tmp

EXTRACTED_DIR=$(tar -tf "/tmp/$asset_pattern" | grep -o '^[^/]\+' | sort -u | head -1)
echo "Extracted directory: /tmp/${EXTRACTED_DIR}"

BAT_PATH=$(find "/tmp/${EXTRACTED_DIR}" -type f -name bat | head -1)

if [[ -z "$BAT_PATH" ]]; then
    echo "Failed to find bat binary in extracted directory."
    exit 1
fi

echo "Moving bat binary to $INSTALL_DIR (requires sudo)..."
sudo mv "$BAT_PATH" "$INSTALL_DIR/bat"
sudo chmod +x "$INSTALL_DIR/bat"