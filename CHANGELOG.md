# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [11.0.0] - 2026-02-26

### Added

- Certification documentation set under `docs/`.
- CI workflow for tests and build validation.
- Governance documents (`CONTRIBUTING.md`, certification checklist).
- Standalone pytest coverage for configuration and template helper behavior.

### Changed

- NetBox compatibility locked to `4.5.x` in plugin runtime bounds.
- Project packaging migrated to `pyproject.toml`.
- README aligned to current compatibility policy and support channels.
- Unlinking the last assignment no longer auto-deletes the attachment or its file. Attachments now persist until explicitly deleted.

### Fixed

- Redirect to a deleted attachment URL after unlinking the last assignment (404 error).

## [10.0.0] - 2025-11-11

### Changed

- NetBox 4.5 compatibility line introduced.

[11.0.0]: https://github.com/Kani999/netbox-attachments/releases/tag/v11.0.0
[10.0.0]: https://github.com/Kani999/netbox-attachments/releases/tag/v10.0.0
