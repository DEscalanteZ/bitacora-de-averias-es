# Bitácora de averías: las tres formas en que fallan las automatizaciones con IA

> 🇬🇧 **[English version → README.en.md](README.en.md)**

> **In English, in one paragraph:** a failure log for teams running AI agents and automations in production. 130 logged entries in seven weeks, and almost all of the ones we labelled fall into three families: **the false success** (it finished "OK" and did nothing), **the unlisted piece** (it ran without being registered, so nobody noticed when it died) and **the unchecked conclusion** ("there's no data", "it's broken", without ruling out that the fault was mine). The rule that makes it work: **an incident isn't closed until it has a "lock"**, something that runs and prevents it from happening again. A lesson that's only written down hasn't fixed anything. Includes the template, a checker script and the instructions to wire it into Claude Code.

Llevamos un registro de cada avería de nuestras automatizaciones con agentes de IA: vigías, robots que descargan datos, paneles, agentes de voz y partes diarios, repartidos en varios servidores y tres empresas. En siete semanas (del 8 de agosto al 25 de septiembre de 2026) se apuntaron **130 entradas** (alguna agrupa varias averías, y varias se cazaron antes de llegar a producción).

Casi todas las que llevan familia eran **una de estas tres**, con otra cara.

---

## Las tres familias

110 de las 130 entradas dicen su familia (las de las primeras semanas no la llevaban). De esas 110, **106 son una de estas tres**; las otras 4 se apuntaron como familia nueva. Algunas caen en dos familias:

| Familia | Qué es | Veces |
|---|---|---|
| **1 · El éxito falso** | Un proceso termina «bien» y no ha hecho nada | **46** |
| **2 · La pieza fuera de lista** | Algo corre sin estar dado de alta, y nadie lo echa de menos cuando muere | **32** |
| **3 · La conclusión sin control** | Doy por cierto un negativo («no hay datos», «está roto») sin descartar que el fallo sea mío | **49** |

### 1 · El éxito falso

Devuelve `OK`, sale con código 0, publica ficheros viejos, o escribe un dato fresco y hueco. Es el más peligroso porque **se parece a que todo va bien**.

- **Tres meses sin descargar ni una factura, diciendo que todo iba bien.** Un robot terminaba cada lunes con «0 facturas nuevas» y código 0. Una variable local se llamaba igual que una función: cada correo con factura reventaba, un `except` se tragaba el error y el robot seguía. Al arreglarlo aparecieron 126 facturas.
- **Un vigía llevaba tres semanas avisando por un canal que ya no entregaba nada.** El servicio de mensajes contestaba `200 OK` también cuando **no** enviaba; el motivo venía escrito en el cuerpo de la respuesta, que nadie leía. El registro decía «aviso enviado» todos los días.
- **Un mantenimiento semanal llevaba 17 días muriendo después de escribir «terminado».**
- **Un panel enseñaba datos de hace dos meses como si fueran de hoy.** El proceso que lanzaba los cálculos no miraba si habían salido bien, así que el panel servía el último resultado que hubiera.
- **Una herramienta del agente de voz devolvió `200` seis veces sin dar ni un dato.** Se descubrió por el **tamaño** de la respuesta (266 bytes cuando lo normal eran más de 3.000), no por el código. Encima, una instrucción de «si falla, sigue sin mencionarlo» tapaba el fallo.

**Candado general:** comprobar **qué produjo**, nunca **que corrió**. Un `OK`, un código 0 o un fichero con fecha de hoy no demuestran nada: pueden venir vacíos.

### 2 · La pieza fuera de lista

Algo que funciona, pero que no está en ninguna lista de cosas vigiladas. Cuando muere no hace ruido: se queda callado, y un vigía callado parece uno tranquilo.

- **Tras mudar los procesos a un servidor, un fichero de catálogo no se copió.** El código lo abría dentro de un `try/except` silencioso. Durante ocho semanas, una de las cifras del parte diario salió entre un 26 % y un 46 % más baja de lo real. Nadie lo vio.
- **Un conector hecho «para ver» en el portátil acabó alimentando una previsión.** No tenía refresco ni vigía, y el dato llevaba dos meses y medio parado.
- **El teléfono de un agente de voz dejó de contestar.** El saldo del proveedor había llegado a negativo, y nadie lo miraba.

