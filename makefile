.PHONY: help all install lua

# Main Makefile for dotfiles
# Author: kettle
include scripts/lua.mk

# Default target
all: help
help:
	@echo "Available targets:"
	@echo "  help      - Show this help message"
	@echo "  install   - Install dotfiles using stow"
	@echo "  lua       - Install lua development environment"
	@echo ""
	@echo "For more detailed help on lua target, run: make lua-help"

install:
	@echo "Installing dotfiles..."
	@./install_linux.sh
	@echo "✓ Dotfiles installed"

# Include lua makefile
