.PHONY: demo demo-fail

PYTHON = .venv/bin/python
PV     = .venv/bin/panelview
STAMP  = .venv/.stamp

$(STAMP): pyproject.toml
	python3 -m venv .venv
	.venv/bin/pip install -e . -q
	touch $(STAMP)

# Three silly processes:
#   counter  — counts to 10 on stdout, one line per 0.3 s
#   noisyman — alternates lines to stdout and stderr, 0.25 s apart
#   burster  — prints a burst of 20 lines fast, then sleeps
demo: $(STAMP)
	$(PV) \
	  -t counter  'for i in 1 2 3 4 5 6 7 8 9 10; do echo "line $$i"; sleep 0.3; done' \
	  -t noisyman 'for i in 1 2 3 4 5 6 7 8; do echo "out $$i"; sleep 0.25; echo "err $$i" >&2; sleep 0.25; done' \
	  -t burster  'for i in $$(seq 1 20); do echo "burst $$i of 20"; done; sleep 2'

# Live demo: new tabs are added dynamically as earlier processes finish.
demo-live: $(STAMP)
	$(PYTHON) examples/demo_live.py

# Same but one exits non-zero — shows [failed N] in tab title.
demo-fail: $(STAMP)
	$(PV) \
	  -t ok    'for i in 1 2 3 4 5; do echo "ok $$i"; sleep 0.4; done' \
	  -t kaboom 'echo about to fail; sleep 1; echo failing >&2; exit 42' \
	  -t slow  'for i in 1 2 3 4 5 6 7 8; do echo "slow $$i"; sleep 0.6; done'
