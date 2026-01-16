# Changelog

Versions follow [Semantic Versioning](https://semver.org) (`<major>.<minor>.<patch>`).

This file is managed by [towncrier](https://towncrier.readthedocs.io),
and its format is based on [keep a changelog](https://keepachangelog.com).

Changes for the upcoming release can be found in the
[changelog.d directory](https://github.com/tahv/hed/tree/main/changelog.d)
in the repo.

<!-- towncrier release notes start -->

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
