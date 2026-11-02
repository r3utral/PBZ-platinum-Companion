# Platinum Companion · PWA lista para publicar

Esta es una guía NO OFICIAL de Phantom Blade Zero, pensada para compartirse como aplicación instalable. **El paquete público no contiene ningún progreso personal.**

## Publicar gratis en GitHub Pages
1. Crea un repositorio público en GitHub (por ejemplo `platinum-companion`).
2. Sube **el contenido de esta carpeta** a la raíz del repositorio (`index.html`, `manifest.webmanifest`, `sw.js`, `icons/`, `.nojekyll`). No subas tu respaldo JSON privado.
3. Ve a **Settings → Pages**. En *Build and deployment*, selecciona *Deploy from a branch*, rama `main`, carpeta `/(root)` y guarda.
4. Abre la dirección HTTPS que mostrará GitHub Pages. Su formato suele ser `https://TU-USUARIO.github.io/platinum-companion/`.
5. En Android, abre ese enlace en Chrome → menú ⋮ → **Instalar aplicación** o **Agregar a pantalla principal**. Comparte el mismo enlace por WhatsApp.

## Recuperar TUS 243 marcas (solo en tu teléfono)
Abre la PWA publicada → **Importar JSON** → selecciona tu archivo privado `Phantom_Blade_Zero_Respaldo_243_marcas_v5.json` (se descarga POR SEPARADO). La URL HTTPS tiene almacenamiento distinto al HTML local, por lo que no hereda el progreso automáticamente. Tus amigos no deben importar tu JSON.

## Actualizar la guía
1. Conserva el mismo repositorio, URL, nombres e ID de cada paso existente.
2. Edita o sustituye `index.html` y publica el cambio. Si modificas contenido que debe funcionar sin conexión, aumenta el valor `CACHE_VERSION` de `sw.js` (por ejemplo `...-v1.0.1`), confirma que los assets se cacheen y publica también `sw.js`.
3. Cuando la app instalada compruebe una nueva versión con conexión, mostrará un aviso para recargar. Puede requerir cerrar y abrir de nuevo.
4. No cambies la constante `DATAKEY` en `index.html` ni los IDs de pasos completados. Las marcas y las notas se guardan en localStorage independientemente del código y del caché de la PWA.
5. Antes de cambios grandes, **Exportar JSON** y conservar el respaldo.

## Limitaciones importantes
- La instalación completa/offline exige servir los archivos por HTTPS (o localhost para desarrollo). Abrir `index.html` directamente no instala una PWA.
- El progreso se guarda en el navegador/dispositivo, no en una cuenta online: no sincroniza teléfonos. Borrar los datos del sitio puede borrar las marcas.
- Este paquete es una primera versión publicable, no un sitio ya desplegado. Solo después de subirlo a un servidor habrá una URL compartible.
- Los mapas cuyos trayectos están pendientes siguen expresamente incompletos; convertirlos en PWA no añade datos de juego nuevos.
- Guia de fans no afiliada a los desarrolladores ni a PowerPyx; las fuentes originales están enlazadas.
