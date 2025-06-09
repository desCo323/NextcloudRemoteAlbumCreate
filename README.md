# remote2albums.py  
**Nextcloud Album Auto-Creator**

*Automatisiert das Anlegen von Alben in der Nextcloud-Photos-App aus bereits vorhandenen Ordnern – ideal für Umsteiger von anderen Systemen*

# remote2albums.py  
**_“Wenn 100 Ordner plötzlich keine Alben sind – macht sie remote2albums.py in Minuten sichtbar.”_**

---

## 0 · Kurzfassung

> **Problem:** Nach der Migration zu Nextcloud liegen Tausende Fotos bereits im Cloud-Speicher, erscheinen aber in der **Photos-App nicht als Alben**.  
> **Lösung:** **remote2albums.py** durchsucht diese Ordner direkt auf dem Server, baut aus jedem Unterordner ein echtes Nextcloud-Album und **verlinkt** die Bilder – ohne Upload, ohne Duplikate, ohne Risiko.

---

## 1 · Das typische Schmerz-Szenario

| Migrationsquelle | Ordnerstruktur nach dem Import | Ergebnis in Nextcloud Photos |
|------------------|--------------------------------|------------------------------|
| **AlterHoster** | ` Photos/2023-05-19/IMG_...` | _keine Alben_ |
| **AusUploads** | `SofortUpload/2024/06/01/` | _keine Alben_ |
| ** Photo ** (manueller Export) | `Cloud/2022-09-Urlaub/Tag3/` | _keine Alben_ |
| **NAS / DigiCam** | `Fotos/USA/NY/TimesSquare/` | _keine Alben_ |

*Nextcloud Photos* erkennt nur Ordner, die über die Web-GUI als Album registriert wurden.  
> **Händisch 200 Ordner anklicken?** Unrealistisch.  
> **Alles neu hochladen?** Zeit‐ und Speicherfresser.
>
> Nach dem Script:
> Das Script erstellt aus dem Pfad Albennamen

---

## 2 · Was remote2albums.py konkret tut

1. **Rekursiv scannen**  
   Über WebDAV `PROPFIND` liest es alle Unterordner eines frei wählbaren Pfads.

2. **Album erzeugen** (`MKCOL`)  
   Jeder Ordner wird in `/remote.php/dav/photos/<user>/albums/` als echtes Album angelegt.

3. **Bilder verlinken** (`COPY`)  
   Statt Dateien zu kopieren wird nur ein **WebDAV-Link** gesetzt.  
   *⟶ Kein zusätzlicher Speicher, kein erneuter Upload.*

4. **Idempotent laufen**  
   Läuft das Skript erneut, ignoriert es vorhandene Alben (`405`) und Links (`204/409`).  
   *⟶ Sicheres Batch-Tool, auch als Cron-Job.*

5. **Nur Bilder**  
   Standardmäßig `.jpg / .png / .webp / …` (Liste erweiterbar).

---

## 3 · Warum es so hilfreich ist

| Mehrwert | Erklärung |
|----------|-----------|
| **Spart Zeit** | Wandelt Hunderte–Tausende Ordner in  Minuten in Alben um. |
| **Kein Daten-Wanderspeicher** | Bilder bleiben _wo sie sind_; nur Links werden erzeugt. |
| **Zero-Client** | Läuft auf dem Server oder per SSH – kein Desktop-Sync nötig. |
| **Migrations-Booster** | Ideal nach Umzügen um aus den Ordnern in Nectcloud Alben zu machen. |
| **Wiederholbar & sicher** | Erneuter Lauf ergänzt nur Neues, nichts wird gelöscht oder überschrieben. |
| **Einfach automatisierbar** | Als Cron-Job einsetzbar ➜ neue Upload-Ordner werden regelmäßig zu Alben. |

---

## 4 · Funktionsübersicht (Technik)

| HTTP-Verb | Endpunkt | Zweck |
|-----------|----------|-------|
| `PROPFIND` | `/dav/files/<user>/<REMOTE_PATH>` | Ordner‐ und Dateiliste abfragen |
| `MKCOL`   | `/dav/photos/<user>/albums/<AlbumName>` | Album anlegen (oder 405, falls schon da) |
| `COPY`    | `<file>` → `<album>/<filename>` | Datei **verlinken** (201 neu, 204/409 schon vorhanden) |

Alle Operationen benutzen Standard-WebDAV; keine internen Nextcloud-Hacks.

---

---

## ✨ Lösung

**remote2albums.py** …

1. durchläuft rekursiv **alle Unterordner** eines angegebenen Startpfads  
2. legt für jeden Ordner ein Album an (`MKCOL`)  
3. verlinkt alle Bilddateien ohne Kopieren oder Duplizieren (`COPY`)  
4. ist **idempotent** – kann gefahrlos wiederholt werden  
5. arbeitet **rein serverseitig** über WebDAV (keine lokalen Dateien nötig)

