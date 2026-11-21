"""
Dosya yolları.

Program iki şekilde çalışabilir:
- KAYNAK KODDAN (python silencify/uygulama.py): her şey proje klasöründe durur.
  Kayıtlar ve ayarlar: git-ignore-dosyalari/  (GitHub'a gitmez)
- TEK DOSYALIK .EXE OLARAK: .exe çalışırken kendini Windows'un GEÇİCİ bir klasörüne açar
  ve kapanınca o klasör silinir. Bu yüzden kalıcı olması gereken her şey (kayıtlar,
  ayarlar, "kıstım" notu) Windows'un programlara ayırdığı kalıcı klasöre yazılır:
  C:\\Users\\<ad>\\AppData\\Local\\Silencify

Bütün yollar burada hesaplanır; programın geri kalanı nerede çalıştığını bilmek zorunda değil.
Kayıt klasörü yoksa otomatik oluşturulur.
"""

import os
import sys
from pathlib import Path   # Dosya yollarıyla çalışmak için (Python'la birlikte geliyor)

from surum import AD, ESKI_ADLAR

UYGULAMA_ADI = AD

# .exe olarak mı çalışıyoruz? (PyInstaller .exe'yi oluştururken sys.frozen'ı True yapar)
EXE_MI = getattr(sys, "frozen", False)

# Bu dosyanın (yollar.py) bulunduğu klasör = uygulamanın kod klasörü (silencify/)
KOD_KLASORU = Path(__file__).resolve().parent
# Onun bir üstü = projenin ana klasörü
PROJE_KLASORU = KOD_KLASORU.parent

if EXE_MI:
    # .exe'nin İÇİNE gömülü dosyalar (simgeler) geçici klasörde: sys._MEIPASS
    GOMULU_KLASOR = Path(getattr(sys, "_MEIPASS", KOD_KLASORU))
    KAYIT_KLASORU = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / UYGULAMA_ADI
else:
    GOMULU_KLASOR = KOD_KLASORU
    KAYIT_KLASORU = PROJE_KLASORU / "git-ignore-dosyalari"   # .gitignore'da, GitHub'a gitmez

if EXE_MI and not KAYIT_KLASORU.exists():
    # Program eski bir adla kullanıldıysa ayarlarını ve kayıtlarını yeni ada taşı
    for eski_ad in ESKI_ADLAR:
        eski_klasor = KAYIT_KLASORU.with_name(eski_ad)
        if eski_klasor.is_dir():
            eski_klasor.rename(KAYIT_KLASORU)
            break

KAYIT_KLASORU.mkdir(parents=True, exist_ok=True)   # Yoksa oluştur; varsa hiçbir şey yapma

# Hazır simge resimlerinin konabileceği klasör (GitHub'a gider). Boşsa simge kodla çizilir.
SIMGE_KLASORU = GOMULU_KLASOR / "simgeler"

GOZLEM_KAYDI = KAYIT_KLASORU / "gozlem_kaydi.txt"
SUSTURUCU_KAYDI = KAYIT_KLASORU / "susturucu_kaydi.txt"
KARA_KUTU = KAYIT_KLASORU / "kara_kutu.txt"

# Program Spotify'ı sessize alınca bu dosyayı oluşturur, sesi açınca siler.
# Program düzgün kapanamazsa (terminal × ile kapatıldı, çöktü, bilgisayar kapandı)
# bir sonraki açılışta bu not sayesinde sesi kendisinin kıstığını hatırlar.
KISTIM_NOTU = KAYIT_KLASORU / "kistim.txt"

# Kullanıcının tercihleri (ör. açılışta otomatik başlasın mı)
AYARLAR_DOSYASI = KAYIT_KLASORU / "ayarlar.json"
