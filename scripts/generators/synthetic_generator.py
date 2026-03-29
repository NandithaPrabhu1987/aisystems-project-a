"""
Synthetic Question Generator for RAG Evaluation
Generates synthetic test cases from corpus documents using GPT-4o-mini
Includes auto-critique loop to filter low-quality questions
"""
import os
import json
import glob
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()

client = OpenAI()
CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "corpus")
SCRIPT_DIR = os.path.dirname(__file__)
console = Console()


def generate_questions_from_document(doc_path, num_questions=2, difficulty="medium"):
    """
    Generate synthetic questions from a document using LLM.
    
    Args:
        doc_path: Path to the source document
        num_questions: Number of questions to generate
        difficulty: Difficulty level (easy, medium, hard)
    
    Returns:
        List of generated question dictionaries
    """
    doc_name = os.path.basename(doc_path)
    
    with open(doc_path, 'r') as f:
        content = f.read()
    
    # Determine category from filename
    category_map = {
        "01_return_policy.md": "returns",
        "02_premium_membership.md": "membership",
        "03_shipping_policy.md": "shipping",
        "04_warranty_policy.md": "warranty",
        "05_payment_methods.md": "payments",
        "06_support_faq.md": "support",
        "07_promotional_events.md": "promotions",
        "08_support_tickets.md": "support",
        "09_electronics_catalog.md": "products",
        "10_account_management.md": "account",
        "11_internal_pricing.md": "pricing",
        "12_corporate_gifting.md": "corporate",
        "13_acmera_wallet.md": "wallet",
        "14_probook_troubleshooting.md": "troubleshooting",
        "15_slack_support_chat.md": "support",
        "16_referral_program.md": "referrals",
        "17_smart_home_ecosystem.md": "smart_home",
        "18_sustainability.md": "sustainability",
        "19_acmera_business.md": "business"
    }
    
    category = category_map.get(doc_name, "general")
    
    # Count approximate tokens/words
    word_count = len(content.split())
    
    prompt = f"""You are a QA engineer creating high-quality evaluation questions for a customer support RAG system.

**Your Role**: Generate realistic customer questions that test the RAG system's ability to retrieve and answer from this specific document.

**Source Document**: {doc_name}
**Document Length**: ~{word_count} words
**Content**:
---
{content[:3000]}
---

**Task**: Generate {num_questions} {difficulty}-level customer questions that:

1. **Realistic**: Sound like actual customer inquiries (conversational, not robotic)
2. **Specific**: Target information present in this document
3. **Diverse**: Cover different sections and aspects of the content
4. **Testable**: Have clear, verifiable answers from the document

**Difficulty Level - {difficulty.upper()}**:
- **easy**: Single-fact questions (e.g., "What is the return window?")
- **medium**: Multi-step reasoning or policy understanding (e.g., "If I'm a Premium member, can I return after 30 days?")
- **hard**: Complex scenarios, edge cases, or multi-part questions (e.g., "Compare shipping options for orders under ₹999 vs Premium members")

**Output Format**: Return ONLY a valid JSON array (no markdown, no explanation):
[
  {{
    "query": "Natural customer question here",
    "expected_answer": "Concise but complete answer extracted from the document (2-3 sentences max)",
    "difficulty": "{difficulty}",
    "category": "{category}"
  }}
]

**Quality Checklist**:
✓ Questions sound like real customer inquiries
✓ Answers are directly supported by document content
✓ No hallucinated information in answers
✓ Questions test different parts of the document
✓ Appropriate complexity for {difficulty} difficulty

Generate {num_questions} questions now:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    
    # Parse the response - it should be a JSON array
    content = response.choices[0].message.content.strip()
    
    # Try to extract JSON array if wrapped
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    
    questions = json.loads(content)
    
    # Add doc_name to each question
    for q in questions:
        q["expected_source"] = doc_name
    
    return questions


def generate_synthetic_dataset(num_questions=25, output_file=None, difficulty_mix=None, enable_critique=True):
    """
    Generate synthetic test cases across all documents with optional auto-critique.
    
    Args:
        num_questions: Target number of questions to generate
        output_file: Output JSON file path (optional)
        difficulty_mix: Optional dict with difficulty distribution (e.g., {'easy': 0.3, 'medium': 0.5, 'hard': 0.2})
        enable_critique: If True, use auto-critique loop to filter questions
    
    Returns:
        List of generated questions (filtered if critique enabled)
    """
    doc_files = sorted(glob.glob(os.path.join(CORPUS_DIR, "*.md")))
    
    # If critique is enabled, generate MORE questions than needed to account for drops
    generation_target = int(num_questions * 1.5) if enable_critique else num_questions
    
    # Distribute questions across documents
    questions_per_doc = max(1, generation_target // len(doc_files))
    remaining_questions = generation_target % len(doc_files)
    
    all_questions = []
    doc_content_map = {}  # Store doc content for critique
    
    print(f"{'='*80}")
    print(f"Generating {generation_target} synthetic questions from {len(doc_files)} documents...")
    if enable_critique:
        print(f"Auto-critique ENABLED (target {num_questions} after filtering)")
    print(f"Target: ~{questions_per_doc} questions per document\n")
    
    for i, doc_path in enumerate(doc_files):
        doc_name = os.path.basename(doc_path)
        print(f"Processing {doc_name}...")
        
        # Read document content for critique
        with open(doc_path, 'r') as f:
            doc_content = f.read()
            doc_content_map[doc_name] = doc_content
        
        # Add extra questions to first few documents to reach target
        num_q = questions_per_doc + (1 if i < remaining_questions else 0)
        
        try:
            # Mix of difficulties
            questions = generate_questions_from_document(doc_path, num_questions=num_q, difficulty="medium")
            all_questions.extend(questions)
            print(f"  ✓ Generated {len(questions)} questions")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\nTotal generated: {len(all_questions)} questions")
    
    # Add IDs before critique
    for i, q in enumerate(all_questions):
        q["id"] = f"syn{i+1:03d}"
    
    # Auto-critique loop
    if enable_critique:
        print(f"\n{'='*80}")
        print("🔍 Starting Auto-Critique Loop...")
        print(f"{'='*80}\n")
        
        critique_results = []
        
        for q in all_questions:
            doc_name = q.get('expected_source', '')
            doc_content = doc_content_map.get(doc_name, '')
            
            try:
                critique = critique_question(q, doc_name, doc_content)
                critique_results.append({
                    'question': q,
                    'critique': critique
                })
                print(f"  Critiqued {q['id']}: {critique['decision'].upper()} (realism={critique['realism_score']}, difficulty={critique['difficulty_score']})")
            except Exception as e:
                print(f"  ✗ Critique failed for {q['id']}: {e}")
                # Default to keep if critique fails
                critique_results.append({
                    'question': q,
                    'critique': {
                        'realism_score': 3,
                        'difficulty_score': 3,
                        'decision': 'keep',
                        'reason': 'Critique failed, defaulting to keep'
                    }
                })
        
        # Print critique table
        print(f"\n")
        print_critique_table(critique_results)
        
        # Filter questions based on critique
        kept_questions = [
            item['question'] 
            for item in critique_results 
            if item['critique']['decision'] == 'keep'
        ]
        
        dropped_questions = [
            item['question'] 
            for item in critique_results 
            if item['critique']['decision'] == 'drop'
        ]
        
        rewrite_questions = [
            item['question'] 
            for item in critique_results 
            if item['critique']['decision'] == 'rewrite'
        ]
        
        print(f"📊 Filtering Results:")
        print(f"  ✓ Kept: {len(kept_questions)} questions")
        print(f"  ⟳ Flagged for rewrite: {len(rewrite_questions)} questions")
        print(f"  ✗ Dropped: {len(dropped_questions)} questions")
        
        # Save critique report
        critique_report_file = os.path.join(SCRIPT_DIR, "..", "outputs", "critique_report.json")
        os.makedirs(os.path.dirname(critique_report_file), exist_ok=True)
        
        with open(critique_report_file, 'w') as f:
            json.dump({
                'total_generated': len(all_questions),
                'kept': len(kept_questions),
                'rewrite': len(rewrite_questions),
                'dropped': len(dropped_questions),
                'critique_results': critique_results
            }, f, indent=2)
        
        print(f"\n💾 Critique report saved to: {critique_report_file}")
        
        # Use only kept questions
        all_questions = kept_questions
        
        # Re-number IDs after filtering
        for i, q in enumerate(all_questions):
            q["id"] = f"syn{i+1:03d}"
    
    print(f"\n{'='*80}")
    print(f"Final dataset: {len(all_questions)} questions")
    print(f"{'='*80}\n")
    
    # Save if output file specified
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(all_questions, f, indent=2)
        print(f"💾 Saved to: {output_file}\n")
    
    return all_questions


def critique_question(question, doc_name, doc_content):
    """
    Use GPT-4o-mini to critique a generated question for realism and difficulty.
    
    Args:
        question: Question dictionary with query, expected_answer, difficulty, category
        doc_name: Source document name
        doc_content: Excerpt of source document content
    
    Returns:
        Dictionary with realism_score, difficulty_score, and decision (keep/rewrite/drop)
    """
    critique_prompt = f"""You are a QA quality assessor evaluating synthetic questions for a customer support RAG system.

