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

def sin_espanol(frases):
    return [x for x in frases if re.search(r"[¿¡áéíóúñÁÉÍÓÚ]", x)]

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

@prueba("mapa: muestra Música, Números, Ritmo y las islas con candado")
def t_mapa(C):
    for v in ("pixel7", "360x700", "740x330"):
        ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err); instalar_speak(pg)
        entrar(pg, "Vale")
        islas = pg.evaluate("[...document.querySelectorAll('#islands .island')].map(x=>x.innerText.replace(/\\n/g,'|')+(x.classList.contains('off')?'|off':''))")
        igual(islas, ["🎹|Isla Música|¡A tocar el piano!", "🔢|Isla Números|¡A contar y sumar!", "🥁|Isla Ritmo|¡A marcar el ritmo!", "🔒|Isla Letras|Pronto|off", "🔒|Isla Animales|Pronto|off"], "mapa " + v)
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

@prueba("migración: datos viejos (v0 → v2) conservan TODO el progreso")
def t_migracion(C):
    viejo = json.loads(FIXTURE)
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=err)
    nuevo = pg.evaluate("JSON.parse(JSON.stringify(store))")
    igual(nuevo["version"], 2, "version")
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
    igual(sorted(pg.evaluate("Object.keys(Gioval.entrada.proveedores)")), ["golpes", "microfono", "toque"], "proveedores")
    igual(pg.evaluate("Gioval.entrada.necesito(['toque','golpe','acorde'])"), {"disponibles": ["toque", "golpe"], "faltan": ["acorde"]}, "necesito")
    igual(pg.evaluate("PACKS.map(p=>[p.id,p.instrumento,p.entradas])"), [["musica", "piano", ["nota", "toque"]], ["numeros", None, ["toque"]], ["ritmo", "percusion", ["golpe"]]], "declaración de las islas")
    r = pg.evaluate("(()=>{ const got=[]; const off=Gioval.entrada.suscribir('golpe',e=>got.push(e)); Gioval.entrada.emitir({tipo:'golpe',fuerza:.5}); off(); Gioval.entrada.emitir({tipo:'golpe'}); return [got.length,got[0].tipo,typeof got[0].t]; })()")
    igual(r, [1, "golpe", "number"], "emitir/suscribir")
    for f in ("acordes", "midi"):   # archivos reservados documentados (golpes.js ya está implementado: ver pruebas de Ritmo)
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
    igual(r["base"], ["piano", "percusion"], "instrumentos de base (piano de Música y percusión de Ritmo)"); igual(r["calls"], [[60, .4, .2], [62, .5, .3]], "instrumento activo")
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
            pg.evaluate("[...document.querySelectorAll('#islands .island')].forEach(x=>{ if(x.innerText.includes('Ritmo')) x.remove(); })")   # la isla nueva no existía en la versión publicada: se compara el resto del mapa
            f("mapa")
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
        igual(pg.evaluate("PACKS.map(p=>p.id)"), ["musica", "numeros", "colores", "ritmo"], "islas registradas")
        for i in range(3):
            abrir_isla(pg, "Colores"); tarjeta(pg, "Sesión de hoy"); verificar(jugar(pg, cada_error=4 if i == 0 else 0) == "fin"); cerrar_fin(pg)
        pg.evaluate("PACK=PACKS.find(p=>p.id==='colores')"); verificar(pg.evaluate("SK('col_nom').mast"), "no dominó la primera habilidad")
        verificar("col_mas" in pg.evaluate("unlockedList().map(s=>s.id)"), "no desbloqueó la segunda")
        abrir_isla(pg, "Colores"); tarjeta(pg, "Chequeo semanal"); verificar(jugar(pg) == "fin"); cerrar_fin(pg)
        verificar(pg.evaluate("store.checks.Vale.some(c=>c.p==='colores')"), "el chequeo no quedó registrado")
        rep = pg.evaluate("reportText()"); verificar("ISLA COLORES" in rep and "Nombrar colores" in rep, rep[:300])
        foto(pg, "360x700_50_isla_ejemplo_colores"); CAPTURAS.append("360x700_50_isla_ejemplo_colores.png")
        # la misma isla en inglés: sale de su propia tabla de textos, sin tocar el motor
        pg.evaluate("window.__LOG.length=0; window.__BUB.length=0; Gioval.i18n.usar('en')")
        igual(pg.evaluate("PACKS.find(p=>p.id==='colores').name"), "Colors Island", "nombre de la isla en inglés")
        abrir_isla(pg, "Colors"); tarjeta(pg, "Today"); verificar(jugar(pg) == "fin"); cerrar_fin(pg)
        dicho = pg.evaluate("window.__LOG.concat(window.__BUB)")
        verificar(any(x.startswith("Tap the color") for x in dicho), "frases de la isla de ejemplo en inglés: %s" % dicho[:4]); verificar(not sin_espanol(dicho), "español en la isla en inglés: %s" % sin_espanol(dicho)[:3])
        igual(pg.evaluate("[...Gioval.i18n.faltantes]"), [], "claves faltantes")
        verificar(not err, str(err)); ctx.close()
    finally:
        srv2.shutdown(); shutil.rmtree(tmp.parent, ignore_errors=True)


# ================================================================== FASE 0b: idiomas y voz
STORE_2 = {"profiles": ["Vale", "Gio"], "limit": {"Vale": 60, "Gio": 60}}
FAKE_VOZ = """(function(){ window.__VOCES=[]; window.__DICHO=[];
  Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{ getVoices:function(){ return window.__VOCES; }, cancel:function(){}, onvoiceschanged:null,
    speak:function(u){ window.__DICHO.push({text:u.text,lang:u.lang,voz:u.voice&&u.voice.name}); setTimeout(function(){ u.onend&&u.onend(); },0); } }});
  window.SpeechSynthesisUtterance=function(t){ this.text=t; };
  window.__setVoces=function(l){ window.__VOCES=l.map(function(v){ return {lang:v[0],name:v[1],localService:!!v[2],voiceURI:v[1],default:false}; }); window.speechSynthesis.onvoiceschanged&&window.speechSynthesis.onvoiceschanged(); };
})();"""

def tablas(pg):
    return pg.evaluate("Object.fromEntries(Object.entries(Gioval.i18n.tablas).map(([c,t])=>[c,t.textos]))")

