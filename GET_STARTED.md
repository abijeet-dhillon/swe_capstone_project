# 🚀 GET STARTED - Your 3-Step LLM Integration Guide

## ⚡ Super Quick Start (2 minutes)

### Step 1️⃣: Install Dependencies
```bash
cd /Users/mishagavura/Documents/UBC/cosc499/capstone-project-team-14
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2️⃣: Get OpenAI API Key
1. Go to: https://platform.openai.com/api-keys
2. Sign up/login
3. Click "Create new secret key"
4. Copy the key (looks like: `sk-proj-abc123...`)

### Step 3️⃣: Configure & Test
```bash
# Create .env file
cp env.template .env

# Edit .env and paste your API key
# (Replace 'sk-your-openai-api-key-here' with your actual key)

# Test it!
python src/example_usage.py
```

✅ **Done!** You should see LLM analysis results!

---

## 📖 What You Got

### Files Created (11 files, ~3000+ lines)

```
✅ Core Module
   src/llm_analyzer.py              (540 lines) - Main LLM integration
   
✅ Examples  
   src/example_usage.py             (340 lines) - 8 working examples
   src/integration_example.py       (450 lines) - Full pipeline demos
   
✅ Tests
   tests/test_llm_analyzer.py       (350 lines) - 25+ unit tests
   
✅ Documentation
   docs/LLM_SETUP_GUIDE.md          (600 lines) - Complete setup guide
   docs/PROMPT_ENGINEERING_GUIDE.md (500 lines) - How to "teach" the model
   docs/LLM_ARCHITECTURE.md         (400 lines) - System architecture
   src/QUICKSTART.md                 (80 lines) - 5-minute guide
   LLM_INTEGRATION_SUMMARY.md       (300 lines) - Complete summary
   
✅ Config
   requirements.txt                  - All dependencies
   env.template                      - Environment template
   .gitignore                        - Git ignore rules
```

---

## 💡 What Can You Do?

### 1. Code Review
```python
from src.llm_analyzer import LLMAnalyzer, AnalysisType

analyzer = LLMAnalyzer()
result = analyzer.analyze_code_file(
    code="def factorial(n): return 1 if n == 0 else n * factorial(n-1)",
    filename="math.py",
    language="Python"
)
print(result["analysis"])
```

**Output**: Detailed code review with suggestions!

### 2. Commit Summary
```python
commits = [
    {"hash": "abc123", "message": "Add feature", "author": "You", "date": "2024-10-20"}
]
result = analyzer.analyze_git_commits(commits, "my-repo")
print(result["analysis"])
```

**Output**: AI-generated commit history summary!

### 3. Extract Skills
```python
artifacts = [
    "Built REST API with FastAPI",
    "Created React frontend with TypeScript"
]
result = analyzer.extract_skills(artifacts)
print(result["analysis"])
```

**Output**: Categorized technical skills!

### 4. Generate Portfolio
```python
project = {
    "name": "My Project",
    "technologies": ["Python", "FastAPI"],
    "commit_count": 150
}
result = analyzer.generate_portfolio_entry(project)
print(result["analysis"])
```

**Output**: Professional portfolio text ready for export!

### 5. Batch Processing
```python
files = [
    {"id": "app.py", "content": code1},
    {"id": "utils.py", "content": code2}
]
results = analyzer.batch_analyze(files, AnalysisType.CODE_REVIEW)
```

**Output**: Analysis for multiple files at once!

---

## 🎯 Choose Your Path

### Path A: Just Want to Use It?
👉 Read: `src/QUICKSTART.md` (5 minutes)
👉 Run: `python src/example_usage.py`
👉 Done!

### Path B: Want Full Understanding?
👉 Read: `docs/LLM_SETUP_GUIDE.md` (20 minutes)
👉 Read: `LLM_INTEGRATION_SUMMARY.md` (10 minutes)
👉 Run: Both example files

### Path C: Want to Customize Everything?
👉 Read: `docs/PROMPT_ENGINEERING_GUIDE.md` (30 minutes)
👉 Read: `docs/LLM_ARCHITECTURE.md` (15 minutes)
👉 Experiment with custom prompts!

---

## 🔍 Quick Reference

### Basic Usage
```python
from src.llm_analyzer import LLMAnalyzer, AnalysisType

# Initialize
analyzer = LLMAnalyzer(model="gpt-4o-mini")

# Analyze
result = analyzer.analyze(
    content="your content here",
    analysis_type=AnalysisType.CODE_REVIEW
)

# Get result
print(result["analysis"])
print(f"Cost: ${result['tokens_used'] * 0.0000015:.4f}")
```

### Analysis Types
- `CODE_REVIEW` - Review code quality
- `COMMIT_SUMMARY` - Summarize commits  
- `PROJECT_OVERVIEW` - Create project overview
- `SKILL_EXTRACTION` - Extract skills
- `DOCUMENTATION_SUMMARY` - Summarize docs
- `PORTFOLIO_GENERATION` - Generate portfolio

### Cost Info
- **gpt-4o-mini** (default): ~$0.15/1M tokens → Most analyses < $0.01
- **gpt-4o** (better quality): ~$2.50/1M tokens → ~$0.05 per analysis

---

## 🎨 How to "Teach" the Model

### Method 1: Custom Prompts
```python
result = analyzer.analyze(
    content=code,
    analysis_type=AnalysisType.CODE_REVIEW,
    custom_prompt="Focus only on security vulnerabilities"
)
```

### Method 2: Change System Prompt
```python
analyzer.set_custom_system_prompt(
    AnalysisType.CODE_REVIEW,
    "You are a security expert. Only report security issues."
)
```

### Method 3: Adjust Creativity
```python
# More focused (for factual analysis)
analyzer = LLMAnalyzer(temperature=0.2)

