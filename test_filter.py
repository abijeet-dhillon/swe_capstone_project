"""Quick test script for project filtering."""
from src.insights.project_filter import ProjectFilterEngine, ProjectFilter, SortBy, ProjectType

# Initialize the filter engine
engine = ProjectFilterEngine("data/app.db")

# Test 1: List all projects
print("=== All Projects ===")
all_projects = engine.apply_filter(ProjectFilter())
print(f"Found {len(all_projects)} projects")
for p in all_projects[:3]:
    print(f"  - {p['project_name']} ({p['total_lines']} LOC, {p['total_commits']} commits)")

# Test 2: Search by text
print("\n=== Search Test ===")
results = engine.search_projects("test", limit=5)
print(f"Search 'test' found {len(results)} projects")

# Test 3: Filter by metrics
print("\n=== Filter by LOC > 100 ===")
from src.insights.project_filter import SuccessMetrics
filter_config = ProjectFilter(
    metrics=SuccessMetrics(min_lines=100),
    sort_by=SortBy.LOC_DESC,
    limit=5
)
filtered = engine.apply_filter(filter_config)
print(f"Found {len(filtered)} projects with >100 LOC")

print("\n✓ Filtering system works!")

