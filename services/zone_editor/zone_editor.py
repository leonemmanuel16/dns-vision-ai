"""
DNS Vision AI — Zone Editor + Line Counter + Heatmap Viewer
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import urllib.request
import base64
from pathlib import Path

CAMERA_IP = os.environ.get("CAMERA_IP", "192.168.8.26")
CAMERA_USER = os.environ.get("CAMERA_USER", "dns")
CAMERA_PASS = os.environ.get("CAMERA_PASS", "admin12345")
ZONES_FILE = os.environ.get("ZONES_FILE", "/home/manny/dns-vision-ai/config/zones.json")
HEATMAP_DIR = os.environ.get("HEATMAP_DIR", "/home/manny/dns-vision-ai/heatmaps")
PORT = int(os.environ.get("ZONE_EDITOR_PORT", "8888"))

Path(os.path.dirname(ZONES_FILE)).mkdir(parents=True, exist_ok=True)


def get_snapshot_base64():
    pm = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    pm.add_password(None, f"http://{CAMERA_IP}", CAMERA_USER, CAMERA_PASS)
    opener = urllib.request.build_opener(urllib.request.HTTPDigestAuthHandler(pm))
    resp = opener.open(f"http://{CAMERA_IP}/ISAPI/Streaming/channels/101/picture", timeout=5)
    return base64.b64encode(resp.read()).decode()


def get_heatmap_base64():
    path = f"{HEATMAP_DIR}/heatmap_latest.jpg"
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def load_zones():
    if os.path.exists(ZONES_FILE):
        with open(ZONES_FILE) as f:
            return json.load(f)
    return {"zones": [], "lines": []}


def save_zones(data):
    with open(ZONES_FILE, "w") as f:
        json.dump(data, f, indent=2)


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DNS Vision AI — Control Panel</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#ffffff; color:#333333; font-family:'Segoe UI',sans-serif; }
.header { background:#ffffff; padding:14px 24px; display:flex; align-items:center; justify-content:space-between; border-bottom:2px solid #3b82f6; }
.header h1 { font-size:18px; color:#3b82f6; }
.tabs { display:flex; gap:4px; }
.tab { padding:8px 16px; border:none; border-radius:6px 6px 0 0; cursor:pointer; font-size:13px; font-weight:600; background:#f1f5f9; color:#64748b; }
.tab.active { background:#3b82f6; color:white; }
.container { display:flex; gap:16px; padding:16px; height:calc(100vh - 100px); }
.canvas-panel { flex:1; position:relative; }
.sidebar { width:340px; background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:16px; overflow-y:auto; }
.canvas-container { position:relative; display:inline-block; border-radius:8px; overflow:hidden; border:1px solid #e2e8f0; }
.canvas-container img { display:block; max-width:100%; height:auto; }
.canvas-container canvas { position:absolute; top:0; left:0; cursor:crosshair; }
.btn { padding:6px 14px; border:none; border-radius:6px; cursor:pointer; font-size:13px; font-weight:600; transition:0.2s; }
.btn-primary { background:#3b82f6; color:white; }
.btn-primary:hover { background:#2563eb; }
.btn-danger { background:#ef4444; color:white; }
.btn-success { background:#10b981; color:white; }
.btn-warning { background:#f59e0b; color:black; }
.btn-purple { background:#8b5cf6; color:white; }
.btn-sm { padding:3px 8px; font-size:11px; }
.toolbar { display:flex; gap:6px; margin:10px 0; flex-wrap:wrap; align-items:center; }
.toolbar .status { color:#94a3b8; font-size:12px; margin-left:auto; }
.zone-card { background:#f8fafc; border-radius:8px; padding:10px; margin-bottom:8px; border-left:4px solid #3b82f6; border:1px solid #e2e8f0; border-left:4px solid #3b82f6; }
.zone-card h3 { font-size:13px; margin-bottom:4px; color:#1e293b; }
.zone-card .meta { font-size:11px; color:#94a3b8; }
.zone-card input,.zone-card select { background:#ffffff; border:1px solid #cbd5e1; color:#333333; padding:3px 6px; border-radius:4px; font-size:12px; width:100%; margin-bottom:3px; }
.zone-card label { font-size:11px; color:#64748b; display:block; margin-bottom:1px; }
.section-title { font-size:15px; font-weight:700; color:#1e293b; margin:12px 0 8px; padding-bottom:6px; border-bottom:1px solid #e2e8f0; }
.empty { color:#94a3b8; font-size:13px; text-align:center; padding:20px; }
.color-options { display:flex; gap:4px; margin:3px 0; }
.color-dot { width:18px; height:18px; border-radius:50%; cursor:pointer; border:2px solid transparent; }
.color-dot.selected { border-color:#333333; }
.checkbox-group { display:flex; flex-wrap:wrap; gap:4px; margin:3px 0; }
.checkbox-group label { font-size:11px; display:flex; align-items:center; gap:3px; color:#475569; cursor:pointer; }
.instructions { background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px; margin-bottom:12px; font-size:11px; color:#64748b; line-height:1.5; }
.instructions strong { color:#1e293b; }
.counter-display { background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px; text-align:center; margin:8px 0; }
.counter-display .count { font-size:36px; font-weight:800; color:#3b82f6; }
.counter-display .label { font-size:12px; color:#94a3b8; }
.heatmap-container { text-align:center; }
.heatmap-container img { max-width:100%; border-radius:8px; }
.panel { display:none; }
.panel.active { display:flex; }
</style>
</head>
<body>

<div class="header">
    <div style="display:flex;align-items:center;gap:12px;">
        <img src="/api/logo" style="height:36px;" alt="DNS" />
        <h1 style="margin:0;">🎯 DNS Vision AI</h1>
    </div>
    <div class="tabs">
        <button class="tab active" onclick="showPanel('zones')">📐 Zonas</button>
        <button class="tab" onclick="showPanel('lines')">📏 Líneas de Conteo</button>
        <button class="tab" onclick="showPanel('heatmap')">🔥 Mapa de Calor</button>
    </div>
    <button class="btn btn-primary" onclick="refreshSnapshot()">🔄 Actualizar</button>
</div>

<!-- ZONES PANEL -->
<div class="container panel active" id="panel-zones">
    <div class="canvas-panel">
        <div class="toolbar">
            <button class="btn btn-primary" onclick="startDrawing('zone')">✏️ Dibujar zona</button>
            <button class="btn btn-warning" onclick="undoPoint()">↩️ Deshacer</button>
            <button class="btn btn-danger" onclick="cancelDrawing()">✖ Cancelar</button>
            <button class="btn btn-success" onclick="finishZone()">✅ Cerrar zona</button>
            <span class="status" id="status-zones">Listo</span>
        </div>
        <div class="canvas-container">
            <img id="cameraImg-zones" src="" />
            <canvas id="canvas-zones"></canvas>
        </div>
    </div>
    <div class="sidebar">
        <div class="instructions">
            <strong>📐 Zonas de monitoreo</strong><br>
            Click "Dibujar zona" → marca puntos → "Cerrar zona"<br>
            Configura qué detectar en cada zona.
        </div>
        <div class="section-title">Zonas</div>
        <div id="zoneList"></div>
        <button class="btn btn-success" style="width:100%;margin-top:10px" onclick="saveAll()">💾 Guardar todo</button>
    </div>
</div>

<!-- LINES PANEL -->
<div class="container panel" id="panel-lines">
    <div class="canvas-panel">
        <div class="toolbar">
            <button class="btn btn-purple" onclick="startDrawing('line')">📏 Dibujar línea</button>
            <button class="btn btn-danger" onclick="cancelDrawing()">✖ Cancelar</button>
            <span class="status" id="status-lines">Click 2 puntos para crear línea de conteo</span>
        </div>
        <div class="canvas-container">
            <img id="cameraImg-lines" src="" />
            <canvas id="canvas-lines"></canvas>
        </div>
    </div>
    <div class="sidebar">
        <div class="instructions">
            <strong>📏 Líneas de conteo</strong><br>
            Dibuja una línea virtual. Cuando una persona la cruce, se cuenta.<br>
            Configura dirección: entrada, salida o ambas.
        </div>
        <div class="counter-display">
            <div class="count" id="totalCount">0</div>
            <div class="label">Personas contadas hoy</div>
        </div>
        <div class="section-title">Líneas</div>
        <div id="lineList"></div>
        <button class="btn btn-success" style="width:100%;margin-top:10px" onclick="saveAll()">💾 Guardar todo</button>
    </div>
</div>

<!-- HEATMAP PANEL -->
<div class="container panel" id="panel-heatmap">
    <div style="flex:1; padding:20px;">
        <div class="toolbar">
            <button class="btn btn-primary" onclick="refreshHeatmap()">🔄 Actualizar mapa de calor</button>
            <span class="status" id="status-heatmap">Click para cargar</span>
        </div>
        <div class="heatmap-container">
            <img id="heatmapImg" src="" style="max-width:100%; border-radius:8px;" />
            <p style="color:#94a3b8; margin-top:10px; font-size:13px;">
                El mapa de calor muestra las áreas con más movimiento.<br>
                🔴 Rojo = mucho movimiento | 🔵 Azul = poco movimiento<br>
                Se actualiza cada 5 minutos automáticamente.
            </p>
        </div>
    </div>
</div>

<script>
const COLORS = ['#3b82f6','#ef4444','#10b981','#f59e0b','#8b5cf6','#ec4899','#06b6d4','#f97316'];
const DETECT_TYPES = ['persona','persona_sin_casco','vehiculo','animal','cualquier_movimiento'];

let zones = [], lines = [];
let currentPoints = [];
let drawMode = null; // 'zone', 'line', null
let activePanel = 'zones';

window.onload = async () => {
    await loadData();
    refreshSnapshot();
    setupCanvas('zones');
    setupCanvas('lines');
};

function showPanel(name) {
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById('panel-' + name).classList.add('active');
    event.target.classList.add('active');
    activePanel = name;
    cancelDrawing();
    setTimeout(() => {
        resizeCanvas('zones');
        resizeCanvas('lines');
        drawAll();
    }, 50);
    if (name === 'heatmap') refreshHeatmap();
}

function setupCanvas(panel) {
    const canvas = document.getElementById('canvas-' + panel);
    const img = document.getElementById('cameraImg-' + panel);
    img.onload = () => { resizeCanvas(panel); drawAll(); };
    canvas.addEventListener('click', (e) => onCanvasClick(e, panel));
    window.addEventListener('resize', () => { resizeCanvas(panel); drawAll(); });
}

function resizeCanvas(panel) {
    const canvas = document.getElementById('canvas-' + panel);
    const img = document.getElementById('cameraImg-' + panel);
    if (!img.naturalWidth) return;
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;
}

function getScale(panel) {
    const img = document.getElementById('cameraImg-' + panel);
    if (!img.naturalWidth) return {sx:1, sy:1, w:1, h:1};
    return { sx: img.naturalWidth / img.clientWidth, sy: img.naturalHeight / img.clientHeight, w: img.naturalWidth, h: img.naturalHeight };
}

async function refreshSnapshot() {
    try {
        const resp = await fetch('/api/snapshot');
        const data = await resp.json();
        const src = 'data:image/jpeg;base64,' + data.image;
        document.getElementById('cameraImg-zones').src = src;
        document.getElementById('cameraImg-lines').src = src;
    } catch(e) {}
}

async function refreshHeatmap() {
    setStatus('heatmap', '⏳ Cargando...');
    try {
        const resp = await fetch('/api/heatmap');
        const data = await resp.json();
        if (data.image) {
            document.getElementById('heatmapImg').src = 'data:image/jpeg;base64,' + data.image;
            setStatus('heatmap', '✅ Mapa de calor actualizado');
        } else {
            setStatus('heatmap', '⚠️ Aún no hay mapa de calor. El generador necesita correr unos minutos.');
        }
    } catch(e) {
        setStatus('heatmap', '❌ Error: ' + e.message);
    }
}

async function loadData() {
    try {
        const resp = await fetch('/api/zones');
        const data = await resp.json();
        zones = data.zones || [];
        lines = data.lines || [];
        renderZoneList();
        renderLineList();
    } catch(e) {}
}

function startDrawing(mode) {
    drawMode = mode;
    currentPoints = [];
    if (mode === 'zone') setStatus('zones', '🎯 Click puntos del polígono...');
    if (mode === 'line') setStatus('lines', '📏 Click punto inicio de la línea...');
}

function onCanvasClick(e, panel) {
    if (!drawMode) return;
    const canvas = document.getElementById('canvas-' + panel);
    const rect = canvas.getBoundingClientRect();
    const s = getScale(panel);
    const x = ((e.clientX - rect.left) * s.sx) / s.w;
    const y = ((e.clientY - rect.top) * s.sy) / s.h;
    currentPoints.push({x, y});

    if (drawMode === 'line' && currentPoints.length === 2) {
        finishLine();
        return;
    }

    if (drawMode === 'zone') setStatus('zones', `📍 ${currentPoints.length} puntos. Click más o "Cerrar zona"`);
    if (drawMode === 'line') setStatus('lines', '📏 Click punto final de la línea...');
    drawAll();
}

function undoPoint() {
    if (currentPoints.length > 0) { currentPoints.pop(); drawAll(); }
}

function cancelDrawing() {
    drawMode = null;
    currentPoints = [];
    drawAll();
}

function finishZone() {
    if (currentPoints.length < 3) { setStatus('zones', '⚠️ Mínimo 3 puntos'); return; }
    zones.push({
        id: 'zone_' + Date.now(), name: 'Zona ' + (zones.length + 1),
        points: [...currentPoints], color: COLORS[zones.length % COLORS.length],
        detect: ['persona'], enabled: true
    });
    drawMode = null; currentPoints = [];
    renderZoneList(); drawAll();
    setStatus('zones', '✅ Zona creada');
}

function finishLine() {
    lines.push({
        id: 'line_' + Date.now(), name: 'Línea ' + (lines.length + 1),
        start: currentPoints[0], end: currentPoints[1],
        color: COLORS[(lines.length + 2) % COLORS.length],
        direction: 'both', count_in: 0, count_out: 0, enabled: true
    });
    drawMode = null; currentPoints = [];
    renderLineList(); drawAll();
    setStatus('lines', '✅ Línea de conteo creada');
}

function deleteZone(i) { zones.splice(i, 1); renderZoneList(); drawAll(); }
function deleteLine(i) { lines.splice(i, 1); renderLineList(); drawAll(); }

function drawAll() {
    drawOnCanvas('zones');
    drawOnCanvas('lines');
}

function drawOnCanvas(panel) {
    const canvas = document.getElementById('canvas-' + panel);
    const ctx = canvas.getContext('2d');
    const s = getScale(panel);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw zones
    zones.forEach(z => {
        if (!z.enabled) return;
        drawPolygon(ctx, z.points, z.color, z.name, s, 0.2);
    });

    // Draw lines
    lines.forEach(l => {
        if (!l.enabled) return;
        drawLine(ctx, l.start, l.end, l.color, l.name, l.direction, s);
    });

    // Draw current drawing
    if (currentPoints.length > 0 && drawMode === 'zone') {
        drawPolygon(ctx, currentPoints, '#ffffff', '', s, 0.15, true);
    }
    if (currentPoints.length === 1 && drawMode === 'line') {
        const p = currentPoints[0];
        ctx.beginPath();
        ctx.arc(p.x * canvas.width, p.y * canvas.height, 6, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
    }
}

function drawPolygon(ctx, points, color, label, s, alpha, isOpen) {
    const cw = ctx.canvas.width, ch = ctx.canvas.height;
    if (points.length < 2) {
        points.forEach(p => { ctx.beginPath(); ctx.arc(p.x*cw, p.y*ch, 5, 0, Math.PI*2); ctx.fillStyle=color; ctx.fill(); });
        return;
    }
    ctx.beginPath();
    ctx.moveTo(points[0].x*cw, points[0].y*ch);
    for (let i=1; i<points.length; i++) ctx.lineTo(points[i].x*cw, points[i].y*ch);
    if (!isOpen) ctx.closePath();
    ctx.fillStyle = color + Math.round(alpha*255).toString(16).padStart(2,'0');
    ctx.fill();
    ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke();
    points.forEach(p => { ctx.beginPath(); ctx.arc(p.x*cw, p.y*ch, 4, 0, Math.PI*2); ctx.fillStyle=color; ctx.fill(); });
    if (label) {
        const cx = points.reduce((s,p) => s + p.x*cw, 0) / points.length;
        const cy = points.reduce((s,p) => s + p.y*ch, 0) / points.length;
        ctx.font = 'bold 13px Segoe UI'; ctx.fillStyle = 'white';
        ctx.strokeStyle = 'rgba(0,0,0,0.8)'; ctx.lineWidth = 3;
        ctx.strokeText(label, cx-20, cy); ctx.fillText(label, cx-20, cy);
    }
}

function drawLine(ctx, start, end, color, label, direction, s) {
    const cw = ctx.canvas.width, ch = ctx.canvas.height;
    const sx = start.x*cw, sy = start.y*ch, ex = end.x*cw, ey = end.y*ch;

    // Line
    ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(ex, ey);
    ctx.strokeStyle = color; ctx.lineWidth = 3;
    ctx.setLineDash([8, 4]); ctx.stroke(); ctx.setLineDash([]);

    // Endpoints
    [start, end].forEach(p => { ctx.beginPath(); ctx.arc(p.x*cw, p.y*ch, 6, 0, Math.PI*2); ctx.fillStyle=color; ctx.fill(); ctx.strokeStyle='white'; ctx.lineWidth=2; ctx.stroke(); });

    // Direction arrows
    const mx = (sx+ex)/2, my = (sy+ey)/2;
    const angle = Math.atan2(ey-sy, ex-sx);
    const perpAngle = angle + Math.PI/2;

    if (direction === 'both' || direction === 'in') {
        drawArrow(ctx, mx, my, perpAngle, color);
    }
    if (direction === 'both' || direction === 'out') {
        drawArrow(ctx, mx, my, perpAngle + Math.PI, color);
    }

    // Label
    ctx.font = 'bold 12px Segoe UI'; ctx.fillStyle = 'white';
    ctx.strokeStyle = 'rgba(0,0,0,0.8)'; ctx.lineWidth = 3;
    ctx.strokeText(label, mx-20, my-10); ctx.fillText(label, mx-20, my-10);

    // Count badge
    ctx.font = 'bold 11px Segoe UI';
    ctx.strokeText('→ IN/OUT', mx-20, my+15); ctx.fillText('→ IN/OUT', mx-20, my+15);
}

function drawArrow(ctx, x, y, angle, color) {
    const len = 15;
    const ex = x + Math.cos(angle) * len;
    const ey = y + Math.sin(angle) * len;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(ex, ey);
    ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke();
    // Arrowhead
    const ha = 0.4, hl = 8;
    ctx.beginPath();
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - hl*Math.cos(angle-ha), ey - hl*Math.sin(angle-ha));
    ctx.lineTo(ex - hl*Math.cos(angle+ha), ey - hl*Math.sin(angle+ha));
    ctx.closePath(); ctx.fillStyle = color; ctx.fill();
}

function renderZoneList() {
    const list = document.getElementById('zoneList');
    if (!zones.length) { list.innerHTML = '<div class="empty">Sin zonas</div>'; return; }
    list.innerHTML = zones.map((z,i) => `
        <div class="zone-card" style="border-left-color:${z.color}">
            <label>Nombre:</label>
            <input value="${z.name}" onchange="zones[${i}].name=this.value;drawAll();" />
            <label>Detectar:</label>
            <div class="checkbox-group">
                ${DETECT_TYPES.map(dt => `<label><input type="checkbox" ${z.detect.includes(dt)?'checked':''} onchange="toggleDetect(${i},'${dt}',this.checked)"> ${dt.replace(/_/g,' ')}</label>`).join('')}
            </div>
            <label>Color:</label>
            <div class="color-options">
                ${COLORS.map(c => `<div class="color-dot ${z.color===c?'selected':''}" style="background:${c}" onclick="zones[${i}].color='${c}';renderZoneList();drawAll();"></div>`).join('')}
            </div>
            <label style="margin-top:4px;display:flex;align-items:center;gap:4px;color:#cbd5e1;cursor:pointer;">
                <input type="checkbox" ${z.enabled?'checked':''} onchange="zones[${i}].enabled=this.checked;drawAll();"> Activa
            </label>
            <div class="meta">📐 ${z.points.length} puntos</div>
            <button class="btn btn-danger btn-sm" style="margin-top:4px" onclick="deleteZone(${i})">🗑️</button>
        </div>
    `).join('');
}

function renderLineList() {
    const list = document.getElementById('lineList');
    if (!lines.length) { list.innerHTML = '<div class="empty">Sin líneas</div>'; return; }
    list.innerHTML = lines.map((l,i) => `
        <div class="zone-card" style="border-left-color:${l.color}">
            <label>Nombre:</label>
            <input value="${l.name}" onchange="lines[${i}].name=this.value;drawAll();" />
            <label>Dirección:</label>
            <select onchange="lines[${i}].direction=this.value;drawAll();">
                <option value="both" ${l.direction==='both'?'selected':''}>↔️ Ambas</option>
                <option value="in" ${l.direction==='in'?'selected':''}>→ Entrada</option>
                <option value="out" ${l.direction==='out'?'selected':''}>← Salida</option>
            </select>
            <label>Color:</label>
            <div class="color-options">
                ${COLORS.map(c => `<div class="color-dot ${l.color===c?'selected':''}" style="background:${c}" onclick="lines[${i}].color='${c}';renderLineList();drawAll();"></div>`).join('')}
            </div>
            <label style="margin-top:4px;display:flex;align-items:center;gap:4px;color:#cbd5e1;cursor:pointer;">
                <input type="checkbox" ${l.enabled?'checked':''} onchange="lines[${i}].enabled=this.checked;drawAll();"> Activa
            </label>
            <button class="btn btn-danger btn-sm" style="margin-top:4px" onclick="deleteLine(${i})">🗑️</button>
        </div>
    `).join('');
    // Update total count
    const total = lines.reduce((s,l) => s + (l.count_in||0) + (l.count_out||0), 0);
    document.getElementById('totalCount').textContent = total;
}

function toggleDetect(i, type, checked) {
    if (checked) { if (!zones[i].detect.includes(type)) zones[i].detect.push(type); }
    else { zones[i].detect = zones[i].detect.filter(d => d !== type); }
}

async function saveAll() {
    setStatus(activePanel, '💾 Guardando...');
    try {
        await fetch('/api/zones', {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({zones, lines})
        });
        setStatus(activePanel, '✅ Guardado!');
    } catch(e) { setStatus(activePanel, '❌ Error'); }
}

function setStatus(panel, msg) {
    const el = document.getElementById('status-' + panel);
    if (el) el.textContent = msg;
}
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path == '/':
            self.respond(200, 'text/html', HTML_PAGE.encode())
        elif self.path == '/api/logo':
            logo_path = '/home/manny/dns-vision-ai/dns_logo.png'
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    self.respond(200, 'image/png', f.read())
            else:
                self.respond(404, 'text/plain', b'Logo not found')
            return
        elif self.path == '/api/snapshot':
            try:
                self.send_json({"image": get_snapshot_base64()})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        elif self.path == '/api/heatmap':
            b64 = get_heatmap_base64()
            self.send_json({"image": b64} if b64 else {"image": None})
        elif self.path == '/api/zones':
            self.send_json(load_zones())
        else:
            self.respond(404, 'text/plain', b'Not found')

    def do_POST(self):
        if self.path == '/api/zones':
            data = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
            save_zones(data)
            n = len(data.get('zones', [])) + len(data.get('lines', []))
            self.send_json({"message": f"Guardado: {n} elementos"})

    def respond(self, code, ctype, body):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


if __name__ == "__main__":
    print(f"🎯 DNS Vision AI — Control Panel")
    print(f"📍 Cámara: {CAMERA_IP}")
    print(f"🌐 http://0.0.0.0:{PORT}")
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
