# Playground Tab — Wireframe Spec

## 0) Screen Definition

**Screen name:** Playground

**Primary user goal:** Interactively test AI models with real-time chat, configure parameters, and compare responses.

**Data dependencies:**

- Available models: `GET /api/v1/playground/models`
- Presets: `GET /api/v1/playground/presets`
- Chat: `POST /api/v1/playground/chat` or WebSocket streaming
- Chat history: Client-side state

---

## 1) Overall Layout

The page is divided into **two main columns**:

1. **Left: Chat Interface** (60-70% width)
2. **Right: Configuration Panel** (30-40% width)

---

## 2) Left Column - Chat Interface

### 2.1 Chat Header

- **Title:** "AI Playground"
- **Actions:**
  - Clear chat button (trash icon)
  - Export conversation button (download icon)

### 2.2 Chat Messages Area

- **Scrollable container** with auto-scroll to bottom
- **Message types:**
  - User messages (right-aligned, blue background)
  - Assistant messages (left-aligned, gray background)
  - System messages (centered, italic, muted)

#### Message Card Layout

Each message shows:

- **Role badge:** USER / ASSISTANT / SYSTEM
- **Content:** Markdown-rendered text
- **Timestamp:** Relative time (e.g., "2 min ago")
- **Latency (assistant only):** "{X}ms" badge
- **Copy button:** Copy message content

#### Streaming Indicator

- Show typing indicator while streaming
- Display partial content as it arrives
- Loading dots animation

### 2.3 Input Area (Bottom Fixed)

#### Text Input

- **Multi-line textarea**
- **Placeholder:** "Type your message..."
- **Auto-resize** up to 5 lines
- **Keyboard shortcut:** Enter to send, Shift+Enter for new line

#### Send Button

- **Icon:** Send/paper plane
- **Disabled when:** Input empty or loading
- **Loading state:** Spinner while waiting for response

---

## 3) Right Column - Configuration Panel

The configuration panel uses **tabs** for organization:

1. **Model Settings**
2. **Presets**
3. **Stats**

---

### 3.1 Tab: Model Settings

#### Provider Selection

- **Label:** "Provider"
- **Dropdown:** List of providers (OpenAI, Anthropic, Google, etc.)
- **Grouped options** by provider

#### Model Selection

- **Label:** "Model"
- **Dropdown:** Models available for selected provider
- **Shows context window** (e.g., "GPT-4 (8K context)")

#### System Prompt

- **Label:** "System Prompt"
- **Textarea:** Multi-line input
- **Default:** "You are a helpful AI assistant."
- **Placeholder:** "Define the assistant's behavior..."

#### Temperature

- **Label:** "Temperature"
- **Slider:** Range 0.0 - 2.0
- **Step:** 0.1
- **Default:** 0.7
- **Display value** next to slider

#### Max Tokens

- **Label:** "Max Tokens"
- **Slider:** Range 256 - 4096
- **Step:** 256
- **Default:** 2048
- **Display value** next to slider

#### Streaming Toggle

- **Label:** "Enable Streaming"
- **Switch:** ON/OFF
- **Default:** ON
- **Description:** "Stream responses in real-time"

---

### 3.2 Tab: Presets

#### Preset List

- **Radio buttons** or **cards**
- Available presets:
  - 🎯 **Balanced** - Default settings (temp: 0.7, tokens: 2048)
  - 🧠 **Creative** - High creativity (temp: 1.2, tokens: 3072)
  - 📝 **Precise** - Deterministic (temp: 0.2, tokens: 1024)
  - 💻 **Code Assistant** - Code generation (temp: 0.3, tokens: 4096)

#### Apply Button

- **Label:** "Apply Preset"
- **Action:** Load preset settings into Model Settings tab
- **Toast notification:** "Preset applied: {name}"

#### Preset Details

When selected, show:

- System prompt
- Temperature value
- Max tokens value

---

