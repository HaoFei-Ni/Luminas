"""Luminas quality-gate tooling (not model / scheduler code).

Taxonomy:

- ``tools.checks.*`` — analyzers (architecture, native C/CUDA, reliability,
  naming, performance, Python AST, comment policy)
- ``tools.reporting.*`` — Python structure gate + bilingual reports
- ``tools.support.*`` — shared cache, Hypothesis profiles, metrics facade

CLI:

- ``python -m tools.run_quality_gate``
- ``python -m tools.complexity_precommit``
"""
