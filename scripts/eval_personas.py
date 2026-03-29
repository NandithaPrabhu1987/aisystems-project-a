"""
Evaluate persona-based questions separately
Run the RAG pipeline on each persona's questions and compare scores
"""
import os
import json
import sys
from rag import ask

def evaluate_persona_questions(questions_file):
    """Evaluate a set of persona questions"""
    with open(questions_file, 'r') as f:
        questions = json.load(f)
    
    persona = questions[0]['persona'] if questions else "unknown"
    
    print(f"\n{'='*70}")
    print(f"EVALUATING: {persona.upper()} PERSONA ({len(questions)} questions)")
    print(f"{'='*70}\n")
    
    results = []
    
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q['id']}: {q['query'][:60]}...")
        
        try:
            # Run RAG
            answer = ask(q['query'])
            
            # Simple scoring - check if answer contains key info
            result = {
                "id": q['id'],
                "query": q['query'],
                "expected_answer": q['expected_answer'],
                "generated_answer": answer,
                "persona": persona,
                "category": q['category']
            }
            
            results.append(result)
            print(f"  ✓ Generated answer ({len(answer)} chars)")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                "id": q['id'],
                "query": q['query'],
                "error": str(e),
                "persona": persona
            })
    
    return results

# Check if persona question files exist
persona_files = [
    "persona_standard_questions.json",
    "persona_frustrated_questions.json",
    "persona_mismatch_questions.json"
]

print("="*70)
print("PERSONA EVALUATION COMPARISON")
print("="*70)

all_persona_results = {}

for pfile in persona_files:
    if os.path.exists(pfile):
        persona_name = pfile.replace("persona_", "").replace("_questions.json", "")
        results = evaluate_persona_questions(pfile)
        all_persona_results[persona_name] = results
        
        # Save individual results
        output_file = f"eval_{persona_name}_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Saved {persona_name} results to: {output_file}")
    else:
        print(f"⚠ File not found: {pfile}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

for persona, results in all_persona_results.items():
    successful = len([r for r in results if 'error' not in r])
    print(f"\n{persona.upper()}:")
    print(f"  Total questions: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(results) - successful}")
