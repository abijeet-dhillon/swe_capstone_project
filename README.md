[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=20510468&assignment_repo_type=AssignmentRepo)

# Digital Work Artifact Miner
**Team 14 - COSC 499 Capstone Project**

A privacy-first application that scans local folders to mine digital work artifacts (code repositories, documents, media files) and generates professional portfolio summaries powered by AI.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key (get one at https://platform.openai.com/api-keys)

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
cp env.template .env
# Edit .env and add your OpenAI API key

# Run examples
python src/example_usage.py
```

## ✨ Features

### Current (Implemented)
- ✅ **LLM Integration** - OpenAI-powered artifact analysis
  - Code review and quality analysis
  - Git commit history summarization
  - Technical skill extraction
  - Professional portfolio generation
  - Document summarization
  - Project overview generation

### Planned
- 📅 Local file scanning and type detection (R2)
- 📅 Git repository analysis (R3)
- 📅 Office/PDF document parsing (R4)
- 📅 Media/design file metadata extraction (R5)
- 📅 Local database storage (R6)
- 📅 Analytics and insights (R7)
- 📅 REST API endpoints (R8)
- 📅 Export to JSON/CSV/PDF (R10)
- 📅 Privacy/PII redaction (R12)

## 📁 Project Structure

```
.
├── docs/                      # Documentation files
│   ├── LLM_SETUP_GUIDE.md    # Complete setup instructions
│   ├── PROMPT_ENGINEERING_GUIDE.md  # How to customize LLM
│   ├── LLM_ARCHITECTURE.md   # System architecture
│   ├── contract/             # Team contract
│   ├── proposal/             # Project proposal 
│   ├── design/               # UI mocks
│   ├── minutes/              # Minutes from team meetings
│   ├── logs/                 # Team and individual logs
│   └── plan/                 # Project plan & UML
├── src/                      # Source files
│   ├── llm_analyzer.py       # ⭐ LLM integration module
│   ├── example_usage.py      # Usage examples
│   ├── integration_example.py # Integration demos
│   └── QUICKSTART.md         # 5-minute quick start
├── tests/                    # Automated tests
│   └── test_llm_analyzer.py  # LLM module tests
├── utils/                    # Utility files
├── requirements.txt          # Python dependencies
├── env.template              # Environment variable template
├── LLM_INTEGRATION_SUMMARY.md # Complete integration summary
└── README.md                 # This file
```

## 🎯 Use Cases

1. **Configure Scan** - Select folders and set scanning preferences
2. **Run Scan & Ingest** - Enumerate and parse artifacts with AI analysis
3. **View Insights** - Query AI-generated summaries and insights
4. **Export Summaries** - Generate professional portfolio exports
5. **Manage Privacy** - Configure redaction and retention policies

## 💡 LLM Integration

The project includes comprehensive OpenAI integration for intelligent artifact analysis:

```python
from src.llm_analyzer import LLMAnalyzer, AnalysisType

# Initialize
analyzer = LLMAnalyzer(model="gpt-4o-mini")

# Analyze code
result = analyzer.analyze_code_file(
    code="def hello(): return 'world'",
    filename="app.py",
    language="Python"
)

# Generate portfolio
portfolio = analyzer.generate_portfolio_entry({
    "name": "My Project",
    "technologies": ["Python", "FastAPI"],
    "commit_count": 150
})
```

### Documentation
- 📖 **Quick Start**: `src/QUICKSTART.md`
- 📖 **Full Setup**: `docs/LLM_SETUP_GUIDE.md`
- 📖 **Customization**: `docs/PROMPT_ENGINEERING_GUIDE.md`
- 📖 **Architecture**: `docs/LLM_ARCHITECTURE.md`
- 📖 **Summary**: `LLM_INTEGRATION_SUMMARY.md`

## 🧪 Testing

```bash
# Run tests
pytest tests/test_llm_analyzer.py -v

# Run with coverage
pytest tests/test_llm_analyzer.py --cov=src --cov-report=html

# Integration tests (requires API key)
export OPENAI_API_KEY=your_key
pytest tests/test_llm_analyzer.py::TestIntegration -v
```

## 👥 Team

| Member | GitHub | Responsibilities |
|--------|--------|-----------------|
| Tahsin Jawwad | @tahsinj | R1: Config, R7: Analytics |
| Abijeet Dhillon | @abijeet-dhillon | R3: Git Adapter, R11: Notes |
| Misha Gavura | @mishagavura | R2: Type Detection, R9: Incremental Scan |
| Abhinav Malik | @Malik-Abhinav | R4: Office/PDF, R8: API |
| Kaiden Merchant | @kmerchant1 | R5: Media, R10: Export |
| Abdur Rehman | @abdur026 | R6: Storage, R12: Privacy |

## 🛠️ Technology Stack

- **Backend**: Python 3.11, FastAPI
- **AI/ML**: OpenAI API (GPT-4o-mini, GPT-4o)
- **Parsing**: GitPython, pydriller, python-docx, python-pptx, pdfminer
- **Database**: SQLAlchemy
- **Testing**: pytest, pytest-cov
- **Documentation**: Markdown

## 📊 Development Workflow

1. **Branching**: Use feature branches for development
2. **Pull Requests**: Create PR for code review before merging
3. **Testing**: Ensure tests pass before PR
4. **Documentation**: Keep docs up-to-date
5. **Logs**: Update personal and team logs weekly

## 🔒 Privacy & Security

- **Local-first**: All processing happens on user's machine
- **PII Redaction**: Configurable redaction rules (R12)
- **User Consent**: Clear policies for what's analyzed
- **No Storage**: OpenAI doesn't train on API data
- **Encryption**: Secure API communication (HTTPS)

## 📈 Project Status

**Current Phase**: Week 5 - LLM Integration Complete ✅

See `docs/logs/team-log.md` for detailed progress tracking.

## 📝 License

This is a university capstone project for educational purposes.

## 🔗 Resources

- **Project Plan**: `docs/plan/README.md`
- **Team Logs**: `docs/logs/team-log.md`
- **OpenAI Platform**: https://platform.openai.com/
- **API Documentation**: https://platform.openai.com/docs

---

**Note**: This is an active development project. Features are being implemented iteratively throughout the term.
