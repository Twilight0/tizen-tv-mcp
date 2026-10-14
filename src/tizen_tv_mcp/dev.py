"""Tizen TV development tools: scaffolding, packaging (.wgt), remote key simulation, DevTools inspector."""

import json
import os
import random
import re
import shutil
import string
import subprocess
import urllib.request
import zipfile
from typing import Any, Dict, List, Optional
from .sdb import SDBClient, SDBError


# Standard Samsung Tizen TV remote key mapping
REMOTE_KEY_CODES = {
    "LEFT": 37,
    "UP": 38,
    "RIGHT": 39,
    "DOWN": 40,
    "ENTER": 13,
    "OK": 13,
    "RETURN": 10009,
    "BACK": 10009,
    "EXIT": 10182,
    "PLAY": 415,
    "PAUSE": 19,
    "STOP": 413,
    "FAST_FORWARD": 417,
    "REWIND": 412,
    "VOL_UP": 447,
    "VOL_DOWN": 448,
    "MUTE": 449,
    "COLOR_RED": 403,
    "COLOR_GREEN": 404,
    "COLOR_YELLOW": 405,
    "COLOR_BLUE": 406,
    "CH_UP": 427,
    "CH_DOWN": 428,
}


def generate_package_id() -> str:
    """Generate a valid 10-character alphanumeric Tizen package ID."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(10))


class TizenDevManager:
    """Manages Tizen TV development workflows."""

    def __init__(self, sdb: SDBClient):
        self.sdb = sdb

    def validate_environment(self) -> Dict[str, Any]:
        """Validate the local environment and TV connection status."""
        report: Dict[str, Any] = {
            "sdb_installed": False,
            "sdb_path": self.sdb.binary_path,
            "sdb_version": None,
            "devices": [],
            "status": "ready",
            "messages": [],
        }

        try:
            version_str = self.sdb.get_version()
            report["sdb_installed"] = True
            report["sdb_version"] = version_str
        except Exception as e:
            report["status"] = "error"
            report["messages"].append(f"Failed to query sdb version: {e}")
            return report

        try:
            devices = self.sdb.get_devices()
            report["devices"] = devices
            if not devices:
                report["messages"].append(
                    "No Tizen devices attached. Connect via connect_tv(ip, port=26101)."
                )
            elif all(d["status"] != "device" for d in devices):
                report["messages"].append(
                    "Devices detected but not authorized. Accept the prompt on your TV screen."
                )
        except Exception as e:
            report["messages"].append(f"Could not list devices: {e}")

        return report

    def scaffold_tv_webapp(
        self,
        app_name: str,
        package_id: Optional[str] = None,
        target_dir: Optional[str] = None,
        template: str = "basic",
    ) -> Dict[str, Any]:
        """Scaffold a lightweight Tizen TV Web Application project."""
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "", app_name) or "MyTvApp"
        pkg_id = package_id or generate_package_id()
        if len(pkg_id) != 10:
            raise SDBError(f"Tizen package ID must be exactly 10 alphanumeric characters, got: '{pkg_id}'")

        dest_dir = target_dir or os.path.expanduser(f"~/Projects/{safe_name}")
        os.makedirs(dest_dir, exist_ok=True)
        os.makedirs(os.path.join(dest_dir, "css"), exist_ok=True)
        os.makedirs(os.path.join(dest_dir, "js"), exist_ok=True)

        app_id = f"{pkg_id}.{safe_name}"

        # 1. config.xml
        config_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<widget xmlns="http://www.w3.org/ns/widgets" 
        xmlns:tizen="http://tizen.org/ns/tizen" 
        id="http://tizen.org/{safe_name}" 
        version="1.0.0" 
        viewmodes="maximized">
    <tizen:application id="{app_id}" 
                       package="{pkg_id}" 
                       version="1.0.0" 
                       required_version="3.0"/>
    <content src="index.html"/>
    <feature name="http://tizen.org/feature/screen.size.all"/>
    <icon src="icon.png"/>
    <name>{app_name}</name>
    <tizen:profile name="tv"/>
    <tizen:setting screen-orientation="landscape" context-menu="enable" background-support="disable"/>
    <tizen:privilege name="http://tizen.org/privilege/application.launch"/>
    <tizen:privilege name="http://tizen.org/privilege/tv.inputdevice"/>
</widget>
"""
        with open(os.path.join(dest_dir, "config.xml"), "w") as f:
            f.write(config_xml)

        # 2. index.html
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1920, height=1080, initial-scale=1.0">
    <title>{app_name}</title>
    <link rel="stylesheet" href="css/style.css">
    <script src="js/main.js" defer></script>
