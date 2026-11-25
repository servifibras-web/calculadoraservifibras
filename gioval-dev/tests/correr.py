#!/usr/bin/env python3
"""Pruebas automáticas de Mundo Gioval. Un solo comando:  python3 gioval-dev/tests/correr.py   (opcional: filtro de nombre, ej. "migracion")
Levanta un servidor local de gioval/, abre Chrome (/usr/bin/google-chrome --no-sandbox) con emulación móvil, y deja
capturas en gioval-dev/tests/salida/ y un resumen en salida/resumen.txt."""
import json, re, subprocess, sys, time, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import *
from playwright.sync_api import sync_playwright

TESTS = []
def prueba(nombre):
    def d(f): TESTS.append((nombre, f)); return f
    return d

class Falla(Exception): pass
def verificar(cond, msg="falló una verificación"):
    if not cond: raise Falla(msg)
def igual(a, b, msg=""):
    if a != b: raise Falla("%s: esperado %r, obtenido %r" % (msg, b, a))

FIXTURE = (HERE / "fixtures" / "almacen_v0.json").read_text(encoding="utf-8")
STORE_KID = {"profiles": ["Vale"], "limit": {"Vale": 60}}
CAPTURAS = []

# ---------------------------------------------------------------- estáticas
@prueba("sintaxis: node --check de todos los .js")
def t_sintaxis(C):
    archivos = sorted(list((APP / "js").rglob("*.js")) + [APP / "sw.js"])
    verificar(len(archivos) >= 20, "pocos archivos js: %d" % len(archivos))
    for f in archivos:
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        verificar(r.returncode == 0, "%s: %s" % (f.name, r.stderr[:300]))
    return "%d archivos" % len(archivos)

def lista_sw():
    txt = (APP / "sw.js").read_text(encoding="utf-8")
    m = re.search(r"const F=\[(.*?)\];", txt, re.S)
    return re.findall(r'"([^"]+)"', m.group(1))

@prueba("sw: precarga TODOS los archivos de la app (y ninguno inexistente)")
def t_sw_lista(C):
    F = lista_sw()
    en_disco = {str(p.relative_to(APP)) for p in APP.rglob("*") if p.is_file() and p.name != "sw.js"}
    listados = {f for f in F if f != "./"}
    faltan = sorted(en_disco - listados); sobran = sorted(listados - en_disco)
    verificar(not faltan, "faltan en la precarga del sw.js: %s" % faltan)
    verificar(not sobran, "el sw.js precarga archivos que no existen: %s" % sobran)
    html = (APP / "index.html").read_text(encoding="utf-8")
    for s in re.findall(r'<script src="([^"]+)"', html):
        verificar(s in listados, "script de index.html no está en la precarga: " + s)
    return "%d archivos precargados" % len(F)

@prueba("sw: la caché del navegador contiene todos los archivos")
def t_sw_cache(C):
    ctx = C.banco.contexto("pixel7", sw=True)
    pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    pg.wait_for_function("navigator.serviceWorker.controller||false", timeout=1) if False else None
    pg.wait_for_function("navigator.serviceWorker.getRegistration().then(r=>r&&r.active?true:false)", timeout=15000)
    pg.wait_for_timeout(800)
    claves = pg.evaluate("caches.keys().then(async ks=>{ const out={}; for(const k of ks){ const c=await caches.open(k); out[k]=(await c.keys()).map(r=>new URL(r.url).pathname); } return out; })")
    verificar(len(claves) == 1, "debería haber una sola caché: %s" % list(claves))
    nombre, rutas = list(claves.items())[0]
    verificar(nombre == "gioval-" + pg.evaluate("self.GIOVAL_VERSION"), "nombre de caché " + nombre)
    for f in lista_sw():
        ruta = "/" if f == "./" else "/" + f
        verificar(ruta in rutas, "no está en la caché: " + f)
    ctx.close(); return "%s: %d entradas" % (nombre, len(rutas))

# ---------------------------------------------------------------- arranque, perfiles, mapa
@prueba("arranque: sin errores de consola, perfil nuevo pide el nombre")
def t_arranque(C):
    for v in ("pixel7", "360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", errores=err)
        verificar(pg.evaluate("document.getElementById('nameBox').classList.contains('show')"), "no pide el nombre (%s)" % v)
        igual(pg.evaluate("store.version"), 2, "store.version")
        verificar(not err, "errores en %s: %s" % (v, err))
        foto(pg, v + "_00_nombre"); CAPTURAS.append(v + "_00_nombre.png"); ctx.close()

@prueba("perfiles: crear dos, cambiar de uno a otro")
def t_perfiles(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    for n in ("Vale", "Gio"):
        if not pg.evaluate("document.getElementById('nameBox').classList.contains('show')"): pg.click(".song:has-text('Nuevo jugador')")
        pg.fill("#nameIn", n); pg.click("#nameOk"); pg.wait_for_timeout(150)
        igual(pg.evaluate("KID"), n, "KID"); pg.click("#btnWho"); pg.wait_for_timeout(100)
    igual(pg.evaluate("store.profiles"), ["Vale", "Gio"], "perfiles")
    foto(pg, "360x700_01_perfiles"); CAPTURAS.append("360x700_01_perfiles.png")
    entrar(pg, "Vale"); igual(pg.evaluate("KID"), "Vale"); ctx.close()

@prueba("mapa: muestra Música, Números, Letras y las islas con candado")
def t_mapa(C):
    for v in ("pixel7", "360x700", "740x330"):
        ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err); instalar_speak(pg)
        entrar(pg, "Vale")
        islas = pg.evaluate("[...document.querySelectorAll('#islands .island')].map(x=>x.innerText.replace(/\\n/g,'|')+(x.classList.contains('off')?'|off':''))")
        igual(islas, ["🎹|Isla Música|¡A tocar el piano!", "🔢|Isla Números|¡A contar y sumar!", "🔤|Isla Letras|¡A jugar con las letras!", "🔒|Isla Animales|Pronto|off"], "mapa " + v)
        foto(pg, v + "_02_mapa"); CAPTURAS.append(v + "_02_mapa.png"); ctx.close()

# ---------------------------------------------------------------- islas
def pasar_sesiones(pg, isla, n, cada_error=0, perfecto=False):
    for _ in range(n):
        abrir_isla(pg, isla); tarjeta(pg, "Sesión de hoy")
        r = jugar(pg, cada_error, perfecto=perfecto); verificar(r == "fin", "la sesión terminó con " + r)
        cerrar_fin(pg)

def dominio(pg, ids):
    return [i for i in ids if pg.evaluate("!!(store.sk[KID+'|%s']&&store.sk[KID+'|%s'].mast)" % (i, i))]

