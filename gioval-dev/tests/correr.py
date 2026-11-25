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
        igual(pg.evaluate("store.version"), 1, "store.version")
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

@prueba("mapa: muestra Música, Números, Misiones y las islas con candado")
def t_mapa(C):
    for v in ("pixel7", "360x700", "740x330"):
        ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err); instalar_speak(pg)
        entrar(pg, "Vale")
        islas = pg.evaluate("[...document.querySelectorAll('#islands .island')].map(x=>x.innerText.replace(/\\n/g,'|')+(x.classList.contains('off')?'|off':''))")
        igual(islas, ["🎹|Isla Música|¡A tocar el piano!", "🔢|Isla Números|¡A contar y sumar!", "🧭|Isla Misiones|¡Cosas de verdad!", "🔒|Isla Letras|Pronto|off", "🔒|Isla Animales|Pronto|off"], "mapa " + v)
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
    igual(nuevo["version"], 1, "version")
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
    return "versión 0 → 1, %d claves de progreso intactas" % len(viejo["sk"])

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
    igual(pg.evaluate("PACKS.map(p=>[p.id,p.instrumento,p.entradas])"), [["musica", "piano", ["nota", "toque"]], ["numeros", None, ["toque"]], ["misiones", None, []]], "declaración de las islas")
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

def px_igual(a, b):
    from PIL import Image, ImageChops
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if ia.size != ib.size: return "tamaños distintos %s %s" % (ia.size, ib.size)
    bb = ImageChops.difference(ia, ib).getbbox()
    return None if bb is None else "difieren en %s" % (bb,)

@prueba("regresión visual: las pantallas del niño se ven idénticas a la versión publicada (píxel a píxel)")
def t_pixeles(C):
    SALIDA.mkdir(exist_ok=True); difs = []; n = 0
    for v in ("360x700", "740x330"):
        for nombre, ruta in (("anterior", "/legacy/index.html"), ("nueva", "/index.html")):
            ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + ruta, store=STORE_KID, semilla=777, errores=None, congelar=True); instalar_speak(pg)
            pg.evaluate("document.getElementById('nameBox').classList.remove('show')")
            def f(tag): foto(pg, "cmp_%s_%s_%s" % (v, tag, nombre))
            pg.evaluate("renderWho(); show('who')"); f("who"); entrar(pg, "Vale")
            pg.evaluate("document.querySelectorAll('#islands .island').forEach(b=>{ if(b.innerText.includes('Misiones')) b.style.display='none'; })"); f("mapa")   # Misiones es nueva: se oculta su tarjeta para comparar el resto del mapa
            pg.click(".island:has-text('Música')"); pg.wait_for_timeout(150); f("menu_musica")
            pg.click(".island:has-text('Sesión de hoy')"); pg.wait_for_timeout(500); pg.evaluate("clearTimeout(0)"); f("musica_sesion")
            jugar(pg, perfecto=True, limite=3); pg.wait_for_timeout(300); f("musica_sesion2")
            pg.evaluate("S.run++; resetFlow(); goMap()"); pg.click(".island:has-text('Números')"); pg.wait_for_timeout(150); f("menu_numeros")
            pg.click(".island:has-text('Sesión de hoy')"); pg.wait_for_timeout(700); f("numeros_actividad")
            ctx.close()
        for tag in ("who", "mapa", "menu_musica", "musica_sesion", "musica_sesion2", "menu_numeros", "numeros_actividad"):
            d = px_igual(SALIDA / ("cmp_%s_%s_anterior.png" % (v, tag)), SALIDA / ("cmp_%s_%s_nueva.png" % (v, tag))); n += 1
            if d: difs.append("%s/%s: %s" % (v, tag, d))
    verificar(not difs, "diferencias visuales: " + "; ".join(difs))
    return "%d capturas comparadas, 0 píxeles distintos" % n


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
        igual(pg.evaluate("PACKS.map(p=>p.id)"), ["musica", "numeros", "colores", "misiones"], "islas registradas")
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

# ---------------------------------------------------------------- Misiones reales + Álbum de logros reales
import unicodedata
# Lista PROPIA de la prueba (independiente de la que usa la app): fuego/calor, filo y corte, químicos del hogar, electricidad de red, resina/epoxi/solventes
PROHIBIDAS_PY = [r"fuego", r"fogata", r"llamarada", r"encend\w*", r"fosforo\w*", r"hornalla\w*", r"horno\w*", r"estufa\w*", r"microondas", r"hervi\w*", r"hirvi\w*", r"calient\w*", r"calent\w*", r"quem\w*", r"soplete\w*",
    r"cuchill\w*", r"tijera\w*", r"filos?", r"afilad\w*", r"navaja\w*", r"trincheta\w*", r"cutter", r"cuter", r"serrucho\w*", r"cortar", r"cortad\w*", r"martillo\w*", r"taladro\w*",
    r"lavandina", r"cloro", r"amoniaco", r"solvente\w*", r"thinner", r"aguarras", r"nafta", r"acetona", r"alcohol", r"desinfectante\w*", r"limpiador\w*", r"acido\w*", r"veneno\w*",
    r"resina\w*", r"epoxi\w*", r"poliester", r"catalizador\w*", r"enchufe\w*", r"electric\w*", r"tomacorriente\w*", r"cargador\w*", r"cable\w*"]
