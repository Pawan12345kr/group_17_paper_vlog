# ILearner-LLM with Google Gemini Pro

This project implements the **ILearner-LLM** framework from the AAAI 2025 paper:
> **"Exploring Iterative Enhancement for Improving Learnersourced Multiple-Choice Question Explanations with Large Language Models"**  
> *Strong AI Lab (University of Auckland)*

Instead of relying on multi-GPU setups (8x A100s) and outdated HuggingFace checkpoints, this implementation uses **Google Gemini Pro** via the modern `google-genai` SDK for high-speed, cost-effective, and pedagogical iterative explanation generation and verification.

---

## Architecture Overview

```
                        +----------------------------+
                        | Multiple-Choice Question   |
                        | (Stem, Choices, Answer)    |
                        +--------------+-------------+
                                       |
                                       v
                    +------------------------------------+
                    |        Explanation Generator       |
                    |            (Gemini Pro)            |
                    +------------------+-----------------+
                                       |
                                       | Candidate Explanation
                                       v
                    +------------------------------------+
                    |        Explanation Verifier        |
                    |   (Scores quality: 1.0 to 5.0)     |
                    +------------------+-----------------+
                                       |
                        +---------------+---------------+
                        |                               |
               Score < Threshold               Score >= Threshold
                        |                               |
                        v                               v
          [Refinement Feedback Loop]        [Accepted Final Explanation]
     Feeds previous score & text back
        into Generator for next round
```

---

## Quick Setup in VS Code

### 1. Add your Gemini API Key
Open `.env` in VS Code and paste your key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
```

### 2. Activate Virtual Environment
Open the VS Code Terminal (`Ctrl + ~`) and activate the pre-configured virtual environment:
```powershell
.\venv\Scripts\Activate.ps1
```

---

## How to Run

### Option 1: Terminal Slide Presentation Mode
```powershell
.\venv\Scripts\python.exe terminal_presentation.py
```

### Option 2: Interactive MCQ Session
```powershell
.\venv\Scripts\python.exe interactive_chat_gemini.py
```

### Option 3: Run Batch Evaluation on Datasets
```powershell
.\venv\Scripts\python.exe batch_evaluator_gemini.py --data sample_mcq_dataset.json --threshold 4.5 --max_rounds 3
```

---

## File Structure

* `terminal_presentation.py`: Slide-by-slide terminal presentation script for demos.
* `ilearner_gemini.py`: Core ILearner-LLM engine containing the Generator, Verifier (Way 2), and Iterative Enhancement loop.
* `interactive_chat_gemini.py`: Interactive CLI with formatted panels and demo questions.
* `batch_evaluator_gemini.py`: Batch evaluation script with automated metrics and summary reporting.
* `sample_mcq_dataset.json`: Ready-to-use sample dataset with questions from CS, Biology, Chemistry, Physics, and Economics.
* `ILearner_LLM_10Min_Presentation_Guide.pdf`: 7-page academic presentation and defense guide.
* `.env`: Stores your `GEMINI_API_KEY`.
