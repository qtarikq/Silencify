"""
Programın simgesi (logo + saatin yanındaki tepsi simgesi).

SİMGEYİ DEĞİŞTİRMEK İÇİN (en kolaydan zora):
  1) Hazır resim kullan: 'simgeler' klasörüne simge.png koy (en az 256x256, kare).
     İstersen hâllere göre ayrı resimler de koyabilirsin: simge_calisiyor.png,
     simge_bekliyor.png, simge_durdu.png. Resim varsa çizim yerine o kullanılır.
  2) Başka bir hazır tasarım seç: aşağıdaki AKTIF_TASARIM satırını değiştir.
  3) Renkleri değiştir: RENKLER sözlüğü.
  4) Yeni tasarım ekle: 100x100'lük alana çizen bir fonksiyon yaz, TASARIMLAR'a ekle.

Programın geri kalanı simgenin nasıl çizildiğini bilmez; sadece
    durum_simgesi("REKLAM")   ya da   uygulama_simgesi()
ister.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from yollar import SIMGE_KLASORU

# ---------------------------------------------------------------------------
# AYARLAR: değiştirmek için sadece burayla oynamak yeterli
# ---------------------------------------------------------------------------
AKTIF_TASARIM = "kalkan_nota"   # kalkan_nota, kalkan_dalga, kesik_ekolayzer, sessiz_hoparlor, kesilen_dalga

# Simgenin 3 hâli: (zemin rengi, çizim rengi)
RENKLER = {
    "calisiyor": ("#1D9E75", "#FFFFFF"),   # Program çalışıyor (şarkı, reklam, duraklatma: hepsi)
    "bekliyor":  ("#7F77DD", "#FFFFFF"),   # Spotify bekleniyor
    "durdu":     ("#5F5E5A", "#B4B2A9"),   # Motor durduruldu: reklamlar susturulmuyor
}

# Motorun durumu -> simgenin hâli. Simge SAKİN dursun diye reklamda/duraklatmada renk değişmez.
DURUM_HALI = {
    "KAPALI": "durdu",
    "SPOTIFY_BEKLENIYOR": "bekliyor",
}                                          # Geri kalan her durum: "calisiyor"


# ---------------------------------------------------------------------------
# TASARIMLAR: her biri 100x100'lük bir alana çizer
# ---------------------------------------------------------------------------
def _kalkan_yolu(x, y, g, y_):
    """Üstü yuvarlak, altı sivri yumuşak bir kalkan şekli."""
    yol = QPainterPath()
    yol.moveTo(x + g / 2, y)
    yol.cubicTo(x + g * 0.78, y + y_ * 0.10, x + g, y + y_ * 0.10, x + g, y + y_ * 0.14)
    yol.lineTo(x + g, y + y_ * 0.48)
    yol.cubicTo(x + g, y + y_ * 0.78, x + g * 0.70, y + y_ * 0.93, x + g / 2, y + y_)
    yol.cubicTo(x + g * 0.30, y + y_ * 0.93, x, y + y_ * 0.78, x, y + y_ * 0.48)
    yol.lineTo(x, y + y_ * 0.14)
    yol.cubicTo(x, y + y_ * 0.10, x + g * 0.22, y + y_ * 0.10, x + g / 2, y)
    yol.closeSubpath()
    return yol


def _cubuk(p, x, y_orta, yukseklik, kalinlik):
    p.drawRoundedRect(QRectF(x - kalinlik / 2, y_orta - yukseklik / 2, kalinlik, yukseklik),
                      kalinlik / 2, kalinlik / 2)


def kalkan_nota(p, zemin, cizim):
    """Dolu kalkan, içinde zemin renginde bir nota: 'müzik koruması'."""
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(cizim))
    p.drawPath(_kalkan_yolu(22, 14, 56, 72))
    p.setBrush(QColor(zemin))
    p.drawEllipse(QRectF(36, 52, 15, 12))                  # nota başı
    p.drawRoundedRect(QRectF(46.5, 28, 5, 31), 2, 2)       # sap
    bayrak = QPainterPath()
    bayrak.moveTo(49, 28); bayrak.lineTo(63, 34); bayrak.lineTo(63, 41); bayrak.lineTo(49, 35)
    bayrak.closeSubpath()
    p.drawPath(bayrak)


def kalkan_dalga(p, zemin, cizim):
    """Kalkan çerçevesi + ses dalgası çubukları."""
    p.setPen(QPen(QColor(cizim), 7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    p.drawPath(_kalkan_yolu(22, 16, 56, 70))
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(cizim))
    for x, h in ((39, 16), (50, 28), (61, 16)):
        _cubuk(p, x, 50, h, 7)


def kesik_ekolayzer(p, zemin, cizim):
    """Ekolayzer çubukları + çapraz çizgi."""
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(cizim))
    for x, h in ((26, 26), (42, 46), (58, 34), (74, 20)):
        _cubuk(p, x, 50, h, 10)
    p.setPen(QPen(QColor(zemin), 15, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(22, 78), QPointF(78, 22))
    p.setPen(QPen(QColor(cizim), 6, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(22, 78), QPointF(78, 22))


def sessiz_hoparlor(p, zemin, cizim):
    """Hoparlör + çarpı."""
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(cizim))
    yol = QPainterPath()
    yol.moveTo(20, 40); yol.lineTo(34, 40); yol.lineTo(52, 24); yol.lineTo(52, 76); yol.lineTo(34, 60); yol.lineTo(20, 60)
    yol.closeSubpath()
    p.drawPath(yol)
    p.setPen(QPen(QColor(cizim), 7, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(63, 40), QPointF(81, 60))
    p.drawLine(QPointF(81, 40), QPointF(63, 60))


def kesilen_dalga(p, zemin, cizim):
    """Ortasından kesilen ses dalgası."""
    p.setPen(QPen(QColor(cizim), 7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    sol = QPainterPath(QPointF(14, 50))
    sol.cubicTo(20, 26, 30, 26, 36, 50); sol.cubicTo(39, 60, 41, 62, 43, 56)
    sag = QPainterPath(QPointF(57, 44))
    sag.cubicTo(59, 38, 61, 40, 64, 50); sag.cubicTo(70, 74, 80, 74, 86, 50)
    p.drawPath(sol)
    p.drawPath(sag)
    p.setPen(QPen(QColor(cizim), 5, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(QPointF(46, 64), QPointF(54, 36))


TASARIMLAR = {
    "kalkan_nota": kalkan_nota,
    "kalkan_dalga": kalkan_dalga,
    "kesik_ekolayzer": kesik_ekolayzer,
    "sessiz_hoparlor": sessiz_hoparlor,
    "kesilen_dalga": kesilen_dalga,
}


# ---------------------------------------------------------------------------
# PROGRAMIN KULLANDIĞI FONKSİYONLAR
# ---------------------------------------------------------------------------
def uygulama_simgesi(hal="calisiyor", tasarim=None):
    """Simgenin istenen hâlini (calisiyor / bekliyor / durdu) QIcon olarak döndürür."""
    for dosya in (SIMGE_KLASORU / f"simge_{hal}.png", SIMGE_KLASORU / "simge.png"):
        if dosya.exists():                     # Hazır resim varsa onu kullan
            return QIcon(str(dosya))

    cizici = TASARIMLAR[tasarim or AKTIF_TASARIM]
    zemin, cizim = RENKLER[hal]
    simge = QIcon()
    for boyut in (16, 20, 24, 32, 40, 48, 64, 96, 128, 256):   # Windows her yerde uygun boyutu seçsin
        resim = QPixmap(boyut, boyut)
        resim.fill(Qt.transparent)
        p = QPainter(resim)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(boyut / 100, boyut / 100)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(zemin))
        p.drawRoundedRect(QRectF(2, 2, 96, 96), 24, 24)   # Yuvarlak köşeli kare zemin
        cizici(p, zemin, cizim)
        p.end()
        simge.addPixmap(resim)
    return simge


def durum_hali(durum):
    """Motorun durumuna göre simgenin hâlini söyler."""
    return DURUM_HALI.get(durum, "calisiyor")


def durum_simgesi(durum):
    """Motorun durumuna uygun tepsi simgesi."""
    return uygulama_simgesi(durum_hali(durum))
