# Evrim

Tek hücrelilerin yaşadığı, gerçek zamanlı bir **yapay yaşam** simülasyonu.

Hücreler bir kamçı, bir kemoreseptör ve **tamamen rastgele bir davranış
tablosuyla** doğar. Kimin avcı kimin av olduğu hiçbir yerde yazmaz. Silah
taşımak, zırh örmek, kaçmak ya da saldırmak — hepsi seçilimin sonucudur.

```bash
pip install pygame numpy
python launcher.py
```

`launcher.py` başlatıcıdır: varlıkların organlarını düzenleyebilir, dünya
ve evrim parametrelerini değiştirebilir, sonra simülasyonu başlatabilirsin.
Doğrudan `python simulation.py` de çalışır.

---

## Ekranda ne var

| tuş | işlev |
|---|---|
| `1` … `7` | zaman ölçeği: 0.25x, 0.5x, 1x, 2x, 4x, 8x, 16x |
| `+` / `-` | bir kademe hızlan / yavaşla |
| `BOŞLUK` | duraklat |
| `tıklama` | hücreyi incele (organlar, enerji, genom, algı) |
| `L` | seçili hücrenin **büyütülmüş kesiti** (katmanlar ve gözenekler) |
| `H` | koku ısı haritası |
| `E` | **evrim paneli** — popülasyonun bütünü |
| `fare tekerleği` | yakınlaştır (x64'e kadar; gözenekler tek tek okunur) |

1x'in üstündeki hızlar `dt`'yi büyütmez, kare başına **birden çok adım**
atar: fizik bozulmaz, gerçekten hızlanır. Bir kuşak ~20 simülasyon
saniyesi sürdüğü için evrimi izlemek genelde 8x–16x ister.

---

## Hücre

Bir hücre organlardan kurulur ve her organın bir bedeli vardır — bakım
enerjisi, yer kaplaması, sürüklenme.

- **Zar** — enerji üretimi (ETC), kalsiyum sinyali ve savunma katmanları:
  mukus, kapsül, S-tabakası, hücre duvarı. Her katman ayrı bir saldırı
  kanalına karşı işe yarar; hiçbiri her şeye karşı iyi değildir.
- **Sitoplazma** — gövde. Besin kapasitesi ve sindirim burada.
- **Kemoreseptör** — koku. *Tek alıcı* zamansal kemotaksi yapabilir
  ("az önce daha mı iyiydi?"); *iki veya daha fazla alıcı* uzamsal gradyan
  okuyup doğrudan kaynağa dönebilir — amip ve nötrofilin yaptığı gibi.
- **Fotoreseptör / mekanoreseptör** — görme konisi ve işitme yarıçapı.
  Organ yoksa duyu da yoktur; bedava algı yok.
- **Kamçı ve siller** — itki ve tork. Asimetrik yerleşim hücreyi döndürür.
- **Silahlar** — stilet, harpun (T6SS), nematosist, toksin (bakteriosin),
  lizin (litik enzim), fagositoz.

Hareket düşük Reynolds sayısı fiziğine göre: atalet yok, hız kuvvetle
orantılı, sürüklenme yarıçapla artar. Zırh örmek seni yavaşlatır.

---

## Silah–zırh üçgeni

Hiçbir silah üstün değil; matris de bir yerde tablo olarak yazılı değil.
Her şey iki alandan türer: saldırı hangi **kanaldan** geliyor (mekanik /
kimyasal / yutma) ve **temas** gerekiyor mu.

```
toksin  ->  çıplağı yener,   duvarda gözeneklerde durur
lizin   ->  duvarı yok sayar, ama hızlı olanı yakalayamaz
duvar   ->  toksini durdurur, seni yavaşlatır, lizine yem eder
çıplak  ->  hızlıdır, lizinden kaçar, toksine yem olur
```

Toksin bağışıklığı **allele özgüdür**: üretici yalnızca kendi
bakteriosinine bağışıktır. Bölünmede allel nadiren değişir; değiştiğinde o
soy akrabalarının bağışıklığını yitirir.

---

## Davranış genomu

Tepki ayrık bir emir değil, **sürekli bir sayıdır**:

```
        -1 ────────── 0 ────────── +1
        kaç        yoksay        saldır
      (tam güç)   (motor yok)  (tam güç)
```

- **İşaret** ne yapılacağını söyler.
- **Büyüklük** ne kadar motor enerjisi harcanacağını söyler. İtki eforla
  doğrusal, motor **gücü** eforun karesiyle artar — kaçmak ve saldırmak
  gerçek bir karardır, bedava bir refleks değil.
- Bir eşiği aşan pozitif değer saldırı taahhüdüdür; silahlar ancak o zaman
  ateşlenir.

Hücre bu tepkiyi üç ayrı kanaldan okur: **ışık** (renk tonu), **ses**
(kaynağın boyutu) ve **koku**. Koku ekseni ayrık sınıf değil süreklidir ve
hedefin puanı **algılayana göre** okunur — aynı hücre küçüğe devasa,
iriye önemsiz kokar.

Ayrıca üç ayrı gen daha var: **akraba tepkisi** (kuorum duyusuna dayalı
soy imzası), **kairomon tepkisi** (avcının av yediğini ele veren metabolik
sızıntı) ve **sosyal öncelik** (komşuyla mı ilgileneyim, karnımı mı
doyurayım).

---

## Kalıtım

Üç ayrı gen tipi vardır ve karıştırılmamalıdır:

| | ne kodlar |
|---|---|
| `Genome` | hangi organın **gelişeceği** — ağırlıklı yükseltme torbası |
| `Morphology` | hangi organın **var olduğu ve nerede durduğu** |
| `BehaviorGenome` | hangi uyarana **ne tepki** verileceği |

Hücre besini sindirdiğinde ikiye bölünür. Ebeveyn diye bir şey yoktur:
ortada iki yavru vardır, ikisi de ayrı ayrı mutasyona uğrar ve gelişim
için bağımsız çekiliş yapar. Yapı mutasyonu bölünmede yeni bir organ ya da
zar katmanı kazandırabilir, birini kaybettirebilir, ya da bir organın
açısını kaydırabilir — vücut planı da evrimleşir.

Nüfus tavanı bir duvar değil, **kemostat seyrelmesidir**: fazlalık
rastgele yıkanır. Böyle bir dünyada kazandıran tek şey kendini daha hızlı
yerine koymaktır.

---

## Ölçüm araçları

Evrim göz kararı değerlendirilemez. `arac/` altındakiler çizimden bağımsız
çalışır (`systems/world.py`, oyunla **aynı** ekosistem çekirdeği):

```bash
python arac/kos.py --sure 2500 --her 250 --tohum 1 2 3 --cikti arac/sonuc/kosu.json
python arac/izle.py arac/sonuc/kosu          # süren koşuyu özetle
python arac/rapor.py arac/sonuc/kosu.json    # üç ölçütü değerlendir
python arac/grafik.py arac/sonuc/kosu.json   # tek sayfalık HTML rapor
python arac/gradyan.py --takim av toksin --sabit   # bir organ işe yarıyor mu
python arac/rekabet.py                       # evrimleşmiş davranış vs rastgele
```

`arac/gradyan.py` tek bir soruyu sorar: bu organı taşımak gerçekten daha
çok besin/sağkalım getiriyor mu? Kalıtılabilir çeşitlilik varsa ama farklı
başarı yoksa ortaya çıkan şey evrim değil sürüklenmedir.

`arac/rekabet.py` deneysel evrimin standart sınamasını yapar: evrimleşmiş
popülasyonu ikiye kopyalar, bir gruba **rastgele** davranış tablosu verir
(bedenler birebir aynı kalır) ve ikisini aynı kaba koyar.

---

## Belgeler

`manifesto/` altında tasarımın gerekçeleri var:

- `architecture_manifesto.md` — duyusal ve genetik mimari, kemotaksi
- `evrim_deneyi.md` — evrimin önündeki engellerin ölçümü ve kaldırılması
- `katman_igne_fizigi.md` — katman/gözenek geometrisi ve teslimat modeli
- `koku_ve_kimlik.md` — koku puanı, soy imzası, akraba tanıma
- `savas_ve_olum_plani.md` — saldırı kanalları ve ölüm

Kodun içindeki yorumlar da aynı ilkeyi izler: bir sayı neden o değer,
hangi ölçüm onu belirledi ve önceki hâli neyi bozuyordu — hepsi yazılıdır.