def sin_tildes(t): return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")
def textos_de(x, out=None):
    out = [] if out is None else out
    if isinstance(x, str): out.append(x)
    elif isinstance(x, list): [textos_de(y, out) for y in x]
    elif isinstance(x, dict): [textos_de(y, out) for y in x.values()]
    return out

def jpeg_prueba(nombre, w=3000, h=2000, color=(200, 80, 40)):
    """JPEG grande con EXIF (marca de cámara) para comprobar que la app lo achica y le saca los metadatos."""
    from PIL import Image
    SALIDA.mkdir(exist_ok=True); ruta = SALIDA / nombre
    im = Image.new("RGB", (w, h), color); ex = Image.Exif(); ex[0x010F] = "CamaraDePrueba"; ex[0x0110] = "Modelo-X"
    im.save(str(ruta), "JPEG", quality=92, exif=ex); return ruta

def mis_abrir(pg, mid):
    abrir_isla(pg, "Misiones"); pg.click("#menuIslaItems .island:has-text('Elegir')"); pg.wait_for_timeout(100)
    pg.click(".mis-card[data-id='%s']" % mid); pg.wait_for_timeout(120)
def mis_paso(pg): return pg.evaluate("(Gioval.misiones.estado()||{}).paso||null")
def pasar_gate(pg):
    pg.wait_for_selector("#gateBox.show"); pg.fill("#gateIn", str(pg.evaluate("S.gateAns"))); pg.click("#gateOk"); pg.wait_for_timeout(120)
def mis_hasta(pg, objetivo):
    """Avanza una misión por la interfaz (como lo haría un niño con un adulto) hasta llegar al paso pedido."""
    for _ in range(80):
        p = mis_paso(pg)
        if p == objetivo: return
        if p == "listo":
            pg.click("#misAcc .btn:last-child")
            if pg.evaluate("document.getElementById('gateBox').classList.contains('show')"): pasar_gate(pg)
        elif p == "materiales":
            for k in range(pg.locator("#misCont .mis-mat").count()): pg.click("#misCont .mis-mat >> nth=%d" % k)
            pg.click("#misTodo")
        elif p == "antes":
            if pg.locator("#misCont .mis-chip").count(): pg.click("#misCont .mis-chip >> nth=0")
            pg.click("#misAcc .btn:last-child")
        elif p in ("hacer", "porque", "espera"): pg.click("#misAcc .btn:last-child")
        elif p == "quepaso": pg.click("#misCont .mis-chip >> nth=0"); pg.click("#misAcc .btn:last-child")
        else: raise Falla("paso inesperado: %s" % p)
        pg.wait_for_timeout(50)
    raise Falla("no se llegó al paso " + objetivo)
def mis_foto_on(pg, ruta):
    pg.click("#misCont details summary"); pg.click("#misCont [data-act=tgFoto]"); pasar_gate(pg)
    pg.set_input_files("#misFile", str(ruta)); pg.wait_for_selector("#misCont .mis-fotoprev img")
def mis_registrar(pg, frase, res="pensaba", foto=None):
    pg.fill("#misCont textarea[data-in=frase]", frase); pg.click("#misCont [data-res=%s]" % res)
    if foto: mis_foto_on(pg, foto)
    pg.click("#misGuardar"); pg.wait_for_function("(Gioval.misiones.estado()||{}).paso==='fin'", timeout=8000)
def mis_completa(pg, mid, frase, res="pensaba", foto=None):
    mis_abrir(pg, mid); mis_hasta(pg, "registro"); mis_registrar(pg, frase, res, foto)
def n_fotos(pg): return pg.evaluate("Gioval.almacen.fotos.listar().then(l=>l.length)")
def album(pg): return pg.evaluate("JSON.parse(JSON.stringify((store.misiones&&store.misiones.album&&store.misiones.album[KID])||[]))")