---

## ⚙️ Voraussetzungen

| Komponente | Version |
| ---------- | ------- |
| Nextcloud | **≥ 27** (Photos ≥ 2.0, Album-DAV-API) |
| Python | **≥ 3.8** |
| Python-Paket | `requests` (`pip install --user requests`) |
| Zugriff | App-Passwort oder Login mit *Files*- und *Photos*-Rechten |

---

## 🚀 Installation

```bash
# Systempakete (Debian/Ubuntu)
sudo apt install python3 python3-pip

# Abhängigkeit
pip3 install --user requests

# Skript holen
git clone https://github.com/<your-org>/remote2albums.git
cd remote2albums
chmod +x remote2albums.py
```

---

## 📝 Konfiguration

1. **App-Passwort erzeugen**  
   Profil → Sicherheit → *Neues App-Passwort*  
   Benutzer- & Passwort-Token notieren.

2. **Startordner festlegen**  
   Beispiele  
   Suche den Startordner ab dem du die alben erstellen willst:
   Beispiel:
   /Photos/Urlaube
                  /Urlaub2012
                  /Urlaub2013
   Ergebniss: Alben: Urlaub2012 Urlaub2013

---

## ▶️ Benutzung
Albumnamen + ausführlicher Ausgabe:
Zweck	Albumnamen	Konsolen-Meldungen	Beispielaufruf
Standardmodus	kurz	Albumzeile + Abschlussstatistik	./remote2albums.py --url https://CLOUD --user USER --password PASS --remote "SofortUpload/Pictures"
Vollständig lautlos	kurz	nur Schlusszeile	… --quiet
Ausführlich (jede Datei)	kurz	jede Datei	… --verbose
Langer Albumnamen	ganzer Pfad	Albumzeile + Schluss	… --album-name long
Lang + ausführlich	ganzer Pfad	jede Datei	… --album-name long --verbose
Lang + völlig lautlos	ganzer Pfad	nur Schluss	… --album-name long --quiet

Hinweis: --quiet und --verbose schließen sich gegenseitig aus – gib immer nur einen der beiden Schalter an.
```bash
./remote2albums.py \
  --url     https://cloud.example.com \
  --user    alice \
  --password "APP-PASSWORT" \
  --remote  "Photos/"

./remote2albums.py \
  --url https://meinecloud.com \
  --user appusername \
  --password 3234-2342342342-34wjo \
  --remote "SofortUpload/Pictures" \
  --album-name long \
  --verbose
```

| Parameter | Bedeutung |
|-----------|-----------|
| `--url` | Basis-URL deiner Cloud (ohne Slash am Ende) |
| `--user` | Nextcloud-Benutzername |
| `--password` | App-Passwort |
| `--remote` | Ordner relativ zum **Dateien**-Root, dessen Unterordner zu Alben werden |

**Beispielausgabe**

```
✓ 42 Alben erstellt, 8 314 Bilder verlinkt.
```

Anschließend **Photos öffnen → F5**: Die Alben erscheinen sofort.

---

## ⏰ Automatisierung (Cron-Job)

```cron
# /etc/cron.d/remote2albums  –  alle 6 Stunden neue Ordner verlinken
0 */6 * * *  alice  /usr/bin/python3 /opt/remote2albums/remote2albums.py \
  --url https://cloud.example.com \
  --user alice \
  --password "$NC_APP_PASS" \
  --remote "SofortUpload/Pictures" \
  >> /var/log/remote2albums.log 2>&1
```

---

## 🛠️ Troubleshooting

| Meldung / Code | Bedeutung & Lösung |
|----------------|-------------------|
| `PROPFIND … 401` | Falsches App-Passwort → neues Token erzeugen |
| `MKCOL … 405` | Album existiert bereits → unkritisch |
| `COPY … 409` | Datei ist schon im Album verlinkt → wird übersprungen |
| Album leer | Ordner enthält keine unterstützten Bilddateien → Endungsliste `IMG_EXT` erweitern |

---

## 🛣️ Roadmap

* Option: Hierarchische Albumnamen zusammenfassen (`Urlaub--Tag3`)  
* Video-Support (`.mp4`, `.mov`) via erweiterbarer Endungsliste  
* Dry-Run-Modus (`--dry`) für Testläufe ohne Änderungen

---

## 📜 Lizenz

Diese Software ist ein reines Experiment ohne jede Garantie!

---

**remote2albums.py** erspart stundenlanges Klicken und macht jede bestehende Fotosammlung in wenigen Minuten albumtauglich – der perfekte Start in deine selbst gehostete Fotowelt.
