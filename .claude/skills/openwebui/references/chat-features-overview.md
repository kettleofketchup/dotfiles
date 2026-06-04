# Chat Features Overview

Open WebUI provides a comprehensive set of chat features designed to enhance your interactions with AI models.

## Core Chat Features

- **Folders & Projects**: Transform folders into powerful project workspaces with custom system prompts and attached knowledge bases.
- **URL Parameters**: Configure chat sessions through URL parameters, enabling quick setup of models, tools, and other features.
- **Chat Parameters**: Control system prompts and advanced parameters at different levels (per-chat, per-account, or per-model).
- **Autocomplete**: AI-powered text prediction that helps you write prompts faster using a task model.
- **Chat Sharing**: Share conversations locally or via the Open WebUI Community platform with controllable privacy settings.
- **History & Search**: Navigate and search your previous conversations, or allow models to search them autonomously via native tools.
- **Temporal Awareness**: How models understand time and date, including native tools for precise time calculations.
- **Reasoning & Thinking Models**: Specialized support for models that generate internal chains of thought using thinking tags.
- **Follow-Up Prompts**: Automatic generation of suggested follow-up questions after model responses.
- **Skill Mentions**: Use `$` in the chat input to mention and activate Skills on-the-fly, injecting their manifests into the conversation.
- **Writing & Content Blocks**: Responses from models that include colon-fence blocks (e.g., `:::writing`, `:::code_execution`, `:::search_results`) are automatically rendered as formatted content in a styled container with a copy button. This is commonly used by newer OpenAI models to distinguish different types of output (prose, code results, search results) from the main response text.

---

# Autocomplete

Open WebUI offers an **AI-powered Autocomplete** feature that suggests text completions in real-time as you type your prompt. It acts like a "Copilot" for your chat input, helping you craft prompts faster using your configured task model.

## How It Works

When enabled, Open WebUI monitors your input in the chat box. When you pause typing, it sends your current text to a lightweight **Task Model**. This model predicts the likely next words or sentences, which appear as "ghost text" overlaying your input.

- **Accept Suggestion**: Press `Tab` (or the `Right Arrow` key) to accept the suggestion.
- **Reject/Ignore**: Simply keep typing to overwrite the suggestion.

**Performance Recommendation**: Use a small, fast, **non-reasoning** model (Llama 3.2 1B/3B, Qwen 3 0.6B/3B, Gemma 3 1B, GPT-5 Nano). Avoid reasoning models (o1, o3) — their latency breaks real-time autocomplete.

## Configuration

The Autocomplete feature is controlled by a two-layer system: **Global** availability and **User** preference.

### 1. Global Configuration (Admin)

Admins control whether the autocomplete feature is available on the server.

**Admin Panel Settings:**
Go to **Admin Settings > Interface > Task Model** and toggle **Autocomplete Generation**.

### 2. User Configuration (Personal)

Even if enabled globally, individual users can turn it off for themselves if they find it distracting.

- Go to **Settings > Interface**.
- Toggle **Autocomplete Generation**.

If the Admin has disabled Autocomplete globally, users will **not** be able to enable it in their personal settings.

## Performance & Troubleshooting

### Why aren't suggestions appearing?
1. **Check Settings**: Ensure it is enabled in **both** Admin and User settings.
2. **Task Model**: Go to **Admin Settings > Interface** and verify a **Task Model** is selected. If no model is selected, the feature cannot generate predictions.
3. **Latency**: If your Task Model is large or running on slow hardware, predictions might arrive too late to be useful. Switch to a smaller model.
4. **Reasoning Models**: Ensure you are **not** using a "Reasoning" model (like o1 or o3), as their internal thought process creates excessive latency that breaks real-time autocomplete.

### Performance Impact
Autocomplete sends a request to your LLM essentially every time you pause typing (debounced).
- **Local Models**: This can consume significant GPU/CPU resources on the host machine.
- **API Providers**: This will generate a high volume of API calls (though usually with very short token counts). Be mindful of your provider's **Rate Limits** (Requests Per Minute/RPM and Tokens Per Minute/TPM) to avoid interruptions.

For multi-user instances running on limited local hardware, we recommend **disabling** Autocomplete to prioritize resources for actual chat generation.

---

# Follow-Up Prompts

Open WebUI auto-generates clickable follow-up question chips after each response (using the task model).

Configure in **Settings > Interface > Chat**:

| Setting | Default | Description |
|---------|---------|-------------|
| **Follow-Up Auto-Generation** | On | Generate suggestions after each response |
| **Keep Follow-Up Prompts in Chat** | Off | Show follow-ups for all messages (not just latest) |
| **Insert Follow-Up Prompt to Input** | Off | Insert into input field vs. send immediately |

To regenerate follow-ups for a specific response, use the community [Regenerate Followups](https://openwebui.com/f/silentoplayz/regenerate_followups) action.

---

# Message Queue

The **Message Queue** feature allows you to continue composing and sending messages while the AI is still generating a response. Instead of blocking your input until the current response completes, your messages are queued and automatically sent in sequence.

## How It Works

When you send a message while the AI is generating a response:

1. **Your message is queued** - It appears in a compact queue area just above the input box
2. **You can continue working** - Add more messages, edit queued messages, or delete them
3. **Automatic processing** - Once the current response finishes, all queued messages are combined and sent together

## Queue Management

Each queued message shows three action buttons:

| Action | Description |
|--------|-------------|
| **Send Now** | Interrupts the current generation and sends this message immediately |
| **Edit** | Removes the message from the queue and puts it back in the input field |
| **Delete** | Removes the message from the queue without sending |

### Combining Messages

When the AI finishes generating, all queued messages are **combined into a single prompt** (separated by blank lines) and sent together. This means:

- Multiple quick thoughts become one coherent message
- Context flows naturally between your queued inputs
- The AI receives everything at once for better understanding

## Persistence

The message queue is preserved when you navigate between chats within the same browser session:

- **Leaving a chat** - Queue is saved to session storage
- **Returning to the chat** - Queue is restored and processed
- **Closing the browser** - Queue is cleared (session storage only)

## Settings

You can disable the Message Queue feature if you prefer the traditional behavior:

1. Go to **Settings** > **Interface**
2. Find **Enable Message Queue** under the Chat section
3. Toggle it off

When disabled, sending a message while the AI is generating will:
- **Interrupt** the current generation
- **Send** your new message immediately

Message Queue is **enabled by default**. The toggle allows you to choose between:
- **Queue mode** (default) - Messages queue up until generation completes
- **Interrupt mode** - New messages stop current generation immediately

## Summary

| Feature | Behavior |
|---------|----------|
| **Enabled** | Messages queue during generation, sent together when complete |
| **Disabled** | New messages interrupt current generation immediately |
| **Persistence** | Queue survives navigation within session |
| **Actions** | Send Now, Edit, Delete for each queued item |
