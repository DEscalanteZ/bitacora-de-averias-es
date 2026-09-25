# Bitácora de averías

Este fichero se lee **antes** de diagnosticar y se escribe **antes** de dar una avería por
cerrada. No es un diario: es una lista de trampas conocidas, y cada entrada acaba en un
**candado**, algo que se ejecuta y que impide la repetición. Una lección que solo está
escrita no ha corregido nada.

## Las tres familias

**1 · El éxito falso.** Un proceso termina bien y no ha hecho nada. *Candado genérico:
comprobar qué produjo, nunca que corrió.*

**2 · La pieza fuera de lista.** Algo corre sin estar dado de alta y nadie lo echa de menos
cuando muere. *Candado genérico: censo, y probar que su vigía salta.*

**3 · La conclusión sin control.** Se da por cierto un negativo («no hay datos», «está
roto») sin descartar que el fallo sea propio. *Candado genérico: repetir la prueba sobre un
caso que se sabe bueno.*

## Molde

```
## AAAA-MM-DD · Título corto (familia: …)
**Síntoma.** Lo que se veía.
**Causa real.** Lo que era de verdad, no lo que parecía.
**Cómo se comprobó.** El experimento que lo demostró. Sin esto no vale.
**Candado.** Qué se ha cambiado para que no pueda repetirse, y cómo se probó.
```

---

<!-- Las entradas van debajo, la más reciente arriba. -->
