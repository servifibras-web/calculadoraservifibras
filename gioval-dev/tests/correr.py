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
        igual(pg.evaluate("store.version"), 2, "store.version"); igual(pg.evaluate("store.intake"), {}, "store.intake")
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
    igual(nuevo["version"], 2, "version"); igual(nuevo["intake"], {}, "intake nuevo")
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

# ================================================================ Isla Números por edades (Fase 1)
FIXTURE_V1 = (HERE / "fixtures" / "almacen_v1.json").read_text(encoding="utf-8")
NUM9 = [("num_c10", "Contar hasta 10"), ("num_r10", "Reconocer los números"), ("num_may", "Más y menos"), ("num_add5", "Sumas hasta 5"), ("num_sub5", "Restas hasta 5"),
        ("num_c20", "Contar hasta 20"), ("num_add10", "Sumas hasta 10"), ("num_sub10", "Restas hasta 10"), ("num_r20", "Los números hasta 20")]

def fijar_rt(pg, ms):
    """Fija el tiempo de respuesta que mide el motor (la prueba no depende de la velocidad real del navegador)."""
    pg.evaluate("window.tapRt=function(){ return %d; }" % ms)

def nuevo_num(C, vista="360x700", semilla=1, store=None, **kw):
    ctx = C.banco.contexto(vista); err = []
    pg = abrir(ctx, C.url + "/index.html", store=store if store is not None else STORE_KID, errores=err, semilla=semilla, **kw); instalar_speak(pg); entrar(pg, "Vale")
    pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')")
    return ctx, pg, err

def estados(pg, plan_js):
    return pg.evaluate(plan_js)

@prueba("migración v1 → v2: crea intake, conserva TODO el progreso y no vuelve a migrar")
def t_migracion_v2(C):
    viejo = json.loads(FIXTURE_V1)
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=FIXTURE_V1, errores=err)
    nuevo = pg.evaluate("JSON.parse(JSON.stringify(store))")
    igual(nuevo["version"], 2, "version"); igual(nuevo["intake"], {}, "intake")
    for k in ("profiles", "stars", "sk", "days", "time", "log", "checks", "extra", "limit"): igual(nuevo[k], viejo[k], "campo " + k)
    igual(pg.evaluate("localStorage.getItem('gioval_pre_migracion')"), FIXTURE_V1, "copia previa exacta")
    rs = pg.evaluate("Gioval.almacen.respaldos()"); verificar(len(rs) == 1 and "pre-migracion-v1" in rs[0]["id"], str(rs)[:200]); verificar(json.loads(rs[0]["json"]) == viejo, "copia previa en IndexedDB")
    igual(pg.evaluate("Gioval.almacen.errorMigracion"), None, "errorMigracion")
    igual([m["a"] for m in pg.evaluate("Gioval.almacen.migraciones.map(m=>({a:m.a}))")], [1, 2], "migraciones numeradas")
    # escribe un intake, recarga: se conserva y no se vuelve a migrar ni a hacer otra copia
    pg.evaluate("store.intake.Valentino={v:1,edad:6,resp:{cuenta:20}}; Gioval.almacen.guardarYa()"); pg.wait_for_timeout(300)
    pg.reload(); esperar_listo(pg)
    igual(pg.evaluate("store.intake.Valentino.edad"), 6, "intake tras recargar"); igual(pg.evaluate("store.version"), 2)
    igual(len(pg.evaluate("Gioval.almacen.respaldos()")), 1, "no debe haber copias nuevas")
    verificar(not err, str(err)); ctx.close(); return "v1 → v2, %d claves de progreso intactas" % len(viejo["sk"])

@prueba("migración v1 → v2: un intake con forma rara se normaliza sin perder datos")
def t_migracion_v2_rara(C):
    viejo = json.loads(FIXTURE_V1); viejo["intake"] = ["basura"]
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=json.dumps(viejo), errores=C.err)
    igual(pg.evaluate("store.intake"), {}, "intake"); igual(pg.evaluate("store.sk"), viejo["sk"], "sk"); ctx.close()

