.PHONY: lua lua-install lua-install-deps lua-install-lua lua-install-luarocks lua-install-lsp lua-check lua-clean

# Lua Installation Makefile
# Installs lua from source and luarocks manually following official instructions
# Based on: https://github.com/luarocks/luarocks/blob/main/docs/installation_instructions_for_unix.md

LUA_VERSION ?= 5.1.0
LUAROCKS_VERSION ?= 3.11.1
PREFIX ?= /usr/local
BUILD_DIR ?= /tmp/lua-build

# Detect OS
UNAME_S := $(shell uname -s)

lua: lua-check lua-install
	@echo "✓ Lua environment setup complete"

lua-check:
	@echo "Checking lua installation..."
	@command -v lua >/dev/null 2>&1 || echo "⚠ lua not found, will install"
	@command -v luarocks >/dev/null 2>&1 || echo "⚠ luarocks not found, will install"
	@command -v lua-language-server >/dev/null 2>&1 || echo "⚠ lua-language-server not found, will install"

lua-install: lua-install-deps lua-install-lua lua-install-luarocks lua-install-lsp
	@echo "✓ Lua installation complete"

lua-install-deps:
	@echo "Installing build dependencies..."
ifeq ($(UNAME_S),Linux)
	@if command -v apt-get >/dev/null 2>&1; then \
		echo "Installing dependencies with apt..."; \
		sudo apt-get update && \
		sudo apt-get install -y build-essential libreadline-dev unzip curl wget; \
	elif command -v dnf >/dev/null 2>&1; then \
		echo "Installing dependencies with dnf..."; \
		sudo dnf install -y gcc make readline-devel unzip curl wget libtermcap-devel ncurses-devel libevent-devel; \
	elif command -v pacman >/dev/null 2>&1; then \
		echo "Installing dependencies with pacman..."; \
		sudo pacman -S --noconfirm base-devel readline unzip curl wget; \
	else \
		echo "❌ Unsupported package manager"; \
		exit 1; \
	fi
else ifeq ($(UNAME_S),Darwin)
	@echo "Installing dependencies with Homebrew..."
	@if command -v brew >/dev/null 2>&1; then \
		brew install readline unzip curl wget; \
	else \
		echo "❌ Homebrew not found. Install from https://brew.sh"; \
		exit 1; \
	fi
endif
	@echo "✓ Dependencies installed"

lua-install-lua:
	@if command -v lua >/dev/null 2>&1; then \
		echo "Lua already installed: $$(lua -v 2>&1)"; \
	else \
		echo "Installing Lua $(LUA_VERSION) from source..."; \
		mkdir -p $(BUILD_DIR) && cd $(BUILD_DIR) && \
		wget -q https://www.lua.org/ftp/lua-$(LUA_VERSION).tar.gz && \
		tar -xzf lua-$(LUA_VERSION).tar.gz && \
		cd lua-$(LUA_VERSION) && \
		make linux && echo "✓ Lua $(LUA_VERSION) built successfully" && \
		sudo make install && \
		cd .. && rm -rf lua-$(LUA_VERSION) lua-$(LUA_VERSION).tar.gz && \
		echo "✓ Lua $(LUA_VERSION) installed to $(PREFIX)"; \
	fi

lua-install-luarocks:
	
	@if command -v luarocks >/dev/null 2>&1; then \
		echo "LuaRocks already installed: $$(luarocks --version | head -n1)"; \
	else \
		echo "Installing LuaRocks $(LUAROCKS_VERSION) from source..."; \
		mkdir -p $(BUILD_DIR) && cd $(BUILD_DIR) && \
		wget -q https://luarocks.org/releases/luarocks-$(LUAROCKS_VERSION).tar.gz && \
		tar -xzf luarocks-$(LUAROCKS_VERSION).tar.gz && \
		cd luarocks-$(LUAROCKS_VERSION) && \
		./configure --with-lua-include=$(PREFIX)/include && \
		make && \
		sudo make install && \
		cd .. && rm -rf luarocks-$(LUAROCKS_VERSION) luarocks-$(LUAROCKS_VERSION).tar.gz && \
		echo "✓ LuaRocks $(LUAROCKS_VERSION) installed to $(PREFIX)"; \
	fi

lua-install-lsp:
	@echo "Installing Lua development tools..."
	@if command -v luarocks >/dev/null 2>&1; then \
		echo "Installing luacheck..."; \
		luarocks install --local luacheck || sudo luarocks install luacheck || true; \
	fi
	@if command -v npm >/dev/null 2>&1; then \
		echo "Installing lua-language-server via npm..."; \
		sudo npm install -g lua-language-server || echo "⚠ Failed to install lua-language-server via npm"; \
	elif command -v brew >/dev/null 2>&1 && [ "$(UNAME_S)" = "Darwin" ]; then \
		echo "Installing lua-language-server via Homebrew..."; \
		brew install lua-language-server; \
	else \
		echo "⚠ npm or brew not available for lua-language-server installation"; \
	fi
	@echo "✓ Lua development tools installed" 



lua-clean:
	@echo "Cleaning lua build artifacts and cache..."
	@rm -rf ~/.cache/luarocks
	@rm -rf $(BUILD_DIR)/lua-* $(BUILD_DIR)/luarocks-*
	@echo "✓ Lua cache and build artifacts cleaned"

lua-uninstall:
	@echo "Uninstalling Lua and LuaRocks..."
	@if [ -d "$(BUILD_DIR)" ]; then \
		echo "Removing from $(PREFIX)..."; \
		sudo rm -f $(PREFIX)/bin/lua* $(PREFIX)/bin/luarocks*; \
		sudo rm -rf $(PREFIX)/lib/lua* $(PREFIX)/lib/liblua*; \
		sudo rm -rf $(PREFIX)/include/lua* $(PREFIX)/share/lua*; \
		sudo rm -rf $(PREFIX)/lib/luarocks $(PREFIX)/etc/luarocks; \
		echo "✓ Lua and LuaRocks uninstalled"; \
	else \
		echo "Build directory not found, skipping"; \
	fi

lua-help:
	@echo "Lua Makefile Targets:"
	@echo "  lua                   - Install complete lua environment"
	@echo "  lua-install           - Install all lua components"
	@echo "  lua-install-deps      - Install build dependencies only"
	@echo "  lua-install-lua       - Install Lua from source"
	@echo "  lua-install-luarocks  - Install LuaRocks from source"
	@echo "  lua-install-lsp       - Install Lua development tools (LSP, luacheck)"
	@echo "  lua-check             - Check current installation status"
	@echo "  lua-clean             - Clean cache and build artifacts"
	@echo "  lua-uninstall         - Uninstall Lua and LuaRocks"
	@echo "  lua-help              - Show this help message"
	@echo ""
	@echo "Variables:"
	@echo "  LUA_VERSION        - Lua version to install (default: $(LUA_VERSION))"
	@echo "  LUAROCKS_VERSION   - LuaRocks version (default: $(LUAROCKS_VERSION))"
	@echo "  PREFIX             - Installation prefix (default: $(PREFIX))"
	@echo "  BUILD_DIR          - Temporary build directory (default: $(BUILD_DIR))"
	@echo ""
	@echo "Example: make lua LUA_VERSION=5.4.6 PREFIX=/opt/lua"
