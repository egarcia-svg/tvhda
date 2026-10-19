import os
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=10 * 2048 * 2048)

TV_HTML = """<!DOCTYPE html><html><head><style>body{margin:0;background:#000;height:100vh;display:flex;align-items:center;justify-content:center}img{max-width:100vw;max-height:100vh;object-fit:contain}#msg{color:#fff;font-family:sans-serif;opacity:.3}</style></head><body><div id="msg">Esperando imagen...</div><img id="tv"><script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script><script>const socket=io();const img=document.getElementById('tv');const msg=document.getElementById('msg');socket.on('nueva_imagen',d=>{msg.style.display='none';img.src=d;});document.body.ondblclick=()=>document.documentElement.requestFullscreen();</script></body></html>"""

CONTROL_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{font-family:sans-serif;padding:20px;text-align:center}.box{border:3px dashed #000;padding:40px;border-radius:20px}img{max-width:100%;margin-top:20px}#info{font-size:12px;color:#666;margin-top:10px}</style></head><body><h2>Enviar a TV</h2><div class="box" id="drop">Toca para elegir imagen</div><input type="file" id="f" accept="image/*" style="display:none"><img id="p"><div id="info"></div><br><button id="btn" style="display:none;padding:15px 30px;font-size:20px;background:#000;color:#fff;border-radius:10px">ENVIAR A TV</button><script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script><script>const socket=io();let finalBase64="";const info=document.getElementById('info');document.getElementById('drop').onclick=()=>document.getElementById('f').click();document.getElementById('f').onchange=e=>{const file=e.target.files[0];if(!file)return;info.textContent=`Original: ${(file.size/1024/1024).toFixed(2)} MB - Comprimiendo...`;const reader=new FileReader();reader.onload=ev=>{const img=new Image();img.onload=()=>{const canvas=document.createElement('canvas');let w=img.width,h=img.height;const MAX=1920;if(w>MAX||h>MAX){if(w>h){h*=MAX/w;w=MAX;}else{w*=MAX/h;h=MAX;}}canvas.width=w;canvas.height=h;canvas.getContext('2d').drawImage(img,0,0,w,h);finalBase64=canvas.toDataURL('image/jpeg',0.8);document.getElementById('p').src=finalBase64;document.getElementById('btn').style.display='inline-block';info.textContent=`Original: ${(file.size/1024).toFixed(0)}KB -> Enviando: ${(finalBase64.length*0.75/1024).toFixed(0)}KB`;};img.src=ev.target.result;};reader.readAsDataURL(file);};document.getElementById('btn').onclick=()=>{if(!finalBase64)return;document.getElementById('btn').textContent='ENVIANDO...';socket.emit('nueva_imagen',finalBase64);};socket.on('ok',()=>{document.getElementById('btn').textContent='¡ENVIADO!';setTimeout(()=>document.getElementById('btn').textContent='ENVIAR A TV',2000);});</script></body></html>"""

@app.route('/')
def tv():
    return TV_HTML

@app.route('/control')
def control():
    return CONTROL_HTML

@socketio.on('nueva_imagen')
def handle_img(data):
    socketio.emit('nueva_imagen', data)
    socketio.emit('ok')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port)
