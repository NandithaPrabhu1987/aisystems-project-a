# Langfuse Score Integration

## Overview
The evaluation harness now automatically attaches evaluation scores to Langfuse traces, enabling end-to-end observability of RAG pipeline quality.

## Implementation

### 1. Function: `attach_langfuse_scores(trace_id, metrics)`

Located in `scripts/evaluation/eval_harness.py`, this function attaches three evaluation scores to each Langfuse trace:

```python
def attach_langfuse_scores(trace_id, metrics):
    """
    Attach evaluation scores to a Langfuse trace.
    
    Args:
        trace_id: The Langfuse trace ID from the RAG pipeline
        metrics: Dict with retrieval_hit, faithfulness_score, correctness_score
    """
```

### 2. Scores Attached

For each query evaluation, the following scores are attached:

| Score Name | Type | Range | Description |
|------------|------|-------|-------------|
| **faithfulness** | Numeric | 1-5 | LLM-as-judge evaluation of answer grounding in context |
| **correctness** | Numeric | 1-5 | LLM-as-judge evaluation of answer quality vs expected answer |
| **retrieval_hit** | Binary | 0 or 1 | Whether expected source document was retrieved in top-K |

### 3. Integration Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Evaluation Pipeline                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────┐
         │  1. Load test case from dataset    │
         └────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────┐
         │  2. Run RAG pipeline (ask())       │
         │     - Creates Langfuse trace       │
         │     - Returns trace_id in result   │
         └────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────┐
         │  3. Calculate metrics              │
         │     - retrieval_hit                │
         │     - MRR                          │
         │     - judge_faithfulness()         │
         │     - judge_correctness()          │
         └────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────┐
         │  4. attach_langfuse_scores()       │
         │     - langfuse.score(faithfulness) │
         │     - langfuse.score(correctness)  │
         │     - langfuse.score(retrieval_hit)│
         │     - langfuse.flush()             │
         └────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────┐
         │  Langfuse UI shows trace + scores  │
         └────────────────────────────────────┘
```

## Code Example

```python
# In run_eval(), after scoring each query:
result = {
    "test_case": test_case,
    "rag_output": rag_result,
    "metrics": {
        "retrieval_hit": retrieval_hit,
        "mrr": mrr,
        "faithfulness_score": faithfulness['score'],
        "correctness_score": correctness['score']
    }
}

# Attach scores to Langfuse trace
if rag_result.get('trace_id'):
    attach_langfuse_scores(
        trace_id=rag_result['trace_id'],
        metrics=result['metrics']
    )
```

## Benefits

1. **End-to-End Observability**: See quality metrics alongside traces in Langfuse UI
2. **Historical Tracking**: Monitor how faithfulness/correctness evolve over time
3. **Query-Level Analysis**: Drill down to specific queries that score poorly
4. **Production Monitoring**: Can extend to attach scores to production traces
5. **Debugging**: Correlate low scores with specific retrieval/generation patterns

## Usage

Run the evaluation harness as usual:

```bash
python scripts/evaluation/eval_harness.py
```

The scores will automatically be attached to Langfuse. You can view them in the Langfuse UI at:
- Navigate to the trace
- Scores appear in the "Scores" section
- Each score shows: name, value, and comment

## Error Handling

The function includes try-except to handle Langfuse API failures gracefully:
- Prints warning if score attachment fails
- Doesn't block evaluation from continuing
- Flushes scores immediately to ensure they're sent

## Future Enhancements

Potential additions:
- **MRR score**: Could attach MRR value as well
- **Latency score**: Track answer generation speed
- **Context relevance**: Score quality of retrieved chunks
- **Production deployment**: Attach scores to live queries (sample-based)
