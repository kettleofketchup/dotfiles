# Main justfile - imports from just/ directory
set quiet
set dotenv-load

import 'just/dev.just'

# List all available recipes
default:
    just --list
