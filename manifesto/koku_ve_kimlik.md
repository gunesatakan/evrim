# Koku, Kimlik ve Davranış — Uygulanan Mimari

> **Durum:** Uygulandı ve ölçüldü
> **Kapsam:** Hücrelerin birbirini nasıl tanıdığı ve davranışın nasıl evrimleştiği
> **Not:** Buradaki her sayı ölçümdür, tahmin değil. Negatif sonuçlar da yazılıdır.

---

## 0. Çözülen problem

Davranış genomu başlangıçta `(uyaran, sınıf, seviye) → tepki` tablosuydu ve
**evrimleşmiyordu**. Ölçüldüğünde sebep netti:

- Koku uyaranının 18 satırı hiç okunmuyordu (ölü ağırlık)
- Skaler koku alanı **kimlik taşımıyordu**: besin, av ve avcı aynı sayıya
  yazıyordu. Üstelik kaotropi bir besinin 8 katı koku yayıyordu, yani
  kemotaksis hücreyi besin sanıp avcıya sürüklüyordu.
- Tablo 72 satırdı; her karşılaşma 72 satırdan *birini* bilgilendiriyor, o
  satır nadiren tekrar ediyordu. Sürüklenme sinyali siliyordu.

---

## 1. Üç kanal, üç ayrı soru

| kanal | soruyu cevaplar | kalıcılığı | yalan söylenir mi |
|---|---|---|---|
| **Koku puanı** | *Ne kadarsın?* | genomla birlikte kademeli değişir | hayır |
| **Soy imzası** | *Kimden geldin?* | eşik aşılana kadar sabit | evet (taklit) |
| **Kairomon** | *Ne yaptın?* | söner (~12,5 sn) | hayır |

Tehlike bilgisini taşıyan tek kanal kairomondur: zırh *seni öldürmenin ne
kadar zor olduğunu* söyler, *senin ne kadar tehlikeli olduğunu* değil.

---

## 2. Koku puanı — sürekli eksen

`systems/signaling/scent_profile.py`

Puan, organların ağırlıklı toplamıdır ve **gelişimle ölçeklenir**:

```
katkı = taban_ağırlık × (gelişim_niteliği / taban_değer)
```

Stilet 2,0 · Fagositoz 3,0 · Gövde 1,0 · Flagella 0,8 · Vakuol 0,2

Geliştirilmiş bir stilet 2,0'ın üstüne çıkar. Ölçülen başlangıç değerleri:
Kaotropi **8,10** · Notropi **3,48** · Optropi **2,85**.

### Neden mutlak değil, göreli okunuyor

Herkes geliştikçe puanlar şişer; sabit eşikler eskirdi. Bu yüzden algılayan
hücre kendi puanına **oranla** okur:

```
x = 50 + 25·log₂(hedef_puanı / kendi_puanım)     [0, 100] arasına kırpılır
```

Eşit → 50 · İki katım → 75 · Yarım → 25

Böylece herkes birlikte büyüdüğünde oranlar sabit kalır ve koku "herkes için
farklı değer" taşır: aynı hücre küçüğe devasa, iriye önemsiz kokar.

### Neden ayrık sınıf terk edildi

Önceki tasarımda koku 6 ayrık sınıftı ve eşik aşılınca bir anda başka sınıfa
atlıyordu — ölçüldü: ortalama 8,4 bölünmede bir **hiç tanımadık biri**
beliriyordu. Gerçekte akrabalık kademelidir.

Sürekli eksende ölçülen süreklilik:

| | tohum 5 | tohum 11 |
|---|---|---|
| Bölünmede koku değişimi (ortanca) | %1,6 | %1,7 |
| %20'den fazla değişen | %0 | %0 |
| **Davranışın döndüğü doğum** | **%3** | %1 |

---

## 3. Davranış — dayatılmış aralık yok

`BehaviorGenome.scent_cuts` (4 kesme) + `scent_bands` (5 tepki)

