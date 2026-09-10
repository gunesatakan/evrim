import math
import pygame

# Her silahin kendi rengi - ekranda ayirt edilebilsin
COLORS = {
    "Stylet":       (255, 210, 120),
    "Harpoon":      (150, 220, 255),
    "Nematocyst":   (255, 120, 220),
    "Toxin":        (170, 255, 120),
    "Lysin":        (255, 150, 90),
    "Phagocytosis": (200, 200, 255),
}

# Laboratuvardaki silah boylari (Attacker.weapon_len) - sekiller bu
# boya gore cizildi; oyunda organ boyuna oranla kucultulur.
LAB_BOY = {0: 46.0, 1: 16.0, 2: 74.0, 3: 66.0, 4: 82.0,
           5: 46.0, 6: 44.0, 7: 42.0, 8: 44.0}


def _lab_markers():
    try:
        import lab
        return lab.MARKERS
    except Exception:
        return None


def _yuk_bilgisi(payload):
    """(renk, stok tavani) - yukun KENDI rengi. Yoksa (None, 44)."""
    try:
        import lab
        pi = int(payload)
        if 0 < pi < len(lab.PAYLOADS) and lab.PAYLOADS[pi][1] is not None:
            return lab.PAYLOADS[pi][5], float(lab.STOCK_MAX)
        return None, float(lab.STOCK_MAX)
    except Exception:
        return None, 44.0


def _kese(screen, P, W, dx, dy, r, dolu, renk):
    """Ureticinin DEPO KESESI: doluluk orani gorunur.

    Salgi kesesi (vezikul) hucrenin icinde gercekten durur ve dolduk ca
    sisirir. Ekranda bunun karsiligi yoktu; kullanici organin kac
    molekul biriktirdigini yalnizca paneldeki sayidan gorebiliyordu.
    """
    if renk is None:
        return
    pygame.draw.circle(screen, (40, 46, 56), P(dx, dy), W(r))
    if dolu > 0.0:
        pygame.draw.circle(screen, renk, P(dx, dy), max(1, W(r * (dolu ** 0.5))))
    pygame.draw.circle(screen, (90, 100, 115), P(dx, dy), W(r), max(1, W(1.5)))


