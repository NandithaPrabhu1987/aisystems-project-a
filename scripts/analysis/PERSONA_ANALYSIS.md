# Persona-Based Question Generation & Evaluation

## Overview
Generated and evaluated questions using 3 different customer personas to test RAG system robustness.

## Test Setup
- **Documents**: 2 corpus files
  - `07_promotional_events.md` 
  - `02_premium_membership.md`
- **Personas**: 3 types
- **Questions per persona**: 6 total (3 per document)
- **Model**: GPT-4o-mini at temperature 0.8

## Personas

### 1. STANDARD Persona 🟢
**Characteristics**:
- Clear, straightforward questions
- Directly answerable from source document
- Polite, neutral language
- Realistic customer queries

**Example**:
> "What types of promotional events does Acmera offer throughout the year?"

**Expected Performance**: **HIGHEST**
- Hit Rate: ~100%
- MRR: ~0.95
- Correctness: ~4.5/5
- Faithfulness: ~5/5

---

### 2. FRUSTRATED Persona 🟡
**Characteristics**:
- Complex, multi-part questions
- Emotional/urgent language
- References edge cases
- May combine multiple concerns in one question

**Example**:
> "I bought a bunch of items during your Diwali Dhamaka sale, but now I see that some are marked as 'Final Sale' and can't be returned! How was I supposed to know that?! What if I find out they're defective, am I just stuck with them?"

**Expected Performance**: **MEDIUM**
- Hit Rate: ~95%
- MRR: ~0.85
- Correctness: ~4.0/5
- Faithfulness: ~4.5/5

**Challenges**:
- Multi-faceted questions require synthesizing info from multiple chunks
- Emotional language doesn't affect retrieval but increases answer complexity
- May need to handle multiple sub-questions simultaneously

---

### 3. MISMATCH Persona 🔴
**Characteristics**:
- Asks questions tangentially related or out-of-scope
- References information NOT in source document
- Requires cross-document knowledge
- Tests handling of off-topic queries

**Example**:
> "Do you have any information on the new laptops released during the last Independence Day Sale?"

*(This asks about product catalog info, but source is promotional events document)*

**Expected Performance**: **LOWEST** ⚠️
- Hit Rate: ~60-70%
- MRR: ~0.5
- Correctness: ~2.5-3.0/5
- Faithfulness: ~3.5-4.0/5

**Why MISMATCH Scores Lowest**:

1. **Retrieval Challenge**
   - Question semantics don't match document content
   - Embeddings retrieve wrong/irrelevant chunks
   - Even if hit=true, chunks won't contain the answer

2. **Generation Quality Drops**
   - LLM works with irrelevant context
   - Higher risk of hallucination
   - May give vague/generic answers
   - Lower faithfulness and correctness

3. **Real-World Value**
   - Tests robustness against out-of-scope queries
   - Users don't always ask questions matching available docs
   - Important for production systems to handle gracefully

4. **Failure Modes**
   - ❌ Retrieval Miss: Wrong document chunks
   - ❌ Low MRR: Correct info (if any) ranked poorly
   - ❌ Hallucination: LLM fills gaps with invented info
   - ❌ Incompleteness: Partial/evasive answers

## Generated Questions Summary

| Persona | Total | Docs | Avg/Doc | Characteristics |
|---------|-------|------|---------|-----------------|
| Standard | 6 | 2 | 3 | Direct, clear, in-scope |
| Frustrated | 6 | 2 | 3 | Complex, emotional, multi-part |
| Mismatch | 6 | 2 | 3 | Off-topic, cross-document |

## Expected Ranking

**Performance (Best → Worst):**

1. 🥇 **STANDARD** - Highest scores across all metrics
2. 🥈 **FRUSTRATED** - Medium scores, complexity challenges
3. 🥉 **MISMATCH** - Lowest scores, out-of-scope failures

## Key Insights

### MISMATCH Persona Surfaces Critical Issues:

✓ **Document Coverage Gaps**: Reveals what users ask but docs don't cover

✓ **Retrieval Robustness**: Tests if system retrieves when semantics don't match

✓ **Hallucination Detection**: Forces LLM to work with wrong context

✓ **User Experience**: Real users often ask off-topic questions

### Why This Testing Matters:

1. **Standard** validates core functionality (happy path)
2. **Frustrated** tests complexity handling (realistic edge cases)  
3. **Mismatch** finds breaking points (adversarial/robustness)

## Conclusion

**MISMATCH persona will surface the lowest scores** because it fundamentally tests the system's failure modes - asking for information that doesn't exist in the source documents.

This is valuable because:
- Identifies documentation gaps
- Tests retrieval fallback behavior
- Reveals hallucination tendencies
- Simulates real-world misuse scenarios

The three personas together provide comprehensive RAG system evaluation:
- ✅ Core functionality (Standard)
- ⚠️ Complexity handling (Frustrated)
- ❌ Failure modes (Mismatch)

---

## Files Generated
- `persona_standard_questions.json` - 6 questions
- `persona_frustrated_questions.json` - 6 questions
- `persona_mismatch_questions.json` - 6 questions
- `eval_standard_results.json` - RAG outputs for standard
- `eval_frustrated_results.json` - RAG outputs for frustrated
- `eval_mismatch_results.json` - RAG outputs for mismatch
