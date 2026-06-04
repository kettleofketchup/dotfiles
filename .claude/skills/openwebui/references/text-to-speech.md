# Text-to-Speech (TTS) - OpenAI Integration

## Requirements

- An OpenAI API key with access to the Audio API
- Open WebUI installed and running

## Quick Setup (UI)

1. Click your **profile icon** (bottom-left corner)
2. Select **Admin Panel**
3. Click **Settings** > **Audio** tab
4. Configure the following:

| Setting | Value |
|---------|-------|
| **Text-to-Speech Engine** | `OpenAI` |
| **API Base URL** | `https://api.openai.com/v1` |
| **API Key** | Your OpenAI API key |
| **TTS Model** | `tts-1` or `tts-1-hd` |
| **TTS Voice** | Choose from available voices |

5. Click **Save**

## Available Models

| Model | Description | Best For |
|-------|-------------|----------|
| `tts-1` | Standard quality, lower latency | Real-time applications, faster responses |
| `tts-1-hd` | Higher quality audio | Pre-recorded content, premium audio quality |

## Available Voices

OpenAI provides 6 built-in voices:

| Voice | Description |
|-------|-------------|
| `alloy` | Neutral, balanced |
| `echo` | Warm, conversational |
| `fable` | Expressive, British accent |
| `onyx` | Deep, authoritative |
| `nova` | Friendly, upbeat |
| `shimmer` | Soft, gentle |

Try different voices to find the one that best suits your use case. You can preview voices in OpenAI's documentation.

## Per-Model TTS Voice

You can assign a specific TTS voice to individual models, allowing different AI personas to have distinct voices. This is configured in the Model Editor.

### Setting a Model-Specific Voice

1. Go to **Workspace > Models**
2. Click the **Edit** (pencil) icon on the model you want to configure
3. Scroll down to find the **TTS Voice** field
4. Enter the voice name (e.g., `alloy`, `echo`, `shimmer`, `onyx`, `nova`, `fable`)
5. Click **Save**

### Voice Priority

When playing TTS audio, Open WebUI uses the following priority:

1. **Model-specific TTS voice** (if set in Model Editor)
2. **User's personal voice setting** (if configured in user settings)
3. **System default voice** (configured by admin)

This allows admins to give each AI persona a consistent voice while still letting users override with their personal preference when no model-specific voice is set.

### Use Cases

- **Character personas**: Give a "British Butler" model the `fable` voice, while an "Energetic Assistant" uses `nova`
- **Language learning**: Assign appropriate voices for different language tutors
- **Accessibility**: Set clearer voices for models designed for accessibility use cases

## Environment Variables Setup

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    environment:
      - AUDIO_TTS_ENGINE=openai
      - AUDIO_TTS_OPENAI_API_BASE_URL=https://api.openai.com/v1
      - AUDIO_TTS_OPENAI_API_KEY=sk-...
      - AUDIO_TTS_MODEL=tts-1
      - AUDIO_TTS_VOICE=alloy
```

### All TTS Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUDIO_TTS_ENGINE` | Set to `openai` | empty |
| `AUDIO_TTS_OPENAI_API_BASE_URL` | OpenAI API base URL | `https://api.openai.com/v1` |
| `AUDIO_TTS_OPENAI_API_KEY` | Your OpenAI API key | empty |
| `AUDIO_TTS_MODEL` | TTS model (`tts-1` or `tts-1-hd`) | `tts-1` |
| `AUDIO_TTS_VOICE` | Voice to use | `alloy` |

### General TTS Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUDIO_TTS_ENGINE` | TTS engine: empty (disabled), `openai`, `elevenlabs`, `azure`, `transformers` | empty |
| `AUDIO_TTS_MODEL` | TTS model | `tts-1` |
| `AUDIO_TTS_VOICE` | Default voice | `alloy` |
| `AUDIO_TTS_SPLIT_ON` | Split text on: `punctuation` or `none` | `punctuation` |
| `AUDIO_TTS_API_KEY` | API key for ElevenLabs or Azure TTS | empty |

### Azure TTS Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUDIO_TTS_AZURE_SPEECH_REGION` | Azure Speech region | `eastus` |
| `AUDIO_TTS_AZURE_SPEECH_BASE_URL` | Custom Azure Speech base URL (optional) | empty |
| `AUDIO_TTS_AZURE_SPEECH_OUTPUT_FORMAT` | Audio output format | `audio-24khz-160kbitrate-mono-mp3` |

### OpenAI-Compatible TTS Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUDIO_TTS_OPENAI_API_BASE_URL` | OpenAI-compatible TTS API base URL | `https://api.openai.com/v1` |
| `AUDIO_TTS_OPENAI_API_KEY` | OpenAI TTS API key | empty |
| `AUDIO_TTS_OPENAI_PARAMS` | Additional JSON params for OpenAI TTS | empty |

## Testing TTS

1. Start a new chat
2. Send a message to any model
3. Click the **speaker icon** on the AI response to hear it read aloud

## Response Splitting

Configure in **Admin Panel > Settings > Audio > Response Splitting**: `Punctuation` (default, sentence boundaries), `Paragraphs` (paragraph breaks), `None` (whole response). Punctuation recommended for best streaming + pacing.

## External TTS Services

Docker: set `AUDIO_TTS_OPENAI_API_BASE_URL=http://host.docker.internal:5050/v1` (Windows/Mac) or host IP (Linux).

## Troubleshooting

- **No audio**: verify API key has Audio API access, check Base URL and browser console (F12)
- **Quality issues**: switch `tts-1` to `tts-1-hd` (higher latency)
- **Rate limits**: cache common phrases, use `tts-1` (fewer tokens)

## Cost

OpenAI charges per character. `tts-1-hd` costs more than `tts-1`. Free alternative: OpenAI Edge TTS (Microsoft's Edge browser TTS).
