# Homebrew distribution

The public application repository is <https://github.com/alvaroum/cli-anything-penpot>. The formula is published in the `alvaroum/homebrew-tap` repository.

## Install

```sh
brew tap alvaroum/tap
brew install cli-anything-penpot
cli-anything-penpot --help
```

The formula installs the CLI into an isolated Python virtual environment and exposes both `cli-anything-penpot` and `penpot`.

## Release flow

1. Update the version in `pyproject.toml` and the formula.
2. Create and push a matching Git tag, for example `v0.1.0`.
3. Create the GitHub release.
4. Compute the tagged source archive SHA-256 with `shasum -a 256`.
5. Update the formula URL, checksum, and test version.
6. Push the formula to `alvaroum/homebrew-tap`.
7. Run `brew audit --new-formula cli-anything-penpot` and `brew install --build-from-source alvaroum/tap/cli-anything-penpot`.

The v0.1.0 formula uses the published tagged archive and pinned Click 8.3.3 wheel resource.
