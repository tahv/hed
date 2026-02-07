# Changelog

Versions follow [Semantic Versioning](https://semver.org) (`<major>.<minor>.<patch>`).

This file is managed by [towncrier](https://towncrier.readthedocs.io),
and its format is based on [keep a changelog](https://keepachangelog.com).

Changes for the upcoming release can be found in the
[changelog.d directory](https://github.com/tahv/hed/tree/main/changelog.d)
in the repo.

<!-- towncrier release notes start -->

## [1.2.0](https://github.com/tahv/hed/releases/tag/1.2.0) - 2026-02-07

### Enhancements

- [!12](https://github.com/tahv/hed/issues/12):
  Add flag `--softbreak/--no-softbreak` to format
  [softbreaks](https://github.github.com/gfm/#softbreak).
  This is useful for GitHub release notes, where soft line breaks are not supported.
- [!12](https://github.com/tahv/hed/issues/12):
  Support [GitHub style tables](https://github.github.com/gfm/#tables-extension-).
- [!13](https://github.com/tahv/hed/issues/13):
  Add `-V` flag, alias for `--version`.

### Bug fixes

- [!10](https://github.com/tahv/hed/issues/10):
  Fix version returned by `hed --version`.

### Other changes

- [!12](https://github.com/tahv/hed/issues/12):
  Use [mistletoe](https://github.com/miyuchina/mistletoe) to parse markdown.

## [1.1.0](https://github.com/tahv/hed/releases/tag/1.1.0) - 2026-01-16

### Enhancements

- [!5](https://github.com/tahv/hed/issues/5):
  The `--changelog` option supports stdin by using the `-` special character.

    Changelog can be provided in the following ways:

    ```bash
    # Positional stdin
    $ cat CHANGELOG.md | hed --tag 1.0.0 -

    # Keyword stdin
    $ cat CHANGELOG.md | hed --tag 1.0.0 --changelog -

    # Keyword path
    $ hed --tag 1.0.0 --changelog CHANGELOG.md

    # Positional path
    $ hed --tag 1.0.0 CHANGELOG.md
    ```

- [!5](https://github.com/tahv/hed/issues/5):
  `--changelog` can be a positional argument or a keyword option.

## [1.0.0](https://github.com/tahv/hed/releases/tag/1.0.0) - 2026-01-14

- [!1](https://github.com/tahv/hed/issues/1):
  Initial release.
