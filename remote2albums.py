#!/usr/bin/env python3
"""
remote2albums.py  –  Version 3
Erzeugt für jeden Unterordner unter <REMOTE_PATH> ein Album
und verlinkt alle Bilddateien dorthin – rein serverseitig.

Aufrufbeispiel:
  ./remote2albums.py --url https://chaosnet.me \
      --user frithjofe --password APPPASS \
      --remote "SofortUpload/Pictures"
"""

import argparse, urllib.parse, xml.etree.ElementTree as ET
from collections import Counter, deque
from pathlib import PurePosixPath
import requests

IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp",
           ".heic", ".tif", ".tiff", ".bmp", ".raw"}
NS = {"d": "DAV:"}


# --------------------------------------------------------------------------- #
# DAV-Hilfsfunktionen                                                         #
# --------------------------------------------------------------------------- #
def propfind(sess, url, depth="1"):
    body = ('<?xml version="1.0"?><d:propfind xmlns:d="DAV:">'
            '<d:prop><d:resourcetype/></d:prop></d:propfind>')
    r = sess.request("PROPFIND", url, data=body, headers={"Depth": depth})
    if r.status_code != 207:
        raise RuntimeError(f"PROPFIND {url} → {r.status_code}")
    return ET.fromstring(r.text)


def list_children(sess, url, root_url):
    base = url.rstrip("/") + "/"
    for rsp in propfind(sess, url, "1").findall("d:response", NS):
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
        return True          # neu
    if r.status_code == 405:
        return False         # existiert
    raise RuntimeError(f"MKCOL {url} → {r.status_code}")


def copy(sess, src, dst):
    """
    Verlinkt eine Datei ins Album.
    - 201 Created   → neuer Link
    - 204 NoContent → identischer Link existiert bereits
    - 409 Conflict  → Datei gleichen Namens schon verlinkt
    """
    r = sess.request("COPY", src, headers={"Destination": dst})
    if r.status_code in (201, 204, 409):
        return
    raise RuntimeError(f"COPY {src} → {r.status_code}")


def is_image(href):
    return PurePosixPath(href).suffix.lower() in IMG_EXT


# --------------------------------------------------------------------------- #
# Hauptprogramm                                                               #
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="Erzeugt Alben aus Ordnern im Nextcloud-Files-Storage.")
    ap.add_argument("--url", required=True, help="Basis-URL, z. B. https://chaosnet.me")
    ap.add_argument("--user", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument("--remote", required=True,
                    help="Pfad unterhalb 'Dateien', z. B. SofortUpload/Pictures")
    args = ap.parse_args()

    root_url   = args.url.rstrip("/")
    files_root = f"{root_url}/remote.php/dav/files/{args.user}/{args.remote.strip('/')}"
    albums_root = f"{root_url}/remote.php/dav/photos/{args.user}/albums"

    sess = requests.Session(); sess.auth = (args.user, args.password)
    stats = Counter()

    for dir_url in walk_dirs(sess, files_root, root_url):
        # 1. relativen Pfad ab files_root ermitteln
        rel_path = PurePosixPath(dir_url).relative_to(files_root)

        # 2. Slashes in einen gut lesbaren Trenner umwandeln
        album = str(rel_path).replace('/', ' - ')   # z. B. "Urlaub2024 -- Tag3"
        #album = PurePosixPath(dir_url).name
        album_url = f"{albums_root}/{urllib.parse.quote(album, safe='')}"
        if mkcol(sess, album_url):
            stats["alben"] += 1

        for href, is_dir in list_children(sess, dir_url, root_url):
            if is_dir or not is_image(href):
                continue
            dst = f"{album_url}/{urllib.parse.quote(PurePosixPath(href).name)}"
            copy(sess, href, dst)
            stats["bilder"] += 1

    print(f"✓ {stats['alben']} Alben erstellt, {stats['bilder']} Bilder verlinkt.")


if __name__ == "__main__":
    main()
