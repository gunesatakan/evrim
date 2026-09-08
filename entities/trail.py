import pygame
import time

class TrailPoint:
    # Ekleme sırası. Izgara sorgusu noktaları ekleme sırasından farklı bir
    # düzende döndürdüğü için, tespit edilen noktalar toplanmadan önce bu
    # numaraya göre sıralanır; böylece ağırlıklı ortalamanın toplama sırası
    # ızgara öncesiyle birebir aynı kalır (kayan nokta sonucu değişmesin).
    _next_seq = 0

    #: Her iz noktasi, boyutu ne olursa olsun bu surede silinir.
    OMUR = 20.0

    __slots__ = ("pos", "owner_uid", "direction", "max_intensity",
                 "decay_per_second", "radius", "timestamp", "life_time",
                 "seq", "dogum", "_saat", "x", "y", "r2", "owner_scent")

    def __init__(self, x, y, owner_uid, direction, radius, saat, simdi,
                 owner_scent=0.0):
        self.pos = pygame.math.Vector2(x, y)
        self.owner_uid = owner_uid
        # Izi birakanin KOKU PUANI. Iz, sahibinin kim oldugunu tasimali:
        # bulan hucre buna kendi davranis tablosuyla karar verir - kacar,
        # takip eder ya da umursamaz. Sahipsiz bir iz yalnizca "biri
        # gecmis" der ve tek yapilabilecek sey korkmaktir.
        self.owner_scent = float(owner_scent)
        self.direction = pygame.math.Vector2(direction)

        # 1. Koku Yoğunluğu Hesaplama (Hacim Oranı x 10)
        # Formül: (Alan / Standart Alan) * 10 => (r^2 / 100) * 10 = r^2 / 10
        self.max_intensity = (radius ** 2) / 10.0

        # 2. Azalma Oranı: Her saniye azami değerin %5'i
        # Bu sayede her iz boyutu ne olursa olsun 20 saniyede silinir.
        self.decay_per_second = self.max_intensity * 0.05

        self.radius = radius
        self.timestamp = time.time()
        self.life_time = self.OMUR

        # Yogunluk artik SAKLANMIYOR, dogum zamanindan hesaplaniyor.
        #
        # Eskiden her kare butun noktalar dolasilip tek tek azaltiliyordu.
        # Populasyon 40 hucreye ciktiginda bu 5000 nokta x 60 kare eder ve
        # karenin en pahali islemi haline gelir - oysa azalma DOGRUSAL ve
        # butun noktalar icin ayni: okunacagi anda hesaplanabilir.
        # Ekleme sirasi: izgara sorgusu noktalari farkli duzende
        # dondurdugu icin, agirlikli ortalama alinmadan once buna gore
        # siralanir (toplama sirasi degisince sonuc kayan noktada oynar).
        self.seq = TrailPoint._next_seq
        TrailPoint._next_seq += 1

        self.dogum = simdi
        self._saat = saat            # [t] - yoneticinin paylasilan saati
        # Temas testi saniyede milyonlarca kez calisiyor. Vector2 uzerinden
        # distance_to cagirmak yerine duz kayan noktalar tutulur.
        self.x = float(x)
        self.y = float(y)
        self.r2 = float(radius) * float(radius)

    @property
    def current_intensity(self):
        v = self.max_intensity - self.decay_per_second * (self._saat[0] - self.dogum)
        return v if v > 0.0 else 0.0

