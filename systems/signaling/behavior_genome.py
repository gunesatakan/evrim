"""Davranış genomu: uyaran → tepki. Tepki AYRIK DEĞİL, SÜREKLİ.

Bu, projedeki üçüncü gen tipidir ve diğer ikisiyle karıştırılmamalı:

    Genome      : hangi organın GELİŞECEĞİ   (yükseltme torbası)
    Morphology  : hangi organın NEREDE olduğu (vücut planı)
    BehaviorGenome : hangi uyarana NE TEPKİ verileceği (davranış planı)

---------------------------------------------------------------------------
TEPKİ BİR SPEKTRUMDUR
---------------------------------------------------------------------------

Önceden dört ayrık tepki vardı: kaç / yaklaş / saldır / yoksay. Bunun iki
ayrı sakıncası ölçüldü:

1. **Mutasyonun tırmanabileceği bir eğim yoktu.** Bir gen mutasyona
   uğradığında "rastgele başka bir tepkiye dön" oluyordu; yani birikmiş
   her uyum tek hamlede siliniyordu. Seçilim küçük iyileştirmeleri
   biriktiremez, yalnızca zar atışının sonucunu kabul eder. Popülasyonun
   davranış eğilimi bu yüzden sıfır civarında salınıyordu — öğrenme değil
   sürüklenme.

2. **"Ne yapıyorum" ile "ne kadar enerji harcıyorum" birbirinden
   kopuktu.** Kaçmak da yaklaşmak da aynı motor gücüyle yapılıyordu.

Artık tek bir sayı her ikisini birden kodluyor:

        -1 ────────── 0 ────────── +1
        kaç        yoksay        saldır
      (tam güç)   (motor yok)  (tam güç)

  * **İşaret** ne yapılacağını söyler: pozitif = üzerine git,
    negatif = uzaklaş.
  * **Büyüklük** ne kadar enerji harcanacağını söyler. Uçlar en pahalı
    davranışlardır (itki ∝ efor, ama motor gücü ∝ efor²  — hız iki katına
    çıkarken bedel dörde katlanır, gerçek sürüklenme fiziğinde olduğu gibi).
  * Ortadaki değerler ilgisiz sürüklenme: hafifçe yaklaşma, hafifçe
    uzaklaşma, hiç umursamama.

Belli bir eşiği (`ATAK_ESIGI`) aşan pozitif değer SALDIRI taahhüdüdür:
silahlar ancak o zaman ateşlenir. Yani "saldırmak" ayrı bir emir değil,
üzerine yeterince kararlı gitmenin sonucu.

Hiçbir yerde "güçlüden kaç" gibi bir kural yazılı değildir ve yazılmamalı.
Şans eseri silah kazanmış bir hücrenin etrafında, ona saldıranlar ölür,
kaçanlar yaşar. Kural kodda değil, ölülerde birikir.
"""
import bisect
import colorsys
import math
import random as _rnd

import game_settings


def etiket(deger):
    """Sürekli tepkinin okunabilir adı (yalnızca gösterim için)."""
    if deger >= game_settings.ATAK_ESIGI:
        return 'saldir'
    if deger <= -game_settings.KACIS_ESIGI:
        return 'kac'
    if deger > 0.15:
        return 'yaklas'
    if deger < -0.15:
        return 'uzaklas'
    return 'yoksay'


