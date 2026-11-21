"""
"Windows açılınca başlat" ayarı.

Windows'un kayıt defterinde (registry: Windows'un ayarlarını tuttuğu veritabanı) her kullanıcının
bir "açılışta başlayacak programlar" listesi var:
    HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
Görev Yöneticisi > Başlangıç uygulamaları sekmesinde görünen liste budur.
Program kendini bu listeye SADECE bu kullanıcı için ekler/çıkarır; yönetici izni gerekmez.
"""

import sys
import winreg
from pathlib import Path

RUN_ANAHTARI = r"Software\Microsoft\Windows\CurrentVersion\Run"
DEGER_ADI = "SpotifyReklamSusturucu"
ARKA_PLAN_ISARETI = "--arka-plan"     # Windows başlatınca pencere açılmasın, tepsiye yerleşsin


def baslatma_komutu():
    """Windows açılışta hangi komutu çalıştırsın?"""
    if getattr(sys, "frozen", False):                   # İleride .exe olunca: exe'nin kendisi
        return f'"{sys.executable}" {ARKA_PLAN_ISARETI}'
    pythonw = Path(sys.executable).with_name("pythonw.exe")   # Terminal penceresi açmayan Python
    betik = Path(__file__).resolve().with_name("uygulama.py")
    return f'"{pythonw}" "{betik}" {ARKA_PLAN_ISARETI}'


def acik_mi(anahtar=RUN_ANAHTARI):
    """Program açılış listesinde mi?"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, anahtar) as k:
            winreg.QueryValueEx(k, DEGER_ADI)
            return True
    except FileNotFoundError:
        return False


def ac(anahtar=RUN_ANAHTARI):
    """Programı açılış listesine ekler."""
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, anahtar) as k:
        winreg.SetValueEx(k, DEGER_ADI, 0, winreg.REG_SZ, baslatma_komutu())


def kapat(anahtar=RUN_ANAHTARI):
    """Programı açılış listesinden çıkarır."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, anahtar, 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, DEGER_ADI)
    except FileNotFoundError:
        pass                                            # Zaten listede değil
