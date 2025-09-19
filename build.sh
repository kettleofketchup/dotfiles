#!/bin/bash
# Build the Go project
echo "Building Go project..."
cd src
go build -o ../bin/dotfiles .
cd ..
echo "Build complete!"
