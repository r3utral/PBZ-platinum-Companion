# Platinum Companion v1.2 · Catálogo PowerPyx

**Estado de esta entrega:** la aplicación conserva la guía anterior y ya incluye alertas integradas de bugs y perdibles. El catálogo completo **no está precargado** en este ZIP: se genera ejecutando una acción en GitHub una vez subidos los archivos. Si esa acción falla, la app muestra explícitamente que el inventario está incompleto y mantiene las marcas anteriores.

## 1. Antes de actualizar

Abre la app que ya utilizas y pulsa **Exportar JSON**. Guarda ese archivo en tu teléfono. **No subas el respaldo a GitHub**: en un repositorio público sería visible para todo el mundo.

## 2. Actualizar la aplicación del repositorio

En https://github.com/r3utral/PBZ-platinum-Companion, rama `main`, reemplaza `index.html` y `sw.js` con los archivos de este ZIP. Agrega también el archivo `sync_powerpyx.py` a la raíz del repositorio, y crea la ruta `.github/workflows/actualizar-catalogo.yml` con el contenido del archivo homónimo del ZIP. Conserva `manifest.webmanifest`, `.nojekyll` y la carpeta `icons` tal como están.

Para que GitHub Pages siga publicando desde la rama principal, mantén **Settings → Pages → Deploy from a branch → main → /(root)**.

## 3. Generar los coleccionables nuevos

En GitHub → **Actions**, selecciona el workflow **Actualizar inventario PowerPyx** y pulsa **Run workflow** (rama `main`). Ese procedimiento lee los índices públicos regionales y crea un nuevo `catalog.json` con un registro de los coleccionables, las campanas de referencia y enlaces a PowerPyx. No replica sus descripciones completas. Si el sitio bloquea la extracción o cambia su estructura, la acción fallará sin reemplazar el catálogo existente.

Si aparece un error de permiso para guardar los resultados, revisa **Settings → Actions → General → Workflow permissions** y selecciona permisos de lectura/escritura para el token de GitHub Actions; guarda y vuelve a ejecutar la acción.

Cuando termine con éxito, confirma que exista `catalog.json` en la rama `main`. Espera a que GitHub Pages publique el último commit, abre la aplicación y verifica que el aviso de arriba diga **«Catálogo PowerPyx sincronizado»** y muestre el número de pasos indexados.

## 4. Progreso y dispositivos

Cada amigo tiene sus propios estados en el almacenamiento local de su dispositivo; GitHub no aloja ni sincroniza los estados de los usuarios. Actualizar `index.html`, `sw.js` o `catalog.json` no elimina deliberadamente esos estados. Esta app mantiene la misma clave de progreso local de v1.0, así que el progreso existente se recupera si se abre **la misma dirección** de GitHub Pages en el **mismo navegador/perfil**, salvo que se hayan borrado los datos del sitio. Antes de desinstalar o cambiar de navegador, exporta JSON y vuelve a importarlo.

## 5. Alcance y límites

- Mantiene una sola pestaña de ruta con selector de mapas y consejos de jefes del archivo original.
- Los pasos nuevos utilizan nombres e índices públicos y breves referencias de orientación; para un recorrido detallado, abre el enlace del paso a PowerPyx. Las descripciones antiguas ya redactadas en español se conservan.
- Las **alertas de bugs** se distinguen visualmente de las **advertencias perdibles**.
- Es una herramienta no oficial, sin afiliación a PowerPyx ni al desarrollador del juego.
- El catálogo público puede cambiar. Los elementos del mapa «Pangzhen» incluyen parte de «Mansión del Espejismo» en el contador del propio juego, aunque la guía los muestre en mapas separados.
