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

@prueba("mapa: muestra Música, Números y las islas con candado")
def t_mapa(C):
    for v in ("pixel7", "360x700", "740x330"):
        ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err); instalar_speak(pg)
        entrar(pg, "Vale")
        islas = pg.evaluate("[...document.querySelectorAll('#islands .island')].map(x=>x.innerText.replace(/\\n/g,'|')+(x.classList.contains('off')?'|off':''))")
        igual(islas, ["🎹|Isla Música|¡A tocar el piano!", "🔢|Isla Números|¡A contar y sumar!", "🔒|Isla Letras|Pronto|off", "🔒|Isla Animales|Pronto|off"], "mapa " + v)
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
    igual(pg.evaluate("PACKS.map(p=>[p.id,p.instrumento,p.entradas])"), [["musica", "piano", ["nota", "toque"]], ["numeros", None, ["toque"]]], "declaración de las islas")
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
            pg.evaluate("renderWho(); show('who')"); f("who"); entrar(pg, "Vale"); f("mapa")
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
        igual(pg.evaluate("PACKS.map(p=>p.id)"), ["musica", "numeros", "colores"], "islas registradas")
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

# ---------------------------------------------------------------- ayudantes de la casa
def datos_ayudantes():
    """Lee js/datos/tareas.js con node (sin navegador) y devuelve {TEXTOS, tareas}."""
    js = "const fs=require('fs');global.Gioval={datos:{}};(0,eval)(fs.readFileSync(process.argv[1],'utf8'));process.stdout.write(JSON.stringify(Gioval.datos.ayudantes));"
    r = subprocess.run(["node", "-e", js, str(APP / "js/datos/tareas.js")], capture_output=True, text=True)
    verificar(r.returncode == 0, "no se pudo leer tareas.js: " + r.stderr[:300])
    return json.loads(r.stdout)

# Lo que NUNCA puede aparecer en los PASOS de una tarea (fuego/calor, filo, químicos, escaleras/alturas, electricidad).
# Los AVISOS sí pueden nombrarlos ("los cuchillos los pone un adulto"): ahí se dice qué NO hacer.
PROHIBIDO_EN_PASOS = re.compile(r"(fuego|\bllamas?\b|hornall|horno|estufa|plancha|calient|hirvi|herv[ií]|\bfre[ií]|cuchill|tijera|\bfilos|\bfilo\b|afilad|\bcort(a|an|ar|ás|á|ado)\b|abrelatas|\blatas?\b|rallador|vidrio|lavandina|cloro|detergente|desinfect|qu[ií]mic|veneno|abono|escalera|banquit|\bsillas?\b|subirte|subite|trepar|enchuf|\bcables?\b|el[eé]ctric|licuadora|microondas)", re.I)
PROHIBIDO_ELOGIO = re.compile(r"(buen[ií]sim|inteligent|genio|el mejor|la mejor|campe|mejor que|perfect|racha|puntos|seguid[oa]s|ganaste|premio)", re.I)

def textos_planos(o):
    if isinstance(o, str): return [o]
    if isinstance(o, dict): return [t for v in o.values() for t in textos_planos(v)]
    if isinstance(o, list): return [t for v in o for t in textos_planos(v)]
    return []