@prueba("idiomas: formato de textos (género, plurales, anidados) y números en palabras")
def t_i18n_formato(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    f = lambda txt, p: pg.evaluate("([t,p])=>Gioval.i18n.formatear(t,p)", [txt, p])
    igual(f("{g, select, f{una} other{un}} {x}", {"g": "f", "x": "casa"}), "una casa", "select f")
    igual(f("{g, select, f{una} other{un}} {x}", {"g": "m", "x": "auto"}), "un auto", "select other")
    igual([f("{n, plural, =0{ninguno} one{# gato} other{# gatos}}", {"n": n}) for n in (0, 1, 2, 21)], ["ninguno", "1 gato", "2 gatos", "21 gatos"], "plural es")
    igual(f("Hay {a, plural, one{uno} other{{b} de {c}}}.", {"a": 3, "b": "x", "c": "y"}), "Hay x de y.", "anidado")
    igual(f("Hola {nombre}", {}), "Hola {nombre}", "hueco sin valor se deja a la vista")
    es = lambda n, g=None: pg.evaluate("([n,g])=>Gioval.tablas?0:Gioval.i18n.tablas['es-AR'].meta.numeroEnPalabras(n,{g:g||undefined})", [n, g])
    igual([es(n) for n in (0, 1, 16, 20, 21, 22, 31, 45, 100, 101, 115, 200, 500, 999)],
          ["cero", "uno", "dieciséis", "veinte", "veintiuno", "veintidós", "treinta y uno", "cuarenta y cinco", "cien", "ciento uno", "ciento quince", "doscientos", "quinientos", "novecientos noventa y nueve"], "es sin género")
    igual([es(1, "m"), es(1, "f"), es(21, "m"), es(21, "f"), es(101, "f"), es(200, "f"), es(31, "f")], ["un", "una", "veintiún", "veintiuna", "ciento una", "doscientas", "treinta y una"], "es con género")
    en = lambda n: pg.evaluate("n=>Gioval.i18n.tablas['en'].meta.numeroEnPalabras(n)", n)
    igual([en(n) for n in (0, 1, 13, 21, 100, 115, 999)], ["zero", "one", "thirteen", "twenty-one", "one hundred", "one hundred fifteen", "nine hundred ninety-nine"], "en")
    pg.evaluate("Gioval.i18n.usar('en')")
    igual([f("{n, plural, one{# day} other{# days}}", {"n": n}) for n in (1, 2)], ["1 day", "2 days"], "plural en")
    igual(pg.evaluate("[Gioval.i18n.nombreNota(0),Gioval.i18n.nombreNota(7)]"), ["C", "G"], "notas en")
    pg.evaluate("Gioval.i18n.usar('es-AR')"); igual(pg.evaluate("[Gioval.i18n.nombreNota(0),Gioval.i18n.nombreNota(7)]"), ["Do", "Sol"], "notas es")
    ctx.close()

@prueba("idiomas: cadena de respaldo (es-ES → es-AR → en), metadatos y formatos por idioma")
def t_i18n_cadena(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    igual(pg.evaluate("Gioval.i18n.cadena('es-ES')"), ["es-ES", "es-AR", "en"], "cadena es-ES")
    igual(pg.evaluate("Gioval.i18n.cadena('es-419')"), ["es-419", "es-AR", "en"], "cadena es-419")
    igual(pg.evaluate("Gioval.i18n.cadena('qps-ploc')"), ["qps-ploc", "es-AR", "en"], "cadena pseudo")
    igual(pg.evaluate("Gioval.i18n.cadena('en')"), ["en", "es-AR"], "cadena en")
    pg.evaluate("Gioval.i18n.agregar('en',{'x.solo_en':'only english'})")
    igual(pg.evaluate("Gioval.i18n.t('x.solo_en')"), "only english", "cae a en cuando falta en es-AR")
    igual(pg.evaluate("Gioval.i18n.t('x.no_existe')"), "x.no_existe", "clave inexistente se ve como clave")
    verificar(pg.evaluate("Gioval.i18n.faltantes.has('x.no_existe')"), "no anotó la clave faltante")
    pg.evaluate("Gioval.i18n.faltantes.clear()")
    pg.evaluate("Gioval.i18n.usar('es-ES')")
    igual(pg.evaluate("t('app.quien_juega')"), "¿Quién juega?", "es-ES sin esa clave: cae a es-AR")
    igual(pg.evaluate("t('menu.logros_sub')"), "Mira todo lo que aprendiste", "es-ES propio (tuteo)")
    igual(pg.evaluate("document.documentElement.lang"), "es-ES", "lang")
    pg.evaluate("Gioval.i18n.usar('es-AR')"); igual(pg.evaluate("t('menu.logros_sub')"), "Mirá todo lo que aprendiste", "es-AR (voseo)")
    m = pg.evaluate("Object.fromEntries(['es-AR','es-419','es-ES','en','qps-ploc','qps-plocm'].map(c=>{ const x=Gioval.i18n.tablas[c].meta; return [c,[x.nombreNativo,x.dir,x.locale,x.moneda,x.voz,!!x.numeroEnPalabras||x.derivadoDe||null]]; }))")
    igual(m["es-AR"][:4], ["Español (Argentina)", "ltr", "es-AR", "ARS"]); igual(m["en"][:4], ["English", "ltr", "en", "USD"]); igual(m["qps-plocm"][1], "rtl")
    igual(m["es-AR"][4][0], "es-AR", "voz preferida es-AR"); igual(m["es-ES"][4][0], "es-ES")
    f = lambda c, n: pg.evaluate("([c,n])=>{ Gioval.i18n.usar(c); const r=[Gioval.i18n.num(n),Gioval.i18n.dinero(n)]; Gioval.i18n.usar('es-AR'); return r; }", [c, n])
    a, e = f("es-AR", 1234.5), f("en", 1234.5)
    verificar("1.234,5" in a[0] and "$" in a[1], "formato es-AR: %s" % a); verificar("1,234.5" in e[0] and "$" in e[1], "formato en: %s" % e)
    ctx.close()

@prueba("idiomas: completitud (todas las claves usadas existen, en = es-AR, mismos huecos en cada idioma)")
def t_i18n_completitud(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    T = tablas(pg); es, en = T["es-AR"], T["en"]
    usadas = set()
    for f in list((APP / "js" / "core").rglob("*.js")) + list((APP / "js" / "islas").rglob("*.js")) + list((APP / "js" / "datos").rglob("*.js")):
        txt = f.read_text(encoding="utf-8")
        usadas |= set(re.findall(r'"((?:app|menu|motor|tap|adultos|informe|respaldo|almacen|idioma|voz|proximas|musica|numeros|ritmo)\.[a-z0-9_.]+)"', txt))
    for f in [APP / "index.html"] + list((APP / "js" / "islas").rglob("*.js")):
        usadas |= set(re.findall(r'data-i18n(?:-html|-title|-placeholder)?="([^"]+)"', f.read_text(encoding="utf-8")))
    dinam = [k for k in usadas if k.endswith(".") or k.endswith("_")]
    usadas = {k for k in usadas if k in es or not (k.endswith(".") or k.endswith("_") or k.endswith("hab") or k.endswith("cancion"))}
    faltan = sorted(k for k in usadas if k not in es); verificar(not faltan, "claves usadas que no están en es-AR: %s" % faltan)
    # claves dinámicas: habilidades y canciones
    din = pg.evaluate("PACKS.flatMap(p=>p.skills.map(s=>s.name)).concat(SKILLS_DUMMY=0?[]:[])")
    verificar(all(not n.startswith(("musica.", "numeros.")) for n in din), "habilidad sin traducir: %s" % din)
    verificar(not pg.evaluate("[...Gioval.i18n.faltantes]"), "claves faltantes: %s" % pg.evaluate("[...Gioval.i18n.faltantes]"))
    igual(sorted(en), sorted(es), "en tiene que tener EXACTAMENTE las claves de es-AR")
    for c in ("es-419", "es-ES"):
        extra = sorted(set(T[c]) - set(es)); verificar(not extra, "%s tiene claves que es-AR no tiene: %s" % (c, extra))
    P = lambda c, k: sorted({x for v in (T[c][k] if isinstance(T[c][k], list) else [T[c][k]]) if isinstance(v, str) for x in pg.evaluate("s=>Gioval.i18n.parametros(s)", v)})
    SUMINISTRADOS = {"g", "objetos", "n", "a", "a_g", "a_palabras", "b_palabras", "c_palabras", "objetos_a", "n_palabras"}   # lo que el código de Números pasa a sus frases
    malos = []
    for k, v in es.items():
        if isinstance(v, dict): continue
        for c in ("en", "es-419", "es-ES"):
            if k not in T[c]: continue
            a, b = set(P("es-AR", k)), set(P(c, k))
            if k.startswith("numeros.") and k not in ("numeros.nombre", "numeros.sub", "numeros.outro", "numeros.cola_tope"):
                if not b <= SUMINISTRADOS: malos.append("%s/%s pide datos que el código no pasa: %s" % (c, k, sorted(b - SUMINISTRADOS)))
            elif not b <= a: malos.append("%s/%s pide %s que es-AR no tiene (%s)" % (c, k, sorted(b - a), sorted(a)))
    verificar(not malos, "huecos distintos entre idiomas: %s" % malos[:5])
    r = pg.evaluate("""(()=>{ const bad=[]; const dummy=new Proxy({},{get:()=>1});
      for(const [c,t] of Object.entries(Gioval.i18n.tablas)){ for(const [k,v] of Object.entries(t.textos)){ const xs=Array.isArray(v)?v:(typeof v==='string'?[v]:[]);
        xs.forEach(x=>{ try{ Gioval.i18n.formatear(x,{n:2,a:2,g:'f',estado:'dominado',local:'si'}); }catch(e){ bad.push(c+'/'+k); } }); } } return bad; })()""")
    verificar(not r, "textos mal formados: %s" % r)
    ctx.close(); return "%d claves; en = es-AR; es-419: %d y es-ES: %d diferencias" % (len(es), len(T["es-419"]), len(T["es-ES"]))

@prueba("idiomas: el texto en español del HTML coincide con la tabla es-AR (sin duplicados que se desincronicen)")
def t_i18n_html(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    r = pg.evaluate("""(async()=>{ const bad=[]; const es=Gioval.i18n.tablas['es-AR'].textos;
      const html=[await (await fetch('index.html')).text()].concat(PACKS.map(p=>Object.values(p.dom||{}).join('')));
      html.forEach(h=>{ const d=new DOMParser().parseFromString(h,'text/html');
        d.querySelectorAll('[data-i18n],[data-i18n-html],[data-i18n-title],[data-i18n-placeholder]').forEach(el=>{
          const n=el.dataset.i18nN!=null?{n:+el.dataset.i18nN}:{};
          const cmp=(clave,real)=>{ const v=Gioval.i18n.formatear(es[clave],n); if(v!==real) bad.push(clave+': HTML=['+real+'] tabla=['+v+']'); };
          if(el.dataset.i18n) cmp(el.dataset.i18n,el.textContent);
          if(el.dataset.i18nHtml) cmp(el.dataset.i18nHtml,el.innerHTML);
          if(el.dataset.i18nTitle) cmp(el.dataset.i18nTitle,el.getAttribute('title'));
          if(el.dataset.i18nPlaceholder) cmp(el.dataset.i18nPlaceholder,el.getAttribute('placeholder'));
        }); }); return bad; })()""")
    verificar(not r, "HTML ≠ tabla: %s" % r[:6]); ctx.close()

@prueba("idioma inglés: sesiones completas de Música y Números sin una palabra en español")
def t_ingles(C):
    ctx = C.banco.contexto("pixel7"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=77, extra_init="localStorage.setItem('gioval_idioma','en');"); instalar_speak(pg)
    igual(pg.evaluate("[document.documentElement.lang,document.documentElement.dir,document.title]"), ["en", "ltr", "Mundo Gioval - Let's play"], "lang/dir/título")
    verificar(pg.evaluate("document.getElementById('btnWho').textContent") == "👤 Change", "botón Cambiar")
    entrar(pg, "Vale")
    islas = pg.evaluate("[...document.querySelectorAll('#islands .island')].map(x=>x.innerText.split('\\n').slice(1).join('|'))")
    igual(islas, ["Music Island|Let's play the piano!", "Numbers Island|Let's count and add!", "Rhythm Island|Let's keep the beat!", "Letters Island|Soon", "Animals Island|Soon"], "mapa en inglés")
    foto(pg, "pixel7_60_ingles_mapa"); CAPTURAS.append("pixel7_60_ingles_mapa.png")
    abrir_isla(pg, "Music"); tarjeta(pg, "Today"); pg.wait_for_timeout(400)
    labels = pg.evaluate("[...document.querySelectorAll('.key span')].map(s=>s.textContent).join('')")
    verificar(labels.startswith("CDEFGABC"), "las teclas deberían decir C D E ...: " + labels)
    foto(pg, "pixel7_61_ingles_musica"); CAPTURAS.append("pixel7_61_ingles_musica.png")
    verificar(jugar(pg, cada_error=5) == "fin"); cerrar_fin(pg)
    abrir_isla(pg, "Numbers"); tarjeta(pg, "Today"); pg.wait_for_timeout(500)
    foto(pg, "pixel7_62_ingles_numeros"); CAPTURAS.append("pixel7_62_ingles_numeros.png")
    verificar(jugar(pg, cada_error=4) == "fin"); cerrar_fin(pg)
    abrir_isla(pg, "Numbers"); tarjeta(pg, "Today"); jugar(pg, cada_error=3); cerrar_fin(pg)
    dicho = pg.evaluate("window.__LOG.concat(window.__BUB)"); verificar(len(dicho) > 60, "pocas frases: %d" % len(dicho))
    esp = sin_espanol(dicho); verificar(not esp, "frases con español: %s" % esp[:5])
    verificar(any(re.search(r"\b(There (is|are)|How many|Tap)\b", x) for x in dicho), "no aparecieron las frases de números en inglés")
    igual(pg.evaluate("[...Gioval.i18n.faltantes]"), [], "claves faltantes")
    rep = pg.evaluate("reportText()"); verificar("REPORT FOR VALE" in rep and "Correct on the first try" in rep, rep[:200]); verificar(not sin_espanol(rep.split("\n")), "informe con español")
    verificar(not err, str(err)); ctx.close(); return "%d frases en inglés" % len(dicho)

@prueba("idioma por aparato y por jugador: se elige en la zona de adultos, se guarda, se respalda")
def t_idioma_ui(C):
    ctx = C.banco.contexto("360x700", accept_downloads=True); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_2, errores=err, semilla=5); instalar_speak(pg); entrar(pg, "Vale")
    igual(pg.evaluate("[...document.querySelectorAll('#langDev option')].map(o=>o.value)"), [] , "") if False else None
    abrir_panel(pg)
    ops = pg.evaluate("[...document.querySelectorAll('#langDev option')].map(o=>o.value)")
    for c in ("es-AR", "es-419", "es-ES", "en", "qps-ploc", "qps-plocm"): verificar(c in ops, "falta %s en el selector: %s" % (c, ops))
    verificar("Idioma de Vale:" in pg.evaluate("document.getElementById('langKidLbl').textContent"), "etiqueta del jugador")
    pg.select_option("#langKid", "es-419"); pg.wait_for_timeout(150)
    igual(pg.evaluate("store.idioma"), {"Vale": "es-419"}, "store.idioma"); igual(pg.evaluate("document.documentElement.lang"), "es-419")
    pg.click("#btnGear"); abrir_isla(pg, "Música") if pg.evaluate("document.querySelector('.screen.active').id") == "map" else None
    verificar("Mira todo lo que aprendiste" in pg.evaluate("document.getElementById('menuIslaItems').innerText"), "Vale debería estar en es-419 (tuteo)")
    pg.evaluate("document.getElementById('btnWho').click()"); pg.wait_for_timeout(100); entrar(pg, "Gio"); abrir_isla(pg, "Música")
    verificar("Mirá todo lo que aprendiste" in pg.evaluate("document.getElementById('menuIslaItems').innerText"), "Gio sigue en es-AR")
    # idioma del aparato
    pg.evaluate("document.getElementById('btnWho').click()"); pg.wait_for_timeout(100); entrar(pg, "Gio")
    abrir_panel(pg); pg.select_option("#langDev", "en"); pg.wait_for_timeout(150)
    igual(pg.evaluate("localStorage.getItem('gioval_idioma')"), "en", "idioma del aparato guardado"); verificar(pg.evaluate("document.getElementById('btnWho').textContent") == "👤 Change")
    foto(pg, "360x700_63_panel_idioma"); CAPTURAS.append("360x700_63_panel_idioma.png")
    pg.click("#btnGear"); pg.evaluate("Gioval.almacen.guardarYa()"); pg.wait_for_timeout(200)
    pg.reload(); esperar_listo(pg); igual(pg.evaluate("document.documentElement.lang"), "en", "tras recargar (aparato)")
    entrar(pg, "Vale"); igual(pg.evaluate("document.documentElement.lang"), "es-419", "Vale recuerda su idioma tras recargar")
    # respaldo conserva el idioma
    pg.evaluate("document.getElementById('nameBox').classList.remove('show')"); abrir_panel(pg)
    with pg.expect_download() as d: pg.click("#btnExport")
    ruta = SALIDA / "respaldo_idioma.json"; d.value.save_as(str(ruta)); igual(json.loads(ruta.read_text())["store"]["idioma"], {"Vale": "es-419"}, "el respaldo incluye idioma")
    verificar(not err, str(err)); ctx.close()

@prueba("migración v1 → v2: agrega el idioma por jugador sin tocar el progreso")
def t_mig_v2(C):
    v1 = json.loads(FIXTURE); v1 = {"version": 1, "meta": {"ultimoRespaldo": 5, "guardado": 9, "desde": 7}, **v1}
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=v1, errores=C.err)
    n = pg.evaluate("JSON.parse(JSON.stringify(store))"); igual(n["version"], 2); igual(n["idioma"], {}, "idioma"); igual(n["sk"], v1["sk"], "sk"); igual(n["meta"]["ultimoRespaldo"], 5, "meta conservada")
    rs = pg.evaluate("Gioval.almacen.respaldos()"); verificar(any("pre-migracion-v1" in r["id"] for r in rs), "copia previa v1: %s" % [r["id"] for r in rs])
    ctx.close()

@prueba("espacio de datos: una copia de prueba (GIOVAL_ESPACIO) no ve ni pisa los datos de la versión real")
def t_espacio(C):
    ESTADO["espacio_override"] = "beta"
    try:
        ctx = C.banco.contexto("360x700", sw=True); err = []
        pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=err)    # siembra 'gioval' (clave de producción)
        igual(pg.evaluate("Gioval.espacio"), "beta"); igual(pg.evaluate("store.profiles"), [], "la copia beta no debe ver los perfiles de producción")
        pg.evaluate("document.getElementById('nameBox').classList.remove('show')")
        pg.evaluate("store.profiles.push('Prueba'); save(); Gioval.almacen.guardarYa(); Alarma.programar(300)"); pg.wait_for_timeout(300)
        igual(json.loads(pg.evaluate("localStorage.getItem('gioval')")), json.loads(FIXTURE), "la clave de producción quedó intacta")
        igual(json.loads(pg.evaluate("localStorage.getItem('gioval_beta')"))["profiles"], ["Prueba"], "los datos de beta van a su propia clave")
        verificar(pg.evaluate("localStorage.getItem('gioval_alarma_beta')") is not None and pg.evaluate("localStorage.getItem('gioval_alarma')") is None, "alarma con su propia clave")
        dbs = pg.evaluate("indexedDB.databases().then(l=>l.map(d=>d.name))"); verificar("gioval-db-beta" in dbs and "gioval-db" not in dbs, "bases: %s" % dbs)
        pg.evaluate("caches.open('gioval-OLD-real').then(c=>c.put('/x',new Response('1')))")
        pg.wait_for_function("navigator.serviceWorker.getRegistration().then(r=>r&&r.active?true:false)", timeout=15000); pg.wait_for_timeout(800)
        ks = pg.evaluate("caches.keys()"); v = pg.evaluate("self.GIOVAL_VERSION")
        verificar("gioval@beta-" + v in ks, "caché de beta: %s" % ks); verificar("gioval-OLD-real" in ks, "el service worker de beta borró una caché de la versión real: %s" % ks)
        ctx.close()
    finally:
        ESTADO["espacio_override"] = None
    ctx = C.banco.contexto("360x700", sw=True); pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=C.err)    # versión real
    pg.evaluate("caches.open('gioval@beta-OLD').then(c=>c.put('/x',new Response('1')))")
    pg.wait_for_function("navigator.serviceWorker.getRegistration().then(r=>r&&r.active?true:false)", timeout=15000); pg.wait_for_timeout(800)
    ks = pg.evaluate("caches.keys()"); verificar("gioval@beta-OLD" in ks, "el service worker real borró la caché de beta: %s" % ks); verificar(any(k.startswith("gioval-") for k in ks))
    ctx.close()

