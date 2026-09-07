

# Project EvoSim: Gelişmiş Duyusal ve Genetik Mimari

> **Versiyon:** 2.0 (Biological Realism Update)
> **Tarih:** 2024
> **Durum:** Tasarım & Entegrasyon Aşaması

Bu belge, simülasyonun "oyun mekaniği" tabanlı yapıdan, biyolojik olarak tutarlı **Yapay Yaşam (ALife)** mimarisine geçişini, kullanılan matematiksel modelleri ve teknik uygulama detaylarını içerir.

---

## 1. Temel Felsefe: "Tanrı Modundan" Yerel Algıya

Eski sistemde organizmalar, haritadaki tüm besinlerin konumunu kesin koordinatlarla biliyordu (Global Knowledge). Yeni sistemde organizmalar **Kör (Blind)** ve **Agnostik**tir. Sadece kendi vücutlarının kapladığı alandaki fiziksel büyüklükleri (koku yoğunluğu, ışık şiddeti) algılayabilirler.

**Hedef:** Organizmanın başarısı, "nereye gideceğini bilmesine" değil, "algıladığı sinyalleri nasıl işlediğine" (Sensory Processing) ve "vücut planının ne kadar verimli olduğuna" (Morphology) bağlı olmalıdır.

---

## 2. Ortam Fiziği: Skaler Alan (Scalar Field Environment)

Dünya artık boş bir koordinat sistemi değil, kimyasal bir difüzyon matrisidir.

### Teknik Yapı (`systems/environment.py`)
*   **Grid Sistemi:** Dünya, performans için optimize edilmiş bir ızgaraya (örn. 20x20 piksel hücreler) bölünür.
*   **Çift Tampon (Double Buffering):** Okuma ve yazma çakışmalarını önlemek için hesaplamalar `scratch_buffer` üzerinde yapılır ve `main_buffer` ile takas edilir.

### Fiziksel Süreç (Her Frame)
1.  **Kaynak (Source):** Besinler bulundukları hücreye koku değeri ekler (`+Amount`).
2.  **Buharlaşma (Decay):** Tüm grid belirli bir oranda azalır (`Grid *= 0.98`).
3.  **Yayılım (Diffusion):** Değerler komşu hücrelere yayılır (Laplacian Operator / Gaussian Blur).

**Sonuç:** Organizma `get_food_vector()` çağırmaz; `environment.get_concentration_at(x, y)` çağırır. Bu işlem $O(1)$ karmaşıklığındadır.

---

## 3. Duyusal Ekoloji: Weber-Fechner Yasası

Bir organizmanın algısı, uyaranın şiddetiyle lineer değil, logaritmik ilişkilidir. Bu, organizmanın hem çok düşük hem de çok yüksek yoğunluklarda hassas kalabilmesini sağlar.

### Algı Formülü (`logic_chemoreceptor.py`)
$$ S = \ln\left(1 + \frac{I}{I_{threshold}}\right) $$

*   **$I$ (Raw Intensity):** Ortamdan okunan ham koku değeri.
*   **$I_{threshold}$ (Eşik):** Organın hassasiyeti.
*   **$S$ (Perception):** Beyne giden sinyal.

### Evrimsel Bağlantı (Morphology-Function Coupling)
Eşik değeri sabit değildir; organın fiziksel boyutuna bağlıdır.
$$ I_{threshold} \propto \frac{1}{\text{Organ Length}} $$
*   **Uzun Kemoreseptör:** Düşük eşik $\rightarrow$ Zayıf kokuları algılar $\rightarrow$ Uzaktan tespit.
*   **Kısa Kemoreseptör:** Yüksek eşik $\rightarrow$ Sadece dibindeki yemeği algılar.

---

## 4. Motor Kontrol: Zamansal Algılama (Temporal Sensing)

Organizmaların şekli evrimle sürekli değiştiği için (yeni organlar, farklı açılar), sabit bir "Sağ/Sol sensör farkı" (Stereo Sensing) hesabı güvenilmezdir. Bunun yerine **Zaman** boyutu kullanılır.