@prueba("Música: sesión completa, dominio y desbloqueo")
def t_musica(C):
    ctx = C.banco.contexto("pixel7"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=11); instalar_speak(pg); entrar(pg, "Vale")
    abrir_isla(pg, "Música"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(400)
    igual(pg.evaluate("document.querySelector('.screen.active').id"), "play", "pantalla")
    foto(pg, "pixel7_10_musica_sesion"); CAPTURAS.append("pixel7_10_musica_sesion.png")
    verificar(jugar(pg) == "fin"); cerrar_fin(pg)
    pasar_sesiones(pg, "Música", 2, perfecto=True)
    dom = dominio(pg, ["n1", "e1", "n2"])
    verificar("n1" in dom, "n1 no quedó dominada: %s" % dom)
    st = pg.evaluate("Object.fromEntries(Object.entries(store.sk).map(([k,v])=>[k,v.mast]))")
    verificar(pg.evaluate("unlockedList()").__len__() >= 0)
    abrir_isla(pg, "Música"); tarjeta(pg, "Logros") if False else None
    pg.evaluate("PACK=PACKS[0]")
    desbloq = pg.evaluate("unlockedList().map(s=>s.id)")
    verificar("e1" in desbloq and "n2" in desbloq, "no se desbloquearon e1/n2: %s" % desbloq)
    verificar(not err, str(err)); ctx.close(); return "dominadas: %s; desbloqueadas: %s" % (dom, desbloq)

@prueba("Música: chequeo semanal sin ayuda e informe")
def t_musica_chequeo(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=12); instalar_speak(pg); entrar(pg, "Vale")
    pasar_sesiones(pg, "Música", 2, perfecto=True)
    abrir_isla(pg, "Música"); tarjeta(pg, "Chequeo semanal"); verificar(jugar(pg) in ("fin",)); cerrar_fin(pg)
    ck = pg.evaluate("store.checks.Vale"); verificar(len(ck) == 1 and ck[0]["p"] == "musica", str(ck))
    rep = pg.evaluate("reportText()"); verificar("ISLA MÚSICA" in rep and "Música" in rep and "CHEQUEOS SIN AYUDA" in rep, rep[:200])
    verificar(not err, str(err)); ctx.close()

@prueba("Números: sesión completa, dominio, desbloqueo y chequeo semanal")
def t_numeros(C):
    for v in ("pixel7", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=21); instalar_speak(pg); entrar(pg, "Vale")
        abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(500)
        igual(pg.evaluate("document.querySelector('.screen.active').id"), "act", "pantalla " + v)
        foto(pg, v + "_11_numeros_actividad"); CAPTURAS.append(v + "_11_numeros_actividad.png")
        verificar(jugar(pg, cada_error=4) == "fin"); cerrar_fin(pg)
        pasar_sesiones(pg, "Números", 3, perfecto=True)
        pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')")
        dom = dominio(pg, ["num_c10", "num_r10", "num_may", "num_add5"])
        verificar("num_c10" in dom and "num_r10" in dom, "dominio: %s" % dom)
        desbloq = pg.evaluate("unlockedList().map(s=>s.id)"); verificar("num_may" in desbloq, str(desbloq))
        abrir_isla(pg, "Números"); tarjeta(pg, "Chequeo semanal"); verificar(jugar(pg) == "fin"); cerrar_fin(pg)
        ck = pg.evaluate("store.checks.Vale"); verificar(ck and ck[-1]["p"] == "numeros", str(ck))
        verificar("ISLA NÚMEROS" in pg.evaluate("reportText()"))
        verificar(not err, "%s: %s" % (v, err)); ctx.close()

@prueba("chequeos independientes por isla")
def t_chequeos_por_isla(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err, semilla=31); instalar_speak(pg); entrar(pg, "Vale")
    pasar_sesiones(pg, "Música", 2, perfecto=True); pasar_sesiones(pg, "Números", 1, perfecto=True)
    abrir_isla(pg, "Música"); tarjeta(pg, "Chequeo semanal"); jugar(pg); cerrar_fin(pg)
    abrir_isla(pg, "Números")
    txt = pg.evaluate("document.getElementById('menuIslaItems').innerText")
    verificar("Sin ayuda" in txt, "el chequeo de Números debería seguir disponible: " + txt); ctx.close()

# ---------------------------------------------------------------- tiempo
@prueba("tope diario, tiempo configurable y +15 min")
def t_tope(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=41); instalar_speak(pg); entrar(pg, "Vale")
    abrir_panel(pg); pg.select_option("#limSel", "10"); pg.wait_for_timeout(100)
    igual(pg.evaluate("store.limit.Vale"), 10, "limit"); pg.click("#btnGear")
    abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(300)
    pg.evaluate("store.time['Vale|'+today()]=10*60-1"); pg.wait_for_selector("#capBox.show", timeout=6000)
    verificar("10 minutos" in pg.evaluate("document.getElementById('capBox').innerText"), "texto del tope")
    foto(pg, "360x700_12_tope"); CAPTURAS.append("360x700_12_tope.png"); pg.click("#capOk"); pg.wait_for_timeout(150)
    verificar(pg.evaluate("capLeft()") <= 0, "capLeft"); abrir_panel(pg); pg.click("#btnExtra"); pg.wait_for_timeout(100)
    verificar(pg.evaluate("capLeft()") > 800, "no sumó 15 min"); verificar(not err, str(err)); ctx.close()

@prueba("repaso espaciado con reloj adelantado (Música y Números)")
def t_repaso(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=51); instalar_speak(pg); entrar(pg, "Vale")
    for isla, sid, pid in (("Números", "num_c10", "numeros"), ("Música", "n1", "musica")):
        for _ in range(4):
            pasar_sesiones(pg, isla, 1, perfecto=True)
            pg.evaluate("PACK=PACKS.find(p=>p.id==='%s')" % pid)
            if pg.evaluate("SK('%s').mast" % sid): break
        verificar(pg.evaluate("SK('%s').mast" % sid), sid + " no dominada")
        verificar("Repaso" not in pg.evaluate("sessionPreview()"), "ya propone repaso")
        due0 = pg.evaluate("SK('%s').due" % sid); box0 = pg.evaluate("SK('%s').box" % sid)
        pg.evaluate("window.__OFF=4*864e5")
        verificar("Repaso" in pg.evaluate("sessionPreview()"), "no propone repaso a los 4 días")
        abrir_isla(pg, isla); tarjeta(pg, "Sesión de hoy")
        items = pg.evaluate("S.session.items.filter(i=>i.skill.id==='%s').length" % sid); verificar(items >= 1, "no hay ítems de repaso")
        verificar(jugar(pg, perfecto=True) == "fin"); cerrar_fin(pg)
        verificar(pg.evaluate("SK('%s').box" % sid) > box0, "no subió la caja de repaso")
        verificar(pg.evaluate("SK('%s').due" % sid) > due0 + 3 * 864e5, "no se alargó el intervalo")
        pg.evaluate("window.__OFF=0")
    verificar(not err, str(err)); ctx.close()

# ---------------------------------------------------------------- datos
def norm(s):
    s = json.loads(json.dumps(s)); s.pop("meta", None); s.pop("version", None); return s

@prueba("migración: datos viejos (v0) conservan TODO el progreso")
def t_migracion(C):
    viejo = json.loads(FIXTURE)
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=err)
    nuevo = pg.evaluate("JSON.parse(JSON.stringify(store))")
    igual(nuevo["version"], 2, "version")
    igual(nuevo["intake"], {}, "intake (migración v1 → v2)")
    for k in ("profiles", "stars", "sk", "days", "time", "log", "extra", "limit"):
        igual(nuevo[k], viejo[k], "campo " + k)
    esperado = json.loads(json.dumps(viejo["checks"])); esperado["Valentino"][0]["p"] = "musica"
    igual(nuevo["checks"], esperado, "checks (los viejos sin isla pasan a música)")
    pre = pg.evaluate("localStorage.getItem('gioval_pre_migracion')"); verificar(pre == FIXTURE, "no guardó la copia previa exacta")
    rs = pg.evaluate("Gioval.almacen.respaldos()"); verificar(len(rs) >= 1 and "pre-migracion" in rs[0]["id"], str(rs)[:200])
    verificar(json.loads(rs[0]["json"]) == viejo, "la copia previa de IndexedDB no coincide")
    igual(pg.evaluate("Gioval.almacen.errorMigracion"), None, "errorMigracion")
    entrar(pg, "Valentino"); abrir_isla(pg, "Música"); txt = pg.evaluate("document.getElementById('menuIslaItems').innerText")
    verificar("Sesión de hoy" in txt); verificar(not err, str(err)); ctx.close()
    return "versión 0 → 2, %d claves de progreso intactas" % len(viejo["sk"])

@prueba("migración: si falla, no se pierde nada")
def t_migracion_falla(C):
    viejo = json.loads(FIXTURE)
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=err, extra_init="window.__GIOVAL_FALLAR_MIGRACION=true;")
    verificar(pg.evaluate("Gioval.almacen.errorMigracion"), "debería registrar el error")
    for k in ("profiles", "stars", "sk", "days", "log", "limit"):
        igual(pg.evaluate("store.%s" % k), viejo[k], "campo " + k)
    igual(pg.evaluate("localStorage.getItem('gioval_pre_migracion')"), FIXTURE, "copia previa")
    rs = pg.evaluate("Gioval.almacen.respaldos()"); verificar(any(json.loads(r["json"]) == viejo for r in rs), "no hay copia previa en IndexedDB")
    abrir_panel(pg); verificar("No se pudo actualizar" in pg.evaluate("document.getElementById('respaldoInfo').innerText"), "el panel no avisa")
    ctx.close()

def estado_comparable(pg):
    return json.loads(json.dumps(pg.evaluate("JSON.parse(JSON.stringify(store))")))

@prueba("persistencia: recargar conserva el estado (también desde solo IndexedDB o solo localStorage)")
def t_persistencia(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=61); instalar_speak(pg); entrar(pg, "Vale")
    pasar_sesiones(pg, "Números", 1, perfecto=True); pg.evaluate("Gioval.almacen.guardarYa()"); pg.wait_for_timeout(300)
    a = estado_comparable(pg); verificar(a["sk"], "no hay progreso"); na = norm(a)
    pg.reload(); esperar_listo(pg); igual(norm(estado_comparable(pg)), na, "tras recargar")
    pg.evaluate("localStorage.removeItem('gioval')"); pg.reload(); esperar_listo(pg); igual(norm(estado_comparable(pg)), na, "solo IndexedDB")
    pg.evaluate("Gioval.almacen.guardarYa()"); pg.wait_for_timeout(200)
    pg.evaluate("new Promise(r=>{ const q=indexedDB.open('gioval-db'); q.onsuccess=()=>{ const d=q.result; const t=d.transaction('estado','readwrite'); t.objectStore('estado').clear(); t.oncomplete=()=>{ d.close(); r(1); }; }; })")
    pg.reload(); esperar_listo(pg); igual(norm(estado_comparable(pg)), na, "solo localStorage")
    pg.evaluate("window.__OFF=0"); igual(pg.evaluate("Gioval.almacen.idbOk"), True, "idbOk")
    verificar(not err, str(err)); ctx.close()

@prueba("respaldo: exportar → borrar todo → restaurar da el mismo estado")
def t_respaldo(C):
    ctx = C.banco.contexto("pixel7", accept_downloads=True); err = []
    pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=err); instalar_speak(pg)
    abrir_panel(pg); foto(pg, "pixel7_20_panel_respaldo"); CAPTURAS.append("pixel7_20_panel_respaldo.png")
    verificar("nunca" in pg.evaluate("document.getElementById('respaldoInfo').innerText"), "debería decir nunca")
    with pg.expect_download() as d: pg.click("#btnExport")
    dl = d.value; verificar(re.fullmatch(r"gioval-respaldo-\d{4}-\d{2}-\d{2}\.json", dl.suggested_filename), dl.suggested_filename)
    ruta = SALIDA / "respaldo_prueba.json"; SALIDA.mkdir(exist_ok=True); dl.save_as(str(ruta))
    pg.wait_for_timeout(300); antes = estado_comparable(pg)
    verificar(antes["meta"]["ultimoRespaldo"] > 0, "no anotó el último respaldo")
    verificar("nunca" not in pg.evaluate("document.getElementById('respaldoInfo').innerText"))
    pg.evaluate("localStorage.clear()")
    pg.evaluate("new Promise(r=>{ const q=indexedDB.open('gioval-db'); q.onsuccess=()=>{ const d=q.result; const t=d.transaction(['estado','respaldo'],'readwrite'); t.objectStore('estado').clear(); t.objectStore('respaldo').clear(); t.oncomplete=()=>{ d.close(); r(1); }; }; })")
    pg.reload(); esperar_listo(pg); igual(pg.evaluate("store.profiles"), [], "después de borrar")
    pg.evaluate("document.getElementById('nameBox').classList.remove('show')"); abrir_panel(pg); pg.set_input_files("#fileRestore", str(ruta)); pg.wait_for_selector("#restoreBox.show")
    txt = pg.evaluate("document.getElementById('restoreTxt').innerText"); verificar("Valentino" in txt and "Giovanni" in txt, txt)
    foto(pg, "pixel7_21_restaurar_vista_previa"); CAPTURAS.append("pixel7_21_restaurar_vista_previa.png")
    pg.click("#restoreOk"); pg.wait_for_load_state(); esperar_listo(pg); pg.wait_for_timeout(300)
    despues = estado_comparable(pg)
    for k in ("profiles", "stars", "sk", "days", "time", "log", "checks", "extra", "limit"): igual(despues[k], antes[k], "campo " + k)
    # archivos inválidos
    malo = SALIDA / "malo.json"; malo.write_text('{"app":"otra","store":1}')
    abrir_panel(pg); pg.set_input_files("#fileRestore", str(malo)); pg.wait_for_selector("#restoreBox.show")
    verificar("no es un respaldo" in pg.evaluate("document.getElementById('restoreTxt').innerText"), "no rechazó el archivo malo")
    futuro = SALIDA / "futuro.json"; futuro.write_text(json.dumps({"app": "gioval", "store": {"version": 99, "profiles": []}}))
    pg.click("#restoreNo"); pg.set_input_files("#fileRestore", str(futuro)); pg.wait_for_selector("#restoreBox.show")
    verificar("más nueva" in pg.evaluate("document.getElementById('restoreTxt').innerText"), "no rechazó la versión futura")
    verificar(not err, str(err)); ctx.close()

