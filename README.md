# Group 17 Paper Vlog: ILearner-LLM with Google Gemini Pro

This repository contains the **Group 17 Paper Vlog** presentation, custom evaluation example, and implementation of the **ILearner-LLM** framework from the AAAI 2025 paper:

> **"Exploring Iterative Enhancement for Improving Learnersourced Multiple-Choice Question Explanations with Large Language Models"**  
> *Strong AI Lab (University of Auckland)*

Instead of relying on multi-GPU setups (8x A100s) and outdated HuggingFace checkpoints, this implementation uses **Google Gemini Pro** via the modern `google-genai` SDK for high-speed, cost-effective, and pedagogical iterative explanation generation and verification.

---

## Architecture Overview

```text
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

## Repository File Structure

```text
Group_17_paper_vlog/
├── README.md                                           # Project documentation and setup guide
├── custom question and GITHUB LINK.txt                 # Sample custom MCQ input, threshold setting, and repo link
├── video/
│   └── group_17_paper_vlog.mp4                         # Group 17 Paper Vlog video presentation
└── code_folder/
    ├── .env.example                                    # Template for configuring GEMINI_API_KEY and GEMINI_MODEL
    ├── requirements.txt                                # Python package dependencies
    ├── ilearner_gemini.py                              # Core ILearner-LLM engine (Generator, Verifier Way 2, Iterative Loop)
    ├── interactive_chat_gemini.py                      # Interactive CLI for testing custom and preset MCQs
    ├── batch_evaluator_gemini.py                       # Automated batch evaluation and metrics script using Gemini
    ├── terminal_presentation.py                        # Slide-by-slide interactive terminal presentation script
    ├── sample_mcq_dataset.json                         # Sample MCQ dataset (CS, Biology, Chemistry, Physics, Economics)
    ├── eval_results_gemini.json                        # Saved evaluation output and scoring metrics from Gemini runs
    ├── alpaca_data.json                                # Stanford Alpaca instruction-following dataset
    ├── train.py                                        # Original LLaMA fine-tuning script
    ├── training_script.sh                              # Shell script for distributed model training and evaluation
    ├── utils.py                                        # Helper functions for data loading and tokenization
    ├── chat.py                                         # Base LLaMA interactive chat script
    ├── chat_generator.py                               # LLaMA-based candidate explanation generator
    ├── chat_verifier_way2.py                           # LLaMA-based explanation quality verifier (Way 2)
    ├── chat_explanation_verifier_way2.py               # Combined LLaMA explanation generation & verification pipeline
    ├── batch_evaluation_Cardiff.py                     # Batch evaluation script for the Cardiff dataset
    ├── batch_evaluation_Sydney.py                      # Batch evaluation script for the Sydney dataset
    ├── batch_evaluation_biology_law_psychology.py      # Batch evaluation script for Biology, Law, and Psychology datasets
    ├── data_preprocessing_generator.py                 # Data preprocessing pipeline for the explanation generator
    ├── data_preprocessing_generator_one_dataset.py     # Single-dataset preprocessing for the generator
    ├── data_preprocess_generator_one_dataset_sydney.py # Sydney dataset preprocessing for the generator
    ├── data_preprocessing_verifier_way2.py             # Data preprocessing pipeline for the Way 2 verifier
    ├── bleu_score_calculator.py                        # BLEU score evaluation utility
    ├── json_metric_calculator.py                       # JSON evaluation metric aggregation utility
    ├── explanation_average_length.py                   # Calculates average explanation length across outputs
    ├── explanation_average_length_sydney.py            # Calculates average explanation length for Sydney dataset
    ├── gpt-4_script.py                                 # Baseline evaluation script using OpenAI GPT-4
    ├── merge_model_results.py                          # Utility to merge evaluation outputs across models
    ├── random_sample_selection.py                      # Utility for random subset sampling of MCQ datasets
    ├── unicode_regenerate_explanation.py               # Utility for cleaning and regenerating Unicode explanations
    └── llama/                                          # Base LLaMA model package
        ├── __init__.py
        ├── generation.py                               # Text generation and sampling routines
        ├── model.py                                    # Transformer architecture implementation
        └── tokenizer.py                                # SentencePiece tokenizer wrapper
```

---

## Quick Setup in VS Code

### 1. Navigate to the Code Directory
Open the terminal (`Ctrl + ~`) and move into `code_folder`:
```powershell
cd code_folder
```

### 2. Configure Your Gemini API Key
Create a `.env` file inside `code_folder` (or copy `.env.example` to `.env`) and add your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-pro
```

### 3. Create & Activate Virtual Environment and Install Dependencies
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## How to Run

Make sure you are inside the `code_folder` directory (`cd code_folder`):

### Option 1: Terminal Slide Presentation Mode
```powershell
.\venv\Scripts\python.exe terminal_presentation.py
```

### Option 2: Interactive MCQ Session
```powershell
.\venv\Scripts\python.exe interactive_chat_gemini.py
```
> **Tip:** See `custom question and GITHUB LINK.txt` in the root folder for a ready-to-use custom Biology MCQ prompt and recommended threshold (`3.2` or above).

### Option 3: Run Batch Evaluation on Datasets
```powershell
.\venv\Scripts\python.exe batch_evaluator_gemini.py --data sample_mcq_dataset.json --threshold 4.5 --max_rounds 3
```