### Strateji: Klinokinesis (Run-and-Tumble)
Organizma anlık olarak yönünü bilmez, sadece durumunun **iyiye mi yoksa kötüye mi** gittiğini bilir.

**Algoritma:**
1.  Anlık algı değişimini hesapla: $\Delta S = S_{current} - S_{last}$
2.  **Karar Mekanizması:**
    *   **$\Delta S > 0$ (Koku Artıyor):** Doğru yoldasın. Dönme ihtimalini düşür ($P_{turn} \downarrow$). **(RUN)**
    *   **$\Delta S \le 0$ (Koku Azalıyor):** Yanlış yoldasın. Dönme ihtimalini artır ($P_{turn} \uparrow$). **(TUMBLE)**
3.  **Idle State (Koku Yok):**
    *   **Lévy Uçuşu (Lévy Flight):** Rastgele yürüyüş (Brownian) yerine; çoğunlukla kısa, nadiren çok uzun ve düz hamleler yaparak ortamı tara.

---

## 5. Genetik: Sıralı Deterministik Gelişim

Evrim artık "rastgele stat artışı" değildir. Her canlının bir **Genomu (İnşaat Planı)** vardır.

### Genom Yapısı (`Genome` Class)
Bir liste dolusu talimattır:
`genome = [("Flagella", 0), ("Eye", 1), ("Cilia", 0), ("Membrane", 0), ...]`

*   **Deterministik Büyüme:** Canlı enerji topladığında, listedeki sıradaki talimatı uygular. Liste sonuna gelince başa döner.
*   **Strateji Yarışı:**
    *   Canlı A: `[Motor, Motor, Göz]` $\rightarrow$ Hızlı avcı.
    *   Canlı B: `[Zar, Zar, Motor]` $\rightarrow$ Dayanıklı ve verimli.
*   **Mutasyon:** Üreme sırasında bu listeye;
    *   Yeni gen ekleme (Insertion)
    *   Gen silme (Deletion)
    *   Genlerin yerini değiştirme (Swap)
    işlemleri uygulanır.

---

## 6. Debug & Gözlem: The Inspector

Sistemin "Black Box" olmasını engellemek için geliştirilen Runtime Analiz Aracıdır.

### Özellikleri
*   **Seçim:** Simülasyonda bir canlıya tıklandığında aktif olur.
*   **Görselleştirme:**
    *   **Beyaz Halka:** Seçili canlıyı gösterir.
    *   **Yeşil Heatmap (Toggle 'H'):** Arkaplanda skaler koku alanını çizer.
*   **Veri Paneli (Heads-Up Display):**
    *   *Sensory:* Raw Intensity ($I$) vs Threshold ($I_{th}$) $\rightarrow$ Perception ($S$). (Canlının kör olup olmadığını gösterir).
    *   *Motor:* Delta ($\Delta S$) ve Tumble Probability. (Canlının neden döndüğünü açıklar).
    *   *Genetics:* Genom listesi ve sıradaki upgrade. (Canlının stratejisini gösterir).

---

## 7. Sistem Akış Diyagramı

```mermaid
graph TD
    A[Food Source] -->|Adds Scent| B(Environment Grid)
    B -->|Diffusion & Decay| B
    B -->|Get Concentration (I)| C[Chemoreceptor]
    C -->|Weber-Fechner Law (Log)| D{Perception (S)}
    D -->|Compare S(t) - S(t-1)| E[Cytoskeleton / Brain]
    E -->|Delta > 0| F[RUN Mode (Low Turn Prob)]
    E -->|Delta <= 0| G[TUMBLE Mode (High Turn Prob)]
    E -->|S ~= 0| H[LEVY FLIGHT (Random Search)]
    
    F & G & H -->|Target Vector| I[Smart Motor Controller]
    I -->|Thrust & Torque| J[Physics Body]
```

Bu belge, **EvoSim** projesinin biyolojik ve teknik omurgasıdır. Herhangi bir modülde değişiklik yaparken bu prensiplere sadık kalınmalıdır.