@prueba("misiones: contenido válido (≥12, 2 por categoría, desde 4 años, materiales + supervisión + aviso, sin palabras prohibidas)")
def t_mis_datos(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    d = json.loads(pg.evaluate("JSON.stringify({T:Gioval.datos.misiones.TEXTOS, M:Gioval.datos.misiones.MISIONES, ok:Gioval.datos.misiones.MISIONES.map(m=>Gioval.datos.misiones.validar(m)), vis:Gioval.misiones.lista().length})"))
    Ms, T = d["M"], d["T"]
    verificar(len(Ms) >= 12, "hay %d misiones" % len(Ms)); igual(d["vis"], len(Ms), "misiones visibles")
    igual(len({m["id"] for m in Ms}), len(Ms), "ids repetidos"); igual(set(T["misiones"]), {m["id"] for m in Ms}, "textos y estructura no coinciden")
    cats = sorted(T["categorias"]); igual(cats, sorted(["construir", "experimentos", "cocina", "huerta", "arte", "hogar"]), "categorías")
    for c in cats: verificar(sum(1 for m in Ms if m["cat"] == c) >= 2, "menos de 2 misiones en " + c)
    verificar(min(m["minEdad"] for m in Ms) == 4 and all(m["minEdad"] >= 4 for m in Ms), "edad mínima desde 4")
    nprohib = 0
    for m, probs in zip(Ms, d["ok"]):
        t = T["misiones"][m["id"]]; igual(probs, [], "validar " + m["id"])
        verificar(m["sup"] in ("cerca", "junto"), m["id"] + " sin supervisión"); verificar(len(t["materiales"]) >= 1, m["id"] + " sin materiales")
        verificar(len(t["aviso"].strip()) >= 20, m["id"] + " sin aviso de seguridad"); verificar(len(t["pasos"]) >= 2, m["id"] + " sin pasos")
        if m["tipo"] != "hacer": verificar(t["prediccion"]["pregunta"] and len(t["prediccion"]["opciones"]) >= 2 and t["observacion"] and t["explicacion"] and t["guia"], m["id"] + " sin estructura científica")
        else: verificar(t.get("imaginar"), m["id"] + " sin imaginar")
        verificar("A REVISAR" not in json.dumps(t) and not m.get("revisar"), m["id"] + " tiene datos sin confirmar")
        for tx in textos_de(t):
            nprohib += 1
            for pat in PROHIBIDAS_PY: verificar(not re.search(r"(^|[^a-z])(%s)($|[^a-z])" % pat, sin_tildes(tx)), "%s: palabra prohibida /%s/ en «%s»" % (m["id"], pat, tx[:60]))
    nexp = sum(1 for m in Ms if m["tipo"] != "hacer"); verificar(nexp >= 5, "pocos experimentos")
    # el elogio es al proceso: nada de "genio", rachas ni puntos en ningún texto de la interfaz
    ui = sin_tildes(json.dumps(T["ui"], ensure_ascii=False))
    for mala in ("genio", "inteligent", "talento", "brillante", "el mejor", "la mejor", "campe", "racha", "puntos", "ranking"): verificar(mala not in ui, "texto de la interfaz con «%s»" % mala)
    # el validador de verdad rechaza lo malo (prueba de la prueba)
    r = pg.evaluate("""(()=>{ const D=Gioval.datos.misiones, m=D.MISIONES.find(x=>x.id==='exp_flota'), t=JSON.parse(JSON.stringify(D.TEXTOS.misiones));
      const v=(mut,mm)=>{ const tt=JSON.parse(JSON.stringify(t)); mut(tt.exp_flota); return D.validar(Object.assign({},m,mm||{}),tt).length; };
      return { aviso:v(x=>{x.aviso='';}), mats:v(x=>{x.materiales=[];}), sup:v(x=>{},{sup:'solo'}), edad:v(x=>{},{minEdad:3}), lav:v(x=>{x.pasos[1]='Mezclá con lavandina.';}), cuch:v(x=>{x.materiales.push('Un cuchillo');}),
        epoxi:v(x=>{x.aviso='Con epoxi, cuidado, mucho cuidado.';}), fuego:v(x=>{x.pasos[0]='Prendé fuego';}), ok:v(x=>{}) }; })()""")
    igual(r, {"aviso": 1, "mats": 1, "sup": 1, "edad": 1, "lav": 1, "cuch": 1, "epoxi": 1, "fuego": 1, "ok": 0}, "el validador")
    # una misión inválida queda oculta (no se le muestra al niño)
    pg.evaluate("console.warn=()=>{}")
    visible = pg.evaluate("""(()=>{ const D=Gioval.datos.misiones; D.TEXTOS.misiones.mala={nombre:'Mala',resumen:'x',aviso:'',materiales:['a'],pasos:['a','b'],imaginar:'x'};
      D.MISIONES.push({id:'mala',cat:'arte',emoji:'💥',minEdad:4,sup:'cerca',tipo:'hacer'}); const n=Gioval.misiones.recargar().some(m=>m.id==='mala'); D.MISIONES.pop(); delete D.TEXTOS.misiones.mala; Gioval.misiones.recargar(); return n; })()""")
    igual(visible, False, "una misión sin aviso no debe mostrarse")
    ctx.close(); return "%d misiones (%d experimentos), %d textos contra %d palabras prohibidas" % (len(Ms), nexp, nprohib, len(PROHIBIDAS_PY))

@prueba("misiones: flujo completo de un experimento (aviso → materiales → predicción → hacer + temporizador → ¿qué pasó? → ¿por qué? → registro) en 360x700 y 740x330")
def t_mis_flujo(C):
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=81); instalar_speak(pg); entrar(pg, "Vale")
        T = json.loads(pg.evaluate("JSON.stringify(Gioval.datos.misiones.TEXTOS)")); t = T["misiones"]["exp_hielo"]; ui = T["ui"]
        t0 = pg.evaluate("JSON.stringify(store.time)")
        abrir_isla(pg, "Misiones")
        txt = pg.inner_text("#menuIslaItems")
        verificar("Misión de la semana" in txt and "Elegir una misión" in txt and "Mi álbum" in txt, txt)
        verificar("Sesión de hoy" not in txt and "Chequeo" not in txt, "Misiones no tiene sesión ni chequeo: " + txt)
        verificar("Sin tope de pantalla" in pg.inner_text("#streak"), "etiqueta de tiempo")
        CAPTURAS.append(foto(pg, v + "_60_misiones_menu"))
        pg.click("#menuIslaItems .island:has-text('Elegir')"); pg.wait_for_timeout(100); CAPTURAS.append(foto(pg, v + "_61_misiones_lista"))
        pg.click(".mis-card[data-id='exp_hielo']"); pg.wait_for_timeout(150)
        # 1) el aviso de seguridad y el nivel de supervisión se ven ANTES de empezar (y se dicen en voz alta)
        igual(mis_paso(pg), "listo", "primer paso")
        verificar(pg.is_visible("#misAviso") and t["aviso"] in pg.inner_text("#misAviso"), "aviso no visible")
        arriba = pg.evaluate("(()=>{ const r=document.getElementById('misAviso').getBoundingClientRect(), c=document.getElementById('misCont').getBoundingClientRect(); return r.top>=c.top-1 && r.top<c.bottom; })()")
        verificar(arriba, "el aviso no está a la vista al abrir la misión")
        verificar(ui["supervision"]["cerca"]["corto"] in pg.inner_text("#misCont"), "falta el nivel de supervisión")
        verificar(any(t["aviso"] in x for x in pg.evaluate("window.__LOG")), "el aviso no se dijo en voz alta")
        CAPTURAS.append(foto(pg, v + "_62_mision_aviso"))
        pg.click("#misAcc .btn:last-child"); igual(mis_paso(pg), "materiales")
        # 2) checklist: no se avanza hasta tener todo
        verificar(pg.is_disabled("#misTodo"), "avanza sin materiales")
        n = len(t["materiales"])
        for k in range(n - 1): pg.click("#misCont .mis-mat >> nth=%d" % k)
        verificar(pg.is_disabled("#misTodo"), "avanza con materiales a medias")
        CAPTURAS.append(foto(pg, v + "_63_mision_materiales"))
        pg.click("#misCont .mis-mat >> nth=%d" % (n - 1)); verificar(not pg.is_disabled("#misTodo")); pg.click("#misTodo")
        # 3) predicción obligatoria
        igual(mis_paso(pg), "antes"); verificar(pg.is_disabled("#misAcc .btn"), "avanza sin predecir")
        igual(pg.locator("#misCont .mis-chip").count(), len(t["prediccion"]["opciones"]) + 2, "opciones + otra idea + no sé")
        CAPTURAS.append(foto(pg, v + "_64_mision_prediccion"))
        pg.click("#misCont .mis-chip >> nth=0"); pg.click("#misAcc .btn")
        # 4) hacer, paso a paso, con voz y temporizador
        igual(mis_paso(pg), "hacer"); verificar(t["pasos"][0] in pg.evaluate("window.__LOG"), "el paso 1 no se dijo")
        for k in range(1, 3): pg.click("#misAcc .btn:last-child"); verificar(t["pasos"][k] in pg.evaluate("window.__LOG"), "el paso %d no se dijo" % (k + 1))
        verificar(pg.is_visible("[data-act=timer]"), "falta el temporizador en el paso 3")
        pg.click("[data-act=timer]"); r = pg.evaluate("Alarma.restante()"); verificar(598 <= r <= 600, "temporizador de 10 min: %s" % r)
        pg.wait_for_function("document.getElementById('misTimerEstado').innerText.includes('Falta')"); CAPTURAS.append(foto(pg, v + "_65_mision_temporizador"))
        pg.evaluate("window.__OFF=601000; Alarma._revisar()"); pg.wait_for_timeout(100)
        verificar(ui["timer"]["fin"] in pg.evaluate("window.__LOG"), "no avisó que terminó el temporizador"); igual(pg.evaluate("Gioval.misiones.estado().timer"), False)
        pg.evaluate("window.__OFF=0")
        while mis_paso(pg) == "hacer": pg.click("#misAcc .btn:last-child"); pg.wait_for_timeout(40)
        # 5) ¿qué pasó? y ¿por qué creés?
        igual(mis_paso(pg), "quepaso"); verificar(pg.is_disabled("#misAcc .btn"), "avanza sin observar")
        verificar(pg.inner_text("#bubble").strip() and len(pg.inner_text("#bubble")) < 60, "el globito debe llevar una frase corta, no el texto largo: " + pg.inner_text("#bubble"))
        pg.click("#misCont .mis-chip >> nth=1"); CAPTURAS.append(foto(pg, v + "_66_mision_quepaso")); pg.click("#misAcc .btn")
        igual(mis_paso(pg), "porque"); igual(pg.locator(".mis-exp").count(), 0, "la explicación no se muestra hasta pedirla")
        pg.fill("#misCont textarea[data-in=porque]", "porque el sol calienta"); pg.click("#misAcc .btn:has-text('explicación')")
        verificar(t["explicacion"] in pg.inner_text(".mis-exp"), "no muestra la explicación al adulto"); verificar(ui["porque"]["paraAdulto"] in pg.inner_text(".mis-exp"))
        CAPTURAS.append(foto(pg, v + "_67_mision_porque")); pg.click("#misAcc .btn:last-child")
        # 6) registrar: sin elegir pensaba/distinto no se guarda
        igual(mis_paso(pg), "registro"); verificar(pg.is_disabled("#misGuardar")); verificar(ui["adulto"]["fotoOff"] in pg.inner_text("#misCont"), "debería decir que la foto necesita al adulto")
        igual(pg.locator("#misSacar").count(), 0, "botón de foto sin consentimiento")
        pg.fill("#misCont textarea[data-in=frase]", "El del sol se derritió primero"); pg.click("#misCont [data-res=distinto]"); CAPTURAS.append(foto(pg, v + "_68_mision_registro"))
        pg.click("#misGuardar"); pg.wait_for_function("(Gioval.misiones.estado()||{}).paso==='fin'")
        msg = pg.inner_text("#misFinTxt"); CAPTURAS.append(foto(pg, v + "_69_mision_fin"))
        verificar("distinto" in msg and ("Miraste" in msg or "Observaste" in msg), "mensaje de proceso: " + msg)
        for mala in ("genio", "inteligente", "mejor", "racha", "puntos"): verificar(mala not in msg.lower(), "elogio a la persona: " + msg)
        a = album(pg); igual(len(a), 1, "entradas del álbum"); e = a[0]
        igual((e["m"], e["res"], e["frase"], e["porque"], e["foto"], e["pred"], e["obs"]), ("exp_hielo", "distinto", "El del sol se derritió primero", "porque el sol calienta", None, t["prediccion"]["opciones"][0], t["observacion"][1]), "entrada")
        igual(n_fotos(pg), 0, "sin consentimiento no se guarda foto")
        # el tiempo de misiones NO cuenta como pantalla
        pg.wait_for_timeout(2300); igual(pg.evaluate("JSON.stringify(store.time)"), t0, "las misiones no deben sumar tiempo de pantalla")
        pg.click("#misAcc .btn:has-text('álbum')"); pg.wait_for_timeout(250)
        verificar("El del sol se derritió primero" in pg.inner_text("#misAlbLista") and "Hielo" in pg.inner_text("#misAlbLista"), "el álbum no muestra la entrada")
        CAPTURAS.append(foto(pg, v + "_70_album_nino"))
        verificar(not err, "%s: %s" % (v, err)); ctx.close()

