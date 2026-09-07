# -*- coding: utf-8 -*-
"""Kosu ciktisini tek sayfalik bir HTML raporuna cevirir.

Sayilar tablo halinde okunabiliyor ama bir egilimin gercek olup olmadigi
ancak ZAMAN ICINDE gorulur: silah orani yukseliyor mu yoksa gurultude mi
salini yor, katmanlar birikiyor mu yoksa geliyor gidiyor mu. Grafikler
disaridan bir kutuphane gerektirmesin diye SVG olarak dogrudan uretilir.
"""
import argparse
import html
import json


def _seri(ozet, anahtar):
    return [(s["t"], s.get(anahtar)) for s in ozet
            if isinstance(s.get(anahtar), (int, float))]


def _svg(seriler, baslik, yukseklik=190, genislik=560):
    """Cok cizgili basit bir zaman serisi grafigi."""
    if not seriler or not any(s[1] for s in seriler):
        return "<p>veri yok</p>"
    tum = [v for _ad, noktalar, _r in seriler for _t, v in noktalar]
    t_ler = [t for _ad, noktalar, _r in seriler for t, _v in noktalar]
    if not tum:
        return "<p>veri yok</p>"
    ymin, ymax = min(0.0, min(tum)), max(tum)
    if ymax - ymin < 1e-9:
        ymax = ymin + 1.0
    tmin, tmax = min(t_ler), max(t_ler)
    if tmax - tmin < 1e-9:
        tmax = tmin + 1.0
    sol, alt, ust, sag = 52, 26, 16, 12
    iw = genislik - sol - sag
    ih = yukseklik - ust - alt

    def px(t):
        return sol + iw * (t - tmin) / (tmax - tmin)

    def py(v):
        return ust + ih * (1.0 - (v - ymin) / (ymax - ymin))

    p = ['<svg viewBox="0 0 %d %d" class="cz" role="img" aria-label="%s">'
         % (genislik, yukseklik, html.escape(baslik))]
    # izgara
    for i in range(5):
        y = ust + ih * i / 4.0
        deger = ymax - (ymax - ymin) * i / 4.0
        p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="gr"/>'
                 % (sol, y, genislik - sag, y))
        p.append('<text x="%.1f" y="%.1f" class="ax">%s</text>'
                 % (sol - 6, y + 3.5, ("%.3g" % deger)))
    p.append('<text x="%.1f" y="%.1f" class="ax">%d sn</text>'
             % (sol, yukseklik - 8, tmin))
    p.append('<text x="%.1f" y="%.1f" class="ax" text-anchor="end">%d sn</text>'
             % (genislik - sag, yukseklik - 8, tmax))
    for ad, noktalar, renk in seriler:
        if not noktalar:
            continue
        d = " ".join(("%s%.1f,%.1f" % ("M" if i == 0 else "L", px(t), py(v)))
                     for i, (t, v) in enumerate(noktalar))
        p.append('<path d="%s" fill="none" stroke="%s" stroke-width="2"/>'
                 % (d, renk))
    p.append("</svg>")
    # gosterge
    g = " ".join('<span class="lg"><i style="background:%s"></i>%s</span>'
                 % (r, html.escape(a)) for a, _n, r in seriler)
    return "".join(p) + '<div class="leg">%s</div>' % g


RENK = ["#4fc3f7", "#ffb74d", "#81c784", "#e57373", "#ba68c8", "#fff176"]


