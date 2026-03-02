#!/bin/bash
# Test script for filter API endpoints

BASE_URL="http://localhost:8000"

echo "=== Testing Filter API ==="
echo ""

echo "1. Get filter options"
curl -s "$BASE_URL/filter/options" | python -m json.tool
echo ""

echo "2. Search projects"
curl -s "$BASE_URL/filter/search?q=test&limit=5" | python -m json.tool
echo ""

echo "3. Filter projects (all)"
curl -s -X POST "$BASE_URL/filter/" \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}' | python -m json.tool
echo ""

echo "4. Filter by metrics (>100 LOC)"
curl -s -X POST "$BASE_URL/filter/" \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": {"min_lines": 100},
    "sort_by": "loc_desc",
    "limit": 3
  }' | python -m json.tool
echo ""

echo "5. Save a filter preset"
curl -s -X POST "$BASE_URL/filter/presets" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Large Projects",
    "description": "Projects with more than 1000 lines",
    "filter_config": {
      "metrics": {"min_lines": 1000},
      "sort_by": "loc_desc"
    }
  }' | python -m json.tool
echo ""

echo "6. List all presets"
curl -s "$BASE_URL/filter/presets" | python -m json.tool
echo ""

echo "✓ API tests complete!"