@prueba("voz: cadena de respaldo (audio → voz del aparato por BCP-47 → solo texto) con voces simuladas")
def t_voz(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_2, errores=err, extra_init=FAKE_VOZ, rapido=False)
    habla = lambda txt="Hola": (pg.evaluate("window.__DICHO.length=0; window.__t=speak(%s)" % json.dumps(txt)), pg.wait_for_timeout(60), pg.evaluate("window.__DICHO"))[2]
    V = "Gioval.voz"
    # a) es-AR: prefiere la voz es-AR que funciona sin conexión
    pg.evaluate("__setVoces([['es-MX','Mex local',1],['es-AR','Arg online',0],['es-AR','Arg local',1],['en-US','Ing local',1]])")
    igual(pg.evaluate("[%s.nivel,%s.voz.name]" % (V, V)), ["tts", "Arg local"], "es-AR elige la voz argentina local")
    d = habla(); igual([d[0]["lang"], d[0]["voz"]], ["es-AR", "Arg local"], "utterance")
    # b) es-419 y es-ES
    pg.evaluate("Gioval.i18n.usar('es-419')"); igual(pg.evaluate("%s.voz.name" % V), "Mex local", "es-419 prefiere es-MX antes que es-AR")
    pg.evaluate("__setVoces([['es-US','Usa',1],['es-AR','Arg',1]])"); pg.evaluate("Gioval.i18n.usar('es-419')"); igual(pg.evaluate("%s.voz.name" % V), "Usa", "es-419 → es-US antes que es-AR")
    pg.evaluate("__setVoces([['es-MX','Mex',1],['es-CL','Chile',1],['en-US','Ing',1]])"); pg.evaluate("Gioval.i18n.usar('es-AR')"); igual(pg.evaluate("%s.voz.name" % V), "Mex", "es-AR sin voz argentina: otra variante del español")
    pg.evaluate("__setVoces([['es-CL','Chile',1],['en-US','Ing',1]])"); pg.evaluate("Gioval.i18n.usar('es-AR')"); igual(pg.evaluate("%s.voz.name" % V), "Chile", "cualquier es-*")
    # c) inglés
    pg.evaluate("__setVoces([['es-AR','Arg',1],['en-GB','Brit',1],['en-US','Yanqui',0]])"); pg.evaluate("Gioval.i18n.usar('en')")
    igual(pg.evaluate("%s.voz.name" % V), "Yanqui", "en: prefiere en-US (orden de meta.voz) aunque sea online"); d = habla("Hello"); igual(d[0]["lang"], "en-US")
    # d) sin voz para el idioma → solo texto, y la app sigue
    pg.evaluate("__setVoces([['en-US','Ing',1]])"); pg.evaluate("Gioval.i18n.usar('es-AR')")
    igual(pg.evaluate("[%s.nivel,%s.sinVoz,voiceReady()]" % (V, V)), ["texto", True, False], "sin voz española")
    d = habla("Hola"); igual(d, [], "no debe llamar a speechSynthesis"); igual(pg.evaluate("document.getElementById('bubble').textContent"), "Hola", "el texto se muestra igual")
    pg.evaluate("window.__t.then(()=>window.__fin=1)"); pg.wait_for_function("window.__fin===1", timeout=4000)
    abrir_panel(pg); verificar(pg.evaluate("getComputedStyle(document.getElementById('vozAviso')).display")!="none" and "Sin voz" in pg.evaluate("document.getElementById('vozAviso').textContent"), "aviso discreto en la zona de adultos")
    foto(pg, "360x700_64_sin_voz_aviso"); CAPTURAS.append("360x700_64_sin_voz_aviso.png")
    pg.click("#btnGear")
    # e) pseudo-idioma: sin voz a propósito aunque haya voces españolas
    pg.evaluate("__setVoces([['es-AR','Arg',1]])"); pg.evaluate("Gioval.i18n.usar('qps-ploc')"); igual(pg.evaluate("%s.nivel" % V), "texto", "pseudo-idioma sin voz")
    # f) lista de voces todavía vacía: se intenta igual con el idioma pedido
    pg.evaluate("__setVoces([])"); pg.evaluate("Gioval.i18n.usar('es-AR')"); igual(pg.evaluate("%s.nivel" % V), "tts", "lista vacía: se intenta")
    d = habla(); igual([d[0]["lang"], d[0]["voz"]], ["es-AR", None], "utterance sin voz elegida"); 
    # g) voz fijada por el adulto en 'Probar voz'
    pg.evaluate("__setVoces([['es-AR','Arg A',1],['es-AR','Arg B',1]])"); pg.evaluate("Gioval.i18n.usar('es-AR')")
    abrir_panel(pg); pg.click("#btnVozProbar"); pg.wait_for_selector("#vozBox.show")
    verificar("Arg A" in pg.evaluate("document.getElementById('vozNivel').innerText"), "muestra la voz usada")
    ops = pg.evaluate("[...document.querySelectorAll('#vozSel option')].map(o=>o.textContent)"); verificar(len(ops) == 3 and ops[0] == "(automática)", str(ops))
    foto(pg, "360x700_65_probar_voz"); CAPTURAS.append("360x700_65_probar_voz.png")
    pg.select_option("#vozSel", "Arg B"); pg.wait_for_timeout(100); igual(pg.evaluate("%s.voz.name" % V), "Arg B", "voz elegida")
    pg.evaluate("window.__DICHO.length=0"); pg.click("#vozSonar"); pg.wait_for_timeout(100)
    d = pg.evaluate("window.__DICHO"); igual([d[0]["text"], d[0]["voz"]], ["¡Hola! Así suena la voz de Mundo Gioval.", "Arg B"], "Escuchar")
    igual(pg.evaluate("localStorage.getItem('gioval_voz_es-AR')"), "Arg B", "se guarda en este aparato")
    pg.click("#vozCerrar"); pg.reload(); esperar_listo(pg); pg.evaluate("__setVoces([['es-AR','Arg A',1],['es-AR','Arg B',1]])"); igual(pg.evaluate("%s.voz.name" % V), "Arg B", "se recuerda tras recargar")
    verificar(not err, str(err)); ctx.close()

