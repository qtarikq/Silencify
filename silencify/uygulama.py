"""
Silencify - pencereli sürüm

Çalıştırmak için:  python silencify/uygulama.py

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
import baslangic
from arayuz import EKRANLAR, Pencere, SoruPenceresi
from kayit import kayitci_olustur
from motor import ReklamSusturucu
from simge import durum_hali, durum_simgesi, uygulama_simgesi
from spotify import medya_yoneticisini_sifirla
from surum import AD, SURUM
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
        self._son_hal = None             # Tepsi simgesinin hâli (calisiyor / bekliyor / durdu)
        self._tepsi_bilgisi_verildi = False

        # --- Pencere ---
        self.pencere = Pencere()
        self.pencere.setWindowIcon(uygulama_simgesi())
        self.pencere.dugmeye_basildi.connect(self.baslat_durdur)
        self.pencere.kapatma_istendi.connect(self.kapatma_sorusu)

        # --- Bildirim alanı simgesi ve sağ tık menüsü ---
        self.tepsi = QSystemTrayIcon(durum_simgesi("KAPALI"))
        self.menu = QMenu()
        baslik = self.menu.addAction(f"{AD}  v{SURUM}")
        baslik.setEnabled(False)                     # Tıklanamaz, sadece bilgi
        self.menu.addSeparator()
        self.menu.addAction("Pencereyi göster", self.goster)
        self.menu_baslat = self.menu.addAction("Başlat", self.baslat_durdur)
        self.menu_otomatik = self.menu.addAction("Açılışta otomatik başlat")
        self.menu_otomatik.setCheckable(True)
        self.menu_otomatik.setChecked(bool(self.ayarlar["otomatik_basla"]))
        self.menu_otomatik.toggled.connect(self.otomatik_ayari_degisti)
        self.menu_windows = self.menu.addAction("Windows açılınca başlat")
        self.menu_windows.setCheckable(True)
        baslangic.eski_kayitlari_tasi()   # Eski adla açılış kaydı varsa yeni ada taşı
        if baslangic.acik_mi():
            baslangic.ac()        # Program taşındıysa açılış kaydı yeni yerini göstersin (kaydı tazele)
        self.menu_windows.setChecked(baslangic.acik_mi())
        self.menu_windows.toggled.connect(self.windows_ayari_degisti)
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
    def ac(self, arka_planda=False):
        """arka_planda=True: Windows açılışta başlattı; pencere açılmaz, sadece tepsi simgesi."""
        if not arka_planda:
            self.pencere.show()
        if self.ayarlar["otomatik_basla"] is None:          # İlk açılış: kullanıcıya sor
            self.pencere.show()
            soru = SoruPenceresi(
                self.pencere, "Hoş geldin!",
                f"Program açıldığında {AD} kendiliğinden başlasın mı? "
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
            self.menu_baslat.setText("Başlat" if durum == "KAPALI" else "Durdur")
        hal = durum_hali(durum)
        if hal != self._son_hal:                 # Simge sadece büyük değişimlerde değişir (sakin dursun)
            self._son_hal = hal
            self.tepsi.setIcon(durum_simgesi(durum))
        ipucu = f"{AD}: {DURUM_ADI.get(durum, durum)}"
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
                self.tepsi.showMessage(f"{AD} arka planda çalışıyor",
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

    def windows_ayari_degisti(self, acik):
        if acik:
            baslangic.ac()
            if not self.ayarlar["otomatik_basla"]:
                self.tepsi.showMessage(
                    "Windows açılınca başlayacak",
                    "İpucu: Reklamların açılışta hemen susturulması için "
                    "'Açılışta otomatik başlat' seçeneğini de işaretleyebilirsin.",
                    uygulama_simgesi(), 6000)
        else:
            baslangic.kapat()

    def cik(self):
        """Motoru durdurur (kıstığı sesi açar), simgeyi kaldırır ve programı kapatır."""
        self.zamanlayici.stop()
        self.motoru_durdur(bekle=True)
        self.tepsi.hide()
        self.qt.quit()


def main():
    qt = QApplication(sys.argv)
    qt.setQuitOnLastWindowClosed(False)          # Pencere gizlenince program kapanmasın (tepside yaşasın)
    qt.setWindowIcon(uygulama_simgesi())
    arka_planda = baslangic.ARKA_PLAN_ISARETI in sys.argv    # Windows açılışta mı başlattı?
    if zaten_calisiyor_mu():
        if arka_planda:
            return                               # Açılışta sessizce: uyarı göstermeden çık
        SoruPenceresi(None, "Zaten çalışıyor",
                      f"{AD} zaten açık (pencerede, saatin yanında ya da terminalde). "
                      "İkinci kopya açılmadı.",
                      [("tamam", "Tamam", True)]).exec()
        return
    uygulama = Uygulama(qt)
    uygulama.ac(arka_planda)
    sys.exit(qt.exec())


if __name__ == "__main__":
    main()
