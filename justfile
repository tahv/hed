GITHUB_SERVER_URL := env("GITHUB_SERVER_URL", "https://github.com")
GITHUB_REPOSITORY := env("GITHUB_REPOSITORY", "tahv/hed")

# List available recipes
[default]
list:
    @just --list

# Sync development requirements
sync:
    uv sync

# Open project in neovim
nvim *args:
    uv run -- nvim {{ args }}

# Build Python wheel and sdist
build:
    uv build --no-sources

# Create a news fragment
news filename="":
    uvx towncrier create --no-edit {{ filename }}

# Build changelog from news fragments, or print a draft if `version` is not set
changelog version="":
    uvx towncrier build {{ if version == "" { "--draft --version main" } else { "--version " + version } }}

# Run the ruff linter
ruff *files:
    uvx ruff check --output-format concise {{ files }}

# Print project version
version:
    @uvx hatch version

# Output `version` release notes from CHANGELOG.md
release-notes version:
    @uv run hed --tag "{{ version }}"

# Output project TODO notes
todo:
    rg -g '!pyproject.toml' -g '!justfile' -- TODO

# Run test suite
test *args:
    uv run -m pytest {{ args }}

# Run test suite and report coverage
coverage *args:
    uv run -m coverage erase
    uv run -m coverage run --parallel -m pytest {{ args }}
    uv run -m coverage combine
    uv run -m coverage report
