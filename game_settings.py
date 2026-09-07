import json
import os

# Default Global World/Evolution Settings
DEFAULT_SETTINGS = {
    # Her uzunlugu ayni oranda buyuten kuresel olcek. 1 = eski davranis.
    # ~30 yapinca hucreler laboratuvardaki boyuta gelir ve katman/gozenek
    # yapisi gercekten cizilebilir hale gelir.
    "WORLD_SCALE": 1.0,
    # ARENA: yalnizca sahayi buyutur, hucreyi buyutmez. 2.0 = dort kat alan.
    # 1.0'da 200 hucre sahanin ucte birini kapliyor ve her sey bir arbedeye
    # donusuyor; 2.0'da orani %8'e duser, hareket ve uzun menzilli algi
    # anlam kazanir.
    "ARENA_OLCEK": 2.0,
    "FOOD_COUNT": 80,
    # BASLANGIC: her turden BIR adet. Populasyon zaten dakikalar icinde
    # tavana ciktigi icin bu sayi yalnizca ilk dakikayi belirler; asil yuk
    # DIVISION_MAX_POPULATION'dan gelir.
    "KAOTROPI_COUNT": 1,
    "OPTROPI_COUNT": 1,
    # --- AVLANMA (Optropi -> Notropi) ---
    # Optropiler notropileri yem olarak gorur. Notropiler de koku yayar,
    # boylece kemotaksi onlara dogru surukler; gorus alanina girerse
    # dogrudan takip devreye girer.
    "NOTROPI_COUNT": 1,
    # TROFIK VERIM: avin biyokutlesinin ne kadari yiyene gecer.
    # 1.0 olsaydi avlanmak besin toplamaktan her zaman karli olurdu ve
    # ekosistem tek bir avci tipine cokerdi; gercekte de yenen her seyin
    # tamami kullanilamaz. 0.5 ile ortalama bir hucre 6 besin eder -
    # bir bolunmenin enerjisi kadar, yani avlanmak gercek bir secenek
    # ama bedava degil.
    "PREY_BIOMASS_YIELD": 0.5,
    # Av yemek YENI ORGAN GARANTISI degildir; bir "gelisim hakki"
    # kazandirir. Hak mitoz sirasinda cekilise girer: bu ihtimalle
    # yeni bir organ cikar, aksi halde mevcut bir gen gelisir.
    "PREY_NEW_ORGAN_CHANCE": 0.25,
    # Iz birakma HIZI (nokta/saniye). Once kare basina %30 idi; bu hem
    # kare hizina bagliydi hem de 20 saniyelik omurle birlikte hucre
    # basina 360 canli nokta demekti. 6/sn ayni izi cok daha ucuz birakir.
    "TRAIL_RATE": 6.0,
    "PREY_VISION_PRIORITY": 1,     # 1 = goruse giren avi kokudan once takip et

    # --- SURUKLENME (Stokes) ---
    # Mikro olcekte atalet ihmal edilir, surtunme baskindir:
    #     F = 6*pi*mu*r*v   ->   v = F / (6*pi*mu*r)
    # Yani hiz yaricapla TERS orantilidir. Eskiden hiz = net itme idi ve
    # govde boyutu denkleme hic girmiyordu: kaotropi hem en buyuk hem en
    # hizli olabiliyordu (fiziksel olarak imkansiz).
    #
    #     hiz = net_itme * (DRAG_REF_RADIUS / yaricap) ^ DRAG_EXPONENT
    #
    # DRAG_REF_RADIUS: bu yaricapta ceza yok (varsayilan optropi = 10).
    # DRAG_EXPONENT : 1.0 = Stokes (dogru fizik), 0 = kapali, 2 = alan bazli.
    # ITKI OLCEGI: organ kuvvet birimini px/sn'ye cevirir.
    # Olculdu: olceksiz hucreler saniyede 0.17 GOVDE BOYU gidiyordu; gercek
    # E. coli 10-15 govde boyu/sn yuzer. Kemotaksis yanliligi zaten dogruydu
    # (+0.116, gercekte de yuzme hizinin ~%10'u) ama bu kadar yavas bir
    # govdede net ilerleme sifira yakin kaliyor, hucre besine ulasamiyordu.
    # Ters orantiyi ve flagella/cilia katkilarini DEGISTIRMEZ, yalnizca olcek.
    # Olculdu (4 tohum x 60s): olcek 20/30/40 ekolojik olarak AYIRT
    # EDILEMEZ - dogum 168/168/167, besin alimi 199/200/200 ile doymus,
    # ve her olcegin kendi tohum dagilimi (99-153) olcekler arasi farktan
    # genis. Yani 20'nin ustunde ekosistem hiza duyarsiz; secim biyolojik
    # gercekcilige kaliyor. 40 => 9.79 govde boyu/sn, gercek E. coli'nin
    # 10-15 bandina giren tek deger ve ekolojik bedeli yok.
    # 40 iken tek kamcili hucre 600 px/sn ile yuzuyordu; dunya 1200 px
    # genis, yani iki saniyede bastan basa geciyordu ve davranis
    # (kemotaksi, avlanma, kacis) gozlemlenemiyordu. 4'te hizli bir hucre
    # dunyayi ~10 saniyede geciyor.
    "THRUST_SCALE": 4.0,
    # Fotoreseptor varsayilanlari (yalnizca deger verilmediginde kullanilir)
    "VISION_RANGE_BASE": 15.0,
    "VISION_ANGLE_BASE": 0.35,
    # Yaricap artik ZARFI DA iceriyor (varsayilan hucrede 20 -> 55.2).
    # Referans da ayni oranda buyutuldu ki mevcut hiz dengesi korunsun;
    # aksi halde butun hucreler bir anda 2.76 kat yavaslardi. Zarfin
    # bedeli yine var: kalin zarf yaricapi buyutur, buyuk yaricap
    # yavaslatir - ama taban durum degismedi.
    "DRAG_REF_RADIUS": 27.6,
    "DRAG_EXPONENT": 1.0,
    # DONME SURTUNMESI: Stokes'ta oteleme a ile, DONME a^3 ile buyur.
    # Kod donmeyi `tork / (0.2 * r^2)` ile hesapliyordu; bicim dogruydu
    # (dusuk Reynolds'ta atalet yok, bu bir hareketlilik katsayisi) ama
    # us yanlisti - ustelik ayni dosyadaki OTELEME sürtünmesi zaten a^1
    # ile dogru olcekleniyordu. Olculdu: yaricap 40'ta kod 35.8 deg/s
    # veriyordu, a^3 yasasi 9.0 deg/s. Buyuk hucre olmasi gerekenden
    # dort kat kolay donuyordu.
    #
    # Katsayi, GOVDE yaricapi DRAG_REF_RADIUS iken eski bolenle ayni
    # degeri verecek sekilde secilir (0.2*ref^2 = K*ref^3 -> K = 0.2/ref).
    # Gercek donme yine de yavaslar, cunku bolende artik ORGANLARI da
    # iceren etkin yaricap kullaniliyor - organlar donmeye de direnir.
    "ROT_DRAG_EXPONENT": 3.0,
    # ORGAN SURUKLENMESI: organlar akisin icinde durur, hucreyi yavaslatir.
    # Eskiden hicbir etkileri yoktu - olculdu, 30 fotoreseptor eklemek
    # hizi 10.00'dan 10.00'a getiriyordu. Etken yaricap, govde yaricapina
    # organ alanindan gelen bir katki eklenerek bulunur:
    #     r_etkin = r * (1 + ORGAN_DRAG_GAIN * organ_alani / govde_alani)
    # Kanatlar ne kadar genisse suruklenme o kadar artar.
    # 1.0 = organ alani govde alanina orani kadar etkin yaricapi buyutur
    # (notr, aciklanabilir secim). Olculdu: 30 fazladan fotoreseptor
    # hizi %8 dusuruyor, organsiz bir govdeye gore fark %16.
    "ORGAN_DRAG_GAIN": 1.0,
    # Itme tabani (max(1.0, net_kuvvet)) kaldirilinca silialarin gercek
    # katkisi ortaya cikti: 0.2 ile alti simetrik silia bir kamcinin
    # %15'i kadar itiyordu, yani pratikte islevsizlerdi - taban onlarin
    # eksikligini orturuyordu. 1.0'da alti silia bir kamcinin %74'u kadar
    # eder: silia isini goren ama tek basina kamci kadar guclu olmayan bir
    # yatirim olur.
    "CILIA_SPEED_MULTI": 1.0,
    "FLAGELLA_SPEED_MULTI": 0.5,
    "DIGESTION_TIME": 10.0,
    "RIBOSOME_TIME": 10.0,
    # Depo = vakuol alani (30) x bu carpan = 500 birim
    "VACUOLE_ENERGY_MULTI": 50.0,
    "ENERGY_REGEN_BASE": 1.0,
    # --- ENERJI EKONOMISI ---
    # Enerjinin TEK kaynağı sindirilen besindir. Bir besinin sindirimi
    # bittiğinde membran (ETC) onu enerjiye çevirir:
    #     kazanç = FOOD_ENERGY * ETC verimliliği
    # ETC verimliliği 'move_regen' geniyle yükseltilir.
    # OLCULDU - metabolik marj yoktu ve KARMASIKLIK KARSILANAMIYORDU.
    #
    #   sindirim boru hatti : 10 sn/besin  -> en fazla 3.0 enerji/sn gelir
    #   baslangic hucresinin bakimi        -> 2.18 enerji/sn gider
    #   kalan artik                        -> 0.82 enerji/sn
    #
    # Yani gelirin %73'u ayakta kalmaya gidiyordu. Yeni bir organ 0.12-0.63
    # enerji/sn goturur; iki organ eklemek artigin tamamini siliyordu.
    # Populasyonun organ sayisi bu yuzden butun kosu boyunca 6.9-7.1
    # arasinda cakili kaldi - "kompleks hucreler gelismesi" istenirken
    # karmasiklik fiziksel olarak KARSILANAMAZ durumdaydi.
    #
    # Ayni daralma kusak suresini de belirliyordu: 166 enerjilik bolunme
    # bedeli 0.82 artikla ~200 saniyede toplaniyordu. 900 saniyelik bir
    # kosu topu topu bes kusak eder; bes kusakta evrim gozlenemez.
    #
    # 90 ile gelir 9.0 enerji/sn, artik 6.8 - bakimin uc kati. Hucre hem
    # organ tasiyabilir hem de ~25 saniyede bolunur. Besin TUKETIM hizi
    # degismez (yine 10 saniyede bir besin), yalnizca bir besinin kalorisi
    # artar; ekosistemin besin akisi ve kitlik dengesi bozulmaz.
    "FOOD_ENERGY": 270.0,
    # Yeni bir hücre inşa etmenin bedeli. Bölünme ancak bu enerji varsa
    # gerçekleşir; kalan enerji iki yavruya eşit bölünür.
    # BEDEL BUYUKLUKLE OLCEKLENIR: bolunmek tum hucreyi (govde + organlar)
    # kopyalamaktir. Sabit bedel buyuk hucreleri odullendiriyordu - kaotropi
    # 9 kat govdesiyle optropiyle ayni 50'yi oduyordu.
    "DIVISION_ENERGY_COST": 50.0,
    # Referans alan: bu buyuklukteki hucre tam DIVISION_ENERGY_COST oder.
    # Varsayilan optropi (govde 314 + organlar ~95) ~400 eder.
    "DIVISION_COST_REF_AREA": 400.0,
    # --- ORGAN BAKIM MALIYETLERI (birim/sn) ---
    # Her yapinin sahip oldugu kadar bakim gideri vardir. Eskiden yalnizca
    # motorlar, isitme ve gorme maliyetliydi; burun, govde, depo, ribozom,
    # sindirim, zar ve hafiza bedavaydi - bu yuzden bazi genler saf kazancti.
    # Maliyetler organ mantiklarinda base_energy_cost olarak tanimlidir.
    "COST_FLAGELLA": 0.03,
    "COST_CILIA": 0.05,
    "COST_CHEMORECEPTOR": 0.02,
    "COST_MECHANORECEPTOR": 0.002,
    # SES = hidrodinamik bozulma = yaricap x hiz. Bu referans degerdeki bir
    # hedef, kulagin tam hassasiyet mesafesinden duyulur. Yaricapi 22,
    # hizi 25 olan orta bir hucre ~550 uretir.
    "GURULTU_REF": 550.0,
    # Kulagin hassasiyeti = size x bu. size 1.0 (baslangic) -> 120 px,
    # yani koku menziliyle ayni. Gurultulu hedef daha uzaktan, sessiz
    # hedef hic duyulmaz.
    "SES_MENZIL_OLCEGI": 120.0,
    # Kapsama: sesin YONUNU cikarma yetisi (0 = yonsuz, 1 = tam). Menzili
    # ARTIRMAZ. Kopepodun onlarca setasi bunun icindir: tek seta "bir sey
    # oldu" der, cok seta "surdan geliyor" der. Dusuk baslar ki gelisecek
    # yer olsun.
    "MECHANO_KAPSAMA_TABAN": 0.15,
    "GROW_MECHANO_KAPSAMA": 0.12,
    # Esik gelisimi carpansaldir: her kademe esigi %12 dusurur, yani
    # menzili %6.5 artirir. Alt sinir, tek bir kulagin butun haritayi
    # duymasini engeller.
    "GROW_MECHANO_ESIK": 0.12,
    "MECHANO_ESIK_MIN": 0.0015,
    # KOKU SURUKLENMESI (saniye). Hizli yuzen bir hucrenin kokusu
    # ARKASINDA kalir: kaynak, konumundan `hiz x bu` kadar geride sayilir.
    # Peclet fiziginin karsiligi - uzerine gelen hizli bir cismi burunla
    # gec fark edersin, arkandan gideni cok uzaktan koklarsin. Kulagi
    # gerekli kilan sey tam olarak budur: hizla yaklasan cisim buruna
    # SESSIZ, kulaga GURULTULUDUR.
    "KOKU_SURUKLENME": 1.5,
    # Duyulan sinyal esigin kac kati oldugunda tepki TAM gucle verilir.
    # Tam duyma sinirindaki (1x) bir kipirdanma tepkinin ucte birini,
    # sekiz kat guclu bir dalga tamamini uyandirir.
    "SES_ACILIYET_REF": 8.0,
    "COST_PHOTORECEPTOR": 0.001,
    "COST_CYTOPLASM": 0.15,
    "COST_DIGESTION": 0.3,
    "COST_VACUOLE": 0.01,
    "COST_RIBOSOME": 0.3,
    "COST_MEMBRANE": 0.1,
    "COST_MEMORY": 0.05,
    # Hafiza kapasitesinin dogal alt siniri ve her bolunmede eriyen pay.
    # `memory_length` geni kapasiteyi yalnizca artirabiliyor ve torbadan
    # herkes ayni sikilikta cekiyordu; kapasite 100 bin dogumda 24'ten
    # 173'e ciktı ve tek basina saniyede 8.65 enerji goturur oldu. Gercek
    # hucre kullanmadigi proteini yikar.
    "MEMORY_TABAN": 10.0,
    "MEMORY_CEVRIM": 0.02,
    # --- OLUM VE ELEME ---
    # Enerjisi biten hucre once "shutdown" olur (son sans: midesindeki besini
    # sindirip toparlanabilir). Bu sure boyunca toparlanamazsa olur ve
    # listeden dusser - eskiden sonsuza kadar donuk kalip CPU yiyordu.
    "STARVE_TIMEOUT": 15.0,
    # Olen hucre yerine besin birakir (les). Ilk varan alir.
    "CORPSE_FOOD_MAX": 24,
    # --- ZAR BUTUNLUGU VE SAVUNMA (savunma = zar ozelligi, organ degil) ---
    # Hasar uc kanaldan gelir: mekanik / kimyasal / yutma. Her savunma yalnizca
    # belirli kanallara ve yalnizca belirli menzillere karsi calisir; matris
    # boylece sabit kodlanmadan (kanal, temas) ikilisinden dogar.
    "MEMBRANE_INTEGRITY_BASE": 100.0,
    "GROW_MEMBRANE_INTEGRITY": 20.0,
    # Savunma gelisim adimlari
    # Yeni kazanilan bir katmanin BASLANGIC yatirimi. Sifir olamaz:
    # var olup hicbir koruma vermeyen ama bedelini goturen bir katman
    # her zaman elenir ve savunma hicbir zaman evrimlesemez.
    "YENI_KATMAN_YATIRIM": 0.6,
    "GROW_WALL": 0.5,      # peptidoglikan duvar  -> mekanik
    "GROW_OUTER": 0.5,     # dis zar / LPS        -> kimyasal
    "GROW_CAPSULE": 0.5,   # kapsul / mukus       -> TEMAS gerektiren her sey
    "GROW_EFFLUX": 0.5,    # efflux pompasi       -> kimyasal
    "GROW_REPAIR": 0.5,    # zar onarimi          -> sonradan iyilestirme
    "GROW_SLIP": 0.5,      # kayganlik            -> BAGLANMA direnci
    # Laboratuvar kesitindeki BES katmandan ikisi (mukus ve S-layer) oyunda
    # hic temsil edilmiyordu: kesitte cizilip duruyorlardi ama ne bir
    # yatirim ne bir bedelleri vardi. Artik otekiler gibi birer savunma.
    "GROW_MUCUS": 0.5,     # mukus / slime tabakasi -> yapismayi zorlastirir
    "GROW_SLAYER": 0.5,    # S-layer kristal orgu   -> mekanik + yutulmaya
    # Baglanma: stilet ve fagositoz once tutunmak zorunda. Direnc kayganlik
    # + kapsulden gelir (mukuslu yuzeye tutunmak zordur). Bu, kapsule ikinci
    # bir rol verir: "temas zirhi"nin yani sira "yakalanmaya karsi kacis".
    "BIND_BREAK_RATE": 1.2,          # kurtulma denemesi hizi
    "PHAGO_BIND_TIME": 1.2,          # yutmadan once tutma suresi (sn)
    "NEMATOCYST_TETHER_TIME": 2.5,   # zipkin ipinin avi tuttugu sure (sn)
    # Surekli bakim gideri (karar: savunma gelistirmeleri surekli enerji yakar)
    "COST_WALL": 0.25, "COST_OUTER": 0.15, "COST_CAPSULE": 0.20,
    "COST_EFFLUX": 0.10, "COST_REPAIR": 0.15, "COST_SLIP": 0.15,
    # Mukus ucuz ve hafif (cogu su), S-layer duvar kadar pahali degil ama
    # protein kristali oldugundan surekli yenilenmek zorunda.
    "COST_MUCUS": 0.08, "COST_SLAYER": 0.22,
    # KATMANIN KENDISI de bedel ister. Yatirim yapmasan bile duvari ayakta
    # tutmak, S-layer kristalini surekli yenilemek ATP yakar. Bu bedel
    # olmasaydi bir katmani KALDIRMAK saf kayip olurdu: eleklik korumasini
    # yitirir, karsiliginda hicbir sey kazanmazdin. Degerler taban
    # kalinlikla orantili secildi (mukus 7 ama sulu, S-layer 2 ama protein).
    "TABAN_COST_MUCUS": 0.10, "TABAN_COST_CAPSULE": 0.14,
    "TABAN_COST_SLAYER": 0.30, "TABAN_COST_WALL": 0.35,
    "COST_INTEGRITY": 0.002,   # butunluk puani basina
    "REPAIR_PER_POINT": 1.5,   # onarim puani basina saniyede iyilesen butunluk
    # Agirlik cezalari: duvar ve kapsul hucreyi yavaslatir
    "CAPSULE_SPEED_PENALTY": 0.06,
    "WALL_SPEED_PENALTY": 0.04,
    # GORUNUM OLCEGI: hucreler, organlari ve molekulleri ekranda bu oranda
    # cizilir. Zarf cekirdegin DISINA cizildigi icin bir hucre artik
    # yaricapinin ~2.76 kati yer kapliyordu ve dunya kalabalik gorunuyordu.
    # 0.25 ile her sey dortte bire iner; fare tekerlegi x4'e gelince eski
    # goruntuye donulur. FIZIK degismez - yalnizca cizim olcegi.
    # 1.0: zarf artik cekirdegin DISINA eklenmiyor, entity.radius'un
    # ICINE oturuyor. Cizilen hucre boylece kendiliginden 1/2.76 orani
    # kadar kucaldi (istenen 1/4'e cok yakin) ve en onemlisi cizim ile
    # temas yaricapi AYNI sayi oldu. Ayri bir gorunum olcegi tutmak artik
    # ikisini yeniden ayirmak olurdu.
    "GORUNUM_OLCEGI": 1.0,
    "MUCUS_SPEED_PENALTY": 0.02,
    "SLAYER_SPEED_PENALTY": 0.03,
    # --- SALDIRI ORGANLARI (Asama 3) ---
    # Karar: hasar enerji yakmaz, SALDIRI KULLANIMI yakar.
    # Her silahin kanali ve temas gereksinimi farkli; savunma matrisi
    # bu ikiliden dogar (bkz. logic_membrane.py).
    # Etki yayi (yari-aci, derece). Organ konumu artik isabeti de belirler:
    # hedef, organin BAKTIGI yonden bu kadar sapabilir. 180 = yonsuz.
    # Boylece "onu silahli ama arkasi acik" gibi vucut plani stratejileri
    # anlam kazanir ve donus yetenegi savasin parcasi olur.
    "STYLET_ARC": 18.0,
    "HARPOON_ARC": 60.0,
    "NEMATOCYST_ARC": 30.0,
    "TOXIN_ARC": 180.0,
    "LYSIN_ARC": 120.0,
    "PHAGO_ARC": 90.0,
    "STYLET_DAMAGE": 25.0,
    "STYLET_RANGE": 0.0,
    "STYLET_COOLDOWN": 0.8,
    "STYLET_ENERGY": 2.0,
    "STYLET_GROW": 0.25,
    "STYLET_COST": 0.05,
    "HARPOON_DAMAGE": 15.0,
    "HARPOON_RANGE": 6.0,
    "HARPOON_COOLDOWN": 0.3,
    "HARPOON_ENERGY": 6.0,
    "HARPOON_GROW": 0.25,
    "HARPOON_COST": 0.06,
    "NEMATOCYST_DAMAGE": 40.0,
    "NEMATOCYST_RANGE": 50.0,
    "NEMATOCYST_COOLDOWN": 6.0,
    "NEMATOCYST_ENERGY": 10.0,
    "NEMATOCYST_GROW": 0.2,
    "NEMATOCYST_COST": 0.12,
    # Bakteriosin varyanti sayisi. Kucuk tutulursa iki soy sik sik ayni
    # allele carpar ve birbirine bagisik cikar; buyuk tutulursa bagisiklik
    # neredeyse yalnizca oz kardesler arasinda kalir.
    "TOXIN_ALLELES": 12,
    "TOXIN_ALLELE_MUTATION": 0.02,
    "TOXIN_DAMAGE": 8.0,
    "TOXIN_RANGE": 60.0,
    "TOXIN_COOLDOWN": 0.0,
    "TOXIN_ENERGY": 3.0,
    "TOXIN_GROW": 0.25,
    "TOXIN_COST": 0.1,
    # LIZIN: zirhin CEVABI. Kimyasal oldugu icin duvari yok sayar - zirhli
    # bir populasyonda tek ise yarayan silah odur. 12 hasar / 1.2 sn
    # bekleme = 10 dps ile bu rolu oynayamiyordu: 100 butunluklu bir hedefi
    # oldurmek 10 saniye TEMAS gerektiriyor, iki hucre o kadar sure yan yana
    # kalamaz. Olculdu: lizin tasiyan takim 2/32 sagkalim, silahsiz 11/32.
    # 22 ile dps 18.3 olur - ciplak hedefte harpundan (50) hala cok zayif,
    # ama duvarli hedefte harpun sifira duserken lizin isini gorur.
    "LYSIN_DAMAGE": 9.0,
    "LYSIN_RANGE": 25.0,
    "LYSIN_COOLDOWN": 0.0,
    "LYSIN_ENERGY": 3.5,
    "LYSIN_GROW": 0.25,
    "LYSIN_COST": 0.05,
    "PHAGO_DAMAGE": 0.0,
    "PHAGO_RANGE": 0.0,
    "PHAGO_COOLDOWN": 3.0,
    "PHAGO_ENERGY": 8.0,
    "PHAGO_GROW": 0.1,
    "PHAGO_COST": 0.08,
    # Fagositoz ancak hedef bu oranin altindaysa mumkun (govde orani)
    "PHAGO_SIZE_RATIO": 0.7,
    "PHAGO_STUN": 1.0,   # yutarken avci hareketsiz kalir (sn)
    # --- DAVRANIS GENOMU (Asama 4) ---
    # Tum hucreler rastgele bir uyaran->tepki tablosuyla baslar; tablo
    # bolunmede aktarilir ve mutasyona ugrar. Silahlar ancak tablo "saldir"
    # dediginde ates eder - aksi halde hucreler kendi turunu vuruyordu.
    # --- KOKU ILE TANIMA ---
    # Koku menzili = SMELL_RANGE_BASE * kemoreseptor uzunlugu.
    # Kokunun ayirt edici ozelligi: KONI YOK ve gorusten UZUN. Kimyasal
    # sinyal gorus hatti gerektirmez, kosenin arkasindan gelir.
    # (Olculdu: gorus 15-25 px, ses 10-40 px, kemoreseptor uzunlugu 5-15.)
    # Koku menzili = SMELL_RANGE_BASE * kemoreseptor uzunlugu.
    # 8 iken baslangic burnu (uzunluk 6) yalnizca 48 px goruyordu - hucre
    # yaricapinin iki katindan az. Bir hucrenin baska bir hucreye tepki
    # verebilmesi icin once onu ALGILAMASI gerekiyor; 48 px'de bu ancak
    # carpismayla olur, yani kacma ya da saldirma karari verilecek zaman
    # hic kalmaz. 20 ile baslangic burnu 120 px (yaklasik bes govde capi)
    # kokluyor: nematosist (50) ve toksin (60) menzilinin otesi, yani
    # silah kullanmadan once hedefi secebilecek kadar erken.
    "SMELL_RANGE_BASE": 20.0,
    # --- KOKU KIMLIGI ---
    # Koku artik SUREKLI bir puandir (bkz. systems/signaling/scent_profile).
    # Ayrik sinif kalkti: kucuk genetik degisim puani biraz oynatir,
    # davranis ancak evrimlesmis bir sinira yakinsa doner - ani yabanci yok.
    #
    # SCENT_DIVERGENCE_THRESHOLD artik yalnizca AKRABALIK imzasini yonetir:
    # kac kalitsal degisiklik birikince hucre kendi soyunu tanimaz hale gelir.
    # Gelisimin iraksamaya katkisi. Yeni bir ORGAN kazanmak, tek bir genin
    # bir kademe buyumesinden cok daha buyuk bir fenotip degisimidir.
    "DIVERGENCE_NEW_ORGAN": 5.0,
    "DIVERGENCE_UPGRADE": 1.0,
    "SCENT_WEIGHT_MEMBRANE": 0.5,   # zarin koku puanina katkisi
    # Kesme noktalarinin mutasyonda ne kadar kaydigi (0-100 ekseninde).
    # Kucuk = ince ayar, buyuk = kaba arama.
    "SPECTRUM_MUTATION_SIGMA": 6.0,

    "SCENT_DIVERGENCE_THRESHOLD": 30.0,

    # --- KAIROMON ---
    # Av dokusu sindiren hucrenin metabolizmasindan sizan artik. SINYAL
    # DEGIL: yayan taraf zarar gorur (avlari onu fark eder) ama bastiramaz.
    "KAIROMONE_PER_KILL": 1.0,     # bir av/les yemenin kattigi sizinti
    "KAIROMONE_DECAY": 0.08,       # /sn temizlenme -> tek av ~12.5 sn surer
    "KAIROMONE_MAX": 5.0,          # doyma tavani
    # Alel sayisi INCE cozunurluk: akraba tanimada kullanilir. Ayni kokan
    # iki hucre akraba OLMAYABILIR, ama akraba olanlar ayni kokar.
    "SIGNATURE_ALLELES": 64,
    "SIGNATURE_COUPLED_RATIO": 0.7,
    "BEHAVIOR_MUTATION_RATE": 0.04,
    "BEHAVIOR_ENABLED": True,
    # DAVRANIS BIR SPEKTRUMDUR: -1 (tam guc kac) .. 0 (yoksay) .. +1
    # (tam guc saldir). Isaret ne yapilacagini, BUYUKLUK ne kadar motor
    # enerjisi harcanacagini soyler.
    #
    # Bu esigi asan pozitif deger bir SALDIRI TAAHHUDUDUR: silahlar ancak
    # o zaman ates eder. "Saldir" ayri bir emir degil, uzerine yeterince
    # kararli gitmenin sonucu.
    "ATAK_ESIGI": 0.5,
    # Bu esigi asan negatif deger tam kacistir; tablo kactigini soyluyorsa
    # beslenme onun onune gecemez.
    "KACIS_ESIGI": 0.5,
    # Tepki genlerinin mutasyonda ne kadar kaydigi. Ayrik tabloda mutasyon
    # "rastgele baska bir tepkiye don" idi ve birikmis uyumu tek hamlede
    # siliyordu; surekli eksende kucuk bir tedirginlik secilime
    # tirmanabilecegi bir egim birakir.
    "BEHAVIOR_MUTATION_SIGMA": 0.25,
    # Komsu yokken (besin ararken) motorlara verilen efor. Uclarda efor
    # 1.0'a cikar - kacmak ve saldirmak pahalidir.
    "MOTOR_TABAN_EFOR": 0.55,
    # Motor gucu efor'un KARESIYLE olceklenir (itki dogrusal). Hizi iki
    # katina cikarmak bedeli dorde katlar - surtunme fiziginin gerektirdigi
    # sey budur ve kacmayi/saldirmayi gercek bir karar haline getirir.
    "MOTOR_EFOR_USSU": 2.0,
    # Sosyal oncelik geni ile koku siddetinin karsilastirildigi olcek.
    # Koku algisi logaritmiktir ve pratikte 0-8 arasinda gezer; 8, gen 1.0
    # iken hucrenin en guclu kokuyu bile birakip komsusunun pesine
    # dusebilecegi anlamina gelir.
    "SOSYAL_ESIK": 8.0,
    # --- HUCRE-HUCRE CARPISMA ---
    # Eskiden hic carpisma cozumu yoktu: hucreler birbirinin icinden
    # geciyordu (olculdu: karelerin %100'unde en az bir cift ic ice,
    # en derin gecisme %97). Artik ust uste binenler ayriliyor.
    # Gercek hucreler kismen deforme olup birbirine yaslanabilir, o yuzden
    # kucuk bir tolerans birakilir - amac tam gecismeyi engellemek.
    "OVERLAP_TOLERANCE": 0.10,     # yaricap toplaminin bu kadari serbest
    "SEPARATION_STRENGTH": 0.5,    # girismenin bir karede duzeltilen orani
    "CYTOSKELETON_AREA": 10.0,
    "FOOD_AREA": 50.0,
    # Besin yeniden doğuşu: haritada saniyede kaç yeni besin belirsin.
    # 0 = kapalı (besinler tükenir). FOOD_MAX birikmeyi sınırlar.
    # Besin arzi kusak suresini populasyon duzeyinde belirler: 200 hucre
    # x 2.18 bakim = 436 enerji/sn zaten gidiyor. 20 besin/sn x 90 = 1800
    # enerji/sn arz ile kalan 1364, yani saniyede ~8 bolunme - kusak ~25 sn.
    # Bolluk secilimi zayiflatmaz: nufus tavani zaten saniyede en dusuk
    # enerjili 8 hucreyi eliyor, yani secilim baskisi tavandan geliyor.
    "FOOD_SPAWN_RATE": 4.89,
    # --- BESIN YAMALI DOGAR ---
    #
    # Besin haritaya duzgun dagildiginda koku alaninin gradyani duzlesir
    # ve kemotaksinin tirmanacagi bir egim kalmaz. Olculdu: yamasiz
    # dunyada kemoreseptor tasimak ZARARLI (kamci 16.2 besin, kamci+burun
    # 13.3) - organ enerji ve surtunme goturuyor, karsiliginda hicbir sey
    # vermiyor. Boyle bir dunyada duyu organlari evrimlesemez.
    #
    # Dogada besin zaten obek obektir: deniz kari, cokelti, olu hucre.
    # Bir yamayi bulmak beceri ister ve bulan cok kazanir - kemotaksinin
    # secilim baskisi bundan dogar.
    "FOOD_PATCH_SIZE": 26,       # bir yamadaki besin sayisi
    "FOOD_PATCH_SIGMA": 45.0,    # yamanin yaricapi (px, gauss)

    # BESIN YOGUNLUGU KITLIGI BELIRLER.
    #
    # 450 besin, 960.000 px'lik dunyada besin basina 2133 px demek; 22
    # yaricapli bir hucre 20 px/sn ile suzulurken saniyede 880 px tarar,
    # yani her 2.4 saniyede bir besine RASTGELE carpar. Oysa sindirim 10
    # saniye suruyor - besin bulmak hicbir zaman darbogaz olmuyor,
    # dolayisiyla koklamanin da bir getirisi olmuyordu. Olculdu: bollukta
    # hucreler organlarini dokuyor (7.0 -> 5.0).
    #
    # 150 ile rastgele carpisma araligi ~8-10 saniyeye cikar, yani
    # sindirim hiziyla ayni mertebeye. Artik besin bulmak da darbogaz:
    # daha iyi koklayan, sindirim kapasitesini dolduran kazanir.
    # BESIN SEYREK AMA ZENGIN.
    #
    # Olculdu: kemoreseptor populasyondan siliniyordu (1.00 -> 0.02) ama
    # kulak tutunuyordu (0.00 -> 0.79). Sebep, besin bulmanin BECERI
    # gerektirmemesiydi: 360 besin varken yaricapi 22 olan bir hucre
    # yalnizca suzulerek her 7.7 saniyede bir besine carpiyor, oysa
    # sindirim 10 saniye suruyor. Yani burun hicbir zaman darbogazi
    # acmiyordu; bedelini oduyor, karsiligini alamiyordu.
    #
    # Cozum besini AZALTMAK ama ayni oranda ZENGINLESTIRMEK: toplam enerji
    # akisi degismez (7.33/sn x 270 = 22/sn x 90), degisen tek sey lokmanin
    # seyrek ve degerli olmasi. Carpisma araligi 7.7 -> 23 saniyeye cikar,
    # yani sindirimin iki katindan uzun: artik besin BULMAK darbogaz.
    # Depo da ayni oranda buyur ki hucre ogunler arasinda dayanabilsin
    # (1500 enerji, bakim 2.2/sn ile ~11 dakika).
    "FOOD_MAX": 80,
    # NOT: Bu dört anahtar eskiden yalnızca settings.json'da vardı. save_all()
    # sadece DEFAULT_SETTINGS'te bulunanları yazdığı için, launcher'dan yapılan
    # ilk kayıtta dosyadan siliniyor ve sonraki açılışta program çöküyordu.
    "RIBOSOME_AREA": 20.0,
    "VACUOLE_AREA": 30.0,
    "CILIA_TURN_MULTI": 0.05,
    "FLAGELLA_TURN_MULTI": 0.005,

    "GROW_FLAGELLA": 3.0,
    "GROW_CILIA": 1.0,
    "GROW_DIGESTION": 0.5,
    "GROW_RIBOSOME": 0.5,
    "GROW_ENERGY_REGEN": 0.1,
    "GROW_MAX_ENERGY": 0.05,
    "GROW_VISION_RANGE": 5.0,
    "GROW_VISION_ANGLE": 2.0,
    "GROW_SMELL": 1.0,
    "GROW_SOUND": 2.0,
    # Govde buyumesi 0.01 iken bir adim hicbir sey ifade etmiyordu:
    # fagositozun boy esigine (kendinden %43 buyuk olmak) ulasmak icin
    # ayni geni 90 kez cekmek gerekiyordu - yani hicbir soy "iri avci"
    # olamiyordu. 0.05 ile ~18 cekiste esik asilir; irilesmenin bedeli
    # (surtunme, bolunme maliyeti, bakim) zaten odenmeye devam ediyor.
    "GROW_BODY": 0.05,
    # YUZEY/HACIM: bu boyutta enerji verimi 1.0'dir; iri hucre besinden
    # daha az enerji cikarir (zar cevreyle, sitoplazma alanla buyur).
    "YUZEY_HACIM_REF": 2.0,
    "GROW_MEMORY": 5,

    # Skaler koku alanı (ScentEnvironment)
    # SCENT_EVAP_RATE, koku bulutunun genişliğini belirler: L = sqrt(D/k).
    # Düşük buharlaşma → bulutlar birbirine karışır, arka plan yükselir ve
    # Weber-Fechner logaritması gradyanı ezer (bkz. CHEMO_SAMPLE_INTERVAL).
    # Koku alani hucreden daha uzaga ulasmali. Eski degerlerde
    # (0.8 / 1.0) kullanilabilir menzil 50 px idi - hucrenin kendi
    # yaricapindan (55) bile kucuk; hucre kendinden oteyi koklayamiyordu.
    # Olculdu: 0.08 / 4.0 ile menzil 200 px ve gradyan duzgun
    # (20px=2.91, 50px=0.91, 100px=0.16, 150px=0.03).
    # Bulut genisligi L = sqrt(D/k). 0.08'de L = 35 px; koku yalnizca
    # yamanin dibinde ise yariyordu. 0.012 ile L = 91 px - bulut cok daha
    # uzaga uzanir ve yamalar yine de birbirine karismaz.
    "SCENT_EVAP_RATE": 0.012,
    "SCENT_DIFF_RATE": 4.0,
    # Tavan BAGLAYICI OLMAMALI. 100 iken alan genis bir bolgede tavana
    # yapisip egimi tamamen duzlestiriyordu: buharlasmayi dusurup kokuyu
    # uzaga yaymak, tirmanilabilir alani %19'dan %13'e, daha da dusurunce
    # %0.1'e indiriyordu. Doygunluk gradyani oldurur.
    "SCENT_MAX": 5000.0,
    "FOOD_SCENT_EMISSION": 5.0,   # besin yarıçapı başına birim/sn
    # Izgara çözünürlüğü. Koku hücre başına saklandığı için, hücre ne kadar
    # büyükse kaynak gerçek konumundan o kadar kayık görünür (yarım hücreye
    # kadar). Küçültmek hem görüntüyü hem canlının aldığı sinyali netleştirir,
    # maliyeti hücre sayısıyla kareli artar.
    "SCENT_CELL_SIZE": 10,
    # Isı haritası kaç saniyede bir yeniden çizilsin. Koku yavaş değiştiği
    # için her kare yeniden çizmek gereksiz; arada önbellek kullanılır.
    "SCENT_HEATMAP_INTERVAL": 0.05,
    # Kemoreseptör algı eşiği = SCENT_SENSITIVITY_BASE / organ uzunluğu.
    # Küçültmek tüm burunları hassaslaştırır; büyütmek körleştirir.
    "SCENT_SENSITIVITY_BASE": 0.3,

    # --- BÖLÜNME MODU (mitoz) ---
    # Açıkken hücre, aldığı besinin SİNDİRİMİ BİTTİĞİNDE iki eş yavruya
    # bölünür (ebeveyn kalmaz). Besinin sağladığı gelişim iki yavru için
    # BAĞIMSIZ çekilir: birinin burnu uzarken diğerinin flagellası
    # gelişebilir, aynı geni çekmeleri de mümkündür.
    # Kapalıyken klasik davranış: tek organizma, genom sırasına göre tek
    # yükseltme (manifestodaki "sıralı deterministik gelişim").
    "DIVISION_MODE": True,
    # Nüfus tavanı. 0 = SINIRSIZ (nüfusu besin arzı ve avcılar dengeler).
    # Pozitif bir değer verilirse tavanda bölünme durur, hücre yükseltmesini
    # yine torbadan rastgele çeker (genetik model değişmez).
    # Nufus tavani AYNI ZAMANDA en buyuk hiz kolu. Olculdu (adim maliyeti
    # ve simulasyonun ulasabilecegi en yuksek hiz):
    #     200 -> 26.7 ms -> 1.25x        100 -> 12.7 ms -> 2.62x
    #     140 -> 19.1 ms -> 1.75x         70 ->  9.6 ms -> 3.48x
    #     120 -> ~16  ms -> ~2.1x         45 ->  5.6 ms -> 6.00x
    # Makine zorlaniyorsa launcher'dan dusurulebilir; buyutmek cesitliligi
    # ve secilim gucunu artirir.
    "DIVISION_MAX_POPULATION": 120,

    # --- ORGAN MUTASYONU ---
    #
    # Yeni organ, once YALNIZCA avlanma odulu olarak kazanilabiliyordu
    # (consume_prey -> pending_organ_rolls). Bu bir kisir dongudur: silah
    # kazanmak icin avlanmak, avlanmak icin silah gerekiyordu. Ilk avci
    # hicbir zaman ortaya cikamazdi.
    #
    # Dogada yeni bir islev boyle kazanilmaz; gen ikilenmesi, yatay gen
    # aktarimi ve mutasyon yoluyla - yani hucrenin ne yaptigindan BAGIMSIZ
    # olarak - kazanilir. Ustelik bedeli pesin odenir: organ enerji yer,
    # surtunme artirir. Ise yaramazsa tasiyani eler.
    "ORGAN_GAIN_RATE": 0.02,     # bolunme basina yeni organ olasiligi
    # Kayip da en az kazanc kadar gercek. Islevsiz bir organ enerji
    # yakmaya devam eder; onu yitiren yavru ucuza yasar. Indirgeyici
    # evrim buradan cikar - ve savunma tipinin silahlarini birakmasi da.
    "ORGAN_LOSS_RATE": 0.02,
    # VUCUT PLANI DA EVRIMLESIR. Organin takilma acisi bir kez rastgele
    # atanip sonsuza kadar oyle kaliyordu; ise yaramayan bir yerlesim
    # duzeltilemiyordu. Kucuk kaymalar secilime tirmanacak bir egim verir.
    "ORGAN_ANGLE_RATE": 0.10,
    "ORGAN_ANGLE_SIGMA": 18.0,    # derece
    # Renk kalitsaldir ve kayar; boylece fotoreseptorun okudugu sey bir
    # sinif etiketi degil evrimlesen bir SINYAL olur (aposematizm/mimikri).
    "RENK_MUTASYON": 0.06,
    "RENK_SIGMA": 0.05,

    # Run-and-Tumble chemotaxis
    # KEMOTAKTIK KAZANC: alicidan gelen kucuk bir fark, kosu suresine ne
    # kadar buyuk bir degisim olarak gecer.
    #
    # 5 iken hucre kendi koku alanini KULLANAMIYORDU. Olculdu: ayni alanda
    # tirmanilabilir bolge kazanc 5'te %1.9, kazanc 15'te %62.4, kazanc
    # 40'ta %85.9. Yani darbogaz ne besin yogunlugu ne koku menziliydi -
    # sinyalin YUKSELTILMESIYDI.
    #
    # Yuksek kazanc biyolojik olarak da dogrusu: E. coli'nin kemotaksi
    # agi, binlerce alicinin isbirlikci kumeler halinde dizilmesiyle
    # sinyali ~35 kat yukseltir. 5 gercekci degildi, dusuktu.
    # KAZANC ARTIK BIR GEN (kemoreseptorde). Buradakiler yalnizca TABAN,
    # TAVAN ve gelisim adimi. Kazanc: alicidan gelen kucuk bir fark
    # davranisa ne kadar buyuk bir degisim olarak gecer - esikten
    # bagimsiz bir molekuler ozellik (alici kumelerinin isbirligi).
    "CHEMO_GAIN_TABAN": 20.0,
    "CHEMO_GAIN_MAX": 60.0,
    "GROW_CHEMO_GAIN": 4.0,
    # Ornekleme penceresi de gen: uzun ortalama gurultuyu bastirir ama
    # tepkiyi geciktirir.
    "CHEMO_PENCERE_MAX": 3.0,
    "GROW_CHEMO_PENCERE": 0.25,
    # BERG-PURCELL: bagil olcum hatasi ~ sqrt(bu / (derisim x sure)).
    # Kazanc genini bedelli kilan sey budur - gurultusuz bir kazanc geni
    # "hep buyut" demek olurdu.
    # Olculdu: gurultu 0.005'te en iyi kazanc 48, 0.015'te 24 - yani
    # kazancin gurultuye BAGLI bir optimumu var ve fazlasi geri tepiyor.
    # 0.01, tabani (20) acikca faydali birakip yukselmeye de yer birakan
    # seviye.
    "CHEMO_GURULTU": 0.01,
    # Koku ne kadar sure hic alinmazsa adaptasyon durumu sifirlanir.
    # Tek bir gurultulu kare pencereyi silmemeli.
    "KOKU_UNUTMA": 1.5,
    # (geriye uyumluluk: kemoreseptoru olmayan bir yol buraya duserse)
    "TUMBLE_GAIN_POSITIVE": 20.0,
    # Negatif kazanc pozitifin bu kati (kotulesirken daha cabuk don).
    "TUMBLE_NEG_ORAN": 0.4,
    "TUMBLE_GAIN_NEGATIVE": 8.0,
    "TUMBLE_RATE_MIN": 0.05,
    "TUMBLE_RATE_MAX": 10.0,
    "BASE_TUMBLE_RATE": 1.0,
    # Algı penceresi. Kare başına (1/60 sn) ölçülen fark, canlı o sürede
    # neredeyse hiç yer değiştirmediği için sıfıra yakın çıkar; bu pencere
    # boyunca biriktirilip pencere ortalamaları karşılaştırılır.
    "CHEMO_SAMPLE_INTERVAL": 0.5,

    # Kemotaksinin kosuyu uzatabilecegi/kisaltabilecegi en fazla oran.
    # Ustel kazanc sinirsiz birakilirsa tek bir pencere olcumu hucreyi
    # dakikalarca ayni yone kilitleyebilir.
    "CHEMO_RUN_CLAMP": 6.0,
    # Uzamsal gradyan icin gereken en az KONTRAST (aliciler arasi algi
    # farkinin ortalamaya orani). Altinda kalan fark gurultudur; hucre
    # olmayan bir yonu takip etmemeli.
    "SPATIAL_CHEMO_MIN": 0.06,
    # Tumble acisinin dagilimi (derece, gauss sigma). Duzgun dagilim
    # (-180..180) bir onceki kosudan kalan yon bilgisini tamamen siler;
    # gradyan yuruyusu ancak sureklilik kalirsa ise yarar. E. coli'nin
    # tumble acisi ~68 derece ortalamalidir.
    "TUMBLE_ANGLE_SIGMA": 60.0,

    # Levy flight (idle wandering)
    "LEVY_ALPHA": 1.5,
    "LEVY_MIN_STEP": 0.5,
    "LEVY_MAX_DURATION": 10.0
}

