"""
Spotify Reklam Susturucu - pencereli sürüm

Çalıştırmak için:  python uygulama.py

Parçalar:
- Pencere (arayuz.py): sadece gösterir.
- Motor (motor.py): arka planda AYRI BİR THREAD'de (iş parçacığı) çalışır, Spotify'ı izler.
- Bu dosya ikisini birbirine bağlar: pencere saniyede 4 kez motorun durumuna bakar.
- Bildirim alanında (saatin yanında) durumun renginde bir simge durur.
"""

import asyncio
import sys
import threading

import comtypes
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

import ayarlar
from arayuz import EKRANLAR, Pencere, SoruPenceresi, durum_simgesi
from kayit import kayitci_olustur
from motor import ReklamSusturucu
from spotify import medya_yoneticisini_sifirla
from tek_kopya import zaten_calisiyor_mu
from yollar import SUSTURUCU_KAYDI

GUNCELLEME_ARALIGI = 250     # Pencere motorun durumuna kaç milisaniyede bir baksın
DURUM_ADI = {
    "KAPALI": "Kapalı", "SPOTIFY_BEKLENIYOR": "Spotify bekleniyor", "ŞARKI": "Açık",
    "PODCAST": "Açık", "DURDU": "Duraklatıldı", "REKLAM": "Reklam susturuldu",
}

kayitci = kayitci_olustur("susturucu", SUSTURUCU_KAYDI)


