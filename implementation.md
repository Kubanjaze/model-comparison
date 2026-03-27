# Phase 74 — Multi-Model Comparison: Sonnet vs Haiku Extraction

**Version:** 1.0 | **Tier:** Micro | **Date:** 2026-03-28

## Goal
Compare Claude Haiku vs Sonnet on structured compound data extraction. Same prompt, same data, different models. Measure accuracy, latency, token usage, and cost.

CLI: `python main.py --input data/compounds.csv --n 3`

Outputs: model_comparison.json, model_comparison_report.txt

## Logic
1. Select 3 test compounds with known properties
2. For each model (haiku, sonnet), send extraction prompt asking for name, SMILES, pIC50, activity_class
3. Compare extracted values against ground truth
4. Report accuracy, latency, tokens, cost per model

## Key Concepts
- Model benchmarking on identical tasks
- Cost/quality tradeoff analysis
- Structured extraction accuracy comparison
- Haiku (claude-haiku-4-5-20251001) vs Sonnet (claude-sonnet-4-20250514)

## Verification Checklist
- [ ] Both models called with identical prompts
- [ ] 3 compounds x 2 models = 6 API calls
- [ ] Accuracy comparison table
- [ ] Cost comparison
- [ ] --help works

## Risks
- Sonnet may be overkill for simple extraction (higher cost, same accuracy)
- Rate limits if both called rapidly — sequential calls mitigate