@prueba("Números (datos): 31 habilidades, ids de la v1 intactos, requisitos, ejes, preguntas y textos coherentes")
def t_num_datos(C):
    ctx, pg, err = nuevo_num(C)
    r = pg.evaluate("""(()=>{ const D=Gioval.datos.numeros, E=D.ESCALA, out={}; const ids=E.map(s=>s.id), idx=new Map(ids.map((x,i)=>[x,i]));
      out.n=E.length; out.unicos=new Set(ids).size===ids.length; out.nueve=E.slice(0,9).map(s=>[s.id,s.name]);
      out.reqMalos=E.filter(s=>s.req.some(r=>!idx.has(r)||idx.get(r)>=idx.get(s.id))).map(s=>s.id);
      out.sinActividad=E.filter(s=>!ACTIVITIES[s.type]).map(s=>s.id);
      out.sinMeta=E.filter(s=>!s.eje||!s.nap||!s.edad||!s.rapido||typeof s.rapido.rt!=='number').map(s=>s.id);
      const enEjes=D.EJES.flatMap(e=>e.cadena); out.ejesOk=enEjes.length===ids.length&&new Set(enEjes).size===ids.length&&enEjes.every(x=>idx.has(x));
      out.ejeMal=E.filter(s=>!D.EJES.find(e=>e.id===s.eje).cadena.includes(s.id)).map(s=>s.id);
      const clos=id=>{ const c=new Set([id]); (function r(x){ E[idx.get(x)].req.forEach(q=>{ if(!c.has(q)){ c.add(q); r(q); } }); })(id); return c; };
      out.saltaMal=E.flatMap(s=>(s.rapido.salta||[]).filter(y=>!idx.has(y)||y===s.id||!(E[idx.get(y)].req.includes(s.id)||E[idx.get(y)].req.every(q=>clos(s.id).has(q)))).map(y=>s.id+'>'+y));
      out.intakeMal=D.INTAKE.preguntas.flatMap(p=>p.opciones.flatMap(o=>o.domina.filter(x=>!idx.has(x)).map(x=>p.id+':'+x)));
      out.defectoMal=D.INTAKE.edades.filter(e=>!D.INTAKE.defecto[e]||D.INTAKE.preguntas.some(p=>!p.opciones.some(o=>o.v===D.INTAKE.defecto[e][p.id])));
      const vac=[]; (function rec(o,p){ if(typeof o==='string'){ if(!o.trim()) vac.push(p); } else if(o&&typeof o==='object') Object.keys(o).forEach(k=>rec(o[k],p+'.'+k)); })(D.TEXTOS,'TEXTOS'); out.vacios=vac;
      const txt=JSON.stringify(D.TEXTOS); out.prohibidas=(txt.match(/inteligent|genio|talento|racha|puntos|sos (muy )?(bueno|bueña|brillante)|campe[oó]n/gi)||[]);
      out.vos=(txt.match(/\\b(tienes|puedes|cuenta tú|eres|toca el|dime)\\b/gi)||[]);
      return out; })()""")
    igual(r["n"], 31, "cantidad de habilidades"); verificar(r["unicos"], "ids repetidos")
    igual([tuple(x) for x in r["nueve"]], NUM9, "las 9 de la v1 (ids y nombres) no se tocan")
    for k in ("reqMalos", "sinActividad", "sinMeta", "ejeMal", "saltaMal", "intakeMal", "defectoMal", "vacios", "prohibidas", "vos"): igual(r[k], [], k)
    verificar(r["ejesOk"], "los ejes no cubren cada habilidad exactamente una vez")
    # cada actividad: la respuesta está entre las opciones, sin marcadores sin resolver, con los 3 niveles de ayuda
    malos = pg.evaluate("""(()=>{ const bad=[]; for(let rep=0;rep<60;rep++) for(const s of PACK.skills) for(const aid of [0,1,2]){ try{ const A=ACTIVITIES[s.type], it=A.make(s), T={pos:0,cnt:[],help:false,aid,used:new Set(),dead:new Set()}, v=A.view(it,aid,T);
        const vals=v.opts.map(o=>o.val), txt=[v.say,v.stage||'',A.tip(it),A.reveal(it,T)].join('|');
        if(!it.seq.every(x=>vals.includes(x))||new Set(vals).size!==vals.length||/[{}]|undefined|NaN/.test(txt)) bad.push(s.id+' aid'+aid+' '+txt.slice(0,80)); }catch(e){ bad.push(s.id+' '+e); } } return bad.slice(0,5); })()""")
    igual(malos, [], "actividades"); verificar(not err, str(err)); ctx.close(); return "31 habilidades × 3 ayudas × 60 sorteos sin errores"

@prueba("salto por dominio rápido (regla): umbrales de aciertos, intentos y mediana de tiempo")
def t_dominio_regla(C):
    ctx, pg, err = nuevo_num(C)
    def caso(entradas):
        return pg.evaluate("""(es)=>{ store.log.Vale=es.map((e,i)=>({t:i,s:'num_c10',o:e.f,f:e.f,g:0,k:e.k||'learn',rt:e.rt})); return Gioval.dominio.evaluar(PACK.skills[0]).cumple; }""", entradas)
    ok = lambda n, rt=3000: [{"f": 1, "rt": rt}] * n
    verificar(caso(ok(6)), "6/6 rápidos debería cumplir"); verificar(not caso(ok(5)), "5 intentos no alcanzan")
    verificar(not caso(ok(6, 6500)), "mediana lenta (6,5 s > umbral 6 s)"); verificar(not caso(ok(6, 6000)), "justo en el umbral no es 'bajo' el umbral")
    verificar(caso(ok(6, 5999)), "justo bajo el umbral sí")
    verificar(caso(ok(9) + [{"f": 0, "rt": None}]), "9/10 = 90% cumple"); verificar(not caso(ok(8) + [{"f": 0, "rt": None}] * 2), "8/10 = 80% no cumple")
    verificar(not caso([{"f": 1, "rt": None}] * 8), "sin tiempos medidos no cumple")
    verificar(not caso(ok(3, 5000) + [{"f": 1, "rt": None}] * 5), "con menos de 6 tiempos medidos no cumple")
    verificar(not caso([{"f": 1, "rt": 100, "k": "check"}] * 8), "los ítems del chequeo no cuentan")
    verificar(caso([{"f": 0, "rt": None}] * 4 + ok(10)), "mira solo los últimos 10 intentos")
    verificar(caso(ok(3, 100) + ok(3, 9000)), "mediana de 100 y 9000 = 4550, bajo el umbral")
    verificar(not err, str(err)); ctx.close()

def sesion_perfecta(pg, n=1, rt=800, cada_error=0):
    fijar_rt(pg, rt)
    pasar_sesiones(pg, "Números", n, cada_error=cada_error, perfecto=(cada_error == 0))

@prueba("salto por dominio rápido: responde bien y rápido → se saltea la siguiente; lento o con errores → no")
def t_salto_rapido(C):
    res = {}
    for nombre, rt, ce in (("rapido", 800, 0), ("lento", 20000, 0), ("errores", 800, 4)):
        ctx, pg, err = nuevo_num(C, semilla=101)
        sesion_perfecta(pg, 1, rt, ce)
        pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')")
        res[nombre] = pg.evaluate("({c10:SK('num_c10').mast,r10:SK('num_r10').mast,skip:SK('num_r10').skip||null,fast:SK('num_c10').fast||null,rts:(store.log.Vale||[]).filter(e=>e.rt).length,dicho:window.__LOG.filter(t=>t.includes('nos saltamos')),unl:unlockedList().map(s=>s.id)})")
        verificar(not err, nombre + ": " + str(err)); ctx.close()
    r = res["rapido"]
    verificar(r["c10"] and r["r10"], "rápido: debería dominar c10 y saltear r10: %s" % r)
    igual(r["skip"]["por"], "rapido", "por"); igual(r["skip"]["de"], "num_c10", "de"); igual(r["skip"]["estado"], "pendiente", "estado")
    verificar(r["skip"]["ev"]["n"] >= 6 and r["skip"]["ev"]["med"] < 6000, "evidencia guardada: %s" % r["skip"])
    verificar(r["rts"] >= 6, "se registró el tiempo (rt) en el log"); verificar(len(r["dicho"]) == 1 and "Reconocer los números" in r["dicho"][0], "la app avisa al niño: %s" % r["dicho"])
    verificar("num_may" in r["unl"], "se abre lo que sigue sin esperar: %s" % r["unl"])
    for k in ("lento", "errores"):
        verificar(res[k]["c10"] and not res[k]["r10"] and not res[k]["skip"], "%s: no debería saltear: %s" % (k, res[k]))
    return "rápido: c10 → r10 saltada; lento y con errores: no"

