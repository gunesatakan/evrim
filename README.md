# Evrim Simülasyonu

Bu proje, `evrim.md` dosyasında belirtilen optropi ve kaotropi simülasyonunu içerir.

## Gereksinimler

- Python 3.x
- `pygame` kütüphanesi

## Kurulum

Gerekli kütüphaneyi yüklemek için terminalde şu komutu çalıştırın:

```bash
pip install pygame
```

## Çalıştırma

Simülasyonu başlatmak için:

```bash
python simulation.py
```

## Simülasyon Detayları

- **Kırmızı Daireler (Kaotropi):** Tehdit unsurları. Rastgele yönlerde düz çizgiler halinde hareket ederler ve duvarlardan sekerler.
- **Yeşil Daireler (Optropi):** Hayatta kalmaya çalışanlar. Kaotropileri gördüklerinde rotalarını hafızalarına alırlar ve bu rotalardan kaçınırlar.
- **Çizgiler:** Optropilerin hafızasındaki tehlikeli yollar (sadece Optropi'nin hafızasında olanlar yeşilimsi hayalet çizgiler olarak çizilmiştir).
