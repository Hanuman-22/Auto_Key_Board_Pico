"""
PicoKeyboard - Laptop Sender
Copy code -> Press Ctrl+Shift+\ -> Types on Laptop B
"""

import keyboard
import socket
import json
import time
import threading
import tkinter as tk

# --- Config ---
PICO_IP = "192.168.2.64"  # Change to your Pico IP
PICO_PORT = 8080
HOTKEY = "ctrl+shift+\\"
QUIT = "ctrl+shift+q"
DELAY = 30


def send(text, dms=DELAY):
    body = json.dumps({"text": text, "delay_ms": dms})
    req = ("POST /type HTTP/1.0\r\n"
           "Content-Type: application/json\r\n"
           "Content-Length: " + str(len(body)) + "\r\n"
           "\r\n" + body)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(15)
        s.connect((PICO_IP, PICO_PORT))
        s.sendall(req.encode("utf-8"))
        r = b""
        try:
            while True:
                c = s.recv(1024)
                if not c:
                    break
                r += c
        except socket.timeout:
            pass
        s.close()
        rt = r.decode("utf-8")
        if "\r\n\r\n" in rt:
            bp = rt.split("\r\n\r\n", 1)[1]
            try:
                print(f"  -> {json.loads(bp)}")
                return True
            except Exception:
                pass
        return True
    except Exception as e:
        print(f"  -> Error: {e}")
        return False


def clip():
    try:
        r = tk.Tk()
        r.withdraw()
        t = r.clipboard_get()
        r.destroy()
        return t
    except Exception:
        return ""


def preview(text):
    res = {"ok": False, "text": text}
    root = tk.Tk()
    root.title("Send to Laptop B")
    root.attributes("-topmost", True)
    root.configure(bg="#1e1e1e")
    w, h = 650, 500
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    top = tk.Frame(root, bg="#1e1e1e")
    top.pack(fill=tk.X, padx=16, pady=(12, 4))
    tk.Label(top, text="Code to send", font=("Arial", 13, "bold"),
             fg="white", bg="#1e1e1e").pack(side=tk.LEFT)
    tk.Label(top, text=f"{text.count(chr(10))+1} lines | {len(text)} chars",
             font=("Arial", 9), fg="#888", bg="#1e1e1e").pack(side=tk.RIGHT)

    fr = tk.Frame(root, bg="#1e1e1e")
    fr.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)
    sc = tk.Scrollbar(fr)
    sc.pack(side=tk.RIGHT, fill=tk.Y)
    tx = tk.Text(fr, font=("Consolas", 11), bg="#2d2d2d", fg="#d4d4d4",
                 insertbackground="white", wrap=tk.NONE,
                 yscrollcommand=sc.set, padx=8, pady=8)
    tx.pack(fill=tk.BOTH, expand=True)
    tx.insert("1.0", text)
    sc.config(command=tx.yview)

    bf = tk.Frame(root, bg="#1e1e1e")
    bf.pack(fill=tk.X, padx=16, pady=(4, 12))

    def no():
        res["ok"] = False
        root.destroy()

    def yes():
        res["text"] = tx.get("1.0", tk.END).rstrip('\n')
        res["ok"] = True
        root.destroy()

    tk.Button(bf, text="Cancel", font=("Arial", 10), bg="#333", fg="#eee",
              relief=tk.FLAT, padx=16, pady=6, command=no).pack(side=tk.LEFT)
    tk.Button(bf, text="Send", font=("Arial", 10, "bold"), bg="#0e639c",
              fg="white", relief=tk.FLAT, padx=16, pady=6,
              command=yes).pack(side=tk.RIGHT)
    root.bind("<Return>", lambda e: yes())
    root.bind("<Escape>", lambda e: no())
    root.mainloop()
    return res["ok"], res["text"]


def go():
    print(f"\n{'='*40}")
    print("  TRIGGERED")
    print(f"{'='*40}")
    time.sleep(0.2)
    t = clip()
    if not t or not t.strip():
        print("  -> Clipboard empty")
        return
    print(f"  -> {len(t)} chars")
    ok, final = preview(t)
    if not ok:
        print("  -> Cancelled")
        return
    print(f"  -> Sending {len(final)} chars...")
    if send(final):
        print("  -> Done! Check Laptop B")
    else:
        print("  -> Failed")
    print(f"{'='*40}\n")


def main():
    print()
    print("  +======================================+")
    print("  |  PicoKeyboard - Laptop Sender        |")
    print("  +======================================+")
    print(f"  |  Send:  Ctrl+Shift+\\                 |")
    print(f"  |  Quit:  Ctrl+Shift+Q                 |")
    print("  +======================================+")
    print()

    # Check pico
    try:
        req = "GET /status HTTP/1.0\r\nHost: " + PICO_IP + "\r\n\r\n"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((PICO_IP, PICO_PORT))
        s.sendall(req.encode())
        r = s.recv(1024)
        s.close()
        if b"ready" in r:
            print(f"  [OK] Pico at {PICO_IP}")
        else:
            print(f"  [--] Pico not ready")
    except Exception:
        print(f"  [--] Pico not reachable at {PICO_IP}")

    print("\n  Copy code (Ctrl+C) then press Ctrl+Shift+\\\n")

    keyboard.add_hotkey(HOTKEY, lambda: threading.Thread(
        target=go, daemon=True).start())
    keyboard.wait(QUIT)
    print("\n  Bye!")


if __name__ == "__main__":
    main()
