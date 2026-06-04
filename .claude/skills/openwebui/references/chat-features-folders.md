# Folders & Projects

Open WebUI provides folder-based organization that turns chat containers into **project workspaces**. Folders allow grouping related conversations and defining custom system prompts and knowledge bases that apply to all chats within them.

## Enabling Folders

Folders are enabled by default.

- **Environment Variable**: `ENABLE_FOLDERS` (default: `True`)
- **User permission**: `USER_PERMISSIONS_FEATURES_FOLDERS` (default: `True`)

## Core Features

### Creating Folders

1. In the **sidebar**, click the **+ button** next to "Chats" or right-click in the chat list.
2. Select **"New Folder"**, enter a name, click **Save**.

### Moving Conversations into Folders

- **Drag and Drop**: Drag any conversation from the sidebar into a folder.
- **Right-click Menu**: Right-click on a conversation and select "Move to Folder".

### Nested Folders

- Right-click a folder and select **"Create Folder"** to create a subfolder.
- Drag a folder onto another folder to make it a subfolder.
- Subfolder names must be unique within the same parent (duplicates get a number appended, e.g., "Notes 1").

### Starting a Chat in a Folder

Click on a folder in the sidebar to make it the **active workspace**. New chats created while a folder is active are placed inside it and **inherit the folder's settings** (system prompt and knowledge).

## Folder Settings (Project Configuration)

Hover over a folder > click three-dot menu > **Edit**:

| Setting | Description |
|---------|-------------|
| **Folder Name** | Display name for the folder |
| **Background Image** | Upload a visual background |
| **System Prompt** | Prepended to every new conversation in the folder |
| **Attached Knowledge** | Knowledge bases/files included as context for all folder chats |

The System Prompt field only appears if you have the permission to set system prompts.

## Tags (Complementary Organization)

Tags provide flexible keyword labels for conversations:

- **Adding Tags**: Apply keyword labels based on content or purpose.
- **Searching by Tags**: Filter conversations by tags using the search feature.
- Tags can be added or removed at any time and don't affect folder structure.