# Added ribosome_area and vacuole_area to each entity
DEFAULT_ENTITY_CONFIGS = {
    "optropi_0": {"name": "Magenta", "cytoplasm": 2.0, "flagella": 10.0, "cilia": 3.0, "vision_range": 25.0, "vision_angle": 10.0, "memory": 10, "smell": 5.0, "sound": 30.0, "ribosome_area": 20.0, "vacuole_area": 30.0},
    "optropi_1": {"name": "Yellow", "cytoplasm": 2.0, "flagella": 10.0, "cilia": 3.0, "vision_range": 25.0, "vision_angle": 10.0, "memory": 10, "smell": 5.0, "sound": 30.0, "ribosome_area": 20.0, "vacuole_area": 30.0},
    "optropi_2": {"name": "Lime Green", "cytoplasm": 2.0, "flagella": 10.0, "cilia": 3.0, "vision_range": 25.0, "vision_angle": 10.0, "memory": 10, "smell": 5.0, "sound": 30.0, "ribosome_area": 20.0, "vacuole_area": 30.0},
    "optropi_3": {"name": "Orange", "cytoplasm": 2.0, "flagella": 10.0, "cilia": 3.0, "vision_range": 25.0, "vision_angle": 10.0, "memory": 10, "smell": 5.0, "sound": 30.0, "ribosome_area": 20.0, "vacuole_area": 30.0},
    "kaotropi":  {"name": "Kaotropi", "cytoplasm": 3.0, "flagella": 15.0, "cilia": 2.0, "vision_range": 60.0, "vision_angle": 30.0, "memory": 10, "smell": 5.0, "sound": 40.0, "ribosome_area": 25.0, "vacuole_area": 40.0},
    "notropi":   {"name": "Hunter", "cytoplasm": 2.0, "flagella": 20.0, "cilia": 1.0, "vision_range": 15.0, "vision_angle": 10.0, "memory": 10, "smell": 5.0, "sound": 10.0, "ribosome_area": 15.0, "vacuole_area": 20.0}
}

