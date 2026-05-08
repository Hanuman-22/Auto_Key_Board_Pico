[README.md](https://github.com/user-attachments/files/27506732/README.md)
# PicoKeyboard

**Type code on any computer from your phone or another laptop — using a Raspberry Pi Pico 2 W as a USB keyboard.**

No drivers needed on the target computer. No software to install. Just plug in and type.

![Status](https://img.shields.io/badge/status-working-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%20Pico%202%20W-red)

## What This Does

```
Phone/Laptop A  ---WiFi--->  Pico 2 W  ---USB--->  Laptop B (target)
 (send code)                (keyboard)             (code appears)
```

You paste code into a web page. The Pico types it on the target computer character by character — as if someone is sitting there typing on a keyboard. The target computer sees a regular USB keyboard. No software needed on it.

## Two Ways to Use

### From Phone
1. Open the Pico's web page in your phone browser
2. Paste code
3. Hit Send
4. Code appears on Laptop B

### From Laptop A
1. Copy code (Ctrl+C)
2. Press Ctrl+Shift+\
3. Preview and confirm
4. Code appears on Laptop B

## Features

- **Web UI** — Clean dark-themed page to paste and send code
- **Chunked transfer** — Handles large files (1000+ lines) by splitting into chunks
- **Stop button** — Stop typing mid-way
- **Random typing** — Type random characters until stopped
- **Time estimate** — Shows estimated completion time
- **Reconnect** — Resume from failed chunk instead of starting over
- **WiFi settings** — Change WiFi from the browser, no USB access needed
- **Hotspot fallback** — If WiFi fails, Pico creates its own "PicoKeyboard" network
- **USB storage stays visible** — You can always access CIRCUITPY to update files

## Hardware Needed

| Item | Cost | Notes |
|------|------|-------|
| Raspberry Pi Pico 2 W | ~$6 | Any Pico 2 W board works (Freenove, official, etc.) |
| USB-C cable | ~$3 | Data cable, not charge-only |
| **Total** | **~$9** | That's it |

## Project Structure

```
PicoKeyboard/
├── pico/                      # Files for the Pico 2 W
│   ├── boot.py                # Enables USB keyboard mode
│   ├── code.py                # Main program (web server + keyboard)
│   └── settings.toml          # WiFi credentials
│
├── laptop/                    # Files for Laptop A (optional)
│   ├── send_to_pico.py        # Clipboard sender script
│   ├── find_pico.py           # Network scanner to find Pico IP
│   └── requirements.txt       # Python dependencies
│
├── README.md
└── LICENSE
```

## Setup Guide

### Step 1 — Flash CircuitPython on the Pico

1. Download CircuitPython for Pico 2 W:
   https://circuitpython.org/board/raspberry_pi_pico2_w/
   
2. Hold **BOOTSEL** button on the Pico
3. While holding, plug USB cable into your computer
4. Hold for 3 seconds, let go
5. **RPI-RP2** drive appears in File Explorer
6. Drag the `.uf2` file onto the RPI-RP2 drive
7. Wait 10 seconds — **CIRCUITPY** drive appears

### Step 2 — Install the HID Library

1. Download the CircuitPython Library Bundle (Version 9.x):
   https://circuitpython.org/libraries
   
2. Extract the zip file
3. Find the `adafruit_hid` folder inside the `lib` folder
4. Copy `adafruit_hid` folder to `CIRCUITPY/lib/`

### Step 3 — Copy Project Files

1. Edit `pico/settings.toml` — put your WiFi name and password:
   ```
   CIRCUITPY_WIFI_SSID = "YourWiFiName"
   CIRCUITPY_WIFI_PASSWORD = "YourWiFiPassword"
   ```

2. Copy these 3 files to the **root** of CIRCUITPY drive:
   - `pico/settings.toml`
   - `pico/boot.py`
   - `pico/code.py`

3. Your CIRCUITPY drive should look like:
   ```
   CIRCUITPY/
   ├── lib/
   │   └── adafruit_hid/
   ├── boot.py
   ├── code.py
   └── settings.toml
   ```

### Step 4 — Unplug and Replug

1. Safely eject CIRCUITPY drive
2. Unplug the Pico
3. Plug it into **Laptop B** (the target computer)
4. Wait 15-20 seconds for WiFi to connect
5. The LED will blink rapidly when connected

### Step 5 — Find the Pico's IP Address

**Option A — Use the scanner** (from any computer on the same WiFi):
```
python laptop/find_pico.py
```

**Option B — Check your router** admin page for connected devices

**Option C — If WiFi failed**, the Pico creates a hotspot:
- Connect to WiFi: **PicoKeyboard**
- Password: **type1234**
- Open: http://192.168.4.1:8080

### Step 6 — Use It!

Open your browser and go to:
```
http://[PICO_IP]:8080
```

You'll see the web interface. Paste code, hit Send, watch it type on Laptop B.

## Laptop A Setup (Optional)

If you want to send code from a laptop instead of your phone:

```bash
cd laptop
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

Edit `send_to_pico.py` and change `PICO_IP` to your Pico's IP address.

Run:
```bash
python send_to_pico.py
```

Copy code (Ctrl+C), press Ctrl+Shift+\, preview, send.

## Changing WiFi

You can change WiFi without accessing the CIRCUITPY drive:

1. Open `http://[PICO_IP]:8080/settings` in your browser
2. Enter new WiFi name and password
3. Click "Save and Reboot"
4. Pico reboots and connects to the new network

If the Pico can't connect to any WiFi, it automatically creates a hotspot:
- **Network:** PicoKeyboard
- **Password:** type1234
- **URL:** http://192.168.4.1:8080/settings

## Tips

- **Use Notepad** on Laptop B for best results — IDEs like VS Code add auto-formatting
- **Increase chunk wait time** if chunks fail on slow networks
- **Press STOP** to halt typing at any time
- **Reconnect button** appears when a chunk fails — resumes from where it stopped
- The Pico only supports **2.4GHz WiFi** — not 5GHz

## Troubleshooting

| Problem | Solution |
|---------|----------|
| CIRCUITPY drive not showing | Unplug, hold BOOTSEL, plug in, reflash CircuitPython |
| WiFi won't connect | Check 2.4GHz band, verify exact WiFi name/password in settings.toml |
| Can't find Pico IP | Run `find_pico.py` or check router, or connect to PicoKeyboard hotspot |
| Typing is garbled | Use Notepad instead of VS Code, reduce typing speed to Slow |
| Chunks failing | Reduce chunk size in web page, check WiFi signal strength |
| Pico crashes on large text | Text is split into chunks automatically, but very large files may need manual splitting |
| Random typing won't stop | Press STOP button, wait a few seconds for it to register |

## How It Works

1. **boot.py** enables the USB HID keyboard device on startup
2. **code.py** connects to WiFi and starts a web server on port 8080
3. The web page lets you paste code and choose typing speed
4. Large text is split into 500-character chunks by the web page
5. Each chunk is sent as a POST request to the Pico
6. The Pico types each character using the `adafruit_hid` library
7. Laptop B sees a regular USB keyboard typing — no drivers needed

## License

MIT License. Free to use, modify, distribute.

## Contributing

Pull requests welcome. Open an issue for bugs or feature requests.
