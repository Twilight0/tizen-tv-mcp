---
name: tizen-tv
description: Comprehensive guide for Samsung Smart TV (Tizen OS) operations, development, and system administration using SDB (Smart Development Bridge). Covers device connectivity, remote shell inspection, process telemetry, app lifecycle, privacy debloating, lightweight Web App scaffolding and .wgt packaging without Tizen Studio, remote debugging via Chromium inspector, and remote control key simulation.
---

# Samsung Tizen TV Management & Development Guide

This skill provides complete operational patterns for interacting with Samsung Smart TVs running Tizen OS via the Smart Development Bridge (`sdb`). It enables developers and power users to administer, inspect, debloat, and develop applications on Samsung TVs without requiring the full ~2 GB Tizen Studio suite.

---

## 1. Prerequisites & Developer Mode Setup

### On the Samsung Smart TV:
1. Turn on the TV and press **Home** or open **Apps**.
2. Focus on the **Apps** panel and press **1-2-3-4-5** sequentially on the physical remote control.
3. In the Developer Mode pop-up that appears:
   - Toggle **Developer Mode** to **ON**.
   - Enter your computer's LAN IP address into the **Host PC IP** field (e.g. `192.168.1.150`).
   - *Note on loopback*: Do not enter `127.0.0.1` unless running on-TV autonomous daemons (like Vetro). For host administration, use the computer's actual LAN IP.
4. Press **OK** and restart the TV (press and hold the remote power button until the Samsung logo appears, or unplug power for 10 seconds).

### On the Host Machine:
Verify that `sdb` is installed (`which sdb`). If missing on Arch Linux / AliveOS, install `sdb-bin` from AUR or `aliveos-repo`:
```bash
# Verify sdb binary
sdb version
# Smart Development Bridge version 4.2.36 (or 2.3+)
```

---

## 2. Device Connectivity & Lifecycle

Samsung Tizen TVs listen on port **`26101`** by default.

### Connection Commands:
```bash
# Connect to TV over LAN
export TV_IP="192.168.1.100"  # Replace with actual TV IP
sdb connect "$TV_IP:26101"

# Check connected devices and status
sdb devices
# Output format:
# List of devices attached
# 192.168.1.100:26101    device    UE55Q80A

# Query connection state
sdb get-state
# Returns: 'device', 'offline', or 'unknown'

# Disconnect target
sdb disconnect "$TV_IP:26101"
# Or disconnect all:
sdb disconnect
```

### Authentication & Pairing Diagnostics:
* **First-time prompt**: When connecting for the first time, the TV screen will display an authorization popup ("Allow connection from Host PC?"). You must accept it with the TV remote.
* **Status stuck in `offline`**:
  1. Verify the TV is powered on (not in deep standby / eco mode).
  2. Confirm Host PC IP in the TV Developer Mode menu matches the host's current local IP.
  3. Restart the SDB server on the host:
     ```bash
     sdb kill-server
     sdb start-server
     sdb connect "$TV_IP:26101"
     ```

---

## 3. Remote Shell & Telemetry Inspection

Tizen runs a Linux kernel with standard UNIX utilities and Samsung/Tizen-specific management tools.

### Shell Access:
```bash
# Interactive remote shell
sdb shell

# One-shot command execution
sdb shell "<command>"
```

### System Telemetry & Hardware Queries:
```bash
# Hardware & CPU specs
sdb shell "cat /proc/cpuinfo"
sdb shell "uname -a"

# Memory & Swap / zRAM
sdb shell "cat /proc/meminfo"
sdb shell "free -m"

# Real-time resource usage & processes
sdb shell "top -b -n 1 | head -n 30"
sdb shell "ps -ef"

# Storage & partition mounts
sdb shell "df -h"

# Network interfaces & routes
sdb shell "ip a"
sdb shell "netstat -tuln"

# TV firmware and platform properties (vconf values)
sdb shell "vconftool -g db/system/model_name"
sdb shell "vconftool -g db/system/platform_version"
```