Hücre ekseni kendi kesme noktalarıyla böler **ve her banda kendi tepkisini
atar**. İkisi de gendir, ikisi de evrimleşir.

"Zayıfa saldır, güçlüden kaç" bir varsayım olarak **dayatılmaz**. Çıkarsa
kendiliğinden çıkar; tersi de evrimleşebilir.

Kesme noktaları mutasyonda **sıçramaz, kayar** (`SPECTRUM_MUTATION_SIGMA`).
Ayrık tabloda mutasyon "rastgele başka bir tepkiye dön" olduğu için seçilim
rastgele yürüyüş yapıyordu; sürekli eksende eğim tırmanabilir.

---

## 4. Soy imzası — kilit ve anahtar

`systems/signaling/lineage.py`

Sentaz (imza) + reseptör (anahtar). Gerçekte luxI/luxR operonda yan yanadır
ve birlikte kalıtılır. Sentaz tek başına değişirse hücre kendi akrabasını
tanıyamaz hâle gelir.

İmzayı **zar atışı değil, biriken ıraksama** değiştirir:

```
her bölünmede: genom mutasyonları + tablo değişimleri + gelişim ağırlığı
                → biriktir; eşik (30) aşılırsa yeni imza
```

Ölçülen birikim: bölünme başına ~5,1 · yeni organ +5,0 · gen kademesi +1,0

Eşik aşıldığında %70 ihtimalle kilit ve anahtar birlikte kayar; kalan %30'da
yalnız biri değişir ve sinyalleşme kırılır.

---

## 5. Kairomon — diyet kaynaklı sızıntı

Feromondan ve allomondan farkı, faydanın **alıcıya** gitmesidir: yayan taraf
zarar görür ama **bastıramaz**, çünkü sinyal değil artıktır. Avlanmanın
bugüne kadar hiç olmayan bedeli budur.

*Daphnia* balık kairomonunu algılar ve tepkisi, balığın **yakında Daphnia
yemiş olmasıyla** orantılı olarak güçlenir.

Sızıntı **leş yemekle** üretilir — çünkü avcıların çoğu avını doğrudan
yutmaz: stiletle öldürür, leş besine dönüşür, sonra onu yer. Bu kanca ilk
uygulamada `consume_prey`'e bağlanmıştı ve **kaotropinin kairomonu sıfır
çıktı**; ölçüm hatayı yakaladı.

Düzeltme sonrası ortalama sızıntı: Kaotropi **1,585** · Optropi 0,120 ·
Notropi 0,039 — avcı avdan kırk kat fazla.

---

## 6. Ekosistem kararlılığı — ölçmenin önkoşulu

Uzun süre hiçbir evrimsel sinyal ölçülemedi. Sebep mutasyon yükü değildi
(8 kat düşürüldü, değişmedi); **nüfus çökmesiydi**. Kaotropi sayısı 16'dan
8'e indirildi — ölümlerin %75-80'i stiletten geliyordu.

Aynı 5 tohumda, aynı kodla:

| | kao=16 | kao=8 |
|---|---|---|
| Ortalama son nüfus | 36 | **156** |
| Tohumlar arası değişkenlik | %61 | **%39** |
| Çöken tohum | 1/5 | **0/5** |
| En kötü tohum | 18 | **65** |

Sürüklenme 1/N ile ölçeklendiği için en kötü durumun 18'den 65'e çıkması
gürültüyü kabaca dörtte birine indirdi. Stilet ölüm payı %45-79'dan
%33-64'e indi: avcı baskısı azaldı ama **kaybolmadı** - seçilim baskısı
korundu.

---

## 7. İlk tutarlı evrimsel sinyal

Kararlı ekosistemde, 5 tohum × 120 sn. Değerler "kaç" tepkisinin yüzde
puan değişimi:

| eksen konumu | 5 | 11 | 23 | 41 | 59 | tutarlılık |
|---|---|---|---|---|---|---|
| 10 (çok küçük) | −22 | −3 | +31 | −1 | −8 | 4/5 ↓ |
| **30 (yarım)** | +21 | +22 | +55 | +9 | +27 | **5/5 ↑** |
| 50 (eşit) | +27 | +6 | +9 | −1 | +14 | 4/5 ↑ |
| **70 (iri)** | −17 | −4 | −1 | −7 | −13 | **5/5 ↓** |
| 90 (çok iri) | −15 | −8 | −20 | +2 | −11 | 4/5 ↓ |

Kesme noktaları da tutarlı biçimde **aşağı göçüyor**:
`[23,41,61,83] → [20,41,52,69]`, `[17,35,58,82] → [7,21,36,62]`.

**Popülasyon kendinden iri olandan kaçmayı BIRAKIYOR.** Beklenenin tersi.

Tek bir konum için işaret testi p≈0,06, yani tek başına sınırda. Ama üç
bağımsız gözlem aynı yönü gösteriyor: iki konumda 5/5, komşularda 4/5, ve
kesme noktalarının göçü.

### Neden ters yönde — hipotez

Gözlemlerin **%55'i x>70**: hücreler çoğunlukla kendilerinden iri şeylerle
karşılaşıyor. "İriden kaç" kuralı, zamanın yarısından fazlasını kaçarak
geçirmek demek - ve kaçmak yememek demek. Açlık hâlâ ciddi bir ölüm nedeni.

Kesme noktalarının aşağı göçü bunu destekliyor: üst bant genişleyip yaygın
durumu kapsıyor ve o bandın tepkisi "kaç"tan uzaklaşıyor.

**Doğrulanmadı.** x=30'daki tutarlı artış (5/5) ise henüz açıklanamıyor;
saf sürüklenme olsa beş tohumda aynı yönde çıkmazdı.

---

## 8. Gruplaşma — birden fazla yaşam biçimi bir arada

Önceki bölümlerdeki ölçümler **popülasyon ortalamasına** bakıyordu ve bu,
"herkes biraz değişti" ile "yarısı tamamen değişti" arasını ayırt edemez.
Ayırt eden ölçüm (3 tohum × 120 sn), her hücreyi baskın stratejisine göre
etiketler:

| baskın strateji % | tohum 5 | tohum 11 | tohum 41 |
|---|---|---|---|
| **flee** | 24 → 21 | 50 → **15** | 15 → **2** |
| **attack** | 24 → **5** | 26 → **54** | 38 → 32 |
| **approach** | 29 → **43** | 9 → 6 | 32 → **47** |
| **ignore** | 24 → 30 | 15 → 26 | 15 → 19 |
| Farklı strateji | 4/4 | 4/4 | 4/4 |
| En büyük grup | %43 | %54 | %47 |
| **Soy içi strateji birliği** | **%82** | **%85** | **%67** |

### Üç tohumda da tutarlı

**Kaçma her zaman kaybediyor** (−3, −35, −13). Bölüm 7'deki bulguyla
uyuşuyor: kaçmanın besin bedeli var (−%2 ile −%31), koruma faydası **yok**
(stilet ölüm oranı kaçanla kaçmayanda birebir aynı: %17/%18, %16/%13,
%42/%41). Bedeli olup faydası olmayan davranış elenir.

**Dört strateji birlikte yaşıyor.** En büyük grup asla %54'ü geçmiyor.
Tek bir optimuma yakınsama yok — gerçek polimorfizm.

**Strateji kalıtsal olarak tutunuyor.** Soy içi birlik %67-85; dört
strateji arasında rastgele dağılım ~%25-40 verirdi. Yani gerçekten
"kaçıcı soylar" ve "saldırgan soylar" oluşuyor.

### Kazanan tohuma göre değişiyor

Tohum 5'te saldırganlık çöktü, yaklaşma kazandı. Tohum 11'de kaçma çöktü,
saldırganlık kazandı (%54). Aynı kod, aynı ayarlar, farklı sonuç:
**evrimsel olumsallık**.

### Bu, daha önceki "tutarsızlık"ı da açıklıyor