class Uygulama:
    def __init__(self, qt):
        self.qt = qt
        self.ayarlar = ayarlar.oku()
        self.motor = None
        self.is_parcacigi = None         # Motorun çalıştığı thread
        self._son_durum = None
        self._tepsi_bilgisi_verildi = False

        # --- Pencere ---
        self.pencere = Pencere()
        self.pencere.dugmeye_basildi.connect(self.baslat_durdur)
        self.pencere.kapatma_istendi.connect(self.kapatma_sorusu)

        # --- Bildirim alanı simgesi ve sağ tık menüsü ---
        self.tepsi = QSystemTrayIcon(durum_simgesi("KAPALI"))
        self.menu = QMenu()
        self.menu.addAction("Pencereyi göster", self.goster)
        self.menu_baslat = self.menu.addAction("Başlat", self.baslat_durdur)
        self.menu_otomatik = self.menu.addAction("Açılışta otomatik başlat")
        self.menu_otomatik.setCheckable(True)
        self.menu_otomatik.setChecked(bool(self.ayarlar["otomatik_basla"]))
        self.menu_otomatik.toggled.connect(self.otomatik_ayari_degisti)
        self.menu.addSeparator()
        self.menu.addAction("Tamamen kapat", self.cik)
        self.tepsi.setContextMenu(self.menu)
        self.tepsi.activated.connect(self.tepsiye_tiklandi)
        self.tepsi.show()

        # --- Pencereyi motorun durumuyla güncel tutan zamanlayıcı ---
        self.zamanlayici = QTimer(interval=GUNCELLEME_ARALIGI)
        self.zamanlayici.timeout.connect(self.guncelle)
        self.zamanlayici.start()

    # -----------------------------------------------------------------------
    # Açılış
    # -----------------------------------------------------------------------
    def ac(self):
        self.pencere.show()
        if self.ayarlar["otomatik_basla"] is None:          # İlk açılış: kullanıcıya sor
            soru = SoruPenceresi(
                self.pencere, "Hoş geldin!",
                "Program açıldığında reklam susturucu kendiliğinden başlasın mı? "
                "Bunu sonradan saatin yanındaki simgeye sağ tıklayarak değiştirebilirsin.",
                [("evet", "Açılınca otomatik başlasın", True),
                 ("hayir", "Ben elimle başlatayım", False)],
                cerceve="#1D9E75")
            soru.exec()
            self.ayarlar["otomatik_basla"] = soru.secim != "hayir"
            ayarlar.yaz(self.ayarlar)
            self.menu_otomatik.setChecked(self.ayarlar["otomatik_basla"])
        if self.ayarlar["otomatik_basla"]:
            self.motoru_baslat()

    # -----------------------------------------------------------------------
    # Motor
    # -----------------------------------------------------------------------
    def motor_calisiyor_mu(self):
        return self.is_parcacigi is not None and self.is_parcacigi.is_alive()

    def motoru_baslat(self):
        if self.motor_calisiyor_mu():
            return
        self.motor = ReklamSusturucu(kaydet=kayitci.info)
        self.is_parcacigi = threading.Thread(target=self._motor_is_parcacigi, args=(self.motor,), daemon=True)
        self.is_parcacigi.start()

    @staticmethod
    def _motor_is_parcacigi(motor):
        """Motorun ayrı thread'de çalışan kısmı."""
        comtypes.CoInitializeEx()            # Windows'un ses sistemi (COM) her thread'de ayrıca başlatılmalı
        medya_yoneticisini_sifirla()         # Medya yöneticisini bu thread'de yeniden iste
        try:
            asyncio.run(motor.calis())
        finally:
            comtypes.CoUninitialize()

    def motoru_durdur(self, bekle=False):
        if self.motor is not None:
            self.motor.durdur()
        if bekle and self.motor_calisiyor_mu():
            self.is_parcacigi.join(timeout=10)   # Motor sesi açıp kapanana kadar bekle

    def baslat_durdur(self):
        if self.motor_calisiyor_mu() and self.motor.calisiyor:
            self.motoru_durdur()
        else:
            self.motoru_baslat()

    # -----------------------------------------------------------------------
    # Ekranı güncelle (saniyede 4 kez)
    # -----------------------------------------------------------------------
    def guncelle(self):
        if self.motor is not None and self.motor_calisiyor_mu():
            durum, baslik = self.motor.durum, self.motor.baslik
        else:
            durum, baslik = "KAPALI", None
        self.pencere.durumu_goster(durum, baslik)
        if durum != self._son_durum:
            self._son_durum = durum
            self.tepsi.setIcon(durum_simgesi(durum))
            self.menu_baslat.setText("Başlat" if durum == "KAPALI" else "Durdur")
        ipucu = f"Reklam susturucu: {DURUM_ADI.get(durum, durum)}"
        if baslik and durum in ("ŞARKI", "PODCAST", "DURDU"):
            ipucu += f"\n{baslik}"
        self.tepsi.setToolTip(ipucu[:127])       # Windows ipucu uzunluk sınırı

    # -----------------------------------------------------------------------
    # Pencere ve tepsi olayları
    # -----------------------------------------------------------------------
    def kapatma_sorusu(self):
        renk = EKRANLAR.get(self._son_durum or "KAPALI", EKRANLAR["KAPALI"])["cerceve"]
        soru = SoruPenceresi(
            self.pencere, "Kapatılsın mı?",
            "Arka planda çalışırsa reklamları susturmaya devam eder; "
            "saatin yanındaki simgeden pencereyi tekrar açabilirsin.",
            [("arka", "Arka planda çalışsın", True),
             ("kapat", "Uygulama tamamen kapansın", False),
             (None, "Vazgeç", False)],
            cerceve=renk)
        soru.exec()
        if soru.secim == "arka":
            self.pencere.hide()
            if not self._tepsi_bilgisi_verildi:
                self.tepsi.showMessage("Reklam susturucu arka planda çalışıyor",
                                       "Pencereyi açmak için saatin yanındaki simgeye tıkla.",
                                       durum_simgesi(self._son_durum or "KAPALI"), 4000)
                self._tepsi_bilgisi_verildi = True
        elif soru.secim == "kapat":
            self.cik()

    def tepsiye_tiklandi(self, neden):
        if neden == QSystemTrayIcon.Trigger:        # Sol tık
            self.goster()

    def goster(self):
        self.pencere.showNormal()
        self.pencere.raise_()
        self.pencere.activateWindow()

    def otomatik_ayari_degisti(self, acik):
        self.ayarlar["otomatik_basla"] = acik
        ayarlar.yaz(self.ayarlar)

    def cik(self):
        """Motoru durdurur (kıstığı sesi açar), simgeyi kaldırır ve programı kapatır."""
        self.zamanlayici.stop()
        self.motoru_durdur(bekle=True)
        self.tepsi.hide()
        self.qt.quit()


def main():
    qt = QApplication(sys.argv)
    qt.setQuitOnLastWindowClosed(False)          # Pencere gizlenince program kapanmasın (tepside yaşasın)
    if zaten_calisiyor_mu():
        SoruPenceresi(None, "Zaten çalışıyor",
                      "Reklam susturucu zaten açık (pencerede, saatin yanında ya da terminalde). "
                      "İkinci kopya açılmadı.",
                      [("tamam", "Tamam", True)]).exec()
        return
    uygulama = Uygulama(qt)
    uygulama.ac()
    sys.exit(qt.exec())


if __name__ == "__main__":
    main()
