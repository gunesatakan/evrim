# Ölüm, Savaş ve Renk — Uygulama Planı

> **Durum:** Taslak — tartışmaya açık
> **Kapsam:** Ölüm/eleme → zar dayanıklılığı → saldırı/savunma organları → renk
> **Amaç:** Davranış genomu için gerekli seçilim baskısını kurmak

---

## 0. Neden bu sırayla

Davranış genomu (uyaran → tepki tablosu) ancak **kötü davranan ölürse** evrimleşir.
Şu an tek ölüm yolu kaotropi çarpması ve o da davranıştan bağımsız. Bu yüzden
önce ölüm, sonra savaş, en son davranış.

Renk araya giriyor çünkü davranış genomunun ilk uyaranı o olacak ve altyapı
gerektirmiyor (bkz. Aşama 4).

---

## Aşama 1 — Ölüm ve eleme

### Mevcut sorun

| | Şu an |
|---|---|
| Enerji 0'a inince | `shutdown` — donuyor ama listede kalıyor, CPU yiyor |
| Açlıktan ölüm | **yok** |
| Kaotropi çarpması | **anında ölüm** (dayanıklılıkla çelişecek) |
| Nüfus tavanında | kimse elenmiyor, sadece üreme duruyor |

### Yapılacak

1. **Açlıktan ölüm.** `shutdown` durumu `STARVE_TIMEOUT` (öneri: 15 sn) boyunca
   sürerse hücre listeden düşer. Midesinde besin varsa sindirim onu kurtarabilir —
   yani donma "son şans" penceresi olur, kalıcı zombi değil.

2. **Ölüm = leş.** Ölen hücre bulunduğu yere besin bırakır (öneri: organ
   sayısıyla orantılı, `CORPSE_FOOD` adet). Biyolojik olarak doğru ve besin
   döngüsünü kapatıyor: ölüm başkasının kazancı oluyor.

3. **Nüfus tavanı yerine eleme.** Tavana ulaşıldığında bölünmeyi engellemek
   yerine en düşük enerjili hücre elenir. Böylece hızlı beslenen gerçekten
   yavaşın yerini alır — **seçilim buradan doğar.**

4. **Kaotropi çarpması hasara döner** (Aşama 2 ile birlikte). Anında ölüm
   kalırsa iki farklı ölüm modeli yan yana durur.

### Ölçüt

Nüfusun tavanda sabitlenmesi değil, **devir hızı**: birim zamanda kaç doğum /
kaç ölüm. Devir varsa seçilim işliyor demektir.

---

## Aşama 2 — Zar dayanıklılığı ve hasar kanalları

Tek bir "can" değeri yerine **hasar kanalı** kavramı. Her saldırı bir kanaldan
vurur, her savunma belirli kanallara karşı işe yarar. Tek sayıya indirgenmiş bir
"atak vs defans" karşılaştırması olmayacak.

### Üç kanal

| Kanal | Ne yapar | Doğadaki karşılığı |
|---|---|---|
| **Mekanik** | Zarı fiziksel olarak deler | delici stilet, harpun, nematosist |
| **Kimyasal** | Zarı çözer / hücreyi zehirler | bakteriosin, litik enzim |
| **Yutma** | Hasar vermez, hedefi tümüyle alır | fagositoz |

### Zar

- `integrity` (0–max): zarın bütünlüğü. 0 = ölüm.
- Maksimum, zara yapılan yatırımla artar (yeni bir gen: `membrane_integrity`).
- Kendini yavaş onarır, **enerji harcayarak**. Onarım hızı ayrı bir savunma
  organının (Aşama 3) işi.

---

## Aşama 3 — Saldırı ve savunma organları

> **Bu bölüm tartışılacak.** Aşağıdaki altı saldırı / beş savunma mekanizması
> gerçek mikrobiyal sistemlerden alındı. Hepsinin farklı bir üstünlüğü ve
> farklı bir açığı var — kimse her şeye karşı iyi değil.

