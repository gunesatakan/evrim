# Evrim Deneyi: özelleşmemiş hücreden avcıya

> **Amaç:** Bir kamçı, bir kemoreseptör ve tamamen rastgele bir davranış
> tablosuyla bırakılan hücrelerden zamanla kompleks hücreler gelişmesi;
> avlanmanın **emergent** olarak başlaması; savunma tiplerinin ortaya
> çıkması.

Bu belge, o hedefin önündeki engelleri ve her birinin nasıl ölçülüp
kaldırıldığını anlatır. Her madde bir **ölçümle** başlar — çünkü bu
sistemde "makul görünen" ile "işe yarayan" birbirini sık sık tutmuyor.

---

## 0. Başlangıç koşulu ve yöntem

**Başlangıç.** Bütün varlıklar aynı doğar: zar, sitoplazma (boyut 2),
iskelet, koful, ribozom, **bir kamçı**, **bir kemoreseptör**. Katman yok,
silah yok. Davranış tablosu rastgele.

**Roller sınıfa göre dağıtılmıyor.** Kaotropi/Notropi/Optropi ayrımı
yalnızca renk ve başlangıç konumu; kimin avcı kimin av olduğu hiçbir yerde
yazmıyor. Bunu bilerek yaptık: rolü kod dağıtırsa "avlanmanın kendiliğinden
başlaması" diye bir şey olamaz — başlamış olur.

**Ölçüm.** `systems/world.py` ekosistemin çizimden bağımsız çekirdeği;
`simulation.py` de onu kullanıyor. Böylece ölçülen dünya ile oynanan dünya
aynı kod. `arac/kos.py` birkaç tohumu paralel koşturur, `arac/rapor.py`
üç ölçütü tohumlar arası standart hataya göre değerlendirir.

---

## 1. Kemotaksi hiç çalışmıyordu

**Ölçüm.** Aynı dünyaya bırakılan takımlar, 120 saniyede aldıkları besin:

| takım | besin |
|---|---|
| çıplak (motorsuz) | 3.5 |
| yalnızca burun | 3.4 |
| yalnızca kamçı | **16.2** |
| kamçı + burun | 13.3 |

Kemoreseptör taşımak **net zarardı**. Böyle bir dünyada duyu organları
evrimleşemez; ikinci ölçüt (kaç/saldır öğrenmesi) için gereken
duyu–davranış bağlantısı hiç kurulamaz.

Üç ayrı sebep vardı:

**(a) Hücre kendi kokusunu duyuyordu.** Hücreler, kemoreseptörün okuduğu
aynı difüzyon alanına salgı bırakıyordu. Kendi sinyali kendi konumunda en
yüksek olduğu için — ve Weber-Fechner algıyı logaritmik sıkıştırdığı için —
besinin gradyanı onun altında kayboluyordu. Ölçüldü: 120 besinlik yığına
700 px uzaktaki bir hücre sabit 3.5–4.3 okuyor, Δ ±0.1 gürültü. Difüzyon
alanı artık yalnızca besin; hücrelerin birbirini koklaması zaten iki ayrı
yoldan var (iz sistemi ve koku menzili).

**(b) İki arama modu birbiriyle çelişiyordu.** Koku varsa run-and-tumble,
yoksa Lévy uçuşu çalışıyordu. Lévy süperdifüzyondur (koşular 10 saniyeye
kadar uzar); run-and-tumble ise saniyede bir dönen bir rastgele yürüyüştür.
Yani **koku almak, iyi bir arama stratejisini kötüsüyle değiştiriyordu.**
Artık tek arama var: taban keşif Lévy, koku yalnızca koşunun süresini
uzatıp kısaltıyor — E. coli'nin yaptığı da budur. Tumble açısı da düzgün
dağılım olmaktan çıktı (~60°), yoksa her dönüşte önceki koşunun yön
bilgisi siliniyordu.

**(c) Besin haritaya düzgün dağılmıştı.** Düzgün dağılım koku alanının
gradyanını düzler; tırmanılacak eğim kalmaz. Besin artık yama yama doğuyor
(deniz karı, çökelti, leş gibi).

**Ek: uzamsal gradyan.** İki kemoreseptör tek kemoreseptörden **kötüydü**.
Gerçekte tersinedir: birden fazla alıcı aynı anda farklı yerlerden okur,
yani uzamsal gradyan çıkarıp doğrudan o yöne dönebilir (amip, nötrofil).
Artık öyle — tek alıcı zamansal, iki alıcı uzamsal kemotaksi. Karmaşıklaşmanın
karşılığını veren gerçek bir kazanç.

