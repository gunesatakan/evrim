"""Davranış genomu: uyaran → tepki tablosu.

Bu, projedeki üçüncü gen tipidir ve diğer ikisiyle karıştırılmamalı:

    Genome      : hangi organın GELİŞECEĞİ   (yükseltme torbası)
    Morphology  : hangi organın NEREDE olduğu (vücut planı)
    BehaviorGenome : hangi uyarana NE TEPKİ verileceği (davranış planı)

Her uyaran üç bilgiyle kodlanır:

    (tip, sınıf, seviye) → tepki

  tip    : 'light' | 'sound' | 'scent'
  sınıf  : NE olduğu  — ışık için renk tonu kutusu (0-5)
  seviye : NE KADAR   — 0 zayıf, 1 orta, 2 güçlü

Bu ayrım, "yüksek sese yaklaşırken düşük sesten kaçmak" ya da "farklı
renklere farklı davranmak" gibi paternleri mümkün kılar. Sınıf ve seviye
AYRIK kutulardır: sürekli değer kullanılsa genom sınırsız büyür ve mutasyon
anlamını yitirirdi.

Tüm hücreler rastgele bir tabloyla başlar; tablo bölünmede aktarılır ve
mutasyona uğrar. Böylece davranış paterni zamanla evrimleşir.
"""
import bisect
import colorsys
import math
import random as _rnd

import game_settings


