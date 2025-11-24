"""
Unit tests for presentation module (portfolio and resume generation)
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from src.project.presentation import (
    extract_project_metrics,
    generate_portfolio_item,
    generate_resume_item,
    PortfolioItem,
    ResumeItem,
    ProjectMetrics
)


class TestProjectMetrics:
    """Test ProjectMetrics dataclass"""
    
    def test_project_metrics_initialization(self):
        """Test that ProjectMetrics initializes with defaults"""
        metrics = ProjectMetrics()
        
        assert metrics.languages == []
        assert metrics.frameworks == []
        assert metrics.skills == []
        assert metrics.total_files == 0
        assert metrics.total_lines == 0
        assert metrics.total_commits == 0
        assert metrics.total_contributors == 0
        assert metrics.is_collaborative is False
    
    def test_project_metrics_with_values(self):
        """Test that ProjectMetrics can be initialized with values"""
        metrics = ProjectMetrics(
            languages=["Python", "JavaScript"],
            frameworks=["Flask", "React"],
            skills=["REST API", "Frontend"],
            total_files=50,
            total_lines=5000,
            total_commits=100,
            total_contributors=3,
            is_collaborative=True
        )
        
        assert metrics.languages == ["Python", "JavaScript"]
        assert metrics.frameworks == ["Flask", "React"]
        assert metrics.skills == ["REST API", "Frontend"]
        assert metrics.total_files == 50
        assert metrics.total_lines == 5000
        assert metrics.total_commits == 100
        assert metrics.total_contributors == 3
        assert metrics.is_collaborative is True


class TestExtractProjectMetrics:
    """Test extract_project_metrics helper function"""
    
    def test_extract_metrics_from_full_project_dict(self):
        """Test extraction from a fully populated project dict"""
        project_dict = {
            "project_name": "test-project",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["Python", "JavaScript", "TypeScript"],
                        "frameworks": ["Django", "React", "pytest"],
                        "skills": ["REST API", "Database Design", "Unit Testing"],
                        "total_files": 42,
                        "total_lines": 3500
                    }
                }
            },
            "git_analysis": {
                "total_commits": 150,
                "total_contributors": 4
            }
        }
        
        metrics = extract_project_metrics(project_dict)
        
        assert metrics.languages == ["Python", "JavaScript", "TypeScript"]
        assert metrics.frameworks == ["Django", "React", "pytest"]
        assert metrics.skills == ["REST API", "Database Design", "Unit Testing"]
        assert metrics.total_files == 42
        assert metrics.total_lines == 3500
        assert metrics.total_commits == 150
        assert metrics.total_contributors == 4
        assert metrics.is_collaborative is True  # > 1 contributor
    
    def test_extract_metrics_individual_project(self):
        """Test that is_collaborative is False when only 1 contributor"""
        project_dict = {
            "git_analysis": {
                "total_commits": 50,
                "total_contributors": 1
            }
        }
        
        metrics = extract_project_metrics(project_dict)
        
        assert metrics.total_commits == 50
        assert metrics.total_contributors == 1
        assert metrics.is_collaborative is False
    
    def test_extract_metrics_missing_analysis_results(self):
        """Test extraction when analysis_results is missing"""
        project_dict = {
            "project_name": "test-project",
            "git_analysis": {
                "total_commits": 20,
                "total_contributors": 2
            }
        }
        
        metrics = extract_project_metrics(project_dict)
        
        # Code metrics should be defaults
        assert metrics.languages == []
        assert metrics.frameworks == []
        assert metrics.skills == []
        assert metrics.total_files == 0
        assert metrics.total_lines == 0
        
        # Git metrics should be present
        assert metrics.total_commits == 20
        assert metrics.total_contributors == 2
        assert metrics.is_collaborative is True
    
    def test_extract_metrics_missing_git_analysis(self):
        """Test extraction when git_analysis is missing"""
        project_dict = {
            "project_name": "test-project",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["Java"],
                        "frameworks": ["Spring"],
                        "skills": ["OOP"],
                        "total_files": 10,
                        "total_lines": 1000
                    }
                }
            }
        }
        
        metrics = extract_project_metrics(project_dict)
        
        # Code metrics should be present
        assert metrics.languages == ["Java"]
        assert metrics.frameworks == ["Spring"]
        assert metrics.skills == ["OOP"]
        assert metrics.total_files == 10
        assert metrics.total_lines == 1000
        
        # Git metrics should be defaults
        assert metrics.total_commits == 0
        assert metrics.total_contributors == 0
        assert metrics.is_collaborative is False
    
    def test_extract_metrics_completely_empty_dict(self):
        """Test extraction from an empty dict"""
        project_dict = {}
        
        metrics = extract_project_metrics(project_dict)
        
        # Should return all defaults without crashing
        assert metrics.languages == []
        assert metrics.frameworks == []
        assert metrics.skills == []
        assert metrics.total_files == 0
        assert metrics.total_lines == 0
        assert metrics.total_commits == 0
        assert metrics.total_contributors == 0
        assert metrics.is_collaborative is False
    
    def test_extract_metrics_with_code_error(self):
        """Test extraction when code analysis has error"""
        project_dict = {
            "analysis_results": {
                "code": {
                    "error": "Analysis failed"
                }
            },
            "git_analysis": {
                "total_commits": 10,
                "total_contributors": 1
            }
        }
        
        metrics = extract_project_metrics(project_dict)
        
        # Code metrics should be defaults (error present)
        assert metrics.languages == []
        assert metrics.frameworks == []
        assert metrics.skills == []
        assert metrics.total_files == 0
        assert metrics.total_lines == 0
        
        # Git metrics should still be extracted
        assert metrics.total_commits == 10
        assert metrics.total_contributors == 1
    
    def test_extract_metrics_with_git_error(self):
        """Test extraction when git analysis has error"""
        project_dict = {
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["Python"],
                        "frameworks": [],
                        "skills": [],
                        "total_files": 5,
                        "total_lines": 500
                    }
                }
            },
            "git_analysis": {
                "error": "Git failed"
            }
        }
        
        metrics = extract_project_metrics(project_dict)
        
        # Code metrics should be present
        assert metrics.languages == ["Python"]
        assert metrics.total_files == 5
        assert metrics.total_lines == 500
        
        # Git metrics should be defaults (error present)
        assert metrics.total_commits == 0
        assert metrics.total_contributors == 0
        assert metrics.is_collaborative is False
    
    def test_extract_metrics_partial_code_metrics(self):
        """Test extraction when code metrics is partially populated"""
        project_dict = {
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["Ruby"],
                        "total_files": 15
                        # Missing frameworks, skills, total_lines
                    }
                }
            }
        }
        
        metrics = extract_project_metrics(project_dict)
        
        assert metrics.languages == ["Ruby"]
        assert metrics.total_files == 15
        # Missing fields should have defaults
        assert metrics.frameworks == []
        assert metrics.skills == []
        assert metrics.total_lines == 0


class TestGeneratePortfolioItem:
    """Test generate_portfolio_item function"""
    
    def test_generate_portfolio_item_happy_path(self):
        """Test portfolio generation with full metrics"""
        project_dict = {
            "project_name": "E-Commerce Platform",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["Python", "JavaScript"],
                        "frameworks": ["Django", "React", "PostgreSQL"],
                        "skills": ["REST API", "Authentication", "Payment Integration"],
                        "total_files": 85,
                        "total_lines": 7500
                    }
                }
            },
            "git_analysis": {
                "total_commits": 200,
                "total_contributors": 3
            }
        }
        
        result = generate_portfolio_item(project_dict)
        
        # Check structure
        assert isinstance(result, dict)
        assert "project_name" in result
        assert "tagline" in result
        assert "description" in result
        assert "languages" in result
        assert "frameworks" in result
        assert "skills" in result
        assert "is_collaborative" in result
        assert "total_commits" in result
        assert "total_lines" in result
        
        # Check values
        assert result["project_name"] == "E-Commerce Platform"
        assert result["languages"] == ["Python", "JavaScript"]
        assert result["frameworks"] == ["Django", "React", "PostgreSQL"]
        assert result["skills"] == ["REST API", "Authentication", "Payment Integration"]
        assert result["is_collaborative"] is True
        assert result["total_commits"] == 200
        assert result["total_lines"] == 7500
        
        # Check generated fields
        assert isinstance(result["tagline"], str)
        assert len(result["tagline"]) > 0
        assert "Collaborative" in result["tagline"]
        
        assert isinstance(result["description"], str)
        assert len(result["description"]) > 0
        assert "85 source files" in result["description"]
        assert "7,500 lines of code" in result["description"]
    
    def test_generate_portfolio_item_individual_project(self):
        """Test portfolio generation for individual project"""
        project_dict = {
            "project_name": "Personal Blog",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["Python"],
                        "frameworks": ["Flask"],
                        "skills": ["Web Development"],
                        "total_files": 20,
                        "total_lines": 1500
                    }
                }
            },
            "git_analysis": {
                "total_commits": 50,
                "total_contributors": 1
            }
        }
        
        result = generate_portfolio_item(project_dict)
        
        assert result["project_name"] == "Personal Blog"
        assert result["is_collaborative"] is False
        assert "Individual" in result["tagline"]
    
    def test_generate_portfolio_item_minimal_metrics(self):
        """Test portfolio generation with minimal/missing metrics"""
        project_dict = {
            "project_name": "Simple Script"
        }
        
        result = generate_portfolio_item(project_dict)
        
        # Should still return valid structure
        assert isinstance(result, dict)
        assert result["project_name"] == "Simple Script"
        assert isinstance(result["tagline"], str)
        assert len(result["tagline"]) > 0
        assert isinstance(result["description"], str)
        assert len(result["description"]) > 0
        assert result["languages"] == []
        assert result["frameworks"] == []
        assert result["skills"] == []
        assert result["is_collaborative"] is False
        assert result["total_commits"] == 0
        assert result["total_lines"] == 0
    
    def test_generate_portfolio_item_unnamed_project(self):
        """Test portfolio generation when project_name is missing"""
        project_dict = {}
        
        result = generate_portfolio_item(project_dict)
        
        assert result["project_name"] == "Unnamed Project"
        assert isinstance(result["tagline"], str)
        assert isinstance(result["description"], str)
    
    def test_generate_portfolio_item_truncates_long_lists(self):
        """Test that long lists are truncated appropriately"""
        project_dict = {
            "project_name": "Large Project",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": [f"Lang{i}" for i in range(20)],
                        "frameworks": [f"Framework{i}" for i in range(20)],
                        "skills": [f"Skill{i}" for i in range(25)],
                        "total_files": 100,
                        "total_lines": 10000
                    }
                }
            }
        }
        
        result = generate_portfolio_item(project_dict)
        
        # Lists should be truncated
        assert len(result["languages"]) <= 10
        assert len(result["frameworks"]) <= 10
        assert len(result["skills"]) <= 15
    
    def test_generate_portfolio_item_tagline_variations(self):
        """Test tagline generation with different language/framework combos"""
        # Single language, single framework
        project_dict1 = {
            "project_name": "Test1",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["Python"],
                        "frameworks": ["Django"],
                        "skills": [],
                        "total_files": 10,
                        "total_lines": 1000
                    }
                }
            },
            "git_analysis": {
                "total_commits": 10,
                "total_contributors": 1
            }
        }
        
        result1 = generate_portfolio_item(project_dict1)
        assert "Python" in result1["tagline"]
        assert "Django" in result1["tagline"]
        assert "Individual" in result1["tagline"]
        
        # Multiple languages, no frameworks
        project_dict2 = {
            "project_name": "Test2",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["JavaScript", "TypeScript", "CSS"],
                        "frameworks": [],
                        "skills": [],
                        "total_files": 10,
                        "total_lines": 1000
                    }
                }
            }
        }
        
        result2 = generate_portfolio_item(project_dict2)
        assert "multi-language" in result2["tagline"]


class TestGenerateResumeItem:
    """Test generate_resume_item function"""
    
    def test_generate_resume_item_happy_path(self):
        """Test resume generation with full metrics"""
        project_dict = {
            "project_name": "Mobile App",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["Swift", "Kotlin"],
                        "frameworks": ["UIKit", "Jetpack Compose"],
                        "skills": ["Mobile Development", "RESTful APIs", "Push Notifications"],
                        "total_files": 60,
                        "total_lines": 5000
                    }
                }
            },
            "git_analysis": {
                "total_commits": 120,
                "total_contributors": 2
            }
        }
        
        result = generate_resume_item(project_dict)
        
        # Check structure
        assert isinstance(result, dict)
        assert "project_name" in result
        assert "bullets" in result
        
        # Check values
        assert result["project_name"] == "Mobile App"
        assert isinstance(result["bullets"], list)
        assert len(result["bullets"]) >= 2
        assert len(result["bullets"]) <= 3
        
        # Check that all bullets are non-empty strings
        for bullet in result["bullets"]:
            assert isinstance(bullet, str)
            assert len(bullet) > 0
            assert bullet.endswith(".")
        
        # Check content - should mention collaboration, languages, skills
        bullets_text = " ".join(result["bullets"])
        assert "Swift" in bullets_text or "Kotlin" in bullets_text
        assert "120 commits" in bullets_text or "2 contributors" in bullets_text
        assert any(skill in bullets_text for skill in ["Mobile Development", "RESTful APIs", "Push Notifications"])
    
    def test_generate_resume_item_individual_project(self):
        """Test resume generation for individual project"""
        project_dict = {
            "project_name": "CLI Tool",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["Go"],
                        "frameworks": ["Cobra"],
                        "skills": ["Command Line", "File Processing"],
                        "total_files": 15,
                        "total_lines": 1200
                    }
                }
            },
            "git_analysis": {
                "total_commits": 40,
                "total_contributors": 1
            }
        }
        
        result = generate_resume_item(project_dict)
        
        assert result["project_name"] == "CLI Tool"
        assert len(result["bullets"]) >= 2
        
        bullets_text = " ".join(result["bullets"])
        assert "Developed" in bullets_text
        assert "Go" in bullets_text
        assert "40" in bullets_text or "Git" in bullets_text
    
    def test_generate_resume_item_minimal_metrics(self):
        """Test resume generation with minimal metrics"""
        project_dict = {
            "project_name": "Minimal Project"
        }
        
        result = generate_resume_item(project_dict)
        
        # Should still return valid structure
        assert isinstance(result, dict)
        assert result["project_name"] == "Minimal Project"
        assert isinstance(result["bullets"], list)
        assert len(result["bullets"]) >= 1
        
        # All bullets should be valid
        for bullet in result["bullets"]:
            assert isinstance(bullet, str)
            assert len(bullet) > 0
    
    def test_generate_resume_item_no_git_data(self):
        """Test resume generation without Git data"""
        project_dict = {
            "project_name": "No Git Project",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["Ruby"],
                        "frameworks": ["Rails"],
                        "skills": ["MVC", "Database"],
                        "total_files": 30,
                        "total_lines": 3000
                    }
                }
            }
        }
        
        result = generate_resume_item(project_dict)
        
        assert result["project_name"] == "No Git Project"
        assert len(result["bullets"]) >= 2
        
        # Should still have valid bullets with generic statements
        bullets_text = " ".join(result["bullets"])
        assert "Ruby" in bullets_text
        assert "MVC" in bullets_text or "Database" in bullets_text
    
    def test_generate_resume_item_collaborative_project(self):
        """Test resume bullets emphasize collaboration"""
        project_dict = {
            "project_name": "Team Project",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["Java"],
                        "frameworks": ["Spring Boot"],
                        "skills": ["Microservices"],
                        "total_files": 50,
                        "total_lines": 4000
                    }
                }
            },
            "git_analysis": {
                "total_commits": 300,
                "total_contributors": 5
            }
        }
        
        result = generate_resume_item(project_dict)
        
        bullets_text = " ".join(result["bullets"])
        assert "Collaborated" in bullets_text or "contributors" in bullets_text
        assert "5 contributors" in bullets_text
        assert "300 commits" in bullets_text
    
    def test_generate_resume_item_unnamed_project(self):
        """Test resume generation when project_name is missing"""
        project_dict = {}
        
        result = generate_resume_item(project_dict)
        
        assert result["project_name"] == "Unnamed Project"
        assert isinstance(result["bullets"], list)
        assert len(result["bullets"]) >= 1
    
    def test_generate_resume_item_skills_formatting(self):
        """Test that skills are formatted nicely in bullets"""
        # Test with 2 skills
        project_dict1 = {
            "project_name": "Test1",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["Python"],
                        "frameworks": [],
                        "skills": ["Skill1", "Skill2"],
                        "total_files": 10,
                        "total_lines": 1000
                    }
                }
            }
        }
        
        result1 = generate_resume_item(project_dict1)
        bullets_text1 = " ".join(result1["bullets"])
        assert "Skill1 and Skill2" in bullets_text1
        
        # Test with 3+ skills
        project_dict2 = {
            "project_name": "Test2",
            "analysis_results": {
                "code": {
                    "metrics": {
                        "languages": ["JavaScript"],
                        "frameworks": [],
                        "skills": ["SkillA", "SkillB", "SkillC"],
                        "total_files": 10,
                        "total_lines": 1000
                    }
                }
            }
        }
        
        result2 = generate_resume_item(project_dict2)
        bullets_text2 = " ".join(result2["bullets"])
        # Should have comma-separated list
        assert "SkillA" in bullets_text2
        assert "SkillB" in bullets_text2
        assert "SkillC" in bullets_text2


class TestPortfolioItemDataclass:
    """Test PortfolioItem dataclass"""
    
    def test_portfolio_item_creation(self):
        """Test PortfolioItem can be created"""
        item = PortfolioItem(
            project_name="Test",
            tagline="Test tagline",
            description="Test description"
        )
        
        assert item.project_name == "Test"
        assert item.tagline == "Test tagline"
        assert item.description == "Test description"
        assert item.languages == []
        assert item.frameworks == []
        assert item.skills == []
        assert item.is_collaborative is False
        assert item.total_commits == 0
        assert item.total_lines == 0
    
    def test_portfolio_item_to_dict(self):
        """Test PortfolioItem.to_dict() method"""
        item = PortfolioItem(
            project_name="Test",
            tagline="Tagline",
            description="Description",
            languages=["Python"],
            frameworks=["Django"],
            skills=["REST"],
            is_collaborative=True,
            total_commits=50,
            total_lines=2000
        )
        
        result = item.to_dict()
        
        assert isinstance(result, dict)
        assert result["project_name"] == "Test"
        assert result["tagline"] == "Tagline"
        assert result["description"] == "Description"
        assert result["languages"] == ["Python"]
        assert result["frameworks"] == ["Django"]
        assert result["skills"] == ["REST"]
        assert result["is_collaborative"] is True
        assert result["total_commits"] == 50
        assert result["total_lines"] == 2000


class TestResumeItemDataclass:
    """Test ResumeItem dataclass"""
    
    def test_resume_item_creation(self):
        """Test ResumeItem can be created"""
        item = ResumeItem(
            project_name="Test",
            bullets=["Bullet 1", "Bullet 2"]
        )
        
        assert item.project_name == "Test"
        assert item.bullets == ["Bullet 1", "Bullet 2"]
    
    def test_resume_item_to_dict(self):
        """Test ResumeItem.to_dict() method"""
        item = ResumeItem(
            project_name="Test",
            bullets=["First bullet", "Second bullet", "Third bullet"]
        )
        
        result = item.to_dict()
        
        assert isinstance(result, dict)
        assert result["project_name"] == "Test"
        assert result["bullets"] == ["First bullet", "Second bullet", "Third bullet"]

