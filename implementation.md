# Phase 74 — Multi-Model Comparison: Sonnet vs Haiku Extraction

**Version:** 1.1 | **Tier:** Micro | **Date:** 2026-03-28

## Goal
Compare Claude Haiku vs Sonnet on structured compound data extraction. Same prompt, same data, different models. Measure accuracy, latency, token usage, and cost.

CLI: `python main.py --input data/compounds.csv --n 3`

Outputs: model_comparison.json, model_comparison_report.txt

## Logic
1. Select 3 test compounds with known properties
2. For each model (haiku, sonnet), send extraction prompt asking for name, activity_class, pic50_estimate, scaffold_family
3. Compare extracted values against ground truth
4. Report accuracy, latency, tokens, cost per model

## Key Concepts
- Model benchmarking on identical tasks
- Cost/quality tradeoff analysis
- Structured extraction accuracy comparison
- Haiku (claude-haiku-4-5-20251001) vs Sonnet (claude-sonnet-4-20250514)

## Verification Checklist
- [x] Both models called with identical prompts
- [x] 3 compounds x 2 models = 6 API calls
- [x] Accuracy comparison table
- [x] Cost comparison
- [x] --help works

## Results
| Metric | Haiku | Sonnet |
|--------|-------|--------|
| Class accuracy | 100% | 100% |
| Family accuracy | 100% | 100% |
| Input tokens | 595 | 595 |
| Output tokens | 185 | 170 |
| Avg latency | 0.81s | 1.83s |
| Cost | $0.0012 | $0.0043 |
| Cost ratio | 1.0x | 3.6x |

Key findings:
- Both models achieved 100% accuracy on this simple extraction task
- Haiku is 2.3x faster and 3.6x cheaper than Sonnet
- For straightforward structured extraction, Haiku is the clear winner
- Sonnet's extra capability provides no benefit here — reserve for complex reasoning tasks

## Risks
- Sonnet overkill confirmed: same accuracy, higher cost, higher latency
- Task may be too simple to differentiate — complex extraction would show bigger delta
