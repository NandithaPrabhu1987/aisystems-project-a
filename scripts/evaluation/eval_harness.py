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
from langfuse import Langfuse
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
langfuse = Langfuse()

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
    
    Args:
        retrieved_chunks: List of chunk dicts with 'doc_name' key
        expected_source: String filename like "01_return_policy.md"
    
    Returns:
        True if any chunk is from the expected source, False otherwise
    """
    for chunk in retrieved_chunks:
        if chunk.get("doc_name") == expected_source:
            return True
    return False


def calculate_mrr(retrieved_chunks, expected_source):
    """
    Mean Reciprocal Rank — how high is the first relevant chunk?
    If relevant chunk is at position 1: MRR = 1.0
    If at position 3: MRR = 0.33
    If not found: MRR = 0.0
    
    Args:
        retrieved_chunks: List of chunk dicts with 'doc_name' key
        expected_source: String filename like "01_return_policy.md"
    
    Returns:
        Float: 1/rank of first relevant chunk, or 0.0 if not found
    """
    for rank, chunk in enumerate(retrieved_chunks, start=1):
        if chunk.get("doc_name") == expected_source:
            return 1.0 / rank
    return 0.0


# =========================================================================
# GENERATION METRICS (LLM-as-Judge)
# =========================================================================

def judge_faithfulness(query, answer, context):
    """
    Is the answer grounded in the retrieved context?
    Uses GPT-4o-mini as a judge with a structured rubric.
    Returns: {"score": 1-5, "reason": "explanation"}
    
    Args:
        query: The user's question
        answer: The generated answer from the RAG system
        context: The retrieved context used to generate the answer
    
    Returns:
        Dict with 'score' (1-5) and 'reason' (explanation)
    """
    prompt = f"""You are evaluating the faithfulness of an AI assistant's answer to a question based on the provided context.

Question: {query}

Context:
{context}

Answer: {answer}

Evaluate whether the answer is faithful to the context using this rubric:

5 - Perfectly faithful: All claims in the answer are directly supported by the context
4 - Mostly faithful: Most claims are supported, minor details may be reasonable inferences
3 - Partially faithful: Some claims are supported, but there are unsupported statements
2 - Minimally faithful: Few claims are supported, significant unsupported content
1 - Not faithful: Answer contradicts context or invents information not present

