import asyncio
import json
import socket
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
import Quartz.CoreGraphics as CG

def post_key_combo(modifier_flag, keycode):
    down = CG.CGEventCreateKeyboardEvent(None, keycode, True)
    up = CG.CGEventCreateKeyboardEvent(None, keycode, False)
    if modifier_flag:
        CG.CGEventSetFlags(down, modifier_flag)
        CG.CGEventSetFlags(up, modifier_flag)
    CG.CGEventPost(CG.kCGHIDEventTap, down)
    CG.CGEventPost(CG.kCGHIDEventTap, up)

def trigger_mission_control():
    post_key_combo(CG.kCGEventFlagMaskControl, 126)

def trigger_app_expose():
    post_key_combo(CG.kCGEventFlagMaskControl, 125)

def trigger_switch_space_left():
    post_key_combo(CG.kCGEventFlagMaskControl, 123)

def trigger_switch_space_right():
    post_key_combo(CG.kCGEventFlagMaskControl, 124)

def trigger_show_desktop():
    post_key_combo(0, 103)

def quartz_move(dx, dy):
    loc = CG.CGEventGetLocation(CG.CGEventCreate(None))
    new_x = max(0.0, loc.x + dx)
    new_y = max(0.0, loc.y + dy)
    event = CG.CGEventCreateMouseEvent(
        None,
        CG.kCGEventMouseMoved,
        CG.CGPoint(new_x, new_y),
        CG.kCGMouseButtonLeft
    )
    CG.CGEventPost(CG.kCGHIDEventTap, event)

def quartz_click(button):
    loc = CG.CGEventGetLocation(CG.CGEventCreate(None))
    down_type = CG.kCGEventRightMouseDown if button == 1 else CG.kCGEventLeftMouseDown
    up_type = CG.kCGEventRightMouseUp if button == 1 else CG.kCGEventLeftMouseUp
    mouse_btn = CG.kCGMouseButtonRight if button == 1 else CG.kCGMouseButtonLeft
    
    down = CG.CGEventCreateMouseEvent(None, down_type, loc, mouse_btn)
    up = CG.CGEventCreateMouseEvent(None, up_type, loc, mouse_btn)
    CG.CGEventPost(CG.kCGHIDEventTap, down)
    CG.CGEventPost(CG.kCGHIDEventTap, up)

