# Chrome Extension Design Document

## LLM-Driven DOM Personalization via Action Map + jQuery Selectors

---

### **1. Overview**

This document describes the design for a Chrome extension that allows users to personalize webpages using natural language prompts. The system captures the page's DOM structure, screenshot, and the user prompt, and sends these to a backend service that uses an LLM to generate structured jQuery selector-based transformations.

The transformations are categorized under predefined **action types** (e.g., `color`, `text`) and are applied safely and continuously by the extension.

---

### **2. System Goals**

* Enable natural-language customization of arbitrary web pages.
* Use LLMs to interpret HTML and visual context into concrete DOM modifications.
* Generate structured, safe, and repeatable transformations using jQuery selectors.
* Apply these transformations in real time and persist them across sessions.

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
Actions defined in backend

#### **6.1 Input Schema (to LLM)**

```json
{
  "prompt": "Make the background green",
  "html": "<html>...</html>",
  "screenshot": "<base64_image>",
  "actions": ["color", "text", "layout", "visibility", "style"]
}
```

#### **6.2 Output Schema (from LLM)**

```json
{
  "transformations": [
    {
      "selector": "body",
      "action": "color",
      "params": { "background-color": "green" }
    },
    {
      "selector": "h1.title, h2.title",
      "action": "text",
      "params": { "replace": "Welcome to My Blog" }
    }
  ]
}
```

#### **6.3 Transformation Schema**

```typescript
interface Transformation {
  selector: string;            // CSS or jQuery selector
  action: ActionType;          // One of the predefined actions
  params: Record<string, any>; // Key-value pairs for properties
}
```

#### **6.4 ActionType Enum**

```typescript
type ActionType = 'color' | 'text' | 'layout' | 'visibility' | 'style';
```

---

### **7. Action Execution (Client-Side)**

Each action type maps to a handler function:

```js
const actionHandlers = {
  color: (selector, params) => $(selector).css(params),
  text: (selector, params) => $(selector).text(params.replace),
  visibility: (selector, params) => $(selector).css('display', params.display),
  style: (selector, params) => $(selector).css(params),
  layout: (selector, params) => $(selector).css(params),
};
```

Execution:

```js
function applyTransformations(data) {
  data.transformations.forEach(t => {
    if (actionHandlers[t.action]) {
      actionHandlers[t.action](t.selector, t.params);
    }
  });
}
```

---

### **8. LLM Prompt Template**

#### **System Prompt (Use Structured Output Here)**

```
You are a web page personalization assistant.

Given (HTML, Screenshot, Prompt, and the list of valid Actions), generate structured JSON describing jQuery selector-based actions that will modify the page according to the user’s intent.

Rules:
- Output JSON only, no text or explanations.
- Each transformation object must contain:
  { "selector": "...", "action": one of [color, text, layout, visibility, style], "params": {...} }
- Use concise and specific selectors that generalize well.
- Do not include scripts or event handlers; only safe DOM/style changes.
```

#### **Example Input**

```json
{
  "prompt": "Make all titles larger and buttons rounded",
  "html": "<html>...</html>",
  "actions": ["color", "text", "layout", "visibility", "style"]
}
```

#### **Expected Output**

```json
{
  "transformations": [
    { "selector": "h1, h2, h3", "action": "style", "params": {"font-size": "2em"} },
    { "selector": "button", "action": "style", "params": {"border-radius": "12px"} }
  ]
}
```

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
