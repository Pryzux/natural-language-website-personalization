# AI-Powered Web Customization Extension

Transform any webpage forever using natural language - powered by Multi-Modal LLMs and executed with safe, CSP-compliant jQuery operations.

## Demo



https://github.com/user-attachments/assets/7d25cfaf-a666-4d18-babc-54893f47c1dc



---

## Overview

This Chrome extension allows you to customize any website using plain English. Simply describe what you want to change, and an LLM analyzes the page structure to generate precise DOM transformations that are applied peristently. Works on any page, forever. If the site updates, simply prompt again!

Works for: Ad-Blocking, Layout changes, Styling, and content filtering (Ex I don't want to see tweets from x username, or 'I don't want to see political posts on this page'). 

**Key Features:**
- **Natural language interface** - "Hide all ads", "Make the background darker", "Remove sponsored content"
- **CSP-safe** - All transformations use declarative jQuery methods (no inline scripts or eval)
- **Context-aware** - LLM analyzes both HTML structure and visual screenshots
- **Persistent** - Changes are saved per-URL and reapplied automatically
- **Generic Domain optimization** - HTML Sanitization Library to reduce LLM Context
- **Multi-provider support** - Works with OpenAI (GPT-4o) or Anthropic (Claude)

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Chrome Extension (Frontend)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Popup UI    │  │   Content    │  │    Background    │  │
│  │  (Input)     │──│    Script    │──│     Script       │  │
│  └──────────────┘  │ (Executor)   │  │   (Bridge)       │  │
│                    └──────────────┘  └──────────────────┘  │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │   FastAPI Backend    │
                   └──────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐   ┌──────────────┐
│ Sanitization │    │   LLM Service    │   │   Request    │
│   Pipeline   │    │ (OpenAI/Claude)  │   │    Saver     │
└──────────────┘    └──────────────────┘   └──────────────┘
        │                     │
        ▼                     ▼
   HTML cleaning        jQuery Commands
                        
```

### Flow

1. **User Input** → Type natural language request in popup
2. **Context Capture** → Extension captures page HTML + screenshot
3. **Sanitization** → Backend cleans HTML (removes scripts, reduces size)
4. **LLM Analysis** → AI analyzes structure + screenshot, generates jQuery commands
5. **Validation** → Commands validated against safe method whitelist
6. **Execution** → Extension applies transformations to live DOM
7. **Persistence** → Changes saved to Chrome storage, reapplied on reload

---

## Getting Started

### Prerequisites

- **Node.js** (for extension development)
- **Python 3.10+** (for backend)
- **Chrome Browser** (for extension installation)
- **OpenAI API Key** or **Anthropic API Key**

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the server
uvicorn api.api:app --reload --host 0.0.0.0 --port 8000
```

### Extension Setup

```bash
cd extension

# Load unpacked extension in Chrome
# 1. Go to chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select the /extension directory
```

---

## Configuration

### Backend `.env` File

```bash
# LLM Provider (REQUIRED)
LLM_MODEL=OpenAI                    # or "Anthropic"
LLM_VERSION=gpt-4o                  # or "claude-3-5-sonnet-20241022"
LLM_API_KEY=your-api-key-here

# Debug Settings
SAVE_REQUESTS=true                  # Save all requests for debugging
MAX_HTML_LENGTH_FROM_EXTENSION=None # Truncate HTML (None = no limit)
DISABLE_SANITIZATION=false          # Skip HTML sanitization (testing only)
```

### Supported LLM Models

**OpenAI:**
**Anthropic:**

---

## How It Works

### 1. Natural Language → jQuery Commands

**User Input:**
```
Hide all sponsored posts and make the background darker
```

**LLM Output:**
```json
{
  "transformations": [
    {
      "selector": "article:contains('Sponsored'), article[data-promoted='true']",
      "commands": [
        { "method": "hide", "args": [] }
      ]
    },
    {
      "selector": "body",
      "commands": [
        { "method": "css", "args": [{"background-color": "#1a1a1a"}] }
      ]
    }
  ]
}
```

