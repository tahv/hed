check-wheel-contents := "uvx check-wheel-contents@0.6.3"
creosote := "uvx creosote@5.2.0"
hatch := "uvx hatch@1.18.0"
ruff := "uvx ruff@0.16.6"
towncrier := "uvx towncrier@25.8.0"
twine := "uvx twine@7.0.0"
uvbump := "uvx --from git+https://github.com/Rezarys/uvbump@3f33228 uvbump"
ty := "uvx ty@0.0.80"
tombi := "uvx tombi@1.8.9"
rumdl := "uvx rumdl@0.3.0"

# List available recipes
[default]
list:
    @just --list --list-heading "" --list-prefix ""

# Sync development requirements
sync:
    uv sync

# Open project in neovim
nvim *args:
    uv run -- nvim {{ args }}

# Build Python wheel and sdist
build:
    uv build --no-sources
    {{ check-wheel-contents }} dist/*.whl
    {{ twine }} check --strict dist/*

# Run mypy type checker
mypy:
    uv run -m mypy

# Perform type-checking with `ty`
ty:
    {{ ty }} check

# Create a news fragment
news filename="":
    {{ towncrier }} create --no-edit {{ filename }}

# Build changelog from news fragments, or print a draft if `version` is not set
changelog version="":
    {{ towncrier }} build {{ if version == "" { "--draft --version main" } else { "--version " + version } }}

# Run `ruff` linter
ruff *files:
    {{ ruff }} check --output-format concise {{ files }}

# Dry run `ruff` formatter and output diff
fmt:
    {{ ruff }} format --check

# Update project dependencies
update:
    @{{ uvbump }} --exclude bpy

# Identify unused dependencies
creosote:
    @{{ creosote }}

# Run `rumdl` linter for Markdown
rumdl:
    @{{ rumdl }} check

# Run `tombi` linter for TOML
tombi:
    @{{ tombi }} check

# Print project version
version:
    @{{ hatch }} version

# Print release notes from `CHANGELOG.md` for `version`
hed version:
    @uv run hed --tag {{ version }}

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

# Generate `.github/README.md`
[script("uv", "run", "--script")]
github-readme:
    import sys, pathlib
    header = """\
    > [!IMPORTANT]
    > Development takes place on GitLab:
    > [gitlab.com/tahv/menuet](https://gitlab.com/tahv/hed).

    """
    body = pathlib.Path('README.md').read_text()
    pathlib.Path(".github/README.md").write_text(f"{header}{body}")
