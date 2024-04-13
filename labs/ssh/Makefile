.PHONY: venv

venv: requirements.txt keys/server keys/client
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt || ( rm -r venv; false )
	touch venv

keys/server:
	mkdir -p keys
	ssh-keygen -t ed25519 -f keys/server -N ""

keys/client:
	mkdir -p keys
	ssh-keygen -t ed25519 -f keys/client -N ""
