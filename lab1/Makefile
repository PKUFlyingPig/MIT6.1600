venv:
	python3 -m venv venv
	${SHELL} -c ". venv/bin/activate && pip install -r requirements.txt"

test: venv
	. venv/bin/activate && python3 -m doctest client/client.py common/crypto.py common/codec.py
.PHONY: test

clean:
	-rm -r venv
.PHONY: clean

run-server: venv
	. venv/bin/activate && python -m flask --app server/app run
.PHONY: run-server

grade-lab1: venv
	. venv/bin/activate && python3 grade-lab.py --lab=1
.PHONY: grade-lab1

