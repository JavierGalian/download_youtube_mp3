# YouTube MP3

Descarga y convierte a MP3 el audio de videos de YouTube que sean tuyos o que
estés autorizado a descargar. Respeta los derechos de autor y las condiciones
del servicio aplicables.

## Requisitos

- Python 3.10 o posterior.
- FFmpeg y ffprobe disponibles en `PATH`.
- Acceso a Internet.

Instala las dependencias de Python:

```shell
python -m pip install -r requirements.txt
```

En Termux:

```shell
pkg install python ffmpeg
python -m pip install -r requirements.txt
```

Para guardar en almacenamiento compartido de Android, concede acceso una vez
con `termux-setup-storage` y especifica una ruta como
`~/storage/shared/Music`. Las rutas con `~` se expanden automáticamente.

## Uso

Inicio interactivo (solicita la URL en consola):

```shell
python main.py
```

También se puede pegar la URL como argumento, con las opciones habituales:

```shell
python -m youtube_mp3 "https://www.youtube.com/watch?v=VIDEO_ID"
python main.py "URL" --output "~/storage/shared/Music" --retries 3
```

El directorio predeterminado es `~/storage/shared/Music/YouTube MP3` en Termux
(detectado por sus variables de entorno o por la existencia del directorio de
almacenamiento compartido), y `~/Music/YouTube MP3` en Windows y Linux de
escritorio. El programa valida la URL antes de iniciar, requiere que FFmpeg
esté disponible en `PATH`, reintenta errores de red transitorios con espera
exponencial y elimina su espacio de trabajo temporal incluso si la descarga se
cancela o falla. Si ya existe un MP3 con el mismo nombre, se reemplaza.

## Arquitectura

- `cli.py`: argumentos, mensajes y códigos de salida; no contiene lógica de
  descarga.
- `agent.py`: coordina validación, política de reintentos y publicación.
- `media_processor.py`: contrato abstracto `MediaProcessor`, basado en `abc`.
  Se pueden añadir adaptadores para otros servicios sin acoplarlos al agente.
- `youtube_processor.py`: adaptador yt-dlp/FFmpeg y traducción de errores de
  descarga a excepciones de aplicación.
- `file_manager.py`: rutas, directorio temporal aislado y publicación del MP3.

Ejecuta las pruebas con:

```shell
python -m unittest discover -s tests
```
