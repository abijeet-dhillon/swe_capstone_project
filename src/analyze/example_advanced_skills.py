"""
Example usage of Advanced Skill Extractor
Demonstrates local, library-based skill extraction without AI/LLM
"""

from pathlib import Path
from advanced_skill_extractor import AdvancedSkillExtractor, DeepSkillAnalysis
import json


def analyze_single_file_example():
    """Example: Analyze a single file"""
    print("=" * 60)
    print("EXAMPLE 1: Single File Analysis")
    print("=" * 60)
    
    extractor = AdvancedSkillExtractor()
    
    # Analyze the code_analyzer.py file
    file_path = Path(__file__).parent / 'code_analyzer.py'
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
    
    analysis = extractor.analyze_file(file_path)
    
    print(f"\nFile: {analysis.file_path}")
    print(f"\nBasic Skills: {', '.join(analysis.basic_skills) if analysis.basic_skills else 'None'}")
    print(f"\nAdvanced Skills: {', '.join(analysis.advanced_skills) if analysis.advanced_skills else 'None'}")
    print(f"\nDesign Patterns: {', '.join(analysis.design_patterns) if analysis.design_patterns else 'None'}")
    
    if analysis.complexity_insights:
        print(f"\nComplexity Insights:")
        for key, value in analysis.complexity_insights.items():
            print(f"  - {key}: {value}")
    
    print(f"\nEvidence Found: {len(analysis.evidence)} items")
    for i, evidence in enumerate(analysis.evidence[:5], 1):  # Show first 5
        print(f"\n  {i}. {evidence.skill} (confidence: {evidence.confidence:.0%})")
        print(f"     Location: {evidence.location}")
        print(f"     Reasoning: {evidence.reasoning}")


def analyze_directory_example():
    """Example: Analyze entire directory"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 2: Directory Analysis")
    print("=" * 60)
    
    extractor = AdvancedSkillExtractor()
    
    # Analyze the entire src/analyze directory
    analyze_dir = Path(__file__).parent
    
    print(f"\nAnalyzing directory: {analyze_dir}")
    results = extractor.analyze_directory(analyze_dir)
    
    print(f"\nFiles analyzed: {len(results)}")
    
    # Aggregate skills across all files
    aggregated = extractor.aggregate_skills(results)
    
    print(f"\n--- Aggregated Skills Across All Files ---")
    print(f"\nBasic Skills ({len(aggregated['basic_skills'])}):")
    for skill in aggregated['basic_skills']:
        print(f"  - {skill}")
    
    print(f"\nAdvanced Skills ({len(aggregated['advanced_skills'])}):")
    for skill in aggregated['advanced_skills']:
        count = len(aggregated['evidence_by_skill'].get(skill, []))
        print(f"  - {skill} (found in {count} locations)")
    
    print(f"\nDesign Patterns ({len(aggregated['design_patterns'])}):")
    for pattern in aggregated['design_patterns']:
        count = len(aggregated['evidence_by_skill'].get(pattern, []))
        print(f"  - {pattern} (found in {count} locations)")
    
    print(f"\nTotal Evidence Items: {aggregated['evidence_count']}")


def export_to_json_example():
    """Example: Export analysis to JSON"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 3: Export to JSON")
    print("=" * 60)
    
    extractor = AdvancedSkillExtractor()
    
    # Analyze a file
    file_path = Path(__file__).parent / 'code_analyzer.py'
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
    
    analysis = extractor.analyze_file(file_path)
    
    # Convert to dictionary for JSON export
    result_dict = {
        'file_path': analysis.file_path,
        'basic_skills': analysis.basic_skills,
        'advanced_skills': analysis.advanced_skills,
        'design_patterns': analysis.design_patterns,
        'complexity_insights': analysis.complexity_insights,
        'evidence': [
            {
                'skill': e.skill,
                'evidence_type': e.evidence_type,
                'location': e.location,
                'reasoning': e.reasoning,
                'confidence': e.confidence
            }
            for e in analysis.evidence
        ]
    }
    
    # Print JSON
    json_output = json.dumps(result_dict, indent=2)
    print("\nJSON Output (first 1000 chars):")
    print(json_output[:1000])
    print("...")
    
    # Optionally save to file
    output_path = Path(__file__).parent / 'skill_analysis_output.json'
    with open(output_path, 'w') as f:
        json.dump(result_dict, f, indent=2)
    
    print(f"\nFull output saved to: {output_path}")


def compare_files_example():
    """Example: Compare skill profiles of different files"""
    print("\n\n" + "=" * 60)
    print("EXAMPLE 4: Compare Multiple Files")
    print("=" * 60)
    
    extractor = AdvancedSkillExtractor()
    
    files_to_compare = [
        'code_analyzer.py',
        'text_analyzer.py',
        'video_analyzer.py'
    ]
    
    base_dir = Path(__file__).parent
    
    print("\nComparing skill profiles:\n")
    
    for filename in files_to_compare:
        file_path = base_dir / filename
        
        if not file_path.exists():
            print(f"  {filename}: Not found")
            continue
        
        analysis = extractor.analyze_file(file_path)
        
        total_skills = (
            len(analysis.basic_skills) + 
            len(analysis.advanced_skills) + 
            len(analysis.design_patterns)
        )
        
        print(f"  {filename}:")
        print(f"    Total skills: {total_skills}")
        print(f"    Advanced: {len(analysis.advanced_skills)}")
        print(f"    Patterns: {len(analysis.design_patterns)}")
        print(f"    Evidence: {len(analysis.evidence)}")
        
        if analysis.advanced_skills:
            print(f"    Top skills: {', '.join(analysis.advanced_skills[:3])}")
        print()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("ADVANCED SKILL EXTRACTOR - LOCAL ANALYSIS DEMO")
    print("No AI/LLM - Pure Python AST & Pattern Detection")
    print("=" * 60)
    
    try:
        # Run all examples
        analyze_single_file_example()
        analyze_directory_example()
        export_to_json_example()
        compare_files_example()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
