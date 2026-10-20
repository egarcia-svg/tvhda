import os, json, csv, io
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=10 * 1024 * 1024)

DATA_FILE = "huespedes.json"

def cargar_huespedes():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {
        "101": {"nombre": "García", "nombre_completo": "Familia García", "checkin": "2026-05-13", "checkout": "2026-05-14"},
        "102": {"nombre": "Newman", "nombre_completo": "Sr. Newman", "checkin": "", "checkout": ""},
        "201": {"nombre": "Givaudan", "nombre_completo": "Grupo Givaudan", "checkin": "", "checkout": ""},
        "202": {"nombre": "", "nombre_completo": "", "checkin": "", "checkout": ""},
    }

def guardar_huespedes(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

huespedes = cargar_huespedes()

TV_HAB_HTML = """
<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;600&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:100%;overflow:hidden;font-family:'Inter',sans-serif;background:#000}
.bg{position:absolute;inset:0;background:linear-gradient(rgba(0,0,0,.3), rgba(0,0,0,.6)), url('https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1920&q=80') center/cover}
.container{position:relative;z-index:2;width:100%;height:100%;display:flex;flex-direction:column;padding:3vh 3vw;color:#fff}
.header{display:flex;justify-content:space-between;align-items:center;padding-bottom:2vh;border-bottom:1px solid rgba(255,255,255,.2)}
.header h1{font-family:'Playfair Display',serif;font-weight:400;font-size:2.2vw}
.logo{font-weight:700;letter-spacing:2px;background:#fff;color:#000;padding:6px 14px;border-radius:4px;font-size:1.1vw}
.main{flex:1;display:grid;grid-template-columns:1.2fr .8fr;gap:2vw;padding-top:3vh}
.welcome-card{background:rgba(255,255,255,.92);color:#1a1a1a;border-radius:12px;padding:3vh 2vw;backdrop-filter:blur(10px)}
.welcome-card h2{font-family:'Playfair Display',serif;font-size:2.8vw;line-height:1.1;margin-bottom:1vh;color:#4a2c2a}
.welcome-card .sub{font-size:1.1vw;color:#666;margin-bottom:2vh}
.info-grid{display:grid;gap:1.5vh;margin-top:2vh}
.info-item{display:flex;align-items:center;gap:1vw;background:rgba(0,0,0,.05);padding:1.2vh 1vw;border-radius:8px}
.info-item .icon{font-size:1.8vw}
.info-item h4{font-size:1vw;font-weight:600}
.info-item p{font-size:.85vw;color:#555}
.right-col{display:flex;flex-direction:column;gap:2vh}
.card{background:rgba(255,255,255,.88);color:#1a1a1a;border-radius:12px;padding:2vh 1.5vw;backdrop-filter:blur(10px)}
.card h3{font-size:1.1vw;margin-bottom:1vh}
.qr{width:6vw;height:6vw;background:#000;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:.7vw;text-align:center}
.footer{margin-top:auto;padding-top:2vh;border-top:1px solid rgba(255,255,255,.2);display:flex;justify-content:space-between;font-size:.8vw;opacity:.7}
@media(max-width:900px){.main{grid-template-columns:1fr}.header h1{font-size:5vw}.welcome-card h2{font-size:7vw}.logo{font-size:3vw}}
</style>
</head><body>
<div class="bg"></div>
<div class="container">
  <div class="header">
    <h1 id="saludo">¿Qué tal <span id="nombre">Huésped</span>?</h1>
    <div class="logo">HACIENDA DE CORTES</div>
  </div>
  <div class="main">
    <div class="welcome-card">
      <div class="sub">Hotel & Spa Hacienda de Cortés • Cuernavaca, Morelos</div>
      <h2>Bienvenido,<br><span id="nombreCompleto">a su casa</span></h2>
      <p style="margin-top:1vh;color:#666;font-size:1vw">Nos da mucho gusto tenerle con nosotros.</p>
      <div class="info-grid">
        <div class="info-item"><div class="icon">📶</div><div><h4>Conéctate al WiFi</h4><p>Red: HACIENDA-CORTES • Contraseña: bienvenidos2026</p></div></div>
        <div class="info-item"><div class="icon">📱</div><div><h4>Habitación</h4><p>Habitación: <b id="roomLabel">101</b></p></div></div>
        <div class="info-item"><div class="icon">🔑</div><div><h4>Check-out</h4><p id="checkout">12:00 PM</p></div></div>
      </div>
    </div>
    <div class="right-col">
      <div class="card"><h3>🏨 Hotel Info</h3><p style="font-size:.9vw">Restaurante 7am-10pm<br>Alberca 8am-8pm<br>Spa previa cita</p></div>
      <div class="card"><h3>🍽️ ¿Tienes hambre?</h3><p style="font-size:.9vw">Room Service disponible</p><p style="font-size:.8vw;color:#8B0000;margin-top:1vh;font-weight:600">www.hotelhaciendadecortes.com.mx</p></div>
    </div>
  </div>
  <div class="footer"><span id="fecha"></span><span>Habitación <b id="roomFooter">101</b></span></div>
</div>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script>
const params=new URLSearchParams(location.search);
const room=params.get('hab')||params.get('tv')||params.get('room')||'101';
document.getElementById('roomLabel').textContent=room;
document.getElementById('roomFooter').textContent=room;
document.getElementById('fecha').textContent=new Date().toLocaleDateString('es-MX',{weekday:'long',day:'numeric',month:'long',year:'numeric'});
const socket=io();
function cargarDatos(){
  fetch('/api/huespedes').then(r=>r.json()).then(data=>{
    const h=data[room];
    if(h && h.nombre){
      document.getElementById('nombre').textContent=h.nombre;
      document.getElementById('nombreCompleto').textContent=h.nombre_completo || h.nombre;
      if(h.checkout) document.getElementById('checkout').textContent='Check-out: '+h.checkout;
    }
  });
}
socket.on('connect',()=>{socket.emit('join_tv',{tv:'hab_'+room});cargarDatos();});
socket.on('actualizar_hab',d=>{if(d.room===room||d.room==='all'){cargarDatos();}});
socket.on('nueva_imagen',d=>{if(d.image){document.body.innerHTML=`<img src="${d.image}" style="width:100vw;height:100vh;object-fit:cover">`;}});
document.body.addEventListener('dblclick',()=>document.documentElement.requestFullscreen());
cargarDatos();
setInterval(cargarDatos,30000);
</script>
</body></html>
"""

ADMIN_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin Habitaciones - Hacienda de Cortés</title>
<style>
body{font-family:system-ui,sans-serif;background:#f5f1eb;margin:0;padding:20px;color:#2c2c2c}
h1{font-family:serif;color:#4a2c2a}
.container{max-width:900px;margin:auto;background:#fff;padding:25px;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.08)}
table{width:100%;border-collapse:collapse;margin-top:20px}
th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}
th{background:#4a2c2a;color:#fff}
input{width:100%;padding:8px;border:1px solid #ddd;border-radius:6px}
button{padding:10px 16px;border:none;border-radius:8px;cursor:pointer;font-weight:600}
.btn-save{background:#4a2c2a;color:#fff}
.btn-add{background:#000;color:#fff;width:100%;margin-top:15px;padding:14px}
.btn-del{background:#c0392b;color:#fff;padding:6px 10px;font-size:12px}
.upload-box{border:2px dashed #4a2c2a;padding:20px;border-radius:12px;text-align:center;margin:20px 0;background:#fdf8f3}
.link{font-size:12px;color:#4a2c2a;word-break:break-all}
.status{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#000;color:#fff;padding:12px 20px;border-radius:30px;display:none}
.grid{ display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-top:15px}
.card{border:1px solid #eee;padding:12px;border-radius:10px}
</style>
</head><body>
<div class="container">
<h1>🏨 Hacienda de Cortés - Bienvenida Habitaciones</h1>
<p>Administra el nombre del huésped para cada TV. La TV se actualiza sola en 30 segundos.</p>

<div class="upload-box">
<h3>📄 Cargar archivo .txt o .csv</h3>
<p style="font-size:13px">Formato: <code>habitacion,nombre_completo,nombre_corto</code> ejemplo:<br><code>101,Familia Garcia,Garcia<br>102,Juan Newman,Newman<br>201,Grupo Givaudan,Givaudan</code></p>
<input type="file" id="fileInput" accept=".txt,.csv">
<button onclick="subirArchivo()" style="margin-top:10px;background:#4a2c2a;color:#fff">Cargar Archivo</button>
<textarea id="txtManual" rows="5" style="width:100%;margin-top:15px" placeholder="101,Familia Perez,Perez&#10;102,Newman,Newman"></textarea>
<button onclick="cargarTexto()" class="btn-add" style="background:#8B4513">Cargar desde texto de arriba</button>
</div>

<div class="grid">
<div class="card"><b>TV Habitación 101:</b><br><a class="link" target="_blank" href="/?hab=101">/ ?hab=101</a></div>
<div class="card"><b>TV Habitación 102:</b><br><a class="link" target="_blank" href="/?hab=102">/ ?hab=102</a></div>
<div class="card"><b>TV Recepción:</b><br><a class="link" target="_blank" href="/?tv=1">/ ?tv=1</a></div>
<div class="card"><b>Control Imágenes:</b><br><a class="link" href="/control">/control</a></div>
</div>

<table id="tabla"><thead><tr><th>Hab</th><th>Nombre Corto</th><th>Nombre Completo</th><th>Check-out</th><th>Ver TV</th><th></th></tr></thead><tbody></tbody></table>
<button class="btn-add" onclick="agregarFila()">+ Agregar Habitación</button>
<button class="btn-add" style="background:#4a2c2a" onclick="guardarTodo()">💾 GUARDAR TODO Y ACTUALIZAR TELES</button>

</div>
<div id="status" class="status"></div>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script>
const socket=io();
let datos={};
function showMsg(m){const s=document.getElementById('status');s.textContent=m;s.style.display='block';setTimeout(()=>s.style.display='none',3000);}
function cargarTabla(){
 fetch('/api/huespedes').then(r=>r.json()).then(d=>{
   datos=d;
   const tbody=document.querySelector('#tabla tbody');
   tbody.innerHTML='';
   Object.keys(d).sort().forEach(hab=>{
     const h=d[hab];
     tbody.innerHTML+=`<tr>
       <td><input value="${hab}" data-old="${hab}" class="hab"></td>
       <td><input value="${h.nombre||''}" class="nombre" placeholder="Ej: Newman"></td>
       <td><input value="${h.nombre_completo||''}" class="completo" placeholder="Ej: Sr. Newman"></td>
       <td><input value="${h.checkout||''}" class="checkout" placeholder="2026-05-14"></td>
       <td><a target="_blank" href="/?hab=${hab}">Ver TV ${hab}</a></td>
       <td><button class="btn-del" onclick="this.closest('tr').remove()">X</button></td>
     </tr>`;
   });
 });
}
function agregarFila(){
 const tbody=document.querySelector('#tabla tbody');
 tbody.innerHTML+=`<tr><td><input class="hab" placeholder="103"></td><td><input class="nombre" placeholder="Nombre corto"></td><td><input class="completo" placeholder="Nombre completo"></td><td><input class="checkout" placeholder="Check-out"></td><td>Guarda primero</td><td><button class="btn-del" onclick="this.closest('tr').remove()">X</button></td></tr>`;
}
function guardarTodo(){
 const filas=document.querySelectorAll('#tabla tbody tr');
 const nuevo={};
 filas.forEach(tr=>{
   const hab=tr.querySelector('.hab').value.trim();
   if(!hab) return;
   nuevo[hab]={
     nombre: tr.querySelector('.nombre').value.trim(),
     nombre_completo: tr.querySelector('.completo').value.trim(),
     checkout: tr.querySelector('.checkout').value.trim()
   };
 });
 fetch('/api/huespedes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(nuevo)})
 .then(r=>r.json()).then(()=>{showMsg('✅ Guardado y Teles Actualizadas');socket.emit('actualizar_hab',{room:'all'});cargarTabla();});
}
function subirArchivo(){
 const file=document.getElementById('fileInput').files[0];
 if(!file){showMsg('Elige un archivo');return;}
 const reader=new FileReader();
 reader.onload=e=>{procesarTexto(e.target.result);};
 reader.readAsText(file);
}
function cargarTexto(){const txt=document.getElementById('txtManual').value;procesarTexto(txt);}
function procesarTexto(texto){
 const lineas=texto.split('\\n');
 const nuevo={...datos};
 lineas.forEach(l=>{
   l=l.trim(); if(!l) return;
   const partes=l.split(',');
   if(partes.length>=2){
     const hab=partes[0].trim();
     const completo=partes[1].trim();
     const corto=partes[2]?partes[2].trim():completo.split(' ').pop();
     nuevo[hab]={nombre:corto,nombre_completo:completo,checkout:''};
   }
 });
 fetch('/api/huespedes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(nuevo)})
 .then(()=>{showMsg('Archivo cargado');cargarTabla();socket.emit('actualizar_hab',{room:'all'});});
}
cargarTabla();
</script>
</body></html>
"""

CONTROL_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>
body{font-family:sans-serif;padding:20px;text-align:center;max-width:500px;margin:auto}
.box{border:3px dashed #000;padding:30px;border-radius:20px;cursor:pointer}
img{max-width:100%;margin-top:15px;border-radius:10px}#info{font-size:12px;color:#666;margin-top:10px}
select{padding:12px 20px;font-size:18px;border-radius:10px;border:2px solid #000;margin:15px 0;width:100%}
button{padding:15px 30px;font-size:18px;background:#000;color:#fff;border-radius:10px;border:none;width:100%;margin-top:10px}
.tv-list{display:flex;gap:10px;margin:15px 0;flex-wrap:wrap}.tv-btn{flex:1;padding:12px;border:2px solid #000;border-radius:10px;background:#fff;cursor:pointer;font-weight:bold;min-width:80px}.tv-btn.active{background:#000;color:#fff}
</style></head><body>
<h2>Hacienda de Cortés - Imágenes</h2>
<div class="tv-list">
<div class="tv-btn active" data-tv="1">TV 1 Recepción</div>
<div class="tv-btn" data-tv="2">TV 2 Salón</div>
<div class="tv-btn" data-tv="all">TODAS</div>
</div>
<select id="tvSelect"><option value="1">TV 1 Recepción</option><option value="2">TV 2 Salón</option><option value="all">TODAS</option><option value="hab_101">Hab 101</option><option value="hab_102">Hab 102</option></select>
<div class="box" id="drop">Toca para elegir imagen</div><input type="file" id="f" accept="image/*" style="display:none"><img id="p"><div id="info"></div>
<button id="btn" style="display:none">ENVIAR A TV <span id="btnTv">1</span></button>
<p><a href="/admin">Ir a Admin Habitaciones →</a></p>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script><script>
const socket=io();let finalBase64="";let currentTv="1";const tvSelect=document.getElementById('tvSelect');const btnTv=document.getElementById('btnTv');const info=document.getElementById('info');
function setTv(tv){currentTv=tv;tvSelect.value=tv;btnTv.textContent=tv;document.querySelectorAll('.tv-btn').forEach(b=>b.classList.toggle('active',b.dataset.tv===tv));}
document.querySelectorAll('.tv-btn').forEach(b=>{b.onclick=()=>setTv(b.dataset.tv);});tvSelect.onchange=e=>setTv(e.target.value);
document.getElementById('drop').onclick=()=>document.getElementById('f').click();
document.getElementById('f').onchange=e=>{
const file=e.target.files[0];if(!file)return;info.textContent=`Comprimiendo...`;
const reader=new FileReader();reader.onload=ev=>{const img=new Image();img.onload=()=>{
const canvas=document.createElement('canvas');let w=img.width,h=img.height;const MAX=1920;
if(w>MAX||h>MAX){if(w>h){h*=MAX/w;w=MAX;}else{w*=MAX/h;h=MAX;}}
canvas.width=w;canvas.height=h;canvas.getContext('2d').drawImage(img,0,0,w,h);
finalBase64=canvas.toDataURL('image/jpeg',0.85);document.getElementById('p').src=finalBase64;
document.getElementById('btn').style.display='block';};img.src=ev.target.result;};reader.readAsDataURL(file);};
document.getElementById('btn').onclick=()=>{if(!finalBase64)return;document.getElementById('btn').textContent='ENVIANDO...';socket.emit('nueva_imagen',{tv:currentTv,image:finalBase64});};
socket.on('ok',d=>{document.getElementById('btn').textContent=`¡ENVIADO!`;setTimeout(()=>document.getElementById('btn').textContent=`ENVIAR A TV ${currentTv}`,2000);});
</script></body></html>
"""

@app.route('/')
def tv(): return TV_HAB_HTML

@app.route('/admin')
def admin(): return ADMIN_HTML

@app.route('/control')
def control(): return CONTROL_HTML

@app.route('/api/huespedes', methods=['GET'])
def api_get(): return jsonify(huespedes)

@app.route('/api/huespedes', methods=['POST'])
def api_post():
    global huespedes
    data = request.get_json()
    if not data: return jsonify({"error": "no data"}), 400
    huespedes = data
    guardar_huespedes(huespedes)
    return jsonify({"ok": True, "count": len(huespedes)})

@socketio.on('join_tv')
def handle_join(data):
    tv=str(data.get('tv','1'))
    join_room(tv)

@socketio.on('nueva_imagen')
def handle_img(data):
    tv=data.get('tv','1')
    image=data.get('image')
    if not image: return
    if tv=='all':
        socketio.emit('nueva_imagen',{'image':image})
        socketio.emit('ok',{'tv':'TODAS'})
    else:
        socketio.emit('nueva_imagen',{'image':image}, room=tv)
        socketio.emit('ok',{'tv':tv})

@socketio.on('actualizar_hab')
def handle_update(data):
    room=data.get('room','all')
    if room=='all':
        socketio.emit('actualizar_hab',{'room':'all'})
    else:
        socketio.emit('actualizar_hab',{'room':room}, room=f'hab_{room}')

if __name__ == '__main__':
    port=int(os.environ.get("PORT",10000))
    socketio.run(app,host='0.0.0.0',port=port)
