"""
Reklam tanıma kuralı.

Programın "şu an ne çalıyor?" kararını verdiği TEK yer burası.
Hem reklam_susturucu.py hem kural_testi.py kuralı buradan alır;
böylece test ettiğimiz kural ile programın kullandığı kural hep aynı kalır.
"""

DURAKLATMA_BASLIKLARI = {"Spotify Free", "Spotify Premium"}
BILINEN_REKLAM_METINLERI = {"şimdi dinle", "indir ve dinle"}   # Küçük harfle, noktasız


def turkce_kucuk_harf(metin):
    """Türkçeye uygun küçük harfe çevirir. (Python'un lower()'ı 'İ' ve 'I' harflerini yanlış çevirir.)"""
    return metin.replace("İ", "i").replace("I", "ı").lower()


def bilinen_reklam_metni_mi(sarki):
    """Şarkı adı bilinen bir reklam metniyse True döndürür. Harf büyüklüğüne ve sondaki noktaya bakmaz."""
    return turkce_kucuk_harf(sarki).strip().rstrip(".") in BILINEN_REKLAM_METINLERI


def karar_ver(baslik, sarki, sanatci):
    """
    Ana pencere başlığına ve medya bilgisine bakıp şu kararlardan birini döndürür:
    "DURDU", "REKLAM", "PODCAST", "ŞARKI" ya da bilgi yoksa "?".
    Sorular SIRAYLA sorulur, ilk "evet"te karar verilir.
    """
    if baslik is None:
        return "?"
    if baslik in DURAKLATMA_BASLIKLARI:      # 1. Duraklatılmış mı?
        return "DURDU"
    if sanatci == "Spotify":                 # 2. Sanatçı Spotify mı?
        return "REKLAM"
    if bilinen_reklam_metni_mi(sarki):       # 2+. Bilinen bir reklam metni mi?
        return "REKLAM"
    if sanatci == "":                        # 3. Sanatçı boş mu?
        return "PODCAST"
    if " - " in baslik:                      # 4. Başlık "Sanatçı - Şarkı" formatında mı?
        return "ŞARKI"
    return "REKLAM"                          # 5. Hiçbiri değilse