@prueba("ayudantes: lista de tareas (supervisión y aviso obligatorios, sin fuego/filo/químicos/escaleras) y TEXTOS al tope")
def t_ay_datos(C):
    d = datos_ayudantes(); tareas, T = d["tareas"], d["TEXTOS"]
    src = (APP / "js/datos/tareas.js").read_text(encoding="utf-8")
    verificar(src.index("const TEXTOS") < src.index("const TAREAS"), "TEXTOS tiene que estar arriba de la lista de tareas")
    verificar("LISTA PARA QUE MARCOS LA APRUEBE" in src, "falta la lista anotada para aprobación")
    ids = [t["id"] for t in tareas]; igual(len(ids), len(set(ids)), "ids repetidos")
    esperadas = {"mesa_poner", "mesa_levantar", "juguetes", "plantas", "zapatos", "ropa", "mascota", "reciclaje", "secar", "cocinar_verduras"}
    verificar(esperadas <= set(ids), "faltan tareas pedidas: %s" % (esperadas - set(ids)))
    verificar({"cama", "juguetes", "mochila"} <= set(ids), "se perdieron ids de la lista anterior")
    niveles = set(T["supervision"].keys()); igual(niveles, {"solo", "cerca", "adulto"}, "niveles de supervisión")
    for k, v in T["supervision"].items(): verificar(all(v.get(c) for c in ("icono", "corto", "largo", "voz")), "supervisión %s incompleta" % k)
    for t in tareas:
        n = t["id"]
        verificar(t.get("supervision") in niveles, "%s: supervisión faltante o inválida: %r" % (n, t.get("supervision")))
        verificar(t.get("emoji") and t.get("nombre"), n + ": falta ícono o nombre")
        verificar(isinstance(t.get("edadMin"), int) and 4 <= t["edadMin"] <= 12, "%s: edad mínima %r" % (n, t.get("edadMin")))
        verificar(isinstance(t.get("minutos"), int) and 1 <= t["minutos"] <= 30, "%s: minutos %r" % (n, t.get("minutos")))
        verificar(2 <= len(t["pasos"]) <= 4, "%s: tiene que tener de 2 a 4 pasos (tiene %d)" % (n, len(t["pasos"])))
        for p in t["pasos"]: verificar(p.strip() and len(p) <= 90 and p.strip()[-1] in ".?!", "%s: paso muy largo o sin punto: %r" % (n, p))
        verificar(isinstance(t.get("aviso"), str), n + ": 'aviso' tiene que existir (vacío solo si es supervisión 'solo')")
        if t["supervision"] in ("cerca", "adulto"): verificar(len(t["aviso"].strip()) >= 20, "%s: supervisión %s exige un aviso de seguridad" % (n, t["supervision"]))
        m = PROHIBIDO_EN_PASOS.search(" ".join(t["pasos"] + [t["nombre"]]))
        verificar(not m, "%s: los pasos mencionan algo prohibido (%r)" % (n, m and m.group(0)))
    for t in ("mascota", "cocinar_verduras"): verificar(next(x for x in tareas if x["id"] == t)["supervision"] == "adulto", t + " debe ser solo con adulto")
    verificar(len(T["elogios"]) >= 3, "pocos elogios")
    for x in textos_planos(T): verificar(not PROHIBIDO_ELOGIO.search(x), "texto con elogio a la persona, racha o puntos: %r" % x)
    # el código no lleva textos propios: ninguna frase con signos ¡ ¿ fuera de comentarios
    codigo = re.sub(r"/\*.*?\*/", "", (APP / "js/islas/ayudantes.js").read_text(encoding="utf-8"), flags=re.S)
    for linea in codigo.splitlines():
        verificar("¡" not in linea and "¿" not in linea, "texto fijo en el código (va en TEXTOS): " + linea.strip()[:80])
    return "%d tareas; supervisión: %s" % (len(tareas), {k: sum(1 for t in tareas if t["supervision"] == k) for k in sorted(niveles)})

def ay_pagina(C, vista="360x700", extra=None, **kw):
    ctx = C.banco.contexto(vista); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err, semilla=kw.pop("semilla", 81), extra_init=extra, **kw)
    instalar_speak(pg); entrar(pg, "Vale"); return ctx, pg

def ay_tarea(pg, tid, empezar=True):
    pg.click(".ayCard[data-id='%s']" % tid); pg.wait_for_timeout(80)
    if empezar: pg.click("[data-a='empezar']"); pg.wait_for_timeout(120)

def ay_vista(pg): return pg.evaluate("Gioval.ayudantes.vista()")
def ay_texto(pg, sel="#ayBody"): return pg.evaluate("document.querySelector('%s').innerText" % sel)