# Modülün kendi konumuna göre mutlak yol. Göreli yol kullanılırsa, proje
# klasörü dışından başlatıldığında dosya bulunamaz ve ayarlar sessizce
# varsayılanlara düşer; sadece settings.json'da tanımlı olan anahtarlar
# (RIBOSOME_AREA gibi) kaybolduğu için program çöker.
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "settings.json")

def get_default(attr):
    """Bir ayarın koddaki özgün varsayılanı (settings.json'dan bağımsız)."""
    return DEFAULT_SETTINGS.get(attr)

def reset_value(attr):
    """Ayarı koddaki varsayılanına döndür ve kaydet."""
    if attr in DEFAULT_SETTINGS:
        globals()[attr] = DEFAULT_SETTINGS[attr]
        save_all()
        return DEFAULT_SETTINGS[attr]
    return None

def load():
    # DİKKAT: sözlüklerin KOPYASI alınır. Eskiden DEFAULT_SETTINGS doğrudan
    # kullanılıp update() ile yerinde güncelleniyordu; bu, import anında
    # varsayılanları yok ediyor ve "varsayılana dön" imkânsız hale geliyordu.
    configs = {
        "settings": dict(DEFAULT_SETTINGS),
        "entities": {k: dict(v) for k, v in DEFAULT_ENTITY_CONFIGS.items()},
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if "settings" in loaded: configs["settings"].update(loaded["settings"])
                if "entities" in loaded:
                    for k, v in loaded["entities"].items():
                        if k in configs["entities"]: configs["entities"][k].update(v)
        except Exception as e:
            # Sessizce yutma: bozuk bir settings.json'ın fark edilmemesi,
            # saatlerce yanlış parametrelerle simülasyon koşturmaya yol açar.
            print(f"[UYARI] {SETTINGS_FILE} okunamadi ({e}); varsayilanlar kullanilacak.")
    return configs

def save_all():
    current_settings = {k: v for k, v in globals().items() if k.isupper() and k in DEFAULT_SETTINGS}
    to_save = {"settings": current_settings, "entities": ENTITY_CONFIGS}
    # load() utf-8 okuduğu için yazarken de açıkça utf-8 kullanılır
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=4)

