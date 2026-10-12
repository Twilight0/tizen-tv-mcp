"""Tizen TV Unified MCP Server (Development + Operations + Privacy Debloating)."""

import json
from typing import Any, Dict, List, Optional

from mcp.server.mcpserver import MCPServer

from .dev import TizenDevManager
from .ops import KNOWN_TELEMETRY, PROTECTED_COMPONENTS, TizenOpsManager
from .sdb import SDBClient, SDBError

mcp = MCPServer(
    name="tizen-tv-mcp",
    title="Samsung Tizen TV Manager & Dev MCP Server",
    description=(
        "Comprehensive MCP server for Samsung Smart TVs running Tizen OS. "
        "Provides development tools (scaffolding, .wgt packaging, remote key simulation, DevTools inspector) "
        "and operational tools (connecting, deep telemetry, app lifecycle, privacy debloating, port forwarding)."
    ),
    version="1.0.0",
)

# Shared clients
sdb = SDBClient()
dev_mgr = TizenDevManager(sdb)
ops_mgr = TizenOpsManager(sdb)


# ============================================================================
# Development Tools (Official Approach)
# ============================================================================

@mcp.tool()
def validate_environment() -> Dict[str, Any]:
    """Validate the local environment, sdb installation, and connected TV devices."""
    return dev_mgr.validate_environment()


@mcp.tool()
def scaffold_tv_webapp(
    app_name: str,
    package_id: Optional[str] = None,
    target_dir: Optional[str] = None,
    template: str = "basic",
) -> Dict[str, Any]:
    """Scaffold a lightweight Tizen TV Web Application with config.xml and remote key listeners.

    Args:
        app_name: Display name of the application.
        package_id: 10-character alphanumeric ID (auto-generated if omitted).
        target_dir: Target directory on host (defaults to ~/Projects/<AppName>).
        template: Project template ('basic', 'streaming', etc.).
    """
    return dev_mgr.scaffold_tv_webapp(
        app_name=app_name,
        package_id=package_id,
        target_dir=target_dir,
        template=template,
    )


