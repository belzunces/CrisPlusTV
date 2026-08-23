# -*- coding: utf-8 -*-
"""TorBox API client for the Kodi addon.

Only talks to the official TorBox API to list content the user already has
in their own account and to generate playable streams. No torrent searching.
Uses only the Python standard library (urllib) so there are no extra
package dependencies to install on the Kodi device.
"""
import json
import urllib.error
import urllib.parse
import urllib.request


class TorBoxAPI:
    """Minimal client for the TorBox API (v1)."""

    def __init__(self, api_key, api_url="https://api.torbox.app/v1/api"):
        self.api_key = (api_key or "").strip()
        self.api_url = api_url.rstrip("/")

    def _get(self, path, params=None):
        url = "%s%s" % (self.api_url, path)
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
            "Authorization": "Bearer %s" % self.api_key,
            "User-Agent": "CrisPlusTV-Kodi/1.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError("Error HTTP %s de TorBox" % e.code)
        except Exception as e:
            raise RuntimeError("No se pudo conectar con TorBox: %s" % e)
        if not data.get("success"):
            raise RuntimeError(data.get("detail") or data.get("error") or "Error de TorBox")
        return data.get("data")

    def my_torrents(self):
        """Return the full list of torrents in the user's account."""
        return self._get("/torrents/mylist")

    def create_stream(self, torrent_id, file_id=None, torrent_type="torrent"):
        """Initialize a stream for a torrent/file and return its data (hls_url etc)."""
        params = {"id": torrent_id, "type": torrent_type}
        if file_id is not None:
            params["file_id"] = file_id
        return self._get("/stream/createstream", params)

    def stream_url(self, torrent_id, file_id=None, torrent_type="torrent"):
        """Return a playable URL for the given torrent/file."""
        data = self.create_stream(torrent_id, file_id, torrent_type)
        url = data.get("hls_url") or data.get("url")
        if not url:
            raise RuntimeError("TorBox no devolvió una URL de reproducción")
        return url
