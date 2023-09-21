# Setting up Virtual Environment

Instead of `make venv`:

```
python3 -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

# Running the Lab

Make sure you have called activate on your venv.

Instead of `venv/bin/python cli.py ...` 
```
python cli.py <get/put/reset>
```

Instead of `make run-server`:
```
python -m flask --app server run
```


Instead of `make check`:
```
python grader.py
```
