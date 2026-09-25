#!/usr/bin/env python3
"""Revisa una bitácora de averías: cada entrada tiene que tener sus cuatro apartados, un candado
con contenido y su familia.

Una avería no está cerrada hasta que tiene candado. Este script es el candado de la propia bitácora:
sale con código 1 si alguna entrada está a medias, para que se pueda poner en un hook, en la
integración continua o antes de cada commit.

Qué cuenta como entrada: todo título que lleve una fecha (2026-09-25, 2026-9-5, 25-09-2026,
25-sep-2026 o «25 de septiembre de 2026»), esté donde esté, y también todo título SIN fecha cuya
sección lleve alguno de los rótulos del molde. Si la fecha falta o no va al principio en formato
AAAA-MM-DD, se revisa igual y se marca, para que ninguna entrada se cuele sin revisar. Los títulos
«## » que no son entradas (secciones como «Cómo se usa») se listan al final.

Qué se exige en cada entrada:
  - los rótulos **Síntoma**, **Causa real**, **Cómo se comprobó** y **Candado** (con punto, con dos
    puntos o sin nada; «Candados» también vale);
  - que el candado tenga texto debajo antes del siguiente rótulo;
  - la familia, dicha en el título «(familia: …)» o en una línea «Familia: …»: éxito falso, pieza
    fuera de lista o conclusión sin control (también en inglés: false success, unlisted piece,
    unchecked conclusion). Si es una familia nueva, se escribe «familia nueva: …» y también vale.

Uso:
    python3 revisar_bitacora.py BITACORA.md
    python3 revisar_bitacora.py --prueba      # comprueba que el revisor distingue cada caso

Licencia: MIT.
"""
import re
import sys

APARTADOS = {
    "Síntoma": r"S[íi]ntomas?",
    "Causa real": r"Causa real",
    "Cómo se comprobó": r"C[óo]mo se comprob[óo]",
    "Candado": r"Candados?",
}
FAMILIAS = r"(éxito falso|exito falso|fuera de lista|sin control|false success|unlisted piece|unchecked conclusion|nueva|new)"
TITULO = re.compile(r"^(#{1,4})[ \t]+(.+)$", re.M)
FECHA = re.compile(r"(?i)^(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}-(\d{1,2}|[a-zé]{3,4})-\d{4})\b")
PARECE_FECHA = re.compile(r"(?i)\b(\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}|\d{1,2}[-/. ][a-zé]{3,10}\.?[-/. ]\d{4}"
                          r"|\d{1,2}\s+de\s+[a-zé]{3,10}\s+(?:de\s+|del\s+)?\d{4})\b")
# Un rótulo es una negrita corta que acaba en punto o dos puntos: «**Candado.**», «**Síntoma:**».
# «**Se niega** a…» dentro de una lista NO es un rótulo: es texto del candado.
ROTULO = re.compile(r"^\s*(?:[-*]\s*)?\*\*[^*\n]{2,40}?(?:[.:]\*\*|\*\*:)", re.M)
# Candados de relleno: no cuentan como candado.
RELLENO = re.compile(r"(?i)\b(pendiente|todo|tbd|por hacer|ninguno|ninguna|n/a|sin candado|no hay candado|"
                     r"todavía no|aún no|más adelante)\b")
# Intenciones: «a partir de ahora tendré cuidado» no se ejecuta, así que no es un candado.
INTENCION = re.compile(r"(?i)(a partir de ahora|tendré (más )?cuidado|tener (más )?cuidado|intentaré|"
                       r"procuraré|no volverá a pasar)")
# Texto del molde sin rellenar.
MOLDE = re.compile(r"(?i)^\W*(lo que se veía|lo que era de verdad|el experimento que lo demostró|"
                   r"qué se ha cambiado para que no pueda repetirse|what you saw|what it really was|"
                   r"the experiment that proved it)")


def rotulo(nombre_re):
    return re.compile(r"^\s*(?:[-*]\s*)?\*\*" + nombre_re + r"\s*[.:]?\*\*:?", re.M | re.I)


def sin_codigo(texto):
    """Vacía el contenido de los bloques de código (```), conservando las líneas: un «# comentario»
    de bash dentro de un bloque no es un título."""
    fuera, lineas = True, []
    for l in texto.split("\n"):
        if l.lstrip().startswith("```"):
            fuera = not fuera
            lineas.append(l)
        else:
            lineas.append(l if fuera else " " * len(l))  # misma longitud: las posiciones no cambian
    return "\n".join(lineas)


