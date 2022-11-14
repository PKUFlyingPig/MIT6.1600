venv:
	python3 -m venv venv
	${SHELL} -c ". venv/bin/activate && pip install -r requirements.txt"

clean:
	-rm -r venv
.PHONY: clean

typecheck: api.py attacker.py secure_server.py
	mypy --strict $^
.PHONY: typecheck

check: venv
	. venv/bin/activate && python3 attacker.py
.PHONY: check

grade-lab5: venv
	. venv/bin/activate && python3 grade-lab.py $(GRADE_EXTRA_ARGS)
.PHONY: grade-lab5

grade: grade-lab5
.PHONY: grade

