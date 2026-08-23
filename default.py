# -*- coding: utf-8 -*-
"""TorBox Library - Kodi plugin main entry point.

Lets the user browse and play the content already present in their own
TorBox account, using their own API key (per-user, set in the addon
settings). Optionally uses TMDB for pretty titles/posters.
"""
import sys
import urllib.parse

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from resources.lib import tmdb as tmdb_mod
from resources.lib import library as lib_mod
from resources.lib.torbox_api import TorBoxAPI

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]
ADDON_ID = ADDON.getAddonInfo("id")

TORBOX_KEY = ADDON.getSetting("torbox_api_key")
TORBOX_URL = ADDON.getSetting("torbox_api_url") or "https://api.torbox.app/v1/api"
TMDB_TOKEN = ADDON.getSetting("tmdb_token")
GROUP_SERIES = ADDON.getSetting("group_series") == "true"


def build_url(action, **kwargs):
    qs = urllib.parse.urlencode(kwargs)
    return "%s?action=%s&%s" % (BASE_URL, action, qs)


def log(msg):
    xbmc.log("[CrisPlusTV] %s" % msg, xbmc.LOGDEBUG)


def notify(msg):
    xbmcgui.Dialog().notification("TorBox Library", msg, xbmcgui.NOTIFICATION_WARNING, 4000)


def add_dir(name, url, icon=None, is_folder=True):
    li = xbmcgui.ListItem(label=name)
    if icon:
        li.setArt({"icon": icon, "thumb": icon})
    xbmcplugin.addDirectoryItem(HANDLE, url, li, isFolder=is_folder)


def add_playable(name, url, icon=None, info=None):
    li = xbmcgui.ListItem(label=name, path=url)
    if icon:
        li.setArt({"icon": icon, "thumb": icon})
    li.setProperty("isPlayable", "true")
    if info:
        li.setInfo("video", info)
    xbmcplugin.addDirectoryItem(HANDLE, url, li, isFolder=False)


def get_api():
    if not TORBOX_KEY:
        notify("Configura tu TorBox API Key en los ajustes del addon")
        return None
    return TorBoxAPI(TORBOX_KEY, TORBOX_URL)


def get_tmdb():
    t = tmdb_mod.TMDB(TMDB_TOKEN)
    return t if t.enabled() else None


def main_menu():
    api = get_api()
    if not api:
        xbmcplugin.endOfDirectory(HANDLE)
        return
    add_dir("Series", build_url("series"))
    add_dir("Películas", build_url("movies"))
    add_dir("Todo (sin agrupar)", build_url("all"))
    add_dir("Buscar", build_url("search"))
    xbmcplugin.endOfDirectory(HANDLE)


def _fetch_library():
    api = get_api()
    if not api:
        return None
    try:
        torrents = api.my_torrents()
        return lib_mod.build_library(torrents, group_series=GROUP_SERIES)
    except Exception as e:
        notify("Error leyendo TorBox: %s" % e)
        return None


def list_series():
    lib = _fetch_library()
    if not lib:
        xbmcplugin.endOfDirectory(HANDLE)
        return
    tmd = get_tmdb()
    for key, sdata in lib["series"].items():
        # try to enrich with TMDB
        icon = None
        if tmd:
            meta = tmd.search_tv(sdata["show"])
            if meta:
                icon = tmd.poster_url(meta.get("poster"))
        n = len(sdata["items"])
        label = "%s (%d %s)" % (sdata["show"], n, "archivo" if n == 1 else "archivos")
        add_dir(label, build_url("serie", show=key), icon=icon)
    xbmcplugin.endOfDirectory(HANDLE)


