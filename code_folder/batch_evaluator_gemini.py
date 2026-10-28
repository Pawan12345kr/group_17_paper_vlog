"""
Batch Evaluation Script for ILearner-LLM with Google Gemini.
Replaces `batch_evaluation_Cardiff.py` and `gpt-4_script.py`.
Evaluates an entire dataset of MCQs and logs before-and-after improvement metrics.
"""

import os
import json
import argparse
from tqdm import tqdm
from ilearner_gemini import ILearnerGemini
from rich.console import Console
from rich.table import Table

console = Console()


def simple_token_overlap(hyp: str, ref: str) -> float:
    """Calculates word overlap F1 between generated explanation and reference."""
    if not ref:
        return 0.0
    hyp_words = set(hyp.lower().split())
    ref_words = set(ref.lower().split())
    if not hyp_words or not ref_words:
        return 0.0
    intersection = hyp_words.intersection(ref_words)
    precision = len(intersection) / len(hyp_words)
    recall = len(intersection) / len(ref_words)
    if precision + recall == 0:
        return 0.0
    return (2 * precision * recall) / (precision + recall)


def run_batch_evaluation(
    dataset_path: str = "sample_mcq_dataset.json",
    output_path: str = "eval_results_gemini.json",
    threshold: float = 4.0,
    max_rounds: int = 3,
    sample_limit: int = 10,
):
    console.print(f"[bold cyan]Starting Batch Evaluation on:[/bold cyan] {dataset_path}")

    if not os.path.exists(dataset_path):
        console.print(f"[bold red]Dataset not found:[/bold red] {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if sample_limit and len(data) > sample_limit:
        data = data[:sample_limit]
        console.print(f"[dim]Evaluating first {sample_limit} items...[/dim]")

    engine = ILearnerGemini()
    results = []

    total_initial_score = 0.0
    total_final_score = 0.0

    for idx, item in enumerate(tqdm(data, desc="Evaluating MCQs")):
        question = item.get("question", "")
        answer = item.get("answer", "")
        ground_truth = item.get("ground_truth_explanation", "")

        # Collect options
        options = {}
        for k in ["A", "B", "C", "D", "E"]:
            alt_key = f"alt{k}"
            if alt_key in item and item[alt_key]:
                options[k] = item[alt_key]
            elif f"Option {k}" in item:
                options[k] = item[f"Option {k}"]

        res = engine.run_enhancement_loop(
            question=question,
            options=options,
            answer=answer,
            threshold=threshold,
            max_iterations=max_rounds,
            verbose=False,
        )

        initial_round = res["history"][0]
        final_round = res["history"][-1]

        initial_score = initial_round["score"]
        final_score = final_round["score"]
        score_gain = final_score - initial_score

        initial_overlap = simple_token_overlap(initial_round["explanation"], ground_truth)
        final_overlap = simple_token_overlap(final_round["explanation"], ground_truth)

        record = {
            "id": item.get("id", idx + 1),
            "subject": item.get("subject", "General"),
            "question": question,
            "answer": answer,
            "rounds_run": res["rounds_run"],
            "threshold_reached": res["threshold_reached"],
            "initial_score": initial_score,
            "final_score": final_score,
            "score_gain": score_gain,
            "initial_explanation": initial_round["explanation"],
            "final_explanation": final_round["explanation"],
            "ground_truth_explanation": ground_truth,
            "initial_overlap_f1": round(initial_overlap, 4),
            "final_overlap_f1": round(final_overlap, 4),
            "history": res["history"],
        }
        results.append(record)
        total_initial_score += initial_score
        total_final_score += final_score

    # Save output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    avg_init = total_initial_score / len(results) if results else 0.0
    avg_final = total_final_score / len(results) if results else 0.0
    avg_gain = avg_final - avg_init

    # Display summary table
    table = Table(title="Batch Evaluation Results (ILearner-LLM + Gemini Pro)")
    table.add_column("ID", style="cyan", justify="center")
    table.add_column("Subject", style="magenta")
    table.add_column("Rounds", justify="center")
    table.add_column("Init Score", justify="center")
    table.add_column("Final Score", justify="center")
    table.add_column("Gain", justify="center", style="green")

    for r in results:
        table.add_row(
            str(r["id"]),
            r["subject"],
            str(r["rounds_run"]),
            f"{r['initial_score']:.2f}",
            f"{r['final_score']:.2f}",
            f"+{r['score_gain']:.2f}" if r["score_gain"] >= 0 else f"{r['score_gain']:.2f}",
        )

    console.print(table)
    console.print(f"\n[bold green]Summary Statistics:[/bold green]")
    console.print(f"  • Average Initial Verifier Score: [bold]{avg_init:.2f}[/bold] / 5.0")
    console.print(f"  • Average Final Verifier Score:   [bold]{avg_final:.2f}[/bold] / 5.0")
    console.print(f"  • Average Quality Improvement:   [bold green]+{avg_gain:.2f}[/bold green]")
    console.print(f"\nSaved detailed evaluation log to: [bold]{output_path}[/bold]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="sample_mcq_dataset.json", help="Path to MCQ dataset JSON")
    parser.add_argument("--out", default="eval_results_gemini.json", help="Output path for evaluation log")
    parser.add_argument("--threshold", type=float, default=4.0, help="Quality threshold score")
    parser.add_argument("--max_rounds", type=int, default=3, help="Max iterations per MCQ")
    parser.add_argument("--limit", type=int, default=10, help="Max questions to evaluate")
    args = parser.parse_args()

    run_batch_evaluation(
        dataset_path=args.data,
        output_path=args.out,
        threshold=args.threshold,
        max_rounds=args.max_rounds,
        sample_limit=args.limit,
    )
