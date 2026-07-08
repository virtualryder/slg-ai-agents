# SLG AI Agent Suite — developer convenience targets (no API key, no AWS).
PYTHON ?= python
export PYTHONPATH := platform_core:.

.PHONY: help test eval-311 eval-311-gen

help:
	@echo "SLG targets:"
	@echo "  make test         run the control-plane + governance unit suite (no API key)"
	@echo "  make eval-311     scored quality eval for Agent 01 (Resident Services / 311);"
	@echo "                    gates on regulatory thresholds incl. the PII-leak hard gate"
	@echo "  make eval-311-gen regenerate the labeled 311 golden set, then score it"

# --- unit suite (control plane + governance) ---------------------------------
test:
	$(PYTHON) -m pytest platform_core/tests governance/tests -q

# --- scored eval for the hero pilot (Agent 01 / 311) -------------------------
eval-311:  ## Scored eval for Agent 01 (Resident Services / 311) — gates on thresholds
	$(PYTHON) -m governance.evals.score_311

eval-311-gen:
	$(PYTHON) -m governance.evals.gen_golden_311
	$(PYTHON) -m governance.evals.score_311
