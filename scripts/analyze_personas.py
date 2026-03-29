"""
Analyze persona evaluation results and compare scores
"""
import json
import os

def analyze_persona_results():
    personas = ["standard", "frustrated", "mismatch"]
    
    print("="*70)
    print("PERSONA COMPARISON ANALYSIS")
    print("="*70)
    
    all_data = {}
    
    for persona in personas:
        result_file = f"eval_{persona}_results.json"
        
        if not os.path.exists(result_file):
            print(f"\n⚠ {persona}: Results not found")
            continue
        
        with open(result_file, 'r') as f:
            results = json.load(f)
        
        all_data[persona] = results
        
        print(f"\n{persona.upper()} PERSONA:")
        print("-" * 70)
        
        successful = [r for r in results if 'error' not in r]
        failed = [r for r in results if 'error' in r]
        
        print(f"Total questions: {len(results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        
        if successful:
            avg_answer_length = sum(len(r['generated_answer']) for r in successful) / len(successful)
            print(f"Avg answer length: {avg_answer_length:.0f} characters")
            
            # Show sample questions
            print(f"\nSample questions:")
            for i, r in enumerate(successful[:2], 1):
                print(f"\n  Q{i}: {r['query'][:80]}...")
                print(f"  Answer: {r['generated_answer'][:150]}...")
    
    # Comparative analysis
    print("\n" + "="*70)
    print("COMPARATIVE ANALYSIS")
    print("="*70)
    
    print("\n📊 Expected Performance Ranking (Hypothesis):")
    print("  1. STANDARD - Should perform BEST")
    print("     → Clear, direct questions matching document scope")
    print("     → RAG should retrieve relevant chunks easily")
    print("     → LLM should generate accurate answers")
    
    print("\n  2. FRUSTRATED - Should perform MEDIUM")
    print("     → Complex, multi-part questions")
    print("     → May require synthesizing info from multiple chunks")
    print("     → Emotional language doesn't affect retrieval but increases complexity")
    
    print("\n  3. MISMATCH - Should perform WORST")
    print("     → Questions ask for info NOT in the source document")
    print("     → Retrieval may return irrelevant chunks")
    print("     → LLM may hallucinate or give incomplete answers")
    print("     → Tests system's ability to handle out-of-scope queries")
    
    print("\n📋 Key Differences:")
    
    for persona in personas:
        if persona in all_data:
            print(f"\n{persona.upper()}:")
            results = all_data[persona]
            
            if results:
                # Show first question as example
                sample = results[0]
                print(f"  Example: {sample['query'][:100]}...")
                
                if persona == "standard":
                    print("  → Direct, answerable from source document")
                elif persona == "frustrated":
                    print("  → Complex, emotional, multi-faceted")
                elif persona == "mismatch":
                    print("  → Asks for info from OTHER documents/topics")
    
    print("\n" + "="*70)
    print("WHY MISMATCH SHOULD SCORE LOWEST:")
    print("="*70)
    print("""
1. **Retrieval Challenge**: Questions about content NOT in the document
   → Embeddings won't match well → Wrong chunks retrieved

2. **Answer Quality**: LLM forced to work with irrelevant context
   → May hallucinate to fill gaps
   → May give generic/vague answers
   → Lower faithfulness and correctness scores

3. **Real-world Value**: Tests robustness against out-of-scope queries
   → Important for production RAG systems
   → Users don't always ask questions matching available docs

4. **Expected Failure Modes**:
   - Hit rate may still be high (retrieves *something*)
   - But MRR will be low (wrong chunks ranked high)
   - Faithfulness will drop (hallucination risk)
   - Correctness will be lowest (wrong/incomplete info)
""")
    
    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("""
To get quantitative scores, run full evaluation with LLM-as-judge:
1. Modify eval_harness.py to accept custom question files
2. Run eval on each persona file separately
3. Compare: hit rate, MRR, faithfulness, correctness
4. Confirm hypothesis: mismatch < frustrated < standard
""")

if __name__ == "__main__":
    analyze_persona_results()
