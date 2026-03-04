# NetBox Plugin Certification Checklist

Source checklist:

- https://github.com/netbox-community/netbox/wiki/Plugin-Certification-Program

This file maps certification requirements to evidence in this repository and identifies external actions.

## Repository Criteria

- [x] Open source license present
  - Evidence: [LICENSE](../LICENSE)

- [x] Plugin metadata and compatibility are explicitly documented
  - Evidence: [README.md](../README.md), [docs/compatibility.md](compatibility.md), [netbox_attachments/__init__.py](../netbox_attachments/__init__.py)

- [x] Installation and configuration docs are available
  - Evidence: [docs/installation.md](installation.md), [docs/configuration.md](configuration.md)

- [x] Usage/API documentation is available
  - Evidence: [docs/usage.md](usage.md)

- [x] Changelog/release notes are maintained
  - Evidence: [CHANGELOG.md](../CHANGELOG.md), [docs/release-process.md](release-process.md)

- [x] Contribution and support pathways are documented
  - Evidence: [CONTRIBUTING.md](../CONTRIBUTING.md), [README.md](../README.md)
- [x] Automated test/build workflow exists
  - Evidence: [ci.yml](../.github/workflows/ci.yml)

## External Criteria (Maintainer Action)

- [ ] Co-maintainer configured for GitHub repository
  - Owner: Maintainer

- [ ] Co-maintainer configured for PyPI project
  - Owner: Maintainer

- [ ] NetDev community account confirmed for maintainer
  - Owner: Maintainer

- [ ] Certification request issue opened in `netbox-community/netbox`
  - Owner: Maintainer
  - Include links to: PyPI package, CI runs, docs index, changelog, support section

## Submission Bundle Links

- Repository: https://github.com/Kani999/netbox-attachments
- PyPI: https://pypi.org/project/netbox-attachments/
- Docs index: [docs/index.md](index.md)
- Changelog: [CHANGELOG.md](../CHANGELOG.md)
- CI workflow: [ci.yml](../.github/workflows/ci.yml)
