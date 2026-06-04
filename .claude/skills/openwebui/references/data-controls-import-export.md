# Import & Export

Open WebUI provides tools to backup your chat history and restore it later, or migrate conversations from other platforms.

## Accessing Import & Export

1. Click on your **profile name** or avatar in the bottom-left corner of the sidebar.
2. Select **Settings** from the menu.
3. Navigate to the **Data Controls** tab.
4. Use the **Import Chats** or **Export Chats** buttons.

## Exporting Chats

Click the **Export Chats** button to download all your conversations as a JSON file. This backup includes:

- All chat messages and their metadata
- Model information used in each conversation
- Timestamps and conversation structure

It's a good practice to periodically export your chats, especially before major updates or migrations.

## Importing Chats

Click the **Import Chats** button and select a JSON file to restore conversations. Open WebUI supports importing from:

- **Open WebUI exports**: Native JSON format from previous exports
- **ChatGPT exports**: Conversations exported from OpenAI's ChatGPT (auto-detected and converted)
- **Custom JSON files**: Any JSON file that follows the expected structure documented below

### Import Behavior

- Imported chats are added to your existing conversations (they don't replace them)
- Each imported chat receives a new unique ID, so re-importing the same file will create duplicates
- If using ChatGPT exports, the format is automatically detected and converted

## Chat Import JSON Schema

The import file must be a **JSON array** of chat objects. There are two accepted formats: the **standard format** (used by Open WebUI exports) and a **legacy format**.

### Standard Format (Recommended)

Each object in the array should have a `chat` key containing the conversation data:

```json
[
  {
    "chat": {
      "title": "My Conversation",
      "models": ["llama3.2"],
      "history": {
        "currentId": "message-id-2",
        "messages": {
          "message-id-1": {
            "id": "message-id-1",
            "parentId": null,
            "childrenIds": ["message-id-2"],
            "role": "user",
            "content": "Hello, how are you?",
            "timestamp": 1700000000
          },
          "message-id-2": {
            "id": "message-id-2",
            "parentId": "message-id-1",
            "childrenIds": [],
            "role": "assistant",
            "content": "I'm doing well, thank you!",
            "model": "llama3.2",
            "done": true,
            "timestamp": 1700000005
          }
        }
      }
    },
    "meta": {
      "tags": ["greeting"]
    },
    "pinned": false,
    "folder_id": null,
    "created_at": 1700000000,
    "updated_at": 1700000005
  }
]
```

### Legacy Format

If the objects in the array do **not** have a `chat` key, the entire object is treated as the chat data itself (i.e. the object is wrapped in `{ "chat": <object> }` automatically). The structure is identical to the `chat` object above, just without the `chat`, `meta`, `pinned`, `folder_id`, `created_at`, and `updated_at` wrapper fields.

### Field Reference

See [data-controls-import-schema.md](data-controls-import-schema.md) for the complete field reference tables (top-level, chat data, history, and message objects).

### ChatGPT Export Format

ChatGPT exports are automatically detected when the first object in the array contains a `mapping` key. You don't need to manually convert ChatGPT exports -- just import the file directly and Open WebUI will handle the conversion.

### Minimal Working Example

The smallest valid import file looks like this:

```json
[
  {
    "title": "Quick Chat",
    "history": {
      "currentId": "msg-1",
      "messages": {
        "msg-1": {
          "id": "msg-1",
          "parentId": null,
          "childrenIds": [],
          "role": "user",
          "content": "Hello!"
        }
      }
    }
  }
]
```

This uses the legacy format (no `chat` wrapper) with a single user message.

## FAQ

- **Will importing overwrite existing chats?** No, imported chats are added alongside existing ones.
- **Can I import from Claude/Gemini?** No built-in converter; transform to the JSON format above.
- **Size limit?** No hard limit; large files may take longer and depend on server memory.
- **Import same file twice?** Creates duplicates (each import gets fresh IDs).
- **Supported roles?** `"user"` and `"assistant"` only; system messages are set via model config.