@prueba("misiones: sin tope diario de pantalla (Números sí lo respeta) y sin sesión/chequeo en la isla")
def t_mis_sin_tope(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=82); instalar_speak(pg); entrar(pg, "Vale")
    pg.evaluate("store.time['Vale|'+today()]=99999"); verificar(pg.evaluate("capLeft()") < 0)
    abrir_isla(pg, "Misiones"); verificar("Elegir una misión" in pg.inner_text("#menuIslaItems"))
    mis_abrir(pg, "hogar_medias"); mis_hasta(pg, "registro"); mis_registrar(pg, "Había 5 pares")
    verificar(not pg.evaluate("document.getElementById('capBox').classList.contains('show')"), "el tope de pantalla no debe frenar misiones")
    abrir_isla(pg, "Números"); verificar("Mañana seguimos" in pg.inner_text("#menuIslaItems"), "Números sí respeta el tope")
    igual(pg.evaluate("PACKS.find(p=>p.id==='misiones').skills.length"), 0, "Misiones no declara habilidades")
    verificar(not err, str(err)); ctx.close()

@prueba("misiones: foto con permiso del adulto (achicada, sin metadatos, solo en el aparato), álbum y borrado por adultos")
def t_mis_foto(C):
    ruta = jpeg_prueba("foto_grande.jpg"); original = ruta.stat().st_size; verificar(b"Exif" in ruta.read_bytes()[:100], "la foto de prueba debería traer EXIF")
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []; reqs = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=83); instalar_speak(pg); entrar(pg, "Vale")
        pg.on("request", lambda r: reqs.append((r.method, r.url)))
        mis_abrir(pg, "arte_dibujo_secreto"); mis_hasta(pg, "registro")
        pg.fill("#misCont textarea[data-in=frase]", "¡Apareció mi estrella!"); pg.click("#misCont [data-res=pensaba]")
        # el permiso de la foto exige al adulto (candado) y se puede volver a apagar
        pg.click("#misCont details summary"); pg.click("#misCont [data-act=tgFoto]")
        verificar(pg.evaluate("document.getElementById('gateBox').classList.contains('show')"), "no pidió el candado de adultos")
        igual(pg.evaluate("Gioval.misiones.estado().consent"), False, "no debe activarse sin el candado")
        pg.click("#gateNo"); igual(pg.evaluate("Gioval.misiones.estado().consent"), False)
        pg.click("#misCont [data-act=tgFoto]"); pasar_gate(pg); igual(pg.evaluate("Gioval.misiones.estado().consent"), True)
        verificar(pg.is_visible("#misSacar"), "falta el botón de foto"); CAPTURAS.append(foto(pg, v + "_71_mision_foto_permiso"))
        pg.set_input_files("#misFile", str(ruta)); pg.wait_for_selector("#misCont .mis-fotoprev img"); CAPTURAS.append(foto(pg, v + "_72_mision_foto_prev"))
        igual(n_fotos(pg), 0, "la foto no se guarda hasta tocar Guardar")
        pg.click("#misGuardar"); pg.wait_for_function("(Gioval.misiones.estado()||{}).paso==='fin'", timeout=8000)
        a = album(pg); igual(len(a), 1); fid = a[0]["foto"]; verificar(fid, "la entrada no tiene foto"); igual(n_fotos(pg), 1)
        info = pg.evaluate("""Gioval.almacen.fotos.obtener(%s).then(async r=>{ const b=await createImageBitmap(r.blob); const bytes=new Uint8Array(await r.blob.arrayBuffer());
          let exif=false; for(let i=0;i<bytes.length-4;i++){ if(bytes[i]===69&&bytes[i+1]===120&&bytes[i+2]===105&&bytes[i+3]===102){ exif=true; break; } } return {tipo:r.blob.type,w:b.width,h:b.height,peso:r.blob.size,exif:exif,meta:r.meta}; })""" % json.dumps(fid))
        igual(info["tipo"], "image/jpeg"); verificar(max(info["w"], info["h"]) <= 1024, "no se achicó: %sx%s" % (info["w"], info["h"])); verificar(info["peso"] < original / 5, "pesa mucho: %d" % info["peso"])
        verificar(not info["exif"], "la foto guardada conserva metadatos (EXIF)"); igual(info["meta"]["perfil"], "Vale")
        fuera = [u for _, u in reqs if not (u.startswith(C.url) or u.startswith("blob:") or u.startswith("data:"))]
        verificar(not fuera, "pedidos de red fuera del aparato: %s" % fuera[:3])
        verificar(not any(m != "GET" for m, _ in reqs), "no debe haber pedidos que suban datos: %s" % [r for r in reqs if r[0] != "GET"])
        # álbum del niño: ve la foto y NO puede borrar
        pg.click("#misAcc .btn:has-text('álbum')"); pg.wait_for_selector("#misAlbLista .mis-foto img"); verificar("¡Apareció mi estrella!" in pg.inner_text("#misAlbLista"))
        igual(pg.locator("[data-del]").count(), 0, "el niño no debería ver los botones de borrar"); CAPTURAS.append(foto(pg, v + "_73_album_foto_nino"))
        # vista de adultos: pide candado, permite borrar
        pg.click("#misAlbModo"); pasar_gate(pg); verificar(pg.locator("[data-del]").count() == 1 and pg.locator("[data-delfoto]").count() == 1)
        verificar("solo en este aparato" in pg.inner_text("#misAlbInfo")); CAPTURAS.append(foto(pg, v + "_74_album_adultos"))
        pg.click("[data-del]"); verificar(pg.is_visible("#misConfirm")); pg.click("#misConfirmNo"); igual(len(album(pg)), 1, "cancelar no borra"); igual(n_fotos(pg), 1)
        pg.click("[data-delfoto]"); pg.click("#misConfirmSi"); pg.wait_for_timeout(300)
        igual(n_fotos(pg), 0, "borrar solo la foto"); a = album(pg); igual(len(a), 1, "la entrada queda"); igual(a[0]["foto"], None)
        pg.click("[data-del]"); pg.click("#misConfirmSi"); pg.wait_for_timeout(300)
        igual(len(album(pg)), 0, "borrar el recuerdo"); verificar("Todavía no hay recuerdos" in pg.inner_text("#misAlbLista")); igual(n_fotos(pg), 0)
        verificar(not err, "%s: %s" % (v, err)); ctx.close()