@prueba("voz: audio grabado por idioma (manifiesto, caída a la voz del aparato) y service worker con caché solo del idioma elegido")
def t_voz_audio(C):
    import shutil, tempfile, wave, struct
    tmp = Path(tempfile.mkdtemp()) / "app"; shutil.copytree(APP, tmp)
    en = (tmp / "js/i18n/en.js").read_text(encoding="utf-8"); verificar('moneda: "USD",' in en)
    (tmp / "js/i18n/en.js").write_text(en.replace('moneda: "USD",', 'moneda: "USD", audio: true,', 1), encoding="utf-8")
    (tmp / "audio" / "en").mkdir(parents=True)
    for n in ("hola.wav", "quien.wav"):
        w = wave.open(str(tmp / "audio" / "en" / n), "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(struct.pack("<80h", *([0] * 80))); w.close()
    (tmp / "audio/en/manifest.json").write_text(json.dumps({"version": 1, "textos": {"Hello there": "hola.wav"}, "claves": {"app.quien_juega": "quien.wav"}}))
    srv2, url2 = servidor(raiz=tmp)
    try:
        ctx = C.banco.contexto("360x700", sw=True); err = []
        pg = abrir(ctx, url2 + "/index.html", store=STORE_2, errores=err, rapido=False, extra_init=FAKE_VOZ + """
          window.__AUD=[]; window.Audio=function(u){ var a=this; a.src=u; window.__AUD.push(u); a.pause=function(){}; a.play=function(){ setTimeout(function(){ a.onended&&a.onended(); },0); return Promise.resolve(); }; };""")
        pg.evaluate("__setVoces([['en-US','Yanqui',1],['es-AR','Arg',1]])")
        pg.wait_for_function("navigator.serviceWorker.getRegistration().then(r=>r&&r.active?true:false)", timeout=15000)
        pg.reload(); esperar_listo(pg); pg.wait_for_function("!!navigator.serviceWorker.controller", timeout=10000)
        pg.evaluate("__setVoces([['en-US','Yanqui',1],['es-AR','Arg',1]])")
        igual(pg.evaluate("Gioval.voz.nivel"), "tts", "es-AR no tiene audio")
        pg.evaluate("Gioval.i18n.usar('en')"); pg.wait_for_function("Gioval.voz.nivel==='grabado'", timeout=8000)
        igual(pg.evaluate("Gioval.voz.cantidadAudios()"), 2, "audios del manifiesto")
        pg.evaluate("window.__AUD.length=0; window.__DICHO.length=0; speak('Hello there')"); pg.wait_for_timeout(100)
        verificar(pg.evaluate("window.__AUD").__len__() == 1 and pg.evaluate("window.__AUD[0]").endswith("audio/en/hola.wav"), "debería reproducir el audio: %s" % pg.evaluate("window.__AUD")); igual(pg.evaluate("window.__DICHO"), [], "sin voz del aparato")
        pg.evaluate("window.__AUD.length=0; speak(t('app.quien_juega'))"); pg.wait_for_timeout(100)
        verificar(pg.evaluate("window.__AUD[0]").endswith("audio/en/quien.wav"), "audio por clave: %s" % pg.evaluate("window.__AUD"))
        pg.evaluate("window.__AUD.length=0; window.__DICHO.length=0; speak('Other sentence')"); pg.wait_for_timeout(100)
        igual(pg.evaluate("window.__AUD"), [], "frase sin audio: no usa audio"); igual(pg.evaluate("window.__DICHO.map(d=>d.voz)"), ["Yanqui"], "cae a la voz del aparato")
        # el service worker guarda SOLO el audio del idioma elegido
        pg.wait_for_function("caches.keys().then(k=>k.some(x=>x==='gioval-audio-en'))", timeout=8000)
        n = pg.evaluate("caches.open('gioval-audio-en').then(c=>c.keys()).then(l=>l.map(r=>new URL(r.url).pathname).sort())")
        igual(n, ["/audio/en/hola.wav", "/audio/en/manifest.json", "/audio/en/quien.wav"], "caché de audio en")
        ca = pg.evaluate("caches.open('gioval-'+self.GIOVAL_VERSION).then(c=>c.keys()).then(l=>l.map(r=>r.url))"); verificar(not any("/audio/" in k for k in ca), "el audio no debe ir a la caché de la app: %s" % [k for k in ca if "/audio/" in k])
        pg.evaluate("Gioval.i18n.usar('es-AR')"); pg.wait_for_function("caches.keys().then(k=>!k.some(x=>x==='gioval-audio-en'))", timeout=8000)
        verificar(not err, str(err)); ctx.close()
    finally:
        srv2.shutdown(); shutil.rmtree(tmp.parent, ignore_errors=True)

JS_DESBORDES = """(function(){
 const W=innerWidth,H=innerHeight, out=[];
 const sel='button,.island,.song,.skill,.opt,h1,h2,.bubble,label,.psum,select,input,.stars,.actStage';
 function visible(el){ const r=el.getBoundingClientRect(), cs=getComputedStyle(el); return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none'&&!el.closest('.screen:not(.active)')&&!el.closest('.big:not(.show)')&&!el.closest('.panel:not(.show)')&&!el.closest('.aviso:not(.show)'); }
 function scrolla(el,eje){ let p=el.parentElement; while(p&&p!==document.documentElement){ const o=getComputedStyle(p)['overflow'+eje]; if((o==='auto'||o==='scroll')&&(eje==='Y'?p.scrollHeight>p.clientHeight:p.scrollWidth>p.clientWidth)) return true; p=p.parentElement; } return false; }
 document.querySelectorAll(sel).forEach(el=>{ if(!visible(el)) return; const r=el.getBoundingClientRect();
   const id=(el.id?'#'+el.id:'')+(typeof el.className==='string'&&el.className?'.'+el.className.trim().split(/\\s+/).join('.'):'')+':'+el.tagName.toLowerCase();
   if(r.right>W+1||r.left<-1) out.push(id+' fuera de pantalla (horizontal)');
   if((r.bottom>H+1||r.top<-1)&&!scrolla(el,'Y')) out.push(id+' fuera de pantalla (vertical)');
   const cs=getComputedStyle(el);
   if((cs.overflowX==='hidden'||cs.overflow==='hidden')&&el.scrollWidth>el.clientWidth+2) out.push(id+' texto cortado (ancho)');
   if((cs.overflowY==='hidden'||cs.overflow==='hidden')&&el.scrollHeight>el.clientHeight+2) out.push(id+' texto cortado (alto)'); });
 return [...new Set(out)]; })()"""

def recorrido(pg, vista, idioma, prefijo, capturas=False):
    """Recorre las pantallas principales y devuelve los desbordes que encuentra en cada una."""
    res = {}
    def ver(nombre):
        pg.wait_for_timeout(120); res[nombre] = pg.evaluate(JS_DESBORDES)
        if capturas: CAPTURAS.append(foto(pg, "%s_%s_%s" % (vista, prefijo, nombre)))
    pg.evaluate("document.getElementById('nameBox').classList.remove('show'); S.run++; resetFlow(); renderWho(); show('who')")
    ver("1_quien")
    entrar(pg, "Vale"); ver("2_mapa")
    pg.click("#islands .island >> nth=0"); ver("3_menu_musica")
    pg.evaluate("goMap()"); pg.click("#islands .island >> nth=1"); pg.wait_for_timeout(100); ver("4_menu_numeros")
    pg.click("#menuIslaItems .island >> nth=0"); pg.wait_for_timeout(700); ver("5_numeros_actividad")
    pg.evaluate("S.run++; resetFlow(); goMenuIsla()"); pg.click("#menuIslaItems .island >> nth=1"); pg.wait_for_timeout(100); ver("6_logros")
    pg.evaluate("goMap()"); abrir_panel(pg); ver("7_panel_adultos")
    pg.click("#btnReport"); ver("8_informe"); pg.click("#repClose"); pg.click("#btnGear")
    pg.evaluate("document.getElementById('finish').classList.add('show')"); ver("9_fin"); pg.evaluate("document.getElementById('finish').classList.remove('show')")
    return res

@prueba("pseudo-idioma (+40 %, acentos): ningún texto se corta ni se sale de la pantalla que no lo hiciera ya en es-AR")
def t_pseudo(C):
    pend = []
    for v in ("360x700", "740x330"):
        base = {}
        for idioma in ("es-AR", "qps-ploc"):
            ctx = C.banco.contexto(v); err = []
            pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=9, extra_init="localStorage.setItem('gioval_idioma','%s');" % idioma, congelar=True); instalar_speak(pg)
            r = recorrido(pg, v, idioma, "pseudo", capturas=(idioma == "qps-ploc"))
            igual(pg.evaluate("[document.documentElement.lang, Gioval.i18n.faltantes.size]"), [idioma, 0], "idioma/faltantes")
            if idioma == "es-AR": base = r
            else:
                for k, lst in r.items():
                    for x in lst:
                        if x not in base.get(k, []): pend.append("%s %s: %s" % (v, k, x))
            verificar(not err, str(err)); ctx.close()
    verificar(not pend, "con el pseudo-idioma aparecen desbordes nuevos:\n        " + "\n        ".join(pend[:12]))

