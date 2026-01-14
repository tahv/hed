# Hed

Extract release notes from markdown changelog that follow
"[keep a changelog](https://keepachangelog.com)"
or "[common changelog](https://common-changelog.org)" format.

Hed, pronounced "head" (`/hɛd/`),
is journalistic shorthand referring to the "headline" of a news story.

## Installation

```bash
pip install hed
```

With [uv](https://docs.astral.sh/uv/):

```bash
uv tool install hed
```

## How it works

1. Extract `--changelog` lines between `--capture-start` (included)
   and `--capture-end` (not included).
2. Normalize the extracted headings so the topmost heading becomes h1,
   e.g., `## Title` becomes `# Title`.

Depending on how it was configured, `hed` can apply some transformations
to the extracted release notes:

- If `--title` is provided, update the h1.
- If `--diff-url` is provided, adds a link to compare between tags at the end.
  If `--previous-tag` is also provided, this tag is used to build the comparison link,
  otherwise, `hed` will try to find the closest reachable tag from `--tag`.

## Configuration

Some command-line options can be configured via `hed.toml` or `pyproject.toml`,
under the `tool.hed` namespace.
See <https://toml.io/> for how to write TOML.

```toml
[tool.hed]
changelog = "CHANGELOG.md"
capture-end = '^## {tag}'
capture-start = '^## '
diff-url = "https://github.com/owner/repo/compare/{prev}...{tag}"
title = "{tag}"
```

## Usage

Given a `CHANGELOG.md` file similar to this:

```markdown
# Changelog

## [1.0.1](https://github.com/owner/repo/releases/tag/1.0.1) - 2026-01-10

### Bug fixes

- Fixed a thing! (#1235)

## [1.0.0](https://github.com/owner/repo/releases/tag/1.0.0) - 2026-01-9

### Breaking changes

- Removed a deprecated feature. (#1234)
```

Extract and normalize release notes:

```text
$ hed --tag 1.0.1
# [1.0.1](https://github.com/owner/repo/releases/tag/1.0.1) - 2026-01-10

## Bug fixes

- Fixed a thing! (#1235)

```

Change the title:

```text
$ hed --tag 1.0.1 --title "{tag} Release Notes"
# 1.0.1 Release Notes

## Bug fixes

- Fixed a thing! (#1235)

```

Add a link to compare between releases:

```text
$ hed --tag 1.0.1 --previous-tag 1.0.0 --diff-url "https://github.com/owner/repo/compare/{prev}...{tag}"
# [1.0.1](https://github.com/owner/repo/releases/tag/1.0.1) - 2026-01-10

## Bug fixes

- Fixed a thing! (#1235)

**Full Changelog:** [1.0.0...1.0.1](https://github.com/owner/repo/compare/1.0.0...1.0.1)

```

## CI Integration

### GitLab

Create a GitLab release using the
[release](https://docs.gitlab.com/ci/yaml/#release) keyword.

```yaml
gitlab-release:
  stage: deploy
  image: registry.gitlab.com/gitlab-org/cli:latest
  rules:
    - if: $CI_COMMIT_TAG
  script:
    - apk update && apk add curl
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - source $HOME/.local/bin/env
    - uvx hed
      --tag $CI_COMMIT_TAG
      --diff-url "$CI_PROJECT_URL/-/compare/{prev}...{tag}"
      > RELEASE_NOTES.md
  release:
    tag_name: '$CI_COMMIT_TAG'
    name: '$CI_COMMIT_TAG'
    description: 'RELEASE_NOTES.md'
```

### GitHub

Create a GitHub release using
[softprops/action-gh-release](https://github.com/softprops/action-gh-release).

```yaml
jobs:
  draft-release:
    name: Create Release
    runs-on: ubuntu-latest
    if: github.ref_type == 'tag'
    permissions:
      contents: write
    steps:
      - uses: astral-sh/setup-uv@v7
      - run: >
          uvx hed
          --tag "${{ github.ref_name }}"
          --diff-url "$GITHUB_SERVER_URL/$GITHUB_REPOSITORY/compare/{prev}...{tag}"
          > RELEASE_NOTES.md
      - uses: softprops/action-gh-release@v2
        with:
          body_path: 'RELEASE_NOTES.md'
```

## Contributing

For guidance on setting up a development environment and contributing,
see [CONTRIBUTING.md](https://github.com/tahv/hed/blob/main/CONTRIBUTING.md).
