# PicoKeyboard v3.1
# Fixed: random stop, flush button, static IP

import time
import os
import board
import digitalio
import wifi
import socketpool
import json
import microcontroller
import gc
import ipaddress
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

PORT = 8080
STATIC_IP = "10.39.206.100"
STATIC_MASK = "255.255.255.0"
STATIC_GW = "10.39.206.5"

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

stop = False


def blink(n, s=0.15):
    for _ in range(n):
        led.value = True
        time.sleep(s)
        led.value = False
        time.sleep(s)


def save_wifi(ssid, pw):
    sb = ssid.encode("utf-8")[:32]
    pb = pw.encode("utf-8")[:64]
    d = bytearray(98)
    d[0] = len(sb)
    d[1:1+len(sb)] = sb
    d[33] = len(pb)
    d[34:34+len(pb)] = pb
    microcontroller.nvm[0:98] = d


def load_wifi():
    try:
        d = microcontroller.nvm[0:98]
        sl = d[0]
        if sl == 0 or sl > 32 or sl == 0xFF:
            return None, None
        ssid = bytes(d[1:1+sl]).decode("utf-8")
        pl = d[33]
        if pl > 64:
            return ssid, ""
        return ssid, bytes(d[34:34+pl]).decode("utf-8")
    except Exception:
        return None, None


ns, np = load_wifi()
if ns and len(ns) > 0:
    wifi_ssid, wifi_pass = ns, np or ""
    src = "saved"
else:
    wifi_ssid = os.getenv("CIRCUITPY_WIFI_SSID") or ""
    wifi_pass = os.getenv("CIRCUITPY_WIFI_PASSWORD") or ""
    src = "toml"

print("\n" + "=" * 40)
print("  PicoKeyboard v3.1")
print("=" * 40)

ip = ""
is_hotspot = False
HS_SSID = "PicoKeyboard"
HS_PASS = "type1234"

if wifi_ssid:
    print(f"\nWiFi: {wifi_ssid} ({src})")
    blink(3, 0.1)
    ok = False
    for a in range(5):
        try:
            wifi.radio.set_ipv4_address(
                ipv4=ipaddress.IPv4Address(STATIC_IP),
                netmask=ipaddress.IPv4Address(STATIC_MASK),
                gateway=ipaddress.IPv4Address(STATIC_GW)
            )
            wifi.radio.connect(wifi_ssid, wifi_pass)
            ip = str(wifi.radio.ipv4_address)
            print(f"OK! IP: {ip}")
            ok = True
            blink(5, 0.08)
            break
        except Exception as e:
            print(f"  {a+1}/5: {e}")
            time.sleep(2)
    if not ok:
        wifi_ssid = ""

if not wifi_ssid:
    print(f"\nHotspot: {HS_SSID} / {HS_PASS}")
    is_hotspot = True
    try:
        wifi.radio.stop_station()
    except Exception:
        pass
    for a in range(3):
        try:
            wifi.radio.start_ap(HS_SSID, HS_PASS, channel=6)
            ip = str(wifi.radio.ipv4_address_ap)
            if ip == "0.0.0.0":
                ip = "192.168.4.1"
            print(f"Hotspot OK! IP: {ip}")
            blink(10, 0.05)
            break
        except Exception as e:
            print(f"  AP {a+1}/3: {e}")
            time.sleep(2)
            try:
                wifi.radio.stop_ap()
            except Exception:
                pass
    else:
        print("Failed. Reboot...")
        time.sleep(3)
        microcontroller.reset()

print("Keyboard...")
kbd = Keyboard(usb_hid.devices)
lay = KeyboardLayoutUS(kbd)
print("Ready!")
gc.collect()


def type_text(text, dms=10):
    global stop
    ds = dms / 1000.0
    led.value = True
    total = 0
    for ch in text:
        if stop:
            led.value = False
            return total
        if ch == '\n':
            kbd.send(Keycode.ENTER)
        elif ch == '\t':
            kbd.send(Keycode.TAB)
        elif ch == '\r':
            pass
        else:
            try:
                lay.write(ch)
            except ValueError:
                pass
        total += 1
        time.sleep(ds)
    led.value = False
    return total