**Source Document**: {doc_name}
**Document Excerpt**:
---
{doc_content[:2000]}
---

**Generated Question**:
- **Query**: {question['query']}
- **Expected Answer**: {question['expected_answer']}
- **Stated Difficulty**: {question['difficulty']}
- **Category**: {question['category']}

**Your Task**: Evaluate this question on TWO dimensions:

1. **REALISM** (1-5): Does this sound like a real customer question?
   - 5: Perfectly natural, conversational customer language
   - 4: Natural with minor artificial elements
   - 3: Somewhat robotic but acceptable
   - 2: Clearly artificial or overly formal
   - 1: Completely unrealistic or nonsensical

2. **DIFFICULTY** (1-5): How hard is this for a RAG system to answer correctly?
   - 5: Very hard - requires multi-hop reasoning, edge case understanding, or synthesis
   - 4: Hard - requires understanding context or combining multiple facts
   - 3: Medium - requires finding specific information and basic reasoning
   - 2: Easy - single fact lookup with clear keywords
   - 1: Trivial - answer is in document title or first sentence

3. **DECISION**: Based on quality, choose:
   - **keep**: High quality (realism ≥3, difficulty 2-5, answer is accurate)
   - **rewrite**: Salvageable but needs improvement (realism 2, or answer unclear)
   - **drop**: Low quality (realism 1, or completely wrong answer, or unanswerable)

