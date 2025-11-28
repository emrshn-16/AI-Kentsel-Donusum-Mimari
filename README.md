# AI Kentsel Dönüşüm Mimarı

Yapay zekâ destekli kentsel analiz, tahmin ve risk değerlendirme paneli (demo sürüm).

## Özellikler

- Alan analizi (yeşil alan oranı, nüfus yoğunluğu, riskler, öneriler)
- 2030 projeksiyonu (konut ihtiyacı, ulaşım yük artışı, öneri)
- AI Risk Skoru (0–100 arası, düşük/orta/yüksek seviye ve açıklama)
- Senaryo motoru:
  - Yoğun Merkez
  - Gelişen Bölge
  - Yeşil Odaklı Bölge
- Yeşil alan simülasyonu (slider ile hedef oranı değiştirerek risk etkisini görmek)
- Proje kaydetme ve listeleme
- Her proje için HTML raporu (tarayıcıdan PDF olarak kaydedilebilir)
- Harita entegrasyonu (Leaflet + OpenStreetMap, her senaryo için temsilî alan)

## Klasör Yapısı

```text
frontend/
  index.html
  app.js

backend.py        # FastAPI uygulaması
docs/             # (İsteğe bağlı) Proje özeti, teknik rapor, sunum