### Saldırı organları

| Organ | Kanal | Menzil | Karakter | Zayıflığı |
|---|---|---|---|---|
| **Stilet** <br><sub>*Vampyrella, Pfiesteria*</sub> | Mekanik | Temas | Yüksek tek hedef hasarı, kısa bekleme, ucuz | Temas şart; kalın duvara karşı zayıf |
| **Harpun (T6SS)** <br><sub>*Tip VI salgı sistemi*</sub> | Mekanik | Temas+ | Hızlı ateş, orta hasar | Atış başına yüksek enerji; kapsül tamamen engeller |
| **Nematosist** <br><sub>*dinoflagellat, silli trikosist*</sub> | Mekanik | **Uzak (~50 px)** | Kaçan avı vurabilen tek mekanik silah | Sınırlı cephane, uzun yeniden dolum, pahalı üretim |
| **Toksin salgısı** <br><sub>*bakteriosin / kolisin*</sub> | Kimyasal | **Alan (çevre)** | Aynı anda birden çok hedef, temas gerekmez, kaçana da işler | Yavaş birikir, nişan alınamaz, sürekli enerji yakar |
| **Litik enzim** <br><sub>*ekstraselüler proteaz*</sub> | Kimyasal | Kısa | **Zırhı yok sayar** — duvara karşı en iyi silah | Yavaş; besinin bir kısmı ortama kaçar (verim düşük) |
| **Fagositoz** <br><sub>*amip*</sub> | Yutma | Temas | Hedefi bütün alır — hasar yok, tam kaynak | Sadece **daha küçük** hedefe; yutarken avcı hareketsiz kalır |

### Savunma organları

| Organ | Neye karşı | Karakter | Bedeli |
|---|---|---|---|
| **Hücre duvarı** <br><sub>*peptidoglikan*</sub> | Mekanik | Sabit hasar azaltma | Ağır — hız cezası; kimyasala tamamen açık |
| **Dış zar / LPS** <br><sub>*Gram-negatif*</sub> | Kimyasal | Toksin/enzim bariyeri | Mekaniğe karşı zayıf |
| **Kapsül / mukus** <br><sub>*glikokaliks*</sub> | **Temas gerektiren her şey** | Stilet, harpun ve fagositozu neredeyse tamamen durdurur | Sürüklenme (hız cezası); menzilli ve yayılan saldırılara **hiç** işe yaramaz |
| **Efflux pompası** | Kimyasal | Toksini aktif olarak dışarı atar — neredeyse sıfırlar | Her kullanımda enerji; mekaniğe karşı işe yaramaz |
| **Zar onarımı** | Hepsi (sonradan) | Zamanla iyileşir, önden ağırlık taşımaz | Hasarı **önlemez**; ani/yoğun hasarda yetişemez, sürekli enerji |

### Etkileşim matrisi

Satır = saldırı, sütun = savunma. Kalın olanlar tasarımın çekirdeği.

| | Duvar | Dış zar | Kapsül | Efflux | Onarım |
|---|---|---|---|---|---|
| **Stilet** | çok iyi savunur | zayıf | **çok iyi savunur** | — | orta |
| **Harpun** | iyi savunur | zayıf | **tamamen durdurur** | — | orta |
| **Nematosist** | iyi savunur | zayıf | **işe yaramaz** | — | zayıf (tek vuruş büyük) |
| **Toksin** | **işe yaramaz** | iyi savunur | zayıf | **tamamen durdurur** | iyi (yavaş hasar) |
| **Litik enzim** | **işe yaramaz** | iyi savunur | orta | orta | orta |
| **Fagositoz** | — | — | **çok iyi savunur** | — | — |