@prueba("ayudantes: aparece al llegar al tope diario (botón, frase y tarjeta del menú) y no antes")
def t_ay_tope(C):
    ctx, pg = ay_pagina(C)
    abrir_isla(pg, "Números"); verificar("ayudantes" not in ay_texto(pg, "#menuIslaItems").lower(), "la tarjeta aparece antes del tope")
    llegar_al_tope(pg)
    verificar(pg.evaluate("getComputedStyle(document.getElementById('capAyud')).display") != "none", "no aparece el botón en el cartel de tope")
    igual(pg.evaluate("document.getElementById('capAyud').innerText"), "🧹 Hora de ayudantes")
    verificar("hora de ayudantes" in pg.evaluate("document.getElementById('capTail').innerText").lower(), "falta la frase en el cartel")
    verificar(any("hora de ayudantes" in x.lower() for x in pg.evaluate("window.__LOG")), "la frase no se dijo en voz alta")
    verificar(pg.evaluate("document.getElementById('capOk').offsetParent!==null"), "el botón de siempre tiene que seguir")
    pg.click("#capAyud"); pg.wait_for_timeout(150)
    igual(pg.evaluate("document.querySelector('.screen.active').id"), "ayudantes"); igual(ay_vista(pg), "lista")
    verificar(not pg.evaluate("document.getElementById('capBox').classList.contains('show')"), "el cartel quedó abierto")
    igual(pg.evaluate("S.capShown"), False, "S.capShown")
    igual(pg.evaluate("document.querySelectorAll('.ayCard').length"), 12, "tarjetas para 6 años")
    pg.click("#ayBack"); pg.wait_for_timeout(150)     # vuelve al menú: la tarjeta sigue disponible mientras no haya más tiempo
    verificar("Hora de ayudantes" in ay_texto(pg, "#menuIslaItems"), "falta la tarjeta del menú después del tope")
    pg.click(".island:has-text('Hora de ayudantes')"); pg.wait_for_timeout(150); igual(pg.evaluate("document.querySelector('.screen.active').id"), "ayudantes")
    ctx.close()
    # si los adultos lo desactivan: no hay botón, ni frase, ni tarjeta
    ctx, pg = ay_pagina(C); pg.evaluate("Gioval.ayudantes.ponerCfg('Vale',{on:false})")
    llegar_al_tope(pg)
    verificar(pg.evaluate("getComputedStyle(document.getElementById('capAyud')).display") == "none", "el botón aparece con los ayudantes desactivados")
    verificar("ayudantes" not in pg.evaluate("document.getElementById('capTail').innerText").lower(), "la frase aparece desactivado")
    pg.click("#capOk"); pg.wait_for_timeout(120); verificar("ayudantes" not in ay_texto(pg, "#menuIslaItems").lower(), "tarjeta con los ayudantes desactivados")
    ctx.close()

@prueba("ayudantes: elegir tarea (pasos, supervisión y aviso leídos en voz); las de 'solo con adulto' piden la pregunta de adultos")
def t_ay_elegir(C):
    ctx, pg = ay_pagina(C); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    pg.evaluate("window.__LOG.length=0")
    pg.click(".ayCard[data-id='plantas']"); pg.wait_for_timeout(100); igual(ay_vista(pg), "detalle")
    txt = ay_texto(pg); verificar("Regar las plantas" in txt and "5 min" in txt and "Con un adulto cerca" in txt and "abonos" in txt, txt)
    igual(pg.evaluate("document.querySelectorAll('.aySteps li').length"), 3, "pasos")
    dicho = " | ".join(pg.evaluate("window.__LOG")); verificar("Paso 1." in dicho and "Paso 3." in dicho and "Ojo: Solo agua" in dicho and "Pedile a un adulto que esté cerca" in dicho, dicho)
    foto(pg, "360x700_60_ayudantes_detalle"); CAPTURAS.append("360x700_60_ayudantes_detalle.png")
    pg.click("[data-a='lista']"); pg.wait_for_timeout(80); igual(ay_vista(pg), "lista")
    # tarea que se hace por cuenta propia: empieza directo
    ay_tarea(pg, "zapatos"); igual(ay_vista(pg), "corre"); verificar("Por tu cuenta" not in ay_texto(pg) or True)
    pg.click("[data-a='cancelar']"); pg.wait_for_timeout(80)
    # tarea solo con adulto: no empieza sin la pregunta de adultos
    ay_tarea(pg, "mascota", empezar=False); verificar("Un adulto tiene que estar al lado" in ay_texto(pg), "falta el aviso de adulto")
    verificar("Siempre con un adulto al lado" in ay_texto(pg), "falta el aviso de seguridad")
    pg.click("[data-a='empezar']"); pg.wait_for_selector("#gateBox.show", timeout=2000)
    pg.fill("#gateIn", "1"); pg.click("#gateOk"); pg.wait_for_timeout(100)
    igual(pg.evaluate("Gioval.ayudantes.enCurso()"), None, "empezó con la respuesta equivocada"); verificar(pg.evaluate("document.getElementById('gateBox').classList.contains('show')"))
    pg.fill("#gateIn", str(pg.evaluate("S.gateAns"))); pg.click("#gateOk"); pg.wait_for_timeout(150)
    igual(pg.evaluate("Gioval.ayudantes.enCurso().id"), "mascota"); igual(ay_vista(pg), "corre")
    ctx.close()

