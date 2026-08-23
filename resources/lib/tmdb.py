# -*- coding: utf-8 -*-
"""TMDB metadata helper (optional). Used only to fetch pretty titles,
posters and synopses for items the user already has in TorBox.
Uses only the standard library (urllib).
"""
import json
import re
import urllib.parse
import urllib.request

VIDEO_EXTS = (".mkv", ".mp4", ".avi", ".mov", ".m4v", ".wmv", ".flv", ".webm", ".ts", ".mpg", ".mpeg", ".vob")

# Direct, backtracking-safe patterns.
# Episode marker like S01E01 (standard and most common).
EP_MARKER_RE = re.compile(r"[Ss](\d{1,2})\s*[Ee](\d{1,3})")
# Season range like S01-S08 / S01 - S08 / S01E01-S08E10
SEASON_RANGE_RE = re.compile(r"[Ss](\d{1,2})\s*[-\u2013]\s*[Ss]?(\d{1,2})")

# Tokens de release que conviene recortar del título (source, resolución, codec, grupos...)
RELEASE_TOKENS = (
    "2160p", "1080p", "720p", "480p", "4K", "UHD", "HDR10", "HDR", "DV", "10bit",
    "BluRay", "WEBRip", "WEB-DL", "WEB DL", "WEB", "BRRip", "x265", "x264", "H265",
    "H264", "HEVC", "AAC", "AC3", "EAC3", "DTS", "DD5.1", "5.1", "7.1", "Atmos",
    "TrueHD", "MULTi", "VFF", "VFI", "ESP", "LAT", "ENG", "MULTI", "QTZ",
    "CameEsp", "Scarlet", "Bitsearch", "Hybrid", "Remux", "HDTV", "COMPLETE",
    "10BIT", "iNTERNAL", "PHOCiS", "AMZN", "NF", "DDP5", "Part2",
)


def is_video_file(name):
    return name.lower().endswith(VIDEO_EXTS)


def guess_season_episode(filename):
    """Return (season, episode) ints if the basename looks like a series episode."""
    base = filename.replace("\\", "/").rsplit("/", 1)[-1]
    m = EP_MARKER_RE.search(base)
    if m:
        try:
            return int(m.group(1)), int(m.group(2))
        except (ValueError, IndexError):
            return None, None
    return None, None


def _is_episode_name(name):
    return bool(EP_MARKER_RE.search(name))


def _is_season_range(name):
    return bool(SEASON_RANGE_RE.search(name))


def _strip_release_tokens(name):
    """Remove noisy release tokens from a title guess."""
    name = re.sub(r"\[[^\]]*\]", " ", name)
    name = re.sub(r"[0-9a-fA-F]{8,}", " ", name)
    for tok in RELEASE_TOKENS:
        name = re.sub(r"(^|[.\-_ ])" + re.escape(tok) + r"([.\-_ ]|$)", r"\1 \2", name, flags=re.I)
    return name


def _title_before_marker(name):
    """Return the substring before the first episode/season-range/season marker,
    so we get a clean show name like "Game of Thrones" from
    "Game of Thrones (2011) S01 - S08 COMPLETE ..."."""
    # 1) episode marker
    m = EP_MARKER_RE.search(name)
    # 2) season range (S01 - S08)
    m2 = SEASON_RANGE_RE.search(name)
    cut = None
    if m and m2:
        cut = min(m.start(), m2.start())
    elif m:
        cut = m.start()
    elif m2:
        cut = m2.start()
    if cut is not None:
        name = name[:cut]
    # 3) year marker (2021, (2011), [2025])
    m3 = re.search(r"[.\-_ ]*[\[\(]?(19|20)\d{2}[\]\)]?", name)
    if m3:
        name = name[:m3.start()]
    return name


def _clean_name(name):
    name = _strip_release_tokens(name)
    name = re.sub(r"[._\-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"^www\s*\S+\s*org\s*", "", name, flags=re.I)
    return name.strip()


def guess_title(filename):
    """Return a cleaned, human-friendly title guess from a filename (or path)."""
    base = filename.replace("\\", "/").rsplit("/", 1)[-1]
    name = _title_before_marker(base)
    # if nothing meaningful extracted, fall back to full basename without ext
    if len(name.strip()) < 2:
        name = base.rsplit(".", 1)[0] if "." in base else base
    return _clean_name(name)


class TMDB:
    """Optional TMDB client to enrich items with poster + overview."""

    def __init__(self, token):
        self.token = (token or "").strip()
        self.base = "https://api.themoviedb.org/3"

    def enabled(self):
        return bool(self.token)

    def _get(self, path, params=None):
        if not self.token:
            return None
        url = self.base + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={
            "Authorization": "Bearer %s" % self.token,
            "User-Agent": "CrisPlusTV-Kodi/1.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def search_movie(self, title, year=None):
        params = {"query": title, "language": "es-ES"}
        if year:
            params["year"] = year
        data = self._get("/search/movie", params)
        if data and data.get("results"):
            r = data["results"][0]
            return {
                "title": r.get("title") or r.get("name"),
                "overview": r.get("overview"),
                "poster": r.get("poster_path"),
                "year": (r.get("release_date") or "")[:4],
            }
        return None

    def search_tv(self, title):
        data = self._get("/search/tv", {"query": title, "language": "es-ES"})
        if data and data.get("results"):
            r = data["results"][0]
            return {
                "title": r.get("name") or r.get("title"),
                "overview": r.get("overview"),
                "poster": r.get("poster_path"),
                "year": (r.get("first_air_date") or "")[:4],
            }
        return None

    def poster_url(self, path, size="w500"):
        if not path:
            return None
        return "https://image.tmdb.org/t/p/%s%s" % (size, path)
