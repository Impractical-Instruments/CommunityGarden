.PHONY: test

test:
	node --test
	python -m pytest || test $$? -eq 5
