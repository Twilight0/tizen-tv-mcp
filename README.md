# Tizen TV Unified MCP Server (`tizen-tv-mcp`)

A unified Model Context Protocol (MCP) server for Samsung Smart TVs running Tizen OS. Combines the **application development lifecycle** (scaffolding, building `.wgt` packages, remote key simulation, DevTools web inspector) with **deep system administration and operations** (device telemetry, app management, privacy debloating, port forwarding, and system logs).

No heavy Tizen Studio IDE (~2 GB) required—powered by the standalone `sdb` (Smart Development Bridge) tool.

---

## Features

### 1. App Development Tools (Official Approach)
* **`validate_environment`**: Verifies local `sdb` binary and attached TV status.
* **`scaffold_tv_webapp`**: Generates a complete Tizen Web App project structure (`config.xml`, `index.html`, 1080p TV CSS with focus states, remote D-pad navigation, and app icons).
* **`build_and_package_wgt`**: Validates manifest and bundles web assets into a standard `.wgt` archive.
* **`install_app`**: Pushes and installs `.wgt` or `.tpk` packages to the TV over SDB.
* **`remote_key_press`**: Injects TV remote control keycodes (`UP`, `DOWN`, `LEFT`, `RIGHT`, `ENTER`, `RETURN`, `PLAY`, `PAUSE`, `VOL_UP`, `VOL_DOWN`, `MUTE`).
* **`start_web_inspector`**: Forwards Chromium DevTools port (`9222`) for debugging web apps on the TV.

### 2. Operations & Administration Tools (Custom Approach)
* **`connect_tv` / `disconnect_tv`**: Connect to TV over LAN (`<TV_IP>:26101`).
* **`list_devices`**: Enumerates connected devices, serials, and connection status.
* **`list_apps`**: Lists installed packages and application IDs.
* **`launch_app` / `stop_app`**: Starts or kills running TV apps (YouTube, Netflix, Vetro, custom apps).
* **`uninstall_app`**: Safely removes user packages (protected by `confirm=True`).
* **`get_system_info`**: Deep TV telemetry (CPU hardware/cores, RAM total/used/free, swap/zRAM, storage partitions, model name, kernel).
* **`get_process_list`**: Lists running processes on the TV.
* **`debloat_component`**: Safely audits, stops, or disables telemetry/ACR services (`com.samsung.tv.acr`, `canalysis-service`, etc.) with strict protection for core platform services (blocks `com.samsung.tv.coba.adagent` and `org.tizen.*` to prevent bricking).
* **`query_dlog`**: Streams device log buffer with tag/priority filtering.
* **`forward_port` / `reverse_port`**: Arbitrary TCP port forwarding between host and TV.
* **`run_shell_command`**: Runs remote shell commands on the TV with safety validation.

### 3. Resources & Prompts
* **`tizen://devices`**: Real-time list of connected devices.
* **`tizen://sysinfo`**: Hardware and OS metrics.
* **`tizen://telemetry-catalog`**: Reference catalog of known telemetry services and protected platform components.

---

## Quick Setup

### 1. Enable Developer Mode on the Samsung TV
1. On the TV, open **Apps**, then press **`1` `2` `3` `4` `5`** sequentially on the remote.
2. In the Developer Mode popup:
   - Toggle **Developer Mode** to **ON**.
   - Set **Host PC IP** to your computer's LAN IP (e.g. `192.168.1.150`).
3. Turn off the TV and turn it back on (or hold the power button for 10 seconds to reboot).

### 2. Connect to the TV
```bash
sdb connect 192.168.1.100:26101
sdb devices
```
*Note*: When connecting for the first time, accept the authorization prompt on the TV screen.

---

## MCP Client Configuration

### GitHub Copilot / IntelliJ (`mcp.json`)
```json
{
  "servers": {
    "tizen-tv": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/home/twilight/Projects/tizen-tv-mcp",
        "run",
        "tizen-tv-mcp"
      ]
    }
  }
}
```

### VS Code (Cline / Roo Code / Cursor)
```json
{
  "mcpServers": {
    "tizen-tv": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/twilight/Projects/tizen-tv-mcp",
        "run",
        "tizen-tv-mcp"
      ]
    }
  }
}
```

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "tizen-tv": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/twilight/Projects/tizen-tv-mcp",
        "run",
        "tizen-tv-mcp"
      ]
    }
  }
}
```

---

## Running Standalone

You can test the server directly from the terminal:

```bash
cd ~/Projects/tizen-tv-mcp
uv run tizen-tv-mcp
```

Or run individual commands through Python:

```bash
uv run python -c "from tizen_tv_mcp.server import mcp; print(mcp.name)"
```

---

## License

MIT License. Not affiliated with Samsung Electronics.
