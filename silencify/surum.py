"""
Programın adı ve sürüm numarası (tek yerde: ad değişirse sadece burası değişir).

Sürüm biçimi: BÜYÜK.KÜÇÜK.YAMA  (semantic versioning: anlamsal sürümleme)
- YAMA  (1.0.0 -> 1.0.1): hata düzeltmesi, davranış aynı
- KÜÇÜK (1.0.1 -> 1.1.0): yeni özellik, eski kullanım bozulmadan
- BÜYÜK (1.1.0 -> 2.0.0): büyük, geriye uyumsuz değişiklik
GitHub'da yayınlarken etiket (tag) olarak da bu numara kullanılır: v1.0.0
"""

AD = "Silencify"
ACIKLAMA = "Spotify reklamlarını susturur"
SURUM = "1.1.0"

# Eski adlar: önceki sürümlerden kalan ayar klasörü ve açılış kaydı yeni ada taşınsın diye
ESKI_ADLAR = ["SpotifyReklamSusturucu"]
