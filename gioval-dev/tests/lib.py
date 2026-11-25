"""Infraestructura de pruebas de Mundo Gioval: servidor local, navegador móvil y ayudas para jugar sesiones."""
import json, os, re, sys, threading, time, subprocess
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEV = HERE.parent
ROOT = DEV.parent
APP = ROOT / "gioval"
REF = HERE / "referencia" / "index_v5.html"
SALIDA = HERE / "salida"
CHROME = "/usr/bin/google-chrome"

ESTADO = {"version_override": None, "espacio_override": None}   # el servidor puede servir otra js/version.js (prueba de aviso de versión)


class Handler(SimpleHTTPRequestHandler):
    raiz = None
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(self.raiz or APP), **k)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/legacy/", "/legacy/index.html"):          # la versión publicada antes del refactor (referencia)
            data = REF.read_bytes()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
        if p == "/js/version.js" and (ESTADO["version_override"] or ESTADO["espacio_override"] is not None):
            data = ('self.GIOVAL_VERSION = "%s";\nself.GIOVAL_ESPACIO = "%s";\n' % (ESTADO["version_override"] or re.search(r'GIOVAL_VERSION = "([^"]+)"', (APP / "js/version.js").read_text()).group(1), ESTADO["espacio_override"] or "")).encode()
            self.send_response(200); self.send_header("Content-Type", "application/javascript"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
        return super().do_GET()


def servidor(puerto=0, raiz=None):
    """raiz: carpeta a servir (por defecto gioval/). Con otra raíz se prueban copias modificadas de la app."""
    H = type("H", (Handler,), {"raiz": raiz}) if raiz else Handler
    s = ThreadingHTTPServer(("127.0.0.1", puerto), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, "http://127.0.0.1:%d" % s.server_address[1]


SEMILLA_JS = """
(function(){ var a=(%d)>>>0; Math.random=function(){ a|=0; a=a+0x6D2B79F5|0; var t=Math.imul(a^a>>>15,1|a); t=t+Math.imul(t^t>>>7,61|t)^t; return((t^t>>>14)>>>0)/4294967296; }; })();
"""
RELOJ_JS = """
(function(){ var rn=Date.now.bind(Date); window.__OFF=0; Date.now=function(){ return rn()+window.__OFF; }; })();
"""
RAPIDO_JS = """
(function(){ var st=window.setTimeout; window.setTimeout=function(f,t){ var r=[].slice.call(arguments,2); return st.apply(window,[f,(t||0)/6].concat(r)); }; })();
"""
CONGELAR_CSS = "*{animation:none!important;transition:none!important}"


class Banco:
    """Un navegador con contextos móviles (emulación real: toque, pixel ratio, user agent)."""
    VISTAS = {"pixel7": None, "360x700": {"width": 360, "height": 700}, "740x330": {"width": 740, "height": 330}}

    def __init__(self, pw, extra_args=None):
        self.pw = pw
        self.browser = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"] + (extra_args or []))
        self.errores = []
        self.paginas = []

    def contexto(self, vista="pixel7", sw=False, **kw):
        if vista == "pixel7":
            d = dict(self.pw.devices["Pixel 7"])
        else:
            v = self.VISTAS[vista]
            d = dict(viewport=v, device_scale_factor=2, is_mobile=True, has_touch=True,
                     user_agent="Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Mobile Safari/537.36")
        d.update(kw)
        d["service_workers"] = "allow" if sw else "block"
        return self.browser.new_context(**d)

    def cerrar(self):
        self.browser.close()


def abrir(ctx, url, store=None, semilla=None, rapido=True, errores=None, reloj=True, extra_init=None, esperar=True, congelar=False):
    """Abre la app. store = dict que se siembra en localStorage SOLO la primera vez (sobrevive a recargas)."""
    pg = ctx.new_page()
    if errores is not None:
        def _c(m):
            if m.type in ("error", "warning") and "favicon" not in m.text and "404" not in m.text and "blocked by Playwright" not in m.text and "navigator.vibrate" not in m.text and "AudioContext was not allowed" not in m.text:
                errores.append("[consola %s] %s" % (m.type, m.text))
        pg.on("console", _c)
        pg.on("pageerror", lambda e: errores.append("[pageerror] " + str(e)))
    if store is not None:
        txt = store if isinstance(store, str) else json.dumps(store)
        pg.add_init_script("if(!sessionStorage.getItem('__sembrado')){ sessionStorage.setItem('__sembrado','1'); localStorage.setItem('gioval',%s); }" % json.dumps(txt))
    if semilla is not None:
        pg.add_init_script(SEMILLA_JS % semilla)
    if reloj:
        pg.add_init_script(RELOJ_JS)
    if rapido:
        pg.add_init_script(RAPIDO_JS)
    if extra_init:
        pg.add_init_script(extra_init)
    pg.goto(url)
    if esperar:
        esperar_listo(pg)
    if congelar:
        pg.add_style_tag(content=CONGELAR_CSS)
    return pg


def esperar_listo(pg):
    pg.wait_for_function("(typeof Gioval==='undefined') ? !!document.getElementById('profiles') : Gioval.listo===true", timeout=15000)


def instalar_speak(pg):
    """window.speak reemplazado: no habla, devuelve enseguida y registra los textos (__LOG hablado, __BUB globito)."""
    pg.evaluate("""(()=>{ window.__LOG=[]; window.__BUB=[]; var sb=window.setBubble;
      window.setBubble=function(t){ window.__BUB.push(t); sb(t); };
      window.speak=function(t){ window.__LOG.push(t); window.setBubble(t); return Promise.resolve(); }; })()""")


def entrar(pg, nombre):
    pg.click(".song:has-text('%s')" % nombre)
    pg.wait_for_timeout(120)


def ir_mapa(pg):
    pg.evaluate("goMap()"); pg.wait_for_timeout(80)


def abrir_isla(pg, nombre):
    ir_mapa(pg)
    pg.click(".island:has-text('%s')" % nombre); pg.wait_for_timeout(120)


def tarjeta(pg, texto):
    pg.click("#musicMenu .island:has-text('%s'), #menuIslaItems .island:has-text('%s')" % (texto, texto)); pg.wait_for_timeout(250)


JS_PIANO = "S.mode==='play'&&!S.tap&&S.chunks&&S.chunks[S.ci]&&S.chunks[S.ci][S.ni]?S.chunks[S.ci][S.ni].midi:0"
JS_TOQUES = "(S.tap&&S.mode==='play'&&S.tap.v)?(function(){var T=S.tap,w=T.it.seq[T.pos];return {w:w,vals:T.v.opts.map(function(o){return o.val}),used:Array.from(T.used),dead:Array.from(T.dead),miss:T.miss,len:T.it.seq.length,run:T.run,pos:T.pos,ids:T.v.opts.map(function(o,i){return o.id!=null?o.id:i})};})():null"


def jugar(pg, cada_error=0, limite=200, perfecto=False):
    """Juega la sesión/chequeo en curso hasta que aparece el cartel final (o el de tope diario).
    cada_error: cada N decisiones elige una respuesta equivocada (0 = nunca). Devuelve 'fin', 'tope' o 'limite'."""
    n = 0; dec = 0
    while n < limite:
        pg.wait_for_timeout(35)
        if pg.evaluate("document.getElementById('finish').classList.contains('show')"): return "fin"
        if pg.evaluate("document.getElementById('capBox').classList.contains('show')"): return "tope"
        m = pg.evaluate(JS_PIANO)
        if m:
            dec += 1
            if cada_error and dec % cada_error == 0 and not perfecto:
                pg.dispatch_event(".key[data-m='%d']" % (60 if m != 60 else 62), "pointerdown")
                pg.wait_for_timeout(420)   # la app ignora toques durante 300 ms después de un error (reloj real)
            else:
                pg.evaluate("window.__ref=[S.ci,S.ni,S.mode,S.run]")
                pg.dispatch_event(".key[data-m='%d']" % m, "pointerdown")
                try:
                    pg.wait_for_function("(function(){var r=window.__ref; return S.ci!==r[0]||S.ni!==r[1]||S.mode!==r[2]||S.run!==r[3];})()", timeout=2500, polling=15)
                except Exception: pass
            n += 1; continue
        t = pg.evaluate(JS_TOQUES)
        if t:
            dec += 1
            ok = [i for i, v in enumerate(t["vals"]) if v == t["w"] and t["ids"][i] not in t["used"] and v not in t["dead"]]
            mal = [i for i, v in enumerate(t["vals"]) if v != t["w"] and t["ids"][i] not in t["used"] and v not in t["dead"]]
            clic = None
            if cada_error and dec % cada_error == 0 and t["len"] == 1 and t["miss"] == 0 and mal and not perfecto: clic = mal[0]
            elif ok: clic = ok[0]
            if clic is not None:
                pg.evaluate("(()=>{var T=S.tap; window.__ref=[T.it,T.pos,T.miss,T.used.size,T.dead.size]; })()")
                pg.click(".opt[data-i='%d']" % clic, force=True)
                try:   # esperar a que el juego procese el toque (determinismo)
                    pg.wait_for_function("(function(){var T=S.tap,r=window.__ref; return !T||S.mode!=='play'||T.it!==r[0]||T.pos!==r[1]||T.miss!==r[2]||T.used.size!==r[3]||T.dead.size!==r[4];})()", timeout=2500, polling=15)
                except Exception: pass
            n += 1
    return "limite"


def cerrar_fin(pg, boton="#btnFinHome"):
    pg.click(boton); pg.wait_for_timeout(120)


def foto(pg, nombre):
    SALIDA.mkdir(parents=True, exist_ok=True)
    pg.wait_for_timeout(250)
    p = SALIDA / (nombre + ".png"); pg.screenshot(path=str(p)); return p.name


def abrir_panel(pg):
    pg.click("#btnGear"); pg.wait_for_timeout(100)
    pg.fill("#gateIn", str(pg.evaluate("S.gateAns"))); pg.click("#gateOk"); pg.wait_for_timeout(150)


def snapshot(pg):
    """Estado comparable del progreso (sin marcas de tiempo)."""
    return pg.evaluate("""(()=>{ var sk={}; Object.keys(store.sk).sort().forEach(function(k){ var v=store.sk[k]; sk[k]=[v.mast,v.att,+v.score.toFixed(6),v.box,v.lvl,JSON.stringify(v.rec)]; });
      var log={}; Object.keys(store.log).forEach(function(k){ log[k]=store.log[k].map(function(e){ return [e.s,e.o,e.f,e.k].join(); }); });
      return {sk:sk, log:log, days:store.days, stars:store.stars, checks:store.checks, profiles:store.profiles, limit:store.limit}; })()""")


# ---------------------------------------------------------------- Isla Ritmo: jugador sintético
JS_JUGADOR = """
window.__jug=(function(){
  var J={enviados:[]};
  function emitir(t,fuente,fuerza){ var d=t-performance.now(); setTimeout(function(){ Gioval.entrada.emitir({tipo:'golpe',t:t,fuerza:fuerza==null?.8:fuerza,fuente:fuente||'toque'}); },Math.max(0,d)); J.enviados.push(t); }
  /* o: {error:'falta'|'extra'|'adelantado'|'atrasado'|null, sesgo:ms, jit:ms, fuente:'mic'|'toque', libre:[beats]} */
  J.responder=function(T,o){
    o=o||{}; var sesgo=o.sesgo||0, jit=o.jit||0, ts=[], i;
    function j(){ return jit?(Math.random()*2-1)*jit:0; }
    if(T.modo==='ioi'){ var a=performance.now()+T.beatMs*.4; for(i=0;i<T.rel.length;i++) ts.push(a+T.rel[i]+j()); }
    else if(T.modo==='grid'){ for(i=0;i<T.esperados.length;i++) ts.push(T.esperados[i]+sesgo+j()); }
    else { var bs=o.libre||[0,1,1.5,2.5]; for(i=0;i<bs.length;i++) ts.push(T.t0+bs[i]*T.beatMs+sesgo+j()); }
    J.plan=ts.slice();
    if(o.error==='falta') ts.pop();
    else if(o.error==='extra'&&ts.length>2) ts.splice(2,0,(ts[1]+ts[2])/2+ (T.W||50)*0.1);
    else if(o.error==='adelantado'&&ts.length>2) ts[2]-=T.W*2.4;
    else if(o.error==='atrasado'&&ts.length>1) ts[ts.length-1]+=T.W*2.4;
    ts.forEach(function(t){ emitir(t,o.fuente); });
    return ts.length;
  };
  return J;
})();
"""


def jugar_ritmo(pg, errores=None, limite_s=300, opciones=None, quieto=False):
    """Juega la sesión/chequeo de la isla Ritmo con un 'niño' sintético (eventos 'golpe' con tiempos exactos).
    errores: lista cíclica de errores a inyectar por turno (None = perfecto). Devuelve 'fin', 'tope' o 'limite'."""
    pg.evaluate(JS_JUGADOR)
    visto = -1; t0 = time.time(); n = 0; comp_id = -1; fichas = ["T", "TT", "S", "T"]
    opciones = dict(opciones or {})
    while time.time() - t0 < limite_s:
        pg.wait_for_timeout(40)
        if pg.evaluate("document.getElementById('finish').classList.contains('show')"): return "fin"
        if pg.evaluate("document.getElementById('capBox').classList.contains('show')"): return "tope"
        st = pg.evaluate("(function(){var R=Gioval.ritmo; return {f:R.fase,t:R.turno?R.turno.id:0,c:R.compose?R.compose.slots.length:-1,ci:R.compose?R.compose.id:0};})()")
        if st["c"] >= 0 and st["c"] < 4:
            pg.evaluate("document.querySelector('#rtPal [data-k=%s]').click()" % fichas[st["c"]]); pg.wait_for_timeout(30); continue
        if st["f"] == "turno" and st["t"] != visto:
            visto = st["t"]
            o = dict(opciones)
            if errores:
                e = errores[n % len(errores)]; o["error"] = e
            n += 1
            pg.evaluate("(function(o){ window.__jug.responder(Gioval.ritmo.turno,o); })(%s)" % json.dumps(o))
    return "limite"


# ---------------------------------------------------------------- audio sintético de golpes (para el detector de ritmo)
def _np():
    import numpy as np
    return np


SR_AUDIO = 48000


def golpe_sintetico(tipo, amp, rng, sr=SR_AUDIO):
    """Un golpe simulado (decaimiento rápido). tipo: click, palma (ráfaga de ruido), tambor, cajon, pandereta."""
    np = _np(); n = int(sr * 0.3); t = np.arange(n) / sr
    ruido = rng.normal(0, 1, n)
    if tipo == "click": return amp * np.exp(-t / 0.004) * np.sin(2 * np.pi * 1800 * t)
    if tipo == "palma": return amp * np.exp(-t / 0.015) * ruido
    if tipo == "tambor": return amp * np.exp(-t / 0.08) * (np.sin(2 * np.pi * 180 * t) + 0.3 * ruido)
    if tipo == "cajon": return amp * (np.exp(-t / 0.06) * np.sin(2 * np.pi * 110 * t * (1 + 0.3 * np.exp(-t / 0.02))) + 0.5 * np.exp(-t / 0.012) * ruido)
    if tipo == "pandereta": return amp * np.exp(-t / 0.10) * ruido * (0.5 + 0.5 * np.sin(2 * np.pi * 5200 * t))
    raise ValueError(tipo)


def senal_golpes(dur_s, golpes_ms, tipo="palma", ruido=0.004, semilla=1, amps=None, sr=SR_AUDIO, zumbido=0.0, extra=None):
    """Audio mono float32 con ruido de fondo (+ zumbido de 50 Hz opcional) y golpes en los instantes indicados (ms)."""
    np = _np(); rng = np.random.default_rng(semilla); n = int(dur_s * sr)
    x = rng.normal(0, ruido, n).astype(np.float64)
    if zumbido: x += zumbido * np.sin(2 * np.pi * 50 * np.arange(n) / sr)
    for k, t in enumerate(golpes_ms):
        a = (amps[k] if amps else 0.45 * (0.7 + 0.3 * ((k * 7) % 3) / 2)); g = golpe_sintetico(tipo, a, rng, sr); i0 = int(round(t * sr / 1000))
        if i0 < n: m = min(len(g), n - i0); x[i0:i0 + m] += g[:m]
    if extra is not None: x = extra(x, rng, sr)
    return np.clip(x, -1, 1).astype(np.float32)


def a_wav(x, ruta, sr=SR_AUDIO):
    import wave
    np = _np(); d = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(d.tobytes())
    return ruta


def a_b64(x):
    import base64
    np = _np(); return base64.b64encode((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()).decode()


JS_SIMULAR = """(args)=>{ const b=atob(args.b64), n=b.length/2, u=new Uint8Array(b.length); for(let i=0;i<b.length;i++) u[i]=b.charCodeAt(i);
  const i16=new Int16Array(u.buffer), f=new Float32Array(n); for(let i=0;i<n;i++) f[i]=i16[i]/32767;
  const G=Gioval.entrada.proveedores.golpes; let mudo=null; if(args.mudo){ mudo=function(t){ return args.mudo.some(function(w){ return t>=w[0]&&t<=w[1]; }); }; }
  const r=G.simular(f,args.sr,{calMs:args.calMs||3000,sens:args.sens||0,mudo:mudo,params:args.params||null});
  return {eventos:r.eventos.map(e=>[e.t,e.fuerza,e.rms]),info:r.info}; }"""


def simular_golpes(pg, x, sr=SR_AUDIO, **kw):
    r = pg.evaluate(JS_SIMULAR, dict(b64=a_b64(x), sr=sr, **kw))
    return r["eventos"], r["info"]


def llegar_al_tope(pg, isla="Números", directo=False):
    """Empieza una sesión y fuerza el tiempo diario al último segundo: espera el cartel de tope diario (capBox).
    directo=True no busca textos (sirve en cualquier idioma): abre la isla de Números por código y toca la primera tarjeta."""
    if directo:
        pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros'); goMenuIsla()"); pg.wait_for_timeout(100)
        pg.click("#menuIslaItems .island >> nth=0"); pg.wait_for_timeout(300)
    else:
        abrir_isla(pg, isla); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(300)
    pg.evaluate("store.time[KID+'|'+today()]=capBase()-1")
    pg.wait_for_selector("#capBox.show", timeout=6000)
