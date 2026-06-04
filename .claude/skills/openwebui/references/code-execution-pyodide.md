# Python Manual Code Execution (Pyodide)

Open WebUI includes a browser-based Python environment using Pyodide (WebAssembly). Run Python scripts directly in your browser with no server-side setup.

The Pyodide worker is **persistent** -- variables, imported modules, and files written to the virtual filesystem are retained between executions within the same session.

## Running Code Manually

1. Ask an LLM to write Python code
2. A **Run** button appears in the code block
3. Click to execute using Pyodide
4. Output appears below the code block

## Supported Libraries

Auto-detected from import statements and loaded on demand:

| Package | Use case |
|---------|----------|
| micropip | Package installer (internal use) |
| requests | HTTP requests |
| beautifulsoup4 | HTML/XML parsing |
| numpy | Numerical computing |
| pandas | Data analysis and manipulation |
| matplotlib | Chart and plot generation |
| seaborn | Statistical data visualization |
| scikit-learn | Machine learning |
| scipy | Scientific computing |
| regex | Advanced regular expressions |
| sympy | Symbolic mathematics |
| tiktoken | Token counting for LLMs |
| pytz | Timezone handling |

Python standard library fully available (json, csv, math, datetime, os, io, etc.).

**Cannot install additional libraries.** Packages requiring C extensions, system calls, or native binaries (torch, tensorflow, opencv, psycopg2) are not available in Pyodide.

## Persistent File System (`/mnt/uploads/`)

A persistent virtual filesystem backed by browser IndexedDB (IDBFS):

- **Cross-execution persistence**: files from one execution accessible in subsequent runs.
- **Cross-reload persistence**: files survive page reloads.
- **Auto upload mounting**: files attached to messages are placed in `/mnt/uploads/` before execution.
- **File browser panel**: appears in chat controls sidebar when Code Interpreter is enabled.

```python
import os
print(os.listdir('/mnt/uploads'))  # List uploaded files

import pandas as pd
df = pd.read_csv('/mnt/uploads/data.csv')
df.to_csv('/mnt/uploads/result.csv', index=False)  # Downloadable via file browser
```

Pyodide-only: when using Jupyter engine, files are managed through Jupyter's own filesystem.

## Browser Compatibility

### Microsoft Edge: Pyodide Crashes

`STATUS_ACCESS_VIOLATION` crash caused by Edge's enhanced security mode.

**Solutions:**
1. `edge://settings/privacy/security` > turn off **"Enhance your security on the web"**
2. Use Chrome or Firefox instead
3. Switch to Jupyter backend: `CODE_INTERPRETER_ENGINE=jupyter`

## Tips

- Tell the LLM it's in a "Pyodide environment" or "code interpreter" for better code generation
- Ask for "base64 data URL output" for images; use `print()` for all output
- Verify required libraries are in the supported list above before requesting them
