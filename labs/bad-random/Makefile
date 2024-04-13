venv: ecdsa/requirements.txt wep/requirements.txt
	python3 -m venv venv
	venv/bin/pip install -r ecdsa/requirements.txt || ( rm -r venv; false )
	venv/bin/pip install -r wep/requirements.txt || ( rm -r venv; false )
	touch venv

check-ecdsa: venv
	venv/bin/python ecdsa/grader.py

check-wep: venv
	venv/bin/python wep/grader.py

check: check-ecdsa check-wep

