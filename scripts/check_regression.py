"""
Regression Detection System
Compares current evaluation metrics against baseline to detect performance degradation.
Flags REGRESSION if metrics drop by >5 percentage points.
"""
import json
import os
from rich.console import Console
from rich.table import Table

console = Console()

# Threshold for regression detection (5 percentage points)
REGRESSION_THRESHOLD = 5.0


def load_baseline():
    """
    Load baseline metrics from baseline_scores.json
    
    Returns:
        dict: Baseline metrics including overall scores and category breakdown
    """
    baseline_file = os.path.join(os.path.dirname(__file__), "evaluation", "baseline_scores.json")
    
    if not os.path.exists(baseline_file):
        console.print(f"[red]❌ Baseline file not found: {baseline_file}[/red]")
        return None
    
    with open(baseline_file, 'r') as f:
        baseline = json.load(f)
    
    console.print(f"[green]✓ Loaded baseline from: {baseline_file}[/green]")
    return baseline


def load_current():
    """
    Load current evaluation metrics from eval_results.json or similar
    
    Returns:
        dict: Current metrics in same format as baseline
    """
    # Try multiple possible locations for current results
    possible_files = [
        os.path.join(os.path.dirname(__file__), "results", "eval_results.json"),
        os.path.join(os.path.dirname(__file__), "evaluation", "current_scores.json"),
        os.path.join(os.path.dirname(__file__), "results", "current_eval.json")
    ]
    
    current_file = None
    for filepath in possible_files:
        if os.path.exists(filepath):
            current_file = filepath
            break
    
    if not current_file:
        console.print(f"[yellow]⚠️  No current results file found. Checking options:[/yellow]")
        for f in possible_files:
            console.print(f"  - {f}")
        return None
    
    with open(current_file, 'r') as f:
        current = json.load(f)
    
    console.print(f"[green]✓ Loaded current from: {current_file}[/green]")
    return current


def check_regression(baseline, current):
    """
    Compare current metrics against baseline and detect regressions.
    
    Args:
        baseline: Baseline metrics dict
        current: Current metrics dict
    
    Returns:
        dict: Regression analysis with:
            - has_regression: bool
            - regressions: list of detected regressions
            - improvements: list of improvements
            - stable: list of stable metrics
    """
    if not baseline or not current:
        console.print("[red]❌ Cannot check regression - missing baseline or current data[/red]")
        return None
    
    regressions = []
    improvements = []
    stable = []
    
    # Check overall metrics
    metric_mapping = {
        'hit_rate': 'hit_rate',
        'average_mrr': 'mrr',
        'average_faithfulness': 'faithfulness',
        'average_correctness': 'correctness'
    }
    
    baseline_overall = baseline.get('overall_metrics', baseline.get('overall', {}))
    current_overall = current.get('overall_metrics', current.get('overall', {}))
    
    for baseline_key, display_name in metric_mapping.items():
        if baseline_key in baseline_overall and baseline_key in current_overall:
            baseline_val = baseline_overall[baseline_key]
            current_val = current_overall[baseline_key]
            
            # Calculate percentage point difference
            diff = (current_val - baseline_val) * 100
            
            if diff < -REGRESSION_THRESHOLD:
                regressions.append({
                    'type': 'overall',
                    'metric': display_name,
                    'baseline': baseline_val,
                    'current': current_val,
                    'diff_pct': diff,
                    'severity': 'CRITICAL' if diff < -10 else 'WARNING'
                })
            elif diff > REGRESSION_THRESHOLD:
                improvements.append({
                    'type': 'overall',
                    'metric': display_name,
                    'baseline': baseline_val,
                    'current': current_val,
                    'diff_pct': diff
                })
            else:
                stable.append({
                    'type': 'overall',
                    'metric': display_name,
                    'baseline': baseline_val,
                    'current': current_val,
                    'diff_pct': diff
                })
    
    # Check category-level metrics
    baseline_cats = baseline.get('category_breakdown', baseline.get('by_category', {}))
    current_cats = current.get('category_breakdown', current.get('by_category', {}))
    
    for category in baseline_cats:
        if category in current_cats:
            baseline_score = baseline_cats[category].get('correctness', baseline_cats[category].get('avg_correctness', 0))
            current_score = current_cats[category].get('correctness', current_cats[category].get('avg_correctness', 0))
            
            # Calculate percentage point difference (converting from /5 scale to %)
            diff = (current_score - baseline_score) / 5.0 * 100
            
            if diff < -REGRESSION_THRESHOLD:
                regressions.append({
                    'type': 'category',
                    'metric': category,
                    'baseline': baseline_score,
                    'current': current_score,
                    'diff_pct': diff,
                    'severity': 'CRITICAL' if diff < -10 else 'WARNING'
                })
            elif diff > REGRESSION_THRESHOLD:
                improvements.append({
                    'type': 'category',
                    'metric': category,
                    'baseline': baseline_score,
                    'current': current_score,
                    'diff_pct': diff
                })
            else:
                stable.append({
                    'type': 'category',
                    'metric': category,
                    'baseline': baseline_score,
                    'current': current_score,
                    'diff_pct': diff
                })
    
    return {
        'has_regression': len(regressions) > 0,
        'regressions': regressions,
        'improvements': improvements,
        'stable': stable,
        'threshold': REGRESSION_THRESHOLD
    }


