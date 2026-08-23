# -*- coding: utf-8 -*-
"""Grouping logic: organise the user's TorBox torrents into a browsable
library (series grouped by show/season, and movies).

This only reorganises what the user already has in their own TorBox account.
It never searches for or adds new content.
"""
import re

from . import tmdb as tmdb_mod


def _torrent_files(torrent):
    files = torrent.get("files") or []
    # de-duplicate by file id
    seen = set()
    out = []
    for f in files:
        fid = f.get("id")
        if fid in seen:
            continue
        seen.add(fid)
        out.append(f)
    return out


def _video_files(torrent, skip_samples=True):
    """Return video files, optionally skipping sample/preview files."""
    out = []
    for f in _torrent_files(torrent):
        name = f.get("name", "") or ""
        if not tmdb_mod.is_video_file(name):
            continue
        if skip_samples and re.search(r"sample|preview|trailer", name, re.I) and "sample" in name.lower():
            continue
        out.append(f)
    return out


def _is_hash(name):
    """True if the name is basically a hex hash (torrent whose name is its hash)."""
    stripped = re.sub(r"[0-9a-fA-F]", "", name)
    return len(stripped) <= 3 and len(name) >= 8


def _torrent_display_name(t, vids):
    """Return a human name for the torrent, falling back to first video file name
    when the torrent's own name is just a hash."""
    name = t.get("name", "") or ""
    if not name or _is_hash(name):
        if vids:
            return vids[0].get("name", "")
    return name


def build_library(torrents, group_series=True):
    """Return a dict:
      {"series": {show_name: [torrent_item, ...]},
       "movies": [torrent_item, ...],
       "other":  [torrent_item, ...]}
    torrent_item: {torrent: <raw>, file: <file dict> or None, title: str}
    """
    series = {}
    movies = []
    other = []

    for t in torrents:
        # skip things with no video files if show_hidden is on (handled by caller)
        vids = _video_files(t)
        if not vids:
            other.append({"torrent": t, "file": None, "title": t.get("name", "Sin nombre")})
            continue

        disp_name = _torrent_display_name(t, vids)
        any_ep = any(tmdb_mod._is_episode_name(f.get("name", "")) for f in vids) or tmdb_mod._is_episode_name(disp_name) or tmdb_mod._is_season_range(disp_name)
        has_ep = any_ep

        if group_series and has_ep:
            # Use the clean episode title as the show name (much better than the
            # raw torrent name, which often carries release spam).
            first_ep_title = tmdb_mod.guess_title(vids[0].get("name", "")) if vids else tmdb_mod.guess_title(disp_name)
            show = first_ep_title or tmdb_mod.guess_title(disp_name)
            key = show.lower()
            series.setdefault(key, {"show": show, "items": []})
            # if torrent has multiple episode files, add each as separate item
            for f in vids:
                se, ep = tmdb_mod.guess_season_episode(f.get("name", ""))
                series[key]["items"].append({
                    "torrent": t, "file": f, "title": tmdb_mod.guess_title(f.get("name", "")),
                    "season": se,
                    "episode": ep,
                })
        else:
            # movie or single file
            f = vids[0] if len(vids) == 1 else None
            movies.append({
                "torrent": t, "file": f, "title": tmdb_mod.guess_title(f.get("name", "") if f else disp_name),
            })

    # sort series alphabetically, sort episodes by season/episode
    for key in series:
        series[key]["items"].sort(key=lambda it: (it.get("season") or 0, it.get("episode") or 0))
    series_sorted = {k: series[k] for k in sorted(series)}
    movies.sort(key=lambda it: it["title"].lower())
    return {"series": series_sorted, "movies": movies, "other": other}