class BehaviorGenome:
    # 'attack' olmadan silah kullanılamaz; 'approach' olmadan beslenme
    # davranışı kodlanamaz (kemotaksi bu tabloya girmeli).
    RESPONSES = ('flee', 'approach', 'attack', 'ignore')

    # 'scent' artik TABLODA DEGIL: ayrik sinif yerine SUREKLI spektrum
    # kullaniyor (asagidaki scent_cuts/scent_bands). Ayrik sinifta kucuk
    # bir genetik degisim hucreyi bir anda "hic tanimadik biri" yapiyordu.
    STIMULI = ('light', 'sound', 'kairomone')

    # --- KOKU SPEKTRUMU ---
    # Hucre koku eksenini kendi KESME NOKTALARIYLA boler ve her banda
    # kendi TEPKISINI atar. Ikisi de gendir, ikisi de evrimlesir: "zayifa
    # saldir, gucluden kac" bir varsayim olarak dayatilmaz - cikarsa
    # kendiliginden cikar, tersi de evrimlesebilir.
    SPECTRUM_CUTS = 4          # 4 kesme -> 5 bant
    SPECTRUM_BANDS = 5
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
        """0-100 eksenindeki bir konuma bu hucrenin verdigi tepki."""
        return self.scent_bands[bisect.bisect_right(self.scent_cuts, x)]

    def __init__(self, table=None, kin_response=None,
                 scent_cuts=None, scent_bands=None, sosyal_oncelik=None):
        # {(tip, sınıf, seviye): tepki}
        self.table = dict(table) if table else {}
        # Akraba tanindiginda ne yapilacagi. Soy imzasi "X sinifina ne
        # tepki vereyim" sorusunu sormaz, tek bir soru sorar: BU BENDEN Mi?
        # O yuzden 18 satir degil, TEK gen yeter. Yine de evrimlesir:
        # "kardesini yeme" cikabilir de cikmayabilir de - kodlanmaz.
        self.kin_response = kin_response or _rnd.choice(self.RESPONSES)
        # Koku spektrumu: kesme noktalari (sirali) + her bandin tepkisi
        self.scent_cuts = (sorted(scent_cuts) if scent_cuts is not None
                           else sorted(_rnd.uniform(0.0, 100.0)
                                       for _ in range(self.SPECTRUM_CUTS)))
        self.scent_bands = (list(scent_bands) if scent_bands is not None
                            else [_rnd.choice(self.RESPONSES)
                                  for _ in range(self.SPECTRUM_BANDS)])
        # SOSYAL ONCELIK: baskasiyla ilgilenmek mi, karnini doyurmak mi?
        #
        # Tablo "yaklas" ya da "saldir" dediginde bu karar BESLENMEYI
        # bastiriyordu. Koku menzili bir hucrenin ~5 govde capina ciktigi
        # ve dunyada 200 hucre oldugu icin her hucrenin HER AN bir komsusu
        # var; yani kemotaksi hic calismiyordu. Burun ve kamci bedelini
        # oduyor ama karsiligini alamiyordu. Olculdu: 400 saniyede
        # kemoreseptor populasyondan tamamen silindi (1.00 -> 0.00), organ
        # sayisi 7.0'dan 5.0'a dustu - yani hucreler hareketsizlesip
        # korlesti. "Kompleks hucreler gelismesi" beklenirken tam tersi
        # oluyordu.
        #
        # Bu bir oncelik sorunudur ve cevabi dayatilmamali: hangi durumda
        # komsuyla ilgilenilecegi de bir GENDIR. 0'a yakin bir hucre once
        # karnini doyurur, 1'e yakin olan komsusunun pesine duser. Kacmak
        # bunun disindadir - yenmek her seyi bitirir.
        self.sosyal_oncelik = (float(sosyal_oncelik)
                               if sosyal_oncelik is not None
                               else _rnd.random())

    # ---------- kodlama ----------

    @staticmethod
    def hue_bin(color):
        """RGB rengi ayrık ton kutusuna çevir (0-5)."""
        r, g, b = (max(0.0, min(1.0, c / 255.0)) for c in color[:3])
        h, _s, _v = colorsys.rgb_to_hsv(r, g, b)
        return int(h * BehaviorGenome.HUE_BINS) % BehaviorGenome.HUE_BINS

    @staticmethod
    def size_bin(radius):
        """Ses sınıfı: kaynağın boyutu.

        Akustikte büyük cisim pes, küçük cisim tiz ses üretir. Böylece
        "büyük bir şeyin sesinden kaç, küçük olana yaklaş" gibi paternler
        kodlanabilir - kullanıcının istediği "yüksek/düşük ses ayrımı".
        """
        edges = (6, 10, 15, 22, 32)      # 6 kutu
        for i, e in enumerate(edges):
            if radius < e:
                return i
        return len(edges)

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
                    table[(stim, c, lvl)] = rng.choice(cls.RESPONSES)
        return table

    @classmethod
    def random(cls, rng=_rnd):
        return cls(cls.random_table(rng), rng.choice(cls.RESPONSES),
                   sorted(rng.uniform(0.0, 100.0) for _ in range(cls.SPECTRUM_CUTS)),
                   [rng.choice(cls.RESPONSES) for _ in range(cls.SPECTRUM_BANDS)],
                   rng.random())

    def sosyali_sec(self, koku_siddeti):
        """Komsuyu mu takip edeyim, besini mi?

        Karsilastirma sureklidir: gen esigi, o anda alinan besin kokusunun
        siddetiyle olculur. Koku ne kadar guclyse besini birakmak o kadar
        zorlasir.
        """
        return (self.sosyal_oncelik * game_settings.SOSYAL_ESIK
                >= koku_siddeti)

    def respond(self, stim, cls_idx, level):
        return self.table.get((stim, cls_idx, level), 'ignore')

    def mutate(self, rng=_rnd):
        """Her girdi düşük olasılıkla başka bir tepkiye döner.

        KAÇ girdinin gerçekten değiştiğini döndürür - bu sayı koku
        kimliğinin ıraksama birikimini besler.
        """
        rate = getattr(game_settings, 'BEHAVIOR_MUTATION_RATE', 0.04)
        changes = 0
        for key in self.table:
            if rng.random() < rate:
                new_r = rng.choice(self.RESPONSES)
                if new_r != self.table[key]:
                    changes += 1
                self.table[key] = new_r
        if rng.random() < rate:
            new_r = rng.choice(self.RESPONSES)
            if new_r != self.kin_response:
                changes += 1
            self.kin_response = new_r

        # Kesme noktalari SICRAMAZ, kayar. Mutasyonun kucuk bir tedirginlik
        # olmasi seciline egim tirmanma imkani verir; ayrik tabloda mutasyon
        # "rastgele baska bir tepkiye don" oldugu icin bu mumkun degildi.
        sigma = game_settings.SPECTRUM_MUTATION_SIGMA
        moved = []
        for c in self.scent_cuts:
            if rng.random() < rate:
                c = min(100.0, max(0.0, c + rng.gauss(0.0, sigma)))
                changes += 1
            moved.append(c)
        self.scent_cuts = sorted(moved)
        for i in range(len(self.scent_bands)):
            if rng.random() < rate:
                new_r = rng.choice(self.RESPONSES)
                if new_r != self.scent_bands[i]:
                    changes += 1
                self.scent_bands[i] = new_r
        # Sosyal oncelik SURELI bir gen: sicramaz, kayar.
        if rng.random() < rate:
            self.sosyal_oncelik = min(1.0, max(0.0, self.sosyal_oncelik
                                               + rng.gauss(0.0, 0.15)))
            changes += 1
        return changes

    # ---------- gözlem ----------

    def counts(self):
        out = {r: 0 for r in self.RESPONSES}
        for r in self.table.values():
            out[r] += 1
        return out

    def describe(self, stim='light'):
        """Bir uyaran tipi için tabloyu kısa metne çevir."""
        rows = []
        short = {'flee': 'K', 'approach': 'Y', 'attack': 'S', 'ignore': '-'}
        for c in range(self.HUE_BINS):
            rows.append("".join(short[self.respond(stim, c, l)]
                                for l in range(self.LEVEL_BINS)))
        return " ".join(rows)
