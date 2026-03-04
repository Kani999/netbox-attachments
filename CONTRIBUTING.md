# Contributing

Thanks for contributing to `netbox-attachments`.

## Development Setup

1. Clone the repository.
2. Ensure your NetBox development environment is available.
3. Install development tooling as needed (`pytest`, `build`).

## Test Commands

Primary local tests:

```bash
make test
```

Package build verification:

```bash
python -m build
```

## Pull Requests

- Keep PRs focused and minimal.
- Include tests for behavior changes.
- Update docs and changelog entries when user-facing behavior changes.
- Ensure CI is passing before requesting review.

## Commit and Release Conventions

- Use clear commit messages describing intent and scope.
- Follow Semantic Versioning.
- Document release notes in [CHANGELOG.md](CHANGELOG.md).

## Reporting Issues

Use GitHub Issues for bugs/feature requests:

- https://github.com/Kani999/netbox-attachments/issues

