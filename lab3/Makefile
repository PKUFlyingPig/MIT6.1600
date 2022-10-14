venv:
	python3 -m venv venv
	${SHELL} -c ". venv/bin/activate && pip install -r requirements.txt"

doctest: venv
	. venv/bin/activate && python3 -m unittest 
.PHONY: doctest

clean:
	-rm -r venv
.PHONY: clean

run-server: venv
	. venv/bin/activate && python -m flask --app server/app run
.PHONY: run-server

grade-lab%: venv
	. venv/bin/activate && python3 grade-lab.py --lab=$(patsubst grade-lab%,%,$@) $(GRADE_EXTRA_ARGS)

prepare:
	zip -r 61600-pset.zip client

grade: grade-lab3
.PHONY: grade

