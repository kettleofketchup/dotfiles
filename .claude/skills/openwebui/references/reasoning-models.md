# Reasoning & Thinking Models

Open WebUI provides first-class support for models that exhibit "thinking" or "reasoning" behaviors (such as DeepSeek R1, OpenAI o1, and others). These models often generate internal chains of thought before providing a final answer.

## How Thinking Tags Work

When a model generates reasoning content, it typically wraps that content in specific XML-like tags (e.g., `<think>...</think>` or `<thought>...</thought>`).

Open WebUI automatically:
1. **Detects** these tags in the model's output stream.
2. **Extracts** the content between the tags.
3. **Renders** the extracted content in a collapsible UI element labeled "Thought" or "Thinking".

This keeps the main chat interface clean while still giving you access to the model's internal processing.

## The `reasoning_tags` Parameter

You can customize which tags Open WebUI should look for using the `reasoning_tags` parameter. This can be set on a **per-chat** or **per-model** basis.

### Default Tags
By default, Open WebUI looks for several common reasoning tag pairs:
- `<think>`, `</think>`
- `<thinking>`, `</thinking>`
- `<reason>`, `</reason>`
- `<reasoning>`, `</reasoning>`
- `<thought>`, `</thought>`
- `<|begin_of_thought|>`, `<|end_of_thought|>`

### Customization
If your model uses different tags, you can provide a list of tag pairs in the `reasoning_tags` parameter. Each pair is a tuple or list of the opening and closing tag.

## Configuration & Behavior

- **Stripping from Payload**: The `reasoning_tags` parameter is an Open WebUI-specific control and is **stripped** from the payload before being sent to the LLM backend (OpenAI, Ollama, etc.).
- **Chat History**: Reasoning content is preserved in chat history and **sent back to the model** across turns. When building messages for subsequent requests, Open WebUI serializes the reasoning content with its original tags (e.g., `<think>...</think>`) and includes it in the assistant message's `content` field.
- **UI Rendering**: Internally, reasoning blocks are processed and rendered using a specialized UI component. When saved or exported, they may be represented as HTML `<details type="reasoning">` tags.

## Open WebUI Settings

Open WebUI provides several built-in settings to configure reasoning model behavior. These can be found in:

- **Chat Controls** (sidebar) > **Advanced Parameters** -- per-chat settings
- **Workspace** > **Models** > **Edit Model** > **Advanced Parameters** -- per-model settings (Admin only)
- **Admin Panel** > **Settings** > **Models** > select a model > **Advanced Parameters** -- alternative per-model settings location

### Reasoning Tags Setting

| Option | Description |
|--------|-------------|
| **Default** | Uses the system default behavior |
| **Enabled** | Explicitly enables reasoning tag detection using default `<think>...</think>` tags |
| **Disabled** | Turns off reasoning tag detection entirely |
| **Custom** | Allows you to specify custom start and end tags |

#### Using Custom Tags

If your model uses non-standard reasoning tags (e.g., `<reasoning>...</reasoning>` or `[thinking]...[/thinking]`), select **Custom** and enter:

- **Start Tag**: The opening tag (e.g., `<reasoning>`)
- **End Tag**: The closing tag (e.g., `</reasoning>`)

### think (Ollama)

This Ollama-specific setting enables or disables the model's built-in reasoning feature:

| Option | Description |
|--------|-------------|
| **Default** | Uses Ollama's default behavior |
| **On** | Explicitly enables thinking mode for the model |
| **Off** | Disables thinking mode |

This setting sends the `think` parameter directly to Ollama. It's separate from how Open WebUI parses the response -- you may need both this setting AND proper reasoning tags configuration for the full experience.

### Reasoning Effort

For models that support variable reasoning depth (like some API providers), this setting controls how much effort the model puts into reasoning:

- Common values: `low`, `medium`, `high`
- Some providers accept numeric values

Reasoning Effort is only applicable to models from specific providers that support this parameter. It has no effect on local Ollama models.

## Interleaved Thinking with Tool Calls

When a model uses **native function calling** (tool use) within a single turn, Open WebUI preserves the reasoning content and sends it back to the API for subsequent calls within that turn. This enables true "interleaved thinking" where:

1. Model generates reasoning > makes a tool call
2. Tool executes and returns results
3. Model receives: original messages + previous reasoning + tool call + tool result
4. Model continues reasoning > may make more tool calls or provide final answer
5. Process repeats until the turn completes

### How It Works

During a multi-step tool calling turn, Open WebUI:

1. **Captures** reasoning content from the model's response (via `reasoning_content`, `reasoning`, or `thinking` fields in the delta)
2. **Stores** it in content blocks alongside tool calls
3. **Serializes** the reasoning with its original tags (e.g., `<think>...</think>`) when building messages for the next API call
4. **Includes** the serialized content in the assistant message's `content` field

### How Reasoning Is Sent Back

When building the next API request during a tool call loop, Open WebUI serializes reasoning as **text wrapped in tags** inside the assistant message's `content` field:

```text
<think>Let me search for the current weather data...</think>
```

The message structure looks like:

```json
{
  "role": "assistant",
  "content": "<think>reasoning content here</think>",
  "tool_calls": [...]
}
```

### Provider Compatibility

| Provider Type | Compatibility |
|--------------|---------------|
| OpenAI-compatible APIs | Works -- reasoning is in the content text |
| Ollama | Works -- Ollama processes the message content |
| Anthropic (extended thinking) | Not supported -- Anthropic requires structured `{"type": "thinking"}` blocks, use a pipe function |
| OpenAI o-series (stateful) | Limited -- reasoning is hidden/internal, nothing to capture |

### Important Notes

- **Within-turn preservation**: Reasoning is preserved and sent back to the API within the same turn (while tool calls are being processed).
- **Cross-turn behavior**: Reasoning content **is** sent back to the API across turns, serialized with original tags in the assistant message's `content` field.
- **Text-based serialization**: Reasoning is sent as text wrapped in tags, not as structured content blocks. This works with most OpenAI-compatible APIs but may not align with provider-specific formats.

---

# Temporal Awareness (Date & Time)

Open WebUI injects `CURRENT_DATE` (YYYY-MM-DD), `CURRENT_TIME` (HH:MM), and `CURRENT_WEEKDAY` into the system prompt. Use `{{CURRENT_DATE}}` syntax in Prompts or Model Files.

## Native Temporal Tools (Agentic)

With **Native Function Calling** enabled, models get:
- **`get_current_timestamp`**: exact current Unix timestamp (UTC) and ISO string
- **`calculate_timestamp`**: relative time arithmetic ("3 days ago", "next Friday")

These tools allow the model to reason precisely about time, essential for searching history or scheduling tasks.