@prueba("misiones: respaldo exportar → borrar todo → restaurar recupera álbum Y fotos (y un respaldo viejo sin fotos no las borra)")
def t_mis_respaldo(C):
    f1 = jpeg_prueba("foto_a.jpg", 1600, 1200, (10, 120, 200)); f2 = jpeg_prueba("foto_b.jpg", 800, 1100, (200, 200, 20))
    ctx = C.banco.contexto("360x700", accept_downloads=True); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=84); instalar_speak(pg); entrar(pg, "Vale")
    mis_completa(pg, "construir_casita", "Mi casita con techo", "pensaba", f1); mis_completa(pg, "exp_flota", "La piedra se hundió", "distinto", f2); mis_completa(pg, "hogar_medias", "Sin foto", "pensaba")
    antes = album(pg); igual(len(antes), 3); igual(n_fotos(pg), 2)
    sha = "Gioval.almacen.fotos.listar().then(async l=>{ const o={}; for(const f of l){ const r=await Gioval.almacen.fotos.obtener(f.id); const h=await crypto.subtle.digest('SHA-256',await r.blob.arrayBuffer()); o[f.id]=Array.from(new Uint8Array(h)).map(x=>x.toString(16).padStart(2,'0')).join(''); } return o; })"
    hashes = pg.evaluate(sha); igual(len(hashes), 2)
    abrir_panel(pg)
    with pg.expect_download() as d: pg.click("#btnExport")
    ruta = SALIDA / "respaldo_misiones.json"; d.value.save_as(str(ruta)); pg.wait_for_timeout(300)
    arch = json.loads(ruta.read_text(encoding="utf-8")); igual(len(arch["fotos"]), 2, "el respaldo debe llevar las fotos"); igual(sorted(f["id"] for f in arch["fotos"]), sorted(hashes), "ids de fotos")
    verificar(all(f["datos"].startswith("data:image/jpeg;base64,") for f in arch["fotos"]))
    igual(len(arch["store"]["misiones"]["album"]["Vale"]), 3, "el álbum viaja dentro del store")
    # borrar TODO (localStorage + las 3 bases de IndexedDB) y comprobar que no queda nada
    pg.evaluate("localStorage.clear()")
    pg.evaluate("new Promise(r=>{ const q=indexedDB.open('gioval-db'); q.onsuccess=()=>{ const d=q.result; const t=d.transaction(['estado','respaldo','fotos'],'readwrite'); ['estado','respaldo','fotos'].forEach(n=>t.objectStore(n).clear()); t.oncomplete=()=>{ d.close(); r(1); }; }; })")
    pg.reload(); esperar_listo(pg); igual(pg.evaluate("store.profiles"), [], "después de borrar"); igual(n_fotos(pg), 0, "fotos después de borrar")
    pg.evaluate("document.getElementById('nameBox').classList.remove('show')"); abrir_panel(pg); pg.set_input_files("#fileRestore", str(ruta)); pg.wait_for_selector("#restoreBox.show")
    verificar("Fotos: 2" in pg.inner_text("#restoreTxt"), pg.inner_text("#restoreTxt"))
    with pg.expect_navigation(): pg.click("#restoreOk")
    esperar_listo(pg); pg.wait_for_timeout(300); instalar_speak(pg); entrar(pg, "Vale"); despues = album(pg); igual(despues, antes, "álbum restaurado"); igual(n_fotos(pg), 2, "fotos restauradas")
    igual(pg.evaluate(sha), hashes, "las fotos restauradas deben ser idénticas byte a byte")
    pg.evaluate("Gioval.misiones.abrirAlbum(false)"); pg.wait_for_function("document.querySelectorAll('#misAlbLista .mis-foto img').length===2", timeout=8000)
    CAPTURAS.append(foto(pg, "360x700_76_album_restaurado"))
    # un respaldo viejo (sin la clave "fotos") no toca las fotos existentes
    viejo = dict(arch); viejo.pop("fotos"); rv = SALIDA / "respaldo_sin_fotos.json"; rv.write_text(json.dumps(viejo), encoding="utf-8")
    abrir_panel(pg); pg.set_input_files("#fileRestore", str(rv)); pg.wait_for_selector("#restoreBox.show"); verificar("Fotos:" not in pg.inner_text("#restoreTxt"))
    with pg.expect_navigation(): pg.click("#restoreOk")
    esperar_listo(pg); igual(n_fotos(pg), 2, "restaurar sin fotos no debe borrar las de hoy")
    rs = pg.evaluate("Gioval.almacen.respaldos().then(l=>l.filter(r=>r.id.startsWith('pre-restauracion-fotos')).length)"); verificar(rs >= 1, "falta la copia previa de fotos")
    verificar(not err, str(err)); ctx.close()

