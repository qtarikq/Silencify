"""
Motoru (motor.py -> ReklamSusturucu) SAHTE bir Spotify ile test eder.

Gerçek Spotify'a, gerçek sese ve gerçek kayıt dosyalarına hiç dokunmaz:
- Spotify'ın penceresi, medya bilgisi ve ses kaynakları taklit edilir (mock).
- Her tur ne çalacağı ve o tur sonunda ne olacağı aşağıdaki SENARYO'da yazılıdır.
- Her önemli turda hem SES durumu hem motorun EKRANI (motor.durum) kontrol edilir.
- Beklemeler (1-5 saniye) atlanır, test saniyeler içinde biter.

Motora dokunduğun her seferde çalıştır:  python test_senaryo.py
"""

import asyncio
import tempfile
from pathlib import Path

import motor as m

# ---------------------------------------------------------------------------
# 1. SAHTE SPOTIFY
# ---------------------------------------------------------------------------
class SahteSes:
    """pycaw'daki SimpleAudioVolume'un taklidi: sadece sessiz/açık bilgisini tutar."""
    def __init__(self):
        self.sessiz = 0
    def GetMute(self):
        return self.sessiz
    def SetMute(self, deger, _):
        self.sessiz = deger


class SahteOturum:
    """Ses karıştırıcısındaki bir ses kaynağının taklidi."""
    def __init__(self, kimlik):
        self.InstanceIdentifier = kimlik
        self.SimpleAudioVolume = SahteSes()


A, B, C = SahteOturum("A"), SahteOturum("B"), SahteOturum("C")
oturumlar = [A, B]                      # Spotify'ın gerçekte de 2 ses kaynağı var

SARKI = ("Gripin - Aşk Nereden Nereye", ("Aşk Nereden Nereye", "Gripin", "ÇALIYOR"))
REKLAM = ("ŞİMDİ DİNLE", ("ŞİMDİ DİNLE", "ADÉLA", "ÇALIYOR"))
DURDU = ("Spotify Free", ("Aşk Nereden Nereye", "Gripin", "DURDU"))
KAPALI = (None, None)                   # Spotify kapalı: pencere de yok, medya bilgisi de

# ---------------------------------------------------------------------------
# 2. SENARYO
# Her tur: (ne çalıyor, tur sonunda ne oluyor, beklenen SES durumu, beklenen EKRAN)
# Beklenen ses: {kaynak: True=sessiz / False=açık}; None = bu turda kontrol etme
# ---------------------------------------------------------------------------
S, Ac = True, False
SENARYO = [
    (SARKI,  None,                         {"A": Ac, "B": Ac},          "ŞARKI"),               # 0
    (REKLAM, None,                         {"A": Ac, "B": Ac},          "ŞARKI"),               # 1 henüz emin değil
    (REKLAM, None,                         {"A": S,  "B": S},           "REKLAM"),              # 2 kısıldı
    (REKLAM, "kullanıcı A'yı açar",        None,                        "REKLAM"),              # 3
    (REKLAM, None,                         None,                        None),                  # 4
    (REKLAM, None,                         None,                        None),                  # 5
    (REKLAM, None,                         None,                        None),                  # 6
    (REKLAM, None,                         {"A": Ac, "B": Ac},          "REKLAM"),              # 7 fark etti, B'yi de açtı
    (REKLAM, None,                         None,                        None),                  # 8
    (REKLAM, None,                         None,                        None),                  # 9
    (REKLAM, None,                         {"A": Ac, "B": Ac},          "REKLAM"),              # 10 tekrar kısmadı
    (SARKI,  None,                         {"A": Ac, "B": Ac},          "ŞARKI"),               # 11 reklam arası bitti
    (DURDU,  None,                         {"A": Ac, "B": Ac},          "DURDU"),               # 12 duraklatıldı
    (SARKI,  None,                         None,                        "ŞARKI"),               # 13
    (REKLAM, None,                         None,                        None),                  # 14
    (REKLAM, None,                         {"A": S,  "B": S},           "REKLAM"),              # 15 yeni reklam: kısıldı
    (REKLAM, "Spotify yeni kaynak C açar", None,                        None),                  # 16
    (REKLAM, None,                         None,                        None),                  # 17
    (REKLAM, None,                         None,                        None),                  # 18
    (REKLAM, None,                         None,                        None),                  # 19
    (REKLAM, None,                         None,                        None),                  # 20
    (REKLAM, None,                         {"A": S, "B": S, "C": S},    "REKLAM"),              # 21 C de kısıldı
    (KAPALI, None,                         {"A": S, "B": S, "C": S},    "SPOTIFY_BEKLENIYOR"),  # 22 Spotify kapandı
    (KAPALI, None,                         None,                        "SPOTIFY_BEKLENIYOR"),  # 23
    (SARKI,  None,                         {"A": Ac, "B": Ac, "C": Ac}, "ŞARKI"),               # 24 açıldı, ses açıldı
    (SARKI,  None,                         None,                        "ŞARKI"),               # 25
]