def list_serie(show_key):
    lib = _fetch_library()
    if not lib:
        xbmcplugin.endOfDirectory(HANDLE)
        return
    sdata = lib["series"].get(show_key)
    if not sdata:
        xbmcplugin.endOfDirectory(HANDLE)
        return
    tmd = get_tmdb()
    meta = None
    if tmd:
        meta = tmd.search_tv(sdata["show"])
    for item in sdata["items"]:
        title = item["title"]
        tid = item["torrent"].get("id")
        fid = item["file"].get("id") if item.get("file") else None
        url = build_url("play", tid=tid, fid=fid or "")
        icon = tmd.poster_url(meta.get("poster")) if (tmd and meta) else None
        info = {"title": title}
        if meta and meta.get("overview"):
            info["plot"] = meta["overview"]
        add_playable(title, url, icon=icon, info=info)
    xbmcplugin.endOfDirectory(HANDLE)


def list_movies():
    lib = _fetch_library()
    if not lib:
        xbmcplugin.endOfDirectory(HANDLE)
        return
    tmd = get_tmdb()
    for item in lib["movies"]:
        title = item["title"]
        tid = item["torrent"].get("id")
        fid = item["file"].get("id") if item.get("file") else None
        url = build_url("play", tid=tid, fid=fid or "")
        icon = None
        info = {"title": title}
        if tmd:
            meta = tmd.search_movie(title)
            if meta:
                icon = tmd.poster_url(meta.get("poster"))
                info["plot"] = meta.get("overview")
        add_playable(title, url, icon=icon, info=info)
    xbmcplugin.endOfDirectory(HANDLE)


def list_all():
    lib = _fetch_library()
    if not lib:
        xbmcplugin.endOfDirectory(HANDLE)
        return
    for item in lib["movies"]:
        fid = item["file"].get("id") if item.get("file") else None
        url = build_url("play", tid=item["torrent"].get("id"), fid=fid or "")
        add_playable(item["title"], url)
    for key, sdata in lib["series"].items():
        for it in sdata["items"]:
            fid = it["file"].get("id") if it.get("file") else None
            url = build_url("play", tid=it["torrent"].get("id"), fid=fid or "")
            add_playable(it["title"], url)
    xbmcplugin.endOfDirectory(HANDLE)


def play(tid, fid):
    api = get_api()
    if not api:
        return
    try:
        tid = int(tid)
        fid = int(fid) if fid else None
        url = api.stream_url(tid, fid)
        li = xbmcgui.ListItem(path=url)
        li.setProperty("inputstream", "inputstream.adaptive")
        li.setProperty("inputstream.adaptive.manifest_type", "hls")
        xbmcplugin.setResolvedUrl(HANDLE, True, li)
    except Exception as e:
        log("play error: %s" % e)
        notify("Error al reproducir: %s" % e)
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())


def search():
    kb = xbmc.Keyboard("", "Buscar en TorBox")
    kb.doModal()
    if not kb.isConfirmed() or not kb.getText():
        xbmcplugin.endOfDirectory(HANDLE)
        return
    q = kb.getText().lower()
    lib = _fetch_library()
    if not lib:
        xbmcplugin.endOfDirectory(HANDLE)
        return
    results = []
    for item in lib["movies"]:
        if q in item["title"].lower():
            results.append(item)
    for key, sdata in lib["series"].items():
        if q in sdata["show"].lower():
            results.extend(sdata["items"])
    for item in results:
        fid = item["file"].get("id") if item.get("file") else None
        url = build_url("play", tid=item["torrent"].get("id"), fid=fid or "")
        add_playable(item["title"], url)
    xbmcplugin.endOfDirectory(HANDLE)


def router():
    params = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)
    action = params.get("action", ["main"])[0]

    if action == "main":
        main_menu()
    elif action == "series":
        list_series()
    elif action == "serie":
        list_serie(params.get("show", [""])[0])
    elif action == "movies":
        list_movies()
    elif action == "all":
        list_all()
    elif action == "search":
        search()
    elif action == "play":
        play(params.get("tid", ["0"])[0], params.get("fid", [""])[0])
    else:
        main_menu()


router()
