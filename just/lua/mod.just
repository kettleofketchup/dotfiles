# Lua Installation Module
# Installs lua from source and luarocks manually following official instructions
# Based on: https://github.com/luarocks/luarocks/blob/main/docs/installation_instructions_for_unix.md
#
# Usage: just lua::install, just lua::check, just lua::clean

lua_version := env("LUA_VERSION", "5.1.0")
luarocks_version := env("LUAROCKS_VERSION", "3.11.1")
prefix := env("PREFIX", "/usr/local")
build_dir := env("BUILD_DIR", "/tmp/lua-build")

# Install complete lua environment
[group('lua')]
default: check install
    echo "Lua environment setup complete"

# Check current lua installation status
[group('lua')]
check:
    echo "Checking lua installation..."
    command -v lua >/dev/null 2>&1 || echo "lua not found, will install"
    command -v luarocks >/dev/null 2>&1 || echo "luarocks not found, will install"
    command -v lua-language-server >/dev/null 2>&1 || echo "lua-language-server not found, will install"

# Install all lua components
[group('lua')]
install: install-deps install-lua install-luarocks install-lsp
    echo "Lua installation complete"

# Install build dependencies
[group('lua')]
install-deps:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Installing build dependencies..."
    case "$(uname -s)" in
        Linux)
            if command -v apt-get >/dev/null 2>&1; then
                echo "Installing dependencies with apt..."
                sudo apt-get update
                sudo apt-get install -y build-essential libreadline-dev unzip curl wget
            elif command -v dnf >/dev/null 2>&1; then
                echo "Installing dependencies with dnf..."
                sudo dnf install -y gcc make readline-devel unzip curl wget libtermcap-devel ncurses-devel libevent-devel
            elif command -v pacman >/dev/null 2>&1; then
                echo "Installing dependencies with pacman..."
                sudo pacman -S --noconfirm base-devel readline unzip curl wget
            else
                echo "Unsupported package manager"
                exit 1
            fi
            ;;
        Darwin)
            echo "Installing dependencies with Homebrew..."
            if command -v brew >/dev/null 2>&1; then
                brew install readline unzip curl wget
            else
                echo "Homebrew not found. Install from https://brew.sh"
                exit 1
            fi
            ;;
    esac
    echo "Dependencies installed"

# Install Lua from source
[group('lua')]
install-lua:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v lua >/dev/null 2>&1; then
        echo "Lua already installed: $(lua -v 2>&1)"
    else
        echo "Installing Lua {{ lua_version }} from source..."
        mkdir -p {{ build_dir }}
        cd {{ build_dir }}
        wget -q https://www.lua.org/ftp/lua-{{ lua_version }}.tar.gz
        tar -xzf lua-{{ lua_version }}.tar.gz
        cd lua-{{ lua_version }}
        make linux
        echo "Lua {{ lua_version }} built successfully"
        sudo make install
        cd ..
        rm -rf lua-{{ lua_version }} lua-{{ lua_version }}.tar.gz
        echo "Lua {{ lua_version }} installed to {{ prefix }}"
    fi

# Install LuaRocks from source
[group('lua')]
install-luarocks:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v luarocks >/dev/null 2>&1; then
        echo "LuaRocks already installed: $(luarocks --version | head -n1)"
    else
        echo "Installing LuaRocks {{ luarocks_version }} from source..."
        mkdir -p {{ build_dir }}
        cd {{ build_dir }}
        wget -q https://luarocks.org/releases/luarocks-{{ luarocks_version }}.tar.gz
        tar -xzf luarocks-{{ luarocks_version }}.tar.gz
        cd luarocks-{{ luarocks_version }}
        ./configure --with-lua-include={{ prefix }}/include
        make
        sudo make install
        cd ..
        rm -rf luarocks-{{ luarocks_version }} luarocks-{{ luarocks_version }}.tar.gz
        echo "LuaRocks {{ luarocks_version }} installed to {{ prefix }}"
    fi

# Install Lua development tools (LSP, luacheck)
[group('lua')]
install-lsp:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Installing Lua development tools..."
    if command -v luarocks >/dev/null 2>&1; then
        echo "Installing luacheck..."
        luarocks install --local luacheck || sudo luarocks install luacheck || true
    fi
    if command -v npm >/dev/null 2>&1; then
        echo "Installing lua-language-server via npm..."
        sudo npm install -g lua-language-server || echo "Failed to install lua-language-server via npm"
    elif command -v brew >/dev/null 2>&1 && [ "$(uname -s)" = "Darwin" ]; then
        echo "Installing lua-language-server via Homebrew..."
        brew install lua-language-server
    else
        echo "npm or brew not available for lua-language-server installation"
    fi
    echo "Lua development tools installed"

# Clean lua build artifacts and cache
[group('lua')]
clean:
    echo "Cleaning lua build artifacts and cache..."
    rm -rf ~/.cache/luarocks
    rm -rf {{ build_dir }}/lua-* {{ build_dir }}/luarocks-*
    echo "Lua cache and build artifacts cleaned"

# Uninstall Lua and LuaRocks
[group('lua')]
uninstall:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Uninstalling Lua and LuaRocks..."
    echo "Removing from {{ prefix }}..."
    sudo rm -f {{ prefix }}/bin/lua* {{ prefix }}/bin/luarocks*
    sudo rm -rf {{ prefix }}/lib/lua* {{ prefix }}/lib/liblua*
    sudo rm -rf {{ prefix }}/include/lua* {{ prefix }}/share/lua*
    sudo rm -rf {{ prefix }}/lib/luarocks {{ prefix }}/etc/luarocks
    echo "Lua and LuaRocks uninstalled"