def quartz_scroll(dx, dy):
    event = CG.CGEventCreateScrollWheelEvent(None, 0, 2, int(dy), int(dx))
    CG.CGEventPost(CG.kCGHIDEventTap, event)

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Mac Trackpad UDP Ultra</title>
  <style>
    * { box-sizing: border-box; touch-action: none; user-select: none; -webkit-user-select: none; }
    body, html {
      margin: 0; padding: 0; width: 100%; height: 100%;
      background: #080808; color: #fff; font-family: -apple-system, sans-serif;
      overflow: hidden; display: flex; flex-direction: column;
    }
    #status-bar {
      padding: 10px 16px; font-size: 13px; background: #141414;
      display: flex; justify-content: space-between; align-items: center;
      border-bottom: 1px solid #222;
    }
    .connected { color: #00e676; font-weight: bold; }
    .disconnected { color: #ff5252; }
    #gesture-hint {
      position: absolute; top: 50px; left: 0; right: 0; text-align: center;
      font-size: 18px; font-weight: bold; color: #00e676; pointer-events: none;
      opacity: 0; transition: opacity 0.15s ease;
    }
    #pad {
      flex: 1; display: flex; align-items: center; justify-content: center;
      background: radial-gradient(circle at center, #1b1b1b 0%, #0d0d0d 100%);
      font-size: 13px; color: #666; text-align: center; line-height: 1.8;
      position: relative;
    }
    #quick-bar {
      display: flex; height: 44px; background: #121212; border-top: 1px solid #222;
    }
    .qbtn {
      flex: 1; background: transparent; border: none; border-right: 1px solid #202020;
      color: #999; font-size: 11px; font-weight: 700; text-transform: uppercase;
      -webkit-tap-highlight-color: transparent;
    }
    .qbtn:active { background: #333; color: #fff; }
    #buttons {
      display: flex; height: 75px; border-top: 1px solid #222;
    }
    .btn {
      flex: 1; display: flex; align-items: center; justify-content: center;
      background: #181818; font-size: 15px; font-weight: 700; color: #aaa;
      border: none; outline: none; -webkit-tap-highlight-color: transparent;
    }
    .btn:active { background: #333; color: #fff; }
    .btn-left { border-right: 1px solid #222; }
  </style>
</head>
<body>
  <div id="status-bar">
    <span>Trackpad WebRTC UDP</span>
    <span id="status" class="disconnected">Connecting...</span>
  </div>
  <div id="gesture-hint"></div>
  <div id="pad">
    <b>1 Jari:</b> Gerak & Tap Klik Kiri<br>
    <b>2 Jari:</b> Smooth Scroll & Tap Klik Kanan<br>
    <b>3/4 Jari Geser Atas:</b> Mission Control<br>
    <b>3/4 Jari Geser Bawah:</b> App Exposé<br>
    <b>3/4 Jari Geser Kiri/Kanan:</b> Pindah Desktop
  </div>
  <div id="quick-bar">
    <button class="qbtn" id="qb-mc">Mission Control</button>
    <button class="qbtn" id="qb-desk">Desktop</button>
    <button class="qbtn" id="qb-left">◀ Space</button>
    <button class="qbtn" id="qb-right">Space ▶</button>
  </div>
  <div id="buttons">
    <button class="btn btn-left" id="btn-left">LEFT CLICK</button>
    <button class="btn" id="btn-right">RIGHT CLICK</button>
  </div>

  <script>
    const statusEl = document.getElementById('status');
    const hintEl = document.getElementById('gesture-hint');
    const pad = document.getElementById('pad');

    function showHint(text) {
      hintEl.textContent = text;
      hintEl.style.opacity = '1';
      setTimeout(() => { hintEl.style.opacity = '0'; }, 700);
    }

    let pc = null;
    let dc = null;
    let ws = null;

    const buf = new ArrayBuffer(5);
    const view = new DataView(buf);

    function sendBinary(type, v1, v2 = 0) {
      view.setUint8(0, type);
      view.setInt16(1, v1);
      view.setInt16(3, v2);

      // Prefer WebRTC DataChannel (UDP Unreliable)
      if (dc && dc.readyState === 'open') {
        dc.send(buf);
      } else if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(buf);
      }
    }

    async function initWebRTC() {
      pc = new RTCPeerConnection({
        iceServers: []
      });

      // SCTP / UDP unordered & no retransmissions for lowest latency
      dc = pc.createDataChannel('mouse', {
        ordered: false,
        maxRetransmits: 0
      });
      dc.binaryType = 'arraybuffer';

      dc.onopen = () => {
        statusEl.textContent = 'UDP Direct (0ms Jitter)';
        statusEl.className = 'connected';
      };
      dc.onclose = () => {
        statusEl.textContent = 'Reconnecting...';
        statusEl.className = 'disconnected';
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const resp = await fetch('/offer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sdp: pc.localDescription.sdp, type: pc.localDescription.type })
      });
      const answer = await resp.json();
      await pc.setRemoteDescription(answer);
    }

    // Fallback WebSocket
    function connectWS() {
      const wsProto = location.protocol === 'https:' ? 'wss:' : 'ws:';
      ws = new WebSocket(`${wsProto}//${location.hostname}:8000/ws`);
      ws.binaryType = 'arraybuffer';
      ws.onopen = () => {
        if (!dc || dc.readyState !== 'open') {
          statusEl.textContent = 'Connected (TCP Fallback)';
          statusEl.className = 'connected';
        }
      };
      ws.onclose = () => setTimeout(connectWS, 1000);
    }

    initWebRTC().catch(() => connectWS());

    // Acceleration curve for mouse pointer
    function accelerate(delta) {
      const abs = Math.abs(delta);
      const sign = Math.sign(delta);
      if (abs < 2) return delta * 1.0;
      if (abs < 8) return sign * Math.pow(abs, 1.15) * 1.2;
      return sign * Math.pow(abs, 1.25) * 1.4;
    }

    let touchStartTime = 0;
    let maxFingers = 0;
    let startX = 0, startY = 0;
    let lastX = 0, lastY = 0;
    let gestureTriggered = false;
    let totalMoved = 0;

    function getCenter(touches) {
      let x = 0, y = 0;
      for (let i = 0; i < touches.length; i++) {
        x += touches[i].clientX;
        y += touches[i].clientY;
      }
      return { x: x / touches.length, y: y / touches.length };
    }

    // Use Pointer events with pointerrawupdate if supported
    pad.addEventListener('touchstart', (e) => {
      e.preventDefault();
      const count = e.touches.length;
      if (count > maxFingers) maxFingers = count;
      touchStartTime = performance.now();
      gestureTriggered = false;
      totalMoved = 0;

      const center = getCenter(e.touches);
      startX = center.x;
      startY = center.y;
      lastX = center.x;
      lastY = center.y;
    }, { passive: false });

    function handleMove(touches) {
      const count = touches.length;
      if (count > maxFingers) maxFingers = count;
      const center = getCenter(touches);

      if (maxFingers >= 3) {
        if (!gestureTriggered) {
          const deltaX = center.x - startX;
          const deltaY = center.y - startY;
          const THRESHOLD = 40;

          if (Math.abs(deltaY) > THRESHOLD || Math.abs(deltaX) > THRESHOLD) {
            gestureTriggered = true;
            if (Math.abs(deltaY) > Math.abs(deltaX)) {
              if (deltaY < 0) {
                showHint('Mission Control');
                sendBinary(4, 1);
              } else {
                showHint('App Exposé');
                sendBinary(4, 2);
              }
            } else {
              if (deltaX < 0) {
                showHint('Desktop Right ▶');
                sendBinary(4, 4);
              } else {
                showHint('◀ Desktop Left');
                sendBinary(4, 3);
              }
            }
          }
        }
      } else if (count === 1 && maxFingers === 1) {
        const rawDx = center.x - lastX;
        const rawDy = center.y - lastY;
        totalMoved += Math.abs(rawDx) + Math.abs(rawDy);
        lastX = center.x;
        lastY = center.y;

        const dx = accelerate(rawDx);
        const dy = accelerate(rawDy);
        sendBinary(1, Math.round(dx), Math.round(dy));
      } else if (count === 2 && maxFingers === 2) {
        const dx = (center.x - lastX) * 1.5;
        const dy = (center.y - lastY) * 1.5;
        totalMoved += Math.abs(dx) + Math.abs(dy);
        lastX = center.x;
        lastY = center.y;
        sendBinary(2, Math.round(dx), Math.round(dy));
      }
    }

    pad.addEventListener('touchmove', (e) => {
      e.preventDefault();
      handleMove(e.touches);
    }, { passive: false });

    pad.addEventListener('touchend', (e) => {
      e.preventDefault();
      if (e.touches.length === 0) {
        const elapsed = performance.now() - touchStartTime;
        if (!gestureTriggered && elapsed < 250 && totalMoved < 8) {
          if (maxFingers === 1) sendBinary(3, 0);
          else if (maxFingers === 2) sendBinary(3, 1);
        }
        maxFingers = 0;
        gestureTriggered = false;
      }
    }, { passive: false });

    document.getElementById('btn-left').addEventListener('pointerdown', (e) => { e.preventDefault(); sendBinary(3, 0); });
    document.getElementById('btn-right').addEventListener('pointerdown', (e) => { e.preventDefault(); sendBinary(3, 1); });
    document.getElementById('qb-mc').addEventListener('click', () => { showHint('Mission Control'); sendBinary(4, 1); });
    document.getElementById('qb-desk').addEventListener('click', () => { showHint('Show Desktop'); sendBinary(4, 5); });
    document.getElementById('qb-left').addEventListener('click', () => { showHint('◀ Desktop Left'); sendBinary(4, 3); });
    document.getElementById('qb-right').addEventListener('click', () => { showHint('Desktop Right ▶'); sendBinary(4, 4); });
  </script>
</body>
</html>
"""

def process_command(data):
    if len(data) >= 5:
        cmd = data[0]
        v1 = int.from_bytes(data[1:3], byteorder='big', signed=True)
        v2 = int.from_bytes(data[3:5], byteorder='big', signed=True)
        if cmd == 1:
            quartz_move(v1, v2)
        elif cmd == 2:
            quartz_scroll(v1, v2)
        elif cmd == 3:
            quartz_click(v1)
        elif cmd == 4:
            if v1 == 1:
                trigger_mission_control()
            elif v1 == 2:
                trigger_app_expose()
            elif v1 == 3:
                trigger_switch_space_left()
            elif v1 == 4:
                trigger_switch_space_right()
            elif v1 == 5:
                trigger_show_desktop()

async def handle_index(request):
    return web.Response(text=HTML_CONTENT, content_type='text/html')

pcs = set()

async def handle_offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, bytes):
                process_command(message)

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

async def handle_ws(request):
    transport = request.transport
    if transport:
        sock = transport.get_extra_info('socket')
        if sock:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    ws = web.WebSocketResponse(autoping=True, heartbeat=10.0)
    await ws.prepare(request)
    
    async for msg in ws:
        if msg.type == web.WSMsgType.BINARY:
            process_command(msg.data)
        elif msg.type == web.WSMsgType.ERROR:
            break
            
    return ws

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

async def run_server():
    ip = get_local_ip()
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_post('/offer', handle_offer)
    app.router.add_get('/ws', handle_ws)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print(f"\\n=== TRACKPAD WEBRTC UDP (ZERO JITTER) SIAP ===")
    print(f"Buka di Poco X7: http://{ip}:8000\\n")
    await asyncio.Future()

if __name__ == '__main__':
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass
