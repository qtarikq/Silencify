"""
Kullanıcı tercihleri: ayarlar.json dosyasında saklanır.

    ayarlar = oku()
    ayarlar["otomatik_basla"] = True
    yaz(ayarlar)
"""

import json

from yollar import AYARLAR_DOSYASI

VARSAYILAN = {
    "otomatik_basla": None,   # None = henüz sorulmadı; True = açılınca başlasın; False = elle başlatılsın
}


def oku():
    """Ayarları okur. Dosya yoksa ya da bozuksa varsayılanları döndürür (program çökmesin)."""
    ayarlar = dict(VARSAYILAN)
    try:
        ayarlar.update(json.loads(AYARLAR_DOSYASI.read_text(encoding="utf-8")))
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return ayarlar


def yaz(ayarlar):
    """Ayarları dosyaya yazar."""
    AYARLAR_DOSYASI.write_text(json.dumps(ayarlar, ensure_ascii=False, indent=2), encoding="utf-8")
