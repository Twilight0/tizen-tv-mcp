"""SDB (Smart Development Bridge) execution wrapper and safety validators."""

import os
import re
import shutil
import socket
import subprocess
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple


class SDBError(Exception):
    """Raised when an SDB command fails."""
    pass


class SDBClient:
    """Wrapper for executing SDB commands against Samsung Tizen devices."""

    def __init__(self, binary_path: Optional[str] = None):
        self.binary_path = binary_path or shutil.which("sdb") or "/usr/bin/sdb"
        if not os.path.exists(self.binary_path) and not shutil.which("sdb"):
            raise SDBError(
                "sdb binary not found in PATH or /usr/bin/sdb. "
                "Ensure sdb-bin is installed from AUR/aliveos-repo."
            )

    def run(
        self,
        args: List[str],
        target_serial: Optional[str] = None,
        timeout: int = 20,
    ) -> str:
        """Run an SDB command and return stdout."""
        cmd = [self.binary_path]
        if target_serial:
            cmd.extend(["-s", target_serial])
        cmd.extend(args)

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            if res.returncode != 0 and not res.stdout:
                raise SDBError(f"sdb command failed ({res.returncode}): {res.stderr.strip()}")
            return res.stdout.strip()
        except subprocess.TimeoutExpired:
            raise SDBError(f"sdb command timed out after {timeout}s: {' '.join(cmd)}")
        except Exception as e:
            raise SDBError(f"Error executing sdb: {e}")

    def shell(
        self,
        command: str,
        target_serial: Optional[str] = None,
        timeout: int = 25,
    ) -> str:
        """Execute a remote shell command on the target Tizen device."""
        self._validate_shell_safety(command)
        return self.run(["shell", command], target_serial=target_serial, timeout=timeout)

    def exec_stream(
        self,
        command: str,
        target_serial: Optional[str] = None,
        port: int = 26099,
        timeout: int = 60,
    ) -> str:
        """Execute a raw service command over SDB transport stream (e.g. shell:0 vd_appinstall)."""
        serial = target_serial
        if not serial:
            devs = self.get_devices()
            if not devs:
                raise SDBError("No devices connected to SDB.")
            serial = devs[0]["serial"]

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect(("127.0.0.1", port))
            trans_req = f"host:transport:{serial}"
            s.sendall(f"{len(trans_req):04x}{trans_req}".encode())
            resp = s.recv(4)
            if resp != b"OKAY":
                raise SDBError(f"SDB transport failed: {resp.decode('utf-8', errors='replace')}")

            s.sendall(f"{len(command):04x}{command}".encode())
            resp2 = s.recv(4)
            if resp2 != b"OKAY":
                raise SDBError(f"SDB command rejected: {resp2.decode('utf-8', errors='replace')}")

            out = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                out += chunk
            return out.decode("utf-8", errors="replace")
        except socket.timeout:
            raise SDBError(f"SDB stream timed out after {timeout}s: {command}")
        except Exception as e:
            raise SDBError(f"SDB stream error: {e}")
        finally:
            s.close()

    def _validate_shell_safety(self, command: str) -> None:
        """Guard against catastrophic or bricking commands."""
        destructive_patterns = [
            r"rm\s+-[rf]*\s+/(?:\s|$)",
            r"mkfs",
            r"dd\s+if=.*of=/dev/(sd|mmc|nvme)",
            r">\s*/dev/(sd|mmc|nvme)",
            r":\(\)\s*\{.*\}",  # fork bomb
            r"chmod\s+-[R]*\s+000\s+/",
        ]
        for pattern in destructive_patterns:
            if re.search(pattern, command):
                raise SDBError(f"Command blocked by safety guardrails: matches destructive pattern '{pattern}'")

    def get_version(self) -> str:
        """Get local sdb version."""
        return self.run(["version"])

    def get_devices(self) -> List[Dict[str, str]]:
        """List attached devices."""
        raw = self.run(["devices"])
        devices = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices") or line.startswith("*"):
                continue
            parts = re.split(r"\s+", line)
            if len(parts) >= 2 and parts[1] in ("device", "offline", "unauthorized", "unknown"):
                serial = parts[0]
                status = parts[1]
                name = parts[2] if len(parts) > 2 else "Unknown"
                devices.append({
                    "serial": serial,
                    "status": status,
                    "name": name,
                })
        return devices

    def connect(self, ip: str, port: int = 26101) -> Dict[str, Any]:
        """Connect to a target Tizen device over TCP/IP."""
        target = f"{ip}:{port}"
        out = self.run(["connect", target])
        devices = self.get_devices()
        connected = any(d["serial"] == target and d["status"] == "device" for d in devices)
        return {
            "target": target,
            "output": out,
            "connected": connected,
            "status": "connected" if connected else "pending_or_failed",
            "notes": (
                "If connection status is offline, accept the authorization prompt on the TV screen "
                "or verify that the Host PC IP in Developer Mode matches your computer's local IP."
                if not connected else "Successfully connected and authorized."
            ),
        }

    def disconnect(self, target: Optional[str] = None) -> str:
        """Disconnect target device or all devices."""
        if target:
            return self.run(["disconnect", target])
        return self.run(["disconnect"])
