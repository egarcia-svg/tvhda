import os
from flask import Flask, request
from flask_socketio import SocketIO, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=10 * 1024 * 1024)

TV_HTML = """<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
html,body{margin:0;padding:0;background:#000;width:100%;height:100%;overflow:hidden}
#tv{width:100vw;height:100vh;object-fit:cover;display:block}
#msg{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#555;font-family:sans-serif;font-size:18px;text-align:center}
#label{position:absolute;top:10px;left:10px;color:#fff;background:rgba(0,0,0,.6);padding:6px 12px;border-radius:20px;font-family:sans-serif;font-size:14px}
</style>
</head><body>
<div id="msg">Esperando imagen...<br><small id="sub"></small></div>
<img id="tv" style="display:none">
<div id="label"></div>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script>
const params = new URLSearchParams(window.location.search);
const tvId = params.get('tv') || '1';
document.getElementById('label').textContent = 'TV ' + tvId;
document.getElementById('sub').textContent = 'Canal: TV ' + tvId;
const socket=io();
socket.on('connect',()=>{socket.emit('join_tv',{tv:tvId});});
const img=document.getElementById('tv');
const msg=document.getElementById('msg');
socket.on('nueva_imagen',d=>{
  msg.style.display='none';
  img.style.display='block';
  img.src=d.image;
});
let taps=0;
document.body.addEventListener('click',()=>{
  taps++; setTimeout(()=>{
    if(taps===2){
      img.style.objectFit = img.style.objectFit==='cover' ? 'contain' : 'cover';
    }
    if(taps===3) document.documentElement.requestFullscreen();
    taps=0;
  },300);
});
</script>
</body></html>"""

CONTROL_HTML = """<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:sans-serif;padding:20px;text-align:center;max-width:500px;margin:auto}
.box{border:3px dashed #000;padding:30px;border-radius:20px;cursor:pointer}
img{max-width:100%;margin-top:15px;border-radius:10px}
#info{font-size:12px;color:#666;margin-top:10px}
select{padding:12px 20px;font-size:18px;border-radius:10px;border:2px solid #000;margin:15px 0;width:100%}
button{padding:15px 30px;font-size:18px;background:#000;color:#fff;border-radius:10px;border:none;width:100%;margin-top:10px}
.tv-list{display:flex;gap:10px;margin:15px 0}
.tv-btn{flex:1;padding:12px;border:2px solid #000;border-radius:10px;background:#fff;cursor:pointer;font-weight:bold}
.tv-btn.active{background:#000;color:#fff}
</style>
</head><body>
<h2>Enviar a Teles - Hacienda de Cortés</h2>

<div class="tv-list">
  <div class="tv-btn active" data-tv="1">TV 1<br><small>Recepción</small></div>
  <div class="tv-btn" data-tv="2">TV 2<br><small>Salón</small></div>
  <div class="tv-btn" data-tv="3">TV 3</div>
</div>
<select id="tvSelect">
  <option value="1">TV 1 - Recepción</option>
  <option value="2">TV 2 - Salón Mario</option>
  <option value="3">TV 3</option>
  <option value="4">TV 4</option>
  <option value="5">TV 5</option>
  <option value="all">TODAS LAS TELES</option>
</select>

<div class="box" id="drop">Toca para elegir imagen</div>
<input type="file" id="f" accept="image/*" style="display:none">
<img id="p"><div id="info"></div>
<button id="btn" style="display:none">ENVIAR A TV <span id="btnTv">1</span></button>

<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<script>
const socket=io();
let finalBase64="";
let currentTv="1";
const tvSelect=document.getElementById('tvSelect');
const btnTv=document.getElementById('btnTv');
const info=document.getElementById('info');

function setTv(tv){
  currentTv=tv;
  tvSelect.value=tv;
  btnTv.textContent=tv==='all'?'TODAS':tv;
  document.querySelectorAll('.tv-btn').forEach(b=>b.classList.toggle('active', b.dataset.tv===tv));
}
document.querySelectorAll('.tv-btn').forEach(b=>{
  b.onclick=()=>setTv(b.dataset.tv);
});
tvSelect.onchange=e=>setTv(e.target.value);

document.getElementById('drop').onclick=()=>document.getElementById('f').click();
document.getElementById('f').onchange=e=>{
  const file=e.target.files[0]; if(!file)return;
  info.textContent=`Comprimiendo ${(file.size/1024).toFixed(0)}KB...`;
  const reader=new FileReader();
  reader.onload=ev=>{
    const img=new Image();
    img.onload=()=>{
      const canvas=document.createElement('canvas');
      let w=img.width,h=img.height;
      const MAX=1920;
      if(w>MAX||h>MAX){if(w>h){h*=MAX/w;w=MAX;}else{w*=MAX/h;h=MAX;}}
      canvas.width=w;canvas.height=h;
      canvas.getContext('2d').drawImage(img,0,0,w,h);
      finalBase64=canvas.toDataURL('image/jpeg',0.85);
      document.getElementById('p').src=finalBase64;
      document.getElementById('btn').style.display='block';
      info.textContent=`Listo: ${(finalBase64.length*0.75/1024).toFixed(0)}KB -> TV ${currentTv}`;
    };
    img.src=ev.target.result;
  };
  reader.readAsDataURL(file);
};

document.getElementById('btn').onclick=()=>{
  if(!finalBase64)return;
  document.getElementById('btn').textContent='ENVIANDO...';
  socket.emit('nueva_imagen',{tv:currentTv,image:finalBase64});
};
socket.on('ok',d=>{
  document.getElementById('btn').textContent=`¡ENVIADO A TV ${d.tv}!`;
  setTimeout(()=>document.getElementById('btn').textContent=`ENVIAR A TV ${currentTv}`,2000);
});
</script>
</body></html>"""

@app.route('/')
def tv():
    return TV_HTML

@app.route('/control')
def control():
    return CONTROL_HTML

@socketio.on('join_tv')
def handle_join(data):
    tv = str(data.get('tv','1'))
    join_room(tv)
    print(f"TV {tv} conectada")

@socketio.on('nueva_imagen')
def handle_img(data):
    tv = data.get('tv','1')
    image = data.get('image')
    if not image:
        return
    if tv == 'all':
        # enviar a todas
        socketio.emit('nueva_imagen', {'image': image})
        socketio.emit('ok', {'tv': 'TODAS'})
    else:
        socketio.emit('nueva_imagen', {'image': image}, room=tv)
        socketio.emit('ok', {'tv': tv}, room=tv)
        # tambien confirmar al control
        socketio.emit('ok', {'tv': tv})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port)