def entradas(texto):
    """Parte el texto en entradas. Devuelve lista de (título, cuerpo, fecha_ok). La estructura se
    busca con los bloques de código vaciados; el cuerpo se devuelve con su texto original."""
    original, texto = texto, sin_codigo(texto)
    todos = list(TITULO.finditer(texto))

    def fin_de(m, inicios):
        nivel = len(m.group(1))
        for otro in re.finditer(r"^(#{1,4})[ \t]", texto[m.end():], re.M):
            if len(otro.group(1)) <= nivel or (m.end() + otro.start()) in inicios:
                return m.end() + otro.start()
        return len(texto)

    # Es una entrada todo título con fecha, y también todo título SIN fecha cuya sección lleve alguno
    # de los rótulos del molde: así una entrada sin fecha no se cuela como «bitácora vacía».
    con_fecha = {m.start() for m in todos if PARECE_FECHA.search(m.group(2))}
    rotulos = [rotulo(p) for p in APARTADOS.values()]
    # Un apartado sin fecha DENTRO de una entrada con fecha (un «### Apéndice») es parte de ella.
    tramos = [(m.start(), fin_de(m, con_fecha), len(m.group(1))) for m in todos if m.start() in con_fecha]
    titulos = []
    for m in todos:
        if m.start() in con_fecha:
            titulos.append(m)
        elif (len(m.group(1)) >= 2
              and not any(a < m.start() < b and nivel < len(m.group(1)) for a, b, nivel in tramos)
              and any(r.search(texto[m.end():fin_de(m, con_fecha)]) for r in rotulos)):
            titulos.append(m)
    inicios = {t.start() for t in titulos}
    res = []
    for m in titulos:
        # La entrada acaba en el siguiente título de su nivel o superior, o en la siguiente entrada.
        nivel = len(m.group(1))
        fin = len(texto)
        for otro in re.finditer(r"^(#{1,4})[ \t]", texto[m.end():], re.M):
            if len(otro.group(1)) <= nivel or (m.end() + otro.start()) in inicios:
                fin = m.end() + otro.start()
                break
        titulo = re.sub(r"^[\W_]+", "", m.group(2).strip()) or m.group(2).strip()
        res.append((titulo, original[m.start():fin], bool(FECHA.match(titulo))))
    return res


def contenido_de(cuerpo, desde):
    """El texto de un apartado: desde su rótulo hasta el siguiente rótulo o título."""
    resto = cuerpo[desde:]
    sig = ROTULO.search(sin_codigo(resto))
    sig_titulo = re.search(r"^#{1,4}[ \t]", sin_codigo(resto), re.M)
    cortes = [x.start() for x in (sig, sig_titulo) if x]
    return resto[:min(cortes)] if cortes else resto


def revisar_entrada(titulo, cuerpo, fecha_ok):
    faltan = []
    if not fecha_ok:
        faltan.append("fecha al principio del título, en formato AAAA-MM-DD")
    for nombre, patron in APARTADOS.items():
        r = rotulo(patron).search(cuerpo)
        if not r:
            faltan.append(nombre)
            continue
        contenido = contenido_de(cuerpo, r.end())
        palabras = re.findall(r"\w+", contenido)
        if not contenido.strip() or not palabras:
            faltan.append(f"{nombre} (está vacío)")
        elif MOLDE.match(contenido.strip()):
            faltan.append(f"{nombre} (es el texto del molde sin rellenar)")
        elif nombre == "Candado" and (INTENCION.search(contenido)
                                      or len(palabras) < 4
                                      or (len(palabras) < 12 and RELLENO.search(contenido))):
            faltan.append("Candado (es de relleno o una intención: «pendiente», «TODO», «tendré cuidado»… "
                          "no se ejecuta, no impide nada)")
    familia_titulo = re.search(r"(?i)\((?:famil(?:ia|ias|y|ies)\b[^)]*" + FAMILIAS + r"|new famil)", titulo)
    familia_linea = re.search(r"(?im)^\s*(?:[-*]\s*)?\**(?:famil(?:ia|ias|y|ies)\b[^\n]*" + FAMILIAS + r"|new famil)", cuerpo)
    if not (familia_titulo or familia_linea):
        faltan.append("familia (en el título «(familia: …)» o en una línea «Familia: …»)")
    return faltan


