"""
Test Critique Loop with Intentionally Poor Questions
Generates a mix of good and bad questions to demonstrate the drop functionality
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import sys

# Add parent directory to path to import from synthetic_generator
sys.path.insert(0, os.path.dirname(__file__))
from synthetic_generator import critique_question, print_critique_table

load_dotenv()

client = OpenAI()
CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "corpus")


def generate_test_questions_with_quality_mix():
    """
    Generate a mix of high, medium, and low quality questions to test critique loop
    """
    
    # Read a sample document
    doc_path = os.path.join(CORPUS_DIR, "01_return_policy.md")
    with open(doc_path, 'r') as f:
        doc_content = f.read()
    
    doc_name = "01_return_policy.md"
    
    # Prompt that generates MIXED quality questions (good + bad)
    prompt = f"""You are testing a QA system by generating MIXED quality questions - some good, some intentionally bad.

**Source Document**: {doc_name}
**Content**:
---
{doc_content[:2000]}
---

**Task**: Generate 12 questions with VARYING quality levels:

**Generate 4 HIGH QUALITY questions** (should be KEPT):
- Realistic customer language
- Clear, accurate answers from the document
- Appropriate difficulty

**Generate 4 MEDIUM QUALITY questions** (might be REWRITE):
- Slightly robotic or formal language
- OR unclear/incomplete answers
- OR answers that require assumptions

**Generate 4 LOW QUALITY questions** (should be DROPPED):
- Completely robotic/artificial language (e.g., "Please provide information regarding...")
- OR questions about information NOT in the document
- OR nonsensical/irrelevant questions
- OR completely wrong answers

**Output Format** (JSON array only):
[
  {{
    "query": "Question text here",
    "expected_answer": "Answer text here",
    "difficulty": "medium",
    "category": "returns",
    "quality_intent": "keep|rewrite|drop"
  }}
]

Generate 12 questions now (4 keep + 4 rewrite + 4 drop):"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0  # Higher temperature for more variety
    )
    
    content = response.choices[0].message.content.strip()
    
    # Extract JSON
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    
    questions = json.loads(content)
    
    # Add IDs and source
    for i, q in enumerate(questions):
        q["id"] = f"test{i+1:03d}"
        q["expected_source"] = doc_name
    
    return questions, doc_name, doc_content


def run_critique_test():
    """Run critique loop on mixed quality questions"""
    
    print("\n" + "="*80)
    print("🧪 TESTING CRITIQUE LOOP WITH MIXED QUALITY QUESTIONS")
    print("="*80)
    print("\nGenerating 12 test questions (4 good, 4 medium, 4 bad)...")
    
    # Generate mixed quality questions
    questions, doc_name, doc_content = generate_test_questions_with_quality_mix()
    
    print(f"✓ Generated {len(questions)} test questions\n")
    print("="*80)
    print("🔍 RUNNING AUTO-CRITIQUE...")
    print("="*80 + "\n")
    
    # Critique each question
    critique_results = []
    
    for q in questions:
        print(f"Critiquing {q['id']} (intent: {q.get('quality_intent', 'unknown')})...")
        
        try:
            critique = critique_question(q, doc_name, doc_content)
            critique_results.append({
                'question': q,
                'critique': critique
            })
            
            # Show real-time feedback
            intent = q.get('quality_intent', 'unknown')
            actual = critique['decision']
            match = "✓" if intent == actual else "✗"
            
            print(f"  {match} Intent: {intent:8} → Actual: {actual:8} "
                  f"(R:{critique['realism_score']}/5, D:{critique['difficulty_score']}/5)")
            
        except Exception as e:
            print(f"  ✗ Critique failed: {e}")
    
    # Print critique table
    print("\n")
    print_critique_table(critique_results)
    
    # Analyze results
    kept = [r for r in critique_results if r['critique']['decision'] == 'keep']
    rewrite = [r for r in critique_results if r['critique']['decision'] == 'rewrite']
    dropped = [r for r in critique_results if r['critique']['decision'] == 'drop']
    
    print("\n" + "="*80)
    print("📊 CRITIQUE ANALYSIS")
    print("="*80)
    
    print(f"\n✓ KEPT: {len(kept)} questions")
    if kept:
        print("   Sample kept questions:")
        for item in kept[:3]:
            print(f"   - {item['question']['id']}: {item['question']['query'][:60]}...")
    
    print(f"\n⟳ REWRITE: {len(rewrite)} questions")
    if rewrite:
        print("   Questions flagged for improvement:")
        for item in rewrite:
            print(f"   - {item['question']['id']}: {item['question']['query'][:60]}...")
            print(f"     Reason: {item['critique']['reason']}")
    
    print(f"\n✗ DROPPED: {len(dropped)} questions")
    if dropped:
        print("   Low quality questions removed:")
        for item in dropped:
            print(f"   - {item['question']['id']}: {item['question']['query'][:60]}...")
            print(f"     Reason: {item['critique']['reason']}")
    
    # Match analysis
    print(f"\n" + "="*80)
    print("🎯 INTENT vs ACTUAL MATCH ANALYSIS")
    print("="*80)
    
    matches = 0
    for item in critique_results:
        intent = item['question'].get('quality_intent', 'unknown')
        actual = item['critique']['decision']
        if intent == actual:
            matches += 1
    
    print(f"\nMatch rate: {matches}/{len(critique_results)} ({matches/len(critique_results)*100:.1f}%)")
    
    # Save results
    output_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    test_report = {
        'total_generated': len(questions),
        'kept': len(kept),
        'rewrite': len(rewrite),
        'dropped': len(dropped),
        'match_rate': matches / len(critique_results),
        'critique_results': critique_results
    }
    
    output_file = os.path.join(output_dir, "test_critique_drops.json")
    with open(output_file, 'w') as f:
        json.dump(test_report, f, indent=2)
    
    print(f"\n💾 Test results saved to: {output_file}")
    
    # Summary
    print("\n" + "="*80)
    if dropped:
        print("✅ SUCCESS: Critique loop successfully identified and dropped low-quality questions!")
    else:
        print("⚠️  WARNING: No questions were dropped. Consider generating more varied quality.")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_critique_test()
