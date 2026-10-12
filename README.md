# Tizen TV Unified MCP Server (`tizen-tv-mcp`)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Protocol: MCP](https://img.shields.io/badge/MCP-2024--11--05-green.svg)](https://modelcontextprotocol.io/)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Arch User Repository](https://img.shields.io/badge/AUR-sdb--bin-1793d1.svg)](https://aur.archlinux.org/packages/sdb-bin)

A unified **Model Context Protocol (MCP)** server for Samsung Smart TVs running Tizen OS. It bridges AI coding assistants (Copilot, Cline, Claude Desktop, Cursor, OpenCode, Muse) directly to your TV over the Smart Development Bridge (`sdb`).

It combines the **official app development workflow** (scaffolding web apps, packaging `.wgt` widgets, injecting remote keys, DevTools inspector) with **deep hardware telemetry and system administration** (process monitoring, app lifecycle, privacy debloating, port forwarding, and system logs).

> **No 2 GB Tizen Studio IDE required.** Powered purely by the standalone `sdb` binary (~2.6 MB).

---

## Table of Contents

- [Features](#features)
  - [App Development](#1-app-development-tools)
  - [Administration & Debloating](#2-operations--administration-tools)
  - [Resources](#3-mcp-resources)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Via pipx (Recommended)](#option-a-via-pipx-recommended)
  - [Via uv](#option-b-via-uv-tool)
  - [From Source](#option-c-from-source)
- [Configuring MCP Clients](#configuring-mcp-clients)
  - [VS Code (Cline / Roo Code)](#1-vs-code-cline--roo-code)
  - [JetBrains / PyCharm / IntelliJ (Copilot)](#2-jetbrains--pycharm--intellij-github-copilot)
  - [Cursor](#3-cursor)
  - [Claude Desktop](#4-claude-desktop)
  - [Antigravity CLI (agy)](#5-antigravity-cli-agy)
  - [OpenCode](#6-opencode)
- [TV Setup (Developer Mode)](#tv-setup-developer-mode)
- [Tool Reference](#tool-reference)
- [Example AI Prompts](#example-ai-prompts)
- [Safety Guardrails](#safety-guardrails)
- [License](#license)

---

## Features

### 1. App Development Tools
* **`validate_environment`**: Verifies local `sdb` binary and attached TV status.
* **`scaffold_tv_webapp`**: Generates a complete Tizen Web App project structure (`config.xml`, `index.html`, 1080p TV CSS with focus states, remote D-pad navigation, and app icons).
* **`build_and_package_wgt`**: Validates manifest and bundles web assets into a standard `.wgt` archive.
* **`install_app`**: Pushes and installs `.wgt` or `.tpk` packages to the TV over SDB.
* **`remote_key_press`**: Injects TV remote control keycodes (`UP`, `DOWN`, `LEFT`, `RIGHT`, `ENTER`, `RETURN`, `PLAY`, `PAUSE`, `VOL_UP`, `VOL_DOWN`, `MUTE`).
* **`start_web_inspector`**: Forwards Chromium DevTools port (`9222`) for debugging web apps directly on the TV screen.

### 2. Operations & Administration Tools
* **`connect_tv` / `disconnect_tv`**: Connect to TV over LAN (`<TV_IP>:26101`).
* **`list_devices`**: Enumerates connected devices, serials, and connection status.
* **`list_apps`**: Lists installed packages and application IDs (distinguishing system vs. user apps).
* **`launch_app` / `stop_app`**: Starts or terminates running TV apps (YouTube, Netflix, Vetro, custom apps).
* **`uninstall_app`**: Safely removes user packages (guarded by `confirm=True`).
* **`get_system_info`**: Deep TV telemetry (CPU hardware/cores, RAM total/used/free, swap/zRAM, storage partitions, model name, kernel).
* **`get_process_list`**: Lists running processes on the TV with CPU, PID, and memory details.
* **`debloat_component`**: Safely audits, stops, or disables telemetry/ACR services (`com.samsung.tv.acr`, `canalysis-service`, etc.) with strict protection for core platform services (blocks `com.samsung.tv.coba.adagent` and `org.tizen.*` to prevent bricking).
* **`query_dlog`**: Streams device log buffer with tag/priority filtering (similar to Android's `logcat`).
* **`forward_port` / `reverse_port`**: Arbitrary TCP port forwarding between host and TV.
* **`run_shell_command`**: Runs remote shell commands on the TV with safety validation.

### 3. MCP Resources
* `tizen://devices` — Real-time list of connected devices.
* `tizen://sysinfo` — Structured TV hardware and OS telemetry.
* `tizen://telemetry-catalog` — Catalog of known telemetry services and protected platform components.

---

## Prerequisites

1. **Samsung Smart TV** running Tizen OS, connected to your local network.
2. **`sdb` (Smart Development Bridge)** installed on your host machine:
   * **Arch Linux / AliveOS**:
     ```bash
     yay -S sdb-bin
     # or via aliveos-repo: pacman -S sdb-bin
     ```
   * **Other Linux / macOS / Windows**: Download standalone SDB from [Samsung Developer](https://developer.samsung.com/smarttv/develop/getting-started/using-sdk/tv-device.html).

---

## Installation

### Option A: Via `pipx` (Recommended)

Keeps the tool isolated in its own virtual environment while exposing `tizen-tv-mcp` globally in your PATH:

```bash
# Direct from GitHub:
pipx install git+https://github.com/Twilight0/tizen-tv-mcp.git

# Or in editable mode for local development:
git clone https://github.com/Twilight0/tizen-tv-mcp.git ~/Projects/tizen-tv-mcp
pipx install --editable ~/Projects/tizen-tv-mcp
```

### Option B: Via `uv tool`

```bash
uv tool install git+https://github.com/Twilight0/tizen-tv-mcp.git
```

### Option C: From Source

```bash
git clone https://github.com/Twilight0/tizen-tv-mcp.git
cd tizen-tv-mcp
uv sync
uv run tizen-tv-mcp
```

Verify that the CLI command works:
```bash
which tizen-tv-mcp
# /home/user/.local/bin/tizen-tv-mcp
```

---

## Configuring MCP Clients

Add `tizen-tv-mcp` to your preferred AI environment:

### 1. VS Code (Cline / Roo Code)
In your Cline MCP settings (`cline_mcp_settings.json`):
```json
{
  "mcpServers": {
    "tizen-tv": {
      "command": "tizen-tv-mcp"
    }
  }
}
```

### 2. JetBrains / PyCharm / IntelliJ (GitHub Copilot)
In `~/.config/github-copilot/intellij/mcp.json`:
```json
{
  "servers": {
    "tizen-tv": {
      "type": "stdio",
      "command": "tizen-tv-mcp"
    }
  }
}
```

### 3. Cursor
In **Settings** → **Features** → **MCP** → **+ Add New MCP Server**:
* **Name**: `tizen-tv`
* **Type**: `command`
* **Command**: `tizen-tv-mcp`

### 4. Claude Desktop
In `~/.config/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "tizen-tv": {
      "command": "tizen-tv-mcp"
    }
  }
}
```

### 5. Antigravity CLI (`agy`)
Add the server using the CLI management command:
```bash
agy mcp add tizen-tv tizen-tv-mcp
```
To verify that the server is enabled and active:
```bash
agy mcp list
# Output includes:
# tizen-tv    stdio    enabled    tizen-tv-mcp
```

### 6. OpenCode
Add `tizen-tv` to your `~/.config/opencode/opencode.json` configuration file under `"mcp"`:
```json
{
  "mcp": {
    "tizen-tv": {
      "type": "local",
      "command": [
        "tizen-tv-mcp"
      ],
      "enabled": true
    }
  }
}
```
*Bonus*: The standalone skill specification is also provided in `~/.config/opencode/skills/tizen-tv/SKILL.md` for agents that read file-based skills.

---

## TV Setup (Developer Mode)

To allow SDB connections on your Samsung TV:

1. Turn on the TV and open the **Apps** panel.
2. Press **`1` `2` `3` `4` `5`** on your remote control in sequence.
3. In the dialog that pops up:
   * Toggle **Developer Mode** to **ON**.
   * Enter your computer's LAN IP (e.g. `192.168.1.150`) in **Host PC IP**.
4. Restart the TV (hold the remote power button for 10 seconds or power-cycle).
5. Connect from your PC:
   ```bash
   sdb connect <TV_IP>:26101
   sdb devices
   ```
6. *First connect*: Accept the authorization popup on the TV screen using the remote.

---

## Tool Reference

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `validate_environment` | *none* | Checks local `sdb` binary and attached target TV. |
| `connect_tv` | `ip` *(str)*, `port` *(int, default 26101)* | Connects to TV over LAN. |
| `disconnect_tv` | `target` *(str, optional)* | Disconnects specified device or all devices. |
| `list_devices` | *none* | Lists connected targets, serials, and states. |
| `list_apps` | `include_system` *(bool)*, `target_serial` *(str)* | Returns all installed apps and package IDs. |
| `launch_app` | `app_id` *(str)*, `target_serial` *(str)* | Launches app by App ID. |
| `stop_app` | `app_id` *(str)*, `target_serial` *(str)* | Kills running app instance. |
| `uninstall_app` | `package_id` *(str)*, `confirm` *(bool)* | Uninstalls package (requires `confirm=True`). |
| `get_system_info` | `target_serial` *(str)* | Queries CPU, RAM, swap, storage, model, kernel. |
| `get_process_list` | `count` *(int)*, `target_serial` *(str)* | Lists active processes with PID and CPU. |
| `debloat_component` | `component_id` *(str)*, `action` *(str)* | Audits (`check`), stops (`kill_process`), disables (`disable`), or enables (`enable`) telemetry components. |
| `query_dlog` | `filter_tag` *(str)*, `priority` *(str)*, `lines` *(int)* | Retrieves TV system log output. |
| `scaffold_tv_webapp`| `app_name` *(str)*, `package_id` *(str)*, `target_dir` *(str)* | Scaffolds a complete 1080p TV Web App project. |
| `build_and_package_wgt` | `project_dir` *(str)*, `output_path` *(str)* | Validates and builds `.wgt` archive. |
| `install_app` | `wgt_path` *(str)*, `target_serial` *(str)* | Installs package to TV. |
| `remote_key_press` | `key` *(str)*, `target_serial` *(str)* | Injects remote key press (`UP`, `DOWN`, `ENTER`, `RETURN`, `PLAY`, etc.). |
| `start_web_inspector`| `remote_port` *(int)*, `local_port` *(int)* | Forwards Chromium DevTools port for live web view debugging. |
| `forward_port` | `local_port` *(int)*, `remote_port` *(int)* | Forwards host port to TV port. |
| `reverse_port` | `remote_port` *(int)*, `local_port` *(int)* | Forwards TV port to host port. |
| `run_shell_command` | `command` *(str)*, `timeout_seconds` *(int)* | Runs validated shell command on TV. |

---

## Example AI Prompts

Once configured in your AI assistant, you can ask natural language questions:

* *"Connect to my TV at 192.168.1.100 and show me CPU and RAM usage."*
* *"List all running processes and check if any ACR or analytics services are consuming resources."*
* *"Disable com.samsung.tv.acr and canalysis-service on my TV."*
* *"Create a new Tizen TV streaming app named RetroPlayer in ~/Projects/RetroPlayer."*
* *"Package ~/Projects/RetroPlayer into a .wgt and install it on the TV."*
* *"Press the OK button, then navigate DOWN 3 times on the TV remote."*
* *"Forward the Chromium DevTools port so I can inspect the app in my browser."*

---

## Safety Guardrails

To prevent accidental bricking or damage to your TV:

1. **Protected Services Shield**: Core system components (`com.samsung.tv.coba.adagent`, `org.tizen.setting`, `org.tizen.home`, `org.tizen.system-manager`) are strictly protected. The `debloat_component` and `uninstall_app` tools will refuse to disable or remove them.
2. **Destructive Shell Command Filter**: Commands matching destructive patterns (`rm -rf /`, formatting commands, raw disk writes) are automatically intercepted and blocked.
3. **Explicit Confirmation**: Package uninstallation requires `confirm=True`.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

*Disclaimer: Not affiliated with Samsung Electronics. Tizen is a registered trademark of The Linux Foundation.*
