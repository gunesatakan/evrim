"""
Scalar Scent Field - Grid-based diffusion environment.

Yiyecekler grid'e koku ekler, koku evaporate olur ve diffuse eder.
Organizmalar grid'den skalar konsantrasyon okur (O(1)).

Koku bulutunun karakteristik yarıçapı L = sqrt(D/k) ile belirlenir;
burada D = diff_rate * cell_size^2 / 4 ve k = evap_rate. Buharlaşma çok
düşük tutulursa bulutlar birbirine karışıp haritayı tek bir platoya
çevirir ve kemotaksi için gereken gradyan kaybolur.
"""
import array
import math

import pygame
import game_settings

try:
    import numpy as _np
except ImportError:      # numpy yoksa oyun yine calisir, sadece yavastir
    _np = None


class ScentEnvironment:
    def __init__(self, world_width, world_height, cell_size=None):
        if cell_size is None:
            cell_size = game_settings.SCENT_CELL_SIZE
        self.cell_size = cell_size
        self.cols = world_width // cell_size   # 60
        self.rows = world_height // cell_size  # 40
        self.total = self.cols * self.rows      # 2400

        # IZGARA BIR 'array' - LISTE DEGIL.
        #
        # Difuzyon numpy ile yapiliyor ama izgara Python listesiydi; her
        # karede liste -> numpy -> liste donusumu yapiliyordu. 240x160'lik
        # bir izgarada bu, kare basina 38.400 elemanin iki kez
        # kopyalanmasi demek (olculdu: yalnizca asarray'e kare basina
        # 1 ms). `array.array` hem liste gibi indekslenir hem de numpy
        # tarafindan SIFIR KOPYAYLA sarilabilir - iki dunyanin da iyi
        # yani.
        self.grid = array.array('d', bytes(8 * self.total))
        self.scratch = array.array('d', bytes(8 * self.total))

        # Parameters
        self.evap_rate = game_settings.SCENT_EVAP_RATE   # per second
        self.diff_rate = game_settings.SCENT_DIFF_RATE   # per second
        self.max_concentration = game_settings.SCENT_MAX

        # Heatmap çizimi için yeniden kullanılan yüzeyler (kare başına
        # yeniden ayırmak pahalı olduğu için bir kez oluşturulur)
        self._heat_small = None
        self._heat_cache = None          # ölçeklenmiş, hazır blit edilecek yüzey
        self._heat_scaled_size = (self.cols * cell_size, self.rows * cell_size)
        self._heat_interval = game_settings.SCENT_HEATMAP_INTERVAL
        self._heat_age = 1e9             # ilk çizimde mutlaka üretilsin
        self._display_max = 1.0

        # Difuzyon agirlik toplami her hucre icin SABIT: yalnizca kac
        # komsusu oldugu belirler. Her karede yeniden toplamak, kare
        # basina 2400 hucre x 8 komsu = 19 bin gereksiz islemdi.
        self._np_wsum = None
        self._np_pad = None
        self._np_acc = None
        if _np is not None:
            m = _np.zeros((self.rows + 2, self.cols + 2))
            m[1:-1, 1:-1] = 1.0
            w = _np.zeros((self.rows, self.cols))
            for dr, dc, ww in self._KOMSU:
                w += m[1 + dr:1 + dr + self.rows,
                       1 + dc:1 + dc + self.cols] * ww
            self._np_wsum = _np.where(w > 0.0, w, 1.0)
            self._np_var = w > 0.0

    def _index(self, col, row):
        return row * self.cols + col

    def _world_to_cell(self, x, y):
        """World coordinates to grid cell (clamped)."""
        col = max(0, min(self.cols - 1, int(x / self.cell_size)))
        row = max(0, min(self.rows - 1, int(y / self.cell_size)))
        return col, row

    def add_scent(self, x, y, amount):
        """Konuma koku ekle (4 hücreye bilinear dağıtım).

        get_concentration'daki bilinear okumanın aynadaki karşılığıdır.
        Kokuyu tek hücreye yazmak kaynağı 20px'lik ızgaraya yapıştırır:
        besin hücrenin neresinde olursa olsun kokusu hücre merkezinde
        belirir, yani gerçek konumundan yarım hücreye (10px) kadar kayar.
        """
        cols = self.cols
        rows = self.rows
        grid = self.grid
        cap = self.max_concentration

        fx = x / self.cell_size - 0.5
        fy = y / self.cell_size - 0.5
        c0 = math.floor(fx)
        r0 = math.floor(fy)
        tx = fx - c0
        ty = fy - r0

        for dc, dr, w in ((0, 0, (1.0 - tx) * (1.0 - ty)),
                          (1, 0, tx * (1.0 - ty)),
                          (0, 1, (1.0 - tx) * ty),
                          (1, 1, tx * ty)):
            if w <= 0.0:
                continue
            c = c0 + dc
            r = r0 + dr
            # Kenarın dışına düşen pay en yakın hücreye yazılır (kütle korunur)
            if c < 0: c = 0
            elif c > cols - 1: c = cols - 1
            if r < 0: r = 0
            elif r > rows - 1: r = rows - 1

            idx = r * cols + c
            v = grid[idx] + amount * w
            grid[idx] = cap if v > cap else v

    def get_concentration(self, x, y):
        """Bilinear interpolation from grid at world position. O(1)."""
        # Continuous cell coordinates
        fx = x / self.cell_size - 0.5
        fy = y / self.cell_size - 0.5

        # Integer cell and fraction
        # floor kullanılır: int() negatife doğru sıfıra kırptığı için
        # haritanın sol/üst kenarında yanlış hücreyi seçerdi.
        c0 = math.floor(fx)
        r0 = math.floor(fy)

        # Clamp — kesir, kırpılmış hücreye göre yeniden hesaplanır ki
        # kenarlarda ızgaranın dışına ekstrapolasyon yapılmasın.
        c0 = max(0, min(self.cols - 2, c0))
        r0 = max(0, min(self.rows - 2, r0))
        tx = min(1.0, max(0.0, fx - c0))
        ty = min(1.0, max(0.0, fy - r0))
        c1 = c0 + 1
        r1 = r0 + 1

        # Four corners
        v00 = self.grid[self._index(c0, r0)]
        v10 = self.grid[self._index(c1, r0)]
        v01 = self.grid[self._index(c0, r1)]
        v11 = self.grid[self._index(c1, r1)]

        # Bilinear
        top = v00 + (v10 - v00) * tx
        bot = v01 + (v11 - v01) * tx
        return top + (bot - top) * ty

    # Diyagonal komşunun ağırlığı: merkeze uzaklığı sqrt(2) olduğu için
    # 1/sqrt(2). Sadece 4 komşu kullanılırsa yayılım eksenler boyunca
    # hızlı, çapraz yönlerde yavaş olur ve koku bulutu yuvarlak yerine
    # artı şeklinde çıkar.
    _DIAG_W = 0.7071067811865476

    #: (satir, sutun, agirlik) - Moore komsulugu
    _KOMSU = ((-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
              (-1, -1, _DIAG_W), (-1, 1, _DIAG_W),
              (1, -1, _DIAG_W), (1, 1, _DIAG_W))

    def update(self, dt):
        """Evaporation + Moore (8-neighbour) diffusion in single pass."""
        if _np is not None:
            return self._update_np(dt)
        return self._update_py(dt)

    def _update_np(self, dt):
        """Ayni difuzyon, izgaranin tamami tek seferde.

        Sonuc saf Python surumuyle BIREBIR ayni (kenar hucrelerinde de:
        eksik komsular agirlik toplamindan da dusuluyor). Fark yalnizca
        hizda: evrim olcumu icin dunyanin gercek zamandan kat kat hizli
        kosmasi gerekiyor ve bu dongu karenin en pahali parcasiydi.
        """
        self._heat_age += dt
        rows, cols = self.rows, self.cols
        # SIFIR KOPYA: ayni bellek hem 'array' hem numpy dizisi olarak
        # gorunur. Donusum maliyeti yok.
        g = _np.frombuffer(self.grid, dtype=_np.float64).reshape(rows, cols)
        if self._np_pad is None:
            self._np_pad = _np.zeros((rows + 2, cols + 2))
            self._np_acc = _np.zeros((rows, cols))
        pad, acc = self._np_pad, self._np_acc
        pad[1:-1, 1:-1] = g
        acc[:] = 0.0
        for dr, dc, ww in self._KOMSU:
            acc += pad[1 + dr:1 + dr + rows, 1 + dc:1 + dc + cols] * ww
        val = g * (1.0 - self.evap_rate * dt)
        val += _np.where(self._np_var,
                         (self.diff_rate * dt) * (acc / self._np_wsum - g),
                         0.0)
        _np.clip(val, 0.0, self.max_concentration, out=val)
        g[:] = val

    def _update_py(self, dt):
        self._heat_age += dt   # ısı haritası önbelleğinin yaşı
        cols = self.cols
        rows = self.rows
        grid = self.grid
        scratch = self.scratch
        evap = 1.0 - self.evap_rate * dt
        diff = self.diff_rate * dt
        dw = self._DIAG_W
        cap = self.max_concentration

        for r in range(rows):
            row_offset = r * cols
            up = r > 0
            down = r < rows - 1
            for c in range(cols):
                idx = row_offset + c
                center = grid[idx]
                val = center * evap  # evaporation

                # Diffusion: ağırlıklı 8-komşu Laplacian
                acc = 0.0
                wsum = 0.0
                left = c > 0
                right = c < cols - 1

                if left:
                    acc += grid[idx - 1]; wsum += 1.0
                if right:
                    acc += grid[idx + 1]; wsum += 1.0
                if up:
                    acc += grid[idx - cols]; wsum += 1.0
                    if left:
                        acc += grid[idx - cols - 1] * dw; wsum += dw
                    if right:
                        acc += grid[idx - cols + 1] * dw; wsum += dw
                if down:
                    acc += grid[idx + cols]; wsum += 1.0
                    if left:
                        acc += grid[idx + cols - 1] * dw; wsum += dw
                    if right:
                        acc += grid[idx + cols + 1] * dw; wsum += dw

                if wsum > 0.0:
                    val += diff * (acc / wsum - center)

                scratch[idx] = 0.0 if val < 0.0 else (cap if val > cap else val)

        # Swap buffers
        self.grid, self.scratch = scratch, grid

    @staticmethod
    def _ramp(t):
        """Koku yoğunluğu (0..1) -> (r, g, b, a) renk geçişi.

        Koyu lacivert (zayıf) -> teal -> yeşil -> sarı (yoğun).
        """
        if t < 0.33:
            k = t / 0.33
            r, g, b = 5 + 5 * k, 25 + 85 * k, 60 + 50 * k
        elif t < 0.66:
            k = (t - 0.33) / 0.33
            r, g, b = 10 + 40 * k, 110 + 90 * k, 110 - 50 * k
        else:
            k = (t - 0.66) / 0.34
            r, g, b = 50 + 205 * k, 200 + 55 * k, 60 - 10 * k
        return int(r), int(g), int(b), int(25 + 175 * t)

    def draw_debug(self, screen):
        """Koku alanını yumuşak bir ısı haritası olarak çizer.

        Grid çözünürlüğünde küçük bir yüzeye yazılıp ekran boyutuna
        smoothscale ile büyütülür; bu hem hücre başına yüzey ayırmaktan
        çok daha hızlıdır hem de kokuyu bloklar yerine yayılan bir bulut
        olarak gösterir.
        """
        # Önbellek taze ise yeniden üretme; koku alanı yavaş değişir.
        if self._heat_cache is not None and self._heat_age < self._heat_interval:
            screen.blit(self._heat_cache, (0, 0))
            return

        if self._heat_small is None:
            self._heat_small = pygame.Surface((self.cols, self.rows),
                                              pygame.SRCALPHA)

        grid = self.grid

        # Otomatik pozlama: tepe değer parametrelere göre değiştiği için
        # sabit bir ölçek yerine gözlenen tepeyi yumuşakça takip et.
        peak = max(grid)
        if peak > self._display_max:
            self._display_max = peak
        else:
            self._display_max += (peak - self._display_max) * 0.05
        scale_max = max(1.0, self._display_max)
        log_max = math.log(1.0 + scale_max)

        small = self._heat_small
        small.fill((0, 0, 0, 0))
        set_at = small.set_at
        for r in range(self.rows):
            row_offset = r * self.cols
            for c in range(self.cols):
                val = grid[row_offset + c]
                if val < 0.01:
                    continue
                t = min(1.0, math.log(1.0 + val) / log_max)
                set_at((c, r), self._ramp(t))

        self._heat_cache = pygame.transform.smoothscale(
            small, self._heat_scaled_size)
        self._heat_age = 0.0
        screen.blit(self._heat_cache, (0, 0))