</head>
<body>
    <div class="tv-container">
        <header>
            <h1>{app_name}</h1>
            <p class="subtitle">Samsung Tizen Smart TV Application</p>
        </header>
        <main id="app-view">
            <div class="card focusable" tabindex="0">
                <h2>Featured Content</h2>
                <p>Welcome to {app_name}. Use the remote D-pad to navigate.</p>
            </div>
            <div class="grid">
                <button class="nav-btn focusable" tabindex="1">Play Stream</button>
                <button class="nav-btn focusable" tabindex="2">Settings</button>
                <button class="nav-btn focusable" tabindex="3">About</button>
            </div>
            <div id="status-box">Status: Ready (Press Return/Back to exit)</div>
        </main>
    </div>
</body>
</html>
"""
        with open(os.path.join(dest_dir, "index.html"), "w") as f:
            f.write(index_html)

        # 3. css/style.css
        style_css = """* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    width: 1920px;
    height: 1080px;
    overflow: hidden;
    background-color: #0b0f19;
    color: #f1f5f9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    user-select: none;
}

.tv-container {
    padding: 80px 100px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

header h1 {
    font-size: 54px;
    font-weight: 700;
    color: #38bdf8;
    margin-bottom: 8px;
}

.subtitle {
    font-size: 24px;
    color: #94a3b8;
}

.card {
    background: #1e293b;
    border: 3px solid transparent;
    border-radius: 16px;
    padding: 40px;
    margin-top: 40px;
    transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.grid {
    display: flex;
    gap: 30px;
    margin-top: 40px;
}

.nav-btn {
    flex: 1;
    background: #1e293b;
    border: 3px solid transparent;
    color: #e2e8f0;
    font-size: 26px;
    font-weight: 600;
    padding: 24px;
    border-radius: 12px;
    cursor: pointer;
    transition: transform 0.15s ease, border-color 0.15s ease, background-color 0.15s ease;
}

/* TV Focus States - Critical for remote navigation */
.focusable:focus {
    outline: none;
    border-color: #38bdf8;
    background: #334155;
    transform: scale(1.04);
    box-shadow: 0 0 25px rgba(56, 189, 248, 0.4);
}

#status-box {
    margin-top: 60px;
    font-size: 20px;
    color: #64748b;
}
"""
        with open(os.path.join(dest_dir, "css", "style.css"), "w") as f:
            f.write(style_css)

        # 4. js/main.js
        main_js = f"""// Tizen TV Remote Control Handler
window.addEventListener('load', function() {{
    // Register remote keys with Tizen TV input device API
    if (window.tizen && window.tizen.tvinputdevice) {{
        var keysToRegister = [
            'MediaPlay', 'MediaPause', 'MediaPlayPause', 'MediaStop',
            'MediaFastForward', 'MediaRewind',
            'VolumeUp', 'VolumeDown', 'VolumeMute',
            'ColorF0Red', 'ColorF1Green', 'ColorF2Yellow', 'ColorF3Blue'
        ];
        keysToRegister.forEach(function(key) {{
            try {{
                window.tizen.tvinputdevice.registerKey(key);
            }} catch (e) {{
                console.warn('Could not register TV key:', key, e);
            }}
        }});
    }}

    // Auto-focus the first element
    var firstFocusable = document.querySelector('.focusable');
    if (firstFocusable) {{
        firstFocusable.focus();
    }}
}});

// Listen for D-pad & standard remote navigation
document.addEventListener('keydown', function(e) {{
    var statusBox = document.getElementById('status-box');
    var active = document.activeElement;

    switch(e.keyCode) {{
        case 37: // Left arrow
            navigateFocus(-1);
            break;
        case 39: // Right arrow
            navigateFocus(1);
            break;
        case 13: // Enter / OK
            if (active) {{
                active.click();
                if (statusBox) statusBox.textContent = 'Action triggered on: ' + (active.textContent || active.tagName);
            }}
            break;
        case 10009: // Return / Back button
            if (statusBox) statusBox.textContent = 'Exiting application...';
            if (window.tizen && window.tizen.application) {{
                window.tizen.application.getCurrentApplication().exit();
            }} else {{
                window.history.back();
            }}
            break;
        default:
            console.log('Key pressed:', e.keyCode);
            break;
    }}
}});

function navigateFocus(direction) {{
    var focusables = Array.from(document.querySelectorAll('.focusable'));
    var currentIndex = focusables.indexOf(document.activeElement);
    if (currentIndex === -1) currentIndex = 0;
    var nextIndex = (currentIndex + direction + focusables.length) % focusables.length;
    focusables[nextIndex].focus();
}}
"""
        with open(os.path.join(dest_dir, "js", "main.js"), "w") as f:
            f.write(main_js)

        # 5. icon.png dummy / placeholder
        icon_path = os.path.join(dest_dir, "icon.png")
        if not os.path.exists(icon_path):
            # Write a minimal 1x1 transparent PNG if none exists
            with open(icon_path, "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

        return {
            "app_name": app_name,
            "package_id": pkg_id,
            "application_id": app_id,
            "project_directory": dest_dir,
            "files_created": [
                "config.xml",
                "index.html",
                "css/style.css",
                "js/main.js",
                "icon.png",
            ],
            "next_steps": [
                f"1. Customize HTML/CSS/JS in {dest_dir}",
                f"2. Package with build_and_package_wgt('{dest_dir}')",
                f"3. Install on TV with install_app('/tmp/{safe_name}.wgt')",
            ],
        }

    def build_and_package_wgt(
        self,
        project_dir: str,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Bundle a Web App directory into a standard Tizen .wgt package."""
        p_dir = os.path.abspath(os.path.expanduser(project_dir))
        config_path = os.path.join(p_dir, "config.xml")

        if not os.path.exists(config_path):
            raise SDBError(f"Directory {p_dir} is not a valid Tizen web app: config.xml missing.")

        # Read app id from config.xml
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        pkg_match = re.search(r'package="([A-Za-z0-9]{10})"', content)
        app_match = re.search(r'id="([A-Za-z0-9\.\-_]+)"', content)
        pkg_id = pkg_match.group(1) if pkg_match else "unknown"
        app_id = app_match.group(1) if app_match else "unknown"

        dir_name = os.path.basename(p_dir)
        target_wgt = output_path or f"/tmp/{dir_name}.wgt"

        # Zip files into .wgt
        with zipfile.ZipFile(target_wgt, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(p_dir):
                # Skip hidden folders / git
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for file in files:
                    if file.startswith(".") or file.endswith(".wgt"):
                        continue
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, p_dir)
                    zf.write(full_p, rel_p)

        file_size = os.path.getsize(target_wgt)

        return {
            "wgt_path": target_wgt,
            "package_id": pkg_id,
            "application_id": app_id,
            "size_bytes": file_size,
            "size_kb": round(file_size / 1024, 2),
            "status": "packaged",
        }

    def install_app(
        self,
        package_path: Optional[str] = None,
        package_id: Optional[str] = None,
        target_serial: Optional[str] = None,
        wgt_path: Optional[str] = None,  # alias used by the MCP tool layer
    ) -> Dict[str, Any]:
        """Install a .wgt (Web Widget) or .tpk (Native) package onto the Samsung TV."""
        raw_path = wgt_path or package_path
        if not raw_path:
            raise SDBError("No package path provided (package_path/wgt_path).")
        p = os.path.abspath(os.path.expanduser(raw_path))
        if not os.path.exists(p):
            raise SDBError(f"Package file not found: {p}")

        filename = os.path.basename(p)
        is_wgt = p.endswith(".wgt")

        if is_wgt:
            # Extract package ID from config.xml if not specified
            pkg_id = package_id
            if not pkg_id:
                try:
                    with zipfile.ZipFile(p, "r") as zf:
                        cfg_content = zf.read("config.xml").decode("utf-8", errors="replace")
                        match = re.search(r'package="([^"]+)"', cfg_content)
                        if match:
                            pkg_id = match.group(1)
                except Exception:
                    pass
            if not pkg_id:
                pkg_id = os.path.splitext(filename)[0]

            # Push to TV sdk_tools directory and execute vd_appinstall
            remote_path = f"/home/owner/share/tmp/sdk_tools/{filename}"
            self.sdb.run(["push", p, remote_path], target_serial=target_serial)
            cmd = f"shell:0 vd_appinstall {pkg_id} {remote_path}"
            out = self.sdb.exec_stream(cmd, target_serial=target_serial)
            success = "was_install_app return WAS_TRUE" in out and "reason: Success" in out

            return {
                "package_path": p,
                "package_id": pkg_id,
                "mode": "vd_appinstall (Web .wgt)",
                "output": out,
                "success": success,
            }
        else:
            out = self.sdb.run(["install", p], target_serial=target_serial, timeout=60)
            return {
                "package_path": p,
                "mode": "appinstall (Native .tpk)",
                "output": out,
                "success": "100%" in out or "success" in out.lower(),
            }
    def remote_key_press(
        self,
        key: str,
        target_serial: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a simulated remote control key press to the TV."""
        key_upper = key.strip().upper()
        keycode = REMOTE_KEY_CODES.get(key_upper)
        if keycode is None:
            try:
                keycode = int(key)
            except ValueError:
                valid = list(REMOTE_KEY_CODES.keys())
                raise SDBError(f"Invalid key name: '{key}'. Supported keys: {', '.join(valid)}")

        # Try sending keyevent via shell
        out = self.sdb.shell(f"input keyevent {keycode}", target_serial=target_serial)
        return {
            "key": key_upper,
            "keycode": keycode,
            "output": out or "sent",
        }

    def start_web_inspector(
        self,
        remote_port: int = 9222,
        local_port: int = 9222,
        target_serial: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Forward Chromium remote debugging port to host machine."""
        out = self.sdb.run(
            ["forward", f"tcp:{local_port}", f"tcp:{remote_port}"],
            target_serial=target_serial,
        )
        return {
            "local_port": local_port,
            "remote_port": remote_port,
            "forward_output": out,
            "devtools_url": f"http://localhost:{local_port}",
            "instructions": (
                f"Open Chromium or Chrome and navigate to http://localhost:{local_port} "
                "to inspect and debug web views running on the TV."
            ),
        }

    def get_tv_duid(
        self,
        target_serial: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Query the TV's unique device identifier (DUID) for certificate profile registration."""
        devices = self.sdb.get_devices()
        serial = target_serial or (devices[0]["serial"] if devices else None)
        tv_ip = serial.split(":")[0] if serial and ":" in serial else None

        duid = None
        model_name = "Unknown"
        if tv_ip:
            try:
                req = urllib.request.urlopen(f"http://{tv_ip}:8001/api/v2/", timeout=2)
                data = json.loads(req.read().decode("utf-8"))
                dev = data.get("device", {})
                duid = dev.get("duid", "").replace("uuid:", "")
                model_name = dev.get("modelName", "Unknown")
            except Exception:
                pass

        return {
            "duid": duid,
            "model_name": model_name,
            "target": serial,
            "notes": (
                f"DUID for certificate creation: {duid}"
                if duid else "Could not resolve DUID. Ensure TV is powered on and connected."
            ),
        }

    def create_tizen_cert(
        self,
        name: str,
        password: str,
        output_path: Optional[str] = None,
        email: Optional[str] = None,
        country: str = "US",
        privilege: str = "public",
    ) -> Dict[str, Any]:
        """Generate an author certificate using tizen-cli without Tizen Studio."""
        tizen_bin = shutil.which("tizen-cli") or shutil.which("tizenjs") or "tizen-cli"
        out_file = output_path or os.path.expanduser(f"~/.tizen-certs/{name}_author.p12")
        os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)

        cmd = [
            tizen_bin,
            "create-tizen-cert",
            "--name", name,
            "--password", password,
            "--output", out_file,
            "--country", country,
            "--privilege", privilege,
        ]
        if email:
            cmd.extend(["--email", email])

        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise SDBError(f"Failed to create Tizen certificate: {res.stderr.strip() or res.stdout.strip()}")

        return {
            "author_p12": out_file,
            "password": password,
            "status": "created",
            "output": res.stdout.strip(),
        }

    def sign_and_package_wgt(
        self,
        target_path: str,
        output_path: Optional[str] = None,
        author_p12: Optional[str] = None,
        author_pwd: Optional[str] = None,
        distributor_p12: Optional[str] = None,
        distributor_pwd: Optional[str] = None,
        privilege: str = "public",
    ) -> Dict[str, Any]:
        """Package and sign a project directory or re-sign an existing .wgt package using tizen-cli.

        Args:
            target_path: Path to directory containing config.xml or path to an existing .wgt/.tpk file.
            output_path: Path for output .wgt package.
            author_p12: Path to author .p12 certificate.
            author_pwd: Password for author certificate.
            distributor_p12: Path to distributor .p12 certificate.
            distributor_pwd: Password for distributor certificate.
            privilege: Privilege level ('public' or 'partner').
        """
        tizen_bin = shutil.which("tizen-cli") or shutil.which("tizenjs") or "tizen-cli"
        full_target = os.path.abspath(os.path.expanduser(target_path))
        if not os.path.exists(full_target):
            raise SDBError(f"Target path does not exist: {full_target}")

        is_pkg = full_target.endswith(".wgt") or full_target.endswith(".tpk")
        out_file = output_path or (
            full_target.replace(".wgt", "_signed.wgt") if is_pkg else f"/tmp/{os.path.basename(full_target)}.wgt"
        )

        # Auto-detect Samsung Partner / Public certificates if omitted
        if not author_p12:
            partner_auth = os.path.expanduser("~/.tizen-certs/samsung-partner/author.p12")
            public_auth = os.path.expanduser("~/.tizen-certs/samsung/author.p12")
            if os.path.exists(partner_auth):
                author_p12 = partner_auth
                author_pwd = author_pwd or "password123"
            elif os.path.exists(public_auth):
                author_p12 = public_auth
                author_pwd = author_pwd or "password123"

        if not distributor_p12:
            partner_dist = os.path.expanduser("~/.tizen-certs/samsung-partner/distributor.p12")
            public_dist = os.path.expanduser("~/.tizen-certs/samsung/distributor.p12")
            if os.path.exists(partner_dist):
                distributor_p12 = partner_dist
                distributor_pwd = distributor_pwd or "password123"
            elif os.path.exists(public_dist):
                distributor_p12 = public_dist
                distributor_pwd = distributor_pwd or "password123"

        cmd = [tizen_bin, "build", "." if not is_pkg else full_target, "--type", "wgt", "-o", out_file]
        if author_p12:
            cmd.extend(["--author", os.path.abspath(os.path.expanduser(author_p12))])
        if author_pwd:
            cmd.extend(["--authorPwd", author_pwd])
        if distributor_p12:
            cmd.extend(["--distributor", os.path.abspath(os.path.expanduser(distributor_p12))])
        if distributor_pwd:
            cmd.extend(["--distributorPwd", distributor_pwd])
        if not distributor_p12:
            cmd.extend(["--privilege", privilege])

        cwd = full_target if not is_pkg else os.path.dirname(full_target)
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise SDBError(f"tizen-cli build failed: {res.stderr.strip() or res.stdout.strip()}")

        size = os.path.getsize(out_file) if os.path.exists(out_file) else 0
        return {
            "package_path": out_file,
            "size_bytes": size,
            "size_kb": round(size / 1024, 2),
            "status": "signed_and_packaged",
            "output": res.stdout.strip(),
        }

    def permit_device(
        self,
        cert_dir: Optional[str] = None,
        target_serial: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Push device-profile.xml to the TV to authorize installing developer applications."""
        search_dirs = [
            cert_dir,
            os.path.expanduser("~/.tizen-certs/samsung-partner"),
            os.path.expanduser("~/.tizen-certs/samsung"),
            os.path.expanduser("~/.tizen-certs"),
        ]
        profile_xml = None
        for d in search_dirs:
            if d and os.path.exists(os.path.join(d, "device-profile.xml")):
                profile_xml = os.path.join(d, "device-profile.xml")
                break
        if not profile_xml:
            raise SDBError("device-profile.xml not found. Generate Samsung certificates first.")

        out = self.sdb.run(["push", profile_xml, "/home/owner/share/tmp/sdk_tools/device-profile.xml"], target_serial=target_serial)
        return {
            "device_profile": profile_xml,
            "target": target_serial,
            "status": "permitted",
            "output": out,
        }