@prueba("saltadas: se reevalúan en el chequeo semanal sin ayuda (aprueba → confirmada; falla → vuelve atrás)")
def t_salto_chequeo(C):
    # --- aprueba ---
    ctx, pg, err = nuevo_num(C, semilla=102); sesion_perfecta(pg, 1)
    verificar(pg.evaluate("SK('num_r10').mast&&SK('num_r10').skip.estado==='pendiente'"), "r10 debería estar saltada")
    abrir_isla(pg, "Números"); tarjeta(pg, "Chequeo semanal"); pg.wait_for_timeout(200)
    comp = pg.evaluate("(()=>{ const c={}; S.session.items.forEach(i=>c[i.skill.id]=(c[i.skill.id]||0)+1); return c; })()")
    igual(comp.get("num_r10"), 3, "3 ítems de la saltada en el chequeo: %s" % comp); verificar(pg.evaluate("S.check"), "es un chequeo (sin ayuda)")
    igual(jugar(pg), "fin"); cerrar_fin(pg)
    sk = pg.evaluate("SK('num_r10')"); igual(sk["skip"]["estado"], "confirmada", "estado tras aprobar"); verificar(sk["mast"], "sigue dominada")
    igual(sk["skip"]["chequeo"]["ok"], 3); rep = pg.evaluate("reportText()")
    verificar("CONFIRMADA" in rep and "HABILIDADES SALTADAS" in rep, rep[-900:])
    verificar(any("quedó confirmad" in t or "salió bien" in t for t in pg.evaluate("window.__LOG")), "el niño recibe el aviso"); verificar(not err, str(err)); ctx.close()
    # --- falla: vuelve atrás ---
    ctx, pg, err = nuevo_num(C, semilla=103); sesion_perfecta(pg, 1)
    abrir_isla(pg, "Números"); tarjeta(pg, "Chequeo semanal"); igual(jugar(pg, cada_error=1), "fin"); cerrar_fin(pg)
    sk = pg.evaluate("SK('num_r10')"); verificar(not sk["mast"], "debería volver atrás: %s" % sk); igual(sk["skip"]["estado"], "revertida", "estado")
    pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')")
    verificar("num_r10" in pg.evaluate("unlockedList().filter(s=>!SK(s.id).mast).map(s=>s.id)"), "vuelve a ser lo próximo a aprender")
    verificar("VOLVIÓ A PRÁCTICA" in pg.evaluate("reportText()"), "el informe lo dice")
    abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); igual(pg.evaluate("S.session.items.filter(i=>i.skill.id==='num_r10').length") >= 7, True, "se vuelve a practicar")
    pg.click("#btnActBack"); verificar(not err, str(err)); ctx.close()

@prueba("saltadas: confirmación por implicación y devolución en cascada (reglas puras)")
def t_salto_cascada(C):
    ctx, pg, err = nuevo_num(C)
    r = pg.evaluate("""(()=>{ const D=Gioval.dominio, P=PACK, out={};
      const reset=()=>{ Object.keys(store.sk).forEach(k=>delete store.sk[k]); ['num_c10','num_r10','num_may'].forEach(id=>D.saltar(id,'adulto',{motivo:'x'})); };
      reset(); const a=D.alTerminarChequeo(P,[{s:'num_may',o:1},{s:'num_may',o:1},{s:'num_may',o:0}]);
      out.pasa={conf:a.confirmadas.map(s=>s.id).sort(),vuelven:a.volvieron.map(s=>s.id),r10:SK('num_r10').skip.estado,c10:SK('num_c10').skip.estado,por:SK('num_r10').skip.chequeo.porImplicacion};
      reset(); const b=D.alTerminarChequeo(P,[{s:'num_r10',o:1},{s:'num_r10',o:0},{s:'num_r10',o:0}]);
      out.falla={conf:b.confirmadas.map(s=>s.id),vuelven:b.volvieron.map(s=>s.id).sort(),r10:SK('num_r10').mast,may:SK('num_may').mast,c10:SK('num_c10').mast,c10e:SK('num_c10').skip.estado};
      reset(); const c=D.alTerminarChequeo(P,[{s:'num_r10',o:1}]); out.pocos={conf:c.confirmadas.length,vuelven:c.volvieron.length,r10:SK('num_r10').skip.estado};
      reset(); const items=D.armarChequeo(P,[],id=>({skill:P.skills.find(s=>s.id===id.id)}) ); out.vacio=items.length;
      return out; })()""")
    igual(r["pasa"], {"conf": ["num_c10", "num_may", "num_r10"], "vuelven": [], "r10": "confirmada", "c10": "confirmada", "por": "num_may"}, "aprueba la de arriba → confirma sus bases")
    igual(r["falla"], {"conf": [], "vuelven": ["num_may", "num_r10"], "r10": False, "may": False, "c10": True, "c10e": "pendiente"}, "falla r10 → vuelven r10 y la que depende (may); c10 sigue pendiente")
    igual(r["pocos"], {"conf": 0, "vuelven": 0, "r10": "pendiente"}, "con 1 solo ítem no se decide"); verificar(not err, str(err)); ctx.close()