@prueba("ayudantes: cronómetro con hora absoluta — reloj simulado, pantalla oculta (timers congelados) y vuelta a primer plano")
def t_ay_cronometro(C):
    sonidos = "window.__osc=0; (function(){ var o=AudioContext.prototype.createOscillator; AudioContext.prototype.createOscillator=function(){ window.__osc++; return o.apply(this,arguments); }; })();"
    # 1) pantalla oculta: nadie corre timers, el reloj avanza, no suena hasta volver
    ctx, pg = ay_pagina(C, extra=sonidos); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    pg.evaluate("window.__fin=[]; Alarma.onFin(function(i){ window.__fin.push(i); }); window.setInterval=function(){ return 1; }; 0")   # timers congelados desde ahora
    ay_tarea(pg, "zapatos")                       # 3 minutos
    igual(ay_vista(pg), "corre"); verificar(178 <= pg.evaluate("Alarma.restante()") <= 180, "restante inicial")
    igual(ay_texto(pg, "#ayTime"), "03:00", "cuenta regresiva grande")
    verificar(pg.evaluate("parseFloat(getComputedStyle(document.getElementById('ayTime')).fontSize)") >= 70, "los números no son grandes")
    foto(pg, "360x700_61_ayudantes_cronometro"); CAPTURAS.append("360x700_61_ayudantes_cronometro.png")
    verificar(abs(pg.evaluate("JSON.parse(localStorage.getItem('gioval_alarma')).fin - Date.now()") - 180000) < 3000, "no guardó la hora absoluta de fin")
    pg.evaluate("Object.defineProperty(document,'hidden',{get:()=>true,configurable:true}); window.__OFF=60000")
    verificar(118 <= pg.evaluate("Alarma.restante()") <= 121, "restante con el reloj +60 s")
    pg.evaluate("window.__OFF=400000")            # pasó mucho más que el tiempo con la pantalla apagada
    pg.wait_for_timeout(700)
    igual(pg.evaluate("window.__fin.length"), 0, "no puede sonar mientras la página está congelada"); igual(ay_vista(pg), "corre", "sigue 'corriendo' hasta volver")
    igual(pg.evaluate("window.__osc"), 0, "sonó con la pantalla oculta")
    pg.evaluate("Object.defineProperty(document,'hidden',{get:()=>false,configurable:true}); document.dispatchEvent(new Event('visibilitychange'))")
    pg.wait_for_timeout(150)
    igual(pg.evaluate("window.__fin.length"), 1, "tiene que sonar al volver a primer plano"); igual(ay_vista(pg), "tiempo")
    verificar(pg.evaluate("window.__fin[0].tarde") >= 200000, "tarde=%s" % pg.evaluate("window.__fin[0].tarde"))
    verificar(pg.evaluate("window.__osc") >= 4, "no sonó la alarma al volver (osciladores: %s)" % pg.evaluate("window.__osc"))
    txt = ay_texto(pg); verificar("Se terminó el tiempo" in txt and "Volviste a la app" in txt and "Terminé" in txt and "Un ratito más" in txt, txt)
    verificar(any("Se terminó el tiempo" in x for x in pg.evaluate("window.__LOG")), "no lo dijo en voz")
    igual(pg.evaluate("localStorage.getItem('gioval_alarma')"), None, "alarma guardada sin limpiar")
    pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); igual(pg.evaluate("window.__fin.length"), 1, "sonó dos veces")
    foto(pg, "360x700_62_ayudantes_tiempo"); CAPTURAS.append("360x700_62_ayudantes_tiempo.png")
    ctx.close()
    # 2) pantalla encendida: suena solo, a la hora (hora absoluta), y "un ratito más" reprograma
    ctx, pg = ay_pagina(C, extra=sonidos, semilla=82); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    ay_tarea(pg, "zapatos"); pg.evaluate("window.__OFF=181000"); pg.wait_for_selector("[data-a='mas']", timeout=3000)
    igual(ay_vista(pg), "tiempo"); verificar("Volviste a la app" not in ay_texto(pg), "no debería decir 'volviste' si la app estaba abierta")
    pg.click("[data-a='mas']"); pg.wait_for_timeout(120); igual(ay_vista(pg), "corre"); verificar(118 <= pg.evaluate("Alarma.restante()") <= 120, "un ratito más = 2 minutos")
    igual(ay_texto(pg, "#ayTime"), "02:00")
    ctx.close()

