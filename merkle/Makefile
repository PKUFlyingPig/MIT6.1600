venv: requirements.txt
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt || ( rm -r venv; false )
	touch venv

run-server: venv
	. venv/bin/activate && python -m flask --app server run

check: venv
	. venv/bin/activate && python grader.py