@mcp.tool()
def build_and_package_wgt(
    project_dir: str,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Package a Tizen Web App directory into a deployable .wgt package.

    Args:
        project_dir: Path to directory containing config.xml and web assets.
        output_path: Path for generated .wgt file (defaults to /tmp/<dirname>.wgt).
    """
    return dev_mgr.build_and_package_wgt(project_dir=project_dir, output_path=output_path)


@mcp.tool()
def install_app(
    wgt_path: str,
    target_serial: Optional[str] = None,
) -> Dict[str, Any]:
    """Install a .wgt or .tpk package on the connected TV.

    Args:
        wgt_path: Local path to the .wgt or .tpk package file.
        target_serial: Target device serial (optional if only one device is connected).
    """
    return dev_mgr.install_app(wgt_path=wgt_path, target_serial=target_serial)


@mcp.tool()
def remote_key_press(
    key: str,
    target_serial: Optional[str] = None,
) -> Dict[str, Any]:
    """Simulate a physical TV remote control key press (e.g. UP, DOWN, LEFT, RIGHT, ENTER, RETURN, EXIT).

    Args:
        key: Key name (e.g. 'UP', 'DOWN', 'LEFT', 'RIGHT', 'ENTER', 'RETURN', 'BACK', 'PLAY', 'PAUSE', 'VOL_UP', 'VOL_DOWN', 'MUTE') or numeric keyCode.
        target_serial: Target device serial (optional).
    """
    return dev_mgr.remote_key_press(key=key, target_serial=target_serial)


@mcp.tool()
def start_web_inspector(
    remote_port: int = 9222,
    local_port: int = 9222,
    target_serial: Optional[str] = None,
) -> Dict[str, Any]:
    """Forward Chromium DevTools remote debugging port for inspecting TV web views.

    Args:
        remote_port: Inspector port on the TV (typically 9222).
        local_port: Port to open on local host (defaults to 9222).
        target_serial: Target device serial (optional).
    """
    return dev_mgr.start_web_inspector(
        remote_port=remote_port,
        local_port=local_port,
        target_serial=target_serial,
    )


# ============================================================================
# Operations & Telemetry Tools (Custom Approach)
# ============================================================================

@mcp.tool()
def connect_tv(
    ip: str,
    port: int = 26101,
) -> Dict[str, Any]:
    """Connect to a Samsung Smart TV over LAN via SDB (default port 26101).

    Args:
        ip: LAN IP address of the TV (e.g. '192.168.1.100').
        port: SDB port (default 26101).
    """
    return sdb.connect(ip=ip, port=port)


@mcp.tool()
def disconnect_tv(
    target: Optional[str] = None,
) -> str:
    """Disconnect target TV or all connected SDB targets.

    Args:
        target: IP:port of the device to disconnect (disconnects all if omitted).
    """
    return sdb.disconnect(target=target)


@mcp.tool()
def list_devices() -> List[Dict[str, str]]:
    """List all connected Tizen targets, serial numbers, and status."""
    return sdb.get_devices()


@mcp.tool()
def list_apps(
    include_system: bool = True,
    target_serial: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List installed applications and package IDs on the TV.

    Args:
        include_system: Include built-in Samsung/Tizen system applications.
        target_serial: Target device serial (optional).
    """
    return ops_mgr.list_apps(include_system=include_system, target_serial=target_serial)


@mcp.tool()
def launch_app(
    app_id: str,
    target_serial: Optional[str] = None,
) -> Dict[str, Any]:
    """Launch an application on the TV by its Application ID.

    Args:
        app_id: Full Application ID (e.g. '9Ur5IzDKqV.TizenYouTube', '3G9P87z91L.Vetro').
        target_serial: Target device serial (optional).
    """
    return ops_mgr.launch_app(app_id=app_id, target_serial=target_serial)


@mcp.tool()
def stop_app(
    app_id: str,
    target_serial: Optional[str] = None,
) -> Dict[str, Any]:
    """Terminate / kill a running application on the TV.

    Args:
        app_id: Application ID to terminate.
        target_serial: Target device serial (optional).
    """
    return ops_mgr.stop_app(app_id=app_id, target_serial=target_serial)


@mcp.tool()
def uninstall_app(
    package_id: str,
    confirm: bool = False,
    target_serial: Optional[str] = None,
) -> Dict[str, Any]:
    """Uninstall a package by its 10-character package ID (requires confirm=True).

    Args:
        package_id: 10-character unique package ID.
        confirm: Must be set to True to prevent accidental uninstalls.
        target_serial: Target device serial (optional).
    """
    return ops_mgr.uninstall_app(
        package_id=package_id,
        confirm=confirm,
        target_serial=target_serial,
    )


@mcp.tool()
def get_system_info(
    target_serial: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch hardware, CPU, memory, storage, and firmware telemetry from the TV."""
    return ops_mgr.get_system_info(target_serial=target_serial)


@mcp.tool()
def get_process_list(
    count: int = 25,
    target_serial: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Get active processes running on the TV with PID, memory, and command line."""
    return ops_mgr.get_process_list(count=count, target_serial=target_serial)


@mcp.tool()
def debloat_component(
    component_id: str,
    action: str = "check",
    target_serial: Optional[str] = None,
) -> Dict[str, Any]:
    """Safely audit or toggle telemetry/ACR services with guardrails against bricking core services.

    Args:
        component_id: Component ID (e.g. 'com.samsung.tv.acr', 'com.samsung.tv.canalysis-service').
        action: 'check' to inspect, 'disable' to disable via package manager, 'enable' to re-enable, or 'kill_process' to stop PID.
        target_serial: Target device serial (optional).
    """
    return ops_mgr.debloat_component(
        component_id=component_id,
        action=action,
        target_serial=target_serial,
    )


@mcp.tool()
def query_dlog(
    filter_tag: Optional[str] = None,
    priority: str = "I",
    lines: int = 50,
    target_serial: Optional[str] = None,
) -> str:
    """Fetch recent TV system dlog buffer (similar to Android logcat).

    Args:
        filter_tag: Optional tag to filter on (e.g. 'Console').
        priority: Minimum priority ('V', 'D', 'I', 'W', 'E', 'F').
        lines: Number of recent log lines to retrieve (default 50).
        target_serial: Target device serial (optional).
    """
    return ops_mgr.query_dlog(
        filter_tag=filter_tag,
        priority=priority,
        lines=lines,
        target_serial=target_serial,
    )


@mcp.tool()
def forward_port(
    local_port: int,
    remote_port: int,
    target_serial: Optional[str] = None,
) -> str:
    """Set up port forwarding: forward host local port to TV target port."""
    return ops_mgr.forward_port(
        local_port=local_port,
        remote_port=remote_port,
        target_serial=target_serial,
    )


@mcp.tool()
def reverse_port(
    remote_port: int,
    local_port: int,
    target_serial: Optional[str] = None,
) -> str:
    """Set up reverse port forwarding: forward TV remote port to host local port."""
    return ops_mgr.reverse_port(
        remote_port=remote_port,
        local_port=local_port,
        target_serial=target_serial,
    )


@mcp.tool()
def run_shell_command(
    command: str,
    timeout_seconds: int = 20,
    target_serial: Optional[str] = None,
) -> str:
    """Run an administrative or inspection shell command on the TV with safety validation.

    Args:
        command: Shell command string to execute.
        timeout_seconds: Timeout limit in seconds.
        target_serial: Target device serial (optional).
    """
    return sdb.shell(command=command, target_serial=target_serial, timeout=timeout_seconds)


# ============================================================================
# Resources
# ============================================================================

@mcp.resource("tizen://devices")
def resource_devices() -> str:
    """Real-time list of attached Tizen devices."""
    return json.dumps(sdb.get_devices(), indent=2)


@mcp.resource("tizen://sysinfo")
def resource_sysinfo() -> str:
    """System telemetry of the connected TV."""
    return json.dumps(ops_mgr.get_system_info(), indent=2)


@mcp.resource("tizen://telemetry-catalog")
def resource_telemetry_catalog() -> str:
    """Catalog of known telemetry services and protected platform components."""
    catalog = {
        "known_telemetry": KNOWN_TELEMETRY,
        "protected_components": PROTECTED_COMPONENTS,
    }
    return json.dumps(catalog, indent=2)


# ============================================================================
# Entrypoint
# ============================================================================

def main():
    """Run MCP server over standard I/O."""
    mcp.run()


if __name__ == "__main__":
    main()
