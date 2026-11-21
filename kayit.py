"""
Kayıt tutma (log).

Python'un hazır 'logging' kütüphanesini kullanır:
- Her kayıt satırı hem ekrana hem dosyaya yazılır ("14:32:05  mesaj" biçiminde).
- Dosya MAKS_BOYUT'u geçince adı ".1" olarak değiştirilir ve yeni bir dosya açılır
  (dönen kayıt / log rotation). En fazla YEDEK_SAYISI eski kopya tutulur,
  daha eskisi otomatik silinir. Böylece kayıtlar diski hiçbir zaman doldurmaz.
"""

import logging                                       # Python'la birlikte geliyor
from logging.handlers import RotatingFileHandler     # Boyut sınırına gelince dosyayı "döndüren" yazıcı

MAKS_BOYUT = 1_000_000     # Bir kayıt dosyası en fazla ~1 MB olsun
YEDEK_SAYISI = 2           # En fazla 2 eski kopya tut (toplam ~3 MB)

BICIM = logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S")


def kayitci_olustur(ad, dosya, maks_boyut=MAKS_BOYUT, yedek_sayisi=YEDEK_SAYISI):
    """
    Hem ekrana hem 'dosya'ya yazan bir kayıtçı (logger) döndürür.
    Kullanımı:  kayitci = kayitci_olustur("susturucu", yol);  kayitci.info("mesaj")
    """
    kayitci = logging.getLogger(ad)
    if kayitci.handlers:                 # Aynı ad için daha önce oluşturulduysa tekrar kurma
        return kayitci
    kayitci.setLevel(logging.INFO)
    kayitci.propagate = False            # Mesajlar başka kayıtçılara da gitmesin (iki kez yazılmasın)

    dosyaya = RotatingFileHandler(dosya, maxBytes=maks_boyut, backupCount=yedek_sayisi,
                                  encoding="utf-8", delay=True)   # delay: ilk mesaja kadar dosyayı açma
    dosyaya.setFormatter(BICIM)
    kayitci.addHandler(dosyaya)

    ekrana = logging.StreamHandler()
    ekrana.setFormatter(BICIM)
    kayitci.addHandler(ekrana)
    return kayitci


def buyukse_kenara_al(dosya, maks_boyut=MAKS_BOYUT):
    """
    Dosya maks_boyut'u geçmişse adını '<ad>.1' yapar (varsa eski .1'in üstüne yazar).
    logging'in kullanamadığı dosyalar için (ör. kara kutu); program başlarken bir kere çağrılır.
    """
    if dosya.exists() and dosya.stat().st_size > maks_boyut:
        dosya.replace(dosya.with_name(dosya.name + ".1"))