Respond in JSON format:
{{"score": <1-5>, "reason": "<brief explanation>"}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return {"score": result["score"], "reason": result["reason"]}


def judge_correctness(query, answer, expected_answer):
    """
    Does the answer match the expected answer?
    Uses GPT-4o-mini as a judge.
    Returns: {"score": 1-5, "reason": "explanation"}
    
    Args:
        query: The user's question
        answer: The generated answer from the RAG system
        expected_answer: The ground truth answer from the golden dataset
    
    Returns:
        Dict with 'score' (1-5) and 'reason' (explanation)
    """
    prompt = f"""You are evaluating the correctness of an AI assistant's answer compared to a reference answer.

Question: {query}

Reference Answer (Ground Truth): {expected_answer}

Generated Answer: {answer}

Evaluate how well the generated answer matches the reference answer using this rubric:

5 - Perfect: Answers are semantically equivalent, all key information matches
4 - Good: Most key information matches, minor differences in wording or detail
3 - Acceptable: Main point is correct, but missing some important details
2 - Poor: Partially correct but has significant errors or omissions
1 - Wrong: Answer is incorrect or contradicts the reference answer

Respond in JSON format:
{{"score": <1-5>, "reason": "<brief explanation>"}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return {"score": result["score"], "reason": result["reason"]}


def attach_langfuse_scores(trace_id, metrics):
    """
    Attach evaluation scores to a Langfuse trace.
    
    Args:
        trace_id: The Langfuse trace ID from the RAG pipeline
        metrics: Dict with retrieval_hit, faithfulness_score, correctness_score
    """
    try:
        # Attach faithfulness score (1-5 scale)
        langfuse.score(
            trace_id=trace_id,
            name="faithfulness",
            value=metrics.get("faithfulness_score", 0),
            comment=f"LLM-as-judge evaluation of answer grounding in context"
        )
        
        # Attach correctness score (1-5 scale)
        langfuse.score(
            trace_id=trace_id,
            name="correctness",
            value=metrics.get("correctness_score", 0),
            comment=f"LLM-as-judge evaluation of answer quality vs expected answer"
        )
        
        # Attach retrieval hit (convert boolean to 0/1)
        langfuse.score(
            trace_id=trace_id,
            name="retrieval_hit",
            value=1 if metrics.get("retrieval_hit", False) else 0,
            comment=f"Whether expected source document was retrieved in top-K"
        )
        
        # Flush to ensure scores are sent immediately
        langfuse.flush()
        
    except Exception as e:
        print(f"Warning: Failed to attach Langfuse scores for trace {trace_id}: {e}")


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
    """
    # Import RAG pipeline
    import sys
    core_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "core"))
    sys.path.insert(0, core_path)
    from rag import ask
    
    # Load golden dataset
    dataset = load_golden_dataset()
    if not dataset:
        print("Error: No golden dataset found!")
        return
    
    print(f"\n{'='*70}")
    print(f"EVALUATION HARNESS - Running on {len(dataset)} test cases")
    print(f"{'='*70}\n")
    
    results = []
    
    # Run evaluation for each test case
    for i, test_case in enumerate(dataset, 1):
        print(f"[{i}/{len(dataset)}] Processing: {test_case['id']} - {test_case['category']}")
        print(f"  Query: {test_case['query'][:70]}...")
        
        # Run RAG pipeline
        rag_result = ask(test_case['query'])
        
        # Calculate retrieval metrics
        retrieval_hit = check_retrieval_hit(
            rag_result['retrieved_chunks'], 
            test_case['expected_source']
        )
        mrr = calculate_mrr(
            rag_result['retrieved_chunks'], 
            test_case['expected_source']
        )
        
        # Calculate generation metrics (LLM-as-judge)
        print(f"  Judging faithfulness...")
        faithfulness = judge_faithfulness(
            test_case['query'],
            rag_result['answer'],
            rag_result['context']
        )
        print(f"  Judging correctness...")
        correctness = judge_correctness(
            test_case['query'],
            rag_result['answer'],
            test_case['expected_answer']
        )
        
        # Store results
        result = {
            "test_case": test_case,
            "rag_output": rag_result,
            "metrics": {
                "retrieval_hit": retrieval_hit,
                "mrr": mrr,
                "faithfulness_score": faithfulness['score'],
                "faithfulness_reason": faithfulness['reason'],
                "correctness_score": correctness['score'],
                "correctness_reason": correctness['reason']
            }
        }
        results.append(result)
        
        # Attach scores to Langfuse trace
        if rag_result.get('trace_id'):
            attach_langfuse_scores(
                trace_id=rag_result['trace_id'],
                metrics=result['metrics']
            )
            print(f"  ✓ Scores attached to Langfuse trace: {rag_result['trace_id']}")
        
        print(f"  ✓ Hit: {retrieval_hit} | MRR: {mrr:.3f} | Faith: {faithfulness['score']}/5 | Correct: {correctness['score']}/5")
        print()
    
    # Calculate aggregate metrics
    total = len(results)
    hit_rate = sum(1 for r in results if r['metrics']['retrieval_hit']) / total
    avg_mrr = sum(r['metrics']['mrr'] for r in results) / total
    avg_faithfulness = sum(r['metrics']['faithfulness_score'] for r in results) / total
    avg_correctness = sum(r['metrics']['correctness_score'] for r in results) / total
    
    # Print scorecard
    print(f"\n{'='*70}")
    print(f"EVALUATION SCORECARD")
    print(f"{'='*70}")
    print(f"\nRetrieval Metrics:")
    print(f"  Hit Rate:          {hit_rate:.1%} ({sum(1 for r in results if r['metrics']['retrieval_hit'])}/{total})")
    print(f"  Average MRR:       {avg_mrr:.3f}")
    print(f"\nGeneration Metrics (LLM-as-Judge):")
    print(f"  Avg Faithfulness:  {avg_faithfulness:.2f}/5.0")
    print(f"  Avg Correctness:   {avg_correctness:.2f}/5.0")
    print(f"\nTest Cases: {total}")
    print(f"{'='*70}\n")
    
    # Print detailed results by category
    print("Breakdown by Category:")
    categories = {}
    for r in results:
        cat = r['test_case']['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)
    
    for cat, cat_results in sorted(categories.items()):
        cat_total = len(cat_results)
        cat_hit_rate = sum(1 for r in cat_results if r['metrics']['retrieval_hit']) / cat_total
        cat_avg_correct = sum(r['metrics']['correctness_score'] for r in cat_results) / cat_total
        print(f"  {cat:15s}: Hit={cat_hit_rate:.1%}, Correctness={cat_avg_correct:.1f}/5")
    
    print(f"\n{'='*70}\n")
    
    return results


if __name__ == "__main__":
    print("="*70)
    print("RAG EVALUATION HARNESS")
    print("="*70)
    run_eval()
