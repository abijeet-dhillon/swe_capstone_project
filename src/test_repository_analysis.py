"""
Test script for repository and zip file analysis.
Demonstrates comprehensive Git repository analysis with contributor insights.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from services.repository_analysis_service import RepositoryAnalysisService
from services.report_generator import ReportGenerator
from save_repository_to_db import convert_repo_analysis_to_pipeline_format
from insights.storage import ProjectInsightsStore


def analyze_repository(repo_path: str, with_ai: bool = False, output_file: str = None):
    """
    Analyze a Git repository and generate a comprehensive report.
    
    Args:
        repo_path: Path to Git repository
        with_ai: Whether to include AI-powered insights
        output_file: Optional path to save report
    """
    print("\n" + "="*70)
    print("🔬 Repository Analysis Tool")
    print("="*70)
    
    # Check if repo exists
    if not Path(repo_path).exists():
        print(f"\n❌ Error: Repository not found: {repo_path}")
        return
    
    # Check if it's a Git repository
    if not (Path(repo_path) / ".git").exists():
        print(f"\n❌ Error: Not a Git repository: {repo_path}")
        print("   (Missing .git directory)")
        return
    
    # Check API key if AI is requested
    if with_ai:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("\n⚠️  Warning: OPENAI_API_KEY not found.")
            print("   AI-powered insights will be skipped.")
            print("   Set up your .env file to enable AI features.")
            with_ai = False
    
    try:
        # Initialize service
        service = RepositoryAnalysisService(
            api_key=os.getenv("OPENAI_API_KEY") if with_ai else None
        )
        
        # Perform analysis
        results = service.analyze_repository(
            repo_path,
            analyze_code_quality=True,
            generate_ai_summary=with_ai
        )
        
        # Generate report
        print("\n📝 Generating report...")
        report = ReportGenerator.generate_text_report(results)
        
        # Display report
        print("\n" + "="*70)
        print(report)
        print("="*70)
        
        # Save report if requested
        if output_file:
            report_path = ReportGenerator.save_report(report, output_file, format='txt')
            print(f"\n💾 Report saved to: {report_path}")
            
            # Also save JSON
            json_report = ReportGenerator.generate_json_report(results)
            json_path = str(Path(output_file).with_suffix('.json'))
            ReportGenerator.save_report(json_report, json_path, format='json')
            print(f"💾 JSON report saved to: {json_path}")
        
        # Automatically save to database
        print("\n💾 Saving to database...")
        try:
            pipeline_result = convert_repo_analysis_to_pipeline_format(repo_path, results)
            store = ProjectInsightsStore()
            stats = store.record_pipeline_run(
                zip_path=repo_path,
                pipeline_result=pipeline_result,
                pipeline_version="repository-analysis/v1"
            )
            print(f"   ✓ Saved to database ({stats.project_count} project(s), "
                  f"{stats.inserted} inserted, {stats.updated} updated)")
        except Exception as db_error:
            print(f"   ⚠️  Warning: Could not save to database: {db_error}")
        
        print("\n✅ Analysis complete!")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


def analyze_zip(zip_path: str, with_ai: bool = False, output_file: str = None):
    """
    Extract and analyze a zip file (repository or documents).
    
    Args:
        zip_path: Path to zip file
        with_ai: Whether to include AI-powered insights
        output_file: Optional path to save report
    """
    print("\n" + "="*70)
    print("📦 Zip File Analysis Tool")
    print("="*70)
    
    # Check if zip exists
    if not Path(zip_path).exists():
        print(f"\n❌ Error: Zip file not found: {zip_path}")
        return
    
    # Check API key if AI is requested
    if with_ai:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("\n⚠️  Warning: OPENAI_API_KEY not found.")
            print("   AI-powered insights will be skipped.")
            with_ai = False
    
    try:
        # Initialize service
        service = RepositoryAnalysisService(
            api_key=os.getenv("OPENAI_API_KEY") if with_ai else None
        )
        
        # Analyze zip
        results = service.analyze_zip_file(
            zip_path,
            analyze_code_quality=True,
            generate_ai_summary=with_ai
        )
        
        # Generate report
        print("\n📝 Generating report...")
        report = ReportGenerator.generate_text_report(results)
        
        # Display report
        print("\n" + "="*70)
        print(report)
        print("="*70)
        
        # Save report if requested
        if output_file:
            report_path = ReportGenerator.save_report(report, output_file, format='txt')
            print(f"\n💾 Report saved to: {report_path}")
            
            # Also save JSON
            json_report = ReportGenerator.generate_json_report(results)
            json_path = str(Path(output_file).with_suffix('.json'))
            ReportGenerator.save_report(json_report, json_path, format='json')
            print(f"💾 JSON report saved to: {json_path}")
        
        # Automatically save to database (if repository analysis exists)
        if 'repository_analysis' in results:
            print("\n💾 Saving to database...")
            try:
                # Try to find extracted repo path
                extracted_path = results.get('extracted_path', zip_path)
                pipeline_result = convert_repo_analysis_to_pipeline_format(extracted_path, results)
                store = ProjectInsightsStore()
                stats = store.record_pipeline_run(
                    zip_path=zip_path,
                    pipeline_result=pipeline_result,
                    pipeline_version="repository-analysis/v1"
                )
                print(f"   ✓ Saved to database ({stats.project_count} project(s), "
                      f"{stats.inserted} inserted, {stats.updated} updated)")
            except Exception as db_error:
                print(f"   ⚠️  Warning: Could not save to database: {db_error}")
        
        print("\n✅ Analysis complete!")
        
        # Cleanup
        service.cleanup()
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze Git repositories or zip files with comprehensive contributor insights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a Git repository
  python test_repository_analysis.py --repo /path/to/repo
  
  # Analyze with AI insights (requires OPENAI_API_KEY)
  python test_repository_analysis.py --repo /path/to/repo --ai
  
  # Analyze a zip file containing a repository
  python test_repository_analysis.py --zip /path/to/repo.zip
  
  # Save report to file
  python test_repository_analysis.py --repo /path/to/repo --output report.txt
  
  # Analyze current directory
  python test_repository_analysis.py --repo .
        """
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        help='Path to Git repository'
    )
    
    parser.add_argument(
        '--zip',
        type=str,
        help='Path to zip file containing repository or documents'
    )
    
    parser.add_argument(
        '--ai',
        action='store_true',
        help='Generate AI-powered insights (requires OPENAI_API_KEY)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Path to save the report (optional)'
    )
    
    args = parser.parse_args()
    
    if not args.repo and not args.zip:
        parser.print_help()
        print("\n❌ Error: Please specify either --repo or --zip")
        sys.exit(1)
    
    if args.repo and args.zip:
        print("❌ Error: Please specify only one of --repo or --zip")
        sys.exit(1)
    
    # Run analysis
    if args.repo:
        analyze_repository(args.repo, with_ai=args.ai, output_file=args.output)
    elif args.zip:
        analyze_zip(args.zip, with_ai=args.ai, output_file=args.output)


if __name__ == "__main__":
    main()



