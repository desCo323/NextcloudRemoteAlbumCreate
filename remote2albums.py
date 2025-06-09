#!/usr/bin/env python3
"""
remote2albums.py  –  Version 6
• legt Alben aus Ordnern an
• verlinkt Bilder *und Videos* (.mp4, .mov, .webm …)
• Logger: quiet | default | verbose
• Albumnamen: short | long
"""

import argparse, urllib.parse, xml.etree.ElementTree as ET
from collections import Counter, deque
from pathlib import PurePosixPath
import requests, sys

MEDIA_EXT = {  # Bilder + Videos
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".tif", ".tiff", ".bmp", ".raw",
    ".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".mpeg", ".mpg"
}
NS = {"d": "DAV:"}


# ---------- DAV-Hilfen -------------------------------------------------------
def propfind(sess, url, depth="1"):
    body = ('<?xml version="1.0"?><d:propfind xmlns:d="DAV:">'
            '<d:prop><d:resourcetype/></d:prop></d:propfind>')
    r = sess.request("PROPFIND", url, data=body, headers={"Depth": depth})
    if r.status_code != 207:
        raise RuntimeError(f"PROPFIND {url} → {r.status_code}")
    return ET.fromstring(r.text)


def list_children(sess, url, root_url):
    base = url.rstrip("/") + "/"
    for rsp in propfind(sess, url).findall("d:response", NS):
        href = urllib.parse.unquote(rsp.find("d:href", NS).text)
        if href == base:
            continue
        if not href.startswith("http"):
            href = root_url + href
        is_dir = rsp.find(".//d:collection", NS) is not None
        yield href, is_dir


def walk_dirs(sess, root_dir, root_url):
    q = deque([root_dir])
    visited = {root_dir}
    while q:
        cur = q.popleft()
        yield cur
        for href, is_dir in list_children(sess, cur, root_url):
            if is_dir and href not in visited:
                visited.add(href)
                q.append(href)


def mkcol(sess, url):
    r = sess.request("MKCOL", url)
    if r.status_code == 201:
        return True      # neu
    if r.status_code == 405:
        return False     # existiert
    raise RuntimeError(f"MKCOL {url} → {r.status_code}")


def copy(sess, src, dst):
    r = sess.request("COPY", src, headers={"Destination": dst})
    return r.status_code


def is_media(href):
    return PurePosixPath(href).suffix.lower() in MEDIA_EXT


# ---------- Hauptprogramm ----------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--remote", required=True,
                    help="Pfad unterhalb 'Dateien', z. B. SofortUpload/Pictures")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--quiet", action="store_true")
    g.add_argument("--verbose", action="store_true")
    ap.add_argument("--album-name", choices=["short", "long"], default="short")
    args = ap.parse_args()

    root_url   = args.url.rstrip("/")
    files_root = f"{root_url}/remote.php/dav/files/{args.user}/{args.remote.strip('/')}"
    albums_root = f"{root_url}/remote.php/dav/photos/{args.user}/albums"

    sess = requests.Session(); sess.auth = (args.user, args.password)
    stats = Counter()

    def log(msg, always=False):
        if args.quiet and not always:
            return
        if args.verbose or always:
            print(msg)

    for dir_url in walk_dirs(sess, files_root, root_url):
        # Albumnamen ermitteln
        if args.album_name == "short":
            album_name = PurePosixPath(dir_url).name
        else:
            rel = PurePosixPath(dir_url).relative_to(files_root)
            album_name = str(rel).replace('/', ' -- ')

        album_url = f"{albums_root}/{urllib.parse.quote(album_name, safe='')}"
        new_album = mkcol(sess, album_url)
        if new_album:
            stats["alben"] += 1
        log(f"[Album {'neu' if new_album else 'ok '}] {album_name}",
            always=not args.quiet)

        # Jede Datei im Ordner prüfen
        for href, is_dir in list_children(sess, dir_url, root_url):
            if is_dir or not is_media(href):
                continue
            fname = PurePosixPath(href).name
            dst = f"{album_url}/{urllib.parse.quote(fname)}"
            code = copy(sess, href, dst)

            if code == 201:
                stats["verlinkt"] += 1
                log(f"  ✔ 201  verlinkt  {fname}")
            elif code in (204, 409, 403):
                reason = {204: "identisch", 409: "Name existiert", 403: "link existiert"}[code]
                log(f"  • {code}  skip ({reason}) {fname}")
            else:
                log(f"  ✖ {code}  Fehler  {fname}")
                raise RuntimeError(f"COPY {href} → {code}")

    print(f"\n✓ {stats['alben']} Alben neu, {stats['verlinkt']} Medien verlinkt.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nAbgebrochen durch Benutzer.")