def revisar(texto):
    """Devuelve (número de entradas, lista de problemas). Cada problema: (título, qué falta)."""
    ents = entradas(texto)
    problemas = []
    for titulo, cuerpo, fecha_ok in ents:
        faltan = revisar_entrada(titulo, cuerpo, fecha_ok)
        if faltan:
            problemas.append((titulo[:80], faltan))
    return len(ents), problemas


def informe(n, problemas, texto=""):
    # Títulos «## » que no se han revisado como entradas (secciones como «Cómo se usa»): se listan,
    # para que se vea qué se ha quedado fuera.
    revisados = {t for t, _, _ in entradas(texto)}
    fuera = [m.group(1).strip() for m in re.finditer(r"^##[ \t]+(.+)$", sin_codigo(texto), re.M)
             if (re.sub(r"^[\W_]+", "", m.group(1).strip()) or m.group(1).strip()) not in revisados]
    nota = ("  (títulos «## » que no son entradas y no se han revisado: " + " · ".join(t[:40] for t in fuera) + ")"
            if fuera else "")
    if n == 0:
        if "# Bitácora de averías" in texto:
            print("OK · la bitácora está vacía (todavía no hay averías apuntadas).")
            if nota:
                print(nota)
            return 0
        # Cero entradas en un fichero que no parece una bitácora es un éxito falso en potencia: se avisa.
        print("No encuentro ninguna entrada («## AAAA-MM-DD · Título»). ¿Es la bitácora correcta?")
        return 1
    if not problemas:
        print(f"OK · {n} entradas, todas con sus cuatro apartados, su candado y su familia.")
    else:
        print(f"{len(problemas)} de {n} entradas sin cerrar:")
        for titulo, faltan in problemas:
            print(f"  - {titulo}\n      falta: {', '.join(faltan)}")
    if nota:
        print(nota)
    return 1 if problemas else 0


def leer(ruta):
    with open(ruta, "rb") as f:
        crudo = f.read()
    if crudo[:2] in (b"\xff\xfe", b"\xfe\xff"):
        texto = crudo.decode("utf-16", errors="replace")
    else:
        texto = crudo.decode("utf-8-sig", errors="replace")
    return texto.replace("\r\n", "\n")