---

## 2. Avlanma zararlı bir seçimdi

**Ölçüm.** Stilet taşıyan hücre 120 saniyede 1.34 besin alıyor; aynı
dünyadaki silahsız hücre 6.47.

Sebep basit bir fiyatlandırma hatası: bir hücrenin sitoplazma alanı 1256,
besin alanı 100 — yani **12.6 besinlik biyokütle**. Ama öldürmek 2 besin
(`PREY_FOOD_VALUE`), leşi ise 1 besin veriyordu. Avcı kavrarken
kıpırdayamıyor ve o sürede toplayabileceği yemi kaybediyor; karşılığında
aldığı 2 besin bu kaybı karşılamıyordu.

Artık değer bedenden çıkıyor ve **enerji korunumuna** bağlı: inşa bedeli +
depodaki artık, trofik verimle (0.5) çarpılı. Aç ölen az bırakır, tok ölen
çok.

---

## 3. Silah–zırh üçgeni

Tek bir silahın üstün gelmesi, çeşitliliği ve dolayısıyla üçüncü ölçütü
öldürür. İlk ölçümde tam olarak bu oluyordu: **toksin 32/32 sağ kalıyor,
diğer bütün takımlar siliniyordu.** Üç düzeltme:

**Bağışıklık allele bağlandı.** "Toksin taşıyan herkes her toksine
bağışıktır" kuralı, toksinlilerin birbirine dokunulmaz bir kartel kurmasına
yol açıyordu. Gerçekte kolisin üreticisi yalnızca **kendi** varyantına
bağışıktır. Her toksin geninin alleli var ve bölünmede nadiren mutasyona
uğruyor — bir varyant değişince o soy akrabalarının bağışıklığını yitirir.

**Zırh artık hasarı artırmıyor.** Ölçülen teslimat tablosunda bazı satırlar
zırh 0'dan 6'ya çıkarken yükseliyordu (toksin 0.654 → 0.856): duvar
örmek toksinden alınan hasarı %30 artırıyordu. Satırlar en yakın azalan
eğriye çekildi (PAVA); hiçbir ölçüm atılmadı, yalnızca fiziksel olarak
imkânsız yön kapatıldı.

**Lizin zırhın cevabı oldu.** 4 px menzilli, tutunmasız ve tek atışlık
haliyle hedefine hiç ulaşamıyordu (3/32 sağkalım). Gerçekteki karşılığı
zaten tutunmalı değil: *Lysobacter* ve miksobakteriler litik enzimi ortama
salar. Artık sürekli ve alan etkili; duvarı yok sayar, menzili kısadır ve
**bağışıklığı yoktur** — kendi soyunu da eritir.

Ortaya çıkan ilişki (izole ölçüm, 3 tohum × 120 sn):

```
toksin  ->  çıplağı yener (30/32),  duvarlıya yenilir (15/30 vs 30/30)
lizin   ->  duvarlıyı yener (30/30 vs 12/30),  çıplağı yakalayamaz
duvar   ->  toksini durdurur ama yavaşlatır,  lizine yem olur
çıplak  ->  hızlı, lizinden kaçar,  toksine yem olur
```

Duvarlının lizine yem olmasının sebebi kimyasal direnç değil **hız**:
zırf yarıçapı büyütür, büyük yarıçap sürüklenmeyi artırır. Yavaş av,
yavaş bir alan silahına yakalanır.

---

## 4. Evrimi donduran üç yapısal hata

Bunlar en sinsi olanlarıydı: hepsi makul görünüyordu ve hepsi seçilimi ya
durduruyor ya da tersine çeviriyordu.

**(a) Nüfus tavanı üremeyi durduruyordu.** Tavana ulaşınca bölünme
engelleniyordu. Ama mutasyon yalnızca bölünmede olur: bölünme yoksa
çeşitlilik de yok, seçilim de yok. Ölçüldü — ilk 100 saniyede 165 doğum,
sonraki 100 saniyede 19.

**(b) Tavan elemesi seçilimi tersine çeviriyordu.** "En düşük enerjili
hücreyi ele" kuralı makul görünüyor. Ama bölünen hücre önce bedeli öder,
sonra enerjisini ikiye böler — yani **her üreyen bir anda listenin dibine
iner ve ilk elenen o olur.** Hiç bölünmeyip enerjisini deposunda tutan ise
hep tepede kalır. Dünya, üreyeni cezalandırıp istifleyeni ödüllendiriyordu.
Sonuç ölçüldü: popülasyon 400 saniyede kamçısını ve kemoreseptörünü
**tamamen** yitirdi (1.00 → 0.00), organ sayısı 7.0'dan 5.0'a düştü.
Hücreler hareketsizleşip körleşti.