class TrailManager:
    # Uzamsal ızgara hücre boyutu. Tipik sorgu yarıçapı (hücre yarıçapı +
    # kemoreseptör uzunluğu + iz yarıçapı) ~55px olduğu için 64 seçildi.
    CELL = 64

    #: Ayni anda yasayabilecek en fazla iz noktasi.
    #
    #  Nokta sayisi NUFUSLA carpiliyordu: 200 hucre x 6 nokta/sn x 20 sn
    #  omur = 24.000 canli nokta, ve her hucre her karede bunlarin
    #  yuzlercesiyle temas testi yapiyordu (olculdu: karenin %29'u).
    #  Tavan, izin ekolojik islevini (baskasinin gectigi yeri okumak)
    #  bozmadan maliyeti nufustan bagimsiz kilar - kalabalikta izler
    #  daha kisa omurlu olur, ki dogrusu da budur.
    MAX_POINTS = 6000

    def __init__(self):
        # Simulasyon saati. Liste olmasinin sebebi iz noktalarinin buna
        # REFERANSLA bakmasi: yoneticinin saati ilerleyince butun
        # noktalarin yogunlugu tek hamlede guncellenmis olur.
        self._saat = [0.0]
        self.points = []
        # {(cx, cy): [TrailPoint, ...]} - noktalar oluşturulduktan sonra
        # hareket etmediği için ızgara yalnızca ekleme/ölme anında değişir.
        self._grid = {}
        self._max_radius = 0.0
        # (tür, yarıçap, alfa) -> hazır yüzey. Nokta başına yüzey ayırmak
        # kare başına binlerce ayırma demekti.
        self._stamp_cache = {}

    @property
    def max_point_radius(self):
        """Yaşayan en büyük iz noktasının yarıçapı (sorgu payı için)."""
        return self._max_radius

    def _cell(self, x, y):
        c = self.CELL
        return (int(x // c), int(y // c))

    def add_point(self, x, y, owner_uid, direction, radius, owner_scent=0.0):
        p = TrailPoint(x, y, owner_uid, direction, radius,
                       self._saat, self._saat[0], owner_scent)
        self.points.append(p)
        self._grid.setdefault(self._cell(x, y), []).append(p)
        if radius > self._max_radius:
            self._max_radius = radius
        if len(self.points) > self.MAX_POINTS:
            self._en_eskiyi_dus()

    def _en_eskiyi_dus(self):
        p = self.points.pop(0)
        kova = self._grid.get(self._cell(p.pos.x, p.pos.y))
        if kova:
            try:
                kova.remove(p)
            except ValueError:
                pass

    def update(self, dt):
        """Saati ilerlet, SURESI DOLANLARI dus.

        Eskiden her karede butun izgara sifirdan kuruluyordu. Oysa iz
        noktasi olusturulduktan sonra KIMILDAMAZ: hucresi hic degismez.
        Ustelik hepsi tam OMUR saniye yasadigi icin liste zaten olum
        sirasinda; bu yuzden yalnizca BASTAN dusmek yeter.
        """
        self._saat[0] += dt
        simdi = self._saat[0]
        pts = self.points
        n = 0
        omur = TrailPoint.OMUR
        while n < len(pts) and simdi - pts[n].dogum >= omur:
            n += 1
        if not n:
            return
        grid = self._grid
        for p in pts[:n]:
            hucre = self._cell(p.pos.x, p.pos.y)
            kova = grid.get(hucre)
            if kova:
                try:
                    kova.remove(p)
                except ValueError:
                    pass
                if not kova:
                    del grid[hucre]
        del pts[:n]
        # En buyuk yaricap yalnizca eleme oldugunda tazelenir
        self._max_radius = max((q.radius for q in pts), default=0.0)

    def query(self, pos, radius):
        """pos çevresindeki yarıçap içindeki hücrelerin noktaları.

        ÜST KÜME döndürür (hücre köşelerindeki noktalar yarıçapın dışında
        kalabilir); kesin mesafe testi çağıran tarafta yapılmalıdır.
        """
        c = self.CELL
        cx0 = int((pos.x - radius) // c)
        cx1 = int((pos.x + radius) // c)
        cy0 = int((pos.y - radius) // c)
        cy1 = int((pos.y + radius) // c)
        grid = self._grid
        out = []
        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                bucket = grid.get((cx, cy))
                if bucket:
                    out.extend(bucket)
        return out

    def draw(self, screen, bolge=None):
        """Izleri ciz. `bolge` verilirse yalnizca oradakiler.

        Kirpma (set_clip) ekrana yazmayi engeller ama Python dongusu yine
        butun noktalari dolasir - 6000 nokta demek kare basina 6000 bosa
        yineleme demek. Uzamsal izgara zaten var; yakinlastirilmis karede
        yalnizca gorunen kutulari sormak yeter.
        """
        cache = self._stamp_cache
        blit = screen.blit
        if bolge is not None:
            c = self.CELL
            noktalar = []
            for cy in range(int(bolge.top // c), int(bolge.bottom // c) + 1):
                for cx in range(int(bolge.left // c), int(bolge.right // c) + 1):
                    b = self._grid.get((cx, cy))
                    if b:
                        noktalar.extend(b)
        else:
            noktalar = self.points
        for p in noktalar:
            intensity_ratio = p.current_intensity / p.max_intensity
            if intensity_ratio <= 0: continue

            # Görsel netlik için alpha hesaplaması
            alpha = int(120 * intensity_ratio)
            # İz boyutu yoğunlukla birlikte hafifçe daralsın
            draw_radius = int(p.radius * (0.4 + 0.6 * intensity_ratio))
            if draw_radius <= 0: continue

            kind = 0 if "kaotropi" in p.owner_uid else 1
            key = (kind, draw_radius, alpha)
            s = cache.get(key)
            if s is None:
                color = (200, 100, 100, alpha) if kind == 0 else (150, 150, 150, alpha)
                s = pygame.Surface((draw_radius*2, draw_radius*2), pygame.SRCALPHA)
                pygame.draw.circle(s, color, (draw_radius, draw_radius), draw_radius)
                cache[key] = s

            blit(s, (int(p.pos.x - draw_radius), int(p.pos.y - draw_radius)))

    def get_nearby_trails(self, pos, radius, ignore_uid=None):
        nearby = []
        for p in self.query(pos, radius):
            if ignore_uid and p.owner_uid == ignore_uid:
                continue
            if pos.distance_to(p.pos) <= radius:
                nearby.append(p)
        return nearby