def type_random(dms=50):
    global stop
    import random
    chars = "abcdefghijklmnopqrstuvwxyz0123456789 "
    ds = dms / 1000.0
    led.value = True
    c = 0
    stop = False
    while not stop:
        if random.randint(0, 20) == 0:
            kbd.send(Keycode.ENTER)
        else:
            try:
                lay.write(chars[random.randint(0, len(chars)-1)])
            except ValueError:
                pass
        c += 1
        time.sleep(ds)
        if c % 30 == 0:
            gc.collect()
    led.value = False
    stop = False
    print(f"  Random: {c}")
    return c


def page_main():
    net = HS_SSID if is_hotspot else wifi_ssid
    return ('<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PicoKeyboard</title>'
    '<style>'
    '*{box-sizing:border-box;margin:0;padding:0}'
    'body{font-family:-apple-system,sans-serif;background:#111;color:#eee;padding:16px;max-width:800px;margin:0 auto}'
    'h1{font-size:22px;margin-bottom:4px;color:#4fc3f7}'
    '.su{font-size:12px;color:#888;margin-bottom:14px}'
    'textarea{width:100%;height:35vh;background:#1e1e1e;color:#d4d4d4;border:1px solid #333;border-radius:8px;padding:12px;font-family:monospace;font-size:14px;resize:vertical}'
    'textarea:focus{outline:none;border-color:#4fc3f7}'
    '.r{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}'
    'button{padding:12px 18px;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer}'
    '.se{background:#4fc3f7;color:#000;flex:1;min-width:120px}'
    '.se:disabled{background:#555;color:#999}'
    '.sp{background:#e53935;color:#fff;flex:1;min-width:80px}'
    '.sp:disabled{background:#444;color:#777}'
    '.rn{background:#7c4dff;color:#fff;flex:1;min-width:80px}'
    '.rn:disabled{background:#555;color:#999}'
    '.fl{background:#ff6d00;color:#fff;flex:1;min-width:80px}'
    '.cl{background:#333;color:#eee}'
    '.rc{background:#ff9800;color:#000;flex:1;min-width:100px;display:none}'
    'select{background:#1e1e1e;color:#eee;border:1px solid #333;border-radius:8px;padding:8px;font-size:14px}'
    '#st{margin-top:10px;padding:10px;border-radius:8px;font-size:14px;display:none}'
    '.bar{width:100%;height:6px;background:#222;border-radius:3px;margin-top:8px;overflow:hidden}'
    '.bar div{height:100%;background:#4fc3f7;border-radius:3px;transition:width 0.3s}'
    '.ti{font-size:12px;color:#aaa;margin-top:6px}'
    '.in{font-size:12px;color:#666;margin-top:12px;text-align:center}'
    '.na{margin-top:12px;text-align:center}'
    '.na a{color:#4fc3f7;font-size:13px;text-decoration:none}'
    '</style></head><body>'
    '<h1>PicoKeyboard</h1>'
    '<div class="su">Paste code. Send to Laptop B.</div>'
    '<textarea id="c" placeholder="Paste code here..." oninput="ue()"></textarea>'
    '<div class="r">'
    '<select id="d" onchange="ue()">'
    '<option value="10">Fast</option>'
    '<option value="30" selected>Normal</option>'
    '<option value="80">Slow</option>'
    '</select>'
    '<button class="cl" onclick="clr()">Clear</button>'
    '</div>'
    '<div id="es" class="ti"></div>'
    '<div class="r">'
    '<button class="se" id="sb" onclick="go()">Send</button>'
    '<button class="sp" id="xb" onclick="stp()">STOP</button>'
    '<button class="fl" id="fb" onclick="flush()">FLUSH</button>'
    '</div>'
    '<div class="r">'
    '<button class="rn" id="rb" onclick="rnd()">Random</button>'
    '<button class="rc" id="rc" onclick="recon()">Reconnect</button>'
    '</div>'
    '<div id="st"></div>'
    '<div class="in">' + ip + ' | ' + net + '</div>'
    '<div class="na"><a href="/settings">WiFi Settings</a></div>'
    '<script>'
    'var CK=500,sn=0,ra=0,sp=0,fi=-1,sc=[],sd=30;'

    'function ue(){'
    'var t=document.getElementById("c").value,d=parseInt(document.getElementById("d").value),e=document.getElementById("es");'
    'if(!t){e.textContent="";return}'
    'var c=t.length,l=t.split("\\n").length,ck=Math.ceil(c/CK);'
    'var ts=c*d/1000+ck*2.5,h=Math.floor(ts/3600),m=Math.floor(ts%3600/60),s=Math.floor(ts%60),r="";'
    'if(h>0)r+=h+"h ";if(m>0)r+=m+"m ";r+=s+"s";'
    'e.textContent=l+" lines | "+c+" chars | ~"+ck+" chunks | "+r}'

    'function clr(){document.getElementById("c").value="";ue();ss("","")}'

    'function ss(bg,txt){var s=document.getElementById("st");if(!txt){s.style.display="none";return}s.style.display="block";s.style.background=bg;s.textContent=txt}'

    'function flush(){'
    'sp=1;sn=0;ra=0;fi=-1;sc=[];'
    'document.getElementById("c").value="";ue();'
    'var x=new XMLHttpRequest();x.open("POST","/stop");x.timeout=3000;'
    'x.onload=function(){ss("#1b5e20","Flushed! Everything cleared and stopped.")};'
    'x.onerror=function(){ss("#1b5e20","Flushed locally. Pico stop sent.")};'
    'x.send("");'
    'document.getElementById("sb").disabled=0;document.getElementById("sb").textContent="Send";'
    'document.getElementById("rb").disabled=0;document.getElementById("rb").textContent="Random";'
    'document.getElementById("rc").style.display="none"}'

    'function stp(){'
    'sp=1;sn=0;'
    'ss("#e65100","Stopping...");'
    'var x=new XMLHttpRequest();x.open("POST","/stop");x.timeout=5000;'
    'x.onload=function(){'
    'ss("#e65100","Stopped!");'
    'ra=0;'
    'document.getElementById("sb").disabled=0;document.getElementById("sb").textContent="Send";'
    'document.getElementById("rb").disabled=0;document.getElementById("rb").textContent="Random";'
    'document.getElementById("rc").style.display="none"};'
    'x.onerror=function(){ss("#e65100","Stop sent");sn=0;ra=0};'
    'x.send("")}'

    'function go(){'
    'var t=document.getElementById("c").value,d=document.getElementById("d").value,s=document.getElementById("st");'
    'if(!t){ss("#b71c1c","No code");return}'
    'sp=0;sn=1;fi=-1;'
    'document.getElementById("sb").disabled=1;document.getElementById("sb").textContent="Sending...";'
    'document.getElementById("rb").disabled=1;'
    'document.getElementById("rc").style.display="none";'
    'var ch=[],i=0;'
    'while(i<t.length){var e=Math.min(i+CK,t.length);if(e<t.length){var n=t.lastIndexOf("\\n",e);if(n>i)e=n+1}ch.push(t.substring(i,e));i=e}'
    'sc=ch;sd=parseInt(d);ss("#1a237e","Starting...");sk(ch,0,parseInt(d))}'

    'function recon(){'
    'if(fi>=0&&sc.length>0){sp=0;sn=1;'
    'document.getElementById("sb").disabled=1;document.getElementById("sb").textContent="Sending...";'
    'document.getElementById("rb").disabled=1;'
    'ss("#1a237e","Reconnecting...");sk(sc,fi,sd)}}'

    'function sk(ch,i,dl){'
    'if(sp||!sn){ss("#e65100","Stopped "+i+"/"+ch.length);sn=0;fi=i;'
    'document.getElementById("sb").disabled=0;document.getElementById("sb").textContent="Send";'
    'document.getElementById("rb").disabled=0;document.getElementById("rc").style.display="block";return}'
    'if(i>=ch.length){ss("#1b5e20","Done! "+ch.length+" chunks");sn=0;'
    'document.getElementById("sb").disabled=0;document.getElementById("sb").textContent="Send";'
    'document.getElementById("rb").disabled=0;document.getElementById("rc").style.display="none";return}'
    'var p=Math.round(i/ch.length*100),rm=0;for(var r=i;r<ch.length;r++)rm+=ch[r].length;'
    'var rs=rm*dl/1000+(ch.length-i)*2.5,m=Math.floor(rs/60),ss2=Math.floor(rs%60),rt=m>0?m+"m "+ss2+"s":ss2+"s";'
    'var st=document.getElementById("st");st.style.display="block";st.style.background="#1a237e";'
    'st.innerHTML=(i+1)+"/"+ch.length+" | "+rt+\' left<div class="bar"><div style="width:\'+p+\'%"></div></div>\';'
    'var x=new XMLHttpRequest();x.open("POST","/type");x.setRequestHeader("Content-Type","application/json");x.timeout=60000;'
    'x.onload=function(){'
    'if(sp||!sn){ss("#e65100","Stopped");sn=0;fi=i+1;'
    'document.getElementById("sb").disabled=0;document.getElementById("sb").textContent="Send";'
    'document.getElementById("rb").disabled=0;document.getElementById("rc").style.display="block";return}'
    'if(x.status==200){var r=JSON.parse(x.responseText),w=r.chars*(dl/1000)*1000;if(i==0)w+=2500;w+=800;'
    'var dp=Math.round((i+1)/ch.length*100);'
    'var st2=document.getElementById("st");st2.innerHTML="Typing "+(i+1)+"/"+ch.length+\'<div class="bar"><div style="width:\'+dp+\'%"></div></div>\';'
    'setTimeout(function(){sk(ch,i+1,dl)},w)}'
    'else{ss("#b71c1c","Error chunk "+(i+1));fi=i;sn=0;'
    'document.getElementById("sb").disabled=0;document.getElementById("sb").textContent="Send";'
    'document.getElementById("rb").disabled=0;document.getElementById("rc").style.display="block"}};'
    'x.onerror=function(){ss("#b71c1c","Lost chunk "+(i+1));fi=i;sn=0;'
    'document.getElementById("sb").disabled=0;document.getElementById("sb").textContent="Send";'
    'document.getElementById("rb").disabled=0;document.getElementById("rc").style.display="block"};'
    'x.ontimeout=function(){ss("#b71c1c","Timeout chunk "+(i+1));fi=i;sn=0;'
    'document.getElementById("sb").disabled=0;document.getElementById("sb").textContent="Send";'
    'document.getElementById("rb").disabled=0;document.getElementById("rc").style.display="block"};'
    'var b={text:ch[i],delay_ms:dl};if(i==0)b.first_chunk=true;x.send(JSON.stringify(b))}'

    'function rnd(){'
    'if(ra)return;sp=0;ra=1;'
    'document.getElementById("sb").disabled=1;'
    'document.getElementById("rb").disabled=1;document.getElementById("rb").textContent="Running...";'
    'ss("#1a237e","Random typing... press STOP");'
    'var x=new XMLHttpRequest();x.open("POST","/random");x.setRequestHeader("Content-Type","application/json");x.timeout=0;'
    'x.onload=function(){ra=0;ss("#e65100","Random stopped");'
    'document.getElementById("sb").disabled=0;document.getElementById("rb").disabled=0;document.getElementById("rb").textContent="Random"};'
    'x.onerror=function(){ra=0;'
    'document.getElementById("sb").disabled=0;document.getElementById("rb").disabled=0;document.getElementById("rb").textContent="Random"};'
    'x.send(JSON.stringify({delay_ms:50}))}'

    'ue()'
    '</script></body></html>')


