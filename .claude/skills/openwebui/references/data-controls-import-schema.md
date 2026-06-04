# Chat Import JSON Schema Reference

## Top-Level Chat Object (Standard Format)

| Field | Type | Required | Description |
|---|---|---|---|
| `chat` | object | Yes | The conversation data |
| `meta` | object | No | Metadata: `tags` (array of strings). Defaults to `{}` |
| `pinned` | boolean | No | Whether the chat is pinned. Defaults to `false` |
| `folder_id` | string or null | No | ID of the folder to place the chat in. Defaults to `null` |
| `created_at` | integer or null | No | Unix timestamp (seconds) when created |
| `updated_at` | integer or null | No | Unix timestamp (seconds) when last updated |

## Chat Data Object

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | No | The conversation title. Defaults to `"New Chat"` |
| `models` | string[] | No | List of model identifiers used in the conversation |
| `history` | object | Yes | Contains the message tree |
| `options` | object | No | Chat-level options/parameters |

## History Object

| Field | Type | Required | Description |
|---|---|---|---|
| `currentId` | string | Yes | ID of the last message in the active branch |
| `messages` | object | Yes | Map of message ID to message object |

## Message Object

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Unique identifier for the message |
| `parentId` | string or null | Yes | ID of the parent message, or `null` for the first message |
| `childrenIds` | string[] | Yes | Array of child message IDs. Empty `[]` for last message |
| `role` | string | Yes | Either `"user"` or `"assistant"` |
| `content` | string | Yes | The message text (supports Markdown) |
| `model` | string | No | Model identifier (for assistant messages) |
| `done` | boolean | No | Whether the response is complete |
| `timestamp` | integer | No | Unix timestamp (seconds) for the message |
| `context` | string or null | No | Additional context for the message |

Messages use a **tree structure**: each message references its parent via `parentId` and children via `childrenIds`. This supports branching conversations. The `history.currentId` points to the last message in the active branch.

## Legacy Format

If objects in the array do NOT have a `chat` key, the entire object is treated as the chat data itself (wrapped in `{ "chat": <object> }` automatically). Structure is identical to the `chat` object above, without the wrapper fields.

## ChatGPT Export Format

Auto-detected when the first object in the array contains a `mapping` key. Import directly — Open WebUI handles the conversion.

## Minimal Working Example

```json
[{
  "title": "Quick Chat",
  "history": {
    "currentId": "msg-1",
    "messages": {
      "msg-1": {
        "id": "msg-1", "parentId": null, "childrenIds": [],
        "role": "user", "content": "Hello!"
      }
    }
  }
}]
```