def uret(veri, cikti, baslik="Evrim Kosusu"):
    ozet = veri["ozet"]
    n_tohum = len(veri["ham"])
    sure = veri["sure"]
    son = ozet[-1] if ozet else {}

    bloklar = []

    def blok(ad, aciklama, anahtarlar):
        seriler = []
        for i, (k, etiket) in enumerate(anahtarlar):
            seriler.append((etiket, _seri(ozet, k), RENK[i % len(RENK)]))
        bloklar.append(
            '<section><h2>%s</h2><p class="ac">%s</p>%s</section>'
            % (html.escape(ad), aciklama, _svg(seriler, ad)))

    blok("Ölçüt 1 — Silahlı avlanma",
         "Silah taşıyan hücrelerin oranı ve silahın <b>kullanılma</b> sayısı. "
         "Taşımak ile kullanmak ayrı şeyler: ucuz taşınan bir organ "
         "sürüklenmeyle de yayılabilir.",
         [("silahli_oran", "silahlı hücre oranı"),
          ("silah_guc", "en güçlü silahın gücü"),
          ("av_yeme", "hücre yeme olayı (birikimli)")])

    blok("Ölçüt 2 — Öğrenilmiş kaç / saldır",
         "Koku ekseninde <i>zayıfa saldırma</i> ve <i>güçlüden kaçma</i> "
         "eğilimi. Rastgele bir davranış tablosunda ikisi de 0 civarındadır; "
         "sıfırdan uzaklaşmak seçilim demektir.",
         [("saldiri_egilimi", "zayıfa saldırı eğilimi"),
          ("kacis_egilimi", "güçlüden kaçış eğilimi"),
          ("kairomon_kacisi", "kairomondan kaçış"),
          ("sosyal_ort", "sosyal öncelik geni")])

    blok("Ölçüt 3 — Savunma tipleri",
         "Hücre başına zar katmanı, savunma yatırımı ve <b>zırhlı ama "
         "silahsız</b> hücrelerin oranı.",
         [("katman_ort", "hücre başına katman"),
          ("savunma_ort", "savunma yatırımı"),
          ("savunmaci_oran", "savunmacı tip oranı"),
          ("silahli_savunmali", "zırhlı avcı oranı")])

    blok("Karmaşıklık ve fizyoloji",
         "Organ sayısı, duyu ve motor organ sayısı, gövde boyu ve sindirim "
         "hızı. Başlangıçta her hücrede 7 organ, 1 burun, 1 kamçı vardı.",
         [("organ_ort", "organ sayısı"),
          ("burun_ort", "kemoreseptör"),
          ("kamci_ort", "kamçı"),
          ("govde_ort", "gövde boyu"),
          ("sindirim_ort", "sindirim süresi sn")])

    blok("Ekosistem",
         "Nüfus, haritadaki besin ve birikimli doğum sayısı.",
         [("n", "nüfus"), ("besin", "besin"), ("dogum", "doğum (birikimli)")])

    silah = son.get("silah") or {}
    olum = son.get("silah_olum") or {}
    tablo = ""
    if silah or olum:
        satirlar = []
        for k in sorted(set(silah) | set(k.capitalize() for k in olum)):
            satirlar.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                            % (html.escape(k), silah.get(k, 0),
                               olum.get(k.lower(), 0)))
        tablo = ('<table><thead><tr><th>silah</th><th>taşıyan organ</th>'
                 '<th>öldürme</th></tr></thead><tbody>%s</tbody></table>'
                 % "".join(satirlar))

    s = """<title>Evrim Koşusu</title>
<style>
:root{--bg:#f7f7f5;--kart:#fff;--yazi:#1c1c1a;--soluk:#6b6b66;--cizgi:#e3e3df;--vurgu:#2f6f4f}
:root:not([data-theme="light"]){}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
 --bg:#16181c;--kart:#1e2126;--yazi:#e8e8e4;--soluk:#9a9a94;--cizgi:#2c3037;--vurgu:#7fd1a8}}
:root[data-theme="dark"]{--bg:#16181c;--kart:#1e2126;--yazi:#e8e8e4;--soluk:#9a9a94;--cizgi:#2c3037;--vurgu:#7fd1a8}
body{background:var(--bg);color:var(--yazi);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;margin:0;padding:28px 20px 60px}
.kap{max-width:660px;margin:0 auto}
h1{font-size:25px;margin:0 0 4px;letter-spacing:-.01em}
.ust{color:var(--soluk);font-size:13px;margin:0 0 22px}
section{background:var(--kart);border:1px solid var(--cizgi);border-radius:10px;padding:16px 18px;margin:0 0 16px}
h2{font-size:16px;margin:0 0 4px;color:var(--vurgu)}
p.ac{color:var(--soluk);font-size:13px;margin:0 0 10px}
svg.cz{width:100%;height:auto;display:block;overflow:visible}
.gr{stroke:var(--cizgi);stroke-width:1}
.ax{fill:var(--soluk);font-size:9px;text-anchor:end}
.leg{display:flex;flex-wrap:wrap;gap:12px;margin-top:8px;font-size:12px;color:var(--soluk)}
.lg{display:inline-flex;align-items:center;gap:5px}
.lg i{width:11px;height:3px;border-radius:2px;display:inline-block}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:6px}
th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--cizgi)}
th{color:var(--soluk);font-weight:600}
.not{color:var(--soluk);font-size:12px;margin-top:26px;border-top:1px solid var(--cizgi);padding-top:14px}
</style>
<div class="kap">
<h1>%s</h1>
<p class="ust">%d tohum &times; %d simülasyon saniyesi &middot; tüm eğriler tohum ortalamasıdır</p>
%s
%s
<p class="not">Başlangıç: her hücrede zar, sitoplazma, iskelet, koful, ribozom
ve <b>bir kamçı + bir kemoreseptör</b>. Davranış tablosu tamamen rastgele.
Roller sınıfa göre dağıtılmıyor; kimin avcı kimin av olduğu yalnızca
taşınan organlardan ve davranış genomundan çıkıyor.</p>
</div>""" % (html.escape(baslik), n_tohum, int(sure),
             "".join(bloklar),
             ('<section><h2>Silah dağılımı (son durum, tüm tohumlar)</h2>%s</section>'
              % tablo) if tablo else "")
    with open(cikti, "w", encoding="utf-8") as f:
        f.write(s)
    return cikti


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dosya")
    ap.add_argument("--cikti", default="arac/sonuc/rapor.html")
    ap.add_argument("--baslik", default="Evrim Koşusu")
    a = ap.parse_args()
    with open(a.dosya, encoding="utf-8") as f:
        veri = json.load(f)
    print(uret(veri, a.cikti, a.baslik))


if __name__ == "__main__":
    main()
