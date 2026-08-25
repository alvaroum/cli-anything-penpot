# Homebrew distribution

The formula in `Formula/cli-anything-penpot.rb` is intended for a tap repository. Homebrew installs the package into an isolated Python virtual environment and exposes the `cli-anything-penpot` executable.

## Release flow

1. Create a Git tag matching the package version, for example `v0.1.0`.
2. Push the tag and wait for the GitHub release archive to exist.
3. Replace the formula `url` with the tagged archive URL and its SHA-256 (`shasum -a 256 ...`).
4. Set `homepage` to the repository URL and commit the formula to a tap.
5. Run `brew audit --new-formula cli-anything-penpot` and `brew install --build-from-source <tap>/cli-anything-penpot`.
6. Smoke test `cli-anything-penpot --help` and `cli-anything-penpot --version`.

The source archive URL and checksum are placeholders until a public Git remote exists; do not publish the formula unchanged.
