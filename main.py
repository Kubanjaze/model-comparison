import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse, os, json, re, time, warnings
warnings.filterwarnings("ignore")
import pandas as pd
from dotenv import load_dotenv
import anthropic

load_dotenv()
os.environ.setdefault("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))

MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-20250514",
}

# Haiku: $0.80/M in, $4/M out; Sonnet: $3/M in, $15/M out
PRICING = {
    "haiku": {"input": 0.80, "output": 4.0},
    "sonnet": {"input": 3.0, "output": 15.0},
}

EXTRACT_PROMPT = """Extract the following fields from this compound record. Respond with ONLY valid JSON:
{
  "compound_name": "<name>",
  "activity_class": "inactive|weak|moderate|potent|highly_potent",
  "pic50_estimate": <float>,
  "scaffold_family": "<family>"
}

Activity classes: inactive (pIC50<5), weak (5-6), moderate (6-7), potent (7-8), highly_potent (>=8).
Scaffold family: first part of compound name before underscore (e.g., benz, ind, naph, quin, pyr, bzim)."""


def pic50_to_class(pic50: float) -> str:
    if pic50 < 5.0:   return "inactive"
    elif pic50 < 6.0: return "weak"
    elif pic50 < 7.0: return "moderate"
    elif pic50 < 8.0: return "potent"
    else:             return "highly_potent"


def main():
    parser = argparse.ArgumentParser(
        description="Phase 74 — Multi-model comparison: Sonnet vs Haiku extraction",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Compounds CSV")
    parser.add_argument("--n", type=int, default=3, help="Number of test compounds")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    df = pd.read_csv(args.input).head(args.n)
    client = anthropic.Anthropic()

    print(f"\nPhase 74 — Multi-Model Comparison")
    print(f"Compounds: {len(df)} | Models: {list(MODELS.keys())}\n")

    all_results = {}

    for model_label, model_id in MODELS.items():
        print(f"--- {model_label.upper()} ({model_id}) ---")
        results = []
        total_in = 0
        total_out = 0
        total_time = 0.0

        for _, row in df.iterrows():
            user_msg = (
                f"{EXTRACT_PROMPT}\n\n"
                f"Compound: {row['compound_name']}, SMILES: {row['smiles']}, pIC50: {row['pic50']:.2f}"
            )

            t0 = time.time()
            response = client.messages.create(
                model=model_id,
                max_tokens=256,
                messages=[{"role": "user", "content": user_msg}],
            )
            elapsed = time.time() - t0

            text = "".join(b.text for b in response.content if hasattr(b, "text"))
            total_in += response.usage.input_tokens
            total_out += response.usage.output_tokens
            total_time += elapsed

            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                parsed = {"parse_error": True, "raw": text}

            true_class = pic50_to_class(row["pic50"])
            true_family = row["compound_name"].split("_")[0]
            pred_class = parsed.get("activity_class", "?")
            pred_family = parsed.get("scaffold_family", "?")

            correct_class = pred_class == true_class
            correct_family = pred_family == true_family

            print(f"  {row['compound_name']:20s} class={'OK' if correct_class else 'MISS':4s} "
                  f"family={'OK' if correct_family else 'MISS':4s} {elapsed:.2f}s")

            results.append({
                "compound": row["compound_name"],
                "true_class": true_class,
                "pred_class": pred_class,
                "correct_class": correct_class,
                "true_family": true_family,
                "pred_family": pred_family,
                "correct_family": correct_family,
                "latency_s": round(elapsed, 3),
            })

        pricing = PRICING[model_label]
        cost = (total_in / 1e6 * pricing["input"]) + (total_out / 1e6 * pricing["output"])
        class_acc = sum(1 for r in results if r["correct_class"]) / len(results)
        family_acc = sum(1 for r in results if r["correct_family"]) / len(results)

        all_results[model_label] = {
            "model_id": model_id,
            "results": results,
            "class_accuracy": class_acc,
            "family_accuracy": family_acc,
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "total_latency_s": round(total_time, 3),
            "avg_latency_s": round(total_time / len(results), 3),
            "cost_usd": round(cost, 6),
        }
        print(f"  Accuracy: class={class_acc:.0%} family={family_acc:.0%} | "
              f"Cost: ${cost:.4f} | Avg latency: {total_time/len(results):.2f}s\n")

    # Summary report
    report = f"Phase 74 — Multi-Model Comparison\n{'='*50}\n\n"
    report += f"{'Metric':<25s} {'Haiku':<15s} {'Sonnet':<15s}\n"
    report += f"{'-'*55}\n"
    for metric in ["class_accuracy", "family_accuracy", "total_input_tokens", "total_output_tokens",
                    "avg_latency_s", "cost_usd"]:
        h_val = all_results["haiku"][metric]
        s_val = all_results["sonnet"][metric]
        if isinstance(h_val, float) and metric.endswith("accuracy"):
            report += f"{metric:<25s} {h_val:<15.0%} {s_val:<15.0%}\n"
        else:
            report += f"{metric:<25s} {str(h_val):<15s} {str(s_val):<15s}\n"
    report += f"\nCost ratio (Sonnet/Haiku): {all_results['sonnet']['cost_usd']/max(all_results['haiku']['cost_usd'],1e-9):.1f}x\n"
    print(report)

    with open(os.path.join(args.output_dir, "model_comparison.json"), "w") as f:
        json.dump(all_results, f, indent=2)
    with open(os.path.join(args.output_dir, "model_comparison_report.txt"), "w") as f:
        f.write(report)
    print("Done.")


if __name__ == "__main__":
    main()
