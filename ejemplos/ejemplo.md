# Ejemplo de entrada completa

Basado en una avería real, contada sin nombres de personas ni de proveedores.

---

## 2026-08-30 · El vigía llevaba tres semanas avisando por un canal que ya no entregaba nada (familia: el éxito falso)
**Síntoma.** Ninguno, y ese es el problema. El vigía del ordenador escribía «aviso enviado» en
su registro todos los días, y a la persona no le llegaba nada. Se descubrió de rebote: al
probar otro aviso, dijo «no me ha llegado nada», cuando el código decía que sí.
**Causa real.** Dos capas.
1. El script daba por bueno un aviso con solo ver un `HTTP 200`. El servicio de mensajes
   responde `200` **también cuando no envía**: el motivo (cupo agotado, mensaje no enviado)
   viene en el cuerpo de la respuesta, que nadie leía.
2. Y lo de fondo: **esto ya se había arreglado en otro sitio.** El cupo del servicio se agotó
   el 4 de agosto y el 8 el vigía principal se pasó a otro canal. Este vigía, el del
   ordenador, se quedó apuntando al canal viejo. Cuando se muda un canal, el que se queda
   atrás no se rompe con estrépito: se queda mudo. Y un vigía mudo parece uno tranquilo.
**Cómo se comprobó.**
1. Llamada real al servicio imprimiendo el **cuerpo** de la respuesta, no solo el código:
   «mensaje no enviado» con `HTTP 200`.
2. La fecha del cambio de canal no es una estimación: está escrita en el código del vigía
   principal, que hizo el cambio.
3. Tras el arreglo, la función de aviso devuelve `False` donde antes devolvía `True`.
**Candado.**
1. El script mira **qué produjo** la llamada: si el cuerpo dice que no se envió, devuelve
   `False` y reenvía el aviso entero por el canal de respaldo.
2. El vigía del ordenador sale por el mismo canal que el principal.
3. Si tampoco puede avisar, lo escribe en su registro en rojo con el mensaje que no pudo
   mandar. Antes se tragaba el error redirigiéndolo a `/dev/null`.
Probado el mismo día de punta a punta: la persona confirmó, con una captura de su pantalla, que los
avisos le llegaban por los dos caminos. No por el código de estado: por lo que vio en su teléfono.
**Lección.** Cuando se cambia un canal de aviso, no basta con cambiarlo donde se detectó el
problema: hay que buscar **todos** los que llamaban al canal viejo. (No se hizo a la primera: ese
mismo día aparecieron otros dos vigías con el mismo código copiado, igual de mudos. De ahí salió otra
regla: un vigía no se da por terminado hasta que la persona confirma que le ha llegado un mensaje suyo.)