# ---------------------------------------------------------------------------
# 3. MOTORU SAHTE DÜNYAYA BAĞLA
# ---------------------------------------------------------------------------
tur = 0
kayitlar = []
gozlemler = {}                          # {tur: (ses durumu, motor.durum)}
motor = m.ReklamSusturucu(kaydet=lambda mesaj: kayitlar.append(f"tur {tur:>2}: {mesaj}"))


async def sahte_medya():
    return SENARYO[tur][0][1]


async def sahte_bekle(_):
    """Motorun beklemesi yerine: o anki durumu not al, sonra senaryodaki olayı gerçekleştir."""
    global tur
    gozlemler[tur] = ({o.InstanceIdentifier: bool(o.SimpleAudioVolume.GetMute()) for o in oturumlar},
                      motor.durum)
    olay = SENARYO[tur][1]
    if olay == "kullanıcı A'yı açar":
        A.SimpleAudioVolume.sessiz = 0
    elif olay == "Spotify yeni kaynak C açar":
        oturumlar.append(C)
    tur += 1
    if tur >= len(SENARYO):
        motor.durdur()                  # Senaryo bitti: durdur düğmesine bas


def main():
    with tempfile.TemporaryDirectory() as gecici:      # Sahte kayıtlar için geçici klasör (sonunda silinir)
        m.KARA_KUTU_DOSYASI = Path(gecici) / "kara_kutu.txt"
        m.KISTIM_NOTU = Path(gecici) / "kistim.txt"
        m.spotify_ses_oturumlari = lambda: list(oturumlar)
        m.spotify_ana_pencere_basligi = lambda: SENARYO[tur][0][0]
        m.spotify_medya_bilgisi = sahte_medya
        motor._bekle = sahte_bekle             # Motorun beklemesi yerine senaryonun bir sonraki turu

        asyncio.run(motor.calis())
        not_kaldi_mi = m.KISTIM_NOTU.exists()

    # --- Sonuçları kontrol et ---
    print("Motorun kayıtları:")
    print("\n".join("  " + k for k in kayitlar))
    print()

    goster = lambda d: " ".join(f"{k}={'sessiz' if v else 'açık'}" for k, v in d.items())
    kontrol_sayisi = hatali = 0
    for t, (_, _, beklenen_ses, beklenen_ekran) in enumerate(SENARYO):
        gercek_ses, gercek_ekran = gozlemler.get(t, ({}, None))
        if beklenen_ses is not None:
            kontrol_sayisi += 1
            tamam = gercek_ses == beklenen_ses
            hatali += not tamam
            print(f"{'TAMAM ' if tamam else 'HATALI'}  tur {t:>2}  ses    beklenen: {goster(beklenen_ses):<34} gerçek: {goster(gercek_ses)}")
        if beklenen_ekran is not None:
            kontrol_sayisi += 1
            tamam = gercek_ekran == beklenen_ekran
            hatali += not tamam
            print(f"{'TAMAM ' if tamam else 'HATALI'}  tur {t:>2}  ekran  beklenen: {beklenen_ekran:<34} gerçek: {gercek_ekran}")

    for aciklama, tamam in (("sonunda 'kıstım' notu kalmamalı", not not_kaldi_mi),
                            ("durdur() sonrası ekran KAPALI olmalı", motor.durum == "KAPALI"),
                            ("durdur() sonrası motor çalışmıyor olmalı", not motor.calisiyor)):
        kontrol_sayisi += 1
        hatali += not tamam
        print(f"{'TAMAM ' if tamam else 'HATALI'}  {aciklama}")

    print("-" * 90)
    print(f"{kontrol_sayisi} kontrolden {kontrol_sayisi - hatali} tanesi TAMAM, {hatali} tanesi HATALI")


if __name__ == "__main__":
    main()
