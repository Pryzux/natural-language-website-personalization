# Natural Language Website Personalization

Chrome extension for intelligent webpage transformation. Uses GPT-4o vision + HTML analysis to generate CSS modifications from natural language. Applications: ad blocking, accessibility enhancement, custom theming, content filtering. Custom webpage layouts.

## Features

- **Natural Language Interface**: Describe changes in plain English, no CSS required
- **Multimodal Analysis**: Combines HTML structure + screenshots context for precise transformations
- **Smart Ad Blocking**: Semantic content filtering beyond traditional filter lists
- **Accessibility**: Quick fixes for text size, contrast, readability
- **Custom Theming**: Apply dark mode or custom styles to any website
- **Persistent**: Transformations save per domain and reapply automatically
- **Dynamic Content**: Continuous reapplication handles SPAs and dynamic loading

## Architecture

```
User Prompt → Extension → Capture (HTML + Screenshot)
           ↓
    Backend API (FastAPI)
           ↓
    GPT-4o Vision Model → Generate CSS Selectors + Actions
           ↓
    Extension → Apply + Persist Transformations
```

## Tech Stack

**Backend:**
- Python 3.12+
- FastAPI
- OpenAI GPT-4o API
- Pydantic for validation

**Extension:**
- Chrome Extension Manifest V3
- JavaScript (ES6+)
- Chrome Storage API
- Chrome Scripting API

## Setup

### Backend

1. Install dependencies:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. Start server:
```bash
uvicorn api.api:app --host 0.0.0.0 --port 8000
# Or use the start script:
./start_server.sh
```

Server runs on `http://localhost:8000`

### Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension` directory
5. Pin the extension to your toolbar

## Usage

1. Navigate to any webpage
2. Click the extension icon
3. Enter a natural language prompt:
   - "Make the background green"
   - "Hide all ads and sponsored content"
   - "Make all text larger and easier to read"
   - "Change all links to orange"
   - "Remove the sidebar"
4. Click "Apply Changes"
5. Transformations persist across page reloads

## API Endpoints

### `POST /generate_transformations`
Generate transformations from natural language prompt.

**Request:**
```json
{
  "prompt": "make the background green",
  "html": "<html>...</html>",
  "screenshot": "base64_encoded_image",
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "transformations": [
    {
      "selector": "body",
      "action": "color",
      "params": {"background-color": "green"}
    }
  ],
  "summary": "Generated 1 transformations",
  "selectors": ["body"]
}
```

### `GET /actions`
List available action types and their parameters.

## Available Actions

- **color**: Modify color properties (background-color, color, border-color)
- **text**: Change text content
- **layout**: Adjust layout properties (margin, padding, width, height)
- **visibility**: Show/hide elements (display, visibility, opacity)
- **style**: General CSS style modifications

## Examples

### Ad Blocking
```
"Hide all ads, sponsored content, and promotional banners"
```

### Accessibility
```
"Make all text 18px, increase line height, and improve contrast"
```

### Custom Theme
```
"Apply dark mode with purple accents"
```

### Layout Fixes
```
"Center all content and remove sidebars"
```

## Development

### Project Structure
```
.
├── backend/
│   ├── api/
│   │   ├── api.py           # FastAPI server
│   │   └── types.py         # API request/response types
│   ├── transform/
│   │   ├── actions/
│   │   │   ├── actions.py   # Actions manager
│   │   │   ├── types.py     # Action type model
│   │   │   └── definitions.py # Action definitions
│   │   └── llm/
│   │       ├── llm_service.py # OpenAI integration
│   │       └── types.py     # LLM types (Transformation)
│   ├── save_requests.py     # Request logging
│   ├── requirements.txt
│   └── .env
├── extension/
│   ├── manifest.json        # Extension config
│   ├── background.js        # Service worker
│   ├── content.js           # Page injection
│   ├── popup.html           # Extension UI
│   ├── popup.js             # UI logic
│   └── popup.css
└── README.md
```

### Adding New Actions

1. Define action in `backend/transform/actions/definitions.py`:
```python
Action(
    action="your_action",
    description="What it does",
    param_examples={"property": "value"}
)
```

2. Add handler in `extension/content.js` and `extension/background.js`:
```javascript
your_action: (selector, params) => {
    document.querySelectorAll(selector).forEach(el => {
        // Implementation
    });
}
```

## License

MIT

## Contributing

Pull requests welcome! Please ensure:
- Code follows existing style
- New actions have full handler implementations
- README is updated for new features
