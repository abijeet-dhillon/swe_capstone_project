[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=20510468&assignment_repo_type=AssignmentRepo)

# Capstone Project Team 14: Document & Repository Analysis System

A comprehensive system for analyzing code repositories and documents with **AI-powered insights**. Supports **35+ file formats**, Git repository analysis, contributor skill detection, code quality metrics, and zip file processing.

**✅ Status**: Core features implemented and tested | **Test Results**: [TEST_RESULTS.md](TEST_RESULTS.md)

## 🚀 Key Features

- **📚 Document Summarization**: Extract and summarize 35+ file formats using OpenAI
- **🔬 Git Repository Analysis**: Comprehensive metrics on commits, contributors, and code
- **🎯 Contributor Skill Detection**: Automatically detect programming languages, frameworks, and expertise
- **📊 Code Quality Metrics**: Analyze code quality with scoring and recommendations
- **📦 Zip File Processing**: Extract and analyze entire project archives
- **🤖 AI-Powered Insights**: Generate intelligent summaries and contributor analysis

## 📁 Project Structure 

```
.
├── docs/                   # Documentation files
│   ├── contract/          # Team contract
│   ├── proposal/          # Project proposal 
│   ├── design/            # UI mocks
│   ├── minutes/           # Minutes from team meetings
│   ├── logs/              # Team and individual logs
│   └── plan/              # Project plan and UML
├── src/                   # Source code (IMPLEMENTED)
│   ├── analyzers/         # Git & code quality analyzers
│   ├── llm/               # OpenAI integration
│   ├── parsers/           # Document parsers (35+ formats)
│   ├── services/          # Analysis & report services
│   ├── utils/             # Zip handling utilities
│   ├── test_*.py          # Test scripts
│   └── README.md          # Detailed documentation
├── tests/                 # Automated tests 
├── TEST_RESULTS.md        # Test execution results ✅
└── README.md              # This file
```

## 🎯 Quick Start

### Installation
```bash
cd src
pip3 install -r requirements.txt
cp env.example .env
# Edit .env and add your OpenAI API key
```

### Usage Examples

**Document Summarization**:
```bash
python3 test_summarization.py document.pdf
```

**Repository Analysis**:
```bash
python3 test_repository_analysis.py --repo . --ai
```

**Zip File Analysis**:
```bash
python3 test_repository_analysis.py --zip project.zip --ai --output report.txt
```

See [src/README.md](src/README.md) for comprehensive documentation.

## ✅ Test Results

**Status**: All core features tested and passing

- ✅ **35 file formats** supported and working
- ✅ **Document parsing** tested (1,231 words from .docx)
- ✅ **AI summarization** verified with OpenAI
- ✅ **Git analysis** tested on this repository (60 commits, 9 contributors)
- ✅ **Contributor skills** automatically detected
- ✅ **Code quality** analysis functional (17 files analyzed)
- ✅ **Report generation** working with formatted output

See [TEST_RESULTS.md](TEST_RESULTS.md) for detailed results.

## 📊 Supported File Types

**Documents**: `.docx`, `.pdf`, `.rtf`, `.txt`, `.md`  
**Presentations**: `.pptx`  
**Spreadsheets**: `.csv`, `.xlsx`, `.xls`  
**Code**: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.go`, `.rs`, `.rb`, `.php`, and more  
**Markup**: `.html`, `.xml`, `.json`, `.yaml`

## 🔬 What Gets Analyzed

### Repository Metrics
- Total commits, branches, contributors
- File type distribution
- Commit timeline and patterns

### Contributor Analysis
- Programming languages used (with percentages)
- Frameworks and technologies detected
- Work areas (Frontend, Backend, Testing, DevOps)
- Activity levels and quality metrics
- Lines added/deleted per contributor

### Code Quality
- Comment ratios
- Code complexity indicators
- Code smell detection
- Quality scoring (0-100)

## 👥 Team

**Team Number**: 14  
**Members**: Tahsin Jawwad, Abijeet Dhillon, Abdur Rehman, Abhinav Malik, Kaiden Merchant, Misha Gavura

## 📚 Documentation

- [src/README.md](src/README.md) - Comprehensive feature documentation
- [TEST_RESULTS.md](TEST_RESULTS.md) - Test execution results
- [src/TESTING.md](src/TESTING.md) - Testing guide
- [docs/plan/README.md](docs/plan/README.md) - Project plan and requirements

## 🔄 Development Workflow

Please use a branching workflow:
1. Create feature branch
2. Implement and test
3. Issue a PR for review
4. Merge into develop/main branch

Keep docs and README.md up-to-date.