Oturum boyunca tohumlar arası tutarsızlık diye raporlanan şeyin bir kısmı
gürültü DEĞİLDİ. Ortalamaya bakılıyordu; altta zıt yönlerde uzmanlaşmış
gruplar vardı. Bir tohumda kaçıcıların, diğerinde saldırganların elenmesi
ortalamayı zıt yönlere çekiyordu. **Ortalama, gruplaşmayı gizliyordu.**

---

## 9. Ölçülen ama ÇÖZÜLMEMİŞ olanlar

Bunlar dürüstçe kayıtlıdır; ileride buradan devam edilmelidir.

### x=30'daki artış açıklanamıyor
Beş tohumda da "kaç" artıyor (+9 ile +55 arası). Saf sürüklenme değil ama
sebebi bilinmiyor. Bakılacak ilk yer burası.

### Denenen ve işe yaramayan: mutasyon yükü
`BEHAVIOR_MUTATION_RATE` 8 kat düşürüldü (0,04 → 0,005), sonuç değişmedi.
Sorun mutasyon oranı değil, nüfus büyüklüğüydü.

### Değişkenlik azaldı ama bitmedi
%61'den %39'a indi ve çökme kalmadı, ama nüfus hâlâ 65 ile 225 arasında
savruluyor. Ölçüm artık mümkün; kesinlik için hâlâ çok tohum gerekiyor.

### Eksen çarpık
Görülen konumların ortalaması 65-69 ve %55'i 70'in üstünde — hücreler
çoğunlukla kendilerinden iri şeylerle karşılaşıyor. Eksenin **alt ucu
neredeyse hiç kullanılmıyor**, o bantlar seçilime girmeden sürükleniyor.

### Akraba tanımanın faydası yok
Kırık sinyalleşmenin ölçülebilir cezası çıkmadı. Gerçekte kuorum duyusu
maliyetli **ortak davranışları** tetikler (biyofilm, virülans); burada
eşgüdümlenecek bir şey olmadığı için kilit-anahtar korunmasını yaratan
seçilim baskısı da yok.

### Işık bu eksene oturmuyor
Renk tonu daireseldir — 350° ile 10° komşudur, "daha fazla" yoktur. Ses,
koku ve kairomon sıralanabilir; ışık kategorik kaldı.

### Kaçmanın neden işe yaramadığı bilinmiyor
Menzil hesabı kaçmanın çalışması gerektiğini söylüyor: av avcıyı 70 px'ten
algılıyor, stilet 38,5 px'te vuruyor, yani 31,5 px uyarı payı var - ve av
daha hızlı (117,6 / 100 px/sn). Ama ölçüm kaçmanın koruma sağlamadığını
söylüyor. Aday açıklamalar, sınanmamış:

- Kaçma tepkisi uyaran yarışını kaybediyor olabilir (`(seviye, -mesafe)`
  ile en güçlü uyaran seçiliyor; yakındaki başka bir hücre kazanabilir)
- Dönüş hızı 31,5 px'lik payı tüketiyor olabilir
- `try_bind` temas anında avı hareketsiz bırakıyor
- Birden fazla tehdit varsa birinden kaçarken diğerine gidiliyor olabilir

### Ayar silme hatası - ders
`game_settings.py`'de iki işaret arasını toptan değiştiren bir düzenleme,
arada duran `KAIROMONE_*` ayarlarını sildi. Oyun `settings.json`'ı yeniden
yazınca oradan da düştüler. Sonuç: leş yiyen ilk hücrede çökme - ve
`COST_SLIP` hiç tanımlanmadığı için `base_energy_cost` her karede çöküyordu.

Kısa doğrulama koşuları bunu YAKALAMADI (leş yenmeden önce bitiyordu) ve
`compileall` de yakalamaz, çünkü sözdizimi değil çalışma zamanı hatası.

**Kural:** ayar ekleyen/silen her düzenlemeden sonra kodda geçen tüm
`game_settings.X` referanslarını tarayıp `hasattr` ile doğrula. Bu tarama
6 eksik ayar buldu.