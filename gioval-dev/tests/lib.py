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
    """Estado comparable del progreso (sin marcas de tiempo). Se omiten las habilidades sin intentos ni dominio: son solo la entrada vacía que crea SK() al mirar una habilidad (la isla Números por edades tiene más habilidades que la versión publicada)."""
    return pg.evaluate("""(()=>{ var sk={}; Object.keys(store.sk).sort().forEach(function(k){ var v=store.sk[k]; if(!v.att&&!v.mast) return; sk[k]=[v.mast,v.att,+v.score.toFixed(6),v.box,v.lvl,JSON.stringify(v.rec)]; });
      var log={}; Object.keys(store.log).forEach(function(k){ log[k]=store.log[k].map(function(e){ return [e.s,e.o,e.f,e.k].join(); }); });
      return {sk:sk, log:log, days:store.days, stars:store.stars, checks:store.checks, profiles:store.profiles, limit:store.limit}; })()""")