**Candado general:** un **censo**. Cualquier robot, vigía o servicio se da de alta **el mismo día** que se crea, y el alta se cierra probando que la comprobación salta: se esconde su fichero y se mira si el vigía se queja. Una comprobación que nunca ha fallado en pruebas no vale nada.

### 3 · La conclusión sin control

La más humana. Afirmar un negativo porque encaja con lo que se esperaba.

- **Di por perdidos 35 ficheros, y estaban todos en la nube.** La búsqueda usaba un comando que no existe en esa máquina: falló sin decir nada, y su silencio lo leí como «no hay nada».
- **Estuve a punto de decir que llevábamos ocho días sin tráfico.** El error `500` venía de **mi** petición, no del proveedor. El control lo demostró: un rango de días que **sí** tenía datos también daba `500`.
- **Un ordenador se reinició solo y culpé al disco lleno.** Encajaba con todo, pero era falso. Un revisor en frío lo tumbó: la batería llegó al 1 %, el sistema intentó hibernar y la copia de la memoria no cabía en su fichero, que tenía un tamaño fijo.
- **Una frase en un cálculo decía «casi con seguridad, también X».** Nadie la comprobó, y la previsión de cierre del año salía un 20 % inflada.

**Candado general:** antes de afirmar un negativo, **repetir la prueba sobre un caso que sé que funciona**. Si el control también falla, el roto soy yo.

### Y una que duele más que las demás

> **Un script de diagnóstico que escribe no es un diagnóstico.**

Relancé un script «para ver qué pasaba». Bajó una descarga a medias y la **escribió encima** de dos meses de datos buenos. No había copia en ninguna parte. Desde entonces, antes de relanzar algo que toque ficheros, se mira si sobrescribe. Si sobrescribe, se copia antes.

---

## El candado: por qué una lección escrita no basta

Algunas de estas averías volvieron a pasar **teniendo la lección escrita**. Una regla escrita nueve días antes no impidió olvidar lo mismo otra vez. Un arreglo hecho en un servidor no llegó a su copia gemela en el otro. La lección estaba; lo que faltaba era algo que obligara a cumplirla.

Por eso la regla de la bitácora es:

> **Una avería no está cerrada hasta que tiene candado: algo que se ejecuta y que impide que se repita.**

Un candado es, por ejemplo:

| Tipo de candado | Ejemplo real |
|---|---|
| El proceso se **niega** a hacer lo peligroso | No sustituye un mes de datos por una descarga con menos del 90 % de las filas que ya había: se niega, lo dice y sale con código 2 |
| El proceso se **para** en vez de seguir en silencio | Si el catálogo carga vacío, el cálculo se detiene con un mensaje claro, en vez de dar una cifra corta |
| Un **vigía** que mira el resultado, no la ejecución | Mira la fecha de los **datos**, no la hora a la que corrió el proceso |
| Una **prueba** que se lanza sola | El script trae un modo `--prueba` con un caso bueno y uno malo, y solo sale bien si distingue los dos |
| Un **aviso** en el sitio exacto donde se va a cometer el error | Cuando una ruta rota apunta a la carpeta de Descargas, el aviso añade «antes de darlo por perdido, mira la copia en la nube» |

**No cuenta como candado:** una nota en un documento, una regla en la memoria del agente o un «a partir de ahora tendré cuidado».

---

## El molde

Cada avería se escribe así. Sin el apartado de **candado**, la entrada no está terminada:

```markdown
## 2026-09-25 · Título corto que diga qué pasó (familia: el éxito falso)
**Síntoma.** Lo que se veía.
**Causa real.** Lo que era de verdad, no lo que parecía.
**Cómo se comprobó.** El experimento que lo demostró. Sin esto no vale.
**Candado.** Qué se ha cambiado para que no pueda repetirse, y cómo se probó que funciona.
```

Tienes una bitácora vacía lista para copiar en [`plantilla/BITACORA.md`](plantilla/BITACORA.md), y un ejemplo completo en [`ejemplos/ejemplo.md`](ejemplos/ejemplo.md).

