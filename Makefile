.PHONY: test test-fast test-fundingcaptcha

# Everything. pytest exits 5 when it collects no tests; that is not a failure.
test:
	node --test
	python3 -m pytest || test $$? -eq 5

# Everything except FundingCAPTCHA. Seconds; needs no OpenGL.
test-fast:
	node --test
	python3 -m pytest --ignore=ShowControl/FundingCAPTCHA || test $$? -eq 5

# FundingCAPTCHA only. The shader tests need a headless OpenGL context and
# take minutes on software Mesa; without one they skip (locally) or fail (CI).
test-fundingcaptcha:
	python3 -m pytest ShowControl/FundingCAPTCHA || test $$? -eq 5