class BehaviorGenome:
    #: Yalnızca gösterim ve ölçüm için: spektrumun beş okunabilir bölgesi.
    ETIKETLER = ('kac', 'uzaklas', 'yoksay', 'yaklas', 'saldir')

    # 'scent' ve 'sound' artik TABLODA DEGIL: ayrik sinif yerine SUREKLI
    # spektrum kullaniyorlar. Ayrik sinifta kucuk bir genetik degisim
    # hucreyi bir anda "hic tanimadik biri" yapiyordu; ustelik mutasyon
    # bir kutudan otekine SICRAMA oldugu icin secilim kucuk iyilestirmeleri
    # biriktiremiyordu.
    #
    # 'light' de spektrum oldu - ama CEMBERSEL bir spektrum. Renk tonu
    # sirali degildir (kirmizi maviden "daha buyuk" degildir) ama SUREKLIDIR
    # ve kapalidir: 0 ile 100 ayni yerdir. Bu yuzden kesme noktalari bir
    # cember uzerinde durur ve son bant ilk banda komsudur. Sabit alti kutu
    # yerine kesme noktalarinin kendisi gen olunca populasyon renk cemberini
    # ONEMLI OLDUGU YERDEN boler.
    #
    # Tabloda yalnizca kairomon kaldi: kutulari SIRALI ve azalan bir
    # sizinti olcegi, ama ayri bir eksene gerek yok - alti kutu yeter.
    STIMULI = ('kairomone',)

    # --- KOKU SPEKTRUMU ---
    # Hucre koku eksenini kendi KESME NOKTALARIYLA boler ve her banda
    # kendi TEPKISINI atar. Ikisi de gendir, ikisi de evrimlesir: "zayifa
    # saldir, gucluden kac" bir varsayim olarak dayatilmaz - cikarsa
    # kendiliginden cikar, tersi de evrimlesebilir.
    SPECTRUM_CUTS = 4          # 4 kesme -> 5 bant
    SPECTRUM_BANDS = 5

    # --- SES SPEKTRUMU ---
    # Kulak bir BASINC DALGASI duyar ve o dalgayi uretenin BOYUTU sirali,
    # surekli bir buyukluktur - tam olarak koku gibi. Bu yuzden ayni
    # makine: kendi kesme noktalari, kendi bantlari, ikisi de gen.
    #
    # Eksen yine GORELIDIR: "benden buyuk mu kucuk mu". Ayni hidrodinamik
    # bozulma, kucuk bir hucre icin devasa bir tehdit, iri bir hucre icin
    # onemsiz bir kipirdanmadir.
    SES_CUTS = 4
    SES_BANDS = 5

    # --- RENK SPEKTRUMU (cembersel) ---
    # Kesme sayisi = bant sayisi: cemberde n kesme n dilim yapar.
    RENK_CUTS = 4
    HUE_BINS = 6      # renk tonu kutusu
    LEVEL_BINS = 3    # zayıf / orta / güçlü

    @staticmethod
    def relative_position(target_value, self_value):
        """Hedefin koku puanini ALGILAYANA GORE 0-100 eksenine yerlestir.

        Mutlak puan okunmaz. Herkes gelistikce puanlar sisecegi icin mutlak
        sinirlar eskir; oran ise sabit kalir. Bu ayni zamanda kokunun
        "herkes icin farkli deger" tasimasini saglar: ayni hucre kucuge
        devasa, iriye onemsiz kokar.

        50 = benimle esit, 75 = benim iki katim, 25 = yarim.
        """
        if self_value <= 0.0 or target_value <= 0.0:
            return 50.0
        x = 50.0 + 25.0 * math.log2(target_value / self_value)
        return 0.0 if x < 0.0 else (100.0 if x > 100.0 else x)

    def spectrum_response(self, x):
        """0-100 KOKU eksenindeki bir konuma verilen tepki (-1..1)."""
        return self.scent_bands[bisect.bisect_right(self.scent_cuts, x)]

    def ses_tepkisi(self, x):
        """0-100 SES (goreli boyut) eksenindeki bir konuma verilen tepki."""
        return self.ses_bands[bisect.bisect_right(self.ses_cuts, x)]

    def renk_tepkisi(self, x):
        """0-100 RENK CEMBERINDEKI bir tona verilen tepki.

        Cembersel: 0 ile 100 ayni yerdir, bu yuzden son kesmenin
        otesindeki ton ilk banda dusher (modulo).
        """
        i = bisect.bisect_right(self.renk_cuts, x) % len(self.renk_bands)
        return self.renk_bands[i]

    @staticmethod
    def renk_ekseni(color):
        """RGB rengi 0-100 ton eksenine cevir (cembersel)."""
        r, g, b = (max(0.0, min(1.0, c / 255.0)) for c in color[:3])
        h, _s, _v = colorsys.rgb_to_hsv(r, g, b)
        return h * 100.0

    @staticmethod
    def aciliyet(sinyal, ref=None):
        """Duyulan sinyal ne kadar ACIL? 0..1.

        Sinyal esik biriminde gelir: 1 = tam duyma sinirinda, buyuk deger
        = gurultulu/yakin/hizli. Aciliyet tepkinin YONUNU degil
        BUYUKLUGUNU olcekler - yani harcanacak motor eforunu.

        Uzaktan gelen zayif bir kipirdanma hafif bir yonelim uretir; tam
        uzerine gelen bir sey tam gucle tepki. Boylece "ne" bilgisi
        spektrumdan, "ne kadar" bilgisi dalganin siddetinden gelir.
        """
        import math as _m
        if sinyal <= 0.0:
            return 0.0
        if ref is None:
            ref = game_settings.SES_ACILIYET_REF
        return min(1.0, _m.log(sinyal + 1.0) / _m.log(max(1.1, ref) + 1.0))

    @staticmethod
    def _rastgele_tepki(rng=_rnd):
        """Baslangicta tepkiler duzgun dagilmis: uclar da orta da esit."""
        return rng.uniform(-1.0, 1.0)

    def __init__(self, table=None, kin_response=None,
                 scent_cuts=None, scent_bands=None, sosyal_oncelik=None,
                 ses_cuts=None, ses_bands=None,
                 renk_cuts=None, renk_bands=None):
        # {(tip, sınıf, seviye): -1..1}
        self.table = dict(table) if table else {}
        # Akraba tanindiginda ne yapilacagi. Soy imzasi "X sinifina ne
        # tepki vereyim" sorusunu sormaz, tek bir soru sorar: BU BENDEN Mi?
        # O yuzden 18 satir degil, TEK gen yeter. Yine de evrimlesir:
        # "kardesini yeme" cikabilir de cikmayabilir de - kodlanmaz.
        self.kin_response = (float(kin_response) if kin_response is not None
                             else self._rastgele_tepki())
        # Koku spektrumu: kesme noktalari (sirali) + her bandin tepkisi
        self.scent_cuts = (sorted(scent_cuts) if scent_cuts is not None
                           else sorted(_rnd.uniform(0.0, 100.0)
                                       for _ in range(self.SPECTRUM_CUTS)))
        self.scent_bands = (list(scent_bands) if scent_bands is not None
                            else [self._rastgele_tepki()
                                  for _ in range(self.SPECTRUM_BANDS)])
        # SOSYAL ONCELIK: baskasiyla ilgilenmek mi, karnini doyurmak mi?
        #
        # Tablo bir tepki verdiginde bu karar BESLENMEYI bastiriyordu. Koku
        # menzili bir hucrenin ~5 govde capina ciktigi ve dunyada yuzlerce
        # hucre oldugu icin her hucrenin HER AN bir komsusu var; yani
        # kemotaksi hic calismiyordu. Burun ve kamci bedelini oduyor ama
        # karsiligini alamiyordu (olculdu: kemoreseptor 400 saniyede
        # populasyondan tamamen silindi).
        #
        # Hangi durumda komsuyla ilgilenilecegi de bir GENDIR. Kacmak bunun
        # disinda kalir - yenmek her seyi bitirir.
        self.sosyal_oncelik = (float(sosyal_oncelik)
                               if sosyal_oncelik is not None
                               else _rnd.random())
        # Ses spektrumu: koku gibi, kendi kesme noktalari ve bantlariyla.
        self.ses_cuts = (sorted(ses_cuts) if ses_cuts is not None
                         else sorted(_rnd.uniform(0.0, 100.0)
                                     for _ in range(self.SES_CUTS)))
        self.ses_bands = (list(ses_bands) if ses_bands is not None
                          else [self._rastgele_tepki()
                                for _ in range(self.SES_BANDS)])
        # Renk spektrumu: cember uzerinde kesme noktalari + bant tepkileri.
        self.renk_cuts = (sorted(renk_cuts) if renk_cuts is not None
                          else sorted(_rnd.uniform(0.0, 100.0)
                                      for _ in range(self.RENK_CUTS)))
        self.renk_bands = (list(renk_bands) if renk_bands is not None
                           else [self._rastgele_tepki()
                                 for _ in range(self.RENK_CUTS)])

    # ---------- kodlama ----------

    # KAIROMON: avcinin AV YEDIGINI ele veren metabolik sizinti.
    #
    # Feromondan ve allomondan farki, faydanin ALICIYA gitmesidir: yayan
    # taraf bundan zarar gorur ama engelleyemez, cunku sinyal degil ARTIKTIR.
    # Daphnia balik kairomonunu algilayip miğfer ve diken gelistirir; ve
    # tepkisi, baligin YAKINDA Daphnia yemis olmasiyla orantili olarak
    # guclenir - yani kritik olan avcinin varligi degil, AVLANMIS OLMASI.
    #
    # Bu yuzden koku kimliginden bagimsiz bir kanal: koku "kim oldugunu"
    # soyler ve soyla birlikte kalicidir; kairomon "ne yaptigini" soyler
    # ve soner. Tehlike bilgisini tasiyan tek kanal budur.
    KAIROMONE_BINS = 6
    _KAIRO_EDGES = (0.05, 0.3, 0.8, 1.5, 3.0)

    @staticmethod
    def kairomone_bin(value):
        """Sizinti siddetini kutuya cevir: 0 = temiz, 5 = yeni ve cok yemis."""
        for i, e in enumerate(BehaviorGenome._KAIRO_EDGES):
            if value < e:
                return i
        return len(BehaviorGenome._KAIRO_EDGES)

    @staticmethod
    def level_bin(value, reference):
        """Şiddeti 0-2 arası kutuya çevir (referansa göre oran)."""
        if reference <= 0:
            return 0
        ratio = value / reference
        if ratio >= 0.66:
            return 2
        if ratio >= 0.33:
            return 1
        return 0

    # ---------- tablo ----------

    @classmethod
    def random_table(cls, rng=_rnd):
        """Başlangıç: her uyaran kombinasyonuna RASTGELE tepki."""
        table = {}
        for stim in cls.STIMULI:
            n_class = cls.KAIROMONE_BINS if stim == 'kairomone' else cls.HUE_BINS
            for c in range(n_class):
                for lvl in range(cls.LEVEL_BINS):
                    table[(stim, c, lvl)] = cls._rastgele_tepki(rng)
        return table

    @classmethod
    def random(cls, rng=_rnd):
        return cls(cls.random_table(rng), cls._rastgele_tepki(rng),
                   sorted(rng.uniform(0.0, 100.0) for _ in range(cls.SPECTRUM_CUTS)),
                   [cls._rastgele_tepki(rng) for _ in range(cls.SPECTRUM_BANDS)],
                   rng.random(),
                   sorted(rng.uniform(0.0, 100.0) for _ in range(cls.SES_CUTS)),
                   [cls._rastgele_tepki(rng) for _ in range(cls.SES_BANDS)],
                   sorted(rng.uniform(0.0, 100.0) for _ in range(cls.RENK_CUTS)),
                   [cls._rastgele_tepki(rng) for _ in range(cls.RENK_CUTS)])

    def respond(self, stim, cls_idx, level):
        return self.table.get((stim, cls_idx, level), 0.0)

    def sosyali_sec(self, koku_siddeti):
        """Komsuyu mu takip edeyim, besini mi?

        Karsilastirma sureklidir: gen esigi, o anda alinan besin kokusunun
        siddetiyle olculur. Koku ne kadar guclyse besini birakmak o kadar
        zorlasir.
        """
        return (self.sosyal_oncelik * game_settings.SOSYAL_ESIK
                >= koku_siddeti)

    def mutate(self, rng=_rnd):
        """Her gen düşük olasılıkla BİRAZ kayar - sıçramaz.

        Ayrık tabloda mutasyon "rastgele başka bir tepkiye dön" idi ve
        birikmiş uyumu tek hamlede siliyordu. Sürekli bir eksende küçük bir
        tedirginlik, seçilime tırmanabileceği bir eğim bırakır: biraz daha
        kararlı saldıran ya da biraz daha erken kaçan bir yavru, ebeveyninin
        yanında az bir farkla öne geçebilir ve o fark birikebilir.

        KAÇ genin gerçekten değiştiğini döndürür - bu sayı koku kimliğinin
        ıraksama birikimini besler.
        """
        rate = game_settings.BEHAVIOR_MUTATION_RATE
        sigma = game_settings.BEHAVIOR_MUTATION_SIGMA
        changes = 0

        def kaydir(v):
            return min(1.0, max(-1.0, v + rng.gauss(0.0, sigma)))

        for key in self.table:
            if rng.random() < rate:
                self.table[key] = kaydir(self.table[key])
                changes += 1
        if rng.random() < rate:
            self.kin_response = kaydir(self.kin_response)
            changes += 1

        # Kesme noktalari da kayar.
        cut_sigma = game_settings.SPECTRUM_MUTATION_SIGMA
        moved = []
        for c in self.scent_cuts:
            if rng.random() < rate:
                c = min(100.0, max(0.0, c + rng.gauss(0.0, cut_sigma)))
                changes += 1
            moved.append(c)
        self.scent_cuts = sorted(moved)
        for i in range(len(self.scent_bands)):
            if rng.random() < rate:
                self.scent_bands[i] = kaydir(self.scent_bands[i])
                changes += 1
        # Ses spektrumu da ayni bicimde kayar.
        ses_moved = []
        for c in self.ses_cuts:
            if rng.random() < rate:
                c = min(100.0, max(0.0, c + rng.gauss(0.0, cut_sigma)))
                changes += 1
            ses_moved.append(c)
        self.ses_cuts = sorted(ses_moved)
        for i in range(len(self.ses_bands)):
            if rng.random() < rate:
                self.ses_bands[i] = kaydir(self.ses_bands[i])
                changes += 1
        # Renk cemberi de ayni bicimde kayar.
        renk_moved = []
        for c in self.renk_cuts:
            if rng.random() < rate:
                c = (c + rng.gauss(0.0, cut_sigma)) % 100.0
                changes += 1
            renk_moved.append(c)
        self.renk_cuts = sorted(renk_moved)
        for i in range(len(self.renk_bands)):
            if rng.random() < rate:
                self.renk_bands[i] = kaydir(self.renk_bands[i])
                changes += 1
        # Sosyal oncelik de sureli bir gen.
        if rng.random() < rate:
            self.sosyal_oncelik = min(1.0, max(
                0.0, self.sosyal_oncelik + rng.gauss(0.0, 0.15)))
            changes += 1
        return changes

    # ---------- gözlem ----------

    def counts(self):
        """Tabloda her etiket bolgesinden kacar tane var."""
        out = {r: 0 for r in self.ETIKETLER}
        for v in self.table.values():
            out[etiket(v)] += 1
        return out

    def describe(self, stim='light'):
        """Bir uyaran tipi için tabloyu kısa metne çevir."""
        rows = []
        kisa = {'kac': 'K', 'uzaklas': 'u', 'yoksay': '-',
                'yaklas': 'y', 'saldir': 'S'}
        for c in range(self.HUE_BINS):
            rows.append("".join(kisa[etiket(self.respond(stim, c, l))]
                                for l in range(self.LEVEL_BINS)))
        return " ".join(rows)