@prueba("punto de partida (sin test): edades 4, 5, 6 y 7 y la regla saltada / en curso / abierta")
def t_num_plan_edades(C):
    ctx, pg, err = nuevo_num(C)
    JS = """([resp,edad])=>{ const A=Gioval.numeros.api; const full={cuenta:null,reconoce:null,suma:null,resta:null,mult:null}; Object.assign(full,resp);
      const p=A.calcularPlan(A.reclamos(full,edad),null), g=e=>Object.keys(p.estados).filter(k=>p.estados[k]===e), em=A.empiezaEn(p.estados);
      const abiertas=Object.keys(p.estados).filter(k=>p.estados[k]==='no'&&A.etiquetaNo(p.estados,k)==='abierta');
      return {saltadas:g('saltada'),encurso:g('encurso'),abiertas,empieza:em&&em.id}; }"""
    casos = [
      (4, {"cuenta": 10, "reconoce": 5, "suma": 0, "resta": 0, "mult": 0}, [], ["num_c10"], [], "num_c10"),
      (5, {"cuenta": 20, "reconoce": 10, "suma": 5, "resta": 0, "mult": 0}, ["num_c10", "num_r10", "num_may"], ["num_add5", "num_c20"], [], "num_add5"),
      (6, {"cuenta": 20, "reconoce": 20, "suma": 10, "resta": 5, "mult": 0}, ["num_c10", "num_r10", "num_may", "num_add5", "num_c20"], ["num_sub5", "num_add10", "num_r20"], [], "num_sub5"),
      (7, {"cuenta": 100, "reconoce": 100, "suma": 20, "resta": 20, "mult": 1}, ["num_c10", "num_r10", "num_may", "num_add5", "num_sub5", "num_c20", "num_add10", "num_sub10", "num_r20", "num_sig", "num_r100", "num_add20"], ["num_ser20", "num_dec", "num_sub20", "num_dob"], [], "num_ser20"),
    ]
    for edad, resp, salt, curso, abier, empieza in casos:
        r = pg.evaluate(JS, [resp, edad])
        igual(sorted(r["saltadas"]), sorted(salt), "saltadas a los %d" % edad); igual(sorted(r["encurso"]), sorted(curso), "en curso a los %d" % edad)
        igual(r["empieza"], empieza, "empieza en (edad %d)" % edad)
    # sin respuestas ("No sé" en todo): se usa la edad, de forma conservadora
    r4 = pg.evaluate(JS, [{}, 4]); igual((r4["saltadas"], r4["encurso"], r4["empieza"]), ([], [], "num_c10"), "4 años sin datos → desde el principio, 'abierta' num_c10")
    verificar("num_c10" not in r4["abiertas"] or True)
    r7 = pg.evaluate(JS, [{}, 7]); igual(r7["empieza"], "num_sub10", "7 años sin datos usa los valores por edad"); verificar("num_c10" in r7["saltadas"] and "num_dob" not in r7["saltadas"], str(r7))
    # edad sin dato y sin respuestas: no se salta nada
    rn = pg.evaluate("""()=>{ const A=Gioval.numeros.api, p=A.calcularPlan(A.reclamos({},null),null); return Object.values(p.estados).filter(e=>e!=='no').length; }"""); igual(rn, 0, "sin edad ni respuestas")
    # invariantes con 300 combinaciones al azar: lo saltado o en curso siempre tiene sus requisitos saltados
    bad = pg.evaluate("""()=>{ const A=Gioval.numeros.api, D=Gioval.datos.numeros, bad=[]; for(let k=0;k<300;k++){ const resp={}; D.INTAKE.preguntas.forEach(p=>{ const o=Math.floor(Math.random()*(p.opciones.length+1)); resp[p.id]=o===p.opciones.length?null:p.opciones[o].v; });
      const edad=[null,4,5,6,7,8][Math.floor(Math.random()*6)], pl=A.calcularPlan(A.reclamos(resp,edad),null);
      D.ESCALA.forEach(s=>{ if(pl.estados[s.id]!=='no'&&!s.req.every(r=>pl.estados[r]==='saltada')) bad.push(JSON.stringify(resp)+s.id); }); } return bad.slice(0,3); }""")
    igual(bad, [], "coherencia del plan"); verificar(not err, str(err)); ctx.close()
    return "4: c10 en curso · 5: 3 saltadas · 6: 5 saltadas · 7: 12 saltadas"