def page_settings():
    net = wifi_ssid if wifi_ssid else HS_SSID
    mode = "Hotspot" if is_hotspot else "WiFi"
    return ('<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>WiFi</title>'
    '<style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,sans-serif;background:#111;color:#eee;padding:16px;max-width:500px;margin:0 auto}'
    'h1{font-size:20px;margin-bottom:4px;color:#4fc3f7}.su{font-size:12px;color:#888;margin-bottom:20px}'
    'label{display:block;font-size:14px;margin-bottom:4px;color:#ccc}'
    'input{width:100%;background:#1e1e1e;color:#eee;border:1px solid #333;border-radius:8px;padding:12px;font-size:16px;margin-bottom:16px}'
    'button{width:100%;padding:14px;background:#4fc3f7;color:#000;border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer}'
    '#st{margin-top:12px;padding:10px;border-radius:8px;font-size:14px}'
    '.w{background:#333;color:#ffb74d;margin-bottom:16px;padding:10px;border-radius:8px;font-size:13px}'
    '.c{background:#1e1e1e;padding:10px;border-radius:8px;margin-bottom:16px;font-size:13px;color:#888}'
    '.n{margin-top:16px;text-align:center}.n a{color:#4fc3f7;font-size:13px;text-decoration:none}</style></head><body>'
    '<h1>WiFi Settings</h1><div class="su">Change WiFi</div>'
    '<div class="c">Now: <b style="color:#eee">' + net + '</b> | ' + mode + ' | ' + ip + '</div>'
    '<div class="w">Pico reboots after saving.</div>'
    '<label>WiFi Name</label><input type="text" id="s" placeholder="WiFi name">'
    '<label>Password</label><input type="password" id="p" placeholder="Password">'
    '<button onclick="sv()">Save and Reboot</button><div id="st"></div>'
    '<div class="n"><a href="/">Back</a></div>'
    '<script>function sv(){var s=document.getElementById("s").value,p=document.getElementById("p").value,t=document.getElementById("st");'
    'if(!s){t.style.background="#b71c1c";t.textContent="Enter name";return}'
    't.style.background="#333";t.textContent="Saving...";'
    'var x=new XMLHttpRequest();x.open("POST","/save_wifi");x.setRequestHeader("Content-Type","application/json");'
    'x.onload=function(){t.style.background="#1b5e20";t.textContent="Saved! Rebooting..."};'
    'x.send(JSON.stringify({ssid:s,password:p}))}</script></body></html>')