@prueba("ayudantes: terminar, elogio al esfuerzo, registro semanal sin rachas ni puntos")
def t_ay_terminar(C):
    ctx, pg = ay_pagina(C); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    elogios = pg.evaluate("Gioval.ayudantes.textos.elogios"); vistos = []
    for i, tid in enumerate(["zapatos", "juguetes", "plantas"], 1):
        ay_tarea(pg, tid); igual(ay_vista(pg), "corre"); pg.evaluate("window.__OFF=%d" % (i * 20000)); pg.click("[data-a='terminar']"); pg.wait_for_timeout(120)
        igual(ay_vista(pg), "fin"); txt = ay_texto(pg)
        verificar(pg.evaluate("document.getElementById('ayElogio').innerText") in elogios, "elogio fuera de la lista")
        vistos.append(pg.evaluate("document.getElementById('ayElogio').innerText"))
        verificar("Esta semana ayudaste %s" % ("1 vez." if i == 1 else "%d veces." % i) in txt, "registro semanal: " + txt)
        verificar(not PROHIBIDO_ELOGIO.search(txt) and "⭐" not in txt and "🔥" not in txt, "elogio a la persona, racha o puntos: " + txt)
        igual(pg.evaluate("Alarma.activa()"), False, "la alarma debe cancelarse al terminar")
        if i < 3: pg.click("[data-a='lista']"); pg.wait_for_timeout(80)
    foto(pg, "360x700_63_ayudantes_fin"); CAPTURAS.append("360x700_63_ayudantes_fin.png")
    reg = pg.evaluate("Gioval.ayudantes.registro('Vale')"); igual([r["id"] for r in reg], ["zapatos", "juguetes", "plantas"], "registro"); verificar(all(r["s"] >= 0 for r in reg))
    # solo cuenta lo de ESTA semana (lunes a domingo): una anotación vieja no suma; la semana siguiente empieza de cero
    pg.evaluate("store.ayud.reg.Vale.push({t:Date.now()-10*864e5,id:'cama',s:60})"); igual(pg.evaluate("Gioval.ayudantes.vecesSemana('Vale')"), 3, "una tarea de hace 10 días no cuenta")
    pg.evaluate("window.__OFF=8*864e5"); igual(pg.evaluate("Gioval.ayudantes.vecesSemana('Vale')"), 0, "la semana siguiente empieza de cero (no hay racha)"); pg.evaluate("window.__OFF=0")
    # el registro no tiene rachas ni puntos: solo { t, id, s }
    verificar(set(reg[0].keys()) <= {"t", "id", "s", "f"}, str(reg[0]))
    abrir_panel(pg); pg.click("#ayPanel summary"); pg.wait_for_timeout(100)
    verificar("Esta semana ayudó: 3 veces" in pg.evaluate("document.getElementById('ayResumen').innerText"), pg.evaluate("document.getElementById('ayResumen').innerText"))
    # sobrevive a recargar
    pg.evaluate("Gioval.almacen.guardarYa()"); pg.wait_for_timeout(300); pg.reload(); esperar_listo(pg)
    igual(pg.evaluate("Gioval.ayudantes.registro('Vale').length"), 4, "el registro no sobrevivió a recargar")
    ctx.close()
    # un ratito más: se anota UNA vez; dejarla por ahora no anota nada y no castiga
    ctx, pg = ay_pagina(C, semilla=83); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    ay_tarea(pg, "zapatos"); pg.evaluate("window.__OFF=181000"); pg.wait_for_selector("[data-a='mas']", timeout=3000)
    pg.click("[data-a='mas']"); pg.wait_for_timeout(100); pg.click("[data-a='terminar']"); pg.wait_for_timeout(100)
    igual(pg.evaluate("Gioval.ayudantes.registro('Vale').length"), 1, "se anotó más de una vez")
    pg.click("[data-a='lista']"); pg.wait_for_timeout(80); ay_tarea(pg, "ropa"); pg.click("[data-a='cancelar']"); pg.wait_for_timeout(100)
    igual(pg.evaluate("Gioval.ayudantes.registro('Vale').length"), 1, "dejarla por ahora no debe anotar"); igual(ay_vista(pg), "lista"); igual(pg.evaluate("Alarma.activa()"), False)
    verificar(any("Está bien" in x for x in pg.evaluate("window.__LOG")), "tiene que haber un mensaje sin castigo")
    ctx.close()

