"""
Demo Critique Loop with Manually Crafted Bad Questions
Shows the drop functionality with intentionally terrible questions
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import sys

sys.path.insert(0, os.path.dirname(__file__))
from synthetic_generator import critique_question, print_critique_table
from rich.console import Console

load_dotenv()
client = OpenAI()
console = Console()


def create_mixed_quality_questions():
    """Manually create questions with clear quality differences"""
    
    doc_name = "01_return_policy.md"
    doc_path = os.path.join(os.path.dirname(__file__), "..", "..", "corpus", doc_name)
    
    with open(doc_path, 'r') as f:
        doc_content = f.read()
    
    # GOOD QUESTIONS (should be KEPT)
    good_questions = [
        {
            "id": "demo001",
            "query": "Can I return my laptop if I opened the box?",
            "expected_answer": "Yes, you can return opened electronics within 30 days of delivery.",
            "difficulty": "easy",
            "category": "returns",
            "expected_source": doc_name,
            "quality_intent": "keep"
        },
        {
            "id": "demo002",
            "query": "What's the return window for Premium members?",
            "expected_answer": "Premium members can return items within 60 days instead of the standard 30 days.",
            "difficulty": "medium",
            "category": "returns",
            "expected_source": doc_name,
            "quality_intent": "keep"
        }
    ]
    
    # BORDERLINE QUESTIONS (might be REWRITE)
    borderline_questions = [
        {
            "id": "demo003",
            "query": "Please provide information regarding the return policy procedures.",
            "expected_answer": "Returns must be initiated within 30 days through our portal.",
            "difficulty": "medium",
            "category": "returns",
            "expected_source": doc_name,
            "quality_intent": "rewrite"
        },
        {
            "id": "demo004",
            "query": "What is the detailed systematic process for merchandise restitution?",
            "expected_answer": "To return items, contact support or use returns.acmera.com within 30 days.",
            "difficulty": "medium",
            "category": "returns",
            "expected_source": doc_name,
            "quality_intent": "rewrite"
        }
    ]
    
    # BAD QUESTIONS (should be DROPPED)
    bad_questions = [
        {
            "id": "demo005",
            "query": "What is the capital of France?",
            "expected_answer": "Paris is the capital of France.",
            "difficulty": "easy",
            "category": "returns",
            "expected_source": doc_name,
            "quality_intent": "drop"
        },
        {
            "id": "demo006",
            "query": "Hereby request information about the thing.",
            "expected_answer": "The thing is described in the document somewhere.",
            "difficulty": "hard",
            "category": "returns",
            "expected_source": doc_name,
            "quality_intent": "drop"
        },
        {
            "id": "demo007",
            "query": "Can I return items to your competitor's store?",
            "expected_answer": "Yes, you can return Acmera items to BestBuy stores.",
            "difficulty": "medium",
            "category": "returns",
            "expected_source": doc_name,
            "quality_intent": "drop"
        },
        {
            "id": "demo008",
            "query": "Please kindly inform me as to the procedural mechanisms by which one might endeavor to effectuate a product restitution transaction.",
            "expected_answer": "Returns are processed according to policy guidelines.",
            "difficulty": "hard",
            "category": "returns",
            "expected_source": doc_name,
            "quality_intent": "drop"
        }
    ]
    
    all_questions = good_questions + borderline_questions + bad_questions
    
    return all_questions, doc_name, doc_content


def run_demo():
    """Run critique demo with clear good/bad examples"""
    
    console.print("\n" + "="*80)
    console.print("[bold cyan]🧪 CRITIQUE LOOP DEMO - Testing Drop Functionality[/bold cyan]")
    console.print("="*80)
    
    # Create test questions
    questions, doc_name, doc_content = create_mixed_quality_questions()
    
    console.print(f"\n[yellow]Created {len(questions)} demo questions:[/yellow]")
    console.print(f"  ✓ {2} HIGH quality (should be KEPT)")
    console.print(f"  ⟳ {2} MEDIUM quality (might be REWRITE)")  
    console.print(f"  ✗ {4} LOW quality (should be DROPPED)")
    
    console.print("\n" + "="*80)
    console.print("[bold]🔍 Running Auto-Critique...[/bold]")
    console.print("="*80 + "\n")
    
    # Critique each question
    critique_results = []
    
    for q in questions:
        intent = q['quality_intent']
        console.print(f"[dim]Critiquing {q['id']} (intent: {intent})...[/dim]")
        
        try:
            critique = critique_question(q, doc_name, doc_content)
            critique_results.append({
                'question': q,
                'critique': critique
            })
            
            actual = critique['decision']
            match_symbol = "✓" if intent == actual else "✗"
            
            if actual == 'keep':
                color = "green"
            elif actual == 'rewrite':
                color = "yellow"
            else:
                color = "red"
            
            console.print(f"  {match_symbol} Intent: [{intent:8}] → Actual: [{color}]{actual:8}[/{color}] "
                         f"(Realism:{critique['realism_score']}/5, Diff:{critique['difficulty_score']}/5)")
            
        except Exception as e:
            console.print(f"  [red]✗ Critique failed: {e}[/red]")
    
    # Print formatted table
    print("\n")
    print_critique_table(critique_results)
    
    # Detailed analysis
    kept = [r for r in critique_results if r['critique']['decision'] == 'keep']
    rewrite = [r for r in critique_results if r['critique']['decision'] == 'rewrite']
    dropped = [r for r in critique_results if r['critique']['decision'] == 'drop']
    
    console.print("\n" + "="*80)
    console.print("[bold cyan]📊 DETAILED ANALYSIS[/bold cyan]")
    console.print("="*80)
    
    # Show kept questions
    console.print(f"\n[bold green]✓ KEPT: {len(kept)} questions[/bold green]")
    for item in kept:
        console.print(f"  • {item['question']['id']}: [dim]{item['question']['query']}[/dim]")
    
    # Show rewrite questions
    console.print(f"\n[bold yellow]⟳ REWRITE: {len(rewrite)} questions[/bold yellow]")
    for item in rewrite:
        console.print(f"  • {item['question']['id']}: [dim]{item['question']['query']}[/dim]")
        console.print(f"    [italic]Why: {item['critique']['reason']}[/italic]")
    
    # Show dropped questions
    console.print(f"\n[bold red]✗ DROPPED: {len(dropped)} questions[/bold red]")
    for item in dropped:
        console.print(f"  • {item['question']['id']}: [dim]{item['question']['query']}[/dim]")
        console.print(f"    [italic]Why: {item['critique']['reason']}[/italic]")
    
    # Save results
    output_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    demo_report = {
        'total_generated': len(questions),
        'kept': len(kept),
        'rewrite': len(rewrite),
        'dropped': len(dropped),
        'critique_results': critique_results
    }
    
    output_file = os.path.join(output_dir, "demo_critique_drops.json")
    with open(output_file, 'w') as f:
        json.dump(demo_report, f, indent=2)
    
    console.print(f"\n💾 Demo results saved to: [cyan]{output_file}[/cyan]")
    
    # Final summary
    console.print("\n" + "="*80)
    if dropped:
        console.print(f"[bold green]✅ SUCCESS![/bold green] Critique loop dropped {len(dropped)} low-quality questions")
        console.print(f"[bold green]Only {len(kept)} high-quality questions would be merged into golden dataset[/bold green]")
    else:
        console.print("[bold yellow]⚠️  No questions dropped - all passed quality checks[/bold yellow]")
    console.print("="*80 + "\n")


if __name__ == "__main__":
    run_demo()