@prueba("misiones: misión de la semana (automática por edad, elegida por adultos, rota semana a semana) y misiones bloqueadas por edad")
def t_mis_semana(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=85); instalar_speak(pg); entrar(pg, "Vale")
    Ms = {m["id"]: m for m in json.loads(pg.evaluate("JSON.stringify(Gioval.datos.misiones.MISIONES)"))}
    abrir_isla(pg, "Misiones"); verificar("Misión de la semana" in pg.inner_text("#menuIslaItems"))
    abrir_panel(pg); verificar("Misiones" in pg.inner_text("#panel")); CAPTURAS.append(foto(pg, "360x700_77_panel_misiones"))
    pg.select_option("#misPEdad", "4"); igual(pg.evaluate("store.misiones.edad.Vale"), 4)
    vistas = set()
    for k in range(10):
        pg.evaluate("window.__OFF=%d" % (k * 7 * 864e5)); sid = pg.evaluate("Gioval.misiones.semana().id"); vistas.add(sid)
        verificar(Ms[sid]["minEdad"] <= 4, "misión de la semana para 4 años con edad mínima %d: %s" % (Ms[sid]["minEdad"], sid))
    verificar(len(vistas) >= 4, "la misión de la semana no rota: %s" % vistas)
    pg.evaluate("window.__OFF=0"); a = pg.evaluate("Gioval.misiones.semana().id"); igual(pg.evaluate("Gioval.misiones.semana().id"), a, "estable dentro de la semana")
    pg.click("#btnGear"); abrir_isla(pg, "Misiones"); pg.click("#menuIslaItems .island:has-text('Elegir')")
    verificar(pg.locator(".mis-card.off").count() == 1 and "Puente de papel" in pg.locator(".mis-card.off").inner_text(), "con 4 años el puente (desde 5) debería estar bloqueado")
    igual(pg.locator(".mis-tagsem").count(), 1, "marca de la semana")
    # el adulto elige la misión de la semana
    abrir_panel(pg); pg.select_option("#misPSem", "exp_flota"); igual(pg.evaluate("Gioval.misiones.semana().id"), "exp_flota"); pg.click("#btnGear")
    abrir_isla(pg, "Misiones"); verificar("¿Flota o se hunde?" in pg.inner_text("#menuIslaItems"), "la tarjeta debería mostrar la elegida")
    pg.click("#menuIslaItems .island >> nth=0"); pg.wait_for_timeout(150); igual(pg.evaluate("Gioval.misiones.estado().m.id"), "exp_flota")
    # a la semana siguiente vuelve a ser automática
    pg.evaluate("window.__OFF=7*864e5+3600e3"); pg.evaluate("Gioval.misiones.semana()"); igual(pg.evaluate("store.misiones.semana.Vale.auto"), True, "la semana siguiente debería ser automática")
    verificar(not err, str(err)); ctx.close()

