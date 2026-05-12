.PHONY: test

test:
	node --test
	python3 -m pytest || test $$? -eq 5
