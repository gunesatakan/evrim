# Katman–İğne Fiziği: Saldırı, Savunma ve Ölüm

> **Durum:** Tasarım — uygulanacak
> **Kapsam:** Hücre dış katmanları, enjekte edilebilir moleküller, birleşik delme formülü
> **İlke:** Kimyasal süreçler basitleştirilir (etki + direnç). **Fiziksel etkileşimler gerçekçi simüle edilir.**

---

## 0. Neden yeniden kuruluyor

Mevcut sistemde tek bir `integrity` sayısı ve `1/(1+direnç)` formülü var. Bu formül
**asla sıfır vermiyor**, yani "bu saldırı bu savunmaya karşı imkânsız" ifade edilemiyor.

Oysa gerçek ölüm mekanizmalarının çoğu birikimli hasar değil, **eşik**:

- Zar delindiği an turgor (1-5 atm) boşalır, ölüm bir saniyeden kısa sürer
- Efflux pompası giriş hızından hızlıysa hücre asla zehirlenmez
- Hedef yeterince büyükse asla yutulamaz

Ayrıca ölçüldü ki mevcut sistemde **kademeli zırhlanma cezalandırılıyor**: duvar 2 olan
hücre duvar 0 olandan daha çok ölüyordu (7/12 ve 4/12), çünkü hız cezası koruma
kazancını aşıyordu. Eşik mantığı bu çukuru kapatır — küçük yatırım bile zayıf
delicilere karşı **tam bağışıklık** verir.

---

## 1. Üç derinlik

Saldırılar yükü **nereye** bıraktığına göre ayrılır ve her derinlik farklı bir
fiziksel bariyerle karşılaşır.

| derinlik | ne yapıyor | gerçek örnekler |
|---|---|---|
| **0 — Yüzeye tutunma** | Delmez. Yapışır, dışarıdan emer ya da üstüne enzim boşaltır. | *Vampirococcus lugosii*, *Micavibrio*, *Bdellovibrio exovorus*, Didinium toksikistleri |
| **1 — Zarın içine** | Lipit çift katmana gömülür, orada gözenek açar. | α-hemolizin, amoebapor, perforin, antimikrobiyal peptitler |
| **2 — Tam geçiş** | Zarı delip sitoplazmaya ulaşır. | T3SS/T4SS injektizomu, nematosist, *Bdellovibrio bacteriovorus* |

**Kritik nokta:** derinlik 0 tutunamazsa hiç başlamaz. Delme gücü konu dışıdır.

---

## 2. Katmanlar (dıştan içe)

| # | katman | parametreleri | asıl işi |
|---|---|---|---|
| 1 | **Mukus / salgı** | kalınlık, viskozite, **atılabilirlik** | yapışmayı engeller, enzimi hapseder, soyulup atılabilir |
| 2 | **Kapsül** (bağlı glikokaliks) | kalınlık, yoğunluk | yapışmayı engeller, sterik mesafe |
| 3 | **S-layer** (protein kristali) | **gözenek boyutu**, kayganlık | küçük molekül eleği, yüzey kayganlığı |
| 4 | **Duvar** (peptidoglikan/selüloz/silis) | kalınlık, **mukavemet**, **gözenek boyutu** | mekanik zırh **ve** moleküler elek |
| 5 | **Hücre zarı** (lipit çift katman) | **paketleme**, esneklik, gerilim | son bariyer; moleküler yerleşmeye üstel direnç |

**O-antijen zincirleri** katman değil, 4-5'in üstündeki uzantıdır. Tek işi
*sterik erişim*: iğnenin boyu zinciri aşamazsa ana zara ulaşamaz.

### Duvarın İKİ bağımsız özelliği

Mukavemet mekaniği durdurur, **gözenek boyutu** molekülü durdurur. Bunlar ayrı
sayılardır ve tek bir `wall` değerine indirilemez.

Gerçekte tam bağımsız değiller: çapraz bağ artınca hem sağlamlaşır hem gözenek
küçülür; kusurlar artınca hem zayıflar hem gözenek büyür. **Kalınlık** ise ayrışır —
kalın duvar mekanik olarak güçlüdür ama gözenek boyutunu değiştirmez, yalnızca
difüzyon yolunu uzatır.

---

## 3. Enjekte edilebilir moleküller

Duvarın eleme sınırı **~22-24 kDa** (gözenek yarıçapı ~2,0-2,5 nm).

| molekül | hedef bölge | boyut | etkisi | duvarı geçer mi |
|---|---|---|---|---|
| İyon / proton | hücre içi | <0,5 kDa | iyon dengesi çöker | evet |
| Antimikrobiyal peptit | **zar içi** | 2-5 kDa | gözenek | evet |
| Nörotoksin | **zar yüzeyi** (kanal) | 3-8 kDa | kanal blokajı, felç | evet |
| Amoebapor | **zar içi** | ~8 kDa | gözenek | evet |
| Küçük bakteriosin | **zar içi** | 3-10 kDa | gözenek | evet |
| Lizozim / litik enzim | **duvar** | ~14 kDa | duvarı çözer | evet |
| α-hemolizin | **zar içi** | ~33 kDa | gözenek | **hayır** |
| Proteaz | **zar yüzeyi** | 20-50 kDa | yüzey proteinlerini sindirir | sınırda |
| T3SS efektörü | **hücre içi** | 20-70 kDa | iç sabotaj | **hayır** |
| Perforin | **zar içi** | ~67 kDa | gözenek | **hayır** |

### Taşıyıcı/yük ayrımının fizik temeli

Bu tablonun sonucu: **yükün boyutu hangi taşıyıcının zorunlu olduğunu belirler.**

- Küçük yük → duvardan kendi geçer, difüzyon yeter, taşıyıcı gerekmez
- Büyük yük → duvarı asla geçemez, **mekanik olarak enjekte edilmek zorunda**

Gerçekte T3SS/T4SS moleküler şırıngalarının var olma sebebi tam budur: kendi başına
asla içeri giremeyecek büyük efektör proteinleri taşımak.

Silah artık tek şey değil, bir **çift**: `(taşıyıcı, yük)`. Aynı nörotoksini biri
stiletle saplayıp verir, öteki zıpkınla fırlatıp verir. Farklı fizik, aynı kimya.
Hücrenin **önce yükü üretmesi**, sonra taşıyıcıya sahip olması gerekir — ayrı gen,
ayrı maliyet.

---

## 4. BİRLEŞİK FORMÜL: katman–iğne etkileşimi

Moleküler yerleşme ve mekanik delme **ayrı sistemler değildir**. İkisi de aynı
denklemin uçlarıdır; fark **enerji miktarı ve deneme deseni**:

- Moleküler yerleşme: düşük enerji (ısıl, ~kT), devasa deneme sayısı
- Mekanik delme: yüksek enerji (kinetik, ~10⁴ kT), tek deneme

### Delici dört sayıyla tanımlanır

```
E  = taşıdığı enerji       (molekülde ısıl, mermide kinetik)
A  = uç kesit alanı        (basıncı belirler)
d  = etkin çapı            (elekten geçebilir mi)
N  = saniyedeki deneme     (difüzyonda milyonlarca, atışta 1)
```

### Katman üç sayıyla

```
mesh = gözenek çapı        (0 = delik yok)
B    = birim alan bariyer enerjisi
t    = kalınlık
```

### Geçiş

```
1. ELEK:   d <= mesh  ->  bedavaya geçer (yalnızca t kadar gecikir)

2. YARMA:  gereken = B * A * t
           P_tek = 1                             eğer E >= gereken
           P_tek = exp(-(gereken - E) / E_ref)   eğer E < gereken
           P_toplam = 1 - (1 - P_tek)^N
```

`E_ref` **küçük** seçilir. Böylece üstel kapı keskin çalışır: enerji eşiğin biraz
altındaysa olasılık pratikte sıfırdır — "imkânsız" gerçekten imkânsız olur.

### Dört durum, tek formül

| durum | sonuç | neden |
|---|---|---|
| Küçük peptit → duvar | serbest geçer | `d <= mesh` |
| Büyük toksin → duvar | **asla geçemez** | `d > mesh`, E ısıl, N büyük ama üstel sıfır |
| Nematosist → duvar | geçer | `d > mesh` ama `E >= gereken` |
| Gözenek toksini → çift katman | paketlemeye bağlı | mesh yok, E ısıl, üstel kapı |

### Neden paketleme birine üstel, ötekine doğrusal etki eder

Aynı parametre iki farklı yere giriyor:

```
YERLEŞME:  olasılık = e^(-engel/kT)     -> paketleme ÜSTELDE
DELME:     gereken  = B*A*t             -> paketleme TOPLAMDA
```

Ölçüm: çift katmanın delinme kuvveti 1-30 nN, kalınlığı ~5 nm → iş ≈ 5×10⁻¹⁷ J.
Isıl enerji (kT) ≈ 4×10⁻²¹ J. Arada **~10⁴ kat** var.

Bu yüzden çift katman geçirgenlik bariyeri olarak mükemmel, mekanik bariyer olarak
berbattır. Mekanik korunma gereken her canlı zarın **dışına ayrı bir duvar** inşa
etmiştir: bakteride peptidoglikan, bitkide selüloz, mantarda kitin, diyatomede silis.

---

## 5. Tutunma — ayrı ve ön koşul

Tutunma enerji eşiği değildir; farklı parametreler belirler:

```
TUTUNMA = f(yüzey sürtünmesi, mukus kalınlığı, çarpma açısı)

açı > kritik_açı(sürtünme)  ->  seker, temas kurulamaz
mukus çok kalın             ->  köprü kurulamaz
```

Başarısızsa yukarıdaki delme formülü **hiç çalışmaz**. Delici ne kadar güçlü olursa
olsun, ısıramadıysa enerjisi anlamsızdır.

### Kayganlık ÇİFT YÖNLÜDÜR

İğne penetrasyon literatürü: toplam kuvvet = uçtaki kesme + şaft boyunca sürtünme.
İğneyi yağlamak batırma kuvvetini **düşürür**.

| aşama | kayganlık kimin lehine |
|---|---|
| Delme öncesi | **savunan** — uç tutunamaz, kuvvet tek noktada toplanamaz |
| Eğik çarpma | **savunan** — sürtünme yok, mermi "ısıramaz", seker |
| Delme sonrası | **saldıran** — şaft sürtünmesi az, içeri kolay girer |

Yani kayganlık monoton bir savunma puanı değil, **gerçek bir ödünleşim**: kaygan
hücre ilk vuruşu savuşturur ama delinirse çabuk gider.

---

## 6. Ölüm nedenleri — fizik temelli kategoriler

Mevcut sistemde ölüm nedenleri mekanizma değil etiket: `stylet`, `toksin`, `aclik`.
Yani "beni ne vurdu", "nasıl öldüm" değil.

| # | kategori | ne oluyor | fiziksel büyüklük | tip |
|---|---|---|---|---|
| **A** | **Mekanik yarılma** | zar delinir, turgor boşalır | delme enerjisi vs bariyer | **EŞİK** |
| **B** | **Ozmotik çöküş** | zar geçirgenleşir, su dolar, patlar | gözenek akısı vs pompa | birikimli |
| **C** | **Dış sindirim** | zar dışarıdan enzimle erir | enzim × temas süresi | birikimli |
| **D** | **Metabolik durma** | yapı sağlam, makine durur | giriş hızı vs efflux | **EŞİK** |
| **E** | **Yutulma** | bütün alınır, asit+ROS ile sindirilir | boyut oranı, katılık | **EŞİK** |
| **F** | **Açlık** | saldırgan yok, enerji biter | enerji dengesi | birikimli |

**Altı kategoriden üçü eşiktir.** Mevcut HP modeli bunları ifade edemez.

---

## 7. Savunma matrisi — onay değil, ağırlık

| savunma | derinlik 0 | derinlik 1 | derinlik 2 |
|---|---|---|---|
| **Kayganlık** | **çok güçlü** | zayıf | **çift yönlü** |
| **Zar paketleme** | zayıf | **çok güçlü** (üstel) | var ama küçük |
| **Duvar gözeneği** | — | **çok güçlü** (elek) | — |
| **Duvar mukavemeti** | — | — | **çok güçlü** |
| **Sterik engel** (O-antijen) | **güçlü** | orta | **güçlü** |
| **Veziküi atma / ESCRT** | — | **güçlü** (sonradan) | orta |

Hiçbiri sıfır değil, hiçbiri her yerde güçlü değil. Matris kodlanmaz — derinlikten
ve formülden kendiliğinden çıkar.

---

## 8. Eksik savunmalar (henüz yok)

| savunma | neye karşı |
|---|---|
| Viskoelastik zar | mekanik basıncı esneyerek emer |
| Sıkı lipit paketleme (sterol) | gözenek açıcı peptitler |
| Veziküi atma / pore-endositoz | açılan deliği koparıp atma |
| Proteaz inhibitörü | dış sindirim enzimleri |
| Ecdysis (dış kabuk soyma) | yapışan toksin |
| Reseptör konformasyon değişimi | kilit-anahtar toksinleri |
| Lizozomal direnç | yutulduktan **sonra** hayatta kalma |

---

## 9. Dürüstlük notları

**S-layer tartışmalı.** Uzun süre *Caulobacter crescentus*'un S-layer'ının
*Bdellovibrio exovorus*'a karşı koruduğu kabul edildi; 2025 tarihli bir çalışma
avcı ve avın dış zarlarının sıkı temas kurduğunu gösterip bu rolü sorguluyor.
"Kaygan yüzey saldırıyı tamamen durdurur" mutlak alınmamalı.

**Sayılar mertebe hesabıdır.** Kesin değerler lipit bileşimine, iyonik güce,
sıcaklığa göre değişir. Aradaki ~10⁴ katlık uçurum sağlamdır; ondalıklar değil.

---

## Kaynaklar