# More creative (for portfolio writing)
analyzer = LLMAnalyzer(temperature=1.0)
```

**Full guide**: `docs/PROMPT_ENGINEERING_GUIDE.md`

---

## 🔗 Integration with Your Project

### For Misha (R2: Type Detection)
```python
# After detecting types, optionally use LLM for unknown files
if file_type == "unknown":
    result = analyzer.analyze(content, AnalysisType.PROJECT_OVERVIEW,
                            custom_prompt="What type of file is this?")
```

### For Abijeet (R3: Git Adapter)
```python
# After extracting commits, add LLM summary
commits = extract_commits(repo)
insights = analyzer.analyze_git_commits(commits, repo_name)
save_to_db({"commits": commits, "insights": insights["analysis"]})
```

### For Abhinav (R4, R8: Docs & API)
```python
# R4: Summarize documents
text = extract_from_pdf(doc_path)
summary = analyzer.analyze(text, AnalysisType.DOCUMENTATION_SUMMARY)

# R8: Add API endpoint
@app.post("/analyze/code")
def analyze_code(code: str):
    return analyzer.analyze_code_file(code, "input.py", "Python")
```

### For Abdur (R6: Storage)
```python
# Store LLM results with artifacts
db.insert({
    "artifact": artifact_data,
    "llm_analysis": result["analysis"],
    "tokens_used": result["tokens_used"]
})
```

### For Tahsin (R7: Analytics)
```python
# Enhance metrics with LLM narrative
metrics = calculate_metrics(artifacts)
narrative = analyzer.analyze(str(metrics), AnalysisType.PROJECT_OVERVIEW)
return {"metrics": metrics, "narrative": narrative["analysis"]}
```

### For Kaiden (R10: Export)
```python
# Generate polished portfolio entries
for project in projects:
    entry = analyzer.generate_portfolio_entry(project)
    add_to_export(entry["analysis"])
```

---

## 📚 Documentation Map

```
📖 Documentation Guide:

Quick Start (5 min)
├─ GET_STARTED.md (this file) ⭐ START HERE
└─ src/QUICKSTART.md

Full Guides (20-30 min each)
├─ LLM_INTEGRATION_SUMMARY.md  - Complete overview
├─ docs/LLM_SETUP_GUIDE.md     - Detailed setup
├─ docs/PROMPT_ENGINEERING_GUIDE.md - Customization
└─ docs/LLM_ARCHITECTURE.md    - System architecture

Code Examples
├─ src/example_usage.py        - Basic examples
└─ src/integration_example.py  - Full pipeline

Reference
├─ src/llm_analyzer.py         - Source code
└─ tests/test_llm_analyzer.py  - Tests
```

---

## ✅ Checklist

Before you start coding, make sure:

- [ ] Installed dependencies (`pip install -r requirements.txt`)
- [ ] Got OpenAI API key
- [ ] Created `.env` file with your API key
- [ ] Ran `python src/example_usage.py` successfully
- [ ] Read at least `QUICKSTART.md`
- [ ] Understand the 6 analysis types
- [ ] Know how to integrate with your component

---

## 🆘 Troubleshooting

### ❌ "OpenAI API key not found"
```bash
# Check .env exists
ls -la .env

# Check it has the key
cat .env | grep OPENAI_API_KEY

# Make sure it's loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

### ❌ "Module not found"
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall
pip install -r requirements.txt
```

### ❌ "Rate limit error"
Wait a few minutes. You've hit OpenAI's rate limit. Or upgrade your plan.

### ❌ "Too expensive"
Use `gpt-4o-mini` (default) instead of `gpt-4o`. Set billing alerts in OpenAI dashboard.

---

## 💰 Cost Management

### Set Up Billing Alerts
1. Go to https://platform.openai.com/account/billing/limits
2. Set soft limit: $5
3. Set hard limit: $10
4. You'll get email alerts

### Track Usage
```python
result = analyzer.analyze(content, AnalysisType.CODE_REVIEW)
tokens = result["tokens_used"]
cost = tokens * 0.0000015  # For gpt-4o-mini
print(f"Cost: ${cost:.4f}")
```

### Typical Costs (gpt-4o-mini)
- Code review: $0.005
- Commit summary: $0.008
- Portfolio generation: $0.015
- **100 analyses**: ~$1-2

---

## 🎉 You're Ready!

Everything is set up and documented. Just:

1. ✅ Get your API key
2. ✅ Run the examples
3. ✅ Start integrating with your component!

**Questions?** Check the documentation or run the examples!

---

## 📞 Quick Links

- **Get API Key**: https://platform.openai.com/api-keys
- **OpenAI Docs**: https://platform.openai.com/docs
- **Pricing**: https://openai.com/pricing
- **Dashboard**: https://platform.openai.com/account

---

## 🚀 Next Steps

### This Week
1. Get OpenAI API key
2. Run all examples
3. Read `QUICKSTART.md`
4. Understand how to use each analysis type

### Next Week  
1. Integrate with your assigned component (R2-R12)
2. Customize prompts for your needs
3. Add API endpoints (if you're doing R8)
4. Test with real data

### This Month
1. Complete your component
2. Add comprehensive tests
3. Document your integration
4. Demo to the team

---

**Happy coding! 🎉**

You now have a production-ready LLM integration with comprehensive documentation!

