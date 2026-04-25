PYTHON=python3

export BOND_ROOT := $(CURDIR)
export PYTHONPATH := $(CURDIR)/src$(if $(PYTHONPATH),:$(PYTHONPATH))

compile:
	$(PYTHON) -m compileall src/bond

selftest:
	$(PYTHON) src/bond/ai_selftest.py

smoke:
	$(PYTHON) -m compileall src/bond && $(PYTHON) src/bond/ai_selftest.py

reviewcheck:
	@./scripts/bond-reviewcheck \
		--docs-reviewed "$${DOCS_REVIEWED:-no}" \
		--docs-updated "$${DOCS_UPDATED:-no}" \
		--external-context-needed "$${EXTERNAL_CONTEXT_NEEDED:-no}" \
		--external-context-provided "$${EXTERNAL_CONTEXT_PROVIDED:-no}" \
		--change-summary "$${CHANGE_SUMMARY:-}" \
		--docs-impact-note "$${DOCS_IMPACT_NOTE:-}" \
		--external-context-note "$${EXTERNAL_CONTEXT_NOTE:-}"
