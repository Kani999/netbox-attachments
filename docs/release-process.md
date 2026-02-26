# Release Process

This project follows Semantic Versioning and Keep a Changelog.

## Versioning Rules

- Major: breaking changes, NetBox compatibility line shifts
- Minor: backward-compatible features
- Patch: bug fixes and maintenance

## Release Steps

1. Ensure CI is green (`ci.yml`).
2. Update [CHANGELOG.md](../CHANGELOG.md) for the new version.
3. Create a Git tag matching the version in `netbox_attachments/version.py`.
4. Publish GitHub release notes from changelog entries.
5. Let the publish workflow upload distributions to TestPyPI/PyPI.

## Artifact Validation

Before tagging:

```bash
make test
python -m build
```

## Backward Compatibility Notes

Any NetBox support-window changes must be documented in:

- [docs/compatibility.md](compatibility.md)
- [README.md](../README.md)
- [CHANGELOG.md](../CHANGELOG.md)
