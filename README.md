# 📱 Phone Trackpad for macOS

Turn your Android phone into an ultra-low latency, multi-touch trackpad with native macOS gestures. No third-party Android APK needed—runs directly inside your mobile browser via WebSockets.

Designed specifically for developers and users using external mechanical keyboards without a mouse or trackpad.

---

## ⚡ Features

- **Ultra-low Latency (60 FPS)**: Directly dispatches native C events to the macOS Quartz CoreGraphics HID server.
- **Binary Network Protocol**: Zero JSON overhead (5-byte payload per movement).
- **Zero App Install on Phone**: Works out of the box via mobile Chrome/Safari.
- **Native macOS Multi-Touch Gestures**:
  - **1 Finger Move**: Cursor navigation
  - **1 Finger Tap**: Left click
  - **2 Fingers Move**: Smooth pixel scrolling
  - **2 Fingers Tap**: Right click
  - **3/4 Fingers Swipe Up**: Mission Control
  - **3/4 Fingers Swipe Down**: App Exposé
  - **3/4 Fingers Swipe Left/Right**: Switch Desktop Spaces
- **On-Screen Quick Bar**: Dedicated buttons for Mission Control, Show Desktop, Switch Space, and Left/Right mouse click buttons.

---

## 🛠️ Prerequisites

- **macOS** (Apple Silicon or Intel)
- **Python 3.9+**
- Python libraries:
  ```bash
  pip install pyobjc-framework-Quartz aiohttp
  ```

---

## 🚀 Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rzlfathurrahman/phone-trackpad.git
   cd phone-trackpad
   ```

2. **Run the server**:
   ```bash
   python3 server.py
   ```

3. **Open on Phone**:
   - Make sure your phone and Mac are connected to the same Wi-Fi network (or use USB Tethering).
   - Open your mobile browser and navigate to the IP address printed on your terminal (e.g. `http://192.168.x.x:8000`).

---

## 🔒 Permissions & Troubleshooting

### 1. macOS Accessibility Permission
When running the script for the first time, macOS may request Accessibility permissions:
- Open **System Settings** > **Privacy & Security** > **Accessibility**.
- Enable toggle for **Terminal** (or **Python**).

### 2. Connection Refused / Timed Out
If your phone cannot reach the Mac:
- Open **System Settings** > **Network** > **Firewall**.
- Either disable Firewall temporarily or click **Options** and uncheck *"Block all incoming connections"*.

### 3. Android Multi-Finger Screenshot Conflict (Poco / Xiaomi / HyperOS)
If swiping 3 fingers down triggers a phone screenshot instead of macOS gestures:
- Open phone **Settings** > **Additional Settings** > **Gesture shortcuts** > **Take a screenshot**.
- Turn off **Slide 3 fingers down** (or use the on-screen Quick Bar buttons).

---

## 📄 License

MIT License. Free to use and modify.