# --- Autoprueba: cada caso salió de un fallo real del propio revisor -------------------------------
BUENA = """## 2026-01-01 · El robot decía OK y no descargaba nada (familia: el éxito falso)
**Síntoma.** Cero ficheros nuevos durante semanas, con código 0.
**Causa real.** Un except se tragaba el error.
**Cómo se comprobó.** Con el except quitado, sale la traza en la línea 42.
**Candado.** El robot sale con código 1 si no descarga nada en 7 días; probado con una carpeta vacía.
"""
CAND = "El robot sale con código 1 si no descarga nada en 7 días; probado con una carpeta vacía."
CASOS = [
    # (nombre, texto, entradas esperadas, lo que debe aparecer en «falta» — None = sin problemas)
    ("entrada buena", BUENA, 1, None),
    ("rótulos con dos puntos y candado en la línea siguiente",
     BUENA.replace("**Síntoma.**", "**Síntoma:**").replace("**Candado.** El", "**Candado:**\n\nEl"), 1, None),
    ("molde en inglés «(family: false success)»", BUENA.replace("(familia: el éxito falso)", "(family: false success)"), 1, None),
    ("falta el Síntoma", BUENA.replace("**Síntoma.** Cero ficheros nuevos durante semanas, con código 0.\n", ""), 1, "Síntoma"),
    ("falta la Causa real", BUENA.replace("**Causa real.**", "**Motivo.**"), 1, "Causa real"),
    ("falta Cómo se comprobó", BUENA.replace("**Cómo se comprobó.**", "**Prueba.**"), 1, "Cómo se comprobó"),
    ("candado vacío seguido de otro rótulo",
     BUENA.replace("**Candado.** El robot sale con código 1 si no descarga nada en 7 días; probado con una carpeta vacía.",
                   "**Candado.**\n**Lección.** Hay que mirar el resultado."), 1, "Candado (está vacío)"),
    ("familia solo de pasada («sin control de versiones»)",
     BUENA.replace(" (familia: el éxito falso)", "").replace("Un except", "La carpeta estaba sin control de versiones y un except"),
     1, "familia"),
    ("entrada con «###» y guion, sin candado, debajo de una buena (no debe quedar absorbida)",
     BUENA + "\n### 2026-01-02 - El vigía no avisó (familia: sin control)\n**Síntoma.** x\n**Causa real.** y\n**Cómo se comprobó.** z\n",
     2, "Candado"),
    ("familia nueva en el título, en una línea y en inglés",
     BUENA.replace("(familia: el éxito falso)", "(familia nueva: el aviso sin contexto)") + "\n"
     + BUENA.replace(" (familia: el éxito falso)", "").replace("**Síntoma.**", "**Familia nueva:** el aviso sin contexto\n**Síntoma.**")
     + "\n" + BUENA.replace("(familia: el éxito falso)", "(new family: silent alert)"), 3, None),
    ("fecha al final del título (no debe colarse sin revisar)",
     BUENA + "\n## El vigía dejó de avisar (25-ago-2026)\nTexto sin apartados.\n", 2, "Síntoma"),
    ("entrada a medias ENCIMA de una buena (no debe tomar prestado su candado)",
     BUENA.replace("2026-01-01", "2026-01-00").replace("**Candado.** El robot sale con código 1 si no descarga nada en 7 días; probado con una carpeta vacía.\n", "")
     .replace("## 2026-01-00", "## 2026-01-02") + BUENA.replace("## ", "### "), 2, "Candado"),
    ("familia «la pieza fuera de lista»", BUENA.replace("el éxito falso", "la pieza fuera de lista"), 1, None),
    ("candado de relleno: «Pendiente.»", BUENA.replace("El robot sale con código 1 si no descarga nada en 7 días; probado con una carpeta vacía.", "Pendiente."), 1, "relleno"),
    ("candado de relleno: «TODO»", BUENA.replace("El robot sale con código 1 si no descarga nada en 7 días; probado con una carpeta vacía.", "TODO"), 1, "relleno"),
    ("candado de relleno: «—»", BUENA.replace("El robot sale con código 1 si no descarga nada en 7 días; probado con una carpeta vacía.", "—"), 1, "Candado"),
    ("candado de relleno: el texto del molde", BUENA.replace("El robot sale con código 1 si no descarga nada en 7 días; probado con una carpeta vacía.", "Qué se ha cambiado para que no pueda repetirse, y cómo se probó."), 1, "molde"),
    ("Síntoma vacío", BUENA.replace("**Síntoma.** Cero ficheros nuevos durante semanas, con código 0.", "**Síntoma.**"), 1, "Síntoma (está vacío)"),
    ("los otros tres apartados con el texto del molde",
     BUENA.replace("Cero ficheros nuevos durante semanas, con código 0.", "Lo que se veía.")
     .replace("Un except se tragaba el error.", "Lo que era de verdad, no lo que parecía.")
     .replace("Con el except quitado, sale la traza en la línea 42.", "El experimento que lo demostró. Sin esto no vale."), 1, "molde"),
    ("candado: «A partir de ahora tendré cuidado.»", BUENA.replace(CAND, "A partir de ahora tendré cuidado."), 1, "intención"),
    ("candado: «Todavía no hay candado.»", BUENA.replace(CAND, "Todavía no hay candado."), 1, "relleno"),
    ("candado: «Queda pendiente hasta el lunes.»", BUENA.replace(CAND, "Queda pendiente hasta el lunes."), 1, "relleno"),
    ("candado: «Montar un vigía (pendiente).»", BUENA.replace(CAND, "Montar un vigía (pendiente)."), 1, "relleno"),
    ("candado real que además deja algo pendiente de otra persona (vale)",
     BUENA.replace(CAND, CAND + " Pendiente de otra persona: renovar la clave del proveedor antes del día 30."), 1, None),
    ("candado que es un bloque de código (vale)",
     BUENA.replace("**Candado.** " + CAND, "**Candado.**\n```bash\n# se niega si baja más del 10 %\npython3 robot.py --comprobar-filas --minimo 0.9\n```"), 1, None),
    ("candado en lista con negritas («- **Se niega** …»)",
     BUENA.replace("**Candado.** El robot", "**Candado.**\n- **Se niega** a seguir: el robot"), 1, None),
    ("un «# comentario» dentro de un bloque de código no corta la entrada",
     BUENA.replace("**Candado.**", "```bash\n# comentario de bash\npython3 robot.py\n```\n**Candado.**"), 1, None),
    ("títulos con la fecha entre corchetes, tras un emoji, en negrita o con otro nivel",
     BUENA.replace("## 2026-01-01", "## [2026-01-01]") + BUENA.replace("## 2026-01-01", "## 🔴 2026-01-01")
     + BUENA.replace("## 2026-01-01", "## **2026-01-01**") + BUENA.replace("## 2026-01-01", "#### 2026-01-01"), 4, None),
    ("fecha escrita «25 sep 2026» o «Avería del 2026-09-25» se revisa (y se marca)",
     BUENA.replace("## 2026-01-01", "## 25 sep 2026") + BUENA.replace("## 2026-01-01", "## Avería del 2026-09-25"), 2, "fecha al principio"),
    ("entrada sin fecha en una bitácora sin más entradas (no debe salir «vacía»)",
     "# Bitácora de averías\n\n## El vigía dejó de avisar\n**Síntoma.** No llegó nada en tres días seguidos.\n", 1, "fecha"),
    ("fecha escrita con palabras: «25 de septiembre de 2026»",
     BUENA.replace("## 2026-01-01", "## 25 de septiembre de 2026").replace(CAND, ""), 1, "Candado"),
    ("un «### Apéndice» sin fecha dentro de una entrada es parte de ella",
     BUENA + "\n### Apéndice del mismo día\n**Síntoma.** Otra cosa que se vio después, ya corregida.\n", 1, None),
    ("«## 3-5 ideas» no es una entrada", BUENA + "\n## 3-5 ideas para mejorar\ntexto\n", 1, None),
    ("fecha mal escrita (2026-9-5 y 25-sep-2026 valen; 5/9/26 no)",
     BUENA.replace("2026-01-01", "2026-9-5") + "\n" + BUENA.replace("2026-01-01", "25-sep-2026")
     + "\n## 5/9/26 · Otra\n", 3, "fecha al principio"),
]