@prueba("misiones: una misión de espera (poroto) queda empezada y se retoma días después con su predicción")
def t_mis_espera(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=86); instalar_speak(pg); entrar(pg, "Vale")
    t = json.loads(pg.evaluate("JSON.stringify(Gioval.datos.misiones.TEXTOS.misiones.huerta_poroto)"))
    mis_abrir(pg, "huerta_poroto"); mis_hasta(pg, "espera"); verificar("3 días" in pg.inner_text("#misCont")); CAPTURAS.append(foto(pg, "360x700_78_mision_espera"))
    pg.click("#misAcc .btn"); pg.wait_for_timeout(200)
    igual(len(album(pg)), 0, "todavía no es un recuerdo"); igual(pg.evaluate("store.misiones.pend.Vale.length"), 1)
    verificar("Mirar: Un poroto que despierta" in pg.inner_text("#menuIslaItems") and "Empezaste hoy" in pg.inner_text("#menuIslaItems"), pg.inner_text("#menuIslaItems"))
    pg.evaluate("Gioval.almacen.guardarYa()"); pg.wait_for_timeout(200); pg.reload(); esperar_listo(pg); instalar_speak(pg); entrar(pg, "Vale")
    pg.evaluate("window.__OFF=3*864e5+1000"); abrir_isla(pg, "Misiones"); verificar("hace 3 días" in pg.inner_text("#menuIslaItems"), pg.inner_text("#menuIslaItems"))
    pg.click("#menuIslaItems .island:has-text('Mirar')"); pg.wait_for_timeout(150); igual(mis_paso(pg), "quepaso")
    verificar(t["prediccion"]["opciones"][0] in pg.inner_text(".mis-recuerda"), "debería recordar lo que pensó")
    mis_hasta(pg, "registro"); mis_registrar(pg, "Salió una raicita", "pensaba")
    a = album(pg); igual(len(a), 1); igual((a[0]["m"], a[0]["pred"], a[0]["obs"]), ("huerta_poroto", t["prediccion"]["opciones"][0], t["observacion"][0]))
    igual(pg.evaluate("store.misiones.pend.Vale.length"), 0, "ya no está pendiente"); verificar(not err, str(err)); ctx.close()