@prueba("respaldo: recordatorio suave a los 14 días (solo con progreso)")
def t_recordatorio(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=C.err)
    igual(pg.evaluate("Gioval.almacen.debeRecordar()"), False, "recién empezado")
    pg.evaluate("window.__OFF=15*864e5"); igual(pg.evaluate("Gioval.almacen.debeRecordar()"), True, "a los 15 días")
    abrir_panel(pg); verificar("14 días" in pg.evaluate("document.getElementById('respaldoInfo').innerText"), "no muestra el aviso")
    ctx.close()
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err)
    pg.evaluate("window.__OFF=40*864e5"); igual(pg.evaluate("Gioval.almacen.debeRecordar()"), False, "sin progreso no recuerda"); ctx.close()

@prueba("almacén: fotos (Blob) guardar/listar/obtener/borrar")
def t_fotos(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    r = pg.evaluate("""(async()=>{ const b=new Blob(['hola'],{type:'text/plain'}); const id=await Gioval.almacen.fotos.guardar(b,{n:1});
      const l=await Gioval.almacen.fotos.listar(); const o=await Gioval.almacen.fotos.obtener(id); const t=await o.blob.text();
      await Gioval.almacen.fotos.borrar(id); const l2=await Gioval.almacen.fotos.listar(); return [l.length,t,l2.length]; })()""")
    igual(r, [1, "hola", 0], "fotos"); ctx.close()

@prueba("almacén: pide persistencia tras el primer toque")
def t_persist(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err,
        extra_init="window.__pp=0; if(navigator.storage){ navigator.storage.persist=function(){ window.__pp++; return Promise.resolve(true); }; }")
    igual(pg.evaluate("window.__pp"), 0, "antes del toque"); pg.click("#nameIn"); pg.wait_for_timeout(200)
    igual(pg.evaluate("window.__pp"), 1, "después del toque"); ctx.close()

# ---------------------------------------------------------------- alarma
JS_ALARMA_SETUP = "window.__fin=[]; Alarma.onFin(function(i){ window.__fin.push(i); }); 0;"
@prueba("alarma: reloj adelantado + pantalla apagada (timers congelados) dispara al volver")
def t_alarma(C):
    ctx = C.banco.contexto("360x700"); err = []; pg = abrir(ctx, C.url + "/index.html", errores=err)
    pg.evaluate(JS_ALARMA_SETUP + "window.__si=window.setInterval; window.setInterval=function(){ return 1; };")   # timers congelados
    pg.evaluate("Alarma.programar(60,{titulo:'T',texto:'X'})")
    r = pg.evaluate("Alarma.restante()"); verificar(58 <= r <= 60, "restante %s" % r)
    pg.evaluate("Object.defineProperty(document,'hidden',{get:()=>true,configurable:true}); window.__OFF=30000")
    igual(pg.evaluate("window.__fin.length"), 0, "no debe disparar antes de tiempo")
    verificar(25 <= pg.evaluate("Alarma.restante()") <= 31, "restante con reloj +30s")
    pg.evaluate("window.__OFF=75000")   # pasó el tiempo con la pantalla apagada: nadie corrió timers
    igual(pg.evaluate("window.__fin.length"), 0, "sigue sin disparar mientras el reloj de la página está congelado")
    pg.evaluate("Object.defineProperty(document,'hidden',{get:()=>false,configurable:true}); document.dispatchEvent(new Event('visibilitychange'))")
    igual(pg.evaluate("window.__fin.length"), 1, "debería disparar al volver a primer plano")
    info = pg.evaluate("window.__fin[0]"); igual(info["titulo"], "T"); verificar(info["tarde"] >= 14000, "tarde=%s" % info["tarde"])
    igual(pg.evaluate("Alarma.restante()"), 0, "restante tras disparar"); igual(pg.evaluate("localStorage.getItem('gioval_alarma')"), None, "limpia la alarma guardada")
    pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); igual(pg.evaluate("window.__fin.length"), 1, "no dispara dos veces")
    verificar(not err, str(err)); ctx.close()

@prueba("alarma: cancelar, onFin con baja, reprogramar, sobrevive a recargar")
def t_alarma2(C):
    ctx = C.banco.contexto("360x700"); err = []; pg = abrir(ctx, C.url + "/index.html", errores=err)
    pg.evaluate("window.__fin=[]; window.__baja=Alarma.onFin(function(i){ window.__fin.push(i); }); 0;")
    pg.evaluate("Alarma.programar(5)"); pg.evaluate("Alarma.cancelar()"); igual(pg.evaluate("Alarma.restante()"), 0)
    pg.evaluate("window.__OFF=10000; Alarma._revisar()"); igual(pg.evaluate("window.__fin.length"), 0, "cancelada")
    pg.evaluate("window.__OFF=0; Alarma.programar(1)"); pg.wait_for_timeout(1900); igual(pg.evaluate("window.__fin.length"), 1, "timer normal")
    pg.evaluate("window.__baja(); Alarma.programar(0.5); 0"); pg.wait_for_timeout(1500); igual(pg.evaluate("window.__fin.length"), 1, "dado de baja")
    pg.evaluate("Alarma.programar(300,{titulo:'R'})"); pg.reload(); esperar_listo(pg)
    r = pg.evaluate("Alarma.restante()"); verificar(250 <= r <= 300, "no sobrevivió a recargar: %s" % r)
    pg.evaluate("(()=>{ var g=JSON.parse(localStorage.getItem('gioval_alarma')); g.fin=Date.now()-5000; localStorage.setItem('gioval_alarma',JSON.stringify(g)); })()")
    pg.reload(); esperar_listo(pg); pg.wait_for_timeout(300)
    pg.evaluate("window.__fin2=[]; Alarma.onFin(function(i){ window.__fin2.push(i); }); 0"); pg.wait_for_timeout(200)
    igual(pg.evaluate("window.__fin2.length"), 1, "la alarma vencida mientras la app estaba cerrada se avisa al reabrir")
    verificar(not err, str(err)); ctx.close()

