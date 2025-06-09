# remote2albums.py  
**Nextcloud Album Auto-Creator**

*Automatisiert das Anlegen von Alben in der Nextcloud-Photos-App aus bereits vorhandenen Ordnern – ideal für Umsteiger von Google Takeout, iCloud Photos, Android „Sofort-Upload“, DigiCam-Importen u. v. m.*

---

## 🧐 Problemstellung

Beim Wechsel zu **Nextcloud Photos** stellen viele fest, dass ihre vorhandenen Verzeichnisstrukturen **nicht** als Alben erkannt werden:

| Typisches Szenario | Ergebnis in Photos |
| :----------------- | :----------------- |
| **Google Takeout**&nbsp;– Takeout legt jeden Tag/Monat als eigenen Ordner an | Keine Alben, nur tiefe Ordnerbäume |
| **Android „SofortUpload“ / iOS Camera Upload** – Ordner nach Jahr / Monat / Tag | Ebenfalls keine Alben sichtbar |
| **NAS- oder DigiCam-Importe** (`urlaub/bali/tag3/img001.jpg`) | Photos zeigt nur die Wurzelordner |

Die Photos-App erzeugt ein „Album“ erst dann, wenn intern ein spezieller DAV-Knoten existiert – das geschieht nur per Web-GUI. Hunderte Ordner manuell anzuklicken ist unpraktisch.

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
   *Google Takeout*: `Google Photos`  
   *Android*: `SofortUpload/Pictures`

---

## ▶️ Benutzung

```bash
./remote2albums.py \
  --url     https://cloud.example.com \
  --user    alice \
  --password "APP-PASSWORT" \
  --remote  "SofortUpload/Pictures"
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

Dieses Projekt steht unter der **MIT-Lizenz** – Details siehe [`LICENSE`](LICENSE).

---

**remote2albums.py** erspart stundenlanges Klicken und macht jede bestehende Fotosammlung in wenigen Minuten albumtauglich – der perfekte Start in deine selbst gehostete Fotowelt.
