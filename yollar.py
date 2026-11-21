"""
Dosya yolları.

Bütün dosya yolları programın KENDİ KONUMUNA göre hesaplanır;
program hangi klasörden başlatılırsa başlatılsın aynı dosyaları kullanır.
Kayıt klasörü yoksa (ör. proje GitHub'dan yeni indirildiyse) otomatik oluşturulur.
"""

from pathlib import Path   # Dosya yollarıyla çalışmak için (Python'la birlikte geliyor)

# Bu dosyanın (yollar.py) bulunduğu klasör = projenin klasörü
PROJE_KLASORU = Path(__file__).resolve().parent

# Hazır simge resimlerinin konabileceği klasör (GitHub'a gider). Boşsa simge kodla çizilir.
SIMGE_KLASORU = PROJE_KLASORU / "simgeler"

# Kayıtların tutulduğu klasör (.gitignore'da, GitHub'a gitmez)
KAYIT_KLASORU = PROJE_KLASORU / "git-ignore-dosyalari"
KAYIT_KLASORU.mkdir(exist_ok=True)    # Yoksa oluştur; varsa hiçbir şey yapma

GOZLEM_KAYDI = KAYIT_KLASORU / "gozlem_kaydi.txt"
SUSTURUCU_KAYDI = KAYIT_KLASORU / "susturucu_kaydi.txt"
KARA_KUTU = KAYIT_KLASORU / "kara_kutu.txt"

# Program Spotify'ı sessize alınca bu dosyayı oluşturur, sesi açınca siler.
# Program düzgün kapanamazsa (terminal × ile kapatıldı, çöktü, bilgisayar kapandı)
# bir sonraki açılışta bu not sayesinde sesi kendisinin kıstığını hatırlar.
KISTIM_NOTU = KAYIT_KLASORU / "kistim.txt"

# Kullanıcının tercihleri (ör. açılışta otomatik başlasın mı)
AYARLAR_DOSYASI = KAYIT_KLASORU / "ayarlar.json"
