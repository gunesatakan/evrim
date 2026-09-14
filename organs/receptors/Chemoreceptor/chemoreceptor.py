import math
import pygame
from organs.base_organ import BaseOrgan
from .logic_chemoreceptor import ChemoreceptorLogic
from .view_chemoreceptor import draw_chemoreceptor, draw_chemoreceptor_debug

class Chemoreceptor(BaseOrgan):
    # Debug modu (tüm kemoreseptörler için)
    DEBUG_ENABLED = True

    def __init__(self, attachment_angle=0, length=5.0):
        # Gövde sınırında olsun
        super().__init__(attachment_angle, offset_distance=1.0)
        self.logic = ChemoreceptorLogic(length)

        # Debug bilgileri
        self.debug_tip_pos = None
        self.debug_direction = None
        self.debug_intensity = 0.0
        self.debug_food_positions = []  # Algılanan besinlerin pozisyonları
        self.debug_is_locked = False  # Koku kilidinde mi?

    def get_tip_position(self, parent):
        """Kemoreseptörün uç pozisyonunu döndürür"""
        organ_pos = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        outward_dir = (organ_pos - parent.pos).normalize() if (organ_pos - parent.pos).length() > 0 else parent.direction
        return organ_pos + outward_dir * self.logic.length

    def _cekirdek_yaricapi(self, parent):
        """Sitoplazmanin yaricapi. Organ ZARFA degil buraya tutunur."""
        govde = getattr(getattr(parent, 'body', None), 'logic', None)
        r = getattr(govde, 'radius', None)
        return float(r) if r else float(getattr(parent, 'radius', 10.0))

    def _taban_ve_boy(self, parent):
        """Kokun konumu, disa dogru yon ve TOPLAM boy.

        Kemoreseptor zarfin dis yuzeyine tutunuyordu; zarf disari
        eklendiginden ucu merkezden ~65 px oteye dusuyor, koku alaninin
        bittigi yerden ornekliyordu. Artik SITOPLAZMA kenarindan cikiyor
        ve zarfi delip disariya uzaniyor - gercek bir alicinin duvari
        gecmesi gibi. Boylece hem yakin mesafede kokuyu kaybetmiyor hem de
        ekranda katmanlarin uzerinden gectigi goruluyor.
        """
        cek = self._cekirdek_yaricapi(parent)
        aci = math.atan2(parent.direction.y, parent.direction.x) + self.attachment_angle
        disa = pygame.math.Vector2(math.cos(aci), math.sin(aci))
        taban = parent.pos + disa * cek
        # Zarfi gecip disariya cikacak kadar uzun olmali
        zarf = max(0.0, float(getattr(parent, 'radius', cek)) - cek)
        return taban, disa, zarf + self.logic.length

    def sample_environment(self, parent, scent_env, dt=None):
        """Organın BOYUNCA örnekle, en güçlü okumayı al.

        Önceden yalnızca UÇ noktası okunuyordu ve bu iki şeyi bozuyordu:

        1. Hücre besine yaklaşınca uç besini GEÇİP arkasına düşüyor ve
           okuma azalıyordu (ölçüldü: 60 px uzakta 5.16, 20 px uzakta
           0.27). Yani yaklaşmak kokuyu kaybettiriyordu.
        2. Uç, hücre merkezinden yarıçap + uzunluk kadar ötede. Zarf
           dışarı eklendiğinden bu mesafe ~65 px'e çıktı; koku alanı ise
           ~60 px'e kadar var. Organ, kokunun bittiği yerden örnekliyordu.

        Sınıfta bunun için zaten bir çok-noktalı örnekleyici vardı
        (`_get_all_sample_points`, U yapısının tabanı + iki kolu) ama
        hiçbir yerden çağrılmıyordu. Artık o kullanılıyor ve zara yakın
        taban noktaları da işin içine girdiği için organ, hücre yüzeyi
        ile ucu ARASINDAKİ tüm aralığı tarıyor.
        """
        en_yuksek = 0.0
        for nokta in self._get_all_sample_points(parent):
            ham = scent_env.get_concentration(nokta.x, nokta.y)
            if ham > en_yuksek:
                en_yuksek = ham
        olculen, algi = self.logic.olc_ve_algila(en_yuksek, dt)
        # Olcum pencere boyunca da biriktirilir: hucre bu alicinin
        # ORTALAMASINI obur alicilarinkiyle karsilastirip kokunun yonunu
        # bulur (bkz. Organism.update, uzamsal gradyan).
        if dt:
            self.logic.ortalamaya_ekle(olculen, dt)
        return algi

    def _get_all_sample_points(self, parent):
        """
        Kemoreseptörün U-yapısı boyunca tüm sample noktalarını döndürür.

        U-yapısı:
        - Taban çizgisi (sol-sağ)
        - Sol kol (tabandan uca)
        - Sağ kol (tabandan uca)

        Her çizgi boyunca pixel aralıklarla noktalar oluşturulur.
        """
        import pygame

        points = []

        # Kemoreseptör geometrisi
        organ_pos, outward_dir, length = self._taban_ve_boy(parent)
        width = length * 0.8
        perp = pygame.math.Vector2(-outward_dir.y, outward_dir.x)

        # U-yapısının köşe noktaları
        left_base = organ_pos + perp * (width / 2.0)
        right_base = organ_pos - perp * (width / 2.0)
        left_tip = left_base + outward_dir * length
        right_tip = right_base + outward_dir * length

        # Pixel aralığı (yaklaşık 2px)
        pixel_step = 2.0

        # 1. Taban çizgisi (left_base → right_base)
        base_length = width
        base_steps = max(1, int(base_length / pixel_step))
        for i in range(base_steps + 1):
            t = i / base_steps
            point = left_base + (right_base - left_base) * t
            points.append(point)

        # 2. Sol kol (left_base → left_tip)
        arm_steps = max(1, int(length / pixel_step))
        for i in range(1, arm_steps + 1):  # 0 zaten tabanda eklendi
            t = i / arm_steps
            point = left_base + (left_tip - left_base) * t
            points.append(point)

        # 3. Sağ kol (right_base → right_tip)
        for i in range(1, arm_steps + 1):
            t = i / arm_steps
            point = right_base + (right_tip - right_base) * t
            points.append(point)

        return points

    def draw(self, screen, parent):
        # Cizim ORNEKLEME ile ayni geometriyi kullanir: neyi gorursen
        # orayi kokluyor. Dis organlar zarftan SONRA cizildigi icin
        # katmanlarin uzerinde gorunur.
        pos, outward_dir, boy = self._taban_ve_boy(parent)
        draw_chemoreceptor(screen, pos, outward_dir, boy, boy)

        # Debug çizimi
        if Chemoreceptor.DEBUG_ENABLED and self.debug_tip_pos:
            draw_chemoreceptor_debug(
                screen,
                parent.pos,
                self.debug_tip_pos,
                self.debug_direction,
                self.debug_intensity,
                self.debug_food_positions,
                self.debug_is_locked,
                0.0
            )

    def grow(self):
        self.logic.grow()

    def touch_probes(self, parent):
        """Temas testinin kullandığı iki noktayı döndürür: (taban, uç).

        Bu değerler yalnızca ebeveynin konumuna/yönüne bağlıdır, test edilen
        koku noktasına değil. Bu yüzden kare başına BİR KEZ hesaplanıp binlerce
        iz noktası için tekrar kullanılabilir; is_touching her çağrıda
        atan2/cos/sin'i baştan hesaplıyordu.
        """
        organ_pos = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        # Reseptörün ucu (U'nun kollarının ulaştığı yer)
        outward_dir = (organ_pos - parent.pos).normalize() if (organ_pos - parent.pos).length() > 0 else parent.direction
        return organ_pos, organ_pos + outward_dir * self.logic.length

    @staticmethod
    def probes_touch(probes, target_pos, target_radius):
        """Önceden hesaplanmış (taban, uç) ikilisi noktaya değiyor mu?"""
        base, tip = probes
        # Basit bir çarpışma kontrolü: Merkeze veya uca yakınlık
        return (base.distance_to(target_pos) < target_radius or
                tip.distance_to(target_pos) < target_radius)

    @staticmethod
    def probes_touch_xy(bx, by, tx, ty, px, py, r2):
        """Ayni test, duz kayan noktalarla.

        Kare basina milyonlarca kez calisan tek yer burasi; Vector2
        olusturmak ve karekok almak burada olcuulebilir bir yuk.
        Kiyaslama KARELERLE yapilir, sonuc birebir aynidir.
        """
        dx = bx - px; dy = by - py
        if dx * dx + dy * dy < r2:
            return True
        dx = tx - px; dy = ty - py
        return dx * dx + dy * dy < r2

    def is_touching(self, parent, target_pos, target_radius):
        """U-yapısı koku noktasına fiziksel olarak temas ediyor mu?"""
        return self.probes_touch(self.touch_probes(parent), target_pos, target_radius)