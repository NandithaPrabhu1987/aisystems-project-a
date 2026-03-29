"""
Generate questions with different personas and evaluate them
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "corpus")

def generate_questions_with_persona(doc_path, persona="standard", num_questions=3):
    """
    Generate questions with different persona styles
    
    Args:
        doc_path: Path to document
        persona: 'standard', 'frustrated', or 'mismatch'
        num_questions: Number of questions to generate
    
    Returns:
        List of question dicts
    """
    doc_name = os.path.basename(doc_path)
    
    with open(doc_path, 'r') as f:
        content = f.read()
    
    # Category mapping
    category_map = {
        "07_promotional_events.md": "promotions",
        "02_premium_membership.md": "membership"
    }
    category = category_map.get(doc_name, "general")
    
    word_count = len(content.split())
    
    # Different persona prompts
    if persona == "standard":
        persona_desc = """**Persona: Standard Customer**
- Asks clear, straightforward questions
- Wants specific information about policies
- Uses polite, neutral language
- Questions are directly answerable from the document"""
        
        example_tone = "What is the return policy for promotional items?"
        
    elif persona == "frustrated":
        persona_desc = """**Persona: Frustrated Customer**
- Has encountered a problem or confusion
- May ask compound/complex questions mixing multiple concerns
- Uses emotional or urgent language
- May reference edge cases or exceptions
- Questions may be more challenging to answer completely"""
        
        example_tone = "I've been trying to understand the promotional return policy but it's so confusing - if I bought something during a flash sale with my Premium membership, and now it's been 20 days, can I still return it or not?!"
        
    elif persona == "mismatch":
        persona_desc = """**Persona: Off-Topic/Mismatch Customer**
- Asks questions that are tangentially related or out of scope
- May reference information NOT in this specific document
- Requires knowledge from OTHER documents to answer fully
- Tests retrieval system's ability to handle cross-document queries
- Questions may be partially unanswerable from this document alone"""
        
        example_tone = "What's the warranty on the ProBook X15 that I bought during the promotional event?"
        
    else:
        raise ValueError(f"Unknown persona: {persona}")
    
    prompt = f"""You are generating customer questions for a RAG system evaluation.

**Source Document**: {doc_name}
**Document Length**: ~{word_count} words

{persona_desc}

**Example question tone**: "{example_tone}"

**Document Content**:
---
{content[:3000]}
---

**Task**: Generate {num_questions} questions matching the {persona.upper()} persona style.

For **{persona}** persona:
- Make questions sound authentic to this customer type
- Ensure questions reflect the persona's characteristics
- Questions should be realistic scenarios this persona would ask

**Output Format**: Return ONLY a valid JSON array:
[
  {{
    "query": "Question in {persona} persona style",
    "expected_answer": "Answer based on document content (say 'Information not available in this document' if mismatch persona asks off-topic)",
    "difficulty": "medium",
    "category": "{category}",
    "persona": "{persona}"
  }}
]

Generate {num_questions} {persona} persona questions now:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    
    content_text = response.choices[0].message.content.strip()
    
    # Clean JSON
    if content_text.startswith("```json"):
        content_text = content_text.replace("```json", "").replace("```", "").strip()
    
    questions = json.loads(content_text)
    
    # Add metadata
    for q in questions:
        q["expected_source"] = doc_name
        q["persona"] = persona
    
    return questions


# Test documents
test_docs = [
    "07_promotional_events.md",
    "02_premium_membership.md"
]

personas = ["standard", "frustrated", "mismatch"]

all_results = {}

print("="*70)
print("PERSONA-BASED QUESTION GENERATION")
print("="*70)

for doc_name in test_docs:
    doc_path = os.path.join(CORPUS_DIR, doc_name)
    
    print(f"\n📄 Document: {doc_name}")
    print("="*70)
    
    for persona in personas:
        print(f"\n  🎭 Persona: {persona.upper()}")
        print("  " + "-"*66)
        
        try:
            questions = generate_questions_with_persona(doc_path, persona=persona, num_questions=3)
            
            # Store for evaluation
            key = f"{doc_name}_{persona}"
            all_results[key] = questions
            
            print(f"  ✓ Generated {len(questions)} questions\n")
            
            for i, q in enumerate(questions, 1):
                print(f"    Q{i}: {q['query'][:100]}...")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()

# Save all questions by persona
for persona in personas:
    persona_questions = []
    for key, questions in all_results.items():
        if persona in key:
            persona_questions.extend(questions)
    
    # Add IDs
    for i, q in enumerate(persona_questions):
        q["id"] = f"{persona[:3]}{i+1:03d}"
    
    output_file = f"persona_{persona}_questions.json"
    with open(output_file, 'w') as f:
        json.dump(persona_questions, f, indent=2)
    
    print(f"\n✓ Saved {len(persona_questions)} {persona} questions to: {output_file}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Documents tested: {len(test_docs)}")
print(f"Personas tested: {len(personas)}")
print(f"Total question sets: {len(all_results)}")

for persona in personas:
    count = sum(len(q) for k, q in all_results.items() if persona in k)
    print(f"  {persona}: {count} questions")