def set_value(attr, val):
    globals()[attr] = val
    save_all()

def set_entity_value(ent_id, key, val):
    ENTITY_CONFIGS[ent_id][key] = val
    save_all()

def set_entity_organs(ent_id, organs_list):
    """
    Organ konfigürasyonunu kaydet.
    organs_list: [{"type": "Photoreceptor", "angle": 0.0, "params": {...}}, ...]
    """
    ENTITY_CONFIGS[ent_id]["organs"] = organs_list
    save_all()

def get_entity_organs(ent_id):
    """Organ konfigürasyonunu al. Yoksa None döner."""
    return ENTITY_CONFIGS.get(ent_id, {}).get("organs", None)

def clear_entity_organs(ent_id):
    """Organ konfigürasyonunu temizle (varsayılana dön)."""
    if ent_id in ENTITY_CONFIGS and "organs" in ENTITY_CONFIGS[ent_id]:
        del ENTITY_CONFIGS[ent_id]["organs"]
        save_all()

# SESSIZ: dogum/motor teshis ciktilarini kapatir.
#
# Bolunme modunda her yavru dogdugunda "Optimal On / Max Hiz" satiri
# basiliyordu. Populasyon evrimlesirken bu saniyede yuzlerce satir eder;
# hem olcum ciktisini bogar hem de yalnizca yazdirma yuzunden simulasyon
# birkac kat yavaslar. Oyun bunu False yapip eski davranisi geri alabilir.
SESSIZ = True

