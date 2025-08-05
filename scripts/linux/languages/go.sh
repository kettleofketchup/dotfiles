#!/bin/bash
GO_URL=$(curl -s https://go.dev/VERSION?m=text | head -n1 | xargs -I{} echo "https://go.dev/dl/{}.linux-amd64.tar.gz")
GO_VERSION=$(basename $GO_URL .linux-amd64.tar.gz)
curl -LO $GO_URL
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf ${GO_VERSION}.linux-amd64.tar.gz
rm ${GO_VERSION}.linux-amd64.tar.gz








