"""
ILearner-LLM Implementation powered by Google Gemini API.
Paper: "Exploring Iterative Enhancement for Improving Learnersourced Multiple-Choice
Question Explanations with Large Language Models" (AAAI 2025).
Original authors: Strong-AI-Lab (University of Auckland).
"""

import os
import re
import sys
import time

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env
load_dotenv()


class ILearnerGemini:
    """
    ILearner-LLM Engine:
    - Generator: produces candidate educational explanations for MCQs.
    - Verifier: scores explanations on educational quality (1.0 - 5.0).
    - Iterative Loop: refines candidate explanations if score is below threshold.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        raw_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.api_key = raw_key.strip()
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please set it in your .env file or pass it to ILearnerGemini(api_key=...)."
            )

        self.model_name = (model_name or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")).strip()
        self.client = genai.Client(api_key=self.api_key)

    def _call_gemini(
        self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048
    ) -> str:
        """Helper to invoke Gemini API with automatic cooldown, fallback, and retry."""
        candidate_models = [self.model_name]
        for m in ["gemini-3.8-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"]:
            if m not in candidate_models:
                candidate_models.append(m)

        last_error = None
        for model in candidate_models:
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                        ),
                    )
                    return response.text.strip() if response.text else ""
                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str or "rate" in err_str:
                        print(f"  [API Cooldown] Rate limit reached on '{model}'. Waiting 3s to respect free quota...")
                        time.sleep(3)
                    elif "404" in err_str or "not found" in err_str:
                        # Model not available in this region/key, move to next model
                        break
                    else:
                        time.sleep(1)

        raise RuntimeError(f"Gemini API generation failed across models: {last_error}")

    @staticmethod
    def format_mcq_input(
        question: str,
        options: Dict[str, str],
        answer: str,
    ) -> str:
        """
        Formats question, options (A..E), and correct answer into the exact
        string structure used by the paper's data preprocessing.
        """
        prompt = f"Given question: {question.strip()}"
        for opt_key in sorted(options.keys()):
            prompt += f" Option {opt_key}: {options[opt_key].strip()}"
        prompt += f" The correct answer is Option {answer.strip().upper()}."
        return prompt

    def generate_explanation(
        self,
        mcq_input_str: str,
        step: int = 0,
        prev_explanation: Optional[str] = None,
        prev_score: Optional[float] = None,
    ) -> str:
        """
        Generator step:
        - Step 0: Generates initial explanation.
        - Step > 0: Feeds previous rating score and previous explanation back
          into the prompt for iterative refinement (as formulated in ILearner-LLM).
        """
        if step == 0 or prev_explanation is None:
            full_prompt = (
                "Instruction: As an explanation generation expert, can you generate the explanation for the given input? "
                "Provide an accurate, pedagogical explanation explaining clearly why the correct option is right "
                "and why each alternative option is wrong.\n\n"
                f"Input: {mcq_input_str}\n\n"
                "Output: "
            )
        else:
            full_prompt = (
                f"Instruction: Your last time verifier rating score for your explanation generation was {prev_score:.2f} "
                f"and the explanation you generated was: '{prev_explanation}'. "
                "As an explanation generation expert, can you generate a better, more educational, and clearer explanation for the given input? "
                "Address any gaps, clarify reasoning, and ensure every choice is adequately addressed.\n\n"
                f"Input: {mcq_input_str}\n\n"
                "Output: "
            )

        explanation = self._call_gemini(full_prompt, temperature=0.6, max_tokens=2048)
        return explanation

    def verify_explanation(
        self,
        mcq_input_str: str,
        explanation: str,
    ) -> Tuple[float, str]:
        """
        Verifier step (Way 2 from paper):
        Inputs the question stem, choices, answer, and the generated explanation,
        evaluating it on a scale of 1.0 to 5.0.
        """
        full_prompt = (
            "Instruction: As a question rating verifier expert, evaluate the quality of the explanation provided for the multiple-choice question. "
            "Rate it on a continuous scale from 1.0 to 5.0, where:\n"
            "- 1.0 - 2.0: Poor, incorrect, or lacks meaningful explanation.\n"
            "- 3.0: Acceptable, states the answer but has superficial reasoning.\n"
            "- 4.0 - 5.0: Excellent, insightful, pedagogically clear, explaining both correct and incorrect options.\n\n"
            f"Input: {mcq_input_str} Explanation: {explanation}\n\n"
            "Output your evaluation strictly in this format:\n"
            "Feedback: <brief 1-2 sentence feedback on strengths and weaknesses>\n"
            "Rating: <number between 1.0 and 5.0>"
        )

        raw_verdict = self._call_gemini(full_prompt, temperature=0.1, max_tokens=256)

        # Extract numeric rating
        match = re.search(r"Rating:\s*([0-5](?:\.\d+)?)", raw_verdict, re.IGNORECASE)
        if not match:
            # Fallback search for any floating point / integer
            match = re.search(r"\b([1-5](?:\.\d+)?)\b", raw_verdict)

        try:
            score = float(match.group(1)) if match else 3.0
            score = max(1.0, min(5.0, score))
        except Exception:
            score = 3.0

        return score, raw_verdict

    def run_enhancement_loop(
        self,
        question: str,
        options: Dict[str, str],
        answer: str,
        threshold: float = 4.0,
        max_iterations: int = 3,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes the iterative enhancement loop for a single MCQ until
        verifier score >= threshold or max_iterations reached.
        """
        mcq_input_str = self.format_mcq_input(question, options, answer)
        history = []
        explanation = None
        score = 0.0
        feedback = ""

        if verbose:
            print("=" * 70)
            print("[ILearner-LLM] Enhancement Pipeline (Google Gemini Pro)")
            print("=" * 70)
            print(f"Target Quality Threshold: {threshold}/5.0 | Max Rounds: {max_iterations}\n")

        for step in range(max_iterations):
            round_num = step + 1
            if verbose:
                print(f"--- [Round {round_num}/{max_iterations}] ---")
                print("[Generator] Crafting explanation...")

            explanation = self.generate_explanation(
                mcq_input_str=mcq_input_str,
                step=step,
                prev_explanation=explanation,
                prev_score=score,
            )

            # Polite pause to avoid bursting the Gemini Free Tier RPM limits
            time.sleep(1.5)

            if verbose:
                print("[Verifier] Scoring explanation...")

            score, raw_eval = self.verify_explanation(mcq_input_str, explanation)

            history.append({
                "round": round_num,
                "explanation": explanation,
                "score": score,
                "verifier_feedback": raw_eval,
            })

            if verbose:
                print(f"\n[Generated Explanation]:\n{explanation}\n")
                print(f"[Verifier Rating Score]: {score:.2f} / 5.0")
                print(f"[Verifier Assessment]:\n{raw_eval}\n")

            if score >= threshold:
                if verbose:
                    print(f"[SUCCESS] Quality threshold reached! Explanation accepted at Round {round_num}.\n")
                break
            else:
                if verbose and round_num < max_iterations:
                    print(f"[Refinement] Score {score:.2f} is below target {threshold}. Initiating next round...\n")

        return {
            "question": question,
            "options": options,
            "correct_answer": answer,
            "final_explanation": explanation,
            "final_score": score,
            "threshold": threshold,
            "threshold_reached": score >= threshold,
            "rounds_run": len(history),
            "history": history,
        }
