"""Tizen TV operations: system telemetry, app management, safe privacy debloating, logging."""

import re
from typing import Any, Dict, List, Optional

from .sdb import SDBClient, SDBError


# Protected components that must NEVER be disabled or removed
PROTECTED_COMPONENTS = {
    "com.samsung.tv.coba.adagent": (
        "CRITICAL: coba.adagent is a protected platform dependency. "
        "Disabling or removing it can cause launcher crashes or system bootloops."
    ),
    "org.tizen.setting": "Essential system settings UI.",
    "org.tizen.home": "Smart Hub / TV launcher interface.",
    "org.tizen.system-manager": "Core system process manager.",
}

# Known telemetry, ACR, and analytics components that can be safely audited/disabled
KNOWN_TELEMETRY = {
    "com.samsung.tv.acr": "Automated Content Recognition (audio/video fingerprinting)",
    "com.samsung.tv.canalysis-service": "Viewing behavioral and analytics engine",
    "com.samsung.tv.vision-data-recognition-service": "Visual metadata and ad-tracking analysis",
    "com.samsung.tv.contents-recognition-dbmgr": "Content recognition cache database",
    "com.samsung.tv.nvision-analysis-dbmgr": "Neural vision analysis cache database",
}


class TizenOpsManager:
    """Manages operational, telemetry, debloating, and lifecycle tasks on Samsung TV."""

    def __init__(self, sdb: SDBClient):
        self.sdb = sdb

    def list_apps(
        self,
        include_system: bool = True,
        target_serial: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List installed applications on the TV."""
        raw = self.sdb.shell("app_launcher -l", target_serial=target_serial)
        apps: List[Dict[str, Any]] = []

        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # Typical app_launcher -l output formats:
            # - '9Ur5IzDKqV.TizenYouTube'
            # - 'org.tizen.browser'
            # or with status/details
            parts = re.split(r"\s+", line)
            app_id = parts[0]
            pkg_id = app_id.split(".")[0] if "." in app_id else app_id
            is_system = app_id.startswith("org.tizen") or app_id.startswith("com.samsung.tv")

            if not include_system and is_system:
                continue

            apps.append({
                "app_id": app_id,
                "package_id": pkg_id,
                "is_system": is_system,
                "raw_info": line,
            })
        return apps

    def launch_app(
        self,
        app_id: str,
        target_serial: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Launch an application by its application ID."""
        out = self.sdb.shell(f"app_launcher -s {app_id}", target_serial=target_serial)
        return {
            "app_id": app_id,
            "output": out or "Launched successfully",
        }

    def stop_app(
        self,
        app_id: str,
        target_serial: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Terminate / stop a running application."""
        out = self.sdb.shell(f"app_launcher -k {app_id}", target_serial=target_serial)
        return {
            "app_id": app_id,
            "output": out or "Stopped successfully",
        }

    def uninstall_app(
        self,
        package_id: str,
        confirm: bool = False,
        target_serial: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Uninstall a package by its 10-character package ID (requires confirm=True)."""
        if not confirm:
            raise SDBError(
                f"Safety confirmation required to uninstall '{package_id}'. "
                "Pass confirm=True to proceed."
            )
        if package_id in PROTECTED_COMPONENTS:
            raise SDBError(f"Cannot uninstall protected component: {PROTECTED_COMPONENTS[package_id]}")

        out = self.sdb.run(["uninstall", package_id], target_serial=target_serial)
        return {
            "package_id": package_id,
            "output": out,
            "success": "success" in out.lower(),
        }

    def get_system_info(
        self,
        target_serial: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch TV hardware, memory, storage, and platform telemetry."""
        info: Dict[str, Any] = {}

        # 1. TV Model & OS
        try:
            model = self.sdb.shell("vconftool -g db/system/model_name", target_serial=target_serial)
            info["model_name"] = model.strip() if "error" not in model.lower() else "Unknown"
        except Exception:
            info["model_name"] = "Unknown"

        try:
            uname = self.sdb.shell("uname -a", target_serial=target_serial)
            info["kernel"] = uname.strip()
        except Exception:
            pass

        # 2. CPU info
        try:
            cpuinfo = self.sdb.shell("cat /proc/cpuinfo", target_serial=target_serial)
            cores = len(re.findall(r"^processor\s*:", cpuinfo, re.M))
            hardware = re.search(r"Hardware\s*:\s*(.*)", cpuinfo)
            info["cpu"] = {
                "cores": cores,
                "hardware": hardware.group(1).strip() if hardware else "ARM/Tizen",
            }
        except Exception:
            pass

        # 3. Memory & Swap
        try:
            meminfo = self.sdb.shell("cat /proc/meminfo", target_serial=target_serial)
            mem_total = re.search(r"MemTotal:\s*(\d+)\s*kB", meminfo)
            mem_free = re.search(r"MemFree:\s*(\d+)\s*kB", meminfo)
            mem_avail = re.search(r"MemAvailable:\s*(\d+)\s*kB", meminfo)
            swap_total = re.search(r"SwapTotal:\s*(\d+)\s*kB", meminfo)
            swap_free = re.search(r"SwapFree:\s*(\d+)\s*kB", meminfo)

            total_kb = int(mem_total.group(1)) if mem_total else 0
            free_kb = int(mem_free.group(1)) if mem_free else 0
            avail_kb = int(mem_avail.group(1)) if mem_avail else free_kb

            info["memory"] = {
                "total_mb": round(total_kb / 1024, 1),
                "available_mb": round(avail_kb / 1024, 1),
                "used_mb": round((total_kb - avail_kb) / 1024, 1),
                "swap_total_mb": round(int(swap_total.group(1)) / 1024, 1) if swap_total else 0,
                "swap_free_mb": round(int(swap_free.group(1)) / 1024, 1) if swap_free else 0,
            }
        except Exception:
            pass

        # 4. Storage partitions
        try:
            df = self.sdb.shell("df -h", target_serial=target_serial)
            info["storage_df"] = df.strip()
        except Exception:
            pass

        return info

    def get_process_list(
        self,
        count: int = 25,
        target_serial: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Fetch active processes on the TV."""
        raw = self.sdb.shell(f"ps -ef | head -n {count + 1}", target_serial=target_serial)
        lines = raw.splitlines()
        if not lines:
            return []

        procs: List[Dict[str, str]] = []
        for line in lines[1:]:
            parts = re.split(r"\s+", line.strip(), maxsplit=7)
            if len(parts) >= 8:
                procs.append({
                    "user": parts[0],
                    "pid": parts[1],
                    "ppid": parts[2],
                    "stime": parts[4],
                    "tty": parts[5],
                    "time": parts[6],
                    "cmd": parts[7],
                })
        return procs

    def debloat_component(
        self,
        component_id: str,
        action: str = "check",
        target_serial: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Safely audit or toggle state of TV telemetry/analytics components."""
        # 1. Enforce safety checks
        for protected_id, reason in PROTECTED_COMPONENTS.items():
            if protected_id in component_id:
                raise SDBError(f"BLOCKED: Component '{component_id}' is protected. {reason}")

        is_known = component_id in KNOWN_TELEMETRY
        desc = KNOWN_TELEMETRY.get(component_id, "Custom / User-specified component")

        # 2. Check running processes
        pid_check = self.sdb.shell(f"pidof {component_id} 2>/dev/null || true", target_serial=target_serial)
        running_pid = pid_check.strip() if pid_check else None

        result: Dict[str, Any] = {
            "component_id": component_id,
            "description": desc,
            "is_known_telemetry": is_known,
            "is_running": bool(running_pid),
            "pid": running_pid,
            "action_taken": action,
        }

        if action == "kill_process":
            if running_pid:
                self.sdb.shell(f"kill -9 {running_pid}", target_serial=target_serial)
                result["status"] = f"Sent SIGKILL to PID {running_pid}"
            else:
                result["status"] = "Component is not currently running"

        elif action == "disable":
            # Attempt disabling via pkg_cmd
            out = self.sdb.shell(f"pkg_cmd -d {component_id} 2>&1 || true", target_serial=target_serial)
            result["disable_output"] = out
            result["status"] = "Disabled flag requested via package manager"

        elif action == "enable":
            out = self.sdb.shell(f"pkg_cmd -e {component_id} 2>&1 || true", target_serial=target_serial)
            result["enable_output"] = out
            result["status"] = "Enable flag requested via package manager"

        elif action == "check":
            result["status"] = "Audit complete"

        return result

    def query_dlog(
        self,
        filter_tag: Optional[str] = None,
        priority: str = "I",
        lines: int = 50,
        target_serial: Optional[str] = None,
    ) -> str:
        """Fetch recent system dlog buffer from the TV."""
        filter_arg = f"{filter_tag}:{priority} *:S" if filter_tag else f"*:{priority}"
        # Use dlog command with line count
        cmd = f"dlog -v time -n 1 {filter_arg} 2>&1 | tail -n {lines}"
        return self.sdb.shell(cmd, target_serial=target_serial)

    def forward_port(
        self,
        local_port: int,
        remote_port: int,
        target_serial: Optional[str] = None,
    ) -> str:
        """Forward local host port to target TV port."""
        return self.sdb.run(
            ["forward", f"tcp:{local_port}", f"tcp:{remote_port}"],
            target_serial=target_serial,
        )

    def reverse_port(
        self,
        remote_port: int,
        local_port: int,
        target_serial: Optional[str] = None,
    ) -> str:
        """Reverse forward TV remote port to local host port."""
        return self.sdb.run(
            ["reverse", f"tcp:{remote_port}", f"tcp:{local_port}"],
            target_serial=target_serial,
        )
