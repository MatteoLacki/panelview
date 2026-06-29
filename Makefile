.PHONY: demo demo-fail

PYTHON = .venv/bin/python
PV     = .venv/bin/panelview
STAMP  = .venv/.stamp

$(STAMP): pyproject.toml
	python3 -m venv .venv
	.venv/bin/pip install -e . -q
	touch $(STAMP)

# Three silly processes:
#   counter  — counts to 10 on stdout, one per 0.3 s
#   noisyman — alternates lines to stdout and stderr, 0.5 s apart
#   burster  — prints a burst of 20 lines fast, then sleeps and exits
demo: $(STAMP)
	$(PV) \
	  "for i in $$(seq 1 10); do echo \"[counter] line \$$i\"; sleep 0.3; done" \
	  "for i in $$(seq 1 8); do echo \"[stdout] msg \$$i\" >&1; sleep 0.25; echo \"[stderr] err \$$i\" >&2; sleep 0.25; done" \
	  "for i in $$(seq 1 20); do echo \"[burst] \$$i of 20\"; done; echo '[burst] done, sleeping...'; sleep 2"

# Same but one process exits non-zero so you can see the [failed N] state.
demo-fail: $(STAMP)
	$(PV) \
	  "for i in $$(seq 1 5); do echo \"[ok] \$$i\"; sleep 0.4; done" \
	  "echo 'about to fail'; sleep 1; echo 'failing now' >&2; exit 42" \
	  "for i in $$(seq 1 8); do echo \"[slow] \$$i\"; sleep 0.6; done"
