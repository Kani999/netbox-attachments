.PHONY: test format lint

test:
	bash -lc 'if [ -f /opt/netbox/venv/bin/activate ]; then source /opt/netbox/venv/bin/activate; fi; pytest -q'

format:
	ruff format netbox_attachments/

lint:
	ruff check netbox_attachments/