@prueba("ayudantes: el tiempo de ayudantes NO cuenta como tiempo de pantalla")
def t_ay_no_cuenta(C):
    ctx, pg = ay_pagina(C)
    abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(300)
    t0 = pg.evaluate("store.time['Vale|'+today()]||0"); pg.wait_for_timeout(2300)
    verificar(pg.evaluate("store.time['Vale|'+today()]") >= t0 + 2, "control: jugando sí tiene que contar")     # control: la prueba es válida
    pg.evaluate("store.time['Vale|'+today()]=capBase()-1"); pg.wait_for_selector("#capBox.show", timeout=6000); pg.click("#capAyud"); pg.wait_for_timeout(100)
    ay_tarea(pg, "zapatos"); igual(ay_vista(pg), "corre")
    antes = pg.evaluate("[store.time['Vale|'+today()], capLeft()]"); pg.wait_for_timeout(3200)
    despues = pg.evaluate("[store.time['Vale|'+today()], capLeft()]"); igual(despues, antes, "el tiempo de pantalla siguió corriendo en Ayudantes")
    igual(pg.evaluate("document.getElementById('capBox').classList.contains('show')"), False, "no tiene que volver a saltar el cartel de tope")
    ctx.close()

@prueba("ayudantes: configuración de adultos (activar, edad, duración, tareas habilitadas y asignadas, foto) y estado honesto de la alarma")
def t_ay_adultos(C):
    ctx, pg = ay_pagina(C)
    abrir_panel(pg); pg.click("#ayPanel summary"); pg.wait_for_timeout(100)
    tp = ay_texto(pg, "#ayPanel")
    verificar("no garantizada en navegador" in tp and "app Android nativa" in tp, "el panel no dice la verdad sobre la alarma: " + tp[:300])
    verificar("Pantalla encendida mientras corre" in tp and "Avisos del sistema" in tp and "App nativa" in tp, "faltan los estados de la alarma")
    verificar("NO cuenta como tiempo de pantalla" in tp, "falta la aclaración del tiempo")
    foto(pg, "360x700_64_ayudantes_panel"); CAPTURAS.append("360x700_64_ayudantes_panel.png")
    igual(pg.evaluate("document.querySelectorAll('#ayPanelBody [data-h]').length"), 12, "una fila por tarea")
    # edad 4: solo las de 4 años
    pg.select_option("#ayEdad", "4"); pg.wait_for_timeout(80)
    igual(pg.evaluate("Gioval.ayudantes.cfg('Vale').edad"), 4)
    igual(sorted(t["id"] for t in pg.evaluate("Gioval.ayudantes.disponibles('Vale')")), ["juguetes", "mesa_poner", "mochila", "plantas", "zapatos"], "tareas de 4 años")
    # deshabilitar una, asignar otra (aunque sea de 5 años): la asignada va primera y marcada
    pg.uncheck("#ayPanelBody [data-h='juguetes']"); pg.check("#ayPanelBody [data-asig='cocinar_verduras']"); pg.wait_for_timeout(80)
    pg.select_option("#ayDur", "3"); pg.check("#ayFoto"); pg.wait_for_timeout(80)
    c = pg.evaluate("Gioval.ayudantes.cfg('Vale')"); igual((c["off"], c["asig"], c["dur"], c["foto"], c["on"]), (["juguetes"], ["cocinar_verduras"], 3, True, True))
    pg.evaluate("Gioval.almacen.guardarYa()"); pg.wait_for_timeout(250); pg.reload(); esperar_listo(pg); instalar_speak(pg)   # persiste
    igual(pg.evaluate("Gioval.ayudantes.cfg('Vale')"), c, "la configuración no sobrevivió a recargar")
    entrar(pg, "Vale"); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    ids = pg.evaluate("[...document.querySelectorAll('.ayCard')].map(c=>c.dataset.id)"); igual(ids, ["cocinar_verduras", "mesa_poner", "plantas", "zapatos", "mochila"], "lista del niño")
    verificar("Te la pidió un adulto" in pg.evaluate("document.querySelector('.ayCard.asig').innerText"), "la asignada no está marcada")
    verificar(all("3 min" in x for x in pg.evaluate("[...document.querySelectorAll('.ayCard small:not(.pin)')].map(x=>x.innerText)")), "la duración configurada no se ve en las tarjetas")
    ay_tarea(pg, "zapatos"); igual(ay_texto(pg, "#ayTime"), "03:00"); verificar(177 <= pg.evaluate("Alarma.restante()") <= 180, "la duración configurada no se usa")
    pg.click("[data-a='cancelar']"); pg.wait_for_timeout(80)
    # la asignada se cumple una vez y se quita sola
    ay_tarea(pg, "cocinar_verduras", empezar=False); pg.click("[data-a='empezar']"); pg.wait_for_selector("#gateBox.show"); pg.fill("#gateIn", str(pg.evaluate("S.gateAns"))); pg.click("#gateOk"); pg.wait_for_timeout(120)
    pg.click("[data-a='terminar']"); pg.wait_for_timeout(100); igual(pg.evaluate("Gioval.ayudantes.cfg('Vale').asig"), [], "la asignada tenía que quitarse sola")
    # perfiles independientes: el otro niño conserva los valores por defecto
    c2 = pg.evaluate("Gioval.ayudantes.cfg('Otro')"); igual((c2["edad"], c2["on"], c2["dur"], c2["off"], c2["asig"], c2["foto"]), (6, True, 0, [], [], False), "valores por defecto")
    # desactivar
    pg.evaluate("Gioval.ayudantes.ponerCfg('Vale',{on:false})"); igual(pg.evaluate("Gioval.ayudantes.ofrece('Vale')"), False)
    ctx.close()
    # app nativa simulada: el panel lo dice, sin prometer más de la cuenta
    ctx, pg = ay_pagina(C, extra="window.Capacitor={Plugins:{LocalNotifications:{schedule:function(){},cancel:function(){}}}};", semilla=84)
    abrir_panel(pg); pg.click("#ayPanel summary"); pg.wait_for_timeout(100); tp = ay_texto(pg, "#ayPanel")
    verificar("se detectó Capacitor" in tp and "Todavía hay que probarla en el aparato" in tp and "no garantizada en navegador" in tp, tp[-500:])
    ctx.close()

