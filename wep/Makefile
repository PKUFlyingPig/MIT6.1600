venv: requirements.txt
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt || ( rm -r venv; false )
	touch venv

run-server: venv
	venv/bin/python -m flask --app server run

check: venv
	venv/bin/python grader.py