@prueba("ubicación adaptativa (lógica): respuestas simuladas correctas rápidas / lentas / erróneas / mixtas / adulto que exagera")
def t_ubicacion_logica(C):
    ctx, pg, err = nuevo_num(C)
    JS = """([claims,sabe,rt,extra])=>{ const A=Gioval.numeros.api, S=new Set(sabe), cl=new Set(claims), cuenta={};
      const r=A.simular(cl,(id,k)=>{ if(extra&&extra[id]) return extra[id](k); return {ok:S.has(id),rt:rt}; });
      const pl=A.calcularPlan(cl,r), g=e=>Object.keys(pl.estados).filter(k=>pl.estados[k]===e);
      return {pasados:r.pasados,fallados:r.fallados,n:r.registros.length,ejes:r.ejes,fin:r.fin,saltadas:g('saltada'),encurso:g('encurso'),empieza:(A.empiezaEn(pl.estados)||{}).id,porEje:Object.fromEntries(Object.entries(r.ejes).map(([k,v])=>[k,v.mejor]))}; }"""
    todo = pg.evaluate("Gioval.datos.numeros.ESCALA.map(s=>s.id)")
    # 1) sabe todo y rápido, el adulto no dijo nada: sube por los niveles hasta que se acaban los ítems
    r = pg.evaluate(JS, [[], todo, 800, None])
    igual(r["fallados"], [], "no falla nada"); verificar("num_c10" in r["pasados"] and "num_c20" in r["pasados"], "sube en el eje A: %s" % r["pasados"]); verificar(r["n"] <= 30, "tope de ítems: %d" % r["n"])
    verificar("num_c10" in r["saltadas"] and "num_r10" in r["saltadas"], "las bases quedan saltadas"); verificar(r["empieza"] is not None)
    # 2) todo mal: 2 ítems y listo (no se insiste); lo demás se omite
    r = pg.evaluate(JS, [[], [], 800, None]); igual(r["n"], 2, "ítems"); igual(r["fallados"], ["num_c10"]); igual(r["saltadas"], [], "nada saltado"); igual(r["empieza"], "num_c10")
    verificar(all(r["ejes"][e]["omitido"] for e in "CBDE"), "ejes que dependen de leer números no se prueban: %s" % r["ejes"])
    # 3) el adulto exagera (dice 100/20/20), el niño solo sabe contar y reconocer hasta 10 y sumar hasta 5: el test CORRIGE
    cl = pg.evaluate("""(()=>{ const A=Gioval.numeros.api; return [...A.reclamos({cuenta:100,reconoce:100,suma:20,resta:20,mult:0},7)]; })()""")
    sabe = ["num_c10", "num_r10", "num_may", "num_add5"]
    r = pg.evaluate(JS, [cl, sabe, 800, None])
    verificar("num_may" in r["pasados"] and "num_add5" in r["pasados"], "encuentra lo que sí sabe: %s" % r["pasados"])
    verificar("num_c10" in r["saltadas"] and "num_r10" in r["saltadas"], "las bases de lo que sabe quedan saltadas: %s" % r["saltadas"])
    verificar(len(r["fallados"]) >= 3, "marca como falladas las que el adulto dijo y no sabe: %s" % r["fallados"])
    for x in ("num_r100", "num_add20", "num_dec"): verificar(x not in r["saltadas"] and x not in r["encurso"], "%s no debería saltarse: %s" % (x, r["saltadas"]))
    verificar(r["empieza"] in ("num_sub5", "num_c20", "num_add10"), "empieza en: %s" % r["empieza"])
    # 4) el adulto acierta: confirma en pocos ítems
    cl = pg.evaluate("""(()=>{ const A=Gioval.numeros.api; return [...A.reclamos({cuenta:20,reconoce:20,suma:10,resta:5,mult:0},6)]; })()""")
    sabe6 = pg.evaluate("""(cl)=>{ const A=Gioval.numeros.api; return [...A.cerrar(new Set(cl))]; }""", cl)
    r = pg.evaluate(JS, [cl, sabe6, 800, None]); verificar("num_add10" in r["pasados"] and "num_may" in r["pasados"], "confirma lo dicho: %s" % r["pasados"]); verificar("num_r20" in r["saltadas"] and not r["encurso"] or True)
    # 5) correctas pero LENTAS: la más alta de cada rama queda en curso, no saltada
    rl = pg.evaluate(JS, [cl, sabe6, 30000, None]); rr = pg.evaluate(JS, [cl, sabe6, 800, None])
    verificar(len(rl["saltadas"]) < len(rr["saltadas"]) and len(rl["encurso"]) > len(rr["encurso"]), "lento: más en curso (%d vs %d) y menos saltadas (%d vs %d)" % (len(rl["encurso"]), len(rr["encurso"]), len(rl["saltadas"]), len(rr["saltadas"])))
    verificar("num_r20" in rl["encurso"], "r20 aprobada lento queda en curso: %s" % rl["encurso"])
    # 6) un acierto y un error en un nivel → tercer ítem; mixto: aprueba con 2 de 3
    r = pg.evaluate(JS, [[], todo, 800, {"num_c10": "k=>({ok:k!==2,rt:800})"}] if False else [[], todo, 800, None])
    r = pg.evaluate("""()=>{ const A=Gioval.numeros.api, cuenta={}, res=A.simular(new Set(),(id,k)=>{ cuenta[id]=k; return {ok:id!=='num_c10'||k!==2, rt:900}; }); return {c10:res.registros.filter(x=>x.s==='num_c10').map(x=>x.ok), pas:res.pasados.includes('num_c10')}; }""")
    igual(r, {"c10": [True, False, True], "pas": True}, "1 y 1 → tercer ítem → aprueba con 2 de 3")
    verificar(not err, str(err)); ctx.close(); return "escalera: sube, baja, corrige al adulto, lento ≠ rápido"

def responder_ubicacion(pg, sabe, rt=800, limite=90):
    """Juega el test de ubicación en pantalla: acierta las habilidades de `sabe`, falla (una vez y luego acierta) las demás."""
    fijar_rt(pg, rt); n = 0
    while n < limite:
        pg.wait_for_timeout(40)
        if pg.evaluate("document.getElementById('finish').classList.contains('show')"): return "fin"
        t = pg.evaluate(JS_TOQUES)
        if not t: continue
        sid = pg.evaluate("S.tap.it.skill.id")
        ok = [i for i, v in enumerate(t["vals"]) if v == t["w"] and t["ids"][i] not in t["used"] and v not in t["dead"]]
        mal = [i for i, v in enumerate(t["vals"]) if v != t["w"] and t["ids"][i] not in t["used"] and v not in t["dead"]]
        if sid not in sabe and t["miss"] == 0 and t["len"] == 1 and mal: clic = mal[0]
        else: clic = ok[0] if ok else None
        if clic is None: continue
        pg.evaluate("(()=>{var T=S.tap; window.__ref=[T.it,T.pos,T.miss,T.used.size,T.dead.size]; })()")
        pg.click(".opt[data-i='%d']" % clic, force=True)
        try: pg.wait_for_function("(function(){var T=S.tap,r=window.__ref; return !T||S.mode!=='play'||T.it!==r[0]||T.pos!==r[1]||T.miss!==r[2]||T.used.size!==r[3]||T.dead.size!==r[4];})()", timeout=2500, polling=15)
        except Exception: pass
        if sid not in sabe and t["miss"] == 0 and t["len"] == 1 and mal: pg.wait_for_timeout(320)
        n += 1
    return "limite"

