# GAUSS AI

<!-- mcp-name: io.github.ec78/gauss-ai -->

**GAUSS AI** helps an AI assistant work with the [GAUSS](https://www.aptech.com/) programming language without guessing. It runs on your machine as an MCP server (for Claude Code, Claude Desktop and other MCP clients) and as a command-line tool, `gauss-ai`.

- **Search the official GAUSS documentation**, downloaded once to your machine, and read any page or section in full.
- **Check GAUSS code deterministically**: documented call signatures, documented preconditions (for example, `invpd` needs a symmetric positive-definite matrix), syntax, unknown or invented functions, and statements that reach outside GAUSS. No model makes these decisions.
- **Run checked code in your own GAUSS**, optionally. Only after you approve the exact code, once, and only code that computes in memory.

Status: **alpha**. gauss-ai is an unofficial, independent project, not affiliated with or endorsed by Aptech Systems, Inc. GAUSS is a trademark of Aptech Systems, Inc.

## Quickstart

You need Python 3.10 or newer. GAUSS itself is optional; without it, search and validation still work. Run every command below in one terminal (PowerShell or Command Prompt on Windows, Terminal on macOS or Linux), from any folder: the `pip` there must belong to the Python you want gauss-ai installed in, and the `claude mcp` commands register the server for your user account, not for a folder.

**1. Install**

```
pip install "gauss-ai[mcp]"
gauss-ai version
```

`pipx install "gauss-ai[mcp]"` or `uv tool install "gauss-ai[mcp]"` work too, and keep it out of your other Python environments. The `[mcp]` extra is needed only for the MCP server; the CLI alone has no third-party dependencies.

**2. Download the documentation (once)**

```
gauss-ai docs fetch
gauss-ai doctor
```

This downloads the published GAUSS documentation (about 8 MB) from docs.aptech.com into `~/.gauss-ai/docs/` and configures it. It runs only when you run it. It takes a few minutes; let it finish, since an interrupted download starts over (it never leaves a partial copy). `gauss-ai doctor` should end with `Overall: PASS` or `Overall: WARN`. A warning that no workspace parent is configured is expected and harmless: only `gauss-ai repair` uses one.

**3. Connect your MCP client**

Claude Code:

```
claude mcp add --transport stdio --scope user gauss-ai -- gauss-ai-mcp
```

Claude Desktop (Windows and macOS): add this to `claude_desktop_config.json` (Settings → Developer → Edit Config), then restart Claude Desktop. Desktop may not find `gauss-ai-mcp` on its own, so use the full path that `where gauss-ai-mcp` (Windows) or `which gauss-ai-mcp` (macOS) prints:

```json
{
  "mcpServers": {
    "gauss-ai": {
      "command": "C:\\full\\path\\to\\gauss-ai-mcp.exe",
      "args": []
    }
  }
}
```

In a new conversation, ask the assistant to start a gauss-ai session. It should report `docs_root_configured: true`.

**4. Real GAUSS (optional)**

Point gauss-ai at your **terminal** GAUSS executable (`tgauss` or `tgauss.exe`, never the GUI), and make it the default runner. On Windows it is `tgauss.exe` in your GAUSS folder. On macOS, use the `tgauss` script in your GAUSS home folder, not the program inside the app, since the script sets up GAUSS's environment. On Linux, it is in the folder where you unpacked GAUSS and ran `./ginstall`.

```
gauss-ai config set gauss-executable "C:\gauss26\tgauss.exe"
gauss-ai config set default-runner gauss
```

Then give the server process your opt-in, `GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1`. Only whoever starts the server can set it, and every run still needs your own "yes":

- Claude Code: `claude mcp remove gauss-ai --scope user`, then
  `claude mcp add --transport stdio --scope user gauss-ai -e GAUSS_AI_MCP_ALLOW_REAL_GAUSS=1 -- gauss-ai-mcp`
  (the server name must come before `-e`, which takes several values)
- Claude Desktop: add `"env": { "GAUSS_AI_MCP_ALLOW_REAL_GAUSS": "1" }` to the entry above, and restart.

Set it for yourself only. Never put it in a project's shared `.mcp.json`, where it would turn real execution on for everyone who clones the project.

To check: in a new conversation, a new session must report `real_gauss_allowed: true`. That confirms the opt-in, not that GAUSS starts; the first approved run shows that. For a first run, ask the assistant to validate and run `x = { 1, 1 }; print sumc(x);`, and answer the prompt yourself. Code must call at least one documented function to be eligible, so `print 1+1;` is refused, by design.

**5. Upgrading**

Close your MCP client (on Windows a running server locks its files), run `pip install -U "gauss-ai[mcp]"`, then reopen the client and start a new conversation. If a session reports a `server_version` other than the one you installed, or a tool asks for an argument its description does not mention, restart the client again: some clients keep old tool descriptions.

## What it will and won't do

- Code from the assistant is **never run** unless gauss-ai's own checks rate it `handoff_candidate` and you approve that exact code. One approval runs it once, in a temporary directory that is deleted afterwards.
- Code that reaches outside GAUSS is **always blocked** from running: OS commands, other programs, `run`/`#include`, directory changes, any file read, write or delete, web data APIs and databases.
- A verdict is **evidence, not a guarantee** of correct results. Much real code is `review_required` (for example, most loops, or an argument computed by an expression, since expressions are never evaluated), and gauss-ai says exactly what it could not check.
- No telemetry. The only network access is `gauss-ai docs fetch`, run by you, and a model provider you explicitly enable for the optional built-in chat.

## Platforms

Search, validation and the MCP server are tested on Windows, Linux and macOS. Running real GAUSS has been verified on Windows (GAUSS 26.1) only; on Linux and macOS the `tgauss` path is implemented but not yet verified. Reports are welcome.

## The GAUSS documentation

gauss-ai never bundles, mirrors or redistributes the GAUSS documentation. Each user downloads Aptech's public documentation from docs.aptech.com with `gauss-ai docs fetch`. Searches run locally, and excerpts go only to your own MCP client.

## More

- [Full README and guides](https://github.com/ec78/gauss-ai#readme)
- [MCP server reference](https://github.com/ec78/gauss-ai/blob/main/docs/mcp-server.md)
- [Known limitations](https://github.com/ec78/gauss-ai/blob/main/KNOWN_LIMITATIONS.md)
- [Report an issue](https://github.com/ec78/gauss-ai/issues)

MIT License.
