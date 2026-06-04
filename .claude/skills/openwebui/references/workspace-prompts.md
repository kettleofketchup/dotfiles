# Prompts

Reusable slash commands that turn complex instructions into one-click forms.

Prompts let you save frequently used instructions as slash commands. Type `/summarize` in any chat and the full prompt fires instantly. Add custom input variables and users get a popup form with dropdowns, date pickers, and text fields before the prompt is sent. No one needs to remember the exact wording or structure.

Every change is tracked with full version history. Roll back to a previous version, compare changes, and share prompts across your team with access controls.

## Why Prompts?

### Stop retyping the same instructions

Save the prompt once, use it with `/command`. Bug report templates, meeting minutes, code reviews, content briefs: anything you type more than twice should be a prompt.

### Turn prompts into interactive forms

Add typed input variables (dropdowns, date pickers, number fields, checkboxes) and users get a clean form instead of editing raw text. Non-technical users can run complex prompts without understanding the syntax.

### Version history with rollback

Every change creates a new version. Compare versions side-by-side, restore a previous version to production, and track who changed what.

### Controlled sharing

Share prompts with specific users or groups. Public prompts appear in everyone's `/` suggestions. Private prompts stay in your own workspace.

## Key Features

| Feature | Description |
| :--- | :--- |
| **Slash commands** | Type `/command` to insert the full prompt |
| **Input variable forms** | Typed fields (text, dropdown, date, number, checkbox, and more) generate a popup form |
| **Version history** | Full change tracking with commit messages, rollback, and production pinning |
| **System variables** | `{{CURRENT_DATE}}`, `{{USER_NAME}}`, `{{CLIPBOARD}}` auto-replaced at runtime |
| **Access control** | Share with specific users, groups, or make public |
| **Enable/Disable toggle** | Deactivate prompts without deleting them |
| **Tags** | Organize and filter your prompt library |

## Creating a Prompt

Navigate to **Workspace > Prompts** and click **+ New Prompt**.

| Field | Description |
| :--- | :--- |
| **Name** | Descriptive title for identification |
| **Tags** | Categorize for filtering |
| **Access** | Control who can view and use the prompt |
| **Command** | The slash command trigger (e.g., `/summarize`) |
| **Prompt Content** | The actual text sent to the model, with variables |
| **Commit Message** | Optional description of changes for version tracking |

Use clear variable names (`{{your_name}}` not `{{var1}}`), add descriptive `placeholder` text, provide `default` values where sensible, and mark only truly essential fields as `:required`. Public prompts appear in every user's `/` suggestions, so be selective about what you make public. Use the enable/disable toggle to shelve prompts you're not actively using.

## Variables

### System variables

Automatically replaced with their value at runtime:

| Variable | Description |
| :--- | :--- |
| `{{CLIPBOARD}}` | Content from your clipboard (requires clipboard permission) |
| `{{CURRENT_DATE}}` | Current date |
| `{{CURRENT_DATETIME}}` | Current date and time |
| `{{CURRENT_TIME}}` | Current time |
| `{{CURRENT_TIMEZONE}}` | Current timezone |
| `{{CURRENT_WEEKDAY}}` | Current day of the week |
| `{{USER_NAME}}` | Your display name |
| `{{USER_EMAIL}}` | Your email address |
| `{{USER_BIO}}` | Bio from Settings > Account > User Profile (unreplaced if not set) |
| `{{USER_GENDER}}` | Gender from Settings > Account > User Profile (unreplaced if not set) |
| `{{USER_BIRTH_DATE}}` | Birth date from Settings > Account > User Profile (unreplaced if not set) |
| `{{USER_AGE}}` | Age calculated from birth date (unreplaced if not set) |
| `{{USER_LANGUAGE}}` | Your selected language |
| `{{USER_LOCATION}}` | Your location (requires HTTPS + Settings > Interface toggle) |

### Custom input variables

Use `{{variable_name}}` for simple text input. Use `{{variable_name | type:property="value"}}` for typed inputs. All variables are **optional by default** — add `:required` to mandate: `{{title | text:required}}`

### Available input types

| Type | Description | Example |
| :--- | :--- | :--- |
| **text** | Single-line text (default) | `{{name \| text:placeholder="Enter name":required}}` |
| **textarea** | Multi-line text | `{{description \| textarea:required}}` |
| **select** | Dropdown menu | `{{priority \| select:options=["High","Medium","Low"]:required}}` |
| **number** | Numeric input | `{{count \| number:min=1:max=100:default=5}}` |
| **checkbox** | Boolean toggle | `{{include_details \| checkbox:label="Include analysis"}}` |
| **date** | Date picker | `{{start_date \| date:required}}` |
| **datetime-local** | Date and time picker | `{{appointment \| datetime-local}}` |
| **color** | Color picker | `{{brand_color \| color:default="#FFFFFF"}}` |
| **email** | Email field with validation | `{{email \| email:required}}` |
| **range** | Slider | `{{rating \| range:min=1:max=10}}` |
| **tel** | Phone number | `{{phone \| tel}}` |
| **time** | Time picker | `{{meeting_time \| time}}` |
| **url** | URL with validation | `{{website \| url:required}}` |
| **month** | Month and year (Chrome/Edge only, falls back to text in Firefox/Safari) | `{{billing_month \| month}}` |
| **map** | Interactive map for coordinates (experimental) | `{{location \| map}}` |

## Message and Prompt Modifiers

These modifiers are especially useful for task model prompts (title generation, tag generation, follow-up suggestions) where conversations contain long messages like pasted documents or code.

### Prompt truncation

The `{{prompt}}` variable supports character-based truncation:

| Modifier | What it does |
| :--- | :--- |
| `{{prompt:start:N}}` | First N characters |
| `{{prompt:end:N}}` | Last N characters |
| `{{prompt:middletruncate:N}}` | First half + last half, N characters total |

### Message selectors vs pipe filters

The `{{MESSAGES}}` variable has two distinct modifier types that work at different levels:

**Message selectors** (colon `:`) control **how many messages** to include:

| Selector | What it does | Example |
| :--- | :--- | :--- |
| `START:N` | First N messages | `{{MESSAGES:START:5}}` |
| `END:N` | Last N messages | `{{MESSAGES:END:5}}` |
| `MIDDLETRUNCATE:N` | First N/2 + last N/2 messages | `{{MESSAGES:MIDDLETRUNCATE:6}}` |

**Pipe filters** (`|`) truncate content per message: `{{MESSAGES|start:300}}`, `{{MESSAGES|end:300}}`, `{{MESSAGES|middletruncate:500}}`.

**Combine**: `{{MESSAGES:END:2|middletruncate:500}}` = last 2 messages, each capped at 500 chars.

**Warning**: Selectors count messages (not chars). `{{MESSAGES:MIDDLETRUNCATE:500}}` selects 500 messages. Use pipe filter for char limits.

## Version History

Every save creates a new version. History sidebar shows commit message, author, timestamp, and "Live" badge. Preview versions by clicking; **Set as Production** to restore; delete old versions (not the active one). As of v0.5.0, all custom input variables are optional by default.

## Limitations

- Public prompts appear in every user's `/` suggestions — use the enable/disable toggle to reduce clutter
- Variables are optional unless marked `:required`