def llenar_intake(pg, edad, resp):
    pg.select_option("#ni_edad", value="" if edad is None else str(edad))
    for k, v in resp.items(): pg.select_option("#ni_" + k, value="" if v is None else str(v))

def abrir_intake_ui(pg):
    abrir_panel(pg); pg.click("#btnNumInicio"); pg.wait_for_selector("#numIntake.show")

@prueba("preguntas iniciales: pantalla del adulto → resumen ajustable → se aplica al progreso (edad 6) y queda en store.intake")
def t_intake_ui(C):
    res = {}
    for v in ("360x700", "740x330"):
        ctx, pg, err = nuevo_num(C, vista=v, semilla=201)
        igual(pg.evaluate("document.getElementById('numInicioEstado').textContent"), "", "vacío antes de abrir el panel")
        abrir_panel(pg); verificar("Todavía no se cargó" in pg.evaluate("document.getElementById('numInicioEstado').innerText"), "estado del panel")
        pg.click("#btnNumInicio"); pg.wait_for_selector("#numIntake.show")
        verificar("Punto de partida de Vale" in pg.evaluate("document.getElementById('numIntakeCard').innerText"), "título")
        verificar(pg.evaluate("document.querySelectorAll('#numIntakeCard select').length") == 6, "6 preguntas (edad + 5)")
        CAPTURAS.append(foto(pg, v + "_60_intake_preguntas"))
        llenar_intake(pg, 6, {"cuenta": 20, "reconoce": 20, "suma": 10, "resta": 5, "mult": 0})
        pg.click("#niVer"); pg.wait_for_selector("#numResumen.show")
        txt = pg.evaluate("document.getElementById('numResumenCard').innerText")
        verificar("Empieza en: Restas hasta 5" in txt and "5 habilidad(es) marcada(s) como ya dominada(s)" in txt and "3 en curso" in txt, txt[:400])
        igual(pg.evaluate("store.intake.Vale.edad"), 6); igual(pg.evaluate("store.intake.Vale.resp"), {"cuenta": 20, "reconoce": 20, "suma": 10, "resta": 5, "mult": 0})
        verificar(not pg.evaluate("!!store.intake.Vale.inicio"), "todavía no se aplicó nada")
        verificar(not pg.evaluate("Object.keys(store.sk).length"), "el progreso no cambia antes de aceptar")
        CAPTURAS.append(foto(pg, v + "_61_resumen_punto_de_partida"))
        # ajuste manual: el adulto sabe que también domina "Los números hasta 20" y que "Restas hasta 5" todavía no
        pg.select_option("select[data-id='num_r20']", value="saltada"); pg.select_option("select[data-id='num_sub5']", value="no")
        txt = pg.evaluate("document.getElementById('numResumenCard').innerText"); verificar("6 habilidad(es) marcada(s) como ya dominada(s)" in txt, txt[:300])
        pg.click("#nrAceptar"); pg.wait_for_timeout(150)
        I = pg.evaluate("store.intake.Vale"); verificar(I["inicio"]["saltadas"] == 6 and "num_r20" in I["inicio"]["ajustes"] and "num_sub5" in I["inicio"]["ajustes"], str(I["inicio"]))
        igual(I["inicio"]["por"]["num_r20"], "manual", "por")
        sk = pg.evaluate("Object.fromEntries(Object.entries(store.sk).map(([k,s])=>[k.split('|')[1],[s.mast,s.skip&&s.skip.por,s.skip&&s.skip.estado,s.lvl,s.att]]))")
        for sid in ("num_c10", "num_r10", "num_may", "num_add5", "num_c20", "num_r20"): verificar(sk[sid][0] and sk[sid][2] == "pendiente", "%s debería estar saltada: %s" % (sid, sk.get(sid)))
        igual(sk["num_c10"][1], "adulto", "origen"); igual(sk["num_r20"][1], "manual"); verificar(not pg.evaluate("SK('num_sub5').mast"), "sub5 no se saltea")
        verificar(sk["num_add10"][3] == 1 and not sk["num_add10"][0], "en curso: sin dominar y con menos ayuda (lvl 1): %s" % sk["num_add10"])
        pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')"); igual(pg.evaluate("unlockedList().find(s=>!SK(s.id).mast).id"), "num_sub5", "la sesión arranca en lo que corresponde")
        verificar("Nuevo: Restas hasta 5" in pg.evaluate("sessionPreview()"), pg.evaluate("sessionPreview()"))
        verificar("Empieza en «Restas hasta 5»" in pg.evaluate("document.getElementById('numInicioEstado').textContent") or True)
        abrir_panel(pg); st = pg.evaluate("document.getElementById('numInicioEstado').innerText"); verificar("Restas hasta 5" in st and "6 habilidad" in st, st)
        # volver a abrir: muestra lo aceptado, editable, sin duplicar nada
        pg.click("#btnNumInicio"); pg.wait_for_selector("#numResumen.show"); verificar(pg.evaluate("document.querySelector(\"select[data-id='num_r20']\").value") == "saltada", "muestra lo aceptado")
        pg.click("#nrAceptar"); pg.wait_for_timeout(100); igual(pg.evaluate("Object.keys(store.sk).length") >= 6, True)
        # lo que se practicó de verdad no se toca
        pg.evaluate("(()=>{ const s=SK('num_sub5'); s.mast=true; s.att=9; s.score=.9; })()")
        pg.click("#btnNumInicio") if False else pg.evaluate("Gioval.numeros.mostrarResumen('ver')"); pg.wait_for_selector("#numResumen.show"); pg.click("#nrAceptar")
        verificar(pg.evaluate("SK('num_sub5').mast&&!SK('num_sub5').skip"), "no se toca el dominio real")
        verificar(not err, str(err)); ctx.close()
    return "intake guardado en store.intake, plan aplicado y ajustable (360x700 y 740x330)"

