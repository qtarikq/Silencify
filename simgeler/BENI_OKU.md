# Simgeler

Bu klasöre bir resim koyarsan program kendi çizdiği simge yerine onu kullanır.

- `simge.png` → her durumda bu resim
- İstersen hâllere göre ayrı resimler:
  - `simge_calisiyor.png` → program çalışırken
  - `simge_bekliyor.png` → Spotify beklenirken
  - `simge_durdu.png` → program durdurulmuşken

Resim **kare** ve en az **256x256** piksel olmalı (şeffaf arka planlı PNG önerilir).
Klasör boşsa simge `simge.py` içindeki koddan çizilir.
