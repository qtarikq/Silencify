"""
Tek dosyalık .exe oluşturur.

Kullanımı (proje klasöründe, sanal ortam açıkken):
    pip install -r requirements-gelistirme.txt     # bir kere
    python paketle.py

Sonuç:  dist/SpotifyReklamSusturucu.exe

Adımlar:
1. Programın simgesinden Windows'un istediği .ico dosyasını üretir.
2. .exe'ye sağ tık > Özellikler > Ayrıntılar'da görünecek sürüm bilgisini hazırlar (surum.py'den).
3. PyInstaller ile her şeyi (Python, kütüphaneler, kod, simgeler) tek bir .exe'ye paketler.
"""

import struct
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtWidgets import QApplication

from simge import uygulama_simgesi
from surum import SURUM

PROJE = Path(__file__).resolve().parent
CALISMA = PROJE / "build"                 # PyInstaller'ın ara dosyaları (GitHub'a gitmez)
CIKTI = PROJE / "dist"                    # Hazır .exe buraya düşer (GitHub'a gitmez)
AD = "SpotifyReklamSusturucu"


def ico_olustur(hedef):
    """Simgeyi birçok boyutta PNG olarak .ico dosyasının içine koyar (Windows her yerde uygun boyutu seçsin)."""
    _ = QApplication.instance() or QApplication(sys.argv)     # Qt çizimi için gerekli
    simge = uygulama_simgesi("calisiyor")
    resimler = []
    for boyut in (16, 20, 24, 32, 40, 48, 64, 128, 256):
        tampon = QBuffer()
        tampon.open(QIODevice.WriteOnly)
        simge.pixmap(boyut, boyut).save(tampon, "PNG")
        resimler.append((boyut, bytes(tampon.data())))
    # .ico biçimi: 6 baytlık başlık + her resim için 16 baytlık kayıt + resimlerin kendisi
    baslik = struct.pack("<HHH", 0, 1, len(resimler))
    kayitlar, veri = b"", b""
    konum = 6 + 16 * len(resimler)
    for boyut, png in resimler:
        b = 0 if boyut >= 256 else boyut                      # .ico'da 256 "0" diye yazılır
        kayitlar += struct.pack("<BBBBHHII", b, b, 0, 0, 1, 32, len(png), konum)
        veri += png
        konum += len(png)
    hedef.write_bytes(baslik + kayitlar + veri)


def surum_bilgisi_olustur(hedef):
    """.exe'nin Özellikler > Ayrıntılar sekmesindeki bilgiler (PyInstaller'ın istediği biçimde)."""
    sayilar = tuple(int(s) for s in SURUM.split(".")) + (0,)
    hedef.write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={sayilar}, prodvers={sayilar}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('041F04B0', [
      StringStruct('ProductName', 'Spotify Reklam Susturucu'),
      StringStruct('FileDescription', 'Spotify Reklam Susturucu'),
      StringStruct('FileVersion', '{SURUM}'),
      StringStruct('ProductVersion', '{SURUM}'),
      StringStruct('CompanyName', 'qtarikq'),
      StringStruct('LegalCopyright', 'Copyright (c) 2026 qtarikq - MIT License'),
      StringStruct('OriginalFilename', '{AD}.exe'),
      StringStruct('InternalName', '{AD}')])]),
    VarFileInfo([VarStruct('Translation', [0x041F, 1200])])
  ]
)
""", encoding="utf-8")


def main():
    CALISMA.mkdir(exist_ok=True)
    ico = CALISMA / "uygulama.ico"
    surum_dosyasi = CALISMA / "surum_bilgisi.txt"
    ico_olustur(ico)
    surum_bilgisi_olustur(surum_dosyasi)
    print(f"Simge ve sürüm bilgisi hazır (v{SURUM}). PyInstaller çalışıyor, birkaç dakika sürebilir...")

    komut = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile",                                  # Tek dosya
        "--windowed",                                 # Siyah terminal penceresi açılmasın
        "--name", AD,
        "--icon", str(ico),
        "--version-file", str(surum_dosyasi),
        "--add-data", f"{PROJE / 'simgeler'};simgeler",   # simgeler/ klasörünü .exe'nin içine göm
        "--collect-submodules", "winrt",              # winrt parçalarının hepsi dahil olsun
        "--workpath", str(CALISMA),
        "--specpath", str(CALISMA),
        "--distpath", str(CIKTI),
        str(PROJE / "uygulama.py"),
    ]
    subprocess.run(komut, check=True)

    exe = CIKTI / f"{AD}.exe"
    print(f"\nHazır: {exe}  ({exe.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