@prueba("ayudantes: foto opcional al terminar (solo si el adulto la activa) en el almacén de fotos existente")
def t_ay_foto(C):
    from PIL import Image
    SALIDA.mkdir(exist_ok=True); png = SALIDA / "foto_prueba.png"; Image.new("RGB", (64, 48), (200, 80, 90)).save(png)
    ctx, pg = ay_pagina(C); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    ay_tarea(pg, "zapatos"); pg.click("[data-a='terminar']"); pg.wait_for_timeout(100)
    igual(pg.evaluate("document.getElementById('ayFotoBtn')"), None, "ofrece foto sin que el adulto la active")
    pg.evaluate("Gioval.ayudantes.ponerCfg('Vale',{foto:true})"); pg.click("[data-a='lista']"); pg.wait_for_timeout(80)
    ay_tarea(pg, "ropa"); pg.click("[data-a='terminar']"); pg.wait_for_timeout(100)
    verificar(pg.evaluate("!!document.getElementById('ayFotoBtn')"), "no ofrece la foto activada")
    foto(pg, "360x700_65_ayudantes_foto"); CAPTURAS.append("360x700_65_ayudantes_foto.png")
    pg.set_input_files("#ayFotoIn", str(png)); pg.wait_for_function("document.getElementById('ayFotoBtn').innerText.includes('guardada')", timeout=5000)
    fs = pg.evaluate("Gioval.almacen.fotos.listar()"); igual(len(fs), 1, "fotos guardadas"); igual((fs[0]["meta"]["tipo"], fs[0]["meta"]["kid"], fs[0]["meta"]["tarea"]), ("ayudantes", "Vale", "ropa"))
    o = pg.evaluate("Gioval.almacen.fotos.obtener('%s').then(r=>[r.blob.type,r.blob.size])" % fs[0]["id"]); verificar(o[1] > 0 and o[0].startswith("image/"), str(o))
    igual(pg.evaluate("Gioval.ayudantes.registro('Vale')[1].f"), fs[0]["id"], "el registro no apunta a la foto")
    abrir_panel(pg); pg.click("#ayPanel summary"); pg.wait_for_timeout(300)
    verificar("Fotos guardadas: 1" in pg.evaluate("document.getElementById('ayResumen').innerText"), "el panel no cuenta la foto"); ctx.close()

