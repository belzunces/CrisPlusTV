# CrisPlus TV

**CrisPlus TV** es un addon para **Kodi** que organiza y reproduce el contenido que ya tienes
descargado en tu cuenta de **TorBox**. Convierte tu biblioteca de TorBox en una navegación
ordenada: series agrupadas por temporada, películas, búsqueda y reproducción en streaming.

> 🔒 **Privacidad**: cada usuario pone **su propia API Key** de TorBox en los ajustes del addon.
> No se comparte ni se incrusta ninguna credencial. Este addon **NO busca ni añade torrents**:
> solo navega y reproduce lo que tú mismo tienes en tu cuenta.

## ✨ Características

- 📺 **Series** agrupadas por título (con número de archivos).
- 🎬 **Películas** listadas alfabéticamente.
- 🔍 **Buscar** dentro de tu biblioteca.
- 🖼️ **Carátulas y sinopsis** opcionales vía **TMDB**.
- ▶️ **Reproducción en streaming** (HLS) generada al instante con la API de TorBox.
- 🔑 Multi-usuario: cada quien usa su propia clave.
- 🪶 **Cero dependencias externas**: solo Python estándar.

## 📦 Instalación

1. Descarga el zip de la release (o clona el repo y comprime la carpeta `plugin.video.crisplus`).
2. En Kodi: **Ajustes → Complementos → Instalar desde zip** → selecciona el archivo.
3. Abre **CrisPlus TV** → **Ajustes**.
4. Pega tu **API Key de TorBox** (obligatorio):
   - Ve a <https://torbox.app> → Ajustes de cuenta → **API Keys** → crea una.
5. *(Opcional)* Pega tu **TMDB Read Access Token** para carátulas y sinopsis.
6. Guarda y abre el addon. ¡Tu biblioteca organizada y lista para reproducir!

## 🗂️ Estructura

```
plugin.video.crisplus/
├── addon.xml              # Manifiesto del addon
├── default.py             # Router principal de Kodi (menús, búsqueda, reproducción)
├── icon.png / fanart.jpg  # Iconos del addon
└── resources/
    ├── settings.xml       # Ajustes (API key TorBox, token TMDB, agrupar series)
    └── lib/
        ├── torbox_api.py  # Cliente de la API de TorBox (listar + crear stream)
        ├── library.py     # Lógica de agrupación (series/películas)
        └── tmdb.py        # Cliente opcional de TMDB (carátulas/sinopsis)
```

## 🛠️ Desarrollo

- **Sin dependencias**: usa `urllib`/`json` de la librería estándar de Python 3.
- **API de TorBox**: `GET /torrents/mylist` (listar) y `GET /stream/createstream` (URL HLS).
- **Reproducción**: se resuelve con `inputstream.adaptive` (manifest tipo `hls`).

## ⚖️ Aviso

**CrisPlus TV** no realiza ninguna búsqueda ni descarga de contenido. Es una herramienta de
organización y reproducción de lo que el usuario ya tiene en su propia cuenta de TorBox.