Okunuşu:
- **Duvar** mekaniğe karşı en iyi, ama kimyasala karşı hiçbir şey yapmıyor
- **Kapsül** temas silahlarını öldürüyor ama nematosist ve toksin onu delip geçiyor
- **Efflux** toksini bitiriyor ama mekanik saldırıya karşı boş
- **Onarım** yavaş aşınmaya karşı iyi, tek büyük vuruşa karşı kötü

Yani hiçbir savunma kombinasyonu her şeye karşı güvenli değil ve saldıran taraf
karşısındakinin zırhına göre farklı silah seçmek zorunda. Aradığın "sadece atak
değeri değil" bu.

---

## Aşama 4 — Renk (davranış genomunun ilk uyaranı)

Ortamda ışık alanı yok ve kurmaya gerek de yok. Elimizde:
- Her hücrenin bir `color`'ı var
- Fotoreseptörde kullanılmayan bir `base_hue` alanı duruyor
- `can_see()` sadece `True/False` dönüyor

Yapılacak: `can_see()` gördüğü nesnenin **renk tonunu** da döndürsün. Renk
ayrık kutulara bölünsün (öneri: 6 ton kutusu). Böylece davranış genomu
"kırmızımsı olandan kaç, yeşilimsi olana yaklaş" diyebilir.

Bu üç uyaran içinde **en ucuzu** — difüzyon yok, yeni alan yok.

---

## Kararlar (tartışma sonucu — kapandı)

1. **Saldırı organları hem baştan hem sonradan.** Launcher'ın organ editöründen
   oyun başlamadan varlıklara eklenebilir. Eklenmemişse de hepsi avlanma ödülü
   çekilişinin havuzunda bulunur — yani evrim de keşfedebilir.

2. **Kaotropi gerçek hücre oluyor.** Zar bütünlüğü, enerjisi, organları ve
   gerçek silahları olacak. Artık çevresel tehlike değil, ekosistemin üçüncü
   oyuncusu. *(Bu, `Kaotropi`'nin `Entity`'den `Organism`'e taşınması demek —
   Aşama 2'nin en büyük kalemi.)*

3. **Savunma = zar özelliği**, organ değil. Kapsül/duvar/efflux hücrenin
   tamamını sarar, konumu yoktur. İskelet geninde yer kaplamaz.

4. **Toksin doğadaki gibi davranır.** Bakteriosinlerde üretici hücre bir
   *bağışıklık proteini* taşır: kendi toksinine karşı bağışıktır ve **aynı
   toksin genini taşıyan herkes** de bağışıktır. Taşımayan herkes zarar görür.
   Sonuç: açık bir akraba tanıma kodu yazmadan, gen paylaşımı üzerinden
   kendiliğinden soy-içi işbirliği doğar. Geni mutasyonla kaybeden yavru
   kendi soyunun toksininden ölebilir.

5. **Leşe ilk varan alır.** Ölen hücre yerine besin bırakır; öldürenin
   önceliği yoktur. Leş kargalığı davranışına alan açar.

6. **Hasar enerji yakmaz**, yalnızca zar bütünlüğünü düşürür.
   - Saldırı organları **kullanım anında** enerji harcar
   - Zar savunma geliştirmeleri **sürekli** enerji harcar (bakım gideri)

---

## Ölçüm planı

Her aşamadan sonra, tek koşuya güvenmeden (sabit tohum + çok koşu):

| Aşama | Ölçülecek |
|---|---|
| 1 | Doğum/ölüm devir hızı; donmuş hücre kalmıyor mu |
| 2 | Ortalama zar bütünlüğü; ölüm sebeplerinin dağılımı |
| 3 | Saldırı/savunma kombinasyonlarının popülasyondaki payı — **tek bir kombinasyon baskın hale geliyorsa matris dengesiz demektir** |
| 4 | Renk sınıflarının dağılımı |

Aşama 3'ün asıl testi bu: eğer herkes aynı silah+zırhı seçiyorsa taş-kağıt-makas
çalışmıyor, sayıları yeniden ayarlamak gerekir.
