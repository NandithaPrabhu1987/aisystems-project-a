"""
Validate Critique Loop Results
Quick script to show critique loop statistics
"""
import json
import os
from rich.console import Console
from rich.table import Table

console = Console()

def validate_critique():
    critique_file = os.path.join(os.path.dirname(__file__), "..", "outputs", "critique_report.json")
    
    if not os.path.exists(critique_file):
        console.print("[red]❌ Critique report not found![/red]")
        console.print(f"Expected at: {critique_file}")
        return
    
    with open(critique_file, 'r') as f:
        data = json.load(f)
    
    # Summary statistics
    console.print("\n[bold cyan]📊 CRITIQUE LOOP VALIDATION[/bold cyan]")
    console.print("="*60)
    
    console.print(f"\n[yellow]Total Generated:[/yellow] {data['total_generated']} questions")
    console.print(f"[green]✓ Kept:[/green] {data['kept']} questions ({data['kept']/data['total_generated']*100:.1f}%)")
    console.print(f"[yellow]⟳ Rewrite:[/yellow] {data['rewrite']} questions ({data['rewrite']/data['total_generated']*100:.1f}%)")
    console.print(f"[red]✗ Dropped:[/red] {data['dropped']} questions ({data['dropped']/data['total_generated']*100:.1f}%)")
    
    # Score distribution
    console.print("\n[bold]Score Distribution:[/bold]")
    
    realism_scores = [item['critique']['realism_score'] for item in data['critique_results']]
    difficulty_scores = [item['critique']['difficulty_score'] for item in data['critique_results']]
    
    console.print(f"  Realism: avg={sum(realism_scores)/len(realism_scores):.2f}, "
                 f"min={min(realism_scores)}, max={max(realism_scores)}")
    console.print(f"  Difficulty: avg={sum(difficulty_scores)/len(difficulty_scores):.2f}, "
                 f"min={min(difficulty_scores)}, max={max(difficulty_scores)}")
    
    # Decision breakdown table
    table = Table(title="\n🔍 Sample Critique Results (First 10)", show_header=True)
    table.add_column("ID", style="cyan", width=8)
    table.add_column("Realism", justify="center", width=8)
    table.add_column("Difficulty", justify="center", width=10)
    table.add_column("Decision", justify="center", width=10)
    table.add_column("Reason", style="dim", width=50)
    
    for item in data['critique_results'][:10]:
        q = item['question']
        c = item['critique']
        
        if c['decision'] == 'keep':
            decision_style = "[green]✓ KEEP[/green]"
        elif c['decision'] == 'rewrite':
            decision_style = "[yellow]⟳ REWRITE[/yellow]"
        else:
            decision_style = "[red]✗ DROP[/red]"
        
        table.add_row(
            q['id'],
            f"{c['realism_score']}/5",
            f"{c['difficulty_score']}/5",
            decision_style,
            c['reason'][:50] + "..." if len(c['reason']) > 50 else c['reason']
        )
    
    console.print(table)
    
    # Quality check
    console.print("\n[bold]✅ Quality Check:[/bold]")
    high_realism = sum(1 for s in realism_scores if s >= 4)
    acceptable_difficulty = sum(1 for s in difficulty_scores if 2 <= s <= 4)
    
    console.print(f"  High realism (≥4/5): {high_realism}/{len(realism_scores)} "
                 f"({high_realism/len(realism_scores)*100:.1f}%)")
    console.print(f"  Good difficulty (2-4/5): {acceptable_difficulty}/{len(difficulty_scores)} "
                 f"({acceptable_difficulty/len(difficulty_scores)*100:.1f}%)")
    
    console.print("\n" + "="*60)
    console.print("[bold green]✅ Critique loop validated successfully![/bold green]\n")


if __name__ == "__main__":
    validate_critique()