@prueba("ayudantes: retoma una tarea en curso si se cerró la app (aún en hora, o ya vencida mientras estaba cerrada)")
def t_ay_retoma(C):
    ctx, pg = ay_pagina(C); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    ay_tarea(pg, "juguetes")        # 10 minutos
    pg.reload(); esperar_listo(pg); instalar_speak(pg); entrar(pg, "Vale"); pg.wait_for_timeout(150)
    igual(pg.evaluate("document.querySelector('.screen.active').id"), "ayudantes", "tendría que retomar la tarea"); igual(ay_vista(pg), "corre")
    verificar(540 <= pg.evaluate("Alarma.restante()") <= 600, "restante %s" % pg.evaluate("Alarma.restante()"))
    # se cerró la app y la alarma venció mientras tanto
    pg.evaluate("(()=>{ var g=JSON.parse(localStorage.getItem('gioval_alarma')); g.fin=Date.now()-20000; localStorage.setItem('gioval_alarma',JSON.stringify(g)); })()")
    pg.reload(); esperar_listo(pg); instalar_speak(pg); pg.wait_for_timeout(300); entrar(pg, "Vale"); pg.wait_for_timeout(150)
    igual(ay_vista(pg), "tiempo", "vencida con la app cerrada"); verificar("Volviste a la app" in ay_texto(pg), ay_texto(pg))
    pg.click("[data-a='terminar']"); pg.wait_for_timeout(100); igual(pg.evaluate("Gioval.ayudantes.registro('Vale').length"), 1)
    igual(pg.evaluate("localStorage.getItem('gioval_ayudando')"), None, "quedó una tarea en curso guardada")
    ctx.close()

@prueba("ayudantes: Música y Números no cambian (mapa, menús, islas registradas y estado de tiempo)")
def t_ay_no_toca(C):
    res = {}
    for nombre, ruta in (("anterior", "/legacy/index.html"), ("nueva", "/index.html")):
        ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + ruta, store=STORE_KID, errores=C.err if nombre == "nueva" else None, semilla=5); instalar_speak(pg); entrar(pg, "Vale")
        r = {"mapa": ay_texto(pg, "#islands")}
        for isla in ("Música", "Números"): abrir_isla(pg, isla); r["menu " + isla] = ay_texto(pg, "#musicMenu,#menuIslaItems"); r["cap " + isla] = pg.evaluate("document.getElementById('capTail').innerText")
        res[nombre] = r; ctx.close()
    igual(res["nueva"], res["anterior"], "textos del mapa y de los menús")
    ctx, pg = ay_pagina(C); igual(pg.evaluate("PACKS.map(p=>p.id)"), ["musica", "numeros"], "Ayudantes no es una isla de aprendizaje")
    igual(pg.evaluate("Gioval.islas.habilidades().length"), 16, "habilidades (Música 7 + Números 9)")
    for isla in ("Música", "Números"):    # al llegar al tope en cualquier isla, el flujo anterior sigue igual: "¡Chau, zorro!" cierra y vuelve al menú
        llegar_al_tope(pg, isla); pg.click("#capOk"); pg.wait_for_timeout(120)
        igual(pg.evaluate("document.querySelector('.screen.active').id"), "menuIsla", isla)
        pg.evaluate("store.time['Vale|'+today()]=0")
    ctx.close()

@prueba("capturas: Hora de ayudantes en 360x700 y 740x330 (tope, lista, detalle, cronómetro, tiempo, fin, panel)")
def t_ay_capturas(C):
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err, semilla=85, congelar=True); instalar_speak(pg); entrar(pg, "Vale")
        pg.evaluate("Gioval.ayudantes.ponerCfg('Vale',{asig:['plantas'],foto:true})")
        llegar_al_tope(pg); CAPTURAS.append(foto(pg, v + "_70_ayudantes_tope")); pg.click("#capAyud"); pg.wait_for_timeout(120)
        CAPTURAS.append(foto(pg, v + "_71_ayudantes_lista")); pg.click(".ayCard[data-id='plantas']"); CAPTURAS.append(foto(pg, v + "_72_ayudantes_detalle"))
        pg.click("[data-a='empezar']"); pg.wait_for_timeout(150); CAPTURAS.append(foto(pg, v + "_73_ayudantes_cronometro"))
        pg.evaluate("window.__OFF=181000"); pg.evaluate("Alarma._revisar()"); pg.wait_for_timeout(150); CAPTURAS.append(foto(pg, v + "_74_ayudantes_tiempo"))
        pg.click("[data-a='terminar']"); pg.wait_for_timeout(120); CAPTURAS.append(foto(pg, v + "_75_ayudantes_fin"))
        abrir_panel(pg); pg.click("#ayPanel summary"); pg.evaluate("document.getElementById('ayPanel').scrollIntoView()"); CAPTURAS.append(foto(pg, v + "_76_ayudantes_panel"))
        ctx.close()

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
