

import os
import sys
from ilearner_gemini import ILearnerGemini
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm

console = Console()


def get_preset_samples():
    return [
        {
            "question": "What happens during the synthesis (S) phase of the eukaryotic cell cycle?",
            "options": {
                "A": "The cell doubles in size and produces ribosomes.",
                "B": "Nuclear division occurs via mitosis.",
                "C": "DNA replication takes place, duplicating the chromosomes.",
                "D": "The nuclear membrane breaks down."
            },
            "answer": "C"
        },
        {
            "question": "Which data structure uses LIFO (Last In First Out) ordering?",
            "options": {
                "A": "Queue",
                "B": "Stack",
                "C": "Linked List",
                "D": "Binary Search Tree"
            },
            "answer": "B"
        }
    ]


def interactive_session():
    console.print(Panel.fit(
        "[bold cyan]ILearner-LLM: Iterative Explanation Enhancement[/bold cyan]\n",
        
        border_style="cyan"
    ))

    try:
        engine = ILearnerGemini()
    except Exception as e:
        console.print(f"[bold red]Initialization Error:[/bold red] {e}")
        console.print("[yellow]Tip: Please set your GEMINI_API_KEY in the `.env` file first![/yellow]")
        sys.exit(1)

    while True:
        console.print("\n[bold green]Choose an option:[/bold green]")
        console.print("  [1] Enter a custom Multiple-Choice Question (MCQ)")
        console.print("  [2] Run a preloaded demo question")
        console.print("  [3] Exit")

        choice = Prompt.ask("Select", choices=["1", "2", "3"], default="1")

        if choice == "3":
            console.print("[bold yellow]Goodbye![/bold yellow]")
            break

        if choice == "2":
            samples = get_preset_samples()
            console.print("\n[bold]Select a demo sample:[/bold]")
            for idx, s in enumerate(samples, 1):
                console.print(f"  [{idx}] {s['question']}")
            sample_idx = int(Prompt.ask("Choose sample", choices=[str(i) for i in range(1, len(samples) + 1)])) - 1
            selected = samples[sample_idx]
            question = selected["question"]
            options = selected["options"]
            answer = selected["answer"]
        else:
            console.print("\n[bold cyan]--- Enter Question Details ---[/bold cyan]")
            question = Prompt.ask("Question text")
            num_options = int(Prompt.ask("Number of options (2 to 5)", choices=["2", "3", "4", "5"], default="4"))
            options = {}
            for i in range(num_options):
                opt_key = chr(ord('A') + i)
                options[opt_key] = Prompt.ask(f"Option {opt_key}")

            allowed_answers = [chr(ord('A') + i) for i in range(num_options)]
            answer = Prompt.ask("Correct Option", choices=allowed_answers).upper()

        threshold = float(Prompt.ask("Quality threshold score (1.0 to 5.0)", default="4.0"))
        max_rounds = int(Prompt.ask("Max enhancement rounds", default="3"))

        console.print("\n[bold green]Running iterative generation & verification...[/bold green]\n")
        result = engine.run_enhancement_loop(
            question=question,
            options=options,
            answer=answer,
            threshold=threshold,
            max_iterations=max_rounds,
            verbose=True
        )

        console.print(Panel(
            Markdown(f"### Final Explanation\n\n{result['final_explanation']}\n\n"
                     f"**Final Verifier Score:** {result['final_score']:.2f}/5.0 "
                     f"({'✅ Threshold Met' if result['threshold_reached'] else '⚠️ Max rounds reached'})\n"
                     f"**Rounds needed:** {result['rounds_run']}"),
            title="🎯 Final Result",
            border_style="green" if result['threshold_reached'] else "yellow"
        ))

        if not Confirm.ask("\nWould you like to analyze another question?", default=True):
            console.print("[bold cyan]Session completed. Thank you![/bold cyan]")
            break


if __name__ == "__main__":
    try:
        interactive_session()
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Session stopped by user (Ctrl+C). Goodbye![/bold yellow]\n")