### Logging (`dlog`):
Tizen uses `dlog` (similar to Android's `logcat`):
```bash
# Stream device logs
sdb dlog

# Filter by priority (V=Verbose, D=Debug, I=Info, W=Warn, E=Error, F=Fatal)
sdb dlog -v time *:E

# Filter by application or tag
sdb dlog -v time Console:* *:S
```

---

## 4. Application Management & Lifecycle

Tizen distinguishes between **Application IDs** (format: `<pkg_id>.<app_name>` or alphanumeric hash) and **Package IDs** (10-character unique string, e.g. `org.tizen.emanual-app`).

### Listing Installed Applications:
```bash
# List all apps with installed details
sdb shell "app_launcher -l"

# Query the package manager directly
sdb shell "pkg_cmd -l"
```

### Launching & Terminating Apps:
```bash
# Launch application by app ID
sdb shell "app_launcher -s <app_id>"

# Examples of common apps:
# YouTube:
sdb shell "app_launcher -s 9Ur5IzDKqV.TizenYouTube"
# Netflix:
sdb shell "app_launcher -s 3201512006785"
# Spotify:
sdb shell "app_launcher -s 3201606009684"
# Amazon Prime Video:
sdb shell "app_launcher -s 3201512006785"
# Vetro Dashboard:
sdb shell "app_launcher -s 3G9P87z91L.Vetro"

# Terminate / kill running app:
sdb shell "app_launcher -k <app_id>"
```

### Package Installation & Removal:
```bash
# Install Tizen Web Widget (.wgt) or Native (.tpk) package
sdb install /path/to/application.wgt

# Uninstall package by package ID
sdb uninstall <pkg_id>
```

---

## 5. Debloating & Privacy Hardening

Samsung TVs run background analytics, Automated Content Recognition (ACR), and recommendation collectors that consume RAM and CPU cycles.

### Known Telemetry & Analytics Services:
| Component ID | Description | Safe Action |
| :--- | :--- | :--- |
| `com.samsung.tv.acr` | Automated Content Recognition (screen/audio fingerprinter) | Disable |
| `com.samsung.tv.canalysis-service` | Content viewing & behavioral analysis service | Disable |
| `com.samsung.tv.vision-data-recognition-service` | Visual recognition / video content metadata engine | Disable |
| `com.samsung.tv.contents-recognition-dbmgr` | Recognition database cache manager | Disable |
| `com.samsung.tv.nvision-analysis-dbmgr` | Neural vision analysis database manager | Disable |

### CRITICAL Protected Components — NEVER TOUCH:
* **`com.samsung.tv.coba.adagent`**: Protected core dependency. Disabling or removing can cause launcher bootloops or boot crashes.
* **`org.tizen.*` core system daemons**: Device manager, security manager, audio manager, display manager.

### Disabling vs. Stopping vs. Removing:
1. **Disable Flag**: Marks the application component as disabled so the system does not load it.
   ```bash
   # Via Tizen package command (if privileged)
   sdb shell "pkg_cmd -d com.samsung.tv.acr"
   ```
2. **Process Stop**: Terminating running PID does not prevent restart if the auto-restart flag is on:
   ```bash
   sdb shell "kill -9 \$(pidof canalysis-service 2>/dev/null)"
   ```
3. **Local Domain / Ad Blocking**:
   You can map telemetry domains directly in the TV's `/etc/hosts` if root access is present (or block upstream via Pi-hole / AdGuard Home):
   ```text
   0.0.0.0 acr0.samsungcloudsolution.com
   0.0.0.0 log-config.samsungcloudsolution.com
   0.0.0.0 sas.samsungcloudsolution.com
   ```

---

## 6. Lightweight Tizen Web App Development (Without Tizen Studio)

Tizen Web Apps (`.wgt`) are zipped HTML/CSS/JavaScript applications containing a W3C-compliant `config.xml` manifest.

### Anatomy of a Tizen Web App:
```text
my-tv-app/
├── config.xml          # Required W3C / Tizen package manifest
├── index.html          # Entry point
├── css/
│   └── style.css       # Styles (designed for 1920x1080 or 3840x2160)
├── js/
│   └── main.js         # Navigation & Remote key listener
└── icon.png            # 117x117 or 512x512 app icon
```

### 1. `config.xml` Manifest Template:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<widget xmlns="http://www.w3.org/ns/widgets" 
        xmlns:tizen="http://tizen.org/ns/tizen" 
        id="http://yourdomain.org/MyTvApp" 
        version="1.0.0" 
        viewmodes="maximized">
    <tizen:application id="aBcDeFgHiJ.MyTvApp" 
                       package="aBcDeFgHiJ" 
                       version="1.0.0" 
                       required_version="3.0"/>
    <content src="index.html"/>
    <feature name="http://tizen.org/feature/screen.size.all"/>
    <icon src="icon.png"/>
    <name>My TV App</name>
    <tizen:profile name="tv"/>
    <tizen:setting screen-orientation="landscape" context-menu="enable" background-support="disable"/>
    <tizen:privilege name="http://tizen.org/privilege/application.launch"/>
    <tizen:privilege name="http://tizen.org/privilege/tv.inputdevice"/>
</widget>
```
*Note on Package ID format*: The package ID (`package="aBcDeFgHiJ"`) must be a 10-character alphanumeric string. The application ID must be `<package_id>.<AppName>`.

### 2. Remote Control Key Handling (`main.js`):
Samsung TV remotes send keyboard events with standard DOM codes:
```javascript
// Register TV remote keys with the tizen input device API
window.addEventListener('load', function() {
    if (window.tizen && window.tizen.tvinputdevice) {
        var supportedKeys = [
            'MediaPlay', 'MediaPause', 'MediaPlayPause', 'MediaStop',
            'MediaFastForward', 'MediaRewind',
            'VolumeUp', 'VolumeDown', 'VolumeMute',
            'ColorF0Red', 'ColorF1Green', 'ColorF2Yellow', 'ColorF3Blue'
        ];
        supportedKeys.forEach(function(key) {
            try {
                window.tizen.tvinputdevice.registerKey(key);
            } catch (e) {
                console.warn('Failed to register key:', key, e);
            }
        });
    }
});

// Listen for D-pad & standard remote navigation
document.addEventListener('keydown', function(e) {
    switch(e.keyCode) {
        case 37: // Left arrow
            navigateLeft();
            break;
        case 38: // Up arrow
            navigateUp();
            break;
        case 39: // Right arrow
            navigateRight();
            break;
        case 40: // Down arrow
            navigateDown();
            break;
        case 13: // Enter / OK
            triggerAction();
            break;
        case 10009: // Return / Back button
            if (window.tizen && window.tizen.application) {
                window.tizen.application.getCurrentApplication().exit();
            }
            break;
    }
});
```

### 3. Packaging & Signing with `tizen-cli` (Zero Studio):
Use `tizen-cli` to package and generate official XML signatures (`author-signature.xml`, `signature1.xml`):
```bash
# Generate Author certificate (.p12)
tizen-cli create-tizen-cert --name "MyName" --password "secret123" --output ~/.tizen-certs/author.p12

# Package and sign a Web App directory
cd /path/to/my-tv-app
tizen-cli build . --type wgt --author ~/.tizen-certs/author.p12 --authorPwd "secret123" --privilege public --output /tmp/my-tv-app.wgt

# Or re-sign an existing third-party .wgt (e.g. Vetro or community apps)
tizen-cli build /path/to/app.wgt --type wgt --author ~/.tizen-certs/author.p12 --authorPwd "secret123" --privilege public --output /tmp/resigned.wgt

# Install directly to the connected TV
sdb install /tmp/my-tv-app.wgt
```

---

## 7. Remote Debugging & Chromium Web Inspector

Tizen TV runs Web Apps inside a WebKit / Chromium Web Runtime (WRT). You can debug any running Web App using Chrome/Chromium DevTools over SDB port forwarding.

### Workflow:
1. Launch your application on the TV.
2. Find the Web Inspector debugging port on the TV:
   ```bash
   sdb shell "netstat -tuln | grep 922"
   # Or query the inspector port of the running app:
   sdb shell "cat /tmp/.debug.*"
   ```
3. Forward the inspector port to your local machine:
   ```bash
   sdb forward tcp:9222 tcp:9222
   ```
4. Open Chrome or Chromium on your computer and navigate to:
   ```text
   http://localhost:9222
   # or
   devtools://devtools/bundled/inspector.html?ws=localhost:9222/...
   ```
5. You can now inspect elements, view console logs, set breakpoints, and profile memory directly on the TV screen.

---

## 8. Remote Control Key Simulation & Automation

You can simulate remote button presses directly over SDB to automate TV testing or control navigation:

```bash
# Inject keys using Tizen's internal input injection tool
# Key codes:
# 10009: Back / Return
# 13: OK / Enter
# 38: Up, 40: Down, 37: Left, 39: Right
# 447: Volume Up, 448: Volume Down, 449: Mute

# Send key press via shell (when input event tools are available)
sdb shell "input keyevent 13" # OK button
sdb shell "input keyevent 10009" # Return / Back
```

---

## 9. File Transfer & Port Forwarding

```bash
# Push local file/dir to TV
sdb push ./local_script.sh /tmp/local_script.sh
sdb shell "chmod +x /tmp/local_script.sh"

# Pull file from TV to host
sdb pull /var/log/messages /tmp/tv_messages.log

# Port Forwarding: Host -> TV
# Access TV service (e.g. Vetro dashboard on port 8099) via localhost:8099
sdb forward tcp:8099 tcp:8099

# Reverse Port Forwarding: TV -> Host
# Allow TV to connect to local development server on host machine:
sdb reverse tcp:3000 tcp:3000
```

---

## 10. Safety Checklist & Heuristics

1. **Verify Target Before Action**: Always run `sdb devices` to ensure only the intended TV is connected before executing destructive operations.
2. **Never Blindly Delete Packages**: Use `app_launcher -k` (terminate) or disable components rather than `sdb uninstall` on vendor packages. Uninstalling core system packages (`org.tizen.*`) requires a full factory reset.
3. **Keep Host PC IP Updated**: If your PC's DHCP IP address changes, you must re-enter it in the TV's Developer Mode menu or connections will fail with authorization errors.
4. **Network Isolation**: When running TV web services or remote debugging (like Vetro or DevTools), keep the TV on an isolated VLAN or local LAN—do not expose SDB port `26101` to the public internet.
