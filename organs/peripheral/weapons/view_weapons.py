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


def _kese(screen, P, W, dx, dy, r, stok, stok_max, renk):
    """Ureticinin DEPO KESESI ve ICINDEKI molekuller.

    Salgi kesesi (vezikul) hucrenin icinde durur ve molekuller onun
    ICINDE birikir. Once stok organin DISINA, cevreye sacilmis noktalar
    olarak ciziliyordu; oysa henuz salinmamis bir molekul disarida
    olamaz - orada gorunen sey stok degil, salinmis molekulun ta
    kendisidir (o zaten lab.Molecule olarak ayrica ciziliyor).

    Kesenin icine stok kadar molekul konur; sigmayacak kadar cok olursa
    dolgu ile gosterilir. Bos kese bos gorunur.
    """
    if renk is None:
        return
    n = int(max(0.0, stok))
    rp = W(r)
    if rp < 2:
        return
    merkez = P(dx, dy)
    # Kesenin kendisi: ince zarli, koyu ic
    pygame.draw.circle(screen, (32, 38, 48), merkez, rp)
    if n > 0:
        # ICERIDEKI MOLEKULLER. Altin aci ile dagitilir - duzgun,
        # deterministik ve kesenin icinde kalir.
        mr = max(1, W(2.0))
        gorunur = min(n, 40)
        # Cok kalabalikta tek tek nokta okunmaz: once dolgu, ustune nokta
        if n > 40:
            _dolu = min(1.0, n / max(1.0, stok_max))
            pygame.draw.circle(screen, tuple(int(c * 0.55) for c in renk),
                               merkez, max(1, int(rp * (_dolu ** 0.5))))
        for i in range(gorunur):
            a = i * 2.399963
            rr = rp * 0.72 * math.sqrt((i + 0.5) / max(1.0, gorunur))
            q = (int(merkez[0] + math.cos(a) * rr), int(merkez[1] + math.sin(a) * rr))
            pygame.draw.circle(screen, renk, q, mr)
    pygame.draw.circle(screen, (95, 105, 120), merkez, rp, max(1, W(1.2)))


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

    # STOK ORGANIN ICINDE. Uretici tasiyicilarin (0-2) cevresine sabit
    # sayida sus noktasi ciziliyordu: bos bir organ da tikabasa dolu bir
    # organ da ayni gorunuyordu. Sonra nokta sayisi stoka baglandi ama
    # noktalar hala organin DISINDAYDI - oysa henuz salinmamis bir
    # molekul disarida olamaz. Stok artik ureticinin DEPO KESESININ
    # icinde, tek tek molekul olarak duruyor; disarida gordugun her
    # nokta gercekten salinmis bir lab.Molecule'dur.
    _yuk_renk, _stok_max = _yuk_bilgisi(payload)
    _stok = max(0.0, float(stok))

    if ci == 0:
        # DIFUZYON: silah yok, molekuller hucrenin her yanindan sizip
        # yayilir - lab'daki gibi hucre cevresinde nokta halkasi
        # Depo kesesi difuzyonda da vardir: salgi once vezikulde birikir,
        # sonra zardan sizar.
        _kese(screen, P, W, 0, 0, 15, _stok, _stok_max, _yuk_renk)
    elif ci == 1:
        # YONLU BOSALTMA: hedefe dogru acilmis kese (yay), molekuller onunde
        yay = []
        for k in range(13):
            a = -1.1 + 2.2 * k / 12.0
            yay.append(P(5 + 23 * math.cos(a), 26 * math.sin(a)))
        pygame.draw.lines(screen, (170, 185, 195), False, yay, W(4))
        _kese(screen, P, W, 2, 0, 18, _stok, _stok_max, _yuk_renk)
    elif ci == 2:
        # FILAMENT: esnek boru, ucundan fiskirtma
        pts = [P(-4 + i * 9, 7 * math.sin(i * 0.9)) for i in range(9)]
        pygame.draw.lines(screen, (185, 175, 205), False, pts, W(7))
        pygame.draw.lines(screen, (110, 100, 130), False, pts, W(2))
        _kese(screen, P, W, -4, 0, 15, _stok, _stok_max, _yuk_renk)
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