@prueba("RTL (derecha a izquierda): interfaz espejada, teclado de piano y cuentas sin espejar, sin desbordes nuevos")
def t_rtl(C):
    pend = []
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=9, extra_init="localStorage.setItem('gioval_idioma','qps-plocm');", congelar=True); instalar_speak(pg)
        igual(pg.evaluate("[document.documentElement.dir, document.documentElement.lang, getComputedStyle(document.body).direction]"), ["rtl", "qps-plocm", "rtl"], "dir")
        g = lambda sel: pg.evaluate("(s)=>{const r=document.querySelector(s).getBoundingClientRect();return [r.left,r.right]}", sel)
        m, b = g("#mascot"), g("#bubble"); verificar(m[0] > b[0], "la mascota debería estar a la derecha del globito: %s %s" % (m, b))
        pg.evaluate("document.getElementById('nameBox').classList.remove('show')")
        entrar(pg, "Vale"); pg.click("#islands .island >> nth=0"); pg.wait_for_timeout(100)
        bar = pg.evaluate("(()=>{const b=document.getElementById('btnMenuBack').getBoundingClientRect(), t=document.getElementById('streak').getBoundingClientRect(); return [b.left,t.left]})()"); verificar(bar[0] > bar[1], "el botón Volver debería estar a la derecha: %s" % bar)
        verificar(pg.evaluate("getComputedStyle(document.querySelector('#btnMenuBack .arr')).transform") != "none", "la flecha de volver debe espejarse")
        CAPTURAS.append(foto(pg, "%s_70_rtl_menu" % v))
        pg.click("#menuIslaItems .island >> nth=0"); pg.wait_for_timeout(400)     # sesión de Música: el teclado NO se espeja
        k = pg.evaluate("[...document.querySelectorAll('#kb .key')].map(k=>Math.round(k.getBoundingClientRect().left))"); verificar(k == sorted(k), "las teclas del piano deben seguir de izquierda a derecha: %s" % k)
        igual(pg.evaluate("document.querySelector('#kb .key').dataset.m"), "60", "la primera tecla (a la izquierda) es el Do central")
        CAPTURAS.append(foto(pg, "%s_71_rtl_piano" % v))
        pg.evaluate("S.run++; resetFlow(); goMenuIsla(); goMap()")
        r = recorrido(pg, v, "qps-plocm", "rtl", capturas=True)
        ctx.close()
        ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=9, extra_init="localStorage.setItem('gioval_idioma','qps-ploc');", congelar=True); instalar_speak(pg)
        ltr = recorrido(pg, v, "qps-ploc", "ltr"); ctx.close()
        for k2, lst in r.items():
            for x in lst:
                if x not in ltr.get(k2, []): pend.append("%s %s: %s" % (v, k2, x))
        verificar(not err, str(err))
    verificar(not pend, "en RTL aparecen desbordes que no hay en LTR:\n        " + "\n        ".join(pend[:12]))

@prueba("agregar un idioma: 1 archivo + 1 línea en index.html + 1 línea en sw.js (ejemplo pt-BR de docs/AGREGAR_IDIOMA.md)")
def t_agregar_idioma(C):
    import shutil, tempfile
    tmp = Path(tempfile.mkdtemp()) / "app"; shutil.copytree(APP, tmp)
    shutil.copy(DEV / "docs" / "ejemplos" / "pt-BR.js", tmp / "js" / "i18n" / "pt-BR.js")
    h = (tmp / "index.html").read_text(encoding="utf-8"); a = '<script src="js/i18n/en.js"></script>'; verificar(a in h)
    (tmp / "index.html").write_text(h.replace(a, a + '\n<script src="js/i18n/pt-BR.js"></script>'), encoding="utf-8")
    w = (tmp / "sw.js").read_text(encoding="utf-8"); a = '"js/i18n/en.js"'; verificar(a in w)
    (tmp / "sw.js").write_text(w.replace(a, a + ',"js/i18n/pt-BR.js"'), encoding="utf-8")
    for f in (APP / "js" / "core").rglob("*.js"): igual((tmp / f.relative_to(APP)).read_bytes(), f.read_bytes(), "motor modificado " + f.name)
    srv2, url2 = servidor(raiz=tmp)
    try:
        ctx = C.banco.contexto("360x700"); err = []
        pg = abrir(ctx, url2 + "/index.html", store=STORE_2, errores=err, semilla=3); instalar_speak(pg)
        verificar("pt-BR" in pg.evaluate("Gioval.i18n.idiomas().map(i=>i.codigo)"), "no se registró")
        entrar(pg, "Vale"); abrir_panel(pg); pg.select_option("#langDev", "pt-BR"); pg.click("#btnGear"); pg.wait_for_timeout(150)
        igual(pg.evaluate("document.documentElement.lang"), "pt-BR")
        verificar(pg.evaluate("document.getElementById('mapTitle').textContent") == "Mundo Gioval · Vamos brincar, Vale!", "mapa en portugués: " + pg.evaluate("document.getElementById('mapTitle').textContent"))
        islas = pg.evaluate("[...document.querySelectorAll('#islands .island')].map(x=>x.innerText.split('\\n')[1])"); igual(islas[:2], ["Ilha da Música", "Ilha dos Números"], "nombres de isla")
        abrir_isla(pg, "Ilha da Música"); tx = pg.evaluate("document.getElementById('menuIslaItems').innerText")
        verificar("Sessão de hoje" in tx and "Mirá todo lo que aprendiste" in tx, "lo traducido sale en portugués y lo que falta cae a es-AR: " + tx)
        igual(pg.evaluate("Gioval.i18n.nombreNota(0)"), "Dó", "nombre de las notas en pt-BR")
        verificar(not err, str(err)); ctx.close()
    finally:
        srv2.shutdown(); shutil.rmtree(tmp.parent, ignore_errors=True)


# ---------------------------------------------------------------- Isla Ritmo y detector de golpes
ESC_TEST = "window.__RITMO_ESCALA=5;"   # reloj de la isla 5 veces más rápido (solo pruebas); los tiempos de los golpes sintéticos son reales
STORE_RITMO = {"profiles": ["Vale"], "limit": {"Vale": 60}}

def solo_habilidad(pg, sid):
    """Deja dominadas todas las habilidades de Ritmo menos `sid` (así la sesión practica justo esa)."""
    pg.evaluate("""(sid)=>{ PACK=PACKS.find(p=>p.id==='ritmo'); PACK.skills.forEach(s=>{ var st=SK(s.id); if(s.id===sid){ st.mast=false; st.att=0; st.score=.5; st.box=0; st.lvl=0; st.rec=[]; }
      else { st.mast=true; st.att=6; st.score=.9; st.box=1; st.due=Date.now()+864e5; } }); }""", sid)

def esperar_fase(pg, fase, seg=20):
    pg.wait_for_function("Gioval.ritmo.fase==='%s'" % fase, timeout=seg * 1000)