def autoprueba():
    ok = True
    for nombre, texto, n_esperado, falta in CASOS:
        n, problemas = revisar(texto)
        rc = 1 if problemas else 0
        if falta is None:
            bien = n == n_esperado and not problemas and rc == 0
        else:
            bien = (n == n_esperado and rc == 1
                    and any(falta in f for _, fs in problemas for f in fs))
        print(("  OK    " if bien else "  FALLA ") + nombre)
        ok &= bien
    # El código de salida también se prueba: es lo que lee la integración continua o un pre-commit.
    import contextlib
    import io
    import os
    import tempfile
    with contextlib.redirect_stdout(io.StringIO()):
        rc_mala = informe(*revisar(CASOS[3][1]), CASOS[3][1])
        rc_buena = informe(*revisar(BUENA), BUENA)
        rc_nada = informe(*revisar("# Notas\nnada que ver\n"), "# Notas\nnada que ver\n")
        rc_vacia = informe(*revisar("# Bitácora de averías\n"), "# Bitácora de averías\n")
    bien = rc_mala == 1 and rc_buena == 0
    print(("  OK    " if bien else "  FALLA ") + "código de salida: 1 con problemas, 0 sin ellos")
    ok &= bien
    bien = rc_nada == 1 and rc_vacia == 0
    print(("  OK    " if bien else "  FALLA ") + "cero entradas: error si no es una bitácora, OK si es una bitácora vacía")
    ok &= bien
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "b.md")
        open(ruta, "wb").write(b"\xef\xbb\xbf" + BUENA.replace("\n", "\r\n").encode("utf-8"))
        n, problemas = revisar(leer(ruta))
    bien = n == 1 and not problemas
    print(("  OK    " if bien else "  FALLA ") + "fichero con BOM y saltos de línea de Windows")
    ok &= bien
    print("PRUEBA OK" if ok else "PRUEBA FALLA")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--prueba":
        sys.exit(autoprueba())
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    texto = leer(sys.argv[1])
    sys.exit(informe(*revisar(texto), texto))
