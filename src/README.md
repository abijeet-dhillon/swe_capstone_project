# Document Summarization with OpenAI

A clean, minimal implementation for summarizing Word documents (.docx) and PowerPoint presentations (.pptx) using OpenAI's API.

## 📋 Features

- **Document Parsing**: Extract text from .docx and .pptx files
- **AI Summarization**: Generate concise summaries using OpenAI GPT models
- **Clean Architecture**: Modular, testable, and easy to extend
- **Privacy-First**: All processing happens locally, only text is sent to OpenAI

## 🚀 Quick Start

### 1. Get Your OpenAI API Key

You need an OpenAI API key to use this service:

1. Go to [https://platform.openai.com/](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to **API Keys** section: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
4. Click **"Create new secret key"**
5. Copy the key (it will look like: `sk-proj-...` or `sk-...`)
6. **Important**: Save it somewhere safe - you won't be able to see it again!

**Note**: You may need to add credit to your account. OpenAI offers free trial credits for new users.

### 2. Set Up Your Environment

```bash
# Navigate to the src directory
cd src

# Install required dependencies
pip install -r requirements.txt
```

### 3. Configure Your API Key

Create a `.env` file in the `src` directory:

```bash
# Copy the example file
cp env.example .env

# Edit the .env file and add your API key
# Change this line:
OPENAI_API_KEY=your-openai-api-key-here
# To something like:
OPENAI_API_KEY=sk-proj-ABC123...XYZ789
```

**Using a text editor:**
```bash
# macOS/Linux
nano .env

# Or use any text editor
code .env  # VS Code
open -a TextEdit .env  # macOS TextEdit
```

### 4. Test It!

```bash
# Test with your document
python test_summarization.py path/to/your/document.docx

# Or with a PowerPoint file
python test_summarization.py path/to/your/presentation.pptx
```

## 📖 Usage Examples

### Basic Usage

```python
from services.summarization_service import SummarizationService

# Initialize the service (reads API key from .env)
service = SummarizationService()

# Summarize a document
result = service.summarize_document("path/to/document.docx")

# Access the results
print(f"File: {result['file_name']}")
print(f"Word Count: {result['word_count']}")
print(f"Summary: {result['summary']}")
```

### Custom Configuration

```python
# Use a specific API key
service = SummarizationService(api_key="sk-...")

# Customize summary length and model
result = service.summarize_document(
    "document.docx",
    max_summary_tokens=300,  # Shorter summary
    model="gpt-4o"  # Use more powerful model
)
```

### Parsing Only (No Summarization)

```python
from parsers.document_parser import DocumentParser

parser = DocumentParser()

# Parse a Word document
docx_data = parser.parse_docx("document.docx")
print(f"Paragraphs: {docx_data['paragraph_count']}")
print(f"Tables: {docx_data['table_count']}")
print(f"Text: {docx_data['text']}")

# Parse a PowerPoint
pptx_data = parser.parse_pptx("presentation.pptx")
print(f"Slides: {pptx_data['slide_count']}")
print(f"Text: {pptx_data['text']}")
```

## 🏗️ Project Structure

```
src/
├── llm/
│   └── openai_client.py          # OpenAI API wrapper
├── parsers/
│   └── document_parser.py        # Document text extraction
├── services/
│   └── summarization_service.py  # Combined parsing + summarization
├── test_summarization.py         # Test script
├── requirements.txt              # Python dependencies
├── env.example                   # Environment variables template
└── README.md                     # This file
```

## 🧪 Testing

The `test_summarization.py` script provides a simple way to test the functionality:

```bash
python test_summarization.py your_document.docx
```

**Expected Output:**
```
============================================================
Testing Summarization
============================================================

🔧 Initializing summarization service...
📄 Processing file: your_document.docx
⏳ Parsing document and generating summary...

============================================================
RESULTS
============================================================

📁 File: your_document.docx
📋 Type: DOCX
📊 Status: SUCCESS
📝 Paragraphs: 15
📊 Tables: 2
🔤 Word Count: 847

────────────────────────────────────────────────────────────
📝 SUMMARY:
────────────────────────────────────────────────────────────
[Your AI-generated summary will appear here]
────────────────────────────────────────────────────────────

✅ Summarization completed successfully!
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |

### Model Options

The default model is `gpt-4o-mini` (fast and cost-effective). You can change it to:

- `gpt-4o-mini`: Fastest and cheapest (recommended)
- `gpt-4o`: More capable, higher cost
- `gpt-4-turbo`: Previous generation, balanced
- `gpt-3.5-turbo`: Older, cheaper but less accurate

### Cost Estimates (approximate)

Using `gpt-4o-mini`:
- Small document (< 1000 words): ~$0.001 - $0.005
- Medium document (1000-5000 words): ~$0.005 - $0.02
- Large document (5000+ words): ~$0.02 - $0.10

## 🔒 Security & Privacy

- **API Key**: Never commit your `.env` file! It's already in `.gitignore`
- **Local Processing**: Document parsing happens locally
- **Data Sent**: Only extracted text is sent to OpenAI for summarization
- **No Storage**: OpenAI doesn't store your data (per their API terms)

## 🛠️ Troubleshooting

### "OpenAI API key not provided"
- Make sure you've created the `.env` file
- Check that your API key is correctly formatted
- Ensure the `.env` file is in the same directory as your script

### "File not found"
- Check the file path is correct
- Use absolute paths if relative paths don't work

### "Failed to parse DOCX/PPTX file"
- Ensure the file isn't corrupted
- Check that the file extension matches the actual format
- Try opening the file in Word/PowerPoint to verify it works

### "Rate limit exceeded"
- You've hit OpenAI's rate limits
- Wait a few seconds and try again
- Consider upgrading your OpenAI plan

### "Insufficient quota"
- Your OpenAI account has run out of credits
- Add payment method and credits at [https://platform.openai.com/account/billing](https://platform.openai.com/account/billing)

## 📚 Dependencies

- **openai**: Official OpenAI Python library
- **python-docx**: Parse Word documents
- **python-pptx**: Parse PowerPoint presentations  
- **python-dotenv**: Load environment variables

## 🔄 Next Steps

This is a minimal, clean implementation. Potential enhancements:

1. **More Formats**: Add PDF, txt, markdown support
2. **Batch Processing**: Summarize multiple files at once
3. **Custom Prompts**: Different summarization styles (bullet points, executive summary, etc.)
4. **Caching**: Store summaries to avoid re-processing
5. **API Integration**: Wrap this in a FastAPI service
6. **Error Recovery**: Retry logic for transient failures

## 📄 License

Part of the capstone-project-team-14 repository.

## 🤝 Contributing

This is a team project. For questions or improvements, contact the team members listed in the project README.

---

**Quick Reference Card:**

```bash
# Setup (one time)
cd src
pip install -r requirements.txt
cp env.example .env
# Edit .env and add your OpenAI API key

# Test it
python test_summarization.py your_file.docx
```

**Get API Key:** [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