**Output Format** (JSON only, no explanation):
{{
  "realism_score": <1-5>,
  "difficulty_score": <1-5>,
  "decision": "<keep|rewrite|drop>",
  "reason": "<one sentence explaining the decision>"
}}

Evaluate now:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": critique_prompt}],
        temperature=0.3  # Lower temperature for more consistent evaluation
    )
    
    content = response.choices[0].message.content.strip()
    
    # Extract JSON
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    
    critique = json.loads(content)
    return critique


def print_critique_table(critique_results):
    """Print a formatted table of critique results"""
    
    table = Table(title="🔍 Auto-Critique Results", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=8)
    table.add_column("Query Preview", style="white", width=40)
    table.add_column("Realism", justify="center", width=8)
    table.add_column("Difficulty", justify="center", width=10)
    table.add_column("Decision", justify="center", width=10)
    table.add_column("Reason", style="dim", width=35)
    
    # Count decisions
    keep_count = sum(1 for c in critique_results if c['critique']['decision'] == 'keep')
    rewrite_count = sum(1 for c in critique_results if c['critique']['decision'] == 'rewrite')
    drop_count = sum(1 for c in critique_results if c['critique']['decision'] == 'drop')
    
    for item in critique_results:
        q = item['question']
        c = item['critique']
        
        # Truncate query for display
        query_preview = q['query'][:40] + "..." if len(q['query']) > 40 else q['query']
        
        # Color code decision
        if c['decision'] == 'keep':
            decision_style = "[green]✓ KEEP[/green]"
        elif c['decision'] == 'rewrite':
            decision_style = "[yellow]⟳ REWRITE[/yellow]"
        else:
            decision_style = "[red]✗ DROP[/red]"
        
        # Color code scores
        realism_style = "green" if c['realism_score'] >= 4 else ("yellow" if c['realism_score'] >= 3 else "red")
        difficulty_style = "green" if 2 <= c['difficulty_score'] <= 4 else "yellow"
        
        table.add_row(
            q.get('id', 'N/A'),
            query_preview,
            f"[{realism_style}]{c['realism_score']}/5[/{realism_style}]",
            f"[{difficulty_style}]{c['difficulty_score']}/5[/{difficulty_style}]",
            decision_style,
            c['reason'][:35] + "..." if len(c['reason']) > 35 else c['reason']
        )
    
    console.print(table)
    console.print(f"\n📊 Summary: [green]{keep_count} KEEP[/green] | [yellow]{rewrite_count} REWRITE[/yellow] | [red]{drop_count} DROP[/red]\n")


if __name__ == "__main__":
    # Generate 25 synthetic questions with auto-critique enabled
    output_path = os.path.join(SCRIPT_DIR, "..", "outputs", "synthetic_questions.json")
    questions = generate_synthetic_dataset(
        num_questions=25, 
        output_file=output_path,
        enable_critique=True  # Enable auto-critique loop
    )
    
    console.print("\n[bold cyan]Sample Kept Questions:[/bold cyan]")
    for q in questions[:3]:
        console.print(f"\n[yellow]Category:[/yellow] {q['category']}")
        console.print(f"[yellow]Query:[/yellow] {q['query']}")
        console.print(f"[yellow]Answer:[/yellow] {q['expected_answer'][:100]}...")
