"""
Failure Heat Map Generator
Analyzes evaluation results to create a 2D table of Category × Difficulty showing correctness scores.
Identifies priority areas (dark red cells = low correctness + hard difficulty).
"""
import json
import os
from collections import defaultdict

# ANSI color codes for terminal output
class Colors:
    RED = '\033[48;5;160m\033[97m'       # Red background, white text
    YELLOW = '\033[48;5;220m\033[30m'    # Yellow background, black text
    GREEN = '\033[48;5;34m\033[97m'      # Green background, white text
    RESET = '\033[0m'
    BOLD = '\033[1m'


def get_color_for_percentage(percentage):
    """
    Return color based on percentage (score/5.0 * 100).
    Green: ≥80% (score ≥4.0)
    Yellow: 60-80% (score 3.0-4.0)
    Red: <60% (score <3.0)
    """
    if percentage >= 80.0:
        return Colors.GREEN
    elif percentage >= 60.0:
        return Colors.YELLOW
    else:
        return Colors.RED


def parse_eval_results(results_file):
    """Parse evaluation results and extract scores by category and difficulty"""
    
    # Load golden dataset to get difficulty levels
    golden_file = os.path.join(os.path.dirname(results_file), "..", "evaluation", "golden_dataset.json")
    with open(golden_file, 'r') as f:
        golden_data = json.load(f)
    
    # Create mapping of id -> (category, difficulty)
    id_map = {}
    for item in golden_data:
        id_map[item['id']] = {
            'category': item['category'],
            'difficulty': item['difficulty']
        }
    
    # Parse eval_results.txt to extract scores
    scores = defaultdict(lambda: defaultdict(list))
    
    with open(results_file, 'r') as f:
        lines = f.readlines()
    
    current_id = None
    for line in lines:
        # Match lines like: [1/75] Processing: q01 - returns
        if line.strip().startswith('[') and 'Processing:' in line:
            parts = line.split('Processing:')[1].strip().split(' - ')
            current_id = parts[0].strip()
        
        # Match lines like: ✓ Hit: True | MRR: 1.000 | Faith: 5/5 | Correct: 4/5
        if '✓ Hit:' in line and 'Correct:' in line:
            try:
                # Extract correctness score
                correct_part = line.split('Correct:')[1].strip()
                correct_score = float(correct_part.split('/')[0])
                
                if current_id and current_id in id_map:
                    info = id_map[current_id]
                    category = info['category']
                    difficulty = info['difficulty']
                    scores[category][difficulty].append(correct_score)
            except:
                continue
    
    return scores


def calculate_averages(scores):
    """Calculate average scores for each category-difficulty combination"""
    averages = {}
    
    for category, diff_dict in scores.items():
        averages[category] = {}
        for difficulty, score_list in diff_dict.items():
            if score_list:
                averages[category][difficulty] = sum(score_list) / len(score_list)
    
    return averages


def create_heat_map(averages):
    """Create a visual heat map table with categories as rows and difficulties as columns"""
    
    # Get all categories and difficulties
    categories = sorted(averages.keys())
    difficulties = ['easy', 'medium', 'hard']
    
    # Print header
    print("\n" + "="*110)
    print(f"{Colors.BOLD}FAILURE HEAT MAP - Category (Rows) × Difficulty (Columns){Colors.RESET}")
    print("="*110)
    print("\n📊 Color Legend (Percentage of Max Score):")
    print(f"{Colors.GREEN}  Green ≥80% (≥4.0/5.0)  {Colors.RESET} |  " + 
          f"{Colors.YELLOW}  Yellow 60-80% (3.0-4.0)  {Colors.RESET} |  " +
          f"{Colors.RED}  Red <60% (<3.0/5.0)  {Colors.RESET}")
    print("\n" + "-"*110)
    
    # Print table header
    header = f"{'Category':<25}"
    for diff in difficulties:
        header += f"| {diff.capitalize():^18} "
    header += "| Avg"
    print(f"{Colors.BOLD}{header}{Colors.RESET}")
    print("-"*110)
    
    # Print each category row
    priority_list = []
    heat_map_table = []
    
    for category in categories:
        row = f"{category:<25}"
        row_data = {'category': category}
        category_scores = []
        
        for difficulty in difficulties:
            score = averages.get(category, {}).get(difficulty)
            
            if score is not None:
                percentage = (score / 5.0) * 100
                color = get_color_for_percentage(percentage)
                row += f"| {color} {score:.2f} ({percentage:.0f}%) {Colors.RESET} "
                category_scores.append(score)
                row_data[difficulty] = {'score': score, 'percentage': percentage}
                
                # Track items below 80% (score < 4.0) for priority list
                if percentage < 80.0:
                    priority_list.append({
                        'category': category,
                        'difficulty': difficulty,
                        'score': score,
                        'percentage': percentage
                    })
            else:
                row += f"| {'N/A':^18} "
                row_data[difficulty] = None
        
        # Calculate category average
        if category_scores:
            avg = sum(category_scores) / len(category_scores)
            avg_pct = (avg / 5.0) * 100
            row += f"| {avg:.2f}"
            row_data['average'] = avg
        else:
            row += f"| N/A"
            row_data['average'] = None
        
        print(row)
        heat_map_table.append(row_data)
    
    print("-"*110)
    
    return priority_list, heat_map_table


