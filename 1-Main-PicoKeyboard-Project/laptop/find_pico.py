"""Scan network to find PicoKeyboard IP address"""
import socket
import concurrent.futures

def check(ip):
    try:
        req = "GET /status HTTP/1.0\r\nHost: " + ip + "\r\n\r\n"
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((ip, 8080))
        s.sendall(req.encode())
        r = s.recv(512)
        s.close()
        if b"ready" in r:
            return ip
    except Exception:
        pass
    return None

# Get local IP to determine subnet
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(("8.8.8.8", 80))
    my_ip = s.getsockname()[0]
except Exception:
    my_ip = "192.168.1.1"
s.close()

subnet = ".".join(my_ip.split(".")[:3])
print(f"Your IP: {my_ip}")
print(f"Scanning {subnet}.1-254 ...")

ips = [f"{subnet}.{i}" for i in range(1, 255)]
# Also scan 192.168.2.x if different
other = "192.168.2" if subnet != "192.168.2" else "192.168.1"
ips += [f"{other}.{i}" for i in range(1, 255)]

with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
    for future in concurrent.futures.as_completed(
        {ex.submit(check, ip): ip for ip in ips}
    ):
        r = future.result()
        if r:
            print(f"\n  *** FOUND: {r} ***\n")

print("Scan done.")
