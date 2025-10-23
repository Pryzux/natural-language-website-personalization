# Chrome Extension Design Document

## LLM-Driven DOM Personalization via Command Chains

---

### **1. Overview**

This document describes the design for a Chrome extension that allows users to personalize webpages using natural language prompts. The system captures the page's DOM structure, screenshot, and the user prompt, and sends these to a backend service that uses an LLM to generate structured jQuery-like command chains.

The LLM has full freedom to generate any combination of jQuery commands needed to achieve the user's intent, from simple CSS changes to complex thematic transformations.

---

### **2. System Goals**

* Enable natural-language customization of arbitrary web pages.
* Use LLMs to interpret HTML and visual context into concrete DOM modifications.
* Generate structured, safe command chains using jQuery-like operations.
* Apply transformations in real time and persist them across sessions.
* Support complex thematic transformations (e.g., "beach theme") with coordinated changes.

---

### **3. High-Level Architecture**

```
User Prompt
   ↓
Extension Popup (UI)
   ↓
Content Script → Capture (HTML, Screenshot, prompt from input)
   ↓
Background Script → Send to Backend (FastAPI)
   ↓
LLM → Generate (Selector + Action Map)
   ↓
Extension → Apply Transformations via jQuery
```

---

### **4. Core Components**

#### 4.1 **Frontend (Chrome Extension)**

* **Popup UI**: Text box for prompt input, “Apply” button
* **Content Script**: Extracts HTML, sends to background, applies transformations.
* **Background Script**: Bridges popup ↔ content ↔ backend communication.

#### 4.2 **Backend (FastAPI Server)**

* Receives `(HTML, Screenshot, Prompt, Actions)`.
* Uses LLM (e.g., GPT-4o) to parse and interpret transformations.
* Returns structured JSON of selector/action pairs.

#### 4.3 **LLM Transformation Engine**

* Layer 1: Understands structure and semantic roles from HTML.
* Layer 2: Maps user intent to defined `Actions` and generates selectors.

---

### **5. Data Flow**

| Step | Input             | Output               | Description                                   |
| ---- | ----------------- | -------------------- | --------------------------------------        |
| 1    | User Prompt       | Context Payload      | User types instruction in popup               |
| 2    | Content Script    | `(HTML, Screenshot)` | Captures context for LLM                      |
| 3    | Background Script | POST to Backend      | Sends payload securely                        |
| 4    | Backend (LLM)     | JSON Transformations | Converts user intent to DOM jquery operations |
| 5    | Content Script    | jQuery Executions    | Applies transformations continuously          |

---

### **6. Data Schemas**

Backend Post Endpoint ({Screenshot, Dom, prompt})

#### **6.1 Input Schema (to LLM)**

```json
{
  "prompt": "Make the background green and add a welcome message",
  "html": "<html>...</html>",
  "screenshot": "<base64_image>",
  "url": "https://example.com"
}
```

#### **6.2 Output Schema (from LLM) - Command Chain Architecture**

```json
{
  "transformations": [
    {
      "description": "Apply green background and add welcome message",
      "commands": [
        {
          "selector": "body",
          "method": "css",
          "args": [{"background-color": "green"}]
        },
        {
          "selector": "body",
          "method": "prepend",
          "args": ["<h1>Welcome!</h1>"]
        },
        {
          "selector": "h1",
          "method": "css",
          "args": [{"color": "white", "text-align": "center"}]
        }
      ]
    }
  ]
}
```

#### **6.3 Command Schema (Pydantic)**

```python
class Command(BaseModel):
    selector: str  # CSS selector
    method: str    # jQuery method (css, addClass, append, etc.)
    args: List[Union[str, Dict[str, Any]]]  # Method arguments

class Transformation(BaseModel):
    description: str  # Human-readable description
    commands: List[Command]  # Commands executed in sequence

class TransformationResponse(BaseModel):
    transformations: List[Transformation]
```

#### **6.4 Available Methods**

- **CSS**: css, addClass, removeClass, toggleClass
- **Content**: text, html, empty, val
- **Attributes**: attr, removeAttr, data
- **DOM**: append, prepend, after, before, wrap, unwrap, replaceWith, remove, clone
- **Visibility**: show, hide, toggle, fadeIn, fadeOut

---

### **7. Command Execution (Client-Side)**

Each command is executed using vanilla JavaScript:

```js
function executeCommand(cmd) {
  const { selector, method, args = [] } = cmd;
  const elements = document.querySelectorAll(selector);

  elements.forEach(el => {
    switch(method) {
      case 'css':
        Object.assign(el.style, args[0]);
        break;
      case 'addClass':
        el.classList.add(args[0]);
        break;
      case 'text':
        el.textContent = args[0];
        break;
      case 'append':
        el.insertAdjacentHTML('beforeend', sanitizeHTML(args[0]));
        break;
      // ... (many more methods)
    }
  });
}

function applyTransformations(transformations) {
  transformations.forEach(transform => {
    console.log(transform.description);
    transform.commands.forEach(executeCommand);
  });
}
```

---

### **8. LLM Prompt Template**

#### **System Prompt (Uses OpenAI Structured Outputs with Pydantic)**

```
You are a web page personalization assistant that generates jQuery command chains.

**Your Task:**
Analyze the HTML, screenshot, and user request, then generate jQuery command chains
that achieve the user's desired changes.

**Available Methods:**
- CSS: css, addClass, removeClass, toggleClass
- Content: text, html, empty, val
- Attributes: attr, removeAttr, data
- DOM: append, prepend, after, before, wrap, unwrap, replaceWith, remove, clone
- Visibility: show, hide, toggle, fadeIn, fadeOut

**Handling Complex Thematic Requests:**
When a user asks for a theme (e.g., "beach theme", "dark mode"):
1. Create MULTIPLE transformations, each handling a different aspect
2. Think holistically: background, text, headings, buttons, links, inputs
3. Use a coordinated color palette
4. Add hover effects by injecting <style> tags
5. Ensure text remains readable

**Command Chaining:**
Commands execute in sequence. Chain logically: create element, then style it.
```

#### **Example: Complex Theme Request**

**Input:** "Make the page beach themed"

**Output:** Multiple transformations covering background, buttons, text, etc. with
coordinated ocean/sand colors, gradients, and decorative elements.

---

### **9. Persistence and Replay**

* Store transformations per URL:

```js
chrome.storage.local.set({ [window.location.href]: transformations });
```

* Replay on page load 

```js
chrome.storage.local.get([window.location.href], applyTransformations);
```

---

### **10. Safety Constraints**

* Restrict actions to the defined set of safe categories.

---

### **11. Example End-to-End**

**User Prompt:**

> "Hide ads and make the background light blue."

**LLM Output:**

```json
{
  "transformations": [
    { "selector": ".ad, .advertisement, .sponsored", "action": "visibility", "params": {"display": "none"} },
    { "selector": "body", "action": "color", "params": {"background-color": "#E0F7FA"} }
  ]
}
```

**Extension Execution:**

```js
$(".ad, .advertisement, .sponsored").css("display", "none");
$("body").css("background-color", "#E0F7FA");
```

---

### **12. Future Enhancements**

* **Compound Actions:** Support multiple chained modifications in one prompt.
* **Undo Stack:** Allow clearing previous transformations.
* **User Profiles:** Store personalization preferences persistently across sessions.

---

### **13. Summary**

This architecture enables a dynamic, safe, and interpretable interface between human intent and webpage modification. The LLM focuses on semantic understanding and selector synthesis, while the extension executes transformations deterministically using the predefined action map.

---
