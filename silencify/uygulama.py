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
from dil import DIL_ADLARI, dil_sec, diger_dil, secili_dil, windows_dili, yazi
from kayit import kayitci_olustur
from motor import ReklamSusturucu
from simge import durum_hali, durum_simgesi, uygulama_simgesi
from spotify import medya_yoneticisini_sifirla
from surum import AD, SURUM
from tek_kopya import zaten_calisiyor_mu
from yollar import SUSTURUCU_KAYDI

GUNCELLEME_ARALIGI = 250     # Pencere motorun durumuna kaç milisaniyede bir baksın

kayitci = kayitci_olustur("susturucu", SUSTURUCU_KAYDI)


class Uygulama:
    def __init__(self, qt):
        self.qt = qt
        self.ayarlar = ayarlar.oku()
        dil_sec(self.ayarlar["dil"] or windows_dili())   # Seçilmemişse Windows'un dili
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
        self.pencere.dil_istendi.connect(lambda: self.dil_degistir(diger_dil()))

        # --- Bildirim alanı simgesi ve sağ tık menüsü ---
        self.tepsi = QSystemTrayIcon(durum_simgesi("KAPALI"))
        self.menu = QMenu()
        baslik = self.menu.addAction(f"{AD}  v{SURUM}")
        baslik.setEnabled(False)                     # Tıklanamaz, sadece bilgi
        self.menu.addSeparator()
        self.menu_goster = self.menu.addAction("", self.goster)
        self.menu_baslat = self.menu.addAction("", self.baslat_durdur)
        self.menu_otomatik = self.menu.addAction("")
        self.menu_otomatik.setCheckable(True)
        self.menu_otomatik.setChecked(bool(self.ayarlar["otomatik_basla"]))
        self.menu_otomatik.toggled.connect(self.otomatik_ayari_degisti)
        self.menu_windows = self.menu.addAction("")
        self.menu_windows.setCheckable(True)
        baslangic.eski_kayitlari_tasi()   # Eski adla açılış kaydı varsa yeni ada taşı
        if baslangic.acik_mi():
            baslangic.ac()        # Program taşındıysa açılış kaydı yeni yerini göstersin (kaydı tazele)
        self.menu_windows.setChecked(baslangic.acik_mi())
        self.menu_windows.toggled.connect(self.windows_ayari_degisti)
        self.menu_dil = self.menu.addMenu("Dil / Language")          # Her iki dilde de okunabilsin
        self.dil_secenekleri = {}
        for kod, ad in DIL_ADLARI.items():
            secenek = self.menu_dil.addAction(ad, lambda k=kod: self.dil_degistir(k))
            secenek.setCheckable(True)
            self.dil_secenekleri[kod] = secenek
        self.menu.addSeparator()
        self.menu_kapat = self.menu.addAction("", self.cik)
        self.menu_yazilarini_yaz()
        self.tepsi.setContextMenu(self.menu)
        self.tepsi.activated.connect(self.tepsiye_tiklandi)
        self.tepsi.show()

        # --- Pencereyi motorun durumuyla güncel tutan zamanlayıcı ---
        self.zamanlayici = QTimer(interval=GUNCELLEME_ARALIGI)
        self.zamanlayici.timeout.connect(self.guncelle)
        self.zamanlayici.start()

    # -----------------------------------------------------------------------
    # Dil
    # -----------------------------------------------------------------------
    def menu_yazilarini_yaz(self):
        self.menu_goster.setText(yazi("menu_goster"))
        self.menu_baslat.setText(yazi("menu_baslat" if self._son_durum in (None, "KAPALI") else "menu_durdur"))
        self.menu_otomatik.setText(yazi("menu_otomatik"))
        self.menu_windows.setText(yazi("menu_windows"))
        self.menu_kapat.setText(yazi("menu_kapat"))
        for kod, secenek in self.dil_secenekleri.items():
            secenek.setChecked(kod == secili_dil())

    def dil_degistir(self, dil):
        """Dili değiştirir, seçimi kaydeder ve bütün yazıları hemen yeni dilde gösterir."""
        dil_sec(dil)
        self.ayarlar["dil"] = secili_dil()
        ayarlar.yaz(self.ayarlar)
        self.pencere.yazilari_yenile()
        self.menu_yazilarini_yaz()
        self.guncelle()

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
                self.pencere, yazi("hosgeldin_baslik"), yazi("hosgeldin_metin", ad=AD),
                [("evet", yazi("hosgeldin_evet"), True),
                 ("hayir", yazi("hosgeldin_hayir"), False)],
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
            self.menu_baslat.setText(yazi("menu_baslat" if durum == "KAPALI" else "menu_durdur"))
        hal = durum_hali(durum)
        if hal != self._son_hal:                 # Simge sadece büyük değişimlerde değişir (sakin dursun)
            self._son_hal = hal
            self.tepsi.setIcon(durum_simgesi(durum))
        durum_adi = yazi(f"ipucu.{durum}") if durum in EKRANLAR else durum
        ipucu = f"{AD}: {durum_adi}"
        if baslik and durum in ("ŞARKI", "PODCAST", "DURDU"):
            ipucu += f"\n{baslik}"
        self.tepsi.setToolTip(ipucu[:127])       # Windows ipucu uzunluk sınırı

    # -----------------------------------------------------------------------
    # Pencere ve tepsi olayları
    # -----------------------------------------------------------------------
    def kapatma_sorusu(self):
        renk = EKRANLAR.get(self._son_durum or "KAPALI", EKRANLAR["KAPALI"])["cerceve"]
        soru = SoruPenceresi(
            self.pencere, yazi("kapat_baslik"), yazi("kapat_metin"),
            [("arka", yazi("kapat_arka"), True),
             ("kapat", yazi("kapat_tamamen"), False),
             (None, yazi("kapat_vazgec"), False)],
            cerceve=renk)
        soru.exec()
        if soru.secim == "arka":
            self.pencere.hide()
            if not self._tepsi_bilgisi_verildi:
                self.tepsi.showMessage(yazi("arka_plan_baslik", ad=AD), yazi("arka_plan_metin"),
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
                    yazi("windows_baslik"), yazi("windows_metin"),
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
        dil_sec(ayarlar.oku()["dil"] or windows_dili())
        SoruPenceresi(None, yazi("zaten_baslik"), yazi("zaten_metin", ad=AD),
                      [("tamam", yazi("tamam"), True)]).exec()
        return
    uygulama = Uygulama(qt)
    uygulama.ac(arka_planda)
    sys.exit(qt.exec())


if __name__ == "__main__":
    main()
