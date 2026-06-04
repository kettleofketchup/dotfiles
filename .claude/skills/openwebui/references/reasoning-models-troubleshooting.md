# Reasoning Models - Streaming, API & Troubleshooting

## Streaming vs Non-Streaming

### Streaming Mode (Default)

In streaming mode (`stream: true`), Open WebUI processes tokens as they arrive and can detect reasoning blocks in real-time. This generally works well without additional configuration.

### Non-Streaming Mode

In non-streaming mode (`stream: false`), the entire response is returned at once. **This is where most parsing issues occur** because:

1. The response arrives as a single block of text
2. Without the reasoning parser, no post-processing separates the `<think>` content
3. The raw response is displayed as-is

If you're using non-streaming requests (via API or certain configurations), **the reasoning parser is essential** for proper thinking block separation.

## API Usage

When using the Open WebUI API with reasoning models:

```json
{
  "model": "qwen3:32b",
  "messages": [
    {"role": "user", "content": "Solve: What is 234 * 567?"}
  ],
  "stream": true
}
```

**Recommendation:** Use `"stream": true` for the most reliable reasoning block parsing.

## Troubleshooting

### Thinking Content Merged with Final Answer

**Symptom:** When using a reasoning model, the entire response (including `<think>...</think>` blocks) is displayed as the final answer, instead of being separated into a hidden/collapsible thinking section.

**Expected behavior:** The thinking content should be hidden or collapsible, with only the final answer visible.

### For Ollama Users

The most common cause is that Ollama is not configured with the correct **reasoning parser**. When running Ollama, you need to specify the `--reasoning-parser` flag to enable proper parsing of thinking blocks.

#### Step 1: Configure the Reasoning Parser

When starting Ollama, add the `--reasoning-parser` flag:

```bash
# For DeepSeek-R1 style reasoning (recommended for most models)
ollama serve --reasoning-parser deepseek_r1

# Alternative parsers (if the above doesn't work for your model)
ollama serve --reasoning-parser qwen3
ollama serve --reasoning-parser deepseek_v3
```

For most reasoning models, including Qwen3 and DeepSeek variants, use `--reasoning-parser deepseek_r1`. This parser handles the standard `<think>...</think>` format used by most reasoning models.

#### Step 2: Restart Ollama

```bash
pkill ollama  # Linux/macOS
ollama serve --reasoning-parser deepseek_r1
```

#### Step 3: Verify

Start a new chat with your reasoning model and ask a reasoning question. Thinking content should appear in a collapsible section.

### Available Reasoning Parsers

| Parser | Description | Use Case |
|--------|-------------|----------|
| `deepseek_r1` | DeepSeek R1 format | Most reasoning models, including Qwen3 |
| `deepseek_v3` | DeepSeek V3 format | Some DeepSeek variants |
| `qwen3` | Qwen3-specific format | If `deepseek_r1` doesn't work with Qwen |

### Troubleshooting Checklist

#### 1. Verify Ollama Is Running with Reasoning Parser

Check if Ollama was started with the correct flag:

```bash
# Check the Ollama process
ps aux | grep ollama
# or on Windows:
Get-Process -Name ollama | Format-List *
```

Look for `--reasoning-parser` in the command line arguments.

#### 2. Check Model Compatibility

Not all models output reasoning in the same format. Verify your model's documentation for:

- What tags it uses for thinking content (e.g., `<think>`, `<reasoning>`, etc.)
- Whether it requires specific prompting to enable thinking mode

#### 3-5. Additional checks

- Enable streaming (default in Chat Controls sidebar)
- Update Open WebUI: `docker pull ghcr.io/open-webui/open-webui:main`
- Test model directly: `ollama run your-model "What is 15 + 27 step by step?"` — look for `<think>` tags

### Reasoning Lost Between Tool Calls

**Symptom:** The model seems to "forget" what it was thinking about after a tool call completes.

**Possible Causes:**
1. The model doesn't output reasoning in a captured format (`reasoning_content`, `reasoning`, or `thinking` delta fields)
2. The model uses text-based thinking tags that aren't being parsed as reasoning blocks

**Solution:** Check if your model outputs reasoning through:
- Structured delta fields (`reasoning_content`, `reasoning`, `thinking`)
- Text-based tags that Open WebUI detects (ensure reasoning tag detection is enabled)

### Anthropic Extended Thinking + Tool Calls

**Symptom:** Tool calls fail with `Expected thinking or redacted_thinking, but found text`.

**Cause:** Open WebUI follows the OpenAI API standard and serializes reasoning as text in tags (`<think>...</think>`). Anthropic requires structured `{"type": "thinking"}` blocks. These are incompatible when using both features together.

**Workarounds:** Create a Pipe Function to convert format, or disable Extended Thinking for tool-calling workflows.

### Stateful Reasoning Models (GPT-5.2, etc.)

Some models keep reasoning internal. Open WebUI can only preserve reasoning actually returned by the model. If a summary is returned, that summary is preserved and sent back.

## Frequently Asked Questions

**Why is the thinking block showing as raw text?** The model uses tags not in the default `reasoning_tags` list. Add correct tags in Model Settings or Chat Controls.

**Does the model see its own thinking?** Yes — within a turn (during tool calls) and across turns. Open WebUI serializes reasoning with original tags in the assistant message `content` field.

**How is reasoning sent during tool calls?** As text with original tags in the assistant `content` field. Works with most OpenAI-compatible providers; Anthropic may expect structured `{"type": "thinking"}` blocks.