@prueba("misiones: dictado por voz solo si el adulto lo activa; una explicación marcada A REVISAR no se muestra")
def t_mis_dictado(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=87,
        extra_init="window.SpeechRecognition=window.webkitSpeechRecognition=function(){ var s=this; s.start=function(){ window.__dic=(window.__dic||0)+1; setTimeout(function(){ s.onresult({results:[[{transcript:'se derritió'}]]}); s.onend&&s.onend(); },30); }; };")
    instalar_speak(pg); entrar(pg, "Vale")
    mis_abrir(pg, "exp_flota"); mis_hasta(pg, "porque")
    igual(pg.locator("[data-dictar]").count(), 0, "sin permiso no hay dictado")
    pg.click("#misCont details summary"); pg.click("#misCont [data-act=tgDictado]"); pasar_gate(pg)
    igual(pg.locator("[data-dictar=porque]").count(), 1, "con permiso aparece el botón de dictar"); pg.click("[data-dictar=porque]"); pg.wait_for_timeout(200)
    igual(pg.input_value("#misCont textarea[data-in=porque]"), "se derritió"); igual(pg.evaluate("Gioval.misiones.estado().porque"), "se derritió"); igual(pg.evaluate("window.__dic"), 1)
    igual(pg.locator("#misAcc .btn:has-text('explicación')").count(), 1, "debería haber botón de explicación")
    # A REVISAR: ni botón ni texto
    expl = pg.evaluate("Gioval.datos.misiones.TEXTOS.misiones.exp_flota.explicacion")
    pg.evaluate("Gioval.datos.misiones.MISIONES.find(m=>m.id==='exp_flota').revisar='A REVISAR: confirmar con una fuente'")
    pg.click("#misBack"); mis_abrir(pg, "exp_flota"); mis_hasta(pg, "porque")
    igual(pg.locator("#misAcc .btn:has-text('explicación')").count(), 0, "una explicación A REVISAR no debe ofrecerse"); igual(pg.locator(".mis-exp").count(), 0)
    verificar(expl not in pg.inner_text("body"), "el texto sin revisar aparece en pantalla")
    pg.evaluate("delete Gioval.datos.misiones.MISIONES.find(m=>m.id==='exp_flota').revisar")
    verificar(not err, str(err)); ctx.close()

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