def generate_priority_list(priority_list):
    """Generate Week 2 priority list based on heat map"""
    
    print("\n" + "="*110)
    print(f"{Colors.BOLD}🎯 WEEK 2 PRIORITY LIST{Colors.RESET}")
    print("="*110)
    print("\n🔴 Red & Yellow Cells (Below 80% Performance)\n")
    
    # Sort by percentage (lowest first) and difficulty (hard first)
    difficulty_weight = {'hard': 3, 'medium': 2, 'easy': 1}
    priority_list.sort(key=lambda x: (x['percentage'], -difficulty_weight[x['difficulty']]))
    
    if not priority_list:
        print("✅ No priority items found! All scores are ≥80% (4.0/5.0).\n")
        return []
    
    print(f"{'Rank':<6} {'Category':<20} {'Difficulty':<12} {'Score':<10} {'%':<8} {'Priority':<15}")
    print("-"*110)
    
    for i, item in enumerate(priority_list, 1):
        category = item['category']
        difficulty = item['difficulty']
        score = item['score']
        percentage = item['percentage']
        
        # Determine priority level based on percentage
        if percentage < 60.0:
            priority = "🔴 CRITICAL"
        elif percentage < 70.0 and difficulty in ['medium', 'hard']:
            priority = "🟠 HIGH"
        elif percentage < 80.0 and difficulty == 'hard':
            priority = "🟡 MEDIUM-HIGH"
        else:
            priority = "🟡 MEDIUM"
        
        print(f"{i:<6} {category:<20} {difficulty:<12} {score:<10.2f} {percentage:<8.0f}% {priority:<15}")
    
    print("\n" + "="*110)
    print(f"{Colors.BOLD}RECOMMENDED ACTIONS{Colors.RESET}")
    print("="*110)
    
    # Group by category
    by_category = defaultdict(list)
    for item in priority_list:
        by_category[item['category']].append(item)
    
    print("\n📋 Focus Areas:\n")
    for category, items in sorted(by_category.items()):
        avg_score = sum(item['score'] for item in items) / len(items)
        difficulties = [item['difficulty'] for item in items]
        
        print(f"\n{Colors.BOLD}{category.upper()}{Colors.RESET} (Avg: {avg_score:.2f})")
        print(f"  Difficulties affected: {', '.join(set(difficulties))}")
        print(f"  Action items:")
        
        if category == "shipping":
            print(f"    • Improve chunking for shipping tier information")
            print(f"    • Add structured metadata for costs and timelines")
            print(f"    • Create comprehensive shipping FAQ chunks")
        elif category == "returns":
            print(f"    • Better chunk exception clauses and conditions")
            print(f"    • Add 'return_conditions' metadata tags")
            print(f"    • Cross-link related policy chunks")
        elif category == "products":
            print(f"    • Implement product-specific knowledge graphs")
            print(f"    • Add structured product metadata")
            print(f"    • Improve product spec chunking strategy")
        else:
            print(f"    • Review and improve document structure")
            print(f"    • Add relevant metadata tags")
            print(f"    • Increase chunk overlap for complex queries")


def save_heat_map_to_file(heat_map_table, priority_list, output_dir):
    """Save heat map to markdown and JSON files"""
    
    # Save markdown version
    md_file = os.path.join(output_dir, "heat_map.md")
    with open(md_file, 'w') as f:
        f.write("# Failure Heat Map - Category × Difficulty\n\n")
        f.write("## Color Legend\n")
        f.write("- 🟢 **Green**: ≥80% (≥4.0/5.0)\n")
        f.write("- 🟡 **Yellow**: 60-80% (3.0-4.0)\n")
        f.write("- 🔴 **Red**: <60% (<3.0/5.0)\n\n")
        
        f.write("## Heat Map Table\n\n")
        f.write("| Category | Easy | Medium | Hard | Avg |\n")
        f.write("|----------|------|--------|------|-----|\n")
        
        for row in heat_map_table:
            category = row['category']
            line = f"| {category} |"
            
            for diff in ['easy', 'medium', 'hard']:
                if row[diff] is not None:
                    score = row[diff]['score']
                    pct = row[diff]['percentage']
                    
                    if pct >= 80:
                        emoji = "🟢"
                    elif pct >= 60:
                        emoji = "🟡"
                    else:
                        emoji = "🔴"
                    
                    line += f" {emoji} {score:.2f} ({pct:.0f}%) |"
                else:
                    line += " N/A |"
            
            if row['average'] is not None:
                line += f" {row['average']:.2f} |"
            else:
                line += " N/A |"
            
            f.write(line + "\n")
        
        f.write("\n## Week 2 Priority List\n\n")
        f.write("Items below 80% performance:\n\n")
        f.write("| Rank | Category | Difficulty | Score | % | Priority |\n")
        f.write("|------|----------|------------|-------|---|----------|\n")
        
        for i, item in enumerate(priority_list, 1):
            pct = item['percentage']
            if pct < 60:
                priority = "🔴 CRITICAL"
            elif pct < 70 and item['difficulty'] in ['medium', 'hard']:
                priority = "🟠 HIGH"
            elif pct < 80 and item['difficulty'] == 'hard':
                priority = "🟡 MEDIUM-HIGH"
            else:
                priority = "🟡 MEDIUM"
            
            f.write(f"| {i} | {item['category']} | {item['difficulty']} | "
                   f"{item['score']:.2f} | {pct:.0f}% | {priority} |\n")
    
    print(f"\n💾 Heat map saved to: {md_file}")