# --- Server ---

pool = socketpool.SocketPool(wifi.radio)
srv = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
srv.setsockopt(pool.SOL_SOCKET, pool.SO_REUSEADDR, 1)
srv.bind(("0.0.0.0", PORT))
srv.listen(2)

gc.collect()
print(f"\n{'='*40}")
if is_hotspot:
    print(f"  HOTSPOT: {HS_SSID} / {HS_PASS}")
else:
    print(f"  WIFI: {wifi_ssid}")
print(f"  http://{ip}:{PORT}")
print(f"  mem: {gc.mem_free()}")
print(f"{'='*40}\n  Ready!\n")


busy = False

while True:
    try:
        if not busy:
            led.value = True
            time.sleep(0.02)
            led.value = False

        cl, addr = srv.accept()

        rd = b""
        cl.settimeout(3)
        try:
            while True:
                buf = bytearray(1536)
                n = cl.recv_into(buf)
                if n == 0:
                    break
                rd += buf[:n]
                if n < 1536:
                    break
        except OSError:
            pass

        rt = rd.decode("utf-8")
        del rd
        gc.collect()

        fl = rt.split("\r\n")[0]
        pp = fl.split(" ")
        if len(pp) < 2:
            cl.close()
            continue

        meth = pp[0]
        path = pp[1]

        body = ""
        if "\r\n\r\n" in rt:
            body = rt.split("\r\n\r\n", 1)[1]
        del rt
        gc.collect()

        def resp(code, ct, b):
            r = "HTTP/1.1 " + code + "\r\nContent-Type: " + ct + "\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\nContent-Length: " + str(len(b)) + "\r\n\r\n" + b
            cl.send(r.encode())

        if meth == "OPTIONS":
            cl.send("HTTP/1.1 200 OK\r\nAccess-Control-Allow-Origin: *\r\nAccess-Control-Allow-Methods: POST,GET,OPTIONS\r\nAccess-Control-Allow-Headers: Content-Type\r\nContent-Length: 0\r\n\r\n".encode())
            cl.close()
            del body
            gc.collect()
            continue

        if meth == "GET" and (path == "/" or path == ""):
            pg = page_main()
            h = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\nContent-Length: " + str(len(pg)) + "\r\n\r\n"
            cl.send(h.encode())
            for i in range(0, len(pg), 1024):
                cl.send(pg[i:i+1024].encode())
            cl.close()
            del pg, body
            gc.collect()
            continue

        if meth == "GET" and path == "/settings":
            pg = page_settings()
            h = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\nContent-Length: " + str(len(pg)) + "\r\n\r\n"
            cl.send(h.encode())
            for i in range(0, len(pg), 1024):
                cl.send(pg[i:i+1024].encode())
            cl.close()
            del pg, body
            gc.collect()
            continue

        if meth == "GET" and path == "/status":
            resp("200 OK", "application/json", '{"status":"ready","ip":"' + ip + '","mem":' + str(gc.mem_free()) + '}')
            cl.close()
            del body
            gc.collect()
            continue

        if meth == "POST" and path == "/stop":
            stop = True
            resp("200 OK", "application/json", '{"status":"stopping"}')
            cl.close()
            print("  STOP")
            del body
            gc.collect()
            continue

        if meth == "POST" and path == "/type":
            txt = ""
            dms = 10
            first = False
            try:
                d = json.loads(body)
                txt = d.get("text", "")
                dms = d.get("delay_ms", 10)
                first = d.get("first_chunk", False)
                del d
            except Exception:
                txt = body.strip()
            del body
            gc.collect()

            if not txt:
                resp("400 Bad Request", "application/json", '{"error":"no text"}')
                cl.close()
                gc.collect()
                continue

            stop = False
            resp("200 OK", "application/json", '{"status":"typing","chars":' + str(len(txt)) + '}')
            cl.close()
            gc.collect()

            busy = True
            if first:
                blink(4, 0.25)
            c = type_text(txt, dms)
            del txt
            busy = False
            gc.collect()
            print(f"  {c}ch mem:{gc.mem_free()}")
            continue

        if meth == "POST" and path == "/random":
            dms = 50
            try:
                d = json.loads(body)
                dms = d.get("delay_ms", 50)
            except Exception:
                pass
            del body
            gc.collect()

            stop = False
            busy = True
            resp("200 OK", "application/json", '{"status":"random"}')
            cl.close()
            blink(4, 0.25)
            type_random(dms)
            busy = False
            gc.collect()
            continue

        if meth == "POST" and path == "/save_wifi":
            try:
                d = json.loads(body)
                ns = d.get("ssid", "")
                np = d.get("password", "")
                del body
                gc.collect()
                if ns:
                    save_wifi(ns, np)
                    resp("200 OK", "application/json", '{"status":"saved"}')
                    cl.close()
                    print(f"  WiFi: {ns}")
                    time.sleep(3)
                    microcontroller.reset()
            except Exception as e:
                print(f"  Err: {e}")
                resp("500 Error", "application/json", '{"error":"failed"}')
                cl.close()
            gc.collect()
            continue

        resp("404 Not Found", "application/json", '{"error":"not found"}')
        cl.close()
        del body
        gc.collect()

    except Exception as e:
        print(f"  Err: {e}")
        busy = False
        try:
            cl.close()
        except Exception:
            pass
        gc.collect()
        time.sleep(0.5)
