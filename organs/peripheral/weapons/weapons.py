"""Saldiri organlarinin cepheleri (BaseOrgan uzerine).

Her silah ayni arayuze sahiptir; farklari logic sinifinda tanimlidir.
Launcher'dan oyun oncesi eklenebilir ve avlanma odulu cekilisinde de
havuzda bulunurlar (karar 1).
"""
import math

import pygame
from organs.base_organ import BaseOrgan
from .logic_weapons import (StyletLogic, HarpoonLogic, NematocystLogic,
                            ToxinLogic, LysinLogic, PhagocytosisLogic)
from .view_weapons import draw_weapon, draw_weapon_socket, LAB_BOY


class BaseWeapon(BaseOrgan):
    LOGIC = None
    DISPLAY_LENGTH = 10.0

    def __init__(self, attachment_angle=0, power=1.0):
        super().__init__(attachment_angle, offset_distance=1.0)
        self.logic = self.LOGIC(power)
        self.last_target_pos = None
        # Bunlar sinif degil, mermiye ait durumdur. Sinif seviyesinde
        # birakilinca iki ayni silah ilk atistan sonra ayni basligi paylasiyor
        # gibi gorunebiliyor ve cizim/fizik birbirinden kopuyordu.
        self.mermi = None
        self.baslik_t = 0.0
        self.geri_tepme = 0.0
        self._atis_sure = 0.0

    def aim_angle(self, parent):
        """Organın dünya üzerindeki bakış yönü (radyan)."""
        return (math.atan2(parent.direction.y, parent.direction.x)
                + self.attachment_angle)

    def can_hit(self, parent, target):
        """Menzil VE yön kontrolü.

        Organ konumu artık isabeti belirliyor: öndeki bir stilet arkadaki
        hedefi delemez. Eskiden yalnızca mesafeye bakılıyordu ve silahın
        nereye takıldığı savaşta hiçbir anlam taşımıyordu - oysa projenin
        geri kalanında (itme, tork, koku örnekleme, görüş konisi) organ
        konumu her zaman belirleyici.
        """
        lg = self.logic
        if not lg.in_range(parent, target):
            return False
        if lg.arc >= 180.0:
            return True                      # yönsüz (toksin)
        to_t = target.pos - parent.pos
        d = to_t.length()
        if d <= 1e-6:
            return True
        diff = abs(((math.atan2(to_t.y, to_t.x) - self.aim_angle(parent)
                     + math.pi) % (2 * math.pi)) - math.pi)
        # Hedefin açısal yarı genişliği sayılır: büyük hedefi vurmak kolaydır
        # (can_see de aynı yaklaşımı kullanıyor)
        half = math.atan2(target.radius, max(1.0, d))
        return diff <= math.radians(lg.arc) + half

    #: Atis cizgisi ekranda bu kadar kalir. Once `last_target_pos` her
    #  karede siliniyordu: cizgi tek bir kare (33 ms) yasiyor, yani hic
    #  gorunmuyordu. Kullanici nematosistin atesledigini hic gormedi.
    ATIS_GORUNME = 0.35

    #: Ates edince silah geriye tepiyor (lab: 14 px, 60 px/sn ile doner).
    GERI_TEPME = 14.0

    #: Basligin disarida kalabilecegi en uzun sure (sn). Fiziksel bir
    #  sinir: uzatilmis bir tup ya da bosalmis bir iplik sonsuza kadar
    #  disarida kalamaz - hedef olur, kopar ya da geri cekilir. Ayni
    #  zamanda guvenlik agi: mermi baska bir yoldan listeden dusup
    #  organi ilelebet kilitli birakmasin.
    BASLIK_SURESI = 12.0

    #: TEK BASLIK. Organ bir sayac degil bir CISIMDIR: harpunun bir
    #  mizragi, stiletin bir sivri ucu, nematosistin bir kapsulu vardir.
    #  O disaridayken ikincisi YOKTUR. (Sinif duzeyinde varsayilan:
    #  eski kayitlardan yuklenen organlarda da tanimli olsun.)
    mermi = None
    baslik_t = 0.0

    # ---- basligin durumu --------------------------------------------

    def baslik_disarida(self):
        """Organin tek basligi su an disarida mi?"""
        m = self.mermi
        if m is None:
            return False
        if getattr(m, 'dead', False) or getattr(m, 'bitti', False):
            return False
        return True

    def baslik_gonder(self, mermi):
        """Basligi yola cikar: organ artik dolu."""
        self.mermi = mermi
        self.baslik_t = 0.0

    def baslik_geri(self):
        """Baslik dondu/tukendi: YENIDEN KURULUM simdi baslar.

        Bekleme suresi atis aninda degil basligin DONDUGU anda baslar -
        T6SS kilifi ic tup geri cekilmeden ClpV ile sokulup yeniden
        kurulamaz, bosalmis nematosist kapsulu de ancak bosaldiktan
        sonra yenisiyle degistirilir.
        """
        self.mermi = None
        self.baslik_t = 0.0
        self.logic.trigger()

    def atisa_hazir(self, parent=None):
        """Organ ates edebilir mi? IKI kosul: baslik icerde VE kurulmus.

        DONUSU BURADA DA YAKALA. Basligin donusu yalnizca `update` icinde
        isleniyordu, oysa kare sirasi `fire_weapons` -> `update`: baslik
        onceki karenin sonunda dondugunde ates once sorulu yor ve organ
        "bos ve hazir" gorunup hemen yeniden atiyordu. Kurulum sayaci hic
        baslamiyor, silah saniyede 14 mizrak firlatiyordu. Donus hangi
        cagri once gelirse orada, BIR KEZ islenir.
        """
        if self.mermi is not None and not self.baslik_disarida():
            self.baslik_geri()
        if self.baslik_disarida():
            return False
        return self.logic.ready
    #: Lab tasiyicisi (0-8) olan silahlar lab sekilleriyle, lab olcegiyle cizilir.
    LAB_TASIYICI = True

    def update(self, dt, parent=None):
        # BASLIK SAYACI. Disarida gecen sure olculur; mermi bir sekilde
        # ortadan kaybolduysa (hedef oldu, liste temizlendi) organ
        # sonsuza kadar kilitli kalmasin.
        if self.mermi is not None:
            self.baslik_t += dt
            if not self.baslik_disarida() or self.baslik_t >= self.BASLIK_SURESI:
                self.baslik_geri()
        self.logic.update(dt)
        self._atis_sure = getattr(self, '_atis_sure', 0.0) - dt
        if self._atis_sure <= 0.0:
            self.last_target_pos = None
        self.geri_tepme = max(0.0, getattr(self, 'geri_tepme', 0.0) - dt * 60.0)

    def atis_isaretle(self, hedef_pos):
        """Atildi: cizgi ATIS_GORUNME saniye boyunca cizilsin; geri tepme."""
        self.last_target_pos = hedef_pos
        self._atis_sure = self.ATIS_GORUNME
        self.geri_tepme = self.GERI_TEPME

    def grow(self):
        self.logic.grow()

    RETRACTED_RATIO = 0.25    # boştayken görünen uzunluk oranı

    def is_deployed(self, parent):
        """Silah şu an çıkarılmış mı?

        Doğadaki delici yapıların çoğu (Pfiesteria pedunkülü, Vampyrella)
        sürekli dışarıda durmaz; besleneceği anda uzatılır. Bu yüzden
        tutunma gerektiren silahlar boştayken kısa bir çıkıntı olarak,
        yalnızca hedefe kenetlendiğinde tam boyda çizilir.
        Sürekli dışarıda olan tipler (suctoria dokunaçları) için bu ayrım
        yoktur; onlar zaten hep açık kabul edilir.
        """
        if not self.logic.REQUIRES_BIND:
            return True
        return getattr(parent, 'bound_target', None) is not None

    def draw(self, screen, parent):
        pos = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        delta = pos - parent.pos
        outward = delta.normalize() if delta.length() > 0 else parent.direction
        # DISPLAY_LENGTH bir SABIT: hucre kucultulup buyutulurken silahlar
        # ayni boyda kaliyordu (dunya gorunumunde hucreden buyuk, kesitte
        # kayip). Cizim olcegi konaktan okunur.
        k = float(getattr(parent, 'ciz_olcegi', 1.0))
        ad = self.__class__.__name__
        ci = getattr(self.logic, 'carrier', None) if self.LAB_TASIYICI else None
        if ci is None:
            length = self.DISPLAY_LENGTH * self.logic.power * k
            if not self.is_deployed(parent):
                length *= self.RETRACTED_RATIO
            draw_weapon(screen, ad, pos, outward, length,
                        self.logic.ready, self.last_target_pos, olcek=k)
            return
        # LAB OLCEGI: lab sekilleri 110 px yaricapli hucre icin cizildi
        # (weapon_len tablosu). Organ, hucre yaricapiyla ORANLI cizilir -
        # mermi fizigi de ayni oranla calisir (hiz_olcegi = r/110).
        # Yakinlastirmada hucreyi_ciz yaricapi zaten buyutmus olur.
        birim = float(parent.radius) / 110.0 * self.logic.power
        if not self.is_deployed(parent):
            birim *= self.RETRACTED_RATIO
        length = LAB_BOY.get(int(ci), 46.0) * birim
        if self.baslik_disarida():
            # Atis basligi artik Shot tarafindan, gercek dunya konumunda
            # cizilir. Burada yalnizca hucreye gomulu soket kalir; tam boy
            # kapsulu tekrar cizmek onu hucreden ayrilmis ikinci bir silah
            # gibi gosteriyordu.
            draw_weapon_socket(
                screen, pos, outward, length, olcek=k,
                carrier=int(ci), recoil=0.0)
            return
        draw_weapon(screen, ad, pos, outward, length,
                    self.logic.ready, self.last_target_pos, olcek=k,
                    carrier=int(ci), marker=int(getattr(self.logic, 'marker', 0)),
                    recoil=float(getattr(self, 'geri_tepme', 0.0)),
                    merkez=parent.pos,
                    # Cizilen molekuller organin FIILEN tasidigi stok.
                    stok=float(getattr(self.logic, 'stok', 0.0)),
                    payload=int(getattr(self.logic, 'payload', 0)))


class Stylet(BaseWeapon):
    LOGIC = StyletLogic
    DISPLAY_LENGTH = 12.0


class Harpoon(BaseWeapon):
    LOGIC = HarpoonLogic
    DISPLAY_LENGTH = 9.0


class Nematocyst(BaseWeapon):
    LOGIC = NematocystLogic
    DISPLAY_LENGTH = 8.0


class Toxin(BaseWeapon):
    LOGIC = ToxinLogic
    DISPLAY_LENGTH = 14.0     # halka yaricapi


class Lysin(BaseWeapon):
    LOGIC = LysinLogic
    DISPLAY_LENGTH = 7.0


class Phagocytosis(BaseWeapon):
    LOGIC = PhagocytosisLogic
    DISPLAY_LENGTH = 10.0
    LAB_TASIYICI = False


WEAPON_CLASSES = {
    "Stylet": Stylet, "Harpoon": Harpoon, "Nematocyst": Nematocyst,
    "Toxin": Toxin, "Lysin": Lysin, "Phagocytosis": Phagocytosis,
}
