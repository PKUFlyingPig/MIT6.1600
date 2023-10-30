venv:
	python3 -m venv venv
	${SHELL} -c ". venv/bin/activate && pip install -r requirements.txt"

clean:
	-rm -r venv
.PHONY: clean

typecheck: wasi.py
	mypy --strict $^
.PHONY: typecheck

shell: venv
	. venv/bin/activate && python3 interactive.py

grade-lab4: venv
	. venv/bin/activate && python3 grade-lab.py $(GRADE_EXTRA_ARGS)

grade: grade-lab4
.PHONY: grade

%.wasm: %.c
	clang \
		--target=wasm32-unknown-wasi \
		--sysroot=/usr/share/wasi-sysroot \
		-o $@ $^

%-noln.wasm: %.c
	clang \
		-DDISABLE_LN \
		--target=wasm32-unknown-wasi \
		--sysroot=/usr/share/wasi-sysroot \
		-o $@ $^

%-export.wasm: %.c
	clang \
		--target=wasm32-unknown-wasi \
		--sysroot=/usr/share/wasi-sysroot \
		-Wl,--export=malloc \
		-o $@ $^