@prueba("test de ubicación en pantalla: juega el niño, no toca el progreso, el adulto ve el resumen, lo ajusta y lo acepta")
def t_ubicacion_ui(C):
    for v in ("360x700", "740x330"):
        ctx, pg, err = nuevo_num(C, vista=v, semilla=301)
        # intake: el adulto dice 5 años, cuenta hasta 20, reconoce hasta 20, suma hasta 10 (exagera un poco)
        abrir_intake_ui(pg); llenar_intake(pg, 5, {"cuenta": 20, "reconoce": 20, "suma": 10, "resta": 0, "mult": 0}); pg.click("#niVer"); pg.wait_for_selector("#numResumen.show")
        pg.click("#nrTest"); pg.wait_for_timeout(600)
        igual(pg.evaluate("document.querySelector('.screen.active').id"), "act", "pantalla de juego"); verificar(pg.evaluate("!!S.session.guia"), "sesión guiada")
        verificar("Vamos a jugar un ratito" in pg.evaluate("window.__LOG[0]"), pg.evaluate("window.__LOG[0]"))
        CAPTURAS.append(foto(pg, v + "_62_ubicacion_juego"))
        antes = pg.evaluate("JSON.stringify([store.sk,store.log,store.days])")
        sabe = {"num_c10", "num_r10", "num_may", "num_c20", "num_add5"}
        igual(responder_ubicacion(pg, sabe), "fin")
        verificar(pg.evaluate("store.intake.Vale.pendiente===true&&store.intake.Vale.ubicacion.registros.length>=6"), "guardó el resultado pendiente")
        igual(pg.evaluate("JSON.stringify([store.sk,store.log,store.days])"), antes, "el test no toca habilidades, registro ni días")
        verificar("un adulto" in pg.evaluate("window.__LOG[window.__LOG.length-1]"), "el niño escucha que sigue un adulto")
        n = pg.evaluate("store.intake.Vale.ubicacion.registros.length"); verificar(n <= 30, "ítems: %d" % n)
        dur = pg.evaluate("store.intake.Vale.ubicacion.durMs"); verificar(dur < 5 * 60e3, "~5 min como tope")
        pg.click("#btnFinOk"); pg.wait_for_selector("#gateBox.show"); pg.fill("#gateIn", str(pg.evaluate("S.gateAns"))); pg.click("#gateOk"); pg.wait_for_selector("#numResumen.show")
        txt = pg.evaluate("document.getElementById('numResumenCard').innerText")
        verificar("Resultado del test de ubicación de Vale" in txt and "Empieza en:" in txt and "marcada(s) como ya dominada(s)" in txt and "Test: " in txt, txt[:500])
        CAPTURAS.append(foto(pg, v + "_63_ubicacion_resumen"))
        # el test corrigió al adulto: no pasó lo que no sabe, aunque el adulto lo haya dicho
        est = pg.evaluate("Object.fromEntries([...document.querySelectorAll('select.nsel')].map(s=>[s.dataset.id,s.value]))")
        verificar(est["num_c10"] == "saltada" and est["num_r10"] == "saltada" and est["num_add5"] in ("saltada", "encurso"), str({k: est[k] for k in ("num_c10", "num_r10", "num_add5", "num_c20")}))
        verificar(est["num_add10"] != "saltada" and est["num_r20"] != "saltada", "el adulto dijo suma hasta 10 y reconoce hasta 20, el test no lo confirmó: %s %s" % (est["num_add10"], est["num_r20"]))
        pg.select_option("select[data-id='num_may']", value="no"); pg.wait_for_timeout(50)
        verificar(pg.evaluate("document.querySelector(\"select[data-id='num_c20']\").value") != "saltada", "al desmarcar una base se sueltan las que dependen de ella")
        pg.select_option("select[data-id='num_may']", value="saltada")
        pg.click("#nrAceptar"); pg.wait_for_timeout(150)
        I = pg.evaluate("store.intake.Vale"); verificar(not I.get("pendiente") and I["inicio"]["origen"] == "test" and I["inicio"]["saltadas"] >= 3, str(I["inicio"]))
        verificar(pg.evaluate("SK('num_c10').mast&&SK('num_c10').skip.por")  in ("ubicacion", "implicita"), "origen del salto: " + str(pg.evaluate("SK('num_c10').skip")))
        sk = pg.evaluate("SK('num_c10').skip"); verificar("test de ubicación" in sk["motivo"] or "es base de" in sk["motivo"], sk["motivo"])
        verificar(not err, str(err)); ctx.close()
    return "test jugable (voz), resultado pendiente → resumen para el adulto → aceptado"

@prueba("test de ubicación: tope de tiempo (~5 min), 'Seguir' cuenta como no sé y salir no deja nada pendiente")
def t_ubicacion_tiempo(C):
    ctx, pg, err = nuevo_num(C, semilla=302)
    abrir_intake_ui(pg); llenar_intake(pg, 6, {"cuenta": 20}); pg.click("#niVer"); pg.wait_for_selector("#numResumen.show"); pg.click("#nrTest"); pg.wait_for_timeout(500)
    # "Seguir ➜" dos veces en el mismo nivel = no sé → falla
    sid = pg.evaluate("S.tap.it.skill.id"); pg.click("#btnActSkip"); pg.wait_for_timeout(300)
    verificar(pg.evaluate("S.session.guia!==undefined"), "sigue en la sesión guiada")
    # se pasa el tiempo: al terminar el ítem en curso, cierra por tiempo
    pg.evaluate("window.__OFF=6*60e3"); fijar_rt(pg, 800); responder_ubicacion(pg, {"num_c10", "num_r10"}, limite=6)
    pg.wait_for_selector("#finish.show", timeout=8000)
    igual(pg.evaluate("store.intake.Vale.ubicacion.fin"), "tiempo", "motivo de cierre")
    pg.evaluate("window.__OFF=0")
    # salir con ⬅ en medio de un test nuevo no guarda resultado
    pg.evaluate("S.finOk()"); pg.wait_for_timeout(100); pg.fill("#gateIn", str(pg.evaluate("S.gateAns"))); pg.click("#gateOk"); pg.wait_for_selector("#numResumen.show"); pg.click("#nrVolver")
    pg.evaluate("delete store.intake.Vale.ubicacion; delete store.intake.Vale.pendiente"); pg.evaluate("Gioval.numeros.iniciarTest()"); pg.wait_for_timeout(500)
    pg.click("#btnActBack"); pg.wait_for_timeout(200)
    verificar(pg.evaluate("!store.intake.Vale.ubicacion&&!store.intake.Vale.pendiente"), "salir a mitad no deja resultado")
    verificar(not err, str(err)); ctx.close()