- [Vampirococcus lugosii — reductive evolution and unique predatory mode](https://www.nature.com/articles/s41467-021-22762-4)
- [Strategies and mechanisms of contact-dependent predation in bacteria](https://www.sciencedirect.com/science/article/pii/S136952742500061X)
- [Intrinsic repair protects cells from pore-forming toxins by microvesicle shedding](https://www.nature.com/articles/cdd201711)
- [Mechanisms protecting host cells against bacterial pore-forming toxins](https://link.springer.com/article/10.1007/s00018-018-2992-8)
- [Lifecycle of a predatory bacterium vampirizing its prey through the cell envelope and S-layer](https://www.nature.com/articles/s41467-024-48042-5)
- [Interrupting peptidoglycan deacetylation during Bdellovibrio predator-prey interaction](https://www.nature.com/articles/srep26010)
- [The Bacterial Surface Layer Provides Protection against Antimicrobial Peptides](https://aem.asm.org/content/78/15/5452)
- [Peptidoglycan structure and architecture](https://academic.oup.com/femsre/article/32/2/149/2683904)
- [Cell shape and cell-wall organization in Gram-negative bacteria](https://www.pnas.org/doi/10.1073/pnas.0805309105)
- [Cations and lipid bilayer nanomechanics — AFM puncture forces](https://www.tandfonline.com/doi/full/10.3109/09687688.2013.868940)
- [Multifrequency AFM: cholesterol modulating membrane viscoelasticity](https://www.pnas.org/doi/10.1073/pnas.1719065115)
- [Needle–tissue interaction forces](https://sciencedirect.com/science/article/abs/pii/S002192901400431X)
- [Low-friction coating for suture needles](https://www.sciencedirect.com/science/article/pii/S0169433226001340)

---

## Etki sınıfları — doz *şiddeti* belirler, molekül *türü* belirler

İlk denemede tek bir merdiven vardı: `yavaşlatma → felç → ölüm`, ve her
moleküle aynen uygulanıyordu. Bu yanlıştı. Orta dozda **her şey felç
ediyordu** — gözenek açıcı bir peptit de, lizozim de. Oysa:

- gözenek açıcı iyon kanalı bloke etmez, **zarı sızdırır**;
- lizozim siniri değil **duvarı** çözer.

Doğrusu: **doz şiddeti ölçekler, molekülün sınıfı etkinin türünü belirler.**
Her sınıfın kendi üç kademesi var.

| sınıf | mekanizma | düşük doz | orta doz | ölümcül |
|---|---|---|---|---|
| **nörotoksin** | kanal blokeri | yavaşlama | **FELÇ** | ölüm |
| **gözenek** | zarda delik, su girer | sızdıran zar | **ŞİŞME** | ozmotik lizis |
| **litik** | duvarı çözer | duvar zayıfladı | **DUVAR İNCELDİ** | duvar çöktü |
| **sabotaj** | nükleaz/NADaz | metabolik yavaşlama | **ÜREME DURDU** | iç çöküş |

Molekül dağılımı: nörotoksin → Nörotoksin; gözenek → Antimikrobiyal peptit,
Amoebapor, α-hemolizin, Perforin; litik → Lizozim; sabotaj → T3SS efektörü.

### Neden orta kademe önemli

Orta doz **kombinasyon kapısı açıyor**. Litik enzimin orta dozu duvarı
6.0 → 2.1'e indiriyor ama çökertmiyor (`weakened` bayrağı %35'te
kilitliyor). Yani tek başına öldürmeyen bir salgı, *sonraki mekanik
saldırının* önünü açıyor: yumuşat, sonra del. Bu, tek merdivenli
tasarımda hiç var olamayacak bir strateji.

### Yakalanan hatalar

- **Ölümcül doz orta doz bayraklarını temizlemiyordu.** Önce orta doz
  lizozim yemiş bir hücrede `weakened=True` kalıyordu; duvar %35'te
  kilitlendiği için ölümcül doz gelse bile asla çökmüyordu.
- **HUD, hücrenin almadığı dozu yazıyordu.** `last_dose`/`last_tier`
  bölge kontrolünden *önce* atanıyordu, dolayısıyla hedef katmanını
  ıskalayan bir atış için ekranda "ozmotik lizis" görünüyordu. Artık
  yalnızca yük hedef bölgesine vardığında yazılıyor; ıskalayınca 0.
- **Ölümcül nörotoksin, felç dozundan ayırt edilemiyordu.** İkisi de
  `felc` görselini tetikliyordu. Patlamayan ölümler için ayrı bir
  `dead_cell` durumu eklendi (karartma + "ÖLDÜ").

---

## Molekül sayımı — doz artık bir sayı değil, bir nüfus

Doz `CARRIER_DOSE[taşıyıcı] × POTENCY[molekül]` şeklinde bir basamak
fonksiyonuydu. Yedi ayrık değer, üç eşik — kademelerin çoğuna çıkacak yol
yoktu. Yerine **tekil molekül** geldi: ekranda çizilen her nokta bir
moleküldür, arka planda yoğunluk hesabı yoktur, **doz varan moleküllerin
sayısıdır**.

Bunun getirdikleri:

- Molekülün yolu, konumu, nerede takıldığı **doğrudan görünür**.
- Eşikler okunur: `alfa-hemolizin (7, 14, 28)` — yedi monomer bir gözenek
  yapar, bir gözenek sızdırır, ikisi şişirir, dördü patlatır. Yedi sayısı
  uydurma değil, heptamerin kendisidir.
- Moleküller **fırlatılmadan önce de vardır**: hücrenin gövdesinde
  taşınırlar, Brown hareketi yaparlar, ateş edince stoktan düşerler.
  Hücre patlarsa stok olduğu gibi **ortama saçılır** — toksin dolu bir
  hücreyi patlatmak onu kimyasal bombaya çevirir ve bu gözle görülür.

### Emergent hale gelen üç şey

Daha önce ayrı ayrı kodlanan üç kural artık fizikten çıkıyor:

**1. Difüzyonun zayıflığı** bir katsayı değil, **açıdır.** 180°'ye saçılan
26 molekülün ancak birkaçı hücrenin gördüğü açıya denk gelir. Ölçüm: aynı
mesafeden difüzyon ortalama **−1 px** yol alıyor (yarısı geriye gidiyor),
fışkırtma 312 px.

**2. Menzil** ayrıca uygulanan bir kontrol değil, **viskoz sürtünmenin**
sonucu: `v(t) = v₀·0.15^t`, menzil = `v₀/ln(1/0.15)`. Ölçülen menziller
beyan edilenlerle örtüşüyor (45→48, 170→156, 320→312).

**3. Nükleazın fışkırtma ile işe yaramaması** ayrı bir kontrol değil,
**elek.** 50 kDa'lık efektörün çapı 2.85, duvar gözeneği 2.2 — duvarda
takılır. İğneli salgı sistemlerinin var olma sebebi bu tek satırdır.

### Kendi hedefine varma kuralı düzeltildi

Eskiden `kDa <= 20` idi — **yanlış.** Belirleyici olan boyut değil,
**hedefin nerede olduğu.** Yüzeyde iş gören molekül (gözenek açıcı, kanal
blokeri, duvar enzimi) dışarı bırakılsa da varır: bağlandığı yapı zaten
dıştadır. Perforin 67 kDa ile en irisidir ama zarı *geçmesi gerekmez*,
üstüne oturur. Nükleaz ondan küçüktür ama geçmek *zorundadır*.

Ama "hedefini bulur" ≠ "her engeli aşar". Molekül yine elekten geçmek
zorundadır — ve tablo bunu gösteriyor:

| zarf | kabuk | difüzyon → nörotoksin | fışkırtma → α-hemolizin |
|---|---|---|---|
| tam zarf | 194 px | 0 vardı | 0 vardı, **26 duvarda takıldı** |
| mukus yok | 130 px | 0 vardı | 0 vardı, 26 takıldı |
| mukus+kapsül yok | 86 px | **11 vardı** | 0 vardı, 26 takıldı |
| sadece duvar+zar | 68 px | 26 vardı | 0 vardı, 26 takıldı |
| **sadece zar** | 14 px | 26 vardı | **26 vardı** |

İki gerçek sonuç: **zarf difüzyona karşı savunmanın kendisidir**, ve
**gözenek açıcılar ancak duvarsız hücrede iş görür** — α-hemolizin ile
perforinin hayvan hücrelerini hedeflemesinin sebebi budur.

### Yakalanan hatalar

- **Varış/elek sırası tersti.** Önce elek soruluyordu, dolayısıyla
  nörotoksin *hedefi olan* hücre zarına varamıyor, gözeneği 0 olan zarda
  "takıldı" diye duruyordu. Bir molekül üzerinde iş gördüğü katmanı
  geçmek zorunda değildir; varış önce sorulmalı.
- **Menzil moleküler taşıyıcılarda hiç uygulanmıyordu.** Mermi
  yaratmadıkları için eski menzil kontrolü devre dışı kaldı, moleküller
  900 px uçuyordu. Sürtünme ile çözüldü.
- **Stok yetmeyince enerji yine harcanıyordu** (`pay_shot` önce çağrılıyordu).
- **Panelde 26 molekül izahsız yok oluyordu.** "Temizlendi" ile
  "seyreldi" aynı duruma yazılmıştı; ayrıldı ve panel artık her molekülün
  hesabını veriyor.

---

## Gerçek gözenekler — elek artık bir karşılaştırma değil, geometri

`cap <= mesh` bir sayı karşılaştırmasıydı. Yerine **gerçek delikler** geldi:
her katmanın kendi gözenek geometrisi üretiliyor, çizilen delikler
molekülün geçtiği deliklerin ta kendisi. Çizim ile fizik aynı veri.

| katman | yapı | tabaka | delik | genişlik | açık |
|---|---|---|---|---|---|
| Mukus | dağınık jel | 1 | 6 | 217–305 px | %90 |
| Kapsül | dağınık | 1 | 10 | 64–119 px | %71 |
| **S-layer** | **kristal** | 1 | 28 | 18 px (hepsi eşit) | %44 |
| Duvar | yarı-düzenli | **3** | ~50 | 8–12 px | %53 |
| Hücre zarı | lipit çift katmanı | 1 | **yok** | — | %0 |

S-layer gerçekte iki boyutlu bir **protein kristalidir** — delikleri
düzenli ve üst üste hizalı. Mukus rastgele bir jeldir. `LAYER_ORDER` bu
farkı taşıyor; düzensiz katmanlarda delikler hem kayar hem genişlikleri
değişir, alt tabakaları hizalanmaz.

Sonuç, keskin bir eşik değil **kademeli boyut dışlaması** (tek molekül,
12 tohum):

| molekül | çap | varan |
|---|---|---|
| Antimikrobiyal peptit … Lizozim | 5.1 – 8.6 px | 12/12 |
| α-hemolizin | 11.4 px | **1/12** (en geniş deliği bulabilirse) |
| T3SS efektörü / Perforin | 13.1 / 14.5 px | 0/12 |

Gerçek gözenek dağılımları da eşik değil dağılımdır; α-hemolizinin arada
sıvışabilmesi doğru davranış.

### Yüzeye tutunma — aramayı mümkün kılan şey

Molekül geçemeyince savrulmaz: **arayüzde kalır ve teğet süpürür**, her
karede başka bir açıyı dener. Gerçekte bir molekül gözenekli bir yüzeye
saniyede milyarlarca kez çarpar; karede bir deneme yapabildiğimiz için
temas süresince kayarak aynı işi yapıyor. Ekranda görünen de tam bu:
molekülün duvar boyunca kayıp bir deliğe kayıvermesi.

Ölçüm — tek nörotoksin molekülünün tabaka tabaka deneme sayısı:
`S-layer 3, duvar 3 / 5 / 3` — her birinde birkaç deneme sonra geçti.

### Yakalanan hatalar (hepsi ölçümle bulundu, hiçbiri gözle)

1. **Sekme molekülün hızının %90'ını yok ediyordu** — tek çarpışma
   ölümdü. Fizik hatası: sürtünme *yönlü* hızı söndürür, ısıl çalkantı
   sönmez, o sıcaklığın kendisidir.
2. **"Isıl taban" yönü koruyordu** — molekül bir kez sekince 52 px/s ile
   düz bir çizgide sonsuza gidiyordu. O difüzyon değil savrulma. Hız
   `drift` (sönen) + `jig` (yönü sürekli yeniden örneklenen) diye ikiye
   ayrıldı.
3. **Sekmenin dışa bileşeni** molekülü zarftan atıyordu; S-layer toplam
   **bir kez** deneniyordu. Radyal ilerlemeyi artık yalnız ısıl çalkantı
   sağlıyor.
4. **Elek tek yönlüydü** — içeri girmek zordu ama dışarı çıkmak bedavaydı.
   Gerçek bir gözenek iki yönü de kısıtlar; molekülün katmanda hapsolması
   aramayı mümkün kılan şeyin kendisi.

Ölçek notu: hücre ~10× büyütülmüş çizildiği için ısıl hız da ölçeğe
uyarlandı (`THERMAL = 240 px/s`). Gerçekte bir protein bakteri zarfını
mikrosaniyelerde geçer; burada saniyeler sürüyor ki izlenebilsin.

---

## Ölüm sonrası reset — hasar ile kullanıcı ayarı karıştırılıyordu

`reset()` "kullanıcının katman düzenlemesini koru" niyetiyle o anki
kalınlıkların anlık görüntüsünü alıp geri yazıyordu. Ama o kalınlık
**lizozimin yediği** kalınlıktı. Sonuç: hücre her ölümden sonra biraz
daha sakat doğuyor, duvarı bir kez çökmüş bir hücre bir daha asla
duvarlı doğmuyordu.

Ölçüm (4 atış lizozim, sonra ölüm ve reset):

```
                    ONCE            SONRA
duvar kalinligi     0.00            6.00
dis yaricap          250             304
kalan molekul   49 (BAGLI)             0
sayaclar           {4: 0}              {}
```

49 molekül hücreye bağlı kalırken sayaç sıfırlanıyordu — ekrandaki nokta
sayısı ile sayacın birbirini tutması, bütün sistemin dayandığı kural.

İki ayrım eklendi:

- **`layer_t0`** — kullanıcının *istediği* kalınlık, savaş hasarından
  ayrı tutuluyor. Kullanıcı duvarı 11'e çıkardıysa, lizozim onu 0'a
  indirse ve hücre ölse bile yeni hücre 11 ile doğuyor.
- **`generation`** — hücre yenilenince artan sayaç. Eski nesle ait
  moleküller kendilerini geçersiz kılıyor. Molekül listesini kimin
  tuttuğundan bağımsız çalışıyor.

Yan etki olarak `seyrelen` sayacı da ölüm anında sahte bir sıçrama
yapıyordu (49 molekül birden "ortamda kayboldu" sayılıyordu); ana döngü
artık nesil değişiminde sayaçları sıfırlıyor.

---

## Görsel ölçek — molekül boyu artık gerçek

Moleküller sabit yarıçapla çiziliyordu (serbest 3, bağlı 4, takılı 5 px).
Fizik gerçek çapı kullanıyordu ama **ekranda 5.1 px'lik peptit ile
14.5 px'lik perforin aynı görünüyordu** — hangi molekülün neden
geçemediği gözle anlaşılmıyordu.

Artık yarıçap gerçek çaptan geliyor. Delikler de aynı `PORE_PX`
ölçeğinde üretildiği için ikisi ekranda birebir orantılı.

Ölçek 4.6'dan **7.0**'a çıkarıldı: 4.6'da yarıçaplar tam sayıya
yuvarlanınca 5.1 ve 6.1 px'lik iki molekül aynı 3 px'e düşüyordu. Bu
çarpan hem delikleri hem molekülleri ölçekler — büyütmek oranları
bozmaz, yalnızca çözünürlüğü artırır.

| molekül | kDa | çap | duvarın kaç deliğinden geçer |
|---|---|---|---|
| Antimikrobiyal peptit | 3 | 7.8 px | 29/29 |
| Nörotoksin | 5 | 9.3 px | 29/29 |
| Amoebapor | 8 | 10.8 px | 29/29 |
| Lizozim | 14 | 13.1 px | 22/29 |
| α-hemolizin | 33 | 17.4 px | **6/29** |
| T3SS efektörü | 50 | 19.9 px | 0/29 |
| Perforin | 67 | 22.0 px | 0/29 |

Duvar deliği 12–19 px. Tek gerçek filtre burası: mukus, kapsül ve
S-layer'ın delikleri her molekülden geniş.

### Jel artık üç boyutlu

Mukus ve kapsül tek bir 2B tabaka olarak çiziliyordu; %85 açık bir
katmanı tek tabakayla göstermek ekranda birkaç dev boşluk üretiyordu.
Düzensiz katmanlar artık en az üç tabaka: hem doku bir örgü gibi
okunuyor hem de fizikçe daha doğru — jel gerçekte üç boyutlu bir fiber
ağıdır, S-layer ise gerçekten tek katmanlı bir 2B kristaldir
(`LAYER_ORDER >= 0.9` olanlar tek tabaka kalıyor).

---

## İki muhasebe ayrışmıştı: derinlik sayacı vs gerçek konum

Mermi yükünü **delme anında** bırakıyordu ve molekülün derinliği merminin
`delivered` sayacından geliyordu. Gözenek geometrisi geldikten sonra bu iki
muhasebe birbirini tutmuyordu:

```
igne "derinlik 5'e ulasti"  ->  ama konumu r = 122
sitoplazma ise               r < 110  (core_r)
```

Yani moleküller "sitoplazmadayım" diye kaydedilip geometrik olarak
**zarın dış tarafında** doğuyor, deliksiz zardan geri sızıp gidiyorlardı.
T3SS efektörü hiçbir iğneyle sitoplazmaya ulaşamıyordu.

İki değişiklik:

- Yük merminin **durduğu** yerde bırakılıyor, delme anında değil. İğne
  hâlâ yol alacaksa (`cyto_travel`) bekleniyor; bırakma noktası ucun son
  konumu.
- Molekülün derinliği sayaçtan değil **konumdan** (`band()`) türetiliyor.
  İki muhasebenin ayrışabildiği tek yer burasıydı.

Sonuç — T3SS efektörü (sitoplazma hedefli, tek ulaşabilen yol iğne):

| taşıyıcı | bırakma yarıçapı | varan | sonuç |
|---|---|---|---|
| T6SS mızrağı | 115 | 6/12 | ÜREME DURDU |
| Stilet | 122 | 0/12 | — (zarda kalıyor) |
| **Nematosist penetrant** | **40** | **12/12** | **iç çöküş** |

Duvar kalınlığına göre penetrant nematosist:

| duvar | bırakma yarıçapı | sitoplazmada mı | sonuç |
|---|---|---|---|
| 2 | 14 – 18 | 3/3 | iç çöküş |
| 6 | 32 – 40 | 3/3 | iç çöküş |
| 10 | 98 – 104 | 3/3 | iç çöküş |
| 14 | 124 – 126 | 0/3 | etki yok |
| 20+ | 174 – 179 | 0/3 | etki yok |

Kalın duvar iğneyi durduruyor; kırılma noktası duvar ≈ 12.

Not: stilet zarda kalıyor (r=122) ve sitoplazma hedefli yük taşıyamıyor.
Miyositoz gerçekte boruyu sitoplazmaya sokar, dolayısıyla bu modelin
eksik tarafı — ama mevcut davranış, değiştirilmiş bir şey değil.

---

## Elek hâlâ tek yönlüydü — sekme her zaman DIŞARI itiyordu

Çift yönlü elek eklenmişti ama `_bounce` molekülü **her zaman dış tarafa**
yerleştiriyordu: `pos = merkez + n * (rr + çap/2 + 0.4)`. İçeriden gelen
bir molekül engele çarpınca duvarın öbür yanına ıraklanıyor, yani tam da
geçemediği tabakadan geçmiş oluyordu.

İzleme (lizozim, sitoplazmadan dışa, deliksiz zar r=117):

```
k=94  r 112.3 -> 116.4   band 4
k=95  r 116.4 -> 123.7   band 4 -> 3     <-- ZARDAN GECTI
```

Ölçüm — deliksiz zardan sızan molekül (24 deneme):

| molekül | çap | önce içerden dışa | sonra | dışardan içe |
|---|---|---|---|---|
| Lizozim | 13.1 px | **18/24** | 0/24 | 0/24 |
| α-hemolizin | 17.4 px | 0/24 | 0/24 | 0/24 |
| T3SS efektörü | 19.9 px | 0/24 | 0/24 | 0/24 |
| Perforin | 22.0 px | 0/24 | 0/24 | 0/24 |

Büyük moleküllerin sızmaması yanıltıcıydı: onlar zaten hedeflerine varıp
donduğu için zarı hiç denemiyorlardı. Hata boyuta bağlı değildi.

`_bounce` artık **geldiği tarafa** itiyor; tutunma da bulunduğu yüzeyde
kalıyor ve delik bulunca **karşı** tarafa geçiyor. Varış kontrolü de
simetrik oldu: hedef katmanına içerden ulaşan molekül de bağlanır.

### Doğrulanan sonuç: derine enjekte etmek her zaman iyi değil

Lizozimin hedefi **duvar** — yani dışarısı. Artık zarın içine bırakılan
lizozim geri çıkamıyor:

| taşıyıcı | bırakma yarıçapı | varan |
|---|---|---|
| Fışkırtma (dışarıdan) | — | 15 – 18 |
| T6SS (derin) | 112 – 116 | 2 – 3 |
| Nematosist (en derin) | 35 – 36 | 0 – 2 |

Yükü ne kadar derine soktuğun değil, **hedefinin nerede olduğu**
belirleyici. Eskiden bu tersti (nematosist 12 veriyordu) ve o sayı
tamamen sızıntı hatasının ürünüydü.

---

## Hareket eden hücre katmanları molekülün üstünden süpürüyordu

Molekül konumları mutlak dünya koordinatındaydı, hücre ise saldırı
algılayınca kaçıyor. Sonuç: hücre kayarken **katmanlar molekülün üstünden
geçiyor** ve sitoplazmadaki bir molekül, hiçbir delikten geçmeden kendini
duvarda buluyordu. Gözenek fiziğinin tamamı bu yolla atlanabiliyordu.

Ölçüm — sitoplazmaya konan 12 molekül, hücre kaçtıktan sonra:

| kaçış | önce | sonra |
|---|---|---|
| 132 px (gerçek hız) | sitoplazma 12 | **duvar 8, zar 1, sitoplazma 3** |
| 720 px | sitoplazma 12 | **dışarıda 12** |

İki şey eklendi:

- **`cell.motion`** — hücrenin o karedeki yer değiştirmesi. Zarfın
  *içindeki* her molekül bu kadar taşınır; dışarıdaki taşınmaz, o ortamda
  serbesttir. Saplanmış / emen mermiler de taşınır, yoksa hedef kaçarken
  iğne havada asılı kalıyordu.
- **Çapa (`_anchor`)** — bağlı molekülün konumu mutlak değil, hücreye
  *göre* saklanır: hangi bant, bandın neresinde, hangi açıda. Her karede
  güncel geometriden yeniden hesaplanır.

Çapa yalnızca hareketi değil **geometri değişimini** de çözüyor: hücre
şişerken (ozmotik) ve duvar erirken (lizozim) de bağlı molekül
bağlandığı yerde kalıyor. Sadece `motion` eklemek yetmiyordu — 1510
kayma 78'e ancak çapayla indi.

Kalan 78 (749.502 örneklemede %0.010) tek bir duruma ait: **lizozim
duvarı 0.00'a erittiğinde**. Bağlı olunan katman ortadan kalkıyor, molekül
komşu banda geçiyor. Tam zarfta duvar 2.10'da durduğu için orada hiç
kayma yok. Bu bir hata değil — yok olan bir katmana bağlı molekülün bir
yere gitmesi gerekir.

---

## Taşıma kuralı silindi — çarpışma zaten yapıyordu

Bir önceki bölümdeki `cell.motion` taşıma kuralı **yanlış çözümdü.**
Doğru soru şuydu: gerçek bir fizik simülasyonunda hücre kaysa da duvar
moleküle çarpar ve onu iter; ayrıca bir "taşı" kuralına gerek olmaz.

Asıl hata çarpışma testinin **çerçevesindeydi**. `d0` ile `d1`'in ikisi
de hücrenin *yeni* merkezine göre ölçülüyordu, dolayısıyla hücrenin o
karede yaptığı yer değiştirme bağıl harekete hiç girmiyordu:

```
d0 = pos.distance_to(YENI merkez)      # yanlis
d1 = nxt.distance_to(YENI merkez)
```

Doğrusu `d0`'ı **önceki** merkeze göre ölçmek. O zaman hücrenin hareketi
de bir geçiş denemesi üretir ve bütün gözenek fiziği kendiliğinden
uygulanır.

Ölçüm — serbest molekül, hücre kaçıyor:

| taşıma kuralı | 22 px/s | 120 px/s |
|---|---|---|
| **açık** | sitoplazma 10/12 | sitoplazma 9/12 |
| **kapalı** | sitoplazma **12/12** | sitoplazma **11/12** |

Kural yalnızca gereksiz değil, **zararlıydı**: bağıl çerçeve hareketi
zaten hesaba katıyor, kural bir kez daha ekliyor, molekül aşırıya
kayıyordu. Kural silindi. Saf çarpışmayla sonuç:

- sitoplazmadaki 12 molekül, hücre **1800 px** kaçsa bile 12/12 içeride
- hücre büyük bir molekülün üstüne 200 px/s sürse bile onu içeri
  **itemiyor** (0/16) — duvar doğru şekilde engelliyor

### Çapa neden kaldı

Bağlı (`arrived`) molekülün çapası bir yama değil: bağlanma **kimyasal
bir bağdır**, molekül bağlandığı yapıyla birlikte hareket eder. Ayrıca
çapa hareketi değil **geometri değişimini** çözüyor — hücre şişerken ve
duvar erirken bantlar kayar, çarpışma bunu görmez. Saplanmış ve emen
mermiler de aynı sebeple hedefiyle taşınır: mekanik olarak kenetlidirler.

---

## Zarın hangi yüzü — elek simetrik, bağlanma taraflı

Eleği simetrik yaparken varış kontrolünü de simetrik yapmıştım. Bu
**elek** için doğruydu (delik iki yönü de kısıtlar) ama **bağlanma** için
fazla genişti: sitoplazmaya boşaltılan bir gözenek açıcı zarın iç
yüzünden etki edip hücreyi öldürüyordu. İkisi ayrı sorular.

Gerçekte zar **asimetriktir** ve bu asimetri ATP harcayan flippazlarla
aktif olarak korunur. Taraf seçiciliği, molekülün *neyi tanıdığından*
gelir:

- **α-hemolizin** fosfokolin başlarına ve ADAM10'a bağlanır — ikisi de dış
  yaprakta.
- **Perforin**'in C2 domaini Ca²⁺ bağımlıdır. Sitozolde Ca²⁺ ~100 nM,
  dışarıda ~1–2 mM. Bağlanamaz — ve bu bir kaza değil, sitotoksik hücrenin
  kendi perforininden korunma mekanizması.
- **Küçük katyonik peptitler** en az seçici: itici güç basit yük çekimi,
  anyonik lipid iki yaprakta da var.
- Tersi de mümkün: **gasdermin D** sitozolde kesilir, iç yaprak lipidlerini
  tanır ve içeriden delik açar. `'ic'` seçeneği bunun için ayrıldı.

`PAYLOAD_SIDE` eklendi: `dis` / `her` / `ic`. Zar dışı hedefler için taraf
kavramı anlamsız olduğundan `her`.

| yük | taraf | dışarıdan | sitoplazmadan |
|---|---|---|---|
| Antimikrobiyal peptit | her | 69/96 | 94/96 |
| Amoebapor | her | 59/96 | 94/96 |
| Nörotoksin | **dış** | 65/96 | **0/96** |
| α-hemolizin | **dış** | 2/96 | **0/96** |
| Perforin | **dış** | 0/96 | **0/96** |

### Yakalanan hata: kare-içi yön ≠ hangi taraftan geldi

İlk sürümde tarafı o karedeki hareket yönünden (`d1 < d0`) türetmiştim.
Sitoplazmada zıplayan bir molekül bazı karelerde içe doğru gider ve
"dışarıdan geliyor" sayılırdı — α-hemolizin hâlâ 34/96 bağlanıyordu.
Doğru ölçüt hareket yönü değil, molekülün **hangi bantta olduğu**:
`self.depth < self.need`.

### Perforin ölü değil, uzmanlaşmış

Matriste perforin her taşıyıcıda 0 çıkınca onu işe yaramaz hâle getirdiğimi
sandım. Ölçüm harness'ımın hatasıymış: hücre küçülünce silahın ağzı
hücrenin *içinde* kalıyordu. Ağzı hep dışarıda tutunca:

| yük | tam zarf | duvar yok | sadece zar |
|---|---|---|---|
| α-hemolizin | 0 | 9 | **26 ŞİŞME** |
| Perforin | 0 | 10 | **26 ŞİŞME** |
| Amoebapor | 16 ŞİŞME | 12 ŞİŞME | 26 ozmotik lizis |

Yani gözenek açıcılar duvarsız hücrede tam iş görüyor — α-hemolizin ile
perforinin hayvan hücrelerini hedeflemesinin sebebi. Duvar hem elek hem
kalkan.

### Oyun açısından sonucu

Derin enjeksiyon artık her yük için üstün değil. Nörotoksin ve gözenek
açıcılar için nematosistle sitoplazmaya göndermek **boşa gidiyor**;
lizozimde de aynı sonuç farklı sebeple çıkmıştı. Hangi taşıyıcının hangi
yüke uygun olduğu gerçek bir karar hâline geldi.

---

## "Zar yüzeyi" ile "zar içi" — etiket olmaktan çıktı

Ölçüm, `ZONE_MODE`'un (`tam` / `enaz`) 42 kombinasyonda yalnızca 3 sonucu
değiştirdiğini gösterdi. Sebep: eskiden mermi yükünü **tek bir son
derinlikte** bırakıyordu ve fazla derine gitmek gerçek bir başarısızlıktı;
şimdi molekül **içeri girerken yolda** bağlanıyor, dolayısıyla koşulu
sağlayan ilk bant zaten `need`'in kendisi. `band >= need` ile
`band == need` aynı şeye çıkıyordu.

Ayrımı fiziksel yapan şey **hidrofobik uyumsuzluk**:

- **Yüzeye bağlanan** molekül (nörotoksin) çift katmana hiç girmez — kanalın
  dış ağzındaki bir reseptöre yapışır. Zar kalınlığı onu ilgilendirmez.
- **Yerleşen** molekül zarı baştan sona geçen bir yapı kurar ve bu yapının
  boyu çift katmanın hidrofobik çekirdeğiyle **eşleşmek** zorundadır.
  Uyuşmazsa yerleşme enerjik olarak pahalıdır ve gerçekleşmez. İki yönlü
  çalışır: zar hem çok kalın hem çok ince olursa bozulur.

`P = exp(-((|t − span| / span) / tol)²)`

| yük | span | tol | zar 0.8 | 1.2 | **1.5** | 2.0 | 2.6 | 3.4 |
|---|---|---|---|---|---|---|---|---|
| Antimikrobiyal peptit | 1.4 | 0.55 | 12 | 13 | 14 | 13 | 4 | **0** |
| Amoebapor | 1.5 | 0.42 | 8 | 15 | 13 | 13 | 3 | **0** |
| α-hemolizin | 1.5 | 0.25 | 1 | 6 | **13** | 3 | 0 | 0 |
| Perforin | 1.9 | 0.22 | 0 | 3 | 7 | **10** | 1 | 0 |
| Nörotoksin | — | — | 13 | 16 | 13 | 12 | 13 | **14** |

Üç sonuç çıktı:

1. **Zar kalınlığı gerçek bir savunma.** 2.6'ya çıkarmak bütün gözenek
   açıcıları durduruyor.
2. **Nörotoksin bu savunmayı umursamıyor** — yüzeye bağlanıyor. Kalın zar
   yapan hücre gözenek açıcılara bağışık olur ama kanal blokerine açık
   kalır. Gerçek bir taş-kağıt-makas.
3. **Perforin daha KALIN zar istiyor** (tepe 2.0). Gerçekte de öyle:
   MACPF domaini uzundur ve perforin kolesterolce zengin — dolayısıyla
   daha kalın — plazma zarlarını hedefler.

### Belirteçler böylece bir işe yaradı

Ölçüm: T6SS zara **4** enerjiyle varıyor, tutunma gücü 60 — kenetleniyor.
Nematosist 164 ile varıyor, kenetlenemiyor (çok hızlı). Kolesterol
belirteciyle T6SS yükünü **r=117**'de, zar bandının (110–124) tam ortasında
bırakıyor; belirteçsiz atış 109'a, sitoplazmaya geçiyor. Yerleşim artık
gerçek bir kısıt olduğu için bu isabet sonucu belirliyor.

### Yakalanan hatalar

- **Başarısız yerleşimde konum yine de işleniyordu.** Molekül zarın
  ötesinde kalıyor, `depth` eski değerde duruyor, bir sonraki karede
  "dışarıdan geliyor" sanılıp yanlış yüzden bağlanabiliyordu (68 vaka).
- **Bağlanan molekül `nxt`'e konuyordu**, bağlandığı tabakanın üzerine
  değil. `nxt` çoğu zaman tabakayı aşmış oluyordu (r=108, zar 110–124) ve
  çapa bir sonraki bandı kaydediyordu — molekül zara bağlandı diye
  sayılırken sitoplazmada görünüyordu.
- **`_hug_step`'te bağlama konumunu `hug_r`'ye ayarlamak** (bunu düzeltme
  sırasında ben ekledim) `bi` ile tutarsızdı: zar bandına bağlanıp duvarda
  görünüyordu, 2278 vaka. Konum zaten doğruydu, geri alındı.

### Açık bırakılan denge sorunu

Kalın zar şu an **bedelsiz**: hem gözenek açıcıları durduruyor hem de
mekanik delmeyi zorlaştırıyor (bariyer ∝ B·t). Gerçekte lipit sentezi
pahalıdır ve kalın zar besin geçişini de yavaşlatır. Laboratuvarda böyle
bir gider yok; ana oyuna taşınırken bir maliyet gerekecek.

---

## Kenetlenme sert eşikti — Bell modeli uygulanmamıştı

Belirteç kodunun yorumunda "Bell modeli: bağın ömrü uygulanan kuvvetle
**üstel** olarak azalır" yazıyordu ama uygulama basit bir eşikti:

```python
if self.pen.energy <= self.grip:   # kesin tutar
```

Bir birim fazla enerji = hiç tutmaz. Sonucu, kenetlenme penceresinin
absürt derecede dar olması: T6SS için **yalnızca duvar 4–6 arası**.
Oyuncunun hedefin duvar kalınlığı üzerinde hiçbir kontrolü yok,
dolayısıyla belirteç kendi hatası olmadan işe yaramıyordu.

```python
P(kenetlenme) = exp(-E / tutunma_gucu)
```

20 atışta kaçının kenetlendiği (kolesterol belirteci):

| taşıyıcı | duvar 1 | 2 | 3 | 4 | 6 | 9 | 12 |
|---|---|---|---|---|---|---|---|
| T6SS | 3 | 4 | 6 | 7 | **15** | 0 | 0 |
| Stilet | 4 | 6 | 6 | 7 | 8 | **18** | 0 |
| Nematosist | 0 | 0 | 0 | 0 | 0 | 6 | **20** |

Uçurum yerine gradyan. Nematosist hâlâ pratikte yakalanamıyor (312
enerjiyle geliyor) ama duvar onu yeterince yavaşlatırsa yakalanabiliyor —
yani zırh ile belirteç birlikte çalışıyor.

### Kalan sınırlama: derinlik enerjiyle sınırlı, uzunlukla değil

İnce duvarda belirteçli T6SS hâlâ az teslim ediyor. Sebebi ölçüldü —
kenetlenemeyen atışların gittiği yer:

| duvar | sitoplazma (çok derin) | zarda durdu | duvarda durdu | kenetlendi |
|---|---|---|---|---|
| 1 | **21/24** | — | — | 3 |
| 3 | 18/24 | — | — | 6 |
| 6 | — | 7 | — | 17 |
| 9 | — | — | 24 | — |

İnce duvar mermiyi durdurmuyor, dolayısıyla mızrak **aşırı derine** gidip
yükü yanlış bölmeye bırakıyor. Fizik olarak tutarlı ama gerçek T6SS'te
böyle olmaz: mızrak sabit uzunlukta ve hücreye **bağlı** bir borudur,
kendi boyundan derine gidemez. Aynı şey stilet için de geçerli (sürekli
tahrikli bir besleme borusu).

Yani nüfuz derinliği şu an **enerjiyle** sınırlı; olması gereken
**uzunlukla**. Bu düzeltilene kadar "ince zırflı hedefe gözenek açıcı
göndermek zor" gibi ters bir sonuç duruyor.

---

## Hedef hücreye organeller

Laboratuvarın hedefi çıplak bir katman yığınıydı. Artık `launcher.py`'deki
`ORGAN_TYPES` kaydındaki **16 organelin hepsi** takılabiliyor (`O` tuşu).

### Tek kaynak

`organs/registry.py` eklendi: addan sınıfa eşleme artık tek yerde.
Launcher'da `ORGAN_TYPES` sözlüğü vardı ama sınıfa nasıl ulaşılacağı orada
değildi — her organ için ayrı bir import ve ayrı bir dal tutuluyordu. Lab'ın
aynı organları kurabilmesi için bu eşlemenin tek yerde olması gerekiyordu;
aksi halde yeni bir organ eklemek iki dosyayı birden düzenlemeyi
gerektirirdi. `check_registry()` iki tarafın örtüştüğünü doğruluyor
(şu an 16/16, fark yok).

### Konak sözleşmesi ölçüldü, tahmin edilmedi

Organlar `Organism` için yazıldı. Tam bir `Organism` gerekip gerekmediğini
tahmin etmek yerine her organı sahte bir konakla çizdirdim. Sonuç:
`draw(screen, owner)` yalnızca **altı** öznitelik okuyor —
`pos`, `radius`, `angle`, `direction`, `color`, `shutdown`. 16/16 organ
bu sözleşmeyle çiziliyor. `LabCell` bunları property olarak veriyor.

### Ölçek

Organlar `owner.radius` ≈ 40 px'lik bir hücre için yazılmış; lab'ın 304 px'lik
hücresine doğrudan çizilince mekanoreseptör 110 px'lik bir top oluyordu.
Çözüm: organları **nominal ölçekte** ayrı bir yüzeye çizip hücrenin
büyütmesiyle aynı oranda ölçeklemek. Oranlar launcher'daki görünümle birebir
kalıyor.

İki görsel sorun daha ölçümle bulundu:

- **İç organlar katman kesitini kapatıyordu** (Sitoplazma gövde boyutunda
  dolu daire çiziyor). İç organlar artık çekirdek yarıçapıyla çiziliyor.
- **Fotoreseptörün görme konisi 47.745, mekanoreseptörün işitme aurası
  32.850 piksel** kaplıyordu — bunlar duyu menzili görselleri ve kesiti
  boğuyorlardı. Organ katmanı yarı saydam (`ORGAN_ALPHA = 150`) çiziliyor.

### Laba gerçek bağlantılar

Hangi organın anlamlı bağlandığı keyfi değil; `logic_membrane` zaten lab'ın
katmanlarıyla örtüşen savunmalar taşıyor:

| organ | bağlantı |
|---|---|
| **Membrane** | `capsule` → Kapsül, `wall` → Duvar, `outer` → Hücre zarı kalınlığı (puan başına 0.45 birim) |
| **Membrane.efflux + repair** | bağlı molekülün **temizlenme süresi** (`CLEARANCE / (1 + efflux·0.28)`) — pompa molekülü içeri sokmaz, bağlandıktan sonra atar |
| **Cilia / Flagella** | hedefin **kaçış hızı** (çıplak 22 px/sn; itki başına +0.9) |
| **Foto/Mekano/Kemoreseptör** | **alarm süresi** (+0.55 sn/adet) — saldırıyı erken fark eder |
| Vacuole / Ribosome / Cytoplasm / Cytoskeleton | yalnızca görsel — lab'da metabolizma yok |
| Silahlar (6 tanesi) | yalnızca görsel — hedefin karşı saldırısı ayrı bir iş |

Zar savunmalarının katkısı `layer_t0` (kullanıcının ayarı) **üzerine
eklenir**, onun yerine geçmez. `bump_thickness` de artık `layer_t0`'ı
değiştiriyor, `l.t`yi değil — yoksa zar organı takılıyken kalınlık ayarlamak
organ katkısını kullanıcının ayarına kalıcı olarak gömüyordu.

Organ düzeni `layer_t0` gibi **reset'te korunur**: kullanıcının kurgusudur,
savaş hasarı değil.

---

## Tam ekran — dünyayı değil görüntüyü ölçekle

İlk deneme sabitleri masaüstü çözünürlüğünden türetmekti. **Kötü sonuç
verdi**, ve ikisi de ölçüldü:

- **lab.py**: 2560×1440'ta yazılar okunmuyor, hücre ekranın küçük bir
  köşesinde kalıyor, saldırgan hedeften 754 px uzakta duruyor ve
  "ULAŞAMAZ" diyor — hiçbir temas silahı kullanılamıyor.
- **simulation.py**: dünya alanı 960.000 → 3.686.400 px, yani **4 kat**.
  Aynı besin ve kaotropi sayısıyla yoğunluk dörde bölünüyor. "Tam ekran
  yap" isteği sessizce ekosistem dengesini bozuyordu — üstelik kaotropi
  sayısını denge için elle yarıya indirmiştik.

Doğrusu: **tasarım ölçüsünde bir tuvale çizip ekrana ölçekleyerek basmak.**
Dünya ve düzen aynı kalıyor, her şey orantılı büyüyor.

```
tuval = Surface(1500x900)      # butun cizim buraya
olcek = min(ekran_w/1500, ekran_h/900)
pencere.blit(smoothscale(tuval, ...), ortalama_kaymasi)
```

Tek incelik: fare olayları pencere koordinatında gelir, tuval
koordinatına çevrilmek zorunda — yoksa tıklamalar görüntüdeki yere denk
gelmez. lab.py'de 10 `ev.pos` kullanımı tek bir çevrimden geçiyor;
simulation.py'de olay döngüsü `event.dunya_pos` alanını yazıyor.

`F11` tam ekran ↔ pencere.

Ölçüldü (lab, tıklama çevrimi ve organ paneli dahil):

| ekran | ölçek | sonuç |
|---|---|---|
| 2560×1440 | 1.60 | 59 fps |
| 1920×1080 | 1.20 | 59 fps |
| 1366×768 | 0.85 | 59 fps (küçülterek sığıyor) |
| 1500×900 | 1.00 | 59 fps |

---

## Organ açısı ve panel kaydırma

İki eksik vardı:

**Organelin yeri değiştirilemiyordu.** Açı takarken bir kez atanıyor,
sonra dokunulamıyordu. Artık organel panelindeki TAKILI listesinde bir
satırın üzerinde **tekerlek = çevir** (15°, `shift` ile 5°).

**Sağ panel taşıyordu** — SEÇİM başlığı ekranın altında kalıyor ve
kaydırma yoktu. Tekerlek panelin üzerindeyken kaydırıyor; sağ kenarda
ince bir çubuk kaydırılacak yer olduğunu gösteriyor.

### Yakalanan iki hata

1. **İçerik yüksekliği yanlış değişkenden ölçülüyordu.** Ölçümü panelin
   bitiminden *sonra* alıyordum ama orada `x, y` molekül sayacı için
   yeniden atanıyor — `panel_max` hep 0 çıkıyor ve panel hiç
   kaydırılamıyordu. Ölçüm panelin bittiği yere alındı.

2. **Ölçekli koordinat kesirli dönüyordu.** Tam ekranda pencere→tuval
   çevrimi `361.875` gibi bir değer üretiyor; satır sınırı 362 olunca
   tıklama 0.125 px ile ıskalıyordu. Bu, tam ekranda satır kenarlarında
   rastgele "tıkladım ama olmadı" olarak görünürdü. Çevrim artık
   yuvarlanıyor.

İkincisini kendi testim ortaya çıkardı: pencerede yaptığım tıklama
tutmadı, sebebini aradığımda çevrimin kesirli olduğunu gördüm.

### Tekerlek çift sayılıyordu

Panel açıkken tekerlek, panelin **arkasındaki** katmanı da
kalınlaştırıyordu. Sebep: pygame bir tekerlek tıkı için **iki olay**
üretir — `MOUSEWHEEL` *ve* `MOUSEBUTTONDOWN(4/5)`. Panel dalı yalnızca
buton 1 ve 3'ü yakalıyordu, 4/5 aşağıya düşüp katmana gidiyordu.

Aynı çift sayım **baştan beri** vardı ve panelle ilgisi yoktu: katman
kalınlığı hem `MOUSEWHEEL` hem `MOUSEBUTTONDOWN(4/5)` dalında
değiştiriliyordu, yani bir tık 0.5 yerine **1.0** ekliyordu. Ölçüm:

| durum | önce | sonra |
|---|---|---|
| panel açık + imleç katmanda | 3 tık → 3 kalınlık değişimi | **değişim yok** |
| panel açık + TAKILI satırı | 1 tık → 30° | **1 tık → 15°** |
| panel kapalı + imleç katmanda | 1 tık → 1.0 | **1 tık → 0.5** |

Panel açıkken artık bütün fare düğmeleri panelde biter, görüntüye düşmez.

---

## Organın zarftaki yeri — hepsi en üstte duruyordu

Dış organların hepsi zarfın **en üstüne**, mukusun üzerine çiziliyordu.
Gerçekte bakteride hemen hiçbir makine dışarıya yapışık değildir;
neredeyse hepsi **iç zara çakılıdır** ve dışarı doğru *uzanır*.

| organ | çapa | dışarı uzanan |
|---|---|---|
| Kemo/Mekano/Fotoreseptör | **hücre zarı** (zarı boydan boya geçer) | yok — algılama ucu periplazmada, sinyal ucu sitoplazmada |
| Kamçı | **hücre zarı** (MS halkası) | çubuk duvarı deler, P halkası duvarda, L halkası dış zarda, filament dışarıda |
| T6SS / zıpkın | **sitoplazma** (taban levhası iç zarın sitoplazma yüzünde) | ateşlenince boru dışarı |
| Nematosist | **sitoplazma** — kapsül | ateşlenene kadar hiç |
| Stilet | **sitoplazma** | boru dışarı |
| Vakuol / ribozom / iskelet | sitoplazma | — |

`ORGAN_CAPA` tablosu eklendi: her organa `(çapa katmanı, uzanır mı)`.
Uzanan organlar için taban halkası çapa katmanında çiziliyor ve **zarfı
kesen bir sap** dış yüzeye kadar uzanıyor.

Bunun bir yan kazancı var: kullanıcı duvarı kalınlaştırınca sapın uzadığı
gözle görülüyor — yani makinenin daha çok iş yapmak zorunda kaldığı.
Ölçüm:

| duvar | çapa (px) | dış yüzey | sap boyu |
|---|---|---|---|
| 1 | 117 | 258 | 142 |
| 6 | 117 | 304 | 187 |
| 16 | 117 | 394 | **277** |

Çapa, zar kalınlığı değişse de zar bandının **ortasında** kalıyor
(0.8 → 114, 1.5 → 117, 3.0 → 124, 5.0 → 132).

### Yanında yakalanan hata: yüzey yükü sitoplazmada çapalanıyordu

Bu değişikliği doğrularken taramaya "yalnız zar" (`enabled=[0,0,0,0,1]`)
varyantını ekledim ve **9360 vaka** çıktı. Organ değişikliğiyle ilgisi
yoktu — varyantı ayrı ayrı koşturunca yalnız o yapılandırmanın tetiklediği
görüldü.

Sebep: nörotoksinin hedefi `zar yüzeyi`, modu `enaz` — koşul
"band ≥ hedef". Dışarıdan hızla gelen molekül tek karede ince zarfı aşıp
sitoplazmaya giriyor, orada `1 >= 0` sağlanıyor ve **çapasını sitoplazmaya
kuruyordu**. Kanal blokeri sitoplazmada yüzüyordu.

Artık hedefi belirli bir katman olan yük **her zaman o katmana**
çapalanıyor; yalnızca sitoplazma hedefli yük (ZONE_TARGET None) içeride
kalıyor. Dört katman yapılandırmasında da 0.

---

## Görünmeyen dört organ

"Vakuolü ve fagositozu göremiyorum" denince ölçtüm; dördü birden
görünmüyordu ve **sebepleri farklıydı**:

| organ | çizdiği | sebep | yapılan |
|---|---|---|---|
| **Vakuol** | 392 px, ort. kontrast 124 | **çift saydamlık** — kendi alfası 150, organ katmanı da 150 → etkin %35 | iç organlar artık tam alfayla; ayrıca keseye **kenar + parlama** eklendi (kontrast 124 → **174**, max 261 → **500**) |
| **İskelet** | **0 px** | `draw` gövdesi `pass` idi | MreB benzeri üç sarmal şerit + FtsZ benzeri bölünme halkası (0 → **4980 px**) |
| **Zar** | 0 px | zarfın kendisidir, lab zaten beş katmanı çiziyor | panelde `x` ile işaretlendi |
| **Fagositoz** | 280 px | **duran bir yapısı yok** | panelde `x` ile işaretlendi |

İkisi düzeltildi, ikisi işaretlendi. **Fagositozun işaretlenmesi sonradan
düzeltildi** — aşağıya bak.

### Fagositoz bir organel değil

Bir **süreçtir**: zar bir parçacığın çevresinde çukurlaşır, aktin bir kadeh
iter, kadeh kapanıp kopar ve **besin vakuolü (fagozom)** oluşur.
Dinlenirken ortada duran bir yapı yoktur. Yani fagositoz ile vakuol aynı
hikâyenin iki ucudur: biri süreç, öteki ürünü.

İskelet ve vakuol değişiklikleri **ortak organ kodunda**, dolayısıyla ana
oyunda da geçerli; ana oyun ayrıca doğrulandı.

### Düzeltme: sitostom kalıcı bir yapıdır

"Fagositozun duran görünümü yok" demiştim; bu **yalnızca genelleşmiş**
sürüm için doğru. Amipte zar tekdüzedir, yalancı ayak nerede aktin
polimerize olursa orada çıkar, dinlenirken yapı yoktur.

Ama biz **yerelleşmiş** sürümü modelliyoruz: organın bir
`attachment_angle`'ı var, yani bir ağzı var. Ve sitostom gerçekte
kalıcıdır — üstelik siliyatın en göze çarpan yapısıdır: oral oluk,
vestibulum, sitofarinks ve o oluğu tarayan özel sil dizisi hep oradadır.
Çizilmezse kullanıcı nereden yutacağını bilemez.

Fagositoz artık `(sitoplazma, uzanır)` çapasına sahip ve **huni** olarak
çiziliyor: boğazı sitoplazmada, ağzı dışarıda, zarfı baştan başa keserek —
çünkü bir ağız tam olarak budur. 280 px → **16.814 px**.

Takas da böylece görünür oluyor: ağız verimlidir ama hücrenin avı **oraya
yönlendirmesi** gerekir. Siliyatların oral oluğu ve onu tarayan silleri bu
nişan alma masrafının ta kendisidir.

---

## Yeme efekti — ağız bir vakuol doğurur

Sitostom statik bir huniydi, yutma diye bir şey yoktu. Artık gerçek dizi
işliyor: ağzın açısal penceresine (±20°) giren molekül **yutulur**, bir
**besin vakuolü** içinde sitoplazmaya taşınır (siklozis), orada sindirilir.

### Duvarlı hücre yutamaz

Kadehin oluşabilmesi için zarın esneyip parçacığı sarması gerekir; sert bir
peptidoglikan duvar ya da kristal S-layer buna izin vermez. Bakterinin
yutmamasının, ökaryotun duvarı bırakmasının standart açıklaması budur.
Sitostom yalnızca `Duvar` ve `S-layer` kapalı (ya da 1.0'ın altında) iken
çalışır; açıkken panelde "SİTOSTOM DEVRE DIŞI: Duvar sert" yazar.

Ölçüm: duvar varken **0 yutulan**, duvar yokken **155**.

### Fagozom bir tuzaktır

Kese asitleşir ve yükünü sindirir. Yalnızca **gözenek açıcı** bir yük
keseyi delip sitoplazmaya kaçabilir — Listeria'nın listeriolizini tam
olarak bunun içindir. Bu, bir sonraki tabloyu ve iğnelerin varlık
sebebini birden açıklıyor:

| yük | sınıf | ağızdan | iğneyle |
|---|---|---|---|
| Perforin | gözenek | yutuldu 155 → **kaçtı 155**, etkili | 0 (dış yüz kuralı) |
| α-hemolizin | gözenek | yutuldu 155 → **kaçtı 155**, etkili | 0 (dış yüz kuralı) |
| T3SS efektörü | sabotaj | yutuldu 155 → **sindirildi 155**, etkisiz | **72 vardı** |
| Lizozim | litik | yutuldu 155 → **sindirildi 155**, etkisiz | **72 vardı** |

Yani ağız bir **besin** yoludur, teslimat yolu değil — yük keseyi
delemiyorsa. T3SS/T6SS iğnesinin yaptığı tam olarak keseyi **atlamaktır**.

### Yakalanan hata

Kese hedefe **varamadan ölüyordu**: yolculuk duvarsız hücrede 6.5 sn
sürüyor, sindirim ömrü 4.5 sn idi ve ikisi aynı sayacı yiyordu — yutulan
155, varan 0. Sindirim artık ancak kese sitoplazmaya **vardıktan sonra**
başlıyor.

---

## Ana oyunu lab modeline taşıma — 1. adım: ölçek

### Varlıklar sıfırlandı

`settings.json`'daki altı varlığın organ listeleri boşaltıldı; skaler
ayarlar (cytoplasm, vacuole_area, vision_range…) korundu. Yedek:
`settings.json.yedek`. Tamamen boş organ listesiyle simülasyonun çalıştığı
ayrıca doğrulandı.

### Neden tek bir küresel ölçek gerekiyor

Laboratuvardaki hücre 304 px, simülasyondaki **10 px** — 30 kat fark.
Gözenek fiziği ancak hücre yeterince büyükken anlamlı (duvar deliği 15 px,
molekül çapı 8–22 px).

Ama hücreyi tek başına büyütmek ekosistemi çökertir. Ölçüldü:

| büyüklük | ölçek 1 | ölçek 30 (hücre tek başına) |
|---|---|---|
| kamçı uzunluğu | 30 | 30 — 300 px'lik hücrede kırıntı |
| görüş menzili | 25 | 25 — hücre kendi gövdesinden öteyi göremez |
| besin yarıçapı | 5.6 | 5.6 — toz tanesi |
| Stokes hızı | %100 | **%3** |

`WORLD_SCALE` eklendi: uzunluk türü her ayar aynı çarpanla, alan türü
karesiyle ölçekleniyor. Tek geçiş noktası `Organism.add_organ` — organlar
altı ayrı dosyada kuruluyor, çarpanı her birinde tekrarlamak yerine orada
uygulanıyor. Doğrulama (ölçek 1 / 5 / 30):

| oran | 1 | 5 | 30 |
|---|---|---|---|
| hücre/görüş | 0.400 | 0.400 | 0.400 |
| hücre/kamçı | 0.333 | 0.333 | 0.333 |
| hücre/işitme | 0.333 | 0.333 | 0.333 |
| hücre/sürüklenme | 1.000 | 1.000 | 1.000 |

Ölçek 30'da hücre yarıçapı tam **300** — laboratuvar boyutu.

### İki hata yakalandı

- **Çift ölçekleme**: hem `logic_cytoplasm.radius` hem `olcekle(size)`
  çarpıyordu; ölçek 30'da yarıçap 300 yerine **9000** çıktı. Ölçek tek
  yerde bırakıldı.
- **Koku ızgarası dünya alanıyla büyüyordu**: ölçek 3'te 60 kare 36 sn.
  `SCENT_CELL_SIZE` de bir uzunluk; ölçeklenince ızgara her ölçekte sabit
  9.600 hücrede kalıyor. (Tam sayı olmak zorunda — ondalık yapınca
  dizinlemede patlıyor.)

### Kalan engel: dünya boyutunda çizim yüzeyi

| ölçek | dünya | yüzey belleği | 60 kare |
|---|---|---|---|
| 1 | 1200×800 | 4 MB | hızlı |
| 3 | 3600×2400 | 35 MB | 36 s |
| 10 | 12000×8000 | 384 MB | 56 s |
| 30 | 36000×24000 | **3.46 GB** | çalışmıyor |

Çizim yüzeyi dünya boyutunda. Büyük ölçek için yüzeyin **pencere
boyutunda** kalması ve dünyaya bir **kamera** ile bakılması gerekiyor.
`WORLD_SCALE` şu an 1.0'da bırakıldı; kamera gelmeden büyütmek yavaşlatır.

---

## Büyütülmüş kesit — dünyayı büyütmeden

Ölçek denemesi bir duvara toslamıştı: ölçek 30'da çizim yüzeyi 3.46 GB.
Doğru çözüm dünyayı büyütmek değil — **seçilen hücreyi ayrıca laboratuvar
ölçeğinde çizmek.** Ekosistem kendi ölçeğinde kalıyor, `WORLD_SCALE`
gerekmiyor.

`LabCell.from_organism()` köprüsü: organizmanın organ listesini ve
**gerçek zar zırhını** (wall / outer / capsule / efflux / repair) lab
hücresine kopyalıyor. Ölçüm: organizmada `wall=9` iken lab kesitinde duvar
6.0 → **10.05**, sitostom "duvar sert" diye kapalı.

Simülasyonda:

- **BOŞLUK** duraklatır (zaten vardı)
- bir varlığa **tıkla** → büyütülmüş kesit açılır
- **L** kesiti aç/kapat

Kesit, katmanları, gözenekleri, çapa derinliklerindeki organları ve zarfı
kesen sapları lab'daki gibi gösterirken sağdaki canlı veri paneli
çalışmaya devam ediyor.

### Sıfırlama varlıkları organsız bırakmıyor

Önemli bir ayrıntı ölçümle çıktı: `settings.json`'da `optropi_0` için
**0 organ** yazıyor, ama yeni bir Optropi **15 organla** doğuyor — varlık
sınıfları kayıt yoksa koda gömülü varsayılan takımı kuruyor. Yani
sıfırlama "boş hücre" vermiyor, varsayılana döndürüyor.

---

## Savaş lab modeline bağlandı

### Varsayılanlar temizlendi — ve altından bir hata çıktı

Varlık sınıfları `if organs_config:` diyordu. Boş liste "yanlış" sayıldığı
için kayıtlı boşluk ile **kayıt yokluğu** ayırt edilmiyordu: `settings.json`
0 organ derken varlık 15 organla doğuyordu. Aynı sebeple **launcher'da
bütün organları silmek de hiç işe yaramıyordu.** Artık
`if organs_config is not None:` — kaydedilmiş boşluğa saygı duyuluyor.
Doğrulandı: yeni Optropi 0 organ.

### Analitik türetme yanlış çıktı, ölçüme dönüldü

Teslimat oranını ilkelerden türetmeyi denedim ve **yanlıştı**: moleküllerin
yüzeye tutunup delik *aramasını* hesaba katmıyordu, çarpım her şeyi
eziyordu (toksin duvar 0'da 0.001 — oysa lab'da ~0.6).

Doğrusu laboratuvarı **ölçüp tablo çıkarmak**; lab zaten referans
uygulama. 10 tohum × 220 kare gerçek molekül simülasyonu:

| silah | zırh 0 | 3 | 6 | 10 | 15 | 20+ |
|---|---|---|---|---|---|---|
| harpoon (T6SS) | **1.000** | 0 | 0 | 0 | 0 | 0 |
| nematocyst | 1.000 | 1.000 | 1.000 | **1.000** | 0 | 0 |
| stylet | 0.750 | 0.750 | 0.675 | 0 | 0 | 0 |
| toxin | 0.612 | 0.612 | 0.612 | 0.612 | 0.612 | **0.412** |
| lysin | 0.638 | … | … | … | … | 0.358 |
| phagocytosis | 0.642 | … | … | … | … | 0.300 |

Silahların zırha karşı **bambaşka eğrileri** var — eski `1/(1+direnç)`
modelinde hepsi aynı şekilde zayıflıyordu. T6SS herhangi bir duvarda
tamamen duruyor; nematosist zırh 10'a kadar deliyor; kimyasal silahlar
daha az duyarlı ama hiç tam etkili değil.

### Dürüstlük notu: tekdüzelik dayatıldı

Ham ölçümde açıklayamadığım noktalar vardı — toksin zırh 20'de 0.412'ye
düşüp 30'da 0.762'ye çıkıyor, stilet zırh 10'da 10 tohumun onunda da
0.000. Zırhın saldırgana *yardım etmesi* fiziksel olarak imkânsız olduğu
için kümülatif minimum alındı. **Bu bir düzeltme değil, bir sınırlama:
aykırılıklar açıklanmış değil, yalnızca zararsız hâle getirildi.**

### Silah → taşıyıcı/yük eşlemesi

İlk eşlemede nematosiste nörotoksin verilmişti ve ölçümde **her zırhta
0.000** çıktı — iğne yükü içeri bırakıyor, oysa nörotoksin dış yüzden
etki ediyor. Eşleme fiziksel tutarlılığa göre düzeltildi: iğneli
taşıyıcılar sitoplazma hedefli yük taşıyor.

### Organsız hücre görünmez oluyordu

Varsayılanlar temizlenince hücreler hem oyunda hem editörde kayboldu;
yalnızca arkalarındaki koku izleri görünüyordu. Sebep: **gövdeyi Cytoplasm
organı çiziyor.** `Organism.draw` yalnızca organ listesini dolaşıyordu,
dolayısıyla sitoplazması olmayan hücrenin çizilecek hiçbir şeyi yoktu.

Bu, sıfırlamanın yan etkisinden fazlası: hücrenin **konumu ve yarıçapı
organlardan bağımsız vardır** ve hiçbir koşulda görünmez olmamalı — yoksa
tıklanıp seçilemez, editörde organ bile eklenemez.

Gövde tabanı iki çizim yoluna da eklendi (`Organism.draw` ve launcher'ın
`draw_entity_preview`'i): sitoplazma yoksa hücrenin kendi renginde yarı
saydam bir gövde + kenar çizilir. Ölçüm: organsız hücre oyunda 0 → 308
piksel, editörde 0 → 4984 piksel.

Not: sitoplazma eklenene kadar hücreler taban yarıçapta (10) kalır —
boyutu belirleyen organ odur.

---

## Hareket: iki hata bir satırda

```python
if has_motor_organs:
    thrust = max(1.0, net_force_mag)
else:
    thrust = 5.0        # <-- iki sorun birden
```

**Motor organı olmayan hücre yüzemez** — kamçısız bakteri kendini itemez.
Üstelik bu sabit, zayıf motoru olan bir hücreninkinden (min 1.0) **daha
fazlaydı**: organsız hücre 200 px/sn ile yüzüyor, 1200 px genişliğindeki
dünyayı 6 saniyede geçiyordu. Artık `thrust = 0.0`.

**Hızlar da absürt yüksekti.** `THRUST_SCALE = 40` ile:

| yapılandırma | önce | sonra (ölçek 4) |
|---|---|---|
| organ yok | 200 px/sn | **0 — hareketsiz** |
| 1 kamçı | 600 px/sn | 60 px/sn |
| 2 kamçı | **1200 px/sn** (dünyayı 1 sn'de geçer) | 120 px/sn (10 sn) |
| 4 sil | 40 px/sn | 4 px/sn |

`THRUST_SCALE` 40 → **4**. Launcher'da "HAREKET (FİZİK)" altında ayarlanabilir.

## Editörde neler var, neler yok

| kategori | durum |
|---|---|
| 16 organ | **hepsi var** — ama 5 iç organ palete kapalıydı |
| zar savunmaları (duvar/dış zar/kapsül/efflux/onarım) | var (Zar organı seçilince) |
| 8 yük (toksin) | ~~yok~~ → **var** (aşağıya bak) |
| 5 belirteç | ~~yok~~ → **var** |
| 9 taşıyıcı (salınım yapısı) | ~~yok~~ → **var** |
| 5 katman | ~~yok~~ → **var** (mukus ve S-layer eklendi) |
| katman başına gözenek ayarı | **yok** (yalnızca lab'da) |

### İç organlar eklenemiyordu

`ADDABLE_ORGANS` yalnızca `internal: False` olanları alıyordu, ve
`add_organ_to_entity` iç organlarda `return False` veriyordu. Varlıkların
organ listesi boşaltılınca bu, hücreye **sitoplazma bile ekleyememek**
demekti — boyutu ve görünürlüğü belirleyen organ o. Artık 16/16
eklenebiliyor.

Yanında ikinci bir hata: organ `entity.organs.append()` ile ekleniyordu,
`entity.add_organ()` ile değil. Yan etkiler (membrane/body/vacuole/ribosome
atamaları, cilia yönleri, küresel ölçek) atlanıyordu — launcher'dan Zar
eklense bile `entity.membrane` atanmıyordu. Artık `add_organ` kullanılıyor;
doğrulandı: 16 organ eklenince dördü de atanıyor.

## Editöre ekleme: taşıyıcı + yük + belirteç + eksik iki katman

Yukarıdaki tablodaki "yok" satırlarının hepsi kapatıldı.

### Silahta seçim artık gerçekten fiziğe giriyor

`WeaponLogic` üç alan kazandı: `carrier`, `payload`, `marker`. Her silah
sınıfı kendi fiziksel varsayılanını taşıyor (`VARSAYILAN_TASIYICI` /
`VARSAYILAN_YUK`); Nematocyst 5/6 (penetrant + T3SS efektörü), Toxin 2/1
(fışkırtma + nörotoksin) gibi. Editörde üçü de seçilebiliyor, seçim
`settings.json`'a yazılıyor ve **üç varlık tipinde de** geri yükleniyor.

> Bu son madde bir hata düzeltmesiydi: `optropi.py` ve `notropi.py`
> `_w = WEAPON_CLASSES[...]` kalıbını kullanıyordu, `kaotropi.py` ise
> doğrudan `self.add_organ(WEAPON_CLASSES[t](...))` diyordu. Editörde
> yapılan seçim kaotropilere hiç ulaşmıyordu.

`take_damage(..., silah=lg)` çarpanı artık `lab.silah_teslimat(...,
carrier=, payload=)` ile hesaplıyor. Ölçüm: `Toxin` varsayılan (2,1) →
zırhsız **0.654**; aynı silah editörden (3,6) yapılınca → **1.000**.
Seçim ölçülebilir şekilde sonucu değiştiriyor.

### Ölçülmeyen kombinasyonlar artık "mucize silah" değil

`teslimat()` bilinmeyen anahtarda **1.0** dönüyordu. Editör bütün
taşıyıcıları açınca bu sessiz bir istismar oldu: ızgarada olmayan her
kombinasyon en güçlü seçenek haline geliyordu. Üç kural kondu:

| durum | değer | gerekçe |
|---|---|---|
| `pi = 0` (yük yok) | 1.0 | silah saf mekanik; kimyasal kapı ona uygulanmaz |
| `CARRIER_EMIT[ci] = 0` | 0.0 | volvent/glutinant/izoriza atış başına **sıfır** molekül bırakır |
| bilinmeyen anahtar | 0.0 | eksik ölçüm sessizce en güçlü seçeneği üretmemeli |

`kombinasyon_ozeti(ci, pi)` editörde ölçülen oranı doğrudan yazıyor
(`-> zirhsiz 0.65 / duvar15 0.85`), taşımayan taşıyıcıda ise turuncu
uyarı. İğne + dış-yüz yük çifti "uyumsuz" olarak işaretleniyor — bir
zamanlar nematosiste nörotoksin verilmesi tam da bu hataydı.

### Kesitteki beş katmanın ikisi oyunda yoktu

Laboratuvar kesiti Mukus / Kapsül / S-layer / Duvar / Hücre zarı çiziyor,
ama zar organında yalnızca `wall`, `outer`, `capsule` vardı. Mukus ve
S-layer çiziliyor ama hiçbir şeye bağlı değildi. İkisi de birer yatırım
oldu:

| özellik | etkisi | bakım | hız cezası |
|---|---|---|---|
| `mucus` | temas direnci + bağlanma direnci | 0.08 | 0.02 |
| `slayer` | mekanik direnç + **sert yüzey** | 0.22 | 0.03 |

Sert yüzey kuralı laboratuvarda zaten vardı (`SERT_KATMANLAR`,
`SERT_ESIK`): kalın duvar ya da S-layer sitostomu devre dışı bırakır.
Aynı kural artık avın tarafında da işliyor — `PhagocytosisLogic.can_engulf`
eşiği `lab.py`'den okuyor, iki taraf ayrışamasın diye. Ölçüm: sert yüzeyli
hedef `False`, yumuşak hedef `True`.

`slip` de editörde yoktu (mantıkta vardı); eklendi. Zar parametreleri
kesitteki sırayla, dıştan içe numaralandı.

### Panel yerleşimi sabit ofsetlerle çiziliyordu

Bölümler `card_y + 150` / `card_y + 260` gibi sabitlerle konumlanıyordu.
Parametre sayısı arttıkça (silahta 4, zarda 9) bölümler birbirinin üstüne
biniyordu; eklenebilir organ 11 → 16 olunca buton ızgarası da talimatların
üstüne binmişti. Artık her bölüm bir öncekinin bittiği yerden başlıyor,
panel yüksekliği içerikten hesaplanıyor, satır başına düşen buton sayısı
panel genişliğinden çıkıyor (3 sabit → 5), uzun etiketler ölçülerek
kırpılıyor. `REMOVE ORGAN` çizildikten sonra `y` ilerletilmiyordu — o da
düzeltildi.

Doğrulama: launcher'ın üç ekranı + popup çiziliyor, `simulation.main()`
701 kare hatasız (silahlar + beş katman yapılandırılmış), üç varlık tipi
de seçimi geri yüklüyor.

### Popup yerleşimi: taşan panel yerine üç sütun

Editör panelinin taşmasının nedeni yerleşimin kendisiydi. Popup 1140x740
iken organ editörü **450x280**'lik bir kutuya sıkışmıştı ve o kutu iki işi
birden yapıyordu: seçili organın parametreleri + 16 düğmelik "organ ekle"
paleti. Sağ sütunun yarısı ise boştu.

| | eski | yeni |
|---|---|---|
| A sütunu | önizleme (450x350) + editör (450x280) | önizleme (430x340) + **ORGAN EKLE** paleti (430x295) |
| B sütunu | dar istatistik kutusu (280x180) | **ORGAN EDITOR** — tam boy tek sütun (300x650) |
| C sütunu | genler (330x650) | istatistikler + genler |

Editör artık 280 px yerine 650 px yüksekliğe sahip; zarın dokuz parametresi
ve silahın dört seçimi rahatça sığıyor. Palet genişlikten satır başına
düşen düğme sayısını hesaplıyor (2 → 4 sütun, 8 satır → 4 satır). Aralık
metni (`0-30`) her satırın kendi kutusunun yanında; bir süre tek satırda
"aralıklar 0..2000" yazıyordum — zar bütünlüğü 20..2000, katmanlar 0..30
olduğuna göre o sayı hiçbir satır için doğru değildi.

**Kaldırılan ölü kod:** `draw_organ_editor_panel` (210 satır) hiçbir
yerden çağrılmıyordu — varlık ekranı yalnızca popup'ı çiziyor. İki ayrı
editör yerleşiminin varlığı, popup'ın geride kalmasının sebebiydi.

**Kaldırılan ikinci kaynak:** olay işleyicisi popup'ın ölçülerini
(`left_section_width = 450`, `preview_height = 350`, ON/OFF konumu)
**ikinci kez** hesaplıyordu. Düzen değişince tıklanabilir alanlar eski
koordinatlarda kaldı. Artık çizim `popup_preview_rect` ve
`popup_toggle_rect`'i kaydediyor, olaylar onları okuyor.

Doğrulama (sentetik tıklama): paletten organ ekleme, önizlemeden seçim,
parametre kutusuna yazma (payload 1 → 4), ON/OFF, ORGANI KALDIR — beşi de
çalışıyor; hiçbir palet düğmesi ya da parametre kutusu popup'ın alt
sınırını aşmıyor.

## Zar ve sitoplazma organ değil, hücrenin kendisi

Editörde "Membrane" ve "Cytoplasm" birer **eklenebilir organ** olarak
duruyordu. Zarsız hücre diye bir şey yok — üstelik kodda zarsız varlık
**ölümsüz** oluyordu:

```python
def take_damage(self, amount, ...):
    if not hasattr(self, 'membrane') or self.dead:
        return 0.0          # zar yoksa hiçbir saldırı işlemiyor
```

Sitoplazmasız hücrenin de gövdesi, dolayısıyla yarıçapı ve çarpışma
alanı yok. İkisi de artık `Organism.temel_yapiyi_tamamla()` ile doğuştan
geliyor, palette yer almıyor, `ORGANI KALDIR` düğmesi seçiliyken
çıkmıyor.

Palette durdukları için **üst üste eklenebiliyorlardı** da: kullanıcının
`optropi_0` kaydında 2 zar ve 5 sitoplazma vardı (40 organ). İki zarlı
hücrede `self.membrane` sonuncuya bağlanıp ötekinin bakım gideri boşa
ödeniyor, iki sitoplazmada gövde yarıçapı belirsizleşiyordu.
`temel_yapiyi_tamamla` fazlalıkları atıyor ve hayatta kalan örneğe
`membrane` / `body` bağlarını yeniden kuruyor — o kayıt 40 organdan
**31**'e indi. Bölünme `deepcopy` ile çalıştığı için her yavruda da
çağrılıyor; aksi halde bir kopya bütün soya geçerdi.

## Editör sınıf sınıf

Üç yerde birden gruplama yapıldı; tek kaynak `ORGAN_SINIFLARI`:

| grup | organlar |
|---|---|
| TEMEL YAPI | Zar, Sitoplazma *(palette yok)* |
| DUYU | Işık / Basınç / Koku alıcısı |
| HAREKET | Kamçı, Sil |
| İÇ YAPI | Koful, Hücre iskeleti, Ribozom |
| SİLAH | Stilet, Zıpkın, Nematosist, Toksin, Lizin, Fagositoz |

Zarın dokuz ayarı da gruplandı: **KATMANLAR** (dıştan içe: mukus, kapsül,
S-layer, duvar, hücre zarı) / **MEKANİZMALAR** (efflux, kayganlık,
onarım) / **BÜTÜNLÜK**. Silahta **GELİŞİM** / **YÜKLEME**.

### Katmanlar neden görünmüyordu

Organ seçmenin tek yolu önizlemeye tıklamaktı, ama:

```python
for i, organ in enumerate(entity.organs):
    if ORGAN_TYPES.get(organ_name, {}).get("internal", True):
        continue        # iç organlar atlanıyor
```

Zar, sitoplazma, koful, iskelet ve ribozom **hiçbir şekilde
seçilemiyordu**; zarın altındaki katman ayarlarına ulaşmanın bir yolu
yoktu. Editör artık ana-liste/detay: üstte **HÜCRE YAPISI** listesi (sınıf
başlıklarıyla, aynı türden organlar `Koful x9` gibi tek satırda), satıra
tıklayınca ayarları açılıyor, `< TUM ORGANLAR` ile geri dönülüyor. Aynı
türden birden fazla organ varsa başlıkta `2/2 < >` ile örnekler arasında
geziniliyor.

Doğrulama: 31 organlı hücre 12 satırda listeleniyor, zar listeden
seçiliyor, S-layer 0 → 6 yazılıyor, temel yapıda KALDIR düğmesi
çıkmıyor, `Sil x2` ileri/geri geziniyor ve başa dönüyor, palet ekleme +
kaldırma çalışıyor, taşan öğe yok.

## Katmanlar çiziliyor

Katmanlar editörde sayı olarak vardı ama **hiçbir yerde çizilmiyorlardı**:
önizleme yalnızca organları çiziyor, zar organının kendi çizimi de gövde
üzerinde ince bir çizgi. Duvarı 2'den 20'ye çıkarmak ekranda hiçbir şey
değiştirmiyordu — laboratuvar kesiti dışında katmanlar görünmezdi.

Kalınlık kuralı tek yere alındı (`lab.katman_bonusu` / `katman_kalinliklari`);
`_apply_membrane_defence` de artık onu çağırıyor. Kesitteki halkalar ile
editördeki halkalar **aynı sayılardan** geliyor.

| yatırım | Mukus | Kapsül | S-layer | Duvar | Hücre zarı |
|---|---|---|---|---|---|
| yok | 7.0 | 5.0 | 2.0 | 6.0 | 1.5 |
| duvar 20 | 7.0 | 5.0 | 2.0 | **15.0** | 1.5 |
| hepsi | 11.5 | 8.6 | 4.7 | 11.4 | 3.3 |

Halkalar hücrenin dış sınırından **içeri** çiziliyor. Dışarı çizmeyi
denedim: organlar zarfın altında kalmasın diye tutundukları yarıçapı
büyütmek gerekti, o da yarıçapa göre çizen organları (mekanoreseptörün
algı dairesi) devasa yaptı. Zarf zaten hücre yarıçapının bir parçası —
kesitte de öyle. Çizim sırası artık hücrenin yapısını izliyor: iç organlar
→ katman halkaları → dış organlar.

Zar seçiliyken sağ üstte **katman kalınlığı** efsanesi çıkıyor. Oradaki
sayı *yatırım* değil, ortaya çıkan *kalınlık* (taban + yatırım ×
`DEFENCE_PER_POINT`) — ikisi aynı şey değil, o yüzden ayrı yazılıyor.

**Önizleme ölçeği** sabit 4.0x idi ve ayarlanabilir değildi: küçük
sitoplazmalı bir hücre 430x340'lık panelin ortasında bezelye
büyüklüğünde kalıyor, katmanları da onunla birlikte küçülüyordu. Artık
panele sığdırılıyor (1x–10x arası).

## Katmanlar eklenip çıkarılabilir

Katmanlar "her hücrede var, sadece kalınlığı değişir" kuralına bağlıydı.
Yatırımın 0 olması ile katmanın **hiç olmaması** ayrı şeyler ama kod ikisini
ayırt edemiyordu: `default_layers()` her katmana taban kalınlık verdiği
için yatırımsız bir hücrenin bile 6.0 kalınlığında duvarı vardı. Duvarsız
hücre (Mycoplasma, hayvan hücresi) ifade edilemiyordu.

Bunun görünmeyen bir sonucu vardı: `SERT_ESIK` 1.0, taban duvar 6.0. Duvar
hep var olduğu için `sert_yuzey` **her zaman** dolu dönüyordu — yani
**fagositoz hiçbir hücrede çalışmıyordu**. Üstelik oyun tarafındaki
`_sert_yuzey` yalnızca yatırıma bakıyor, taban kalınlığı yok sayıyordu:
aynı hücre için lab "sert", oyun "yumuşak" diyordu.

### Neden organ değil, zarın maskesi

Katmanları `entity.organs`'a birer organ olarak koymak arayüzü bedavaya
getirirdi ama dört yerden sızardı: `Morphology.build_organ` bilmediği türe
`None` döndürüp mitozda düşürür, `extract_organ_config` `{"type":"Duvar"}`
yazar ama varlık yükleyicilerinde eşleşen dal yok (sessizce atılır),
`LabCell.from_organism` `ORGAN_CAPA`'ya bakıp eler, "Total Organs" beşe
kadar şişerdi. Bu yüzden varlık, zarın bir maskesi:
`var_mucus / var_capsule / var_slayer / var_wall`. Plazma zarı zorunlu.

> Editörde katman seçimi için negatif sentinel indeks **kullanılmadı**:
> `entity.organs[-2]` Python'da hata vermez, gerçek bir organ döndürür —
> kullanıcı yanlış organı düzenlerdi. Ayrı bir `selected_layer` kanalı var
> ve satır/düğme demetleri artık tür etiketi taşıyor.

### Kaldırmanın karşılığı

| duvar / S-layer | kesitte sert | yutulabilir | bakım gideri |
|---|---|---|---|
| ikisi de var | S-layer | hayır | 1.19 |
| duvar yok | S-layer | hayır | 0.84 |
| S-layer yok | Duvar | hayır | 0.89 |
| **ikisi de yok** | **yok** | **evet** | **0.54** |

Sert yüzey iki taraflıdır: kabuklu hücre yutulamaz ama kendi sitostomunu
da açamaz. Zarf soyunca hücre avlanabilir hale gelir — ve avlanabilir olur.
Ayrıca katmanın kendisi bakım gideri ister (`TABAN_COST_*`); yoksa katman
kaldırmak saf kayıp olurdu.

### Yol boyunca çıkan gerçek hatalar

| yer | neydi |
|---|---|
| `zone_min_depth` | hedef katman yoksa `len(active)` dönüyordu — Z_CYTO ile aynı sayı. Duvarsız hücreye atılan lizozim "sitoplazmaya nişan alan" bir yüke dönüşüp olmayan duvarı eritiyordu. Artık `None`, molekül `hedef_yok` ile hiç varamıyor. |
| `_update('duvar_eri')` | `self.layers[3]` ve `6.0` sabit yazılmıştı; duvarsız hücrede o indeks başka katman, kalınlaştırılmış duvar orantısız eriyordu. |
| lab F1–F5 | F5 **plazma zarını siliyordu**; üç toggle da `enabled`'a ham yazıp seçimi zar organına geri yazmıyor, uçuştaki molekülleri emekli etmiyordu. Tek yazıcı `set_layer_present`. |
| `etkin_zirh` | kaldırılan duvarın depodaki yatırımı hâlâ zırh sayılıyordu (yatırım sayısı bilerek korunuyor). `katman_puani` kapısı eklendi. |
| `membrane_score` | duvarını kaybeden hücre hâlâ duvarlı gibi kokuyordu; mukus ve S-layer koku toplamına hiç girmiyordu. |
| `simulation._draw_lab` | önbellek imzası `(id, organ sayısı)` idi; katman değişince organ sayısı değişmediği için büyütülmüş kesit bayat kalıyordu. |
| `remove_selected_organ` | Cytoskeleton'u engelliyordu ama KALDIR düğmesi onun için çiziliyor ve sessizce hiçbir şey yapmıyordu. Kural tek yerde: `kaldirilabilir()`. |
| palet | KATMANLAR grubu eklenince SILAH satırı panelin altından taştı (önizlemeden 40 px alındı). |

Doğrulama: 24/24 arayüz akışı (var olanı ekleme, kaldır→geri ekle, editör
kapat/aç, katman↔organ geçişleri, Enter'sız yazma, iki KALDIR düğmesinin
çakışmaması, kayıt, sınır durumları), katman testi (8 bölüm), eski editör
testleri, `lab.main()` ve `simulation.main()` 351'er kare — hepsi hatasız.

> Not: bu değişikliğin düşman doğrulaması (4 ajanlı inceleme iş akışı)
> **koşturulamadı** — dördü de oturum limitine takıldı. Yukarıdaki bulgular
> ve düzeltmeler benim kendi taramamdan; bağımsız bir gözden geçirme
> yapılmadı.

### Zarf içeri değil, DIŞARI

İlk sürümde halkalar gövdenin **içine** çiziliyordu ve sitoplazmanın dış
bandını yiyordu: hücre aynı boyda kalıp sitoplazma küçülmüş gibi
görünüyordu. `lab.py`'de zarf çekirdeğin **dışındadır** ve zar üzerindeki
organlar da o dış yüzeye taşınır.

Dışarı çizmeyi ilk denediğimde organlar zarfın altında kalmıştı; düzeltmek
için tutundukları yarıçapı büyüttüm ve mekanoreseptörün algı dairesi devasa
oldu — o yüzden içeri çizmeye dönmüştüm. **Teşhis yanlıştı:** organ
görünümlerini taradığımda görüldü ki `parent.radius` yalnızca KONUM için
kullanılıyor (`get_absolute_position`); mekanoreseptörün çemberi
`size * 30`, kamçının uzunluğu kendi `length`'i. Blob'un sebebi yarıçap
değil, önizleme ölçeğinin `size`'ı 13.7x büyütmesiydi. Dolayısıyla organları
dış yüzeye taşımak hiçbir organı şişirmiyor.

Çizim sırası: iç organlar çekirdek yarıçapında → zarf dışarı → dış organlar
zarfın dış yüzeyinde. Kalınlık oranı lab ile aynı (`PX_PER_UNIT / 110`
başına çekirdek yarıçapı), tıklama testi de dış yarıçapı kullanıyor.

## Hücre neden besin alamıyor: doluluk göstergesi

Besin **temasla** alınıyor (`o.radius + f.radius`), fagositoz gerekmiyor —
fagositoz başka *hücreleri* yutmak için. Alamama sebebi
`Cytoplasm.can_fit_food`:

```
current_food_load + organ_alani + FOOD_AREA <= total_area
```

Kullanıcının `optropi_0` kaydında 31 organ vardı (9 koful, 7 iskelet,
8 silah) ama sitoplazma `size = 1.0`:

| | değer |
|---|---|
| gövde alanı (size 1.0, yarıçap 10) | 314 |
| organların kapladığı | 410 |
| bir besin (FOOD_AREA) | 100 |
| **artan** | **−196 → besin alınamaz** |

Hücre kendi organlarına sığmıyordu ve bunun ekranda **hiçbir işareti
yoktu**; hücre açlıktan ölürken sebebi görünmüyordu. STATISTICS paneline
`Doluluk 410 / 314` satırı eklendi; sığmıyorsa kırmızı yazılıyor ve
gereken sitoplazma boyutu hesaplanıyor (`size >= 1.27`).

## Üç düzeltme: yeme kuralı, oyunda zarf, sabit çekirdek

### Canlı avı dokunarak yutmak

Fagositozun bütün aşamaları `fire_weapons` içinde zaten vardı: adezyon
(`try_bind`) → `PHAGO_BIND_TIME` kadar tutma → `can_engulf` (boy oranı +
sert yüzey) → enerji bedeli → sersemleme. Ama `simulation.py`'deki temas
yolu bunların hiçbirine uğramıyordu:

```python
def can_consume(self, target):
    if target.dead: return True
    return self.has_weapon(Phagocytosis)   # <-- organa SAHIP olmak yetiyor
```

Fagositoz takan bir hücre sağlam bir avı dokunduğu anda **bedelsiz ve
kuralsız** yutuyordu. Artık canlı av bu yoldan yenmiyor: `can_consume`
yalnızca ölüye izin veriyor (saprotrofi), canlıyı yutma işini fagositoz
akışı yapıyor — o akış avı önce öldürüp sonra `consume_prey`'e geliyor.

### Aynı mide

`consume_food` kapasiteden geçiyordu, `consume_prey` geçmiyordu
("kapasite kontrolü atlanır"). Sonuç: organlarına sığmadığı için **bir
besin bile alamayan** hücre koca bir hücreyi yutabiliyordu. Av da artık
en az bir lokmalık yer istiyor; değeri tam ödeniyor.

### Oyunda zarf

Katmanlar yalnızca editör önizlemesinde çiziliyordu; ekosistemde hücre
hâlâ düz bir daireydi. `lab.zarf_ciz` / `zarf_yaricapi` ortak yardımcıları
eklendi ve `Organism.draw` de aynı sırayı izliyor: iç organlar çekirdekte
→ zarf dışarıda → dış organlar zarfın dış yüzeyinde. Ölçüm (çekirdek 20 px):
katmansız 22 px, mukus+kapsül 42 px, hepsi 55 px.

> `entities/organism.py` bunun için `launcher.ORGAN_TYPES`'ı okumak
> zorunda kalacaktı, ama launcher zaten entities'i import ediyor — döngüsel
> bağımlılık. İç/dış sınıflandırması `organs/registry.py`'ye taşındı
> (`IC_ORGANLAR`, `ic_organ`); iki taraf da oradan okuyor ve iki liste
> birbirini tutuyor.

### Katman ekledikçe sitoplazma küçülüyordu

Önizleme ölçeği `(yarıçap + zarf)`'a göre alınıyordu: her eklenen katman
ölçeği küçültüyor, sitoplazma ekranda daralıyordu — "zar biraz daha içeri
itiliyor" görüntüsü buydu. Ölçek artık **yalnızca çekirdeğe** göre
(`yarıkenar * 0.32 / çekirdek`); katman eklendikçe ölçek sabit kalıyor
(ölçüldü: 4.128 → 4.128 → 4.128 → 4.128) ve zarf dışarı doğru büyüyor.

### Test altyapısı sızıntısı

`test_katman.py` `importlib.reload(game_settings)` yapıyor; reload
`save_all`'ın no-op yamasını geri alıyor ve testin bozduğu bellek içi
ayarlar diske yazılabiliyordu. Nitekim `settings.json`'a
`var_*: false` sızmıştı — kullanıcının katmanları kayboldu gibi
görünüyordu. Anahtarlar temizlendi (yok = varsayılan VAR) ve test reload
sonrası no-op'u yeniden koyuyor.

## Gözenekler oyuna girdi: aynı fizik, aynı delikler

### Geometri tek kaynaktan

Gözenek makinesi (`Sheet` üretimi, alt tabakalar, delik poligonları)
`LabCell`'in içine gömülüydü; oysa yalnızca üç şeye bağlı: katman listesi,
hangilerinin açık olduğu, çekirdek yarıçapı. `lab.Zarf` sınıfına çıkarıldı.

Ölçek: laboratuvarda çekirdek 110 px ve bir kalınlık birimi 9 px. Oyunda
çekirdek 20 px olduğu için her şey `çekirdek/110` ile orantılı küçülür —
gözenek genişlikleri dahil. Ölçüldü:

| | tabaka | delik poligonu | dış/çekirdek |
|---|---|---|---|
| lab (çekirdek 110) | 11 | 147 | 2.759 |
| oyun (çekirdek 20) | 11 | 147 | 2.759 |

"Hangi molekül hangi delikten geçer" sorusunun cevabı ölçekten bağımsız
(üç ayrı çap oranında iki ölçek de aynı kararı verdi).

### Molekül fiziği yeniden yazılmadı

`lab.Molecule` 500 satır ve hücreden yalnızca **on bir** şey okuyor.
`lab.HedefZarf` adaptörü bir `Organism`'i o arayüze bağlıyor; böylece
ekosistemdeki molekül ile laboratuvardaki molekül **aynı kodu** çalıştırır.
Sürekli (moleküler) silahlar artık hasarı doğrudan yazmıyor, gerçek
molekül bırakıyor; hasar molekül varınca doğuyor (`receive` → kademe).

Ölçüm — fışkırtma + nörotoksin, 15 s:

| hedef | canlı molekül | nerede | varan | sonuç |
|---|---|---|---|---|
| beş katman | 89 | 56 dışarıda, 33 mukusta | **0** | bütünlük 100 |
| duvar yok | 90 | 71 dışarıda, 19 mukusta | 3 | bütünlük 88 |
| çıplak zar | 21 | 16 zarda | 16 | **öldü (2 s)** |

Katmanlar artık savaşın sonucunu ölçülen bir tabloyla değil, **fiilen**
belirliyor.

> **Ölçek tuzağı:** geometri küçülüyordu ama termal ajitasyon
> (`THERMAL = 240 px/s`) küçülmüyordu. Küçük hücrede molekül zarfın dışına
> savruluyor, hiçbiri varamıyordu (400 karede 0 varış — katman farkı da
> görünmüyordu). Hızlar da `çekirdek/110` ile ölçeklendi; `self.vs`
> `__init__`'in en başında atanmalı, çünkü `jig` daha ilk satırlarda
> kuruluyor.

### Yakınlaştırma

Fare tekerleği kamerayı yakınlaştırır (x1–x16, imlecin gösterdiği dünya
noktası sabit kalır). Yakınlaştırma **yeni bir temsil üretmez** — dünya
zaten gerçek gözenek geometrisiyle çizilmiş durumda, kamera yalnızca daha
büyük çizdirir. Tuvali büyütüp üstünü ölçeklemek detay kazandırmazdı:
1200x800'e çizilmiş 1 px'lik delik büyütülünce bulanıklaşır, açılmaz.

Çizimin tamamı tek yoldan geçiyor: `lab.hucreyi_ciz(screen, entity,
merkez, ölçek)` — oyun (ölçek 1), kamera (ölçek > 1) ve editör önizlemesi.
Organ görünümleri boyutlarını kendi alanlarından alır (`length`, `size`,
`range`, `area`), `parent.radius` yalnızca konum içindir; ölçek uygulanırken
ikisi de geçici olarak büyütülüp geri alınır.

**Bedeli:** moleküller kare başına ~%45 ek maliyet getirdi (351 kare
6.0 s → 8.8 s, başsız ölçüm). Hücre başına molekül üst sınırı 240.

### Sitoplazma 2.0 ile başlıyor

`size 1.0`'da gövde alanı 314 px², organlar 410 — hücre hiçbir besin
alamıyordu. Varsayılan 2.0 (alan 1257); kayıtlı değerler de yükseltildi.
Kaotropi'nin 3.0'ı kendi tür farkı olarak korundu.

### Görünüm ölçeği: dünya 1/4

Zarf çekirdeğin **dışına** çizildiği için bir hücre artık yarıçapının
~2.76 katı yer kaplıyordu ve dünya kalabalık görünüyordu.
`GORUNUM_OLCEGI = 0.25` eklendi: hücreler, organları, molekülleri ve
(kamera görünümünde) besinler ekranda dörtte bir çizilir.

| tekerlek | çizim ölçeği | çizilen dış yarıçap |
|---|---|---|
| x1 | 0.25 | 14 px (dünya görünümü) |
| x4 | 1.00 | 55 px (zarfın gerçek boyu) |
| x16 | 4.00 | 221 px (laboratuvar yakınlığı) |

Üst sınır x16'dan **x64**'e çıkarıldı: x1 artık dörtte bir olduğu için
aynı yakınlığa ulaşmak dört kat daha fazla zoom istiyor.

**Fizik değişmedi** — bu yalnızca çizim ölçeği. Yan etkisi olumlu:
temas yarıçapı (`entity.radius` = 20 px) ile çizilen hücre arasındaki
uyumsuzluk azaldı; önce çizim 55 px iken fizik 20 px'ti, şimdi çizim
14 px. Tam örtüşme için temas yarıçapının zarfın dışını göstermesi
gerekir - ayrı bir karar.

> Testin yakaladığı hata: `_gorunum` kamera dalında besin döngüsünden
> **sonra** tanımlanıyordu; yakınlaştırılmış karede `UnboundLocalError`.

## Dört düzeltme: ölçek, sindirim, yutulma, koku senkronu

### 1. Sabit ölçülü organlar ölçeklenmiyordu

`hucreyi_ciz` organların `length / size / range / area` alanlarını
ölçekliyordu, ama bazı organlar boyutunu **sabit sayıdan** alıyor:
silahlarda `DISPLAY_LENGTH` ve çizim içindeki `pygame.draw.circle(..., 3)`
gibi yarıçaplar. Bunlar ölçek ne olursa olsun aynı büyüklükte kalıyordu —
dünya görünümünde hücreden büyük, kesitte kayıp.

Çizim ölçeği artık konağa yazılıyor (`entity.ciz_olcegi`, çizim bitince
geri alınır) ve sabit ölçülü çizimler onu okuyor. Ölçüldü (nematosist
piksel sayısı): ölçek 0.25 → 11, 1.0 → 71, 4.0 → 1188.

### 2. Sindirim "kalkmış" değildi

`DIGESTION_TIME` kodda 10.0 s, ama `settings.json`'a **1.0** yazılmıştı.
Bir saniyede sinen besin, `DIVISION_MODE` açıkken hemen bölünmeye yol
açıyordu. Kayıt kod varsayılanına (10.0) döndürüldü; launcher'ın SETTINGS
ekranından değiştirilebilir. Ölçüldü: besin tam 10.00 s sonra sindiriliyor.

### 3. Besin ışınlanıyordu

Besin temas anında listeden silinip doğrudan sindirim kuyruğuna giriyordu.
Artık iki aşamalı: temas **yutulmayı başlatır** (`Food.yutulmaya_basla`),
besin 0.55 s boyunca küçülerek merkeze çekilir
(`yutma_guncelle`, smoothstep eğrisi), ancak oraya varınca kuyruğa girer ve
listeden düşer. Avcı bu sırada ölürse besin serbest kalır ve eski boyuna
döner. Optropi ve kaotropi aynı akıştan geçer; ilerleme tek yerde işlenir.

### 4. Koku ve izler kamerayla desenkrondu

`trail_manager.draw` ve `scent_env.draw_debug` dünya koordinatlarında
çiziyor; kamera yakınlaşınca besinler ve hücreler dönüşüyor ama bunlar
yerinde kalıyordu — koku bulutu besinden kopuyordu. Yakınlaştırılmış karede
ikisi de önce dünya ölçeğinde bir ara tuvale çizilip kameranın ölçek ve
kaydırmasıyla aynı dönüşümden geçiriliyor.

Doğrulama: 11/11 yeni kontrol + 28/28 + 14/14 + 16/16 + editör/katman
testleri; `lab.main()` 351 kare, `simulation.main()` 351 kare (ısı haritası
açık, yakınlaştırma ve uzaklaştırma dahil) — hepsi hatasız.

## Motor fiziği: itme tabanı ve yutulan tork

"Sağ tarafında 3 silia olan bir hücre düz ilerliyor" gözlemi doğruydu ve
iki ayrı sebebi vardı. **İkisi de bu oturumda oluşmadı; ilk commit'te de
vardılar** (`git show HEAD` ile doğrulandı).

### 1. İtme tabanı motor fiziğini devre dışı bırakıyordu

```python
thrust = max(1.0, net_force_mag)   # "minimum 1.0"
```

Ölçüldü — silialar bu tabanın **altında** kalıyor:

| yerleşim | net kuvvet | hız |
|---|---|---|
| 3 silia tek yanda | 0.062 | 2.00 |
| 6 silia simetrik | 0.168 | 2.00 |
| 1 kamçı | 4.997 | 9.99 |

Yani her motorlu hücre, silialarını nereye takarsan tak, aynı hızda
(2.00 px/sn) yüzüyordu. Hücreyi silialar değil taban itiyordu. Düşük
Reynolds rejiminde atalet yoktur: hız anlık kuvvetle doğru orantılıdır,
kuvvet yoksa hareket de yoktur. Taban kaldırıldı.

### 2. Tork yalnızca dönüş modunda uygulanıyordu

```python
if "TURN" in motor_mode or "CORRECT" in motor_mode:
    self.direction = self.direction.rotate(...)
```

Düz giderken hücrenin **kendi motorlarının** ürettiği tepki torku
atılıyordu. Aynı tarafta duran motorların `r × F` torkları aynı işaretle
toplanır; hücre dönmek zorundadır. Kendi torkunu görmezden gelmek bir mod
seçimi olamaz — koşul kaldırıldı.

### Sonuç (6 saniye, aynı tohum)

| yerleşim | yol | net dönme | yön değişimi |
|---|---|---|---|
| 3 silia tek yanda | 13.4 px | **134.9°** | 0 |
| 6 silia simetrik | 28.2 px | 62.9° | 0 |
| 1 kamçı arkada | 21.9 px | 148.7° | 0 |
| motorsuz | 0.0 px | 0.0° | 0 |

Tek yanda silia artık dönerek ilerliyor, simetrik dizilim iki katı yol
alıyor. Yön değişimi sayısı her yerde **0**: dönüşler tek yönlü, yani
denetleyici salınıma girmiş değil.

### Silia çarpanı yeniden ayarlandı

Taban kalkınca silialarin gerçek katkısı ortaya çıktı: `0.2` ile altı
simetrik silia bir kamçının **%15**'i kadar itiyordu, yani pratikte
işlevsizlerdi — taban onların eksikliğini örtüyormuş. Ölçülerek `1.0`
seçildi (altı silia ≈ kamçının **%74**'ü): silia işini gören ama tek
başına kamçı kadar güçlü olmayan bir yatırım.

| CILIA_SPEED_MULTI | 6 silia hız | 1 kamçı hız | oran |
|---|---|---|---|
| 0.2 (eski) | 1.03 | 7.02 | 0.15 |
| **1.0** | **5.17** | 7.02 | **0.74** |
| 2.5 | 15.01 | 7.02 | 2.14 |

## Sürüklenme ve kamçı senkronu

### 1. Organlar sürüklenmeye katılıyor

Sürtünme yalnızca `self.radius`'a bakıyordu; ölçüldü, 30 fotoreseptör
eklemek hızı 10.00'dan 10.00'a getiriyordu. Artık etkin yarıçap
`r × (1 + ORGAN_DRAG_GAIN × organ_alanı / gövde_alanı)`. Gain 1.0 seçildi
(nötr, açıklanabilir): 30 fazladan organ hızı **%8** düşürüyor.

### 2. Dönme sürtünmesi a³

Kod dönmeyi `tork / (0.2·r²)` ile hesaplıyordu. Biçim doğruydu (düşük
Reynolds'ta atalet yok, bu bir hareketlilik katsayısı) ama üs yanlıştı —
üstelik aynı dosyadaki öteleme sürtünmesi zaten `a¹` ile doğru
ölçekleniyordu.

| yarıçap | eski | yeni (a³) |
|---|---|---|
| 10 | 143.2 °/s | 47.4 °/s |
| 40 | 35.8 °/s | **8.2 °/s** |

Bölende artık organları da içeren etkin yarıçap var; organlar dönmeye de
direnir.

### 3. Kamçılar birbirini iptal ediyordu

`_apply_turn_mode`'daki tork terimi cebirsel olarak **her kamçı için aynı
±1.0'a** sadeleşiyordu (bağlanma açısı sadeleşir, 90°/45° = 2 doyar).
Küçük açılarda ise her kamçı yalnızca "hedefe bak" diyordu ve farklı
noktalardaki kamçılar zıt işaretli sapma seçiyordu.

Ölçüldü — 180°/90°/300°'de üç kamçı:

| | eski | yeni |
|---|---|---|
| torklar | +63.6 / −63.6 / −5.6 | +49.5 / +49.5 / +49.5 |
| net | ≈ 0 (kilitli) | **+148.5** |
| TURN modunda zıt işaret | var | **240/240 karede yok** |

Kural: **tork = R·F·sin(sapma)** — bağlanma açısı bu ifadede sadeleşir,
yani torkun işareti doğrudan sapmanın işaretidir. Yeni `_kamci_sapmasi`
her kamçının kendi çözümünü hesaplamaya devam ediyor (hangi büyüklük
hedefe en çok katkı verir), ama dönüş talebi varken sapma o işaretin yarı
aralığına kısıtlanıyor: hiçbir kamçı dönüşün tersine tork üretemiyor.
Düz gidişte kısıt yok — orada zıt sapmaların torku iptal etmesi
*doğrudur* (Chlamydomonas'ın kulaç vuruşu gibi).

Düzeltme modu (5–20°) de artık hafif bir talep taşıyor; küçük dönüşlerde
de yaslanma görünüyor.

### 4. Kamçı gerçekten kıvrılıyor

Kamçı düz bir ışındı ve sapma onu kökünden bütün olarak döndürüyordu —
zarda keskin bir kırık oluşuyor, dönerken kıvrılma görünmüyordu. Artık kök
zara dik çıkıyor, gövde boyunca smoothstep ile itme yönüne dönüyor, uç o
yöne oturuyor.

Ayrı bir "kıvrım" durumu tutulmadı: işaretli sapma zaten
`thrust_angle − attachment_angle` farkında var ve motor mantığı onu
8 rad/s ile yumuşatıyor. Kıvrım böylece fizikle kendiliğinden senkron —
hangi tarafa tork üretiliyorsa kamçı o tarafa kıvrılıyor. Ölçüldü:
SOLA DÖN −43/−43/−44°, SAĞA DÖN +43/+38/+38°.

## Fagositoz görünür oldu — ve yarıçap modeli düzeldi

### Engel: temas çekirdekte, çizim zarfla

Yalancı ayakları eklemeye çalışınca çıktı: temas `o.radius + f.radius` ile
**çekirdek** yarıçapında oluyordu, ama hücre zarfla birlikte yarıçapının
**2.76 katı** çiziliyordu. Yani besin, temas ettiği anda görsel olarak
çoktan hücrenin içindeydi; ayakların uzanacağı yer yoktu.

Çözüm modeli değiştirdi: **zarf artık `entity.radius`'un İÇİNE oturuyor**.
Dış sınır = temas yarıçapı = çizilen kenar. Sitoplazma zarfın içinde kalır
(dış 20 px → çekirdek 7.25 px).

Bunun iki yan kazancı oldu:
- Çizilen hücre kendiliğinden **1/2.76** oranında küçüldü — istenen 1/4'e
  çok yakın. `GORUNUM_OLCEGI` 1.0'a döndü; ayrı bir görünüm ölçeği tutmak
  artık çizim ile fiziği yeniden ayırmak olurdu.
- Katman eklemek hücreyi büyütmüyor, **sitoplazmayı küçültüyor** — zarfa
  yatırım yapmanın gerçek bedeli bu.

Launcher önizlemesi de aynı hesaba bağlandı; editörde görülen hücre ile
ekosistemdeki aynı şey.

### Gerçek mekanizma çiziliyor

Fagositozun sırası artık ekranda: zar besinin iki yanından **yalancı ayak**
uzatır, kollar besinin etrafında kapanır, kaynaşıp bir **fagozom** oluşur
ve kese besinle birlikte sitoplazmaya çekilir.

| t | ne olur |
|---|---|
| 0.00–0.60 | kollar uzanır ve kapanır; besin **yerinde durur**, küçülmez |
| 0.60 | kese kapanır (halka) |
| 0.60–1.00 | fagozom sitoplazmaya çekilir, besin hafifçe sıkışır |

Eskiden besin ilk kareden itibaren merkeze kayıyordu — "sarılıyor" değil
"emiliyor" gibi görünüyordu.

> İki hata yol boyunca çıktı: (1) çizim sırasında `entity.pos` **ekran**
> merkezine ayarlı olduğu halde besin **dünya** koordinatındaydı; ikisini
> çıkarmak ekranın bir ucundan ötekine uzanan kollar üretiyordu. (2) Ayaklar
> dış organlardan önce çiziliyordu ve mekanoreseptörün algı dairesi onları
> tamamen örtüyordu — sarmalama sırasında zar en dıştaki yapıdır, en sona
> alındı.

### Alınan besin sitoplazmada duruyor

Yutulan besin ekrandan siliniyordu; oysa fagozom sindirilene kadar
sitoplazmada durur. `Organism.sindirim_keseleri()` kuyruktaki her besini
ve enzimin işlediğini ilerlemesiyle veriyor; `lab.sindirim_keseleri_ciz`
onları sitoplazmanın içine, her biri kendi sabit yerinde çiziyor.
İşlenen kese küçülüyor ve rengi soluyor. Birden çok besin varsa hepsi
ayrı ayrı görünüyor (ölçüldü: 3 besin → 3 kese).

### Düzeltme: yarıçap = sitoplazma + zarf

Bir önceki adımda zarfı `entity.radius`'un **içine** oturtmuştum ve bunu
bir kazanç diye yazmıştım — yanlıştı: katman eklemek sitoplazmayı eziyordu,
zar içeri doğru itiliyordu. İki yanlış arasında sıkışılıyordu:

- zarfı **dışarı** çizince temas çekirdekte oluyordu → besin dokunduğu anda
  görsel olarak hücrenin içindeydi;
- zarfı **içeri** oturtunca katman eklemek sitoplazmayı küçültüyordu.

Doğrusu üçüncü seçenek: **`entity.radius` zarfıyla birlikte ölçülen dış
yarıçaptır.** Sitoplazma kendi boyunu korur, zarf dışarı doğru eklenir,
temas/örtüşme/organ tutunması hep bu dış sınırda olur.

| katmanlar | sitoplazma | dış yarıçap | sürtünme | hız |
|---|---|---|---|---|
| yok | 20.00 | 22.45 | 1.08 | 18.54 |
| mukus | 20.00 | 33.91 | 1.63 | 12.27 |
| +kapsül | 20.00 | 42.09 | 2.02 | 9.89 |
| +S-layer | 20.00 | 45.36 | 2.18 | 9.17 |
| +duvar | 20.00 | 55.18 | 2.65 | 7.54 |

Sitoplazma her satırda aynı; zarf büyüdükçe hücre büyüyor ve
(doğru şekilde) yavaşlıyor. `DRAG_REF_RADIUS` 10 → 27.6 yapıldı ki taban
hız dengesi korunsun — aksi halde bütün hücreler bir anda 2.76 kat
yavaşlardı.

> Önizlemede aynı hata bir kez daha çıktı: ölçek **dış** yarıçapa
> sığdırıldığı için katman eklemek ekrandaki sitoplazmayı yine
> küçültüyordu. Ölçek artık doğrudan sitoplazmadan alınıyor (ölçüldü:
> dört farklı katman kombinasyonunda da 1.935). `radius / zarf_orani` ile
> türetmek de bayat değer üretiyordu — yarıçap bir önceki yapılandırmadan,
> oran yenisinden geliyordu.

## Katman kalınlığı hücrenin kendi özelliği oldu

Kalınlık `lab.default_layers()`'ta **sabit** bir sayıydı: her hücrenin
duvarı 6.0, mukusu 7.0 idi ve değiştirilemiyordu. Oysa bunlar *olgun*
değerler — bir katman ilk kazanıldığında o kalınlıkta olmaz.

Artık her hücre kendi kalınlıklarını taşıyor
(`MembraneLogic.kalinlik`), editörden ayarlanabiliyor ve kayda giriyor.
Katman panelinde iki ayrı sayı var:

| | ne demek |
|---|---|
| **Kalınlık** | katmanın kendi kalınlığı (0.2–20) |
| **Yatırım** | onun üzerine eklenen güçlendirme (0–30) |

`katman_ekle` yeni katmanı **0.6** kalınlıkta doğuruyor
(`YENI_KATMAN_KALINLIK`), olgun 6.0'da değil. Bunun kendiliğinden çıkan
bir sonucu var: sertlik eşiği 1.0 olduğu için **taze bir duvar hücreyi
henüz sertleştirmiyor** — önce kalınlaşması gerekiyor. Ölçüldü: yeni duvar
takılı hücre hâlâ fagosite edilebiliyor, kalınlık 6.0'a çıkınca
edilemiyor. Evrim de aynı yoldan işliyor: altı `grow_defense('slayer')`
çağrısı ince S-layer'ı 0.60 → 1.95 kalınlaştırıyor.

Kalınlık geometriye ve yarıçapa gerçekten giriyor (duvar 2 → 18 birim:
hücre yarıçapı 48.6 → 74.8 px), gözenek geometrisi de onunla yeniden
üretiliyor.

> **Test altyapısı yine sızdırdı.** `test_kalinlik.py` de
> `importlib.reload(game_settings)` kullanıyordu; reload `save_all`'ın
> no-op yamasını geri alıyor ve testin bozduğu bellek içi ayarlar diske
> yazılabiliyor. Bu ikinci kez oldu ve kullanıcının kaydındaki katmanları
> `var_*: false` yaptı. Kayıt temizlendi; test artık reload yerine
> `get_entity_organs`'ı geçici olarak besliyor.
