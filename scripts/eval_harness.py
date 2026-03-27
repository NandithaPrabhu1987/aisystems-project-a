"""
Evaluation Harness — Session 1 Starter

This is a SKELETON. During Session 1, we'll build each function
from scratch to create a complete eval pipeline.

Functions to implement:
  1. check_retrieval_hit() — is the expected source in the top-K results?
  2. calculate_mrr() — how high is the first relevant chunk ranked?
  3. judge_faithfulness() — is the answer grounded in the context? (LLM-as-judge)
  4. judge_correctness() — does the answer match the expected answer? (LLM-as-judge)
  5. run_eval() — orchestrate everything and produce a scorecard

Run: python scripts/eval_harness.py
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

SCRIPT_DIR = os.path.dirname(__file__)


# =========================================================================
# GOLDEN DATASET
# =========================================================================
# TODO: We'll build this together in Session 1.
# Start with 5 hand-written question-answer-context triples.
# Format:
# {
#     "id": "q01",
#     "query": "What is the standard return window?",
#     "expected_answer": "30 calendar days from delivery date.",
#     "expected_source": "01_return_policy.md",
#     "difficulty": "easy",
#     "category": "returns"
# }
# =========================================================================


def load_golden_dataset():
    """Load the golden dataset from JSON file."""
    path = os.path.join(SCRIPT_DIR, "golden_dataset.json")
    if not os.path.exists(path):
        print("No golden_dataset.json found. Create one first!")
        return []
    with open(path) as f:
        return json.loads(f.read())


# =========================================================================
# RETRIEVAL METRICS
# =========================================================================

def check_retrieval_hit(retrieved_chunks, expected_source):
    """
    Is the expected source document in the retrieved chunks?
    Returns True/False.

    TODO: Implement this in Session 1.
    """
    pass


def calculate_mrr(retrieved_chunks, expected_source):
    """
    Mean Reciprocal Rank — how high is the first relevant chunk?
    If relevant chunk is at position 1: MRR = 1.0
    If at position 3: MRR = 0.33
    If not found: MRR = 0.0

    TODO: Implement this in Session 1.
    """
    pass


# =========================================================================
# GENERATION METRICS (LLM-as-Judge)
# =========================================================================

def judge_faithfulness(query, answer, context):
    """
    Is the answer grounded in the retrieved context?
    Uses GPT-4o-mini as a judge with a structured rubric.
    Returns: {"score": 1-5, "reason": "explanation"}

    TODO: Implement this in Session 1.
    """
    pass


def judge_correctness(query, answer, expected_answer):
    """
    Does the answer match the expected answer?
    Uses GPT-4o-mini as a judge.
    Returns: {"score": 1-5, "reason": "explanation"}

    TODO: Implement this in Session 1.
    """
    pass


# =========================================================================
# EVAL RUNNER
# =========================================================================

def run_eval():
    """
    Run the full evaluation:
    1. Load golden dataset
    2. Run each query through the RAG pipeline
    3. Score retrieval (hit rate, MRR)
    4. Score generation (faithfulness, correctness)
    5. Print scorecard

    TODO: Implement this in Session 1.
    """
    pass


if __name__ == "__main__":
    print("Eval harness skeleton loaded.")
    print("Functions to implement: check_retrieval_hit, calculate_mrr,")
    print("judge_faithfulness, judge_correctness, run_eval")
    print("\nWe'll build these together in Session 1.")