**Executed as:**
```javascript
$("article:contains('Sponsored'), article[data-promoted='true']").hide();
$("body").css({"background-color": "#1a1a1a"});
```

### 2. Safe jQuery Subset

The system uses **53 whitelisted jQuery methods** that are all CSP-safe:

- **Traversal:** `find`, `filter`, `closest`, `parent`, `children`, `siblings`, etc.
- **DOM Manipulation:** `append`, `prepend`, `before`, `after`, `remove`, `replaceWith`, etc.
- **Styling:** `css`, `addClass`, `removeClass`, `show`, `hide`, etc.
- **Attributes:** `attr`, `prop`, `data`, etc.

**No inline functions, no eval(), no event handlers with code.**

### 3. HTML Sanitization

Before sending to the LLM, HTML is sanitized based on the domain:

**General Sanitizer (lxml-based):**
- Removes `<script>` tags and `javascript:` URLs
- Removes HTML comments and processing instructions
- Preserves all structural HTML, classes, IDs, and attributes
- Typical reduction: ~9-35%

**Toggle:** Set `DISABLE_SANITIZATION=true` in `.env` to send raw HTML

---

## Logging & Debugging

The backend includes comprehensive logging to track context usage:

```
================================================================================
[API] NEW TRANSFORMATION REQUEST
================================================================================
[API] Prompt: hide all ads
[API] URL: https://twitter.com/home
[API] Incoming HTML size: 562,341 chars (575,294 bytes)
[API] Screenshot size: 123,456 chars

[API] SANITIZATION PHASE:
[API] Sanitized: 562,341 → 98,432 chars (82.5% reduction)

[API] LLM SERVICE PHASE:
[LLM Service] Building prompt messages...
[LLM Service] System prompt: 10,362 chars
[LLM Service] HTML size: original=98,432 chars, sending=98,432 chars, truncated=False
[LLM Service] Total text in prompt: 108,794 chars (~27,198 tokens estimated)
[LLM Service] Images in prompt: 1
[LLM Service] Calling openai API with model gpt-4o...
[OpenAI] Sending request: system=10,362 chars, user_text=98,753 chars, images=1
[OpenAI] Token usage: prompt=29,543, completion=156, total=29,699
[LLM Service] API responded in 4.23s
[LLM Service] Generated 3 transformations

[API] REQUEST COMPLETE
[API] Transformations generated: 3
[API] Unique selectors: 5
================================================================================
```

**What to watch:**
- `truncated=False` → Full HTML being sent
- Token usage vs. model limits (128K for GPT-4o, 200K for Claude)
- Sanitization reduction percentage

---

## Request Saving

When `SAVE_REQUESTS=true`, all requests are saved to `/backend/requests/` for debugging:

```
backend/requests/
└── twitter.com/
    └── request_1/
        ├── metadata.json
        ├── raw_received/
        │   ├── prompt.txt          # User's natural language request
        │   ├── page.html           # Original HTML from extension
        │   └── screenshot.png      # Page screenshot
        └── llm/
            ├── prompt.json         # Messages sent to LLM (with placeholders)
            ├── result.json         # Full LLM response + metadata
            └── sanitized_page.html # Sanitized HTML (if applicable)
```

**View saved request:**
```bash
cd backend
python requests/print_requests.py twitter.com 1
```

---

## Testing

### Test with Simple Requests

```
Make the background green
Make all text bigger
Hide images
```

### Test with Complex Requests

```
Hide all promoted tweets and sponsored content
Make links green and underlined when I hover
Add a dark theme to the entire page
```

## Development

### Adding New jQuery Methods

1. Add to whitelist in `backend/transform/llm/types.py`:
```python
SAFE_JQUERY_METHODS = [
    ...,
    "yourMethod",
]
```

2. Add to system prompt in `backend/transform/llm/system_prompt.txt`:
```markdown
| `yourMethod` | `args` | Description | Example |
```

3. If it accepts HTML, add to sanitization list in `types.py`:
```python
html_methods = [..., 'yourMethod']
```

