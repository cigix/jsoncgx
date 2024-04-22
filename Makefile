all: architecture.png

%.pdf: %.dot
	dot -Tpdf $^ -o $@

%.png: %.dot
	dot -Tpng $^ -o $@

%.cst.pdf: %.jsonc
	jsoncgx/parser.py $^ | dot -Tpdf -o $@
%.ast.pdf: %.jsonc
	jsoncgx/abstract.py $^ | dot -Tpdf -o $@
%.edit.pdf: %.jsonc
	jsoncgx/rexel.py $^ | dot -Tpdf -o $@

tests:
	python3 -m unittest
	python3 -m mypy jsoncgx

upload: tests
	$(RM) -r dist
	python3 -m build
	python3 -m twine upload --repository testpypi dist/*
	python3 -m twine upload dist/*

.PHONY: all tests upload