# Initialize
_data = load()
globals().update(_data["settings"])
ENTITY_CONFIGS = _data["entities"]

# --------------------------------------------------------- KURESEL OLCEK
#
# Laboratuvardaki hucre 304 px, simulasyondaki 10 px - 30 kat fark. Gozenek
# fizigi ancak hucre yeterince buyuk cizilirse anlamli, cunku duvar deligi
# 15 px ve molekul capi 8-22 px.
#
# Ama hucreyi TEK BASINA buyutmek ekosistemi cokertir; olculdu:
#   kamci 30 px       -> 300 px'lik hucrede kirinti kalir
#   gorus menzili 25  -> hucre kendi govdesinden oteyi goremez
#   besin alani 100   -> yaricap 5.6 px, toz tanesi
#   Stokes surtunmesi -> yaricap 300'de hiz %3'e duser
#
# Bu yuzden UZUNLUK turu her ayar ayni carpanla, ALAN turu karesiyle
# olceklenir. Boylece butun oranlar korunur ve gozenek fizigi gercekci
# kalir - istenen tam olarak buydu.
WORLD_SCALE = float(_data["settings"].get("WORLD_SCALE", 1.0))
if WORLD_SCALE != 1.0:
    # SCENT_CELL_SIZE de bir UZUNLUKTUR. Olceklenmezse koku izgarasi
    # dunya alaniyla buyuyor: olcek 3'te 60 kare 36 saniye suruyordu.
    # Olcekle birlikte buyuyunce izgaradaki HUCRE SAYISI sabit kalir.
    for _k in ("DRAG_REF_RADIUS", "SMELL_RANGE_BASE", "THRUST_SCALE"):
        if _k in globals():
            globals()[_k] = globals()[_k] * WORLD_SCALE
    # Izgara adimi TAM SAYI olmali - dizinlemede kullaniliyor, ondalik
    # yapinca "can't multiply sequence by non-int" ile patliyor.
    if "SCENT_CELL_SIZE" in globals():
        SCENT_CELL_SIZE = max(1, int(round(globals()["SCENT_CELL_SIZE"] * WORLD_SCALE)))
        globals()["SCENT_CELL_SIZE"] = SCENT_CELL_SIZE
    for _k in ("FOOD_AREA", "VACUOLE_AREA", "RIBOSOME_AREA",
               "CYTOSKELETON_AREA"):
        if _k in globals():
            globals()[_k] = globals()[_k] * WORLD_SCALE ** 2