### Adding Domain-Specific Sanitizers

1. Create `backend/sanitize/domains/example_sanitizer.py`:
```python
from shared.api import TransformationRequest

def sanitize(request: TransformationRequest) -> TransformationRequest:
    # Your custom sanitization logic
    sanitized_html = clean_html(request.html)

    return TransformationRequest(
        prompt=request.prompt,
        html=sanitized_html,
        screenshot=request.screenshot,
        url=request.url
    )
```

2. Register in `backend/sanitize/sanitization_types.py`:
```python
DOMAIN_SANITIZERS = {
    "example.com": "example_sanitizer",
}
```

---

## Troubleshooting

### Extension Can't Connect to Backend

**Check:**
- Backend is running on `http://localhost:8000`
- CORS is enabled (already configured in `api.py`)
- Check browser console for errors

### LLM Returns Invalid Methods

**Check:**
- System prompt matches schema (`python` script in README)
- Method is in `SAFE_JQUERY_METHODS` whitelist
- Check backend logs for validation errors

### Transformations Don't Apply

**Check:**
- Selectors are valid (test in browser console: `$("your-selector")`)
- Page hasn't changed since transformations were generated
- Check extension console for execution errors

### High Token Usage / Cost

**Solutions:**
- Enable sanitization (`DISABLE_SANITIZATION=false`)
- Set `MAX_HTML_LENGTH_FROM_EXTENSION` to limit HTML size
- Create domain-specific sanitizers for frequently visited sites

---

## 📁 Project Structure

```
.
├── extension/              # Chrome extension frontend
│   ├── manifest.json
│   ├── popup.html
│   ├── popup.js
│   ├── content.js         # Executes transformations
│   └── background.js      # Bridges popup ↔ content ↔ backend
│
├── backend/               # Python FastAPI backend
│   ├── api/
│   │   └── api.py         # Main API endpoint
│   ├── shared/
│   │   └── api.py         # Shared types (TransformationRequest)
│   ├── sanitize/
│   │   ├── sanitize_requests.py      # Routing logic
│   │   ├── sanitization_types.py     # Domain mapping
│   │   └── domains/
│   │       ├── general_sanitizer.py  # lxml-based default
│   │       └── twitter_sanitizer.py  # Twitter-specific
│   ├── transform/
│   │   └── llm/
│   │       ├── llm_service.py        # LLM orchestration
│   │       ├── system_prompt.txt     # jQuery instructions
│   │       ├── types.py              # Validation schemas
│   │       └── models/
│   │           ├── openai_model.py   # OpenAI provider
│   │           └── anthropic_model.py # Anthropic provider
│   ├── requests/          # Saved requests (if enabled)
│   │   ├── save_requests.py
│   │   └── print_requests.py
│   ├── requirements.txt
│   └── .env
│
└── README.md
```

---

## Contributing

Contributions are welcome! Areas for improvement:

- **General sanitizer** - The better this gets, the better the responses are! Anyone who specializes in frontend could make major contributions to the project here.
- **domain specific sanitizers** - YouTube, Reddit, Facebook, etc.
- **Better error handling** - Graceful fallbacks for failed transformations
- **UI improvements** - Better popup interface, transformation previews
- **Testing framework** - Automated tests for sanitizers and transformations
- **Performance optimization** - Caching, request batching

---

## License

MIT License - see LICENSE file for details

---

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Sanitization powered by [lxml](https://lxml.de/) and [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- LLM providers: [OpenAI](https://openai.com/) and [Anthropic](https://www.anthropic.com/)
- jQuery method reference: [jQuery API Documentation](https://api.jquery.com/)

---

## Links

- **Documentation:** See inline code comments and docstrings
- **Issues:** Report bugs or request features (create issues in your repo)
- **Demo Video:** [See above](#-demo)


[![Watch the video](https://img.youtube.com/vi/l2uwvFWxRbE/0.jpg)](https://www.youtube.com/watch?v=l2uwvFWxRbE)