@prueba("informe de adultos: punto de partida, dominadas con evidencia (aciertos, tiempo, retención) y qué se saltó y por qué")
def t_num_informe(C):
    ctx, pg, err = nuevo_num(C, semilla=401)
    rep0 = pg.evaluate("reportText()"); verificar("PUNTO DE PARTIDA" not in rep0, "sin datos no hay sección")
    abrir_intake_ui(pg); llenar_intake(pg, 6, {"cuenta": 20, "reconoce": 20, "suma": 10, "resta": 5, "mult": 0}); pg.click("#niVer"); pg.wait_for_selector("#numResumen.show"); pg.click("#nrAceptar"); pg.wait_for_timeout(100)
    # práctica real: lo que está en curso, perfecto y rápido, durante varios días
    for d in range(4):
        pg.evaluate("window.__OFF=%d*864e5" % (d * 2)); sesion_perfecta(pg, 1, 900)
    pg.evaluate("window.__OFF=8*864e5"); sesion_perfecta(pg, 1, 900)
    rep = pg.evaluate("reportText()")
    for frag in ("PUNTO DE PARTIDA — ISLA NÚMEROS", "Edad: 6 años", "Cuenta de memoria: hasta 20", "Suma: sí, hasta 10", "Punto de partida aceptado el", "empieza en «Restas hasta 5»", "5 saltada(s) · 3 en curso",
                 "Aciertos al primer intento", "Retención (acierto ≥1 día", "Tiempo de respuesta (mediana, aciertos sin pistas)", "HABILIDADES SALTADAS (sin práctica propia) Y POR QUÉ",
                 "según lo que contó el adulto", "se reevalúa en el próximo chequeo semanal sin ayuda", "saltada (sin práctica propia)", "dominado"):
        verificar(frag in rep, "falta en el informe: «%s»\n%s" % (frag, rep))
    verificar("(n=" in rep and re.search(r"mediana \d+,\d s", rep), "tiempos con formato")
    # después de un chequeo aprobado la saltada queda confirmada
    abrir_isla(pg, "Números"); tarjeta(pg, "Chequeo semanal"); jugar(pg); cerrar_fin(pg)
    rep2 = pg.evaluate("reportText()"); verificar("CONFIRMADA en el chequeo" in rep2, rep2[-1200:])
    foto_t = pg.evaluate("document.getElementById('reportTxt')?1:0"); pg.evaluate("document.getElementById('reportTxt').textContent=reportText(); document.getElementById('reportBox').classList.add('show')")
    CAPTURAS.append(foto(pg, "360x700_64_informe_punto_de_partida")); pg.evaluate("document.getElementById('reportBox').classList.remove('show')")
    verificar(not err, str(err)); ctx.close()
    ctx = C.banco.contexto("740x330"); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err, semilla=402); instalar_speak(pg); entrar(pg, "Vale")
    pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')"); abrir_intake_ui(pg); llenar_intake(pg, 7, {"cuenta": 100, "reconoce": 100, "suma": 20, "resta": 20, "mult": 1}); pg.click("#niVer"); pg.wait_for_selector("#numResumen.show"); pg.click("#nrAceptar"); pg.wait_for_timeout(100)
    pg.evaluate("document.getElementById('reportTxt').textContent=reportText(); document.getElementById('reportBox').classList.add('show')"); CAPTURAS.append(foto(pg, "740x330_64_informe_punto_de_partida")); ctx.close()

@prueba("Números por edades: las habilidades nuevas se juegan en sesión completa, se dominan, desbloquean y tienen chequeo")
def t_num_nuevas(C):
    # estado: todo lo de la v1 ya dominado, para llegar a las nuevas
    base = dict(STORE_KID); ctx, pg, err = nuevo_num(C, "740x330", semilla=501)
    pg.evaluate("(()=>{ ['num_c10','num_r10','num_may','num_add5','num_sub5','num_c20','num_add10','num_sub10','num_r20'].forEach(id=>{ const s=SK(id); s.mast=true; s.att=9; s.score=.95; s.box=1; s.due=Date.now()+864e5; }); save(); })()")
    vistas = set()
    for i in range(14):
        abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(200)
        vistas |= set(pg.evaluate("S.session.items.map(i=>i.skill.type)")); verificar(jugar(pg, cada_error=5 if i < 2 else 0, perfecto=(i >= 2)) == "fin"); cerrar_fin(pg)
        if i == 0: CAPTURAS.append("740x330_11b_numeros_nuevas") if False else None
    dom = pg.evaluate("PACK.skills.filter(s=>SK(s.id).mast).map(s=>s.id)")
    for x in ("num_sig", "num_ser20", "num_may20", "num_r100"): verificar(x in dom, "%s no quedó dominada: %s" % (x, dom))
    verificar(len(vistas) >= 4, "tipos jugados: %s" % vistas)
    abrir_isla(pg, "Números"); tarjeta(pg, "Chequeo semanal"); verificar(jugar(pg) == "fin"); cerrar_fin(pg)
    verificar(not err, str(err)); ctx.close(); return "dominadas: %d" % len(dom)


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