Artık kemostat seyrelmesi: yıkanma **rastgele**, yani kazandıran tek şey
kendini daha hızlı yerine koymak. Mikrobiyal evrim deneylerinin standart
düzeni de budur.

**(c) Metabolik marj yoktu.** Sindirim boru hattı en fazla 3.0 enerji/sn
gelir veriyordu, başlangıç hücresinin bakımı ise 2.18 — gelirin %73'ü
ayakta kalmaya gidiyordu. Yeni bir organ 0.12–0.63 enerji/sn götürür; iki
organ eklemek artığın tamamını siliyordu. **Karmaşıklık fiziksel olarak
karşılanamaz durumdaydı.** Aynı daralma kuşak süresini de belirliyordu:
166 enerjilik bölünme bedeli 0.82 artıkla ~200 saniyede toplanıyordu; 900
saniyelik bir koşu topu topu beş kuşak eder.

Besin enerjisi 30'dan 90'a çıkarıldı: artık bakımın üç katı gelir var ve
kuşak süresi ~20 saniye. Besin **tüketim** hızı değişmedi — yalnızca bir
besinin kalorisi arttı, ekosistemin akışı bozulmadı.

---

## 5. Sosyal öncelik geni

Davranış tablosu "yaklaş" ya da "saldır" dediğinde bu, beslenmeyi
**koşulsuz** bastırıyordu. Koku menzili beş gövde çapına çıkıp dünyada 200
hücre olunca her hücrenin her an bir komşusu var — yani kemotaksi hiç
çalışmıyor, burun bedelini ödüyor ama karşılığını alamıyordu.

Bu bir öncelik sorunudur ve cevabı dayatılmamalı: hangi durumda komşuyla
ilgilenileceği de bir **gendir** (`sosyal_oncelik`). 0'a yakın bir hücre
önce karnını doyurur, 1'e yakın olan komşusunun peşine düşer. Kaçmak bunun
dışında — yenmek her şeyi bitirir.

---

## 6. Silahlar hiç gelişmiyordu

`WeaponLogic.grow` içinde artış hasara bölünüyordu (`power += GROW/DAMAGE`);
stilet için bu 0.01 eder, yani bir yükseltme hasarı binde bir artırıyordu.
Fagositoz ise `DAMAGE = 0` olduğu için tam `GROW` kadar büyüyordu ve
aradaki uçurumun bir gerekçesi yoktu. İstenen şey "kompleks saldırı
silahlarıyla donanmış hücreler" ise silahın gelişebilmesi gerekir.

Benzer şekilde gövde büyümesi 0.01 iken fagositozun boy eşiğine ulaşmak
aynı geni 90 kez çekmeyi gerektiriyordu — hiçbir soy "irileşip yutan"
olamıyordu.

---

## 7. Hızlandırma

Bir kuşak ~20 simülasyon saniyesi sürdüğü için evrimi izlemek 1x'te uzun
sürer. `time_scale` doğrudan `dt` ile çarpılıyordu; 4x demek kare başına
0.067 saniyelik bir adım demekti ve o ölçekte hücre bir karede kendi
yarıçapı kadar yer değiştirir, temas fiziği kaçar. Artık 1'in üstündeki
değerler kare başına **kaç kez** adım atılacağını söylüyor (16x'e kadar) ve
kare bütçesi aşılırsa kırpılıyor: fizik bozulmadan gerçek hızlanma.

Tuşlar: `1..7` = 0.25x … 16x, `+/-` kademe, `BOŞLUK` duraklat.

---

## 8. Performans

Evrim uzun koşu ister; ölçüm yapılamayan bir sistem geliştirilemez.
Kare maliyeti ~4.5 kat düşürüldü:

- koku difüzyonu numpy ile (aynı sonuç, birebir doğrulandı),
- iz noktalarında doğrusal sönümün **saklanması değil hesaplanması**,
  ve toplam nokta sayısına tavan,
- besin / hücre / çakışma için uzamsal ızgaralar (O(N²) → O(N·k)),
- koku puanı ve zarf oranı önbelleği,
- organı olmayan hücrede `can_see` erken çıkış,
- algı havuzunun tekilleştirilmesi (her komşu iki kez değerlendiriliyordu).
