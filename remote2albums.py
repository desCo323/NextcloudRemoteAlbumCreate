#!/usr/bin/env python3
"""
remote2albums.py  –  Version 4
Erzeugt Alben in Nextcloud Photos aus Ordnern des Files-Speichers.
Neue Optionen:
  --quiet        => keinerlei Einzelmeldungen
  --verbose      => alle verlinkten Dateien ausgeben
  --album-name   => short (Default) | long
"""

import argparse, urllib.parse, xml.etree.ElementTree as ET
from collections import Counter, deque
from pathlib import PurePosixPath
import requests
import sys

IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp",
           ".heic", ".tif", ".tiff", ".bmp", ".raw"}
NS = {"d": "DAV:"}


# ---------- DAV-Hilfsroutinen ------------------------------------------------
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
    while q:
        cur = q.popleft()
        yield cur
        for href, is_dir in list_children(sess, cur, root_url):
            if is_dir:
                q.append(href)


def mkcol(sess, url):
    r = sess.request("MKCOL", url)
    if r.status_code == 201:
        return True
    if r.status_code == 405:
        return False
    raise RuntimeError(f"MKCOL {url} → {r.status_code}")


def copy(sess, src, dst):
    r = sess.request("COPY", src, headers={"Destination": dst})
    if r.status_code in (201, 204, 409, 403):
        return
    raise RuntimeError(f"COPY {src} → {r.status_code}")


def is_image(href): return PurePosixPath(href).suffix.lower() in IMG_EXT


# ---------- Hauptprogramm ----------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Erzeugt Nextcloud-Alben aus Ordnern")
    ap.add_argument("--url", required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--remote", required=True,
                    help="Pfad relativ zu 'Dateien', z. B. SofortUpload/Pictures")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--quiet", action="store_true",
                   help="Unterdrückt alle Einzelmeldungen")
    g.add_argument("--verbose", action="store_true",
                   help="Zeigt jede verlinkte Datei")
    ap.add_argument("--album-name", choices=["short", "long"], default="short",
                    help="short = letzter Ordnername (Default); "
                         "long = kompletter Pfad mit '--' als Trenner")
    args = ap.parse_args()

    root_url = args.url.rstrip("/")
    files_root = f"{root_url}/remote.php/dav/files/{args.user}/{args.remote.strip('/')}"
    albums_root = f"{root_url}/remote.php/dav/photos/{args.user}/albums"

    sess = requests.Session(); sess.auth = (args.user, args.password)
    stats = Counter()

    def log(msg, force=False):
        if args.quiet and not force:
            return
        if args.verbose or force:
            print(msg)

    for dir_url in walk_dirs(sess, files_root, root_url):
        # Albumnamen bestimmen
        if args.album_name == "short":
            album_name = PurePosixPath(dir_url).name
        else:  # long
            rel_path = PurePosixPath(dir_url).relative_to(files_root)
            album_name = str(rel_path).replace('/', ' - ')

        album_url = f"{albums_root}/{urllib.parse.quote(album_name, safe='')}"
        if mkcol(sess, album_url):
            stats["alben"] += 1
            log(f"[Album] {album_name}", force=not args.quiet)

        for href, is_dir in list_children(sess, dir_url, root_url):
            if is_dir or not is_image(href):
                continue
            dst = f"{album_url}/{urllib.parse.quote(PurePosixPath(href).name)}"
            copy(sess, href, dst)
            stats["bilder"] += 1
            if args.verbose:
                print(f"  ↳ {PurePosixPath(href).name}")

    print(f"✓ {stats['alben']} Alben, {stats['bilder']} Bilder verlinkt.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nAbgebrochen durch Benutzer.")