def draw_weapon(screen, name, pos, outward, length, ready, firing_at=None,
                olcek=1.0, carrier=None, marker=0, recoil=0.0, merkez=None,
                stok=0.0, payload=0):
    """Silahi govde uzerinde ciz - LABORATUVARLA AYNI SEKILLER.

    lab.Attacker._draw_weapon her tasiyiciyi kendi yapisiyla cizer: T6SS
    kasilmali kilif + ic tup + mizrak ucu, stilet sivri cokgen,
    nematosist basincli kapsul + tipe gore uc (penetrant sivri, volvent
    sarmal iplik, glutinant yapiskan damla, izoriza kanca), belirtec
    ucta renkli tanima basligi, ates edince geri tepme. Oyunda ayni
    sekiller organin dogrultusunda ve organ boyuna oranla cizilir.

    Koordinat cercevesi: `pos` organin govdedeki tabani, `outward`
    disari birim vektoru; lab'daki (dx, dy) piksel ofsetleri bu cerceveye
    `s` olcegiyle tasinir.
    """
    def _p(n):
        return max(1, int(round(n * olcek)))

    col = COLORS.get(name, (255, 255, 255))
    if not ready:
        col = tuple(int(c * 0.35) for c in col)
    u = pygame.math.Vector2(outward)
    if u.length_squared() < 1e-12:
        u = pygame.math.Vector2(1, 0)
    u = u.normalize()
    v = pygame.math.Vector2(-u.y, u.x)
    ci = carrier
    # Lab sekilleri lab boyuna (weapon_len) gore cizildi; `length` o boyun
    # oyundaki karsiligi -> s = lab pikseli basina oyun pikseli.
    s = length / max(1.0, LAB_BOY.get(ci, 46.0)) if ci is not None else olcek
    # GERI TEPME: ates edince silah geriye (govdeye) cekilir, 60 px/sn ile
    # doner (lab: cx - recoil). Yalnizca lab tasiyicilarinda.
    taban = pos - u * (recoil * s) if ci is not None else pygame.math.Vector2(pos)

    def P(dx, dy):
        q = taban + u * (dx * s) + v * (dy * s)
        return (int(q.x), int(q.y))

    def W(n):
        return max(1, int(round(n * s)))

    tip = taban + u * length
    tipx = length / max(1e-6, s)          # lab cercevesinde ucun dx'i

    if name == "Phagocytosis":
        # SITOSTOM (hucre agzi) - lab tasiyicisi degil, kendi cizimi.
        perp = v
        agiz = length * 0.85
        bogaz = length * 0.28
        ic = pos - u * length * 0.5
        pygame.draw.polygon(screen, tuple(int(c * 0.30) for c in col),
                            [pos + perp * agiz, tip + perp * agiz * 0.55,
                             tip - perp * agiz * 0.55, pos - perp * agiz])
        pygame.draw.lines(screen, col, False,
                          [tip + perp * agiz * 0.55, pos + perp * agiz,
                           ic + perp * bogaz, ic - perp * bogaz,
                           pos - perp * agiz, tip - perp * agiz * 0.55], 2)
        return

    # GORULEN MOLEKUL = STOKTAKI MOLEKUL.
    #
    # Uretici tasiyicilarin (0-2) cevresine sabit sayida sus noktasi
    # ciziliyordu: bos bir organ da tikabasa dolu bir organ da ayni
    # gorunuyor, hatta hic uretmemis bir hucre puskurtuyormus gibi
    # duruyordu. Cizilen nokta sayisi artik organin FIILEN tasidigi
    # molekul sayisi, rengi de o molekulun kendi rengi. Bos organ bos
    # gorunur; stok dolarken noktalar cogalir.
    _yuk_renk, _stok_max = _yuk_bilgisi(payload)
    _stok = max(0.0, float(stok))
    _dolu = min(1.0, _stok / max(1.0, _stok_max))

    def _nokta_sayisi(en_fazla):
        """Stokun kac molekulu bu cizimde gosterilir."""
        if _yuk_renk is None or _stok < 1.0:
            return 0
        return max(1, int(round(en_fazla * _dolu)))

    if ci == 0:
        # DIFUZYON: silah yok, molekuller hucrenin her yanindan sizip
        # yayilir - lab'daki gibi hucre cevresinde nokta halkasi
        c = pygame.math.Vector2(merkez) if merkez is not None else pygame.math.Vector2(pos)
        R = c.distance_to(pos)
        # Depo kesesi difuzyonda da vardir: salgi once vezikulde birikir,
        # sonra zardan sizar.
        _kese(screen, P, W, 0, 0, 14, _dolu, _yuk_renk)
        _n = _nokta_sayisi(18)
        for k in range(_n):
            a = (k / 18.0) * 2 * math.pi
            d = R + (14 + (k % 3) * 11) * s
            q = c + pygame.math.Vector2(math.cos(a), math.sin(a)) * d
            pygame.draw.circle(screen, _yuk_renk, (int(q.x), int(q.y)), W(3))
    elif ci == 1:
        # YONLU BOSALTMA: hedefe dogru acilmis kese (yay), molekuller onunde
        yay = []
        for k in range(13):
            a = -1.1 + 2.2 * k / 12.0
            yay.append(P(5 + 23 * math.cos(a), 26 * math.sin(a)))
        pygame.draw.lines(screen, (170, 185, 195), False, yay, W(4))
        _kese(screen, P, W, 5, 0, 20, _dolu, _yuk_renk)
        for k in range(_nokta_sayisi(10)):
            dy = -22 + k * 5
            pygame.draw.circle(screen, _yuk_renk, P(20 + (k % 4) * 9, dy), W(3))
    elif ci == 2:
        # FILAMENT: esnek boru, ucundan fiskirtma
        pts = [P(-4 + i * 9, 7 * math.sin(i * 0.9)) for i in range(9)]
        pygame.draw.lines(screen, (185, 175, 205), False, pts, W(7))
        pygame.draw.lines(screen, (110, 100, 130), False, pts, W(2))
        _kese(screen, P, W, -4, 0, 16, _dolu, _yuk_renk)
        for k in range(_nokta_sayisi(6)):
            pygame.draw.circle(screen, _yuk_renk,
                               P(tipx + 6 + k * 7, (k % 3 - 1) * 5), W(3))
    elif ci == 3:
        # T6SS: kasilmali kilif + ic tup + mizrak ucu
        kilif = [P(-2, -13), P(42, -13), P(42, 13), P(-2, 13)]
        pygame.draw.polygon(screen, (150, 170, 190), kilif)
        pygame.draw.polygon(screen, (80, 95, 110), kilif, W(2))
        for k in range(5):
            pygame.draw.line(screen, (95, 115, 130), P(4 + k * 8, -13), P(4 + k * 8, 13), W(2))
        pygame.draw.polygon(screen, (205, 200, 180), [P(42, -5), P(56, -5), P(56, 5), P(42, 5)])
        pygame.draw.polygon(screen, (225, 220, 200), [P(56, -9), P(tipx, 0), P(56, 9)])
    elif ci == 4:
        # STILET: sivri delici - uzatilir, firlatilmaz
        half = 6
        pygame.draw.polygon(screen, (210, 200, 175), [P(-2, -half), P(tipx, 0), P(-2, half)])
        pygame.draw.polygon(screen, (120, 115, 100), [P(-2, -half), P(tipx, 0), P(-2, half)], 1)
    elif ci in (5, 6, 7, 8):
        # NEMATOSIST ailesi: basincli kapsul. Tipe gore uc farkli.
        bx = 18
        pygame.draw.circle(screen, (200, 190, 130), P(bx, 0), W(22))
        pygame.draw.circle(screen, (120, 110, 70), P(bx, 0), W(22), W(2))
        for k in range(5):
            pygame.draw.circle(screen, (150, 140, 95), P(bx, 0), W(19 - k * 4), 1)
        if ci == 5:      # penetrant: sivri delici
            pygame.draw.polygon(screen, (215, 205, 150), [P(bx + 20, -10), P(tipx, 0), P(bx + 20, 10)])
        elif ci == 6:    # volvent: sarmal iplik
            for k in range(8):
                t = k / 7.0
                pygame.draw.circle(screen, (235, 225, 170),
                                   P(bx + 20 + t * (tipx - bx - 20), 8 * math.sin(t * 9)), W(3))
        elif ci == 7:    # glutinant: yapiskan damla
            pygame.draw.circle(screen, (200, 235, 140), P(tipx - 4, 0), W(10))
            pygame.draw.circle(screen, (90, 130, 60), P(tipx - 4, 0), W(10), W(2))
        else:            # izoriza: kanca
            pygame.draw.line(screen, (200, 220, 245), P(bx + 20, 0), P(tipx, 0), W(3))
            pygame.draw.line(screen, (200, 220, 245), P(tipx, 0), P(tipx - 9, -9), W(3))
            pygame.draw.line(screen, (200, 220, 245), P(tipx, 0), P(tipx - 9, 9), W(3))
    else:
        pygame.draw.line(screen, col, taban, tip, _p(2))

    # --- BELIRTEC: ucta renkli tanima basligi (lab ile ayni)
    M = _lab_markers()
    if M is not None and 0 < int(marker) < len(M) and M[int(marker)][1] is not None:
        mcol = M[int(marker)][2]
        pygame.draw.circle(screen, mcol, P(tipx, 0), W(9))
        pygame.draw.circle(screen, (20, 25, 30), P(tipx, 0), W(9), W(2))

    # Surekli silahlarda hedef cizgisi; ignelilerde ucustaki Shot cizer.
    if firing_at is not None and (ci is None or ci < 3):
        pygame.draw.line(screen, col, tip, firing_at, _p(1))