def generate_statistical_summary(averages):
    """Generate statistical summary"""
    
    print("\n" + "="*110)
    print(f"{Colors.BOLD}📈 STATISTICAL SUMMARY{Colors.RESET}")
    print("="*110)
    
    all_scores = []
    for category, diff_dict in averages.items():
        for difficulty, score in diff_dict.items():
            all_scores.append((category, difficulty, score))
    
    # Overall stats
    scores_only = [s[2] for s in all_scores]
    if scores_only:
        print(f"\n📊 Overall Statistics:")
        print(f"  Total category-difficulty combinations: {len(scores_only)}")
        print(f"  Average correctness: {sum(scores_only)/len(scores_only):.2f}/5.0")
        print(f"  Highest score: {max(scores_only):.2f}")
        print(f"  Lowest score: {min(scores_only):.2f}")
        print(f"  Score range: {max(scores_only) - min(scores_only):.2f}")
    
    # By difficulty
    by_diff = defaultdict(list)
    for cat, diff, score in all_scores:
        by_diff[diff].append(score)
    
    print(f"\n📊 By Difficulty:")
    for diff in ['easy', 'medium', 'hard']:
        if diff in by_diff and by_diff[diff]:
            avg = sum(by_diff[diff]) / len(by_diff[diff])
            count = len(by_diff[diff])
            print(f"  {diff.capitalize():<8}: {avg:.2f}/5.0 (n={count})")
    
    # Worst performing
    worst = sorted(all_scores, key=lambda x: x[2])[:5]
    print(f"\n🔴 Worst 5 Combinations:")
    for cat, diff, score in worst:
        print(f"  {cat:<20} {diff:<10} {score:.2f}/5.0")
    
    # Best performing
    best = sorted(all_scores, key=lambda x: x[2], reverse=True)[:5]
    print(f"\n🟢 Best 5 Combinations:")
    for cat, diff, score in best:
        print(f"  {cat:<20} {diff:<10} {score:.2f}/5.0")
    
    print("\n" + "="*110)


def main():
    # Path to evaluation results
    results_file = os.path.join(os.path.dirname(__file__), "..", "results", "eval_results.txt")
    
    if not os.path.exists(results_file):
        print(f"❌ Error: Evaluation results not found at {results_file}")
        print("Please run the evaluation harness first: python evaluation/eval_harness.py")
        return
    
    print("\n🔥 Generating Failure Heat Map...")
    print("Analyzing evaluation results...")
    
    # Parse results
    scores = parse_eval_results(results_file)
    
    # Calculate averages
    averages = calculate_averages(scores)
    
    # Create heat map
    priority_list, heat_map_table = create_heat_map(averages)
    
    # Generate priority list
    generate_priority_list(priority_list)
    
    # Statistical summary
    generate_statistical_summary(averages)
    
    # Save to files
    output_dir = os.path.join(os.path.dirname(__file__))
    os.makedirs(output_dir, exist_ok=True)
    
    # Save JSON data
    json_file = os.path.join(output_dir, "heat_map_data.json")
    heat_map_data = {
        "averages": {cat: dict(diffs) for cat, diffs in averages.items()},
        "priority_list": priority_list,
        "heat_map_table": heat_map_table,
        "metadata": {
            "total_combinations": sum(len(d) for d in averages.values()),
            "categories": len(averages),
            "difficulties": list(set(d for diffs in averages.values() for d in diffs.keys()))
        }
    }
    
    with open(json_file, 'w') as f:
        json.dump(heat_map_data, f, indent=2)
    
    print(f"\n💾 Heat map data (JSON) saved to: {json_file}")
    
    # Save markdown heat map
    save_heat_map_to_file(heat_map_table, priority_list, output_dir)
    
    print("\n✅ Analysis complete!\n")


if __name__ == "__main__":
    main()