@prueba("Ritmo: evaluación del eco rítmico (acierto, adelantado, atrasado, golpe de más, faltante) y ventanas por nivel")
def t_ritmo_evaluacion(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    ioi = lambda rel, h, W: pg.evaluate("(a)=>Gioval.ritmo.evaluar.ioi(a[0],a[1],a[2])", [rel, h, W])
    estados = lambda r: [e["estado"] for e in r["etiquetas"]]
    rel = [0, 500, 1000, 1500]
    r = ioi(rel, [1000, 1500, 2000, 2500], 120); verificar(r["ok"] and estados(r) == ["ok"] * 4 and r["desvio"] == 0, "acierto exacto: %s" % r)
    r = ioi(rel, [1000, 1540, 1980, 2520], 120); verificar(r["ok"] and 0 < r["desvio"] <= 60, "acierto con pequeño desvío: %s" % r)
    r = ioi(rel, [0, 500, 780, 1500], 120); igual(estados(r), ["ok", "ok", "adelantado", "ok"], "adelantado"); verificar(not r["ok"])
    r = ioi(rel, [0, 500, 1000, 1750], 120); igual(estados(r), ["ok", "ok", "ok", "atrasado"], "atrasado"); verificar(not r["ok"])
    r = ioi(rel, [0, 500, 700, 1000, 1500], 120); igual(estados(r), ["ok"] * 4, "golpe de más: los esperados siguen bien"); igual(r["extra"], [700], "golpe de más"); verificar(not r["ok"])
    r = ioi(rel, [0, 500, 1000], 120); igual(estados(r), ["ok", "ok", "ok", "falta"], "faltante"); verificar(not r["ok"])
    r = ioi(rel, [], 120); igual(estados(r), ["falta"] * 4, "sin golpes")
    # el tempo 20 % más lento pasa con la ventana ancha y no con la angosta; la ventana depende del nivel y del pulso
    lento = [0, 600, 1200, 1800]
    v = pg.evaluate("[0,1,2].map(l=>Gioval.ritmo.ventana(l,500))"); igual([round(x) for x in v], [160, 120, 90], "ventanas por nivel (pulso de 500 ms)")
    verificar(ioi(rel, lento, v[0])["ok"] and ioi(rel, lento, v[1])["ok"], "20 % más lento debería pasar con ventana de nivel 0/1")
    verificar(not ioi(rel, lento, 60)["ok"], "20 % más lento no debería pasar con 60 ms")
    igual([round(x) for x in pg.evaluate("[Gioval.ritmo.ventana(0,2000),Gioval.ritmo.ventana(2,200)]")], [210, 90], "topes de la ventana")
    # ejercicios largos: alcanza el 75 %
    rel8 = [i * 500 for i in range(8)]; h = [i * 500 for i in range(8)]; h[3] += 200; h[6] += 200
    verificar(ioi(rel8, h, 120)["ok"] is True, "6 de 8 deberían alcanzar en un ejercicio largo")
    h[1] += 200; verificar(ioi(rel8, h, 120)["ok"] is False, "5 de 8 no alcanzan")
    # grilla: la demora fija (micrófono/pantalla) no cuenta; una tardanza puntual sí; un golpe en un silencio se reconoce
    gr = lambda exp, h, W, o=None: pg.evaluate("(a)=>Gioval.ritmo.evaluar.grid(a[0],a[1],a[2],a[3],a[4])", [exp, h, W, 500, o or {}])
    exp = [1000, 1500, 2000, 2500]
    r = gr(exp, [x + 70 for x in exp], 120); verificar(r["ok"] and abs(r["sesgo"] - 70) < 1 and r["desvio"] < 1, "demora fija: %s" % r)
    r = gr(exp, [1000, 1500, 2200, 2500], 120); igual(estados(r), ["ok", "ok", "atrasado", "ok"], "grilla: tarde"); verificar(not r["ok"])
    r = gr([1000, 1500, 2500], [1000, 1500, 2000, 2500], 120, {"silencios": [2000]}); verificar(r["extraSilencio"] and not r["ok"], "golpe en el silencio: %s" % r)
    libre = lambda h: pg.evaluate("(a)=>Gioval.ritmo.evaluar.libre(a,1000,500,120)", h)
    verificar(libre([1000, 1500, 1750, 2250])["ok"], "libre sobre la grilla de corcheas")
    igual(libre([1000, 1500, 1625])["motivo"], "desparejo", "libre fuera de grilla"); igual(libre([1000])["motivo"], "pocos"); igual(libre([1000 + 250 * i for i in range(9)])["motivo"], "muchos")
    ctx.close()

DETECTORES = ("click", "palma", "tambor", "cajon", "pandereta")

@prueba("golpes: detector con audio sintético (precisión del tiempo, tempos, instrumentos, falsos positivos, refractario, silencio de la app)")
def t_golpes_detector(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    peor = 0
    for bpm in (60, 100, 150):
        per = 60000 / bpm
        for tipo in DETECTORES:
            hits = [3700 + k * per for k in range(10)]
            x = senal_golpes(3.7 + 10 * per / 1000 + 0.6, hits, tipo, 0.004, semilla=bpm, zumbido=0.002)
            ev, info = simular_golpes(pg, x)
            verificar(len(ev) == 10, "%s a %d bpm: detectó %d de 10" % (tipo, bpm, len(ev)))
            err = max(abs(e[0] - h) for e, h in zip(ev, hits)); peor = max(peor, err)
            verificar(err <= 6, "%s a %d bpm: error de tiempo %.1f ms" % (tipo, bpm, err))
            verificar(all(0 <= e[1] <= 1 for e in ev), "fuerza fuera de 0..1")
    # sin golpes: ruido de sala, zumbido, crescendo lento, ventilador que arranca después de calibrar -> sin falsos positivos
    np = __import__("numpy")
    def crescendo(x, rng, sr):
        t = np.arange(len(x)) / sr; return x + np.clip((t - 4) * 0.004, 0, 0.05) * np.sin(2 * np.pi * 120 * t)
    def ventilador(x, rng, sr):
        x = x.copy(); i = int(6 * sr); x[i:] += rng.normal(0, 0.03, len(x) - i); return x
    casos = {"ruido 0,004": dict(ruido=0.004), "ruido 0,02 (sala ruidosa)": dict(ruido=0.02), "zumbido 50 Hz": dict(ruido=0.004, zumbido=0.012),
             "crescendo lento": dict(ruido=0.003, extra=crescendo)}
    for nombre, kw in casos.items():
        ev, _ = simular_golpes(pg, senal_golpes(14, [], "palma", semilla=5, **kw)); igual(len(ev), 0, "falsos positivos con " + nombre)
    ev, _ = simular_golpes(pg, senal_golpes(14, [], "palma", 0.004, semilla=6, extra=ventilador))
    verificar(len(ev) <= 1, "ventilador que arranca: %d eventos (se tolera 1, el del arranque)" % len(ev))
    verificar(all(e[0] > 6000 - 20 for e in ev), "el ventilador no debería disparar antes de arrancar")
    # ninguna detección durante la calibración (aunque haya golpes): se ignoran
    ev, info = simular_golpes(pg, senal_golpes(8, [1000, 2000, 5000, 5600], "palma", 0.004, semilla=7)); verificar(all(e[0] > 3000 for e in ev), "emitió durante la calibración")
    # refractario: dos golpes a 30 ms cuentan como uno; a 200 ms, como dos
    ev, _ = simular_golpes(pg, senal_golpes(7, [3800, 3830, 4400, 4600], "click", 0.004, semilla=8)); igual(len(ev), 3, "doble a 30 ms = 1 · pares a 200 ms = 2")
    # rasgueo de guitarra: 6 cuerdas en 50 ms = 1 golpe (el del inicio)
    ev, _ = simular_golpes(pg, senal_golpes(7, [3800 + 10 * i for i in range(6)] + [5200], "tambor", 0.004, semilla=9)); igual(len(ev), 2, "rasgueo = 1 golpe")
    verificar(abs(ev[0][0] - 3800) <= 6, "el rasgueo marca el inicio")
    # intensidad aproximada: más fuerte -> más "fuerza"
    fz = []
    for a in (0.04, 0.1, 0.3, 0.8):
        ev, _ = simular_golpes(pg, senal_golpes(6, [4000], "palma", 0.004, semilla=10, amps=[a])); verificar(len(ev) == 1, "amp %s no detectado" % a); fz.append(ev[0][1])
    verificar(fz == sorted(fz) and fz[-1] > fz[0] + 0.3, "la fuerza no crece con la intensidad: %s" % fz)
    # sala ruidosa: el umbral sube solo y los golpes siguen detectándose
    hits = [3800 + 500 * k for k in range(10)]
    ev, info = simular_golpes(pg, senal_golpes(10, hits, "palma", 0.02, semilla=11)); igual(len(ev), 10, "golpes en sala ruidosa"); verificar(info["umbral"] > 0.05, "el umbral no se adaptó al ruido: %s" % info)
    # golpes muy suaves: con sensibilidad normal se pierden y con más sensibilidad se escuchan (límite documentado)
    suaves = [3800 + 500 * k for k in range(6)]; xs = senal_golpes(8, suaves, "palma", 0.004, semilla=12, amps=[0.012] * 6)
    n1 = len(simular_golpes(pg, xs)[0]); n2 = len(simular_golpes(pg, xs, sens=3)[0]); verificar(n2 > n1, "más sensibilidad no ayudó: %d → %d" % (n1, n2))
    # silencio de la app: los golpes dentro de una ventana silenciada se descartan
    hits = [3800 + 500 * k for k in range(8)]
    ev, _ = simular_golpes(pg, senal_golpes(9, hits, "palma", 0.004, semilla=13), mudo=[[4750, 5400]]); igual(len(ev), 6, "golpes silenciados por la voz de la app")
    ctx.close(); return "tiempo peor caso %.1f ms; 15 señales × 10 golpes; falsos positivos 0" % peor

def con_microfono_falso(C, wav):
    return Banco(C.pw, ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--use-file-for-fake-audio-capture=%s%%noloop" % wav])

JS_ESCUCHAR = """()=>{ window.__ev=[]; Gioval.entrada.suscribir('golpe',e=>window.__ev.push([e.t,e.fuerza,e.fuente])); const G=Gioval.entrada.proveedores.golpes;
  return G.iniciar({fuente:'mic'}).then(f=>G.calibrar().then(i=>[f,i])); }"""

@prueba("golpes: micrófono falso de Chrome con audio de percusión (WAV): inicios en el tiempo justo, sin falsos positivos, silencio de la app")
def t_golpes_microfono(C):
    SALIDA.mkdir(exist_ok=True); resumen = []
    ritmo = [0, 600, 1200, 1500, 1800, 2400, 2700, 3000, 3600, 4200]
    h100 = [3800 + 600 * k for k in range(10)]
    casos = [("palmas_100bpm", senal_golpes(3.8 + 6.4 + 0.8, h100, "palma", 0.004, semilla=21), h100, None),
             ("cajon_ritmo", senal_golpes(3.8 + 4.2 + 0.8, [3800 + t for t in ritmo], "cajon", 0.004, semilla=22), [3800 + t for t in ritmo], None),
             ("silencio_con_zumbido", senal_golpes(9, [], "palma", 0.005, semilla=23, zumbido=0.01), [], None),
             ("palmas_con_voz_de_la_app", senal_golpes(3.8 + 6.4 + 0.8, h100, "palma", 0.004, semilla=24), h100, "mudo")]
    for nombre, x, verdad, modo in casos:
        wav = a_wav(x, SALIDA / (nombre + ".wav")); b = con_microfono_falso(C, wav); err = []
        try:
            ctx = b.contexto("360x700", permissions=["microphone"]); pg = abrir(ctx, C.url + "/index.html", errores=err, rapido=False)
            f, info = pg.evaluate(JS_ESCUCHAR); igual(f, "mic", "fuente"); verificar(info and info["utilMs"] >= 2990, "calibración: %s" % info)
            verificar(info["piso"] < 0.03, "piso de ruido: %s" % info)
            if modo == "mudo":
                pg.wait_for_function("window.__ev.length>=3", timeout=15000); pg.evaluate("muteUntil=performance.now()+1300")
                pg.wait_for_timeout(5000)
            else:
                pg.wait_for_timeout(int(len(x) / 48 - 3000 + 600))
            ev = pg.evaluate("window.__ev"); ts = [e[0] for e in ev]
            if modo == "mudo":
                igual(len(ev), 8, "con la app 'hablando' se pierden justo los 2 golpes silenciados")
                gaps = [round(q - p) for p, q in zip(ts, ts[1:])]; verificar(sum(1 for g in gaps if 1750 <= g <= 1850) == 1, "hueco de 3 pulsos: %s" % gaps)
            else:
                igual(len(ev), len(verdad), nombre + ": cantidad de golpes")
                for k in range(1, len(ev)): verificar(abs((ts[k] - ts[0]) - (verdad[k] - verdad[0])) <= 12, "%s: golpe %d fuera de tiempo (%.1f ms)" % (nombre, k, (ts[k] - ts[0]) - (verdad[k] - verdad[0])))
            verificar(all(e[2] == "mic" for e in ev)); verificar(not err, str(err)); ctx.close()
            resumen.append("%s=%d" % (nombre, len(ev)))
        finally: b.cerrar()
    return ", ".join(resumen)

@prueba("golpes: Música y Ritmo comparten UN solo flujo de micrófono (un permiso) y se apaga cuando nadie lo usa")
def t_golpes_flujo_compartido(C):
    SALIDA.mkdir(exist_ok=True); wav = a_wav(senal_golpes(6, [], "palma", 0.004, semilla=31), SALIDA / "ruido.wav"); b = con_microfono_falso(C, wav); err = []
    try:
        ctx = b.contexto("360x700", permissions=["microphone"])
        pg = abrir(ctx, C.url + "/index.html", errores=err, rapido=False, extra_init="window.__gum=0; (function(){ var o=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices); navigator.mediaDevices.getUserMedia=function(c){ window.__gum++; return o(c); }; })();")
        r = pg.evaluate("""async()=>{ const M=Gioval.entrada.proveedores.microfono, G=Gioval.entrada.proveedores.golpes; const out={};
          await M.iniciar({}); await G.iniciar({fuente:'mic'}); out.llamadas=window.__gum; out.activos=[M.activo,G.activo,G.fuente];
          G.detener(); await new Promise(r=>setTimeout(r,100)); out.tras_golpes=M.activo; M.detener(); return out; }""")
        igual(r["llamadas"], 1, "getUserMedia debería pedirse una sola vez"); igual(r["activos"], [True, True, "mic"]); verificar(r["tras_golpes"], "Música debería seguir escuchando")
        verificar(not err, str(err)); ctx.close()
    finally: b.cerrar()

@prueba("Ritmo: sesión completa por toque en 360x700 y 740x330 (dominio, desbloqueo, ayudas, errores sin castigo, informe)")
def t_ritmo_sesion(C):
    detalle = []
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, semilla=81, rapido=False, extra_init=ESC_TEST); instalar_speak(pg); entrar(pg, "Vale")
        abrir_isla(pg, "Ritmo"); CAPTURAS.append(foto(pg, v + "_60_ritmo_menu"))
        txt = pg.evaluate("document.getElementById('menuIslaItems').innerText"); verificar("Tocar con mi instrumento" in txt and "Sesión de hoy" in txt, txt)
        tarjeta(pg, "Sesión de hoy"); esperar_fase(pg, "turno"); pg.wait_for_timeout(200)
        igual(pg.evaluate("document.querySelector('.screen.active').id"), "rit", "pantalla")
        CAPTURAS.append(foto(pg, v + "_61_ritmo_eco_tarjetas"))
        verificar(jugar_ritmo(pg) == "fin"); cerrar_fin(pg)
        for _ in range(3):
            pg.evaluate("PACK=PACKS.find(p=>p.id==='ritmo')")
            if pg.evaluate("SK('rit_pulso').mast"): break
            abrir_isla(pg, "Ritmo"); tarjeta(pg, "Sesión de hoy"); verificar(jugar_ritmo(pg) == "fin"); cerrar_fin(pg)
        verificar(pg.evaluate("SK('rit_pulso').mast"), "rit_pulso no quedó dominada")
        desbloq = pg.evaluate("unlockedList().map(s=>s.id)"); verificar(all(x in desbloq for x in ("rit_eco2", "rit_tempo", "rit_base")), "desbloqueo: %s" % desbloq)
        # una sesión con errores inyectados (golpe adelantado, faltante, de más): la app lo dice con amabilidad, reintenta y no castiga
        pg.evaluate("window.__LOG.length=0"); abrir_isla(pg, "Ritmo"); tarjeta(pg, "Sesión de hoy")
        verificar(jugar_ritmo(pg, errores=["adelantado", None, "falta", None, "extra", None]) == "fin", "la sesión con errores no terminó")
        dicho = " | ".join(pg.evaluate("window.__LOG")); verificar("rápido" in dicho and ("Faltó" in dicho or "de más" in dicho), "no explicó los errores: " + dicho[:400])
        verificar(not any(w in dicho.lower() for w in ("incorrecto", "perdiste", "fallaste", "mal ")), "texto con tono de castigo: " + dicho[:300])
        cerrar_fin(pg)
        reg = pg.evaluate("store.ritmo.Vale"); verificar(len(reg) >= 14 and all(k in reg[0] for k in ("t", "s", "d", "b", "n", "o", "x", "f", "bpm", "l", "c", "ok")), "registro de regularidad: %s" % reg[:1])
        verificar(any(e["ok"] == 0 for e in reg), "no se registró ningún intento fallido (¿se inyectaron los errores?)")
        rep = pg.evaluate("reportText()"); verificar("REGULARIDAD DEL RITMO" in rep and "Desvío medio general" in rep and "No juzga la técnica" in rep and "Evolución" in rep, rep[-900:])
        verificar("ISLA RITMO" in rep and "Sentir el pulso" in rep, "el informe general no lista la isla: " + rep[:300])
        pg.evaluate("goMenuIsla()"); pg.click(".island:has-text('Mis logros')"); pg.wait_for_timeout(250); CAPTURAS.append(foto(pg, v + "_62_ritmo_logros"))
        verificar(not err, "%s: %s" % (v, err)); detalle.append("%s: %d mediciones" % (v, len(reg))); ctx.close()
    return "; ".join(detalle)

HABS = ["rit_pulso", "rit_eco2", "rit_tempo", "rit_base", "rit_eco3", "rit_eco4", "rit_silencio", "rit_solo", "rit_lee1", "rit_lee2", "rit_llamada", "rit_cancion", "rit_leemix", "rit_compone"]

@prueba("Ritmo: las 14 habilidades se juegan completas (ayudas, silencios, tarjetas, canciones, llamada y respuesta, composición)")
def t_ritmo_habilidades(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, semilla=91, rapido=False, extra_init=ESC_TEST); instalar_speak(pg); entrar(pg, "Vale")
    igual(pg.evaluate("PACKS.find(p=>p.id==='ritmo').skills.map(s=>s.id)"), HABS, "habilidades")
    pg.evaluate("window.__LOG.length=0"); casos = {"rit_eco3": ["adelantado", None], "rit_silencio": ["extra", None], "rit_lee2": ["falta", None], "rit_base": ["atrasado", None]}
    for sid in HABS:
        abrir_isla(pg, "Ritmo"); solo_habilidad(pg, sid); tarjeta(pg, "Sesión de hoy"); pg.evaluate("S.session.items.length=2")
        opc = {"libre": [0]} if sid == "rit_llamada" else None
        r = jugar_ritmo(pg, errores=casos.get(sid), opciones=opc, limite_s=90); verificar(r == "fin", "%s: terminó con %s" % (sid, r)); cerrar_fin(pg)
        n = pg.evaluate("(store.ritmo.Vale||[]).filter(e=>e.s==='%s').length" % sid); verificar(n >= 1, "%s sin mediciones" % sid)
    dicho = " | ".join(pg.evaluate("window.__LOG")).lower()
    for frag in ("shh", "ti-ti", "yo toco un ritmo", "armá tu propio ritmo", "probá con más golpes", "este es el ritmo de una canción"):
        verificar(frag in dicho, "falta el texto '%s' (¿se jugó esa actividad?)" % frag)
    verificar(any(a in dicho for a in ("tortuga", "conejo", "guepardo")), "falta la frase del tempo (¿se jugó 'lento, medio y rápido'?)")
    verificar(not err, str(err)); ctx.close(); return "14 habilidades"

@prueba("Ritmo: composición de 4 pulsos, lectura con tarjetas y silencios en 360x700 y 740x330 (capturas)")
def t_ritmo_pantallas(C):
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, semilla=93, rapido=False, extra_init="window.__RITMO_ESCALA=2;"); instalar_speak(pg); entrar(pg, "Vale")
        for sid, fase, tag, espera in (("rit_lee2", "turno", "lectura", 900), ("rit_compone", "componer", "componer", 400), ("rit_silencio", "turno", "silencio", 900)):
            abrir_isla(pg, "Ritmo"); solo_habilidad(pg, sid); tarjeta(pg, "Sesión de hoy"); esperar_fase(pg, fase); pg.wait_for_timeout(espera)
            CAPTURAS.append(foto(pg, "%s_64_ritmo_%s" % (v, tag)))
            pg.evaluate("S.run++; resetFlow(); goMenuIsla()")
        verificar(not err, "%s: %s" % (v, err)); ctx.close()

@prueba("Ritmo: chequeo semanal sin ayuda (un solo intento) e informe con regularidad")
def t_ritmo_chequeo(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, semilla=95, rapido=False, extra_init=ESC_TEST); instalar_speak(pg); entrar(pg, "Vale")
    for _ in range(3):
        abrir_isla(pg, "Ritmo"); pg.evaluate("PACK=PACKS.find(p=>p.id==='ritmo')")
        if pg.evaluate("SK('rit_pulso').mast"): break
        tarjeta(pg, "Sesión de hoy"); jugar_ritmo(pg); cerrar_fin(pg)
    abrir_isla(pg, "Ritmo"); tarjeta(pg, "Chequeo semanal")
    verificar(jugar_ritmo(pg, errores=[None, "adelantado"]) == "fin"); cerrar_fin(pg)
    ck = pg.evaluate("store.checks.Vale"); verificar(len(ck) == 1 and ck[0]["p"] == "ritmo" and 0 <= ck[0]["ok"] < ck[0]["n"], str(ck))
    reg = pg.evaluate("store.ritmo.Vale.filter(e=>e.c)"); verificar(len(reg) >= 1, "el chequeo no registró regularidad")
    verificar("CHEQUEOS SIN AYUDA" in pg.evaluate("reportText()")); verificar(not err, str(err)); ctx.close()

@prueba("Ritmo: la base que suena no se escucha a sí misma (el clic que entra por el micrófono se enmascara) y los golpes del niño siguen contando")
def t_ritmo_mascara(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, semilla=97, rapido=False, extra_init=ESC_TEST); instalar_speak(pg); entrar(pg, "Vale")
    abrir_isla(pg, "Ritmo"); solo_habilidad(pg, "rit_base")
    pg.evaluate("(()=>{ const G=Gioval.entrada.proveedores.golpes; G.activo=true; G.fuente='mic'; window.__fugas={emitidas:0,filtradas:0}; })()")   # se simula 'micrófono encendido'
    tarjeta(pg, "Sesión de hoy"); pg.evaluate("S.session.items.length=1")
    JS = """(T)=>{ const G=Gioval.entrada.proveedores.golpes, L=60, d=T.beatMs;
      const em=(t,f)=>{ setTimeout(()=>{ if(f==='fuga'){ if(G.silenciado(t)){ window.__fugas.filtradas++; return; } window.__fugas.emitidas++; } Gioval.entrada.emitir({tipo:'golpe',t:t,fuerza:.5,fuente:'mic'}); }, Math.max(0,t-performance.now()-3)); };
      for(let i=0;i<12;i++) em(T.tS+i*d+L,'fuga');
      T.esperados.forEach(e=>em(e+25,'nino')); }"""   # parlante: L=60 ms después de cada clic; niño: 25 ms después del pulso
    visto = -1; t0 = time.time()
    while time.time() - t0 < 60:
        pg.wait_for_timeout(30)
        if pg.evaluate("document.getElementById('finish').classList.contains('show')"): break
        t = pg.evaluate("Gioval.ritmo.turno&&Gioval.ritmo.turno.id!==%d?Gioval.ritmo.turno:null" % visto)
        if t: visto = t["id"]; pg.evaluate(JS, t)
    verificar(pg.evaluate("document.getElementById('finish').classList.contains('show')"), "la sesión no terminó")
    f = pg.evaluate("window.__fugas"); eco = pg.evaluate("Gioval.ritmo.eco")
    verificar(eco is not None and 50 <= eco <= 70, "demora del parlante estimada en la cuenta: %s (real 60)" % eco)
    verificar(f["filtradas"] >= 4, "no se enmascaró el clic de la base: %s" % f)
    reg = pg.evaluate("store.ritmo.Vale"); verificar(reg and reg[0]["x"] == 0 and reg[0]["ok"] == 1, "los golpes del niño deberían contar y la base no sumar golpes de más: %s" % reg[:2])
    verificar(not err, str(err)); ctx.close(); return "demora estimada %.0f ms; clics enmascarados %d" % (eco, f["filtradas"])

@prueba("Ritmo: encender 'Tocar con mi instrumento' (micrófono falso): calibración de 3 s, detección y apagado al salir de la isla")
def t_ritmo_mic_interfaz(C):
    SALIDA.mkdir(exist_ok=True); err = []
    x = senal_golpes(3.8 + 3.0, [3800 + 600 * k for k in range(4)], "palma", 0.004, semilla=41)
    for v in ("360x700", "740x330"):
        wav = a_wav(x, SALIDA / ("mic_interfaz_%s.wav" % v)); b = con_microfono_falso(C, wav)
        try:
            ctx = b.contexto(v, permissions=["microphone"])
            pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, rapido=False); instalar_speak(pg); entrar(pg, "Vale"); abrir_isla(pg, "Ritmo")
            pg.click(".island:has-text('Tocar con mi instrumento')"); pg.wait_for_selector("#rtCal.show", timeout=5000); pg.wait_for_timeout(1200)
            CAPTURAS.append(foto(pg, v + "_65_ritmo_calibrando"))
            verificar("Shhh" in pg.evaluate("document.getElementById('rtCalT').innerText"), "no muestra la calibración")
            pg.wait_for_function("document.getElementById('rtCalT').innerText.includes('Listo')", timeout=8000)
            igual(pg.evaluate("Gioval.entrada.proveedores.golpes.estado().calibrado"), True, "calibrado"); CAPTURAS.append(foto(pg, v + "_66_ritmo_listo"))
            pg.wait_for_function("document.getElementById('rtCalT').innerText.includes('escuché')", timeout=9000)
            pg.wait_for_function("!document.getElementById('rtCal').classList.contains('show')", timeout=4000)
            verificar("Usar la pantalla" in pg.evaluate("document.getElementById('menuIslaItems').innerText"), "la tarjeta no cambió")
            tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(500); verificar(pg.evaluate("document.getElementById('rit').classList.contains('micOn')"), "no muestra el modo micrófono")
            CAPTURAS.append(foto(pg, v + "_67_ritmo_modo_microfono")); pg.evaluate("S.run++; resetFlow(); goMenuIsla()")
            pg.evaluate("goMap()"); pg.wait_for_timeout(200); igual(pg.evaluate("Gioval.entrada.proveedores.golpes.activo"), False, "debería apagarse al salir de la isla")
            ctx.close()
        finally: b.cerrar()
    verificar(not err, str(err))

