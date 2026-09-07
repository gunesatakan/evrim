"""Soy imzası: kuorum duyusuna dayalı akraba tanıma.

Gerçekte bakteri sinyal molekülünü bir SENTAZ ile üretir (luxI ailesi) ve
bir RESEPTÖR ile okur (luxR ailesi). Bu ikisi operonda yan yanadır ve
birlikte kalıtılır.

Kritik nokta: ikisinin BİRBİRİNE UYMASI zorunludur. Sentaz tek başına
mutasyona uğrarsa molekül değişir, hücrenin kendi reseptörü onu artık
tanımaz ve hücre kendi akrabalarıyla - hatta kendi yavrularıyla -
konuşamaz hâle gelir. Bu şiddetle elenir.

Sonuç: imza KEYFİ ama KORUNMUŞ. Değişmesi için kilidin ve anahtarın
birlikte değişmesi gerekir; bu yüzden her bölünmede değil, nadiren ve
sıçramayla olur. Türleşmeyi kademeli sürüklenme değil, işte bu ender
eşleşmiş kırılma yapar.

Yüzey kimyasından farkı: yüzey kimyası "neden yapıldığın"ı söyler ve
yalan söylenemez; soy imzası "kimden geldiğin"i söyler ve taklit edilebilir.
"""

import random as _rnd

import game_settings


class LineageSignature:

    def __init__(self, synthase=None, receptor=None, rng=_rnd):
        alleles = int(game_settings.SIGNATURE_ALLELES)
        if synthase is None:
            synthase = rng.randrange(alleles)
        self.synthase = synthase
        # Varsayılan: kilit ve anahtar uyumlu doğar
        self.receptor = synthase if receptor is None else receptor
        # Kokunun son değişiminden bu yana biriken kalıtsal ıraksama
        self.divergence = 0.0

    # ---------- tanıma ----------

    def matches(self, other):
        """Bu hücre karşıdakini AKRABA olarak tanıyor mu?

        Tek yönlüdür: benim reseptörüm senin molekülünü okuyor mu? Kulak
        misafiri olmak (başkasının sinyalini okuyabilmek) bu yüzden
        mümkündür - gerçekte de öyle.
        """
        return self.receptor == other.synthase

    @property
    def is_self_compatible(self):
        """Kendi kokusunu okuyabiliyor mu?

        Okuyamıyorsa kendi soyunu da tanıyamaz: kırık sinyalleşme.

        ÖLÇÜLDÜ - şu an bu bir dezavantaj DEĞİL: 3 tohumda kırık hücrelerin
        yavru sayısı sağlamlarla eşit (0.43-1.25 vs 0.76-0.84) ve ölüm oranı
        ikisinde daha düşük çıktı. Sebep, akraba tanımanın henüz bir işe
        yaramaması: kin_response rastgele bir gen ve çoğunlukla 'ignore'a
        düşüyor, tanımayan hücre de yüzey kimyasına geri düşüyor.

        Gerçekte kuorum duyusu MALİYETLİ ORTAK DAVRANIŞLARI tetikler
        (biyofilm, biyolüminesans, virülans) - faydası akrabayla
        eşgüdümden gelir. Burada eşgüdümlenecek bir şey olmadığı için
        kilit-anahtar korunmasını yaratan seçilim baskısı da yok.
        Kanal çalışıyor ama henüz bedeli de ödülü de yok.
        """
        return self.receptor == self.synthase

    # ---------- kalıtım ----------

    def accumulate(self, changes, rng=_rnd):
        """Kalıtsal değişim biriktir; EŞİK aşılırsa koku değişir.

        Kokuyu bir zar atışı değil, gerçekten biriken ıraksama değiştirir.
        Bu yüzden hızlı değişen bir soy kokusunu erken yitirir, durağan bir
        soy nesiller boyu aynı kokar - ve iki torun kolu yeterince
        ayrıştığında birbirini artık tanımaz. Türleşme olayı budur.

        Gerçek mikrobiyoloji de eşeysiz organizmalarda böyle yapar: %95 ANI
        eşiği bir doğa yasası değil, birikmiş ıraksamanın ayrı tür saymaya
        yettiği uzlaşımsal noktadır.

        Koku değiştiyse True döner.
        """
        if changes <= 0:
            return False
        self.divergence += changes
        if self.divergence < game_settings.SCENT_DIVERGENCE_THRESHOLD:
            return False
        self.divergence = 0.0
        self._shift(rng)
        return True

    def _shift(self, rng=_rnd):
        """Eşik aşıldı: yeni koku. Kilit ve anahtar çoğunlukla birlikte gider."""
        alleles = int(game_settings.SIGNATURE_ALLELES)
        new = rng.randrange(alleles)
        if rng.random() < game_settings.SIGNATURE_COUPLED_RATIO:
            # Operon birlikte kopyalandı: yeni imza, hücre kendini hâlâ okur.
            # Türleşmenin gerçekleştiği ender olay budur.
            self.synthase = new
            self.receptor = new
        elif rng.random() < 0.5:
            self.synthase = new     # molekül değişti, reseptör eski kaldı
        else:
            self.receptor = new     # reseptör değişti, molekül eski kaldı

    def copy(self):
        return LineageSignature(self.synthase, self.receptor)

    def __repr__(self):
        tag = '' if self.is_self_compatible else ' KIRIK'
        return f"<soy s{self.synthase}/r{self.receptor}{tag}>"