### 3.3 Tab: Stats

#### Session Statistics

Real-time stats for current session:

- **Total Messages:** Count of user + assistant messages
- **Total Tokens:** Sum of all tokens used
- **Avg Latency:** Average response time
- **Total Cost:** Estimated cost in USD

#### Chart (Optional)

- **Small sparkline** showing latency over time

#### Reset Button

- **Label:** "Reset Stats"
- **Action:** Clear counters
- **Confirmation:** "Are you sure?"

---

## 4) Features & Interactions

### Chat Management

- **New conversation** - Clear all messages
- **Export chat** - Download as JSON or Markdown
- **Copy message** - Copy individual messages
- **Regenerate** - Re-send last user message (optional)

### Model Switching

- Changing model/provider **does NOT** clear chat
- Show notification: "Switched to {model_name}"
- Future messages use new model

### Streaming

- When enabled, show partial responses as they arrive
- Disable during streaming to prevent confusion
- Error handling: abort stream on error

### Error Handling

- Network errors: "Connection lost. Retry?"
- API errors: Display error message in chat
- Rate limits: "Rate limit exceeded. Try again in {X} seconds."

---

## 5) Loading / Empty / Error States

### Loading

- Chat loading: Skeleton message bubbles
- Model loading: Spinner in dropdown
- Preset loading: Skeleton cards

### Empty

- **No messages:** Welcome message
  - "👋 Welcome to the AI Playground!"
  - "Start a conversation to test AI models"
  - Sample prompts (clickable)

### Error

- **Model load error:** "Failed to load models. Retry?"
- **Send error:** Error message in chat
- **WebSocket error:** "Connection lost. Reconnecting..."

---

## 6) API Mapping

| Action              | API Endpoint          | Method    | Notes                         |
| ------------------- | --------------------- | --------- | ----------------------------- |
| Load models         | `/playground/models`  | GET       | Returns providers and models  |
| Load presets        | `/playground/presets` | GET       | Returns preset configurations |
| Send message (HTTP) | `/playground/chat`    | POST      | Request/response mode         |
| Send message (WS)   | `/playground/ws/chat` | WebSocket | Streaming mode                |

### Chat Request Payload

```json
{
  "messages": [
    { "role": "system", "content": "..." },
    { "role": "user", "content": "..." }
  ],
  "model": "gpt-4",
  "provider": "openai",
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": true
}
```

### Chat Response (HTTP)

```json
{
  "content": "Assistant response",
  "tokens": 150,
  "latency_ms": 1234,
  "model": "gpt-4"
}
```

### Chat Response (WebSocket)

```json
// Chunks during streaming
{"type": "chunk", "content": "partial"}

// Final message
{"type": "complete", "content": "full response", "latency_ms": 1234}

// Error
{"type": "error", "error": "Error message"}
```

---

## 7) Responsive Behavior

- **Desktop (lg+):** Two-column layout (chat + config)
- **Tablet (md):** Two-column, narrower config panel
- **Mobile (sm):** Single column, config panel in bottom sheet/drawer

---

## 8) Keyboard Shortcuts

- **Enter:** Send message (when input focused)
- **Shift + Enter:** New line in input
- **Cmd/Ctrl + K:** Clear chat
- **Cmd/Ctrl + /:** Focus input

---

## 9) Accessibility

- **ARIA labels** on all interactive elements
- **Keyboard navigation** support
- **Screen reader** friendly message structure
- **High contrast** mode support

---

## 10) Performance Considerations

### Chat History

- Limit stored messages to **100 messages** in memory
- Older messages pruned automatically
- Option to export before clearing

### Streaming

- Debounce partial updates (every 50-100ms)
- Avoid re-renders on every chunk
- Use virtual scrolling for very long conversations

### Token Counting

- Estimate tokens client-side for UX
- Use server response for accurate count

---

## 11) Implementation Status

✅ **Implemented** - Playground page follows this spec completely