---

## Cómo se conecta con Claude Code (o con cualquier agente)

La bitácora solo funciona si el agente **la lee antes** y **la escribe después**. Pega esto en tu `CLAUDE.md`:

```markdown
## Bitácora de averías (obligatoria)

Fichero: `BITACORA.md`

**Antes de diagnosticar cualquier avería:** buscar el síntoma en la bitácora. Casi todo fallo
nuevo es una de las tres familias (éxito falso, pieza fuera de lista, conclusión sin control)
con otra cara, y el candado casi seguro ya existe en otra entrada.

**Antes de dar una avería por cerrada:** escribir su entrada con el molde. No está terminada
hasta que tiene candado: algo que se ejecuta y que impide la repetición.

Tres reglas que se aplican siempre, sin que nadie las pida:
1. Comprobar qué produjo, nunca que corrió.
2. Antes de afirmar un negativo, repetir la prueba sobre un caso que sé bueno.
3. Antes de relanzar algo que toque ficheros, mirar si sobrescribe. Si sobrescribe, copiar antes.
```

Y para que nadie cierre una entrada sin candado, [`herramientas/revisar_bitacora.py`](herramientas/revisar_bitacora.py) revisa cada entrada (todo título con fecha, y también los que llevan los rótulos del molde aunque no tengan fecha) y sale con error si alguna no tiene sus cuatro apartados, tiene el candado vacío o de relleno («pendiente», «TODO») o no dice su familia (en el título o en una línea «Familia:»):

```bash
python3 herramientas/revisar_bitacora.py plantilla/BITACORA.md   # o la ruta de tu bitácora
python3 herramientas/revisar_bitacora.py --prueba   # comprueba que el propio revisor distingue una entrada buena de una mala
```

Sale con código 1 si algo falla, así que sirve tal cual en la integración continua o en un *pre-commit* de git: la entrada a medias no entra en el repositorio. Los títulos que no son entradas (secciones como «Cómo se usa») no se revisan, pero se listan al final para que se vea qué se ha quedado fuera.

---

## Lo que hemos aprendido de llevarla

1. **Se lee antes, no después.** Buscar el síntoma es rápido. Rediagnosticar desde cero, no.
2. **La familia importa más que el detalle.** Si una avería nueva es un «éxito falso», el candado casi siempre es el mismo: mirar el resultado, no la ejecución.
3. **El arreglo tiene que llegar a las copias gemelas.** Más de una avería volvió a pasar porque el arreglo se hizo en un sitio y no llegó a su copia gemela.
4. **Un revisor en frío caza las conclusiones sin control.** Otro agente, con el contexto limpio y el encargo de tumbar el diagnóstico, encontró varias de las de la familia 3. Ver [refutadores en frío](https://github.com/DEscalanteZ/ai-agent-patterns-es/blob/main/refutadores-en-frio.md).
5. **Un molde que nadie revisa se deforma solo.** Al pasar el revisor por nuestra propia bitácora, 101 de sus 130 entradas no seguían el molde al pie de la letra (91 sin contar la familia, que nuestro molde no exigía): rótulos con otro nombre («Qué pasó»), el candado en un apartado propio en vez de en su rótulo. El contenido estaba, pero cada vez costaba más buscar en ella. Por eso existe el revisor.
6. **La honestidad de la entrada es lo que la hace útil.** «Mi primer diagnóstico era falso» enseña más que un diagnóstico limpio.

---

## Relacionado

- **[Seis patrones para trabajar con agentes de IA](https://github.com/DEscalanteZ/ai-agent-patterns-es)**: la guía de la que sale este trabajo.
- **[Comunicación entre dos Claude Code en ordenadores diferentes](https://github.com/DEscalanteZ/claude-code-buzon-es)**: el canal entre dos agentes, con sus candados.

---

⭐ **Si esto te sirve, dale una estrella al repositorio**: es la forma más sencilla de que le llegue a más gente que trabaja con agentes en español.

*Autor: David Escalante ([@DEscalanteZ](https://github.com/DEscalanteZ)). Textos bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es): puedes copiarlos y adaptarlos citando la fuente. El código de `herramientas/` es [MIT](herramientas/LICENSE).*