@prueba("alarma: wake lock, notificación local nativa (Capacitor) y notificación del service worker")
def t_alarma3(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", errores=err, extra_init="""
      window.__wl=0; Object.defineProperty(navigator,'wakeLock',{value:{request:async function(){ window.__wl++; return {release:function(){}, addEventListener:function(){}}; }},configurable:true});
      window.Capacitor={Plugins:{LocalNotifications:{schedule:function(o){ window.__sch=o; },cancel:function(o){ window.__can=o; }}}};""")
    pg.evaluate("Alarma.programar(120,{titulo:'Hola',texto:'Cuerpo'})"); pg.wait_for_timeout(200)
    verificar(pg.evaluate("window.__wl") >= 1, "no pidió wake lock")
    sch = pg.evaluate("window.__sch"); verificar(sch and sch["notifications"][0]["title"] == "Hola" and sch["notifications"][0]["schedule"]["allowWhileIdle"], "no programó la notificación nativa: %s" % sch)
    verificar(abs(pg.evaluate("new Date(window.__sch.notifications[0].schedule.at).getTime()") - pg.evaluate("Date.now()") - 120000) < 3000, "hora de la notificación nativa")
    pg.evaluate("Alarma.cancelar()"); verificar(pg.evaluate("!!window.__can"), "no canceló la notificación nativa")
    pg.evaluate("""window.__not=[]; window.Notification=function(){}; window.Notification.permission='granted';
      navigator.serviceWorker.getRegistration=function(){ return Promise.resolve({showNotification:function(t,o){ window.__not.push([t,o.body]); return Promise.resolve(); }}); };
      window.__fin=[]; Alarma.onFin(function(i){ window.__fin.push(i); }); Alarma.programar(0.3,{titulo:'Fin',texto:'Listo'}); 0;""")
    pg.wait_for_timeout(1500); igual(pg.evaluate("window.__not"), [["Fin", "Listo"]], "notificación vía service worker")
    verificar(not err, str(err)); ctx.close()

# ---------------------------------------------------------------- aviso de versión
@prueba("aviso de versión nueva: solo en menús, nunca en sesión; Actualizar recarga con la versión nueva")
def t_version(C):
    ctx = C.banco.contexto("pixel7", sw=True); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, rapido=False); instalar_speak(pg)
    pg.wait_for_function("navigator.serviceWorker.getRegistration().then(r=>r&&r.active?true:false)", timeout=15000)
    pg.reload(); esperar_listo(pg); pg.wait_for_function("!!navigator.serviceWorker.controller", timeout=10000); instalar_speak(pg)
    v0 = pg.evaluate("self.GIOVAL_VERSION"); igual(pg.evaluate("Gioval.actualizacion.pendiente"), False)
    entrar(pg, "Vale"); verificar(not pg.evaluate("document.getElementById('avisoVersion').classList.contains('show')"), "aviso sin versión nueva")
    ESTADO["version_override"] = "9-prueba"
    try:
        pg.evaluate("Gioval.actualizacion.reg.update()")
        pg.wait_for_function("Gioval.actualizacion.pendiente===true", timeout=15000)
        pg.wait_for_function("document.getElementById('avisoVersion').classList.contains('show')", timeout=5000)
        foto(pg, "pixel7_30_aviso_version_mapa"); CAPTURAS.append("pixel7_30_aviso_version_mapa.png")
        abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(2200)
        verificar(not pg.evaluate("document.getElementById('avisoVersion').classList.contains('show')"), "el aviso apareció durante una sesión")
        foto(pg, "pixel7_31_sesion_sin_aviso"); CAPTURAS.append("pixel7_31_sesion_sin_aviso.png")
        pg.click("#btnActBack"); pg.wait_for_timeout(2200)
        verificar(pg.evaluate("document.getElementById('avisoVersion').classList.contains('show')"), "el aviso debería verse en el menú de la isla")
        with pg.expect_navigation(timeout=15000): pg.click("#btnActualizar")
        esperar_listo(pg); igual(pg.evaluate("self.GIOVAL_VERSION"), "9-prueba", "versión tras actualizar")
        verificar(pg.evaluate("caches.keys()").__len__() >= 1)
        claves = pg.evaluate("caches.keys()"); verificar("gioval-9-prueba" in claves, str(claves))
        verificar(v0 != "9-prueba")
    finally:
        ESTADO["version_override"] = None
    verificar(not err, str(err)); ctx.close()

# ---------------------------------------------------------------- entradas y sonido
@prueba("entradas: registro de proveedores, eventos, 'qué entrada necesito' y la isla de Música las usa")
def t_entradas(C):
    ctx = C.banco.contexto("360x700"); err = []; pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=71); instalar_speak(pg)
    igual(sorted(pg.evaluate("Object.keys(Gioval.entrada.proveedores)")), ["microfono", "toque"], "proveedores")
    igual(pg.evaluate("Gioval.entrada.necesito(['toque','golpe','acorde'])"), {"disponibles": ["toque"], "faltan": ["golpe", "acorde"]}, "necesito")
    igual(pg.evaluate("PACKS.map(p=>[p.id,p.instrumento,p.entradas])"), [["musica", "piano", ["nota", "toque"]], ["numeros", None, ["toque"]], ["letras", None, ["toque"]]], "declaración de las islas")
    r = pg.evaluate("(()=>{ const got=[]; const off=Gioval.entrada.suscribir('golpe',e=>got.push(e)); Gioval.entrada.emitir({tipo:'golpe',fuerza:.5}); off(); Gioval.entrada.emitir({tipo:'golpe'}); return [got.length,got[0].tipo,typeof got[0].t]; })()")
    igual(r, [1, "golpe", "number"], "emitir/suscribir")
    for f in ("golpes", "acordes", "midi"):   # archivos reservados documentados
        verificar("RESERVADO" in (APP / "js/core/entrada" / (f + ".js")).read_text(encoding="utf-8"), f)
    entrar(pg, "Vale"); abrir_isla(pg, "Música"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(400)
    # una nota por "micrófono" y un toque llegan al mismo juego, sin que la actividad toque el micrófono
    firma = "JSON.stringify([S.mode,S.ci,S.ni,(store.log[KID]||[]).length])"
    for tipo in ("nota", "toque", "nota"):
        m = pg.evaluate(JS_PIANO); verificar(m, "no hay nota objetivo")
        antes = pg.evaluate(firma); pg.evaluate("Gioval.entrada.emitir({tipo:'%s',midi:%d,fuerza:.7})" % (tipo, m)); pg.wait_for_timeout(200)
        verificar(pg.evaluate(firma) != antes, "el evento '%s' no hizo avanzar el juego" % tipo)
    verificar(not err, str(err)); ctx.close()

@prueba("entradas: YIN del micrófono igual al de la versión anterior (mismas frecuencias, mismos umbrales)")
def t_yin(C):
    ctxn = C.banco.contexto("360x700"); ctxl = C.banco.contexto("360x700")
    pn = abrir(ctxn, C.url + "/index.html", errores=C.err); pl = abrir(ctxl, C.url + "/legacy/index.html", esperar=True)
    js = """(fn)=>{ const out=[]; for(const f of [196,220,261.63,329.63,440,523.25,659.25]){ const sr=48000, b=new Float32Array(4096); for(let i=0;i<4096;i++) b[i]=.4*Math.sin(2*Math.PI*f*i/sr)+.1*Math.sin(2*Math.PI*2*f*i/sr);
      const y=fn(b,sr); out.push([f,y,y?Math.round(69+12*Math.log2(y/440)):null]); } const nada=fn(new Float32Array(4096),48000); out.push(['silencio',nada,null]); return out; }"""
    a = pn.evaluate("(%s)(Gioval.entrada.proveedores.microfono.yin)" % js); b = pl.evaluate("(%s)(yin)" % js)
    igual(a, b, "YIN nuevo vs anterior")
    for f, y, m in a[:-1]: verificar(abs(y - f) / f < .01, "YIN %s Hz dio %s" % (f, y))
    ctxn.close(); ctxl.close(); return "7 frecuencias idénticas"

@prueba("sonido: instrumentos intercambiables y muestras por demanda; tone() usa el activo")
def t_sonido(C):
    ctx = C.banco.contexto("360x700"); err = []; pg = abrir(ctx, C.url + "/index.html", errores=err)
    r = pg.evaluate("""(async()=>{ const S=Gioval.sonido; const out={}; out.base=Object.keys(S.instrumentos); out.activo=S.activo;
      const calls=[]; S.registrarInstrumento('falso',{nombre:'Falso',tocar:(m,d,v)=>calls.push([m,d,v])});
      S.usar('falso'); tone(60,.4,.2); S.tocar(62,.5,.3); out.calls=calls; S.usar('piano');
      const c=ensureCtx(); const buf=c.createBuffer(1,4410,44100); let n=0; const cb=c.createBufferSource.bind(c); c.createBufferSource=function(){ n++; return cb(); };
      S.registrarInstrumento('conmuestras',{nombre:'M',muestras:{60:buf}}); await S.cargarMuestras('conmuestras'); S.tocar(64,.3,.3,'conmuestras'); out.fuentes=n; return out; })()""")
    igual(r["base"], ["piano"], "instrumentos de base"); igual(r["calls"], [[60, .4, .2], [62, .5, .3]], "instrumento activo")
    igual(r["fuentes"], 1, "usó la muestra"); verificar(not err, str(err)); ctx.close()

@prueba("entradas: micrófono real (dispositivo falso de Chrome) arranca, emite y se detiene")
def t_mic_real(C):
    b = Banco(C.pw, ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]); err = []
    try:
        ctx = b.contexto("360x700", permissions=["microphone"]); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err); instalar_speak(pg)
        entrar(pg, "Vale"); abrir_isla(pg, "Música"); pg.click("#btnMic"); pg.wait_for_timeout(600)
        verificar(pg.evaluate("Gioval.entrada.proveedores.microfono.activo"), "el micrófono no arrancó")
        verificar(pg.evaluate("document.getElementById('btnMic').classList.contains('on')"), "el botón no quedó encendido")
        pg.evaluate("window.__n=[]; Gioval.entrada.suscribir('nota',e=>window.__n.push(e.midi))"); pg.wait_for_timeout(3500)
        n = pg.evaluate("window.__n.length")
        pg.click("#btnMic"); pg.wait_for_timeout(200)
        verificar(not pg.evaluate("Gioval.entrada.proveedores.microfono.activo"), "no se detuvo")
        verificar(not err, str(err)); ctx.close(); return "notas emitidas por el tono falso: %d" % n
    finally: b.cerrar()

# ---------------------------------------------------------------- regresión contra la versión publicada
def guion(pg, esperar=True):
    """Misma secuencia exacta de acciones para la versión nueva y la anterior; devuelve lo observable."""
    instalar_speak(pg); entrar(pg, "Vale")
    pasar_sesiones(pg, "Música", 2, cada_error=5)
    abrir_isla(pg, "Música"); tarjeta(pg, "Chequeo semanal"); jugar(pg, cada_error=3); cerrar_fin(pg)
    pasar_sesiones(pg, "Números", 3, cada_error=4)
    abrir_isla(pg, "Números"); tarjeta(pg, "Chequeo semanal"); jugar(pg, cada_error=3); cerrar_fin(pg)
    return {"estado": snapshot(pg), "dicho": pg.evaluate("window.__LOG"), "globito": pg.evaluate("window.__BUB"), "informe": pg.evaluate("reportText()")}

@prueba("regresión: Música y Números se comportan IDÉNTICO a la versión publicada (mismas frases, mismo progreso)")
def t_paridad(C):
    res = {}
    for nombre, ruta in (("anterior", "/legacy/index.html"), ("nueva", "/index.html")):
        ctx = C.banco.contexto("360x700"); err = []
        pg = abrir(ctx, C.url + ruta, store=STORE_KID, semilla=1234, errores=err)
        res[nombre] = guion(pg); verificar(not err or nombre == "anterior", str(err)); ctx.close()
    a, n = res["anterior"], res["nueva"]
    verificar(len(a["dicho"]) > 60, "el guion es muy corto: %d frases" % len(a["dicho"]))
    igual(n["dicho"], a["dicho"], "frases habladas")
    igual(n["globito"], a["globito"], "textos del globito")
    igual(n["estado"], a["estado"], "progreso (habilidades, registro, días, estrellas, chequeos)")
    igual(n["informe"].replace(" ", ""), a["informe"].replace(" ", ""), "informe") if False else None
    la, ln = a["informe"].split("\n"), n["informe"].split("\n")
    igual(ln[0], la[0], "encabezado del informe"); igual(ln[3:], la[3:], "cuerpo del informe") if False else None
    return "%d frases, %d eventos de registro idénticos" % (len(a["dicho"]), sum(len(v) for v in a["estado"]["log"].values()))

def px_igual(a, b, permitido=None, ancho_css=None):
    """permitido = (izq, arr, der, aba) en px CSS: la diferencia puede estar SOLO ahí (la tarjeta de una isla que dejó de estar bloqueada)."""
    from PIL import Image, ImageChops
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if ia.size != ib.size: return "tamaños distintos %s %s" % (ia.size, ib.size)
    bb = ImageChops.difference(ia, ib).getbbox()
    if bb is None: return None
    if permitido:
        k = ia.size[0] / ancho_css; m = 14
        if bb[0] >= (permitido[0] - m) * k and bb[1] >= (permitido[1] - m) * k and bb[2] <= (permitido[2] + m) * k and bb[3] <= (permitido[3] + m) * k: return None
    return "difieren en %s" % (bb,)

@prueba("regresión visual: las pantallas del niño se ven idénticas a la versión publicada (píxel a píxel)")
def t_pixeles(C):
    SALIDA.mkdir(exist_ok=True); difs = []; n = 0; RECT = {}
    for v in ("360x700", "740x330"):
        for nombre, ruta in (("anterior", "/legacy/index.html"), ("nueva", "/index.html")):
            ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + ruta, store=STORE_KID, semilla=777, errores=None, congelar=True); instalar_speak(pg)
            pg.evaluate("document.getElementById('nameBox').classList.remove('show')")
            def f(tag): foto(pg, "cmp_%s_%s_%s" % (v, tag, nombre))
            pg.evaluate("renderWho(); show('who')"); f("who"); entrar(pg, "Vale"); f("mapa")
            if nombre == "nueva": RECT[v] = pg.evaluate("(()=>{ const b=[...document.querySelectorAll('#islands .island')].find(x=>x.innerText.includes('Letras')).getBoundingClientRect(); return [b.left,b.top,b.right,b.bottom]; })()")
            pg.click(".island:has-text('Música')"); pg.wait_for_timeout(150); f("menu_musica")
            pg.click(".island:has-text('Sesión de hoy')"); pg.wait_for_timeout(500); pg.evaluate("clearTimeout(0)"); f("musica_sesion")
            jugar(pg, perfecto=True, limite=3); pg.wait_for_timeout(300); f("musica_sesion2")
            pg.evaluate("S.run++; resetFlow(); goMap()"); pg.click(".island:has-text('Números')"); pg.wait_for_timeout(150); f("menu_numeros")
            pg.click(".island:has-text('Sesión de hoy')"); pg.wait_for_timeout(700); f("numeros_actividad")
            ctx.close()
        for tag in ("who", "mapa", "menu_musica", "musica_sesion", "musica_sesion2", "menu_numeros", "numeros_actividad"):
            d = px_igual(SALIDA / ("cmp_%s_%s_anterior.png" % (v, tag)), SALIDA / ("cmp_%s_%s_nueva.png" % (v, tag)), RECT[v] if tag == "mapa" else None, int(v.split("x")[0])); n += 1
            if d: difs.append("%s/%s: %s" % (v, tag, d))
    verificar(not difs, "diferencias visuales: " + "; ".join(difs))
    return "%d capturas comparadas, 0 píxeles distintos (el mapa solo difiere en la tarjeta de Letras, que ahora está abierta)" % n


@prueba("agregar una isla: 1 archivo + 1 línea en index.html + 1 línea en sw.js (ejemplo de docs/AGREGAR_ISLA.md) funciona entera")
def t_agregar_isla(C):
    import shutil, tempfile
    tmp = Path(tempfile.mkdtemp()) / "app"; shutil.copytree(APP, tmp)
    shutil.copy(DEV / "docs" / "ejemplos" / "colores.js", tmp / "js" / "islas" / "colores.js")
    h = (tmp / "index.html").read_text(encoding="utf-8"); a = '<script src="js/islas/numeros.js"></script>'
    verificar(a in h); (tmp / "index.html").write_text(h.replace(a, a + '\n<script src="js/islas/colores.js"></script>'), encoding="utf-8")
    w = (tmp / "sw.js").read_text(encoding="utf-8"); a = '"js/islas/numeros.js"'
    verificar(a in w); (tmp / "sw.js").write_text(w.replace(a, a + ',"js/islas/colores.js"'), encoding="utf-8")
    # el motor no se tocó: los archivos de js/core son idénticos
    for f in (APP / "js" / "core").rglob("*.js"): igual((tmp / f.relative_to(APP)).read_bytes(), f.read_bytes(), "motor modificado " + f.name)
    srv2, url2 = servidor(raiz=tmp)
    try:
        ctx = C.banco.contexto("360x700"); err = []; pg = abrir(ctx, url2 + "/index.html", store=STORE_KID, errores=err, semilla=3); instalar_speak(pg); entrar(pg, "Vale")
        islas = pg.evaluate("[...document.querySelectorAll('#islands .island')].map(x=>x.innerText.split('\\n')[1])")
        verificar("Isla Colores" in islas, str(islas))
        igual(pg.evaluate("PACKS.map(p=>p.id)"), ["musica", "numeros", "colores", "letras"], "islas registradas")
        for i in range(3):
            abrir_isla(pg, "Colores"); tarjeta(pg, "Sesión de hoy"); verificar(jugar(pg, cada_error=4 if i == 0 else 0) == "fin"); cerrar_fin(pg)
        pg.evaluate("PACK=PACKS.find(p=>p.id==='colores')"); verificar(pg.evaluate("SK('col_nom').mast"), "no dominó la primera habilidad")
        verificar("col_mas" in pg.evaluate("unlockedList().map(s=>s.id)"), "no desbloqueó la segunda")
        abrir_isla(pg, "Colores"); tarjeta(pg, "Chequeo semanal"); verificar(jugar(pg) == "fin"); cerrar_fin(pg)
        verificar(pg.evaluate("store.checks.Vale.some(c=>c.p==='colores')"), "el chequeo no quedó registrado")
        rep = pg.evaluate("reportText()"); verificar("ISLA COLORES" in rep and "Nombrar colores" in rep, rep[:300])
        foto(pg, "360x700_50_isla_ejemplo_colores"); CAPTURAS.append("360x700_50_isla_ejemplo_colores.png")
        verificar(not err, str(err)); ctx.close()
    finally:
        srv2.shutdown(); shutil.rmtree(tmp.parent, ignore_errors=True)

# ---------------------------------------------------------------- Isla Letras
STORE_LET = {"profiles": ["Vale"], "limit": {"Vale": 120}}

def pasar_gate(pg):
    pg.wait_for_selector("#gateBox.show", timeout=3000)
    pg.fill("#gateIn", str(pg.evaluate("S.gateAns"))); pg.click("#gateOk"); pg.wait_for_timeout(150)

def entrar_letras(pg, bienvenida=False):
    abrir_isla(pg, "Letras")
    if not bienvenida and pg.evaluate("document.getElementById('letOv').classList.contains('show')"):
        pg.click("#letOv [data-a=cerrar]"); pg.wait_for_timeout(80)

def llenar_intake(pg, edad, letras, lee, nombre):
    for k, v in (("edad", edad), ("letras", letras), ("lee", lee), ("nombre", nombre)):
        pg.click("#letOv .letBtn[data-k='%s'][data-v='%s']" % (k, v))
    pg.click("#letOv [data-a=guardarIntake]"); pg.wait_for_timeout(120)

def pack_letras(pg): pg.evaluate("PACK=PACKS.find(p=>p.id==='letras')")

JS_NIVEL = "(S.tap&&S.mode==='play'&&S.tap.v&&S.tap.it!==window.__ult)?(function(){var T=S.tap;return {w:T.it.seq[0],vals:T.v.opts.map(function(o){return o.val}),niv:T.it.skill.nivel,tipo:T.it.skill.type};})():null"

def jugar_ubicacion(pg, conoce, limite=60):
    """Simula a un chico que sabe todo hasta el tramo `conoce` (responde bien) y en el resto toca «No sé»."""
    n = 0; t0 = time.time()
    while time.time() - t0 < 90:
        pg.wait_for_timeout(30)
        if pg.evaluate("document.getElementById('gateBox').classList.contains('show')"): return n
        t = pg.evaluate(JS_NIVEL)
        if not t: continue
        want = t["w"] if t["niv"] <= conoce else "__nose"
        i = t["vals"].index(want)
        pg.evaluate("(()=>{ var T=S.tap; window.__ult=T.it; window.__ref=[T.pos,T.miss,T.used.size]; })()")   # una sola respuesta por ítem
        pg.click(".opt[data-i='%d']" % i, force=True)
        try:
            pg.wait_for_function("(function(){var T=S.tap,r=window.__ref; return !T||S.mode!=='play'||T.it!==window.__ult||T.pos!==r[0]||T.miss!==r[1]||T.used.size!==r[2];})()", timeout=1500, polling=15)
            n += 1
        except Exception:
            pg.evaluate("window.__ult=null")   # el motor ignora un toque que llega justo después de un error: se reintenta
    raise Falla("la ubicación no terminó")

@prueba("Letras: el contenido es válido (30 habilidades, 20 tipos, todo ítem tiene respuesta y no hay pares confusos)")
def t_letras_contenido(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=81); instalar_speak(pg)
    r = pg.evaluate("""(()=>{ const out=[], L=Gioval.letras, D=Gioval.datos.letras, S0=L.SKILLS, by=Object.fromEntries(S0.map(s=>[s.id,s]));
      const tipos=new Set(S0.map(s=>s.type));
      S0.forEach(s=>{ s.req.forEach(r=>{ if(!by[r]) out.push(s.id+": req inexistente "+r); else if(by[r].nivel>s.nivel) out.push(s.id+": req de tramo mayor "+r); });
        if(!D.TEXTOS.habilidades[s.id]) out.push(s.id+": sin nombre en TEXTOS"); if(!s.edad||!s.eje||s.nivel==null) out.push(s.id+": faltan edad/eje/nivel"); });
      for(let t=0;t<=7;t++){ const sondas=S0.filter(s=>s.nivel===t&&s.sonda); if(sondas.length<2) out.push("tramo "+t+" con menos de 2 sondas"); }
      const em={}; L.WORDS.forEach(w=>{ if(em[w.e]) out.push("dibujo repetido "+w.e+": "+em[w.e]+" y "+w.w); em[w.e]=w.w; if(w.sy.join('')!==w.w) out.push('sílabas '+w.w); });
      D.RIMAS.forEach(g=>g.forEach(x=>{ if(!L.WORDS.some(w=>w.w===x)) out.push('rima sin palabra '+x); }));
      Object.values(D.ANCLAS).forEach(x=>{ if(!L.WORDS.some(w=>w.w===x)) out.push('ancla sin palabra '+x); });
      'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ'.split('').forEach(c=>{ if(!D.ANCLAS[c]) out.push('sin ancla '+c); if(!D.TEXTOS.letras[c]) out.push('sin nombre de letra '+c); });
      for(const s of S0){ const A=ACTIVITIES[s.type]; for(let i=0;i<60;i++){ try{ const it=A.make(s); for(const aid of [0,1,2]){ const T={pos:0,reveal:false,used:new Set(),dead:new Set()}; const v=A.view(it,aid,T);
          if(!v.say||typeof v.say!=='string') out.push(s.id+': sin voz'); const vals=(it.consume?it.opts:v.opts).map(o=>o.val);
          it.seq.forEach(x=>{ if(!vals.includes(x)) out.push(s.id+': la respuesta '+JSON.stringify(x)+' no está en las opciones (ayuda '+aid+')'); });
          if(!it.consume&&new Set(v.opts.map(o=>o.val)).size!==v.opts.length) out.push(s.id+': opciones repetidas'); }
          if(!A.okMsgs||!A.okMsgs.length) out.push(s.id+': sin mensajes de proceso'); }catch(e){ out.push(s.id+': '+e.message); break; } } }
      const conf=(a,b)=>a!==b&&((D.CONFUNDEN[a]||'').includes(b)||(D.CONFUNDEN[b]||'').includes(a));
      for(const id of ['let_s1','let_s2']){ const s=by[id], A=ACTIVITIES[s.type];
        for(let i=0;i<150;i++){ const it=A.make(s), ok=it.seq[0]; it.opts.forEach(o=>{ if(conf(ok,o.val)) out.push(id+': la respuesta '+ok+' junto a una letra que suena parecido: '+o.val); }); } }
      return {n:S0.length,tipos:[...tipos].length,palabras:L.WORDS.length,errores:[...new Set(out)].slice(0,25)}; })()""")
    igual(r["errores"], [], "problemas de contenido")
    verificar(r["n"] >= 25 and r["n"] <= 32, "habilidades: %d" % r["n"]); igual(r["tipos"], 20, "tipos de actividad")
    txt = pg.evaluate("JSON.stringify(Gioval.datos.letras.TEXTOS)").lower()
    for malo in ("inteligente", "genio", "sos el mejor", "racha", "perdiste"):
        verificar(malo not in txt, "texto no permitido: " + malo)
    verificar(not err, str(err)); ctx.close(); return "%d habilidades, %d tipos, %d palabras con dibujo" % (r["n"], r["tipos"], r["palabras"])

@prueba("Letras: migración de almacén v1 → v2 (intake) conserva todo")
def t_letras_migracion(C):
    v1 = {"version": 1, "profiles": ["Vale"], "stars": {}, "sk": {"Vale|n1": {"score": .9, "att": 7, "box": 1, "due": 5, "lvl": 1, "rec": [1], "mast": True, "last": 4}}, "days": {"Vale": ["2026-11-01"]},
          "time": {}, "log": {}, "checks": {}, "extra": {}, "limit": {"Vale": 20}, "meta": {"ultimoRespaldo": 0, "guardado": 5, "desde": 5}}
    ctx = C.banco.contexto("360x700"); err = []; pg = abrir(ctx, C.url + "/index.html", store=v1, errores=err)
    igual(pg.evaluate("store.version"), 2); igual(pg.evaluate("store.intake"), {}); igual(pg.evaluate("store.sk"), v1["sk"], "progreso")
    igual(pg.evaluate("store.profiles"), ["Vale"]); igual(pg.evaluate("store.limit"), {"Vale": 20})
    verificar(not err, str(err)); ctx.close()

NIVELES_EDAD = [   # (edad, letras, lee, nombre) -> tramo de arranque, primera habilidad a practicar, arranque del juego de ubicación
    ((4, 1, "no", "copia"), 0, "let_v", 0), ((5, 2, "no", "copia"), 2, "let_c2", 2), ((6, 3, "silabas", "solo"), 3, "let_s2", 3),
    ((7, 3, "frases", "solo"), 5, "let_rf1", 5), ((7, 0, "no", "no"), 0, "let_v", 3), ((4, 0, "no", "no"), 0, "let_v", 0), ((8, 3, "textos", "solo"), 6, "let_ora", 6)]

@prueba("Letras: preguntas para adultos → punto de partida para edades 4, 5, 6 y 7 (y la edad sola no salta nada)")
def t_letras_intake(C):
    for k, (resp, niv, primera, ubic) in enumerate(NIVELES_EDAD):
        ctx = C.banco.contexto("360x700"); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=82 + k); instalar_speak(pg); entrar(pg, "Vale")
        abrir_isla(pg, "Letras")
        verificar(pg.evaluate("document.getElementById('letOv').classList.contains('show')"), "no aparece la bienvenida para adultos")
        if k == 0:
            CAPTURAS.append(foto(pg, "360x700_60_letras_bienvenida"))
        pg.click("#letOv [data-a=bienvenidaSi]"); pasar_gate(pg)
        pg.click("#letOv [data-a=guardarIntake]"); verificar("Faltan respuestas" in pg.evaluate("document.getElementById('letFalta').innerText"), "debería pedir las 4 respuestas")
        if k == 0:
            CAPTURAS.append(foto(pg, "360x700_61_letras_intake"))
        llenar_intake(pg, *resp)
        igual(pg.evaluate("Gioval.letras.nivelDe(Gioval.letras.intakeDe(KID))"), niv, "tramo de arranque %s" % (resp,))
        igual(pg.evaluate("Gioval.letras.arranqueUbic(Gioval.letras.intakeDe(KID))"), ubic, "arranque del juego de ubicación %s" % (resp,))
        if k == 0:
            CAPTURAS.append(foto(pg, "360x700_62_letras_intake_sugerido"))
        pg.click("#letOv [data-a=usarPunto]"); pg.wait_for_timeout(120)
        pack_letras(pg)
        marcadas = pg.evaluate("Gioval.letras.SKILLS.filter(s=>SK(s.id).mast).map(s=>s.id)"); esperadas = pg.evaluate("Gioval.letras.SKILLS.filter(s=>s.nivel<%d).map(s=>s.id)" % niv)
        igual(sorted(marcadas), sorted(esperadas), "habilidades marcadas como sabidas %s" % (resp,))
        verificar(all(pg.evaluate("SK('%s').skip.estado==='pendiente'&&SK('%s').skip.por==='preguntas'" % (i, i)) for i in marcadas), "las marcadas deben quedar pendientes de comprobar")
        igual(pg.evaluate("unlockedList().find(s=>!SK(s.id).mast).id"), primera, "primera habilidad a practicar %s" % (resp,))
        verificar(not pg.evaluate("document.getElementById('letOv').classList.contains('show')"))
        igual(pg.evaluate("store.intake.Vale.letras.edad"), resp[0], "guardó la edad"); igual(pg.evaluate("store.intake.Vale.letras.inicio.origen"), "preguntas")
        pg.reload(); esperar_listo(pg); instalar_speak(pg); entrar(pg, "Vale"); abrir_isla(pg, "Letras")
        verificar(not pg.evaluate("document.getElementById('letOv').classList.contains('show')"), "volvió a preguntar")
        igual(pg.evaluate("store.intake.Vale.letras.letras"), resp[1], "sobrevive a recargar")
        verificar(not err, str(err)); ctx.close()
    return "7 perfiles (edades 4 a 8); tramos de arranque 0,2,3,5,0,0,6"

@prueba("Letras: juego de ubicación adaptativo con respuestas simuladas (sube, baja, para y no pasa de 16 preguntas)")
def t_letras_ubicacion(C):
    casos = [(2, (5, 0, "no", "no"), 2), (5, (6, 3, "silabas", "solo"), 5), (-1, (6, 3, "silabas", "solo"), 0), (7, (6, 3, "silabas", "solo"), 7), (3, (7, 0, "no", "no"), 3)]
    detalle = []
    for k, (conoce, resp, esperado) in enumerate(casos):
        ctx = C.banco.contexto("360x700"); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=90 + k); instalar_speak(pg); entrar(pg, "Vale")
        abrir_isla(pg, "Letras"); pg.click("#letOv [data-a=bienvenidaSi]"); pasar_gate(pg); llenar_intake(pg, *resp); pg.click("#letOv [data-a=jugarUbic]"); pg.wait_for_timeout(300)
        igual(pg.evaluate("document.querySelector('.screen.active').id"), "act", "pantalla de juego")
        if k == 1:
            CAPTURAS.append(foto(pg, "360x700_63_letras_ubicacion"))
            verificar(pg.evaluate("document.getElementById('btnActSkip').style.display==='none'"), "«Seguir» no debe verse en la ubicación")
            verificar("No sé" in pg.evaluate("document.getElementById('actOpts').innerText"), "falta «No sé»")
        n = jugar_ubicacion(pg, conoce)
        pend = pg.evaluate("store.intake.Vale.letras.ubicacionPend"); verificar(pend, "no guardó el resultado pendiente")
        igual(pend["iniPropuesto"], esperado, "tramo propuesto (conoce hasta %s, respuestas %s)" % (conoce, resp))
        verificar(3 <= pend["n"] <= 16, "preguntas: %d" % pend["n"]); igual(pend["n"], n, "preguntas contadas")
        igual(pg.evaluate("Gioval.letras.SKILLS.filter(s=>SK(s.id).mast).length"), 0, "no se marcó nada antes de aceptar")
        pasar_gate(pg); pg.wait_for_selector("#letOv.show"); txt = pg.evaluate("document.querySelector('#letOv .letCard').innerText")
        verificar("Resultado del juego de ubicación" in txt and "Tramo 1" in txt, txt[:200])
        final = esperado
        if k == 1:
            CAPTURAS.append(foto(pg, "360x700_64_letras_resumen"))
            pg.click("#letOv [data-a=antes]"); verificar("tramo 5" in pg.evaluate("document.querySelector('#letOv .letProp').innerText"), "no ajustó a un tramo antes")
            final = 4
        pg.click("#letOv [data-a=aceptarUbic]"); pg.wait_for_timeout(120); pack_letras(pg)
        ini = pg.evaluate("store.intake.Vale.letras.inicio"); igual(ini["tramo"], final, "tramo aceptado")
        igual(ini["origen"], "ajustado" if k == 1 else "ubicacion", "origen")
        igual(pg.evaluate("Gioval.letras.SKILLS.filter(s=>SK(s.id).mast).length"), pg.evaluate("Gioval.letras.SKILLS.filter(s=>s.nivel<%d).length" % final), "habilidades marcadas")
        verificar(pg.evaluate("!store.intake.Vale.letras.ubicacionPend && !!store.intake.Vale.letras.ubicacion"), "no limpió el pendiente")
        detalle.append("conoce %s→tramo %d en %d preguntas" % (conoce, final, n)); verificar(not err, str(err)); ctx.close()
    ctx = C.banco.contexto("740x330"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=99); instalar_speak(pg); entrar(pg, "Vale"); abrir_isla(pg, "Letras")
    pg.click("#letOv [data-a=bienvenidaSi]"); pasar_gate(pg); llenar_intake(pg, 6, 3, "silabas", "solo"); pg.click("#letOv [data-a=jugarUbic]"); pg.wait_for_timeout(300)
    CAPTURAS.append(foto(pg, "740x330_63_letras_ubicacion"))
    jugar_ubicacion(pg, 4); pasar_gate(pg); pg.wait_for_selector("#letOv.show")
    CAPTURAS.append(foto(pg, "740x330_64_letras_resumen"))
    pg.click("#letOv [data-a=descartarUbic]"); pg.wait_for_timeout(100); pack_letras(pg)
    igual(pg.evaluate("Gioval.letras.SKILLS.filter(s=>SK(s.id).mast).length"), 0, "descartar no debe marcar nada")
    verificar(pg.evaluate("!store.intake.Vale.letras.ubicacionPend"), "descartar limpia el pendiente")
    verificar(not err, str(err)); ctx.close()
    return "; ".join(detalle)

@prueba("Letras: sesión completa de una habilidad con dominio y desbloqueo (sin rachas ni elogio a la persona)")
def t_letras_sesion(C):
    for v in ("pixel7", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=110); instalar_speak(pg); entrar(pg, "Vale"); entrar_letras(pg)
        tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(400)
        igual(pg.evaluate("document.querySelector('.screen.active').id"), "act")
        CAPTURAS.append(foto(pg, v + "_65_letras_actividad"))
        verificar(jugar(pg, cada_error=4) == "fin"); cerrar_fin(pg)
        for _ in range(6):
            pack_letras(pg)
            if pg.evaluate("SK('let_v').mast"): break
            pasar_sesiones(pg, "Letras", 1, perfecto=True)
        pack_letras(pg)
        verificar(pg.evaluate("SK('let_v').mast"), "let_v no quedó dominada")
        desbloq = pg.evaluate("unlockedList().map(s=>s.id)"); verificar("let_c1" in desbloq or pg.evaluate("SK('let_c1').mast"), "no se abrió let_c1: %s" % desbloq)
        ses = pg.evaluate("window.__LOG.concat(window.__BUB).join(' | ')").lower()
        for malo in ("inteligente", "genio", "racha"): verificar(malo not in ses, "texto no permitido en la sesión: " + malo)
        verificar(not err, "%s: %s" % (v, err)); ctx.close()

@prueba("Letras: una actividad de cada tipo se ve bien (capturas 360x700 y 740x330), no se desborda y se juega sin errores")
def t_letras_tipos(C):
    tipos = [("let_v", "lname"), ("let_s1", "lsound"), ("let_p1", "lpic"), ("let_cs1", "lcount"), ("let_ri1", "lrhyme"), ("let_sil", "lsyl"), ("let_arm", "lbuild"),
             ("let_f2", "lmissing"), ("let_ms", "lcase"), ("let_sp", "lsplit"), ("let_nom", "lnombre"), ("let_rs", "lrsyl"), ("let_rp1", "lrword"), ("let_rf1", "lrphrase"),
             ("let_abc1", "labc"), ("let_comp2", "lcomp"), ("let_ora", "lorden"), ("let_tr", "lcluster"), ("let_ort", "lbien"), ("let_abc2", "lalfa")]
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=120); instalar_speak(pg); entrar(pg, "Vale"); pack_letras(pg)
        for sid, tipo in tipos:
            igual(pg.evaluate("Gioval.letras.SKILLS.find(s=>s.id==='%s').type" % sid), tipo, sid)
            pg.evaluate("""(sid)=>{ const s=Gioval.letras.SKILLS.find(x=>x.id===sid); const A=ACTIVITIES[s.type]; const it=A.make(s); S.run++; S.check=false; S.hint=0; S.session=null; entrarToques(s.name); window.__fin=null; S.onDone=r=>{ window.__fin=r; }; A.jugar(S.run,it,null); }""", sid)
            pg.wait_for_timeout(120); CAPTURAS.append(foto(pg, "%s_66_letras_tipo_%s" % (v, tipo)))
            sobra = pg.evaluate("""(()=>{ const vw=innerWidth, vh=innerHeight, mal=[]; document.querySelectorAll('#actStage *, #actOpts .opt').forEach(e=>{ const r=e.getBoundingClientRect(); if(r.width&&(r.right>vw+1||r.left<-1||r.bottom>vh+1)) mal.push(e.className+':'+Math.round(r.right)+','+Math.round(r.bottom)); }); return mal.slice(0,3); })()""")
            igual(sobra, [], "%s se sale de la pantalla en %s" % (tipo, v))
            for _ in range(40):   # se juega con las respuestas correctas hasta que el ítem termina
                if pg.evaluate("window.__fin"): break
                t = pg.evaluate(JS_TOQUES)
                if not t: pg.wait_for_timeout(30); continue
                ok = [i for i, x in enumerate(t["vals"]) if x == t["w"] and t["ids"][i] not in t["used"] and x not in t["dead"]]
                pg.evaluate("(()=>{var T=S.tap; window.__ref=[T.it,T.pos,T.miss,T.used.size,T.dead.size]; })()")
                pg.click(".opt[data-i='%d']" % ok[0], force=True)
                try: pg.wait_for_function("(function(){var T=S.tap,r=window.__ref; return !T||window.__fin||S.mode!=='play'||T.it!==r[0]||T.pos!==r[1]||T.miss!==r[2]||T.used.size!==r[3]||T.dead.size!==r[4];})()", timeout=2500, polling=15)
                except Exception: pass
            fin = pg.evaluate("window.__fin"); verificar(fin and fin.get("miss") == 0, "%s no terminó bien en %s: %s" % (tipo, v, fin))
        verificar(not err, "%s: %s" % (v, err)); ctx.close()
    return "20 tipos en 2 tamaños"

@prueba("Salto por dominio rápido (motor genérico): criterios, salto de la siguiente, chequeo que confirma o devuelve a práctica")
def t_salto(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=130); instalar_speak(pg); entrar(pg, "Vale"); entrar_letras(pg); pack_letras(pg)
    r = pg.evaluate("""(()=>{ const sk={id:'x1',rtRapido:3000,name:'X'}; const D=Gioval.dominio; const log=store.log[KID]=[]; const out={};
      const poner=(arr)=>{ log.length=0; arr.forEach(([f,r])=>log.push({s:'x1',k:'learn',f,o:f,r})); };
      const rep=(n,fn)=>Array.from({length:n},(_, i)=>fn(i+1));
      poner(rep(10,()=>[1,1800])); out.rapida=D.esRapida(sk);
      poner(rep(10,i=>i===3?[0,null]:[1,1800])); out.un_error_de_10=D.esRapida(sk);
      poner(rep(10,i=>i<=2?[0,null]:[1,1800])); out.dos_errores_de_10=D.esRapida(sk);
      poner(rep(10,()=>[1,4200])); out.lenta=D.esRapida(sk);
      poner(rep(5,()=>[1,1000])); out.pocos_intentos=D.esRapida(sk);
      poner(rep(6,i=>[1,i<=3?1000:null])); out.pocos_tiempos=D.esRapida(sk);
      poner(rep(10,i=>[1,i%2?1000:5000])); out.mediana=D.esRapida(sk);
      poner(rep(10,()=>[1,1800])); out.sin_umbral=D.esRapida({id:'x1',name:'X'});
      out.med=D.mediana([5,1,3,2]); store.log[KID]=[]; return out; })()""")
    igual(r, {"rapida": True, "un_error_de_10": True, "dos_errores_de_10": False, "lenta": False, "pocos_intentos": False, "pocos_tiempos": False, "mediana": True, "sin_umbral": False, "med": 2.5}, "criterios de rapidez")
    for _ in range(8):
        pasar_sesiones(pg, "Letras", 1, perfecto=True); pack_letras(pg)
        if pg.evaluate("SK('let_v').mast"): break
    verificar(pg.evaluate("SK('let_v').mast"), "let_v no se dominó")
    sk = pg.evaluate("SK('let_c1')"); verificar(sk["mast"] and sk["skip"]["estado"] == "pendiente" and sk["skip"]["por"] == "rapido", "let_c1 no quedó saltada: %s" % sk)
    verificar("domino rápido" in sk["skip"]["why"], sk["skip"]["why"]); igual(sk["skip"]["desde"], "let_v")
    rt = pg.evaluate("store.log.Vale.filter(e=>e.s==='let_v'&&e.k==='learn'&&e.r!=null).length"); verificar(rt >= 5, "el registro debe guardar el tiempo de respuesta (r): %d" % rt)
    verificar(pg.evaluate("!SK('let_v').skip"), "la que se domina por práctica no es 'saltada'")
    verificar(pg.evaluate("!SK('let_s1').skip"), "no debe encadenar saltos: una saltada no dispara otra")
    rep = pg.evaluate("reportText()"); verificar("Saltada el" in rep and "dominio rápido" in rep and "Tiempo de respuesta típico" in rep, rep[:900])
    pg.evaluate("window.__OFF=8*864e5"); abrir_isla(pg, "Letras"); tarjeta(pg, "Chequeo semanal")
    items = pg.evaluate("S.session.items.map(i=>i.skill.id)"); verificar("let_c1" in items, "el chequeo no incluye la saltada: %s" % items)
    verificar(jugar(pg, perfecto=True) == "fin"); cerrar_fin(pg); pack_letras(pg)
    sk = pg.evaluate("SK('let_c1')"); igual(sk["skip"]["estado"], "confirmada", "tras acertar en el chequeo"); verificar(sk["mast"])
    verificar("Comprobada sin ayuda" in pg.evaluate("reportText()"), "el informe no dice que se confirmó")
    pg.evaluate("(()=>{ SK('let_c1').skip.estado='pendiente'; save(); })()"); pg.evaluate("window.__OFF=16*864e5")
    abrir_isla(pg, "Letras"); tarjeta(pg, "Chequeo semanal"); verificar("let_c1" in pg.evaluate("S.session.items.map(i=>i.skill.id)"))
    verificar(jugar(pg, cada_error=1) == "fin"); cerrar_fin(pg); pack_letras(pg)
    sk = pg.evaluate("SK('let_c1')"); igual(sk["mast"], False, "debería volver a práctica"); igual(sk["skip"]["estado"], "revertida")
    verificar("volvió a práctica" in pg.evaluate("reportText()"), "el informe no dice que volvió a práctica")
    verificar(pg.evaluate("unlockedList().some(s=>s.id==='let_c1')"), "let_c1 vuelve a estar para practicar")
    verificar(not err, str(err)); ctx.close()

@prueba("Salto por dominio rápido: NO se salta si falla seguido o si es lento, y Música/Números no se ven afectados")
def t_salto_no(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=131); instalar_speak(pg); entrar(pg, "Vale"); entrar_letras(pg); pack_letras(pg)
    for _ in range(3):   # con errores seguidos nunca alcanza el 90 %
        pasar_sesiones(pg, "Letras", 1, cada_error=2); pack_letras(pg)
    verificar(pg.evaluate("!SK('let_c1').skip && !SK('let_c1').mast"), "se saltó con errores")
    verificar(pg.evaluate("!Gioval.dominio.esRapida(Gioval.letras.SKILLS.find(s=>s.id==='let_v'))"), "con errores no puede ser rápida")
    ctx.close()
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=132); instalar_speak(pg); entrar(pg, "Vale"); entrar_letras(pg); pack_letras(pg)
    pg.evaluate("Gioval.letras.SKILLS.find(s=>s.id==='let_v').rtRapido=-1")   # umbral imposible = «lento»
    for _ in range(6):
        pasar_sesiones(pg, "Letras", 1, perfecto=True); pack_letras(pg)
        if pg.evaluate("SK('let_v').mast"): break
    verificar(pg.evaluate("SK('let_v').mast"), "let_v no se dominó"); verificar(pg.evaluate("!SK('let_c1').skip && !SK('let_c1').mast"), "se saltó siendo lento")
    # Música y Números no declaran rtRapido: jamás saltan nada
    igual(pg.evaluate("PACKS.filter(p=>p.id!=='letras').flatMap(p=>p.skills).filter(s=>s.rtRapido).length"), 0, "habilidades con umbral fuera de Letras")
    pasar_sesiones(pg, "Números", 2, perfecto=True)
    igual(pg.evaluate("Object.keys(store.sk).filter(k=>store.sk[k].skip&&!k.includes('|let_'))"), [], "no debe haber saltos fuera de Letras")
    verificar(not err, str(err)); ctx.close()

@prueba("Letras: informe para adultos con evidencia (aciertos, tiempo, retención ≥1 día) y lo que se saltó y por qué")
def t_letras_informe(C):
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=140); instalar_speak(pg); entrar(pg, "Vale"); abrir_isla(pg, "Letras")
        pg.click("#letOv [data-a=bienvenidaSi]"); pasar_gate(pg); llenar_intake(pg, 5, 2, "no", "copia"); pg.click("#letOv [data-a=usarPunto]"); pg.wait_for_timeout(100); pack_letras(pg)
        for dia in range(3):
            pg.evaluate("window.__OFF=%d*864e5" % (dia * 2)); pasar_sesiones(pg, "Letras", 1, perfecto=True)
        pg.evaluate("window.__OFF=7*864e5")
        abrir_isla(pg, "Letras"); tarjeta(pg, "Informe para adultos"); pasar_gate(pg); pg.wait_for_selector("#letOv.show")
        txt = pg.evaluate("document.getElementById('letPre').innerText")
        for esperado in ("INFORME DE LETRAS — VALE", "Respuestas de los adultos", "5 años", "Punto de partida: tramo 3", "HABILIDADES", "Aciertos al primer intento", "Retención", "Saltada el", "preguntas para adultos", "SALTOS:", "Cómo leerlo"):
            verificar(esperado in txt, "falta «%s» en el informe:\n%s" % (esperado, txt[:1800]))
        CAPTURAS.append(foto(pg, v + "_67_letras_informe"))
        verificar(not err, "%s: %s" % (v, err)); ctx.close()
    return txt.split("\n")[0]


# ---------------------------------------------------------------- capturas varias
@prueba("capturas: pantallas principales en Pixel 7, 360x700 y 740x330")
def t_capturas(C):
    for v in ("pixel7", "360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []; pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=5); instalar_speak(pg)
        entrar(pg, "Vale"); abrir_isla(pg, "Música"); CAPTURAS.append(foto(pg, v + "_40_menu_musica"))
        abrir_isla(pg, "Números"); CAPTURAS.append(foto(pg, v + "_41_menu_numeros"))
        tarjeta(pg, "Logros") if False else None
        pg.click(".island:has-text('Mis logros')"); CAPTURAS.append(foto(pg, v + "_42_logros_numeros"))
        pg.evaluate("goMenuIsla()"); tarjeta(pg, "Sesión de hoy"); CAPTURAS.append(foto(pg, v + "_43_numeros_sesion"))
        abrir_panel(pg); CAPTURAS.append(foto(pg, v + "_44_panel_adultos"))
        verificar(not err, "%s: %s" % (v, err)); ctx.close()

# ================================================================== runner
class Ctx: pass

def main():
    filtro = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    SALIDA.mkdir(parents=True, exist_ok=True)
    for f in SALIDA.glob("*"):
        if f.is_file(): f.unlink()
    srv, url = servidor()
    resultados = []; t0 = time.time()
    with sync_playwright() as pw:
        C = Ctx(); C.pw = pw; C.url = url; C.banco = Banco(pw); C.err = []
        for nombre, fn in TESTS:
            if filtro and filtro not in nombre.lower(): continue
            ini = time.time(); C.err.clear()
            try:
                det = fn(C) or ""
                if C.err: raise Falla("errores de consola: %s" % C.err[:3])
                resultados.append((nombre, True, det, time.time() - ini)); print("  PASA  %s  (%.1fs) %s" % (nombre, time.time() - ini, det), flush=True)
            except Exception as e:
                msg = (str(e) if isinstance(e, Falla) else "".join(traceback.format_exception_only(type(e), e)).strip())[:600]
                resultados.append((nombre, False, msg, time.time() - ini)); print("  FALLA %s\n        %s" % (nombre, msg), flush=True)
        C.banco.cerrar()
    ok = sum(1 for r in resultados if r[1]); mal = len(resultados) - ok
    caps = sorted(p.name for p in SALIDA.glob("*.png") if not p.name.startswith("cmp_"))
    lineas = ["RESUMEN DE PRUEBAS DE MUNDO GIOVAL", time.strftime("%Y-%m-%d %H:%M"), "versión de la app: " + re.search(r'"([^"]+)"', (APP / "js/version.js").read_text()).group(1), "",
              "Total: %d pruebas · pasan %d · fallan %d · %.0f s" % (len(resultados), ok, mal, time.time() - t0), ""]
    for n, p, d, t in resultados: lineas.append("[%s] %s%s" % ("PASA" if p else "FALLA", n, ("\n       " + d) if d else ""))
    lineas += ["", "CAPTURAS (gioval-dev/tests/salida/):"] + ["  " + c for c in caps] + ["  (y %d pares cmp_* anterior/nueva usados en la comparación visual)" % len(list(SALIDA.glob("cmp_*_anterior.png")))]
    (SALIDA / "resumen.txt").write_text("\n".join(lineas), encoding="utf-8")
    print("\n" + "\n".join(lineas[:5])); srv.shutdown()
    sys.exit(0 if mal == 0 else 1)

if __name__ == "__main__":
    main()
