#!/usr/bin/env python3
"""
Quick script to check if a project is Individual or Collaborative
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.repository_analysis_service import RepositoryAnalysisService

def main():
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        repo_path = ".."  # Default to parent directory
    
    print(f"Analyzing repository: {repo_path}")
    print("-" * 50)
    
    try:
        service = RepositoryAnalysisService(api_key=None)
        results = service.analyze_repository(
            repo_path, 
            analyze_code_quality=False, 
            generate_ai_summary=False
        )
        
        repo = results['repository_analysis']
        contributor_count = repo.get('contributor_count', 0)
        
        print("\n" + "=" * 50)
        if contributor_count > 1:
            print("✅ Project Type: COLLABORATIVE")
            print(f"   Contributors: {contributor_count}")
        else:
            print("✅ Project Type: INDIVIDUAL")
            print(f"   Contributors: {contributor_count}")
        print("=" * 50)
        
        # Show contributor names
        contributors = repo.get('contributors', [])
        if contributors:
            print("\nContributors:")
            for i, contrib in enumerate(contributors[:5], 1):  # Show first 5
                print(f"  {i}. {contrib.get('name', 'Unknown')}")
            if len(contributors) > 5:
                print(f"  ... and {len(contributors) - 5} more")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