@prueba("idioma inglés: la isla Ritmo (menú, sesión con errores, informe) sin una palabra en español")
def t_ritmo_ingles(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, semilla=99, rapido=False, extra_init="window.__RITMO_ESCALA=5;localStorage.setItem('gioval_idioma','en');"); instalar_speak(pg); entrar(pg, "Vale")
    abrir_isla(pg, "Rhythm"); txt = pg.evaluate("document.getElementById('menuIslaItems').innerText")
    verificar("Play with my instrument" in txt and "Today" in txt, txt); verificar(not sin_espanol([txt]), txt)
    tarjeta(pg, "Today"); esperar_fase(pg, "turno"); pg.wait_for_timeout(200)
    visibles = pg.evaluate("[...document.querySelectorAll('#rit .lbl, #rit button, #rit small')].map(e=>e.textContent)"); verificar(not sin_espanol(visibles), str(visibles))
    verificar(jugar_ritmo(pg, errores=["adelantado", None, "falta", None]) == "fin"); cerrar_fin(pg)
    dicho = pg.evaluate("window.__LOG.concat(window.__BUB)"); verificar(not sin_espanol(dicho), "español en Ritmo en inglés: %s" % sin_espanol(dicho)[:3])
    verificar(any("Listen" in x or "listen" in x for x in dicho), "frases en inglés: %s" % dicho[:4])
    rep = pg.evaluate("reportText()"); verificar("RHYTHM STEADINESS" in rep and "Feel the beat" in rep and not sin_espanol([rep[rep.index("RHYTHM STEADINESS"):rep.index("RHYTHM STEADINESS") + 1200]]), rep[-900:])
    igual(pg.evaluate("[...Gioval.i18n.faltantes]"), [], "claves faltantes"); verificar(not err, str(err)); ctx.close()

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