def display_results(analysis):
    """
    Display regression analysis results in formatted tables
    
    Args:
        analysis: Regression analysis dict from check_regression()
    """
    if not analysis:
        console.print("[red]❌ No analysis to display[/red]")
        return
    
    console.print("\n" + "="*100)
    console.print(f"[bold cyan]🔍 REGRESSION DETECTION REPORT[/bold cyan]")
    console.print(f"Threshold: ±{analysis['threshold']} percentage points")
    console.print("="*100)
    
    # Overall Status
    if analysis['has_regression']:
        console.print(f"\n[bold red]❌ REGRESSION DETECTED[/bold red]")
        console.print(f"Found {len(analysis['regressions'])} metric(s) with performance degradation\n")
    else:
        console.print(f"\n[bold green]✅ NO REGRESSION[/bold green]")
        console.print(f"All metrics are stable or improved\n")
    
    # Regressions Table
    if analysis['regressions']:
        console.print("\n" + "="*100)
        console.print("[bold red]🔴 REGRESSIONS (Performance Degradation)[/bold red]")
        console.print("="*100)
        
        table = Table(show_header=True, header_style="bold red")
        table.add_column("Type", style="cyan", width=12)
        table.add_column("Metric", style="white", width=20)
        table.add_column("Baseline", justify="right", width=12)
        table.add_column("Current", justify="right", width=12)
        table.add_column("Diff (pp)", justify="right", width=12)
        table.add_column("Severity", justify="center", width=12)
        
        for reg in sorted(analysis['regressions'], key=lambda x: x['diff_pct']):
            severity_color = "red" if reg['severity'] == 'CRITICAL' else "yellow"
            
            if reg['type'] == 'overall':
                baseline_str = f"{reg['baseline']:.3f}"
                current_str = f"{reg['current']:.3f}"
            else:
                baseline_str = f"{reg['baseline']:.2f}/5"
                current_str = f"{reg['current']:.2f}/5"
            
            table.add_row(
                reg['type'].upper(),
                reg['metric'],
                baseline_str,
                current_str,
                f"[{severity_color}]{reg['diff_pct']:.1f}%[/{severity_color}]",
                f"[{severity_color}]{reg['severity']}[/{severity_color}]"
            )
        
        console.print(table)
    
    # Improvements Table
    if analysis['improvements']:
        console.print("\n" + "="*100)
        console.print("[bold green]🟢 IMPROVEMENTS[/bold green]")
        console.print("="*100)
        
        table = Table(show_header=True, header_style="bold green")
        table.add_column("Type", style="cyan", width=12)
        table.add_column("Metric", style="white", width=20)
        table.add_column("Baseline", justify="right", width=12)
        table.add_column("Current", justify="right", width=12)
        table.add_column("Diff (pp)", justify="right", width=12)
        
        for imp in sorted(analysis['improvements'], key=lambda x: x['diff_pct'], reverse=True):
            if imp['type'] == 'overall':
                baseline_str = f"{imp['baseline']:.3f}"
                current_str = f"{imp['current']:.3f}"
            else:
                baseline_str = f"{imp['baseline']:.2f}/5"
                current_str = f"{imp['current']:.2f}/5"
            
            table.add_row(
                imp['type'].upper(),
                imp['metric'],
                baseline_str,
                current_str,
                f"[green]+{imp['diff_pct']:.1f}%[/green]"
            )
        
        console.print(table)
    
    # Summary
    console.print("\n" + "="*100)
    console.print("[bold]📊 SUMMARY[/bold]")
    console.print("="*100)
    console.print(f"[red]Regressions:[/red] {len(analysis['regressions'])}")
    console.print(f"[green]Improvements:[/green] {len(analysis['improvements'])}")
    console.print(f"[yellow]Stable:[/yellow] {len(analysis['stable'])}")
    console.print("="*100 + "\n")
    
    return analysis['has_regression']


def run_regression_check():
    """Main function to run regression detection"""
    console.print("\n[bold cyan]🔍 Starting Regression Detection...[/bold cyan]\n")
    
    # Load data
    baseline = load_baseline()
    current = load_current()
    
    if not baseline or not current:
        console.print("\n[red]❌ Cannot proceed without baseline and current data[/red]\n")
        return False
    
    # Check for regressions
    console.print("\n[yellow]Analyzing metrics...[/yellow]\n")
    analysis = check_regression(baseline, current)
    
    # Display results
    has_regression = display_results(analysis)
    
    # Save analysis report
    output_file = os.path.join(os.path.dirname(__file__), "results", "regression_report.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    console.print(f"💾 Regression report saved to: [cyan]{output_file}[/cyan]\n")
    
    return not has_regression  # Return True if no regression, False if regression detected


if __name__ == "__main__":
    import sys
    
    success = run_regression_check()
    
    # Exit with appropriate code for CI/CD
    sys.exit(0 if success else 1)
