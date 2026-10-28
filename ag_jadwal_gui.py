import argparse
import os
import random
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass

# ----------------------------------------------------------------------
# 1. DATA (asumsi kapasitas & jumlah mhs: ganti dengan data riil bila ada)
# ----------------------------------------------------------------------
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
JAM = ["07:00-09:00", "09:00-11:00", "11:00-13:00","13:00-15:00", "15:00-17:00"]
N_HARI, N_JAM = len(HARI), len(JAM)
N_SLOT = N_HARI * N_JAM                      # 25 sesi (slot) per minggu

RUANG = {"FT-1": 45, "FT-2": 40, "FT-3": 35, "FT-4": 30, "FT-5": 30}
NAMA_RUANG = list(RUANG)
KAP = list(RUANG.values())
N_RUANG = len(NAMA_RUANG)                    # 5
N_GEN_NILAI = N_SLOT * N_RUANG               # 125 kemungkinan (slot, ruang)

DOSEN = {
    "LHH": "Liyando Hermawan Hasibuan, S.T., M.Kom.",
    "ASS": "Abertun Sagit Sahay, S.T., M.Eng.",
    "FS": "Felicia Sylviana, S.T., M.M.",
    "WDR": "Widiatry, S.T., M.T.",
    "JDP": "Drs. Jadiaman Parhusip, M.Kom.",
    "LCK": "Licantik, S.Kom., M.Kom.",
    "NVK": "Novera Kristianti, S.T., M.T.",
    "ARL": "Ariesta Lestari, S.Kom., M.Cs., Ph.D.",
}


@dataclass(frozen=True)
class MataKuliah:
    nama: str
    sem: int
    sks: int
    dosen: str
    mhs: int


MATKUL = [
    # Semester 1 (40 mhs)
    MataKuliah("Kalkulus I", 1, 3, "ASS", 40),
    MataKuliah("Pengantar Teknik Informatika", 1, 3, "FS", 40),
    MataKuliah("Logika Diskrit", 1, 3, "WDR", 40),
    MataKuliah("Algoritma dan Pemrograman I", 1, 3, "WDR", 40),
    MataKuliah("Aljabar Vektor dan Matriks", 1, 3, "FS", 40),
    MataKuliah("Arsitektur dan Organisasi Komputer", 1, 3, "JDP", 40),
    MataKuliah("Sistem Digital", 1, 3, "LHH", 40),
    # Semester 3 (35 mhs)
    MataKuliah("Basis Data I", 3, 3, "LCK", 35),
    MataKuliah("Pemrograman Berorientasi Objek", 3, 3, "WDR", 35),
    MataKuliah("Jaringan Komputer", 3, 3, "LHH", 35),
    MataKuliah("Kecerdasan Buatan", 3, 3, "ARL", 35),
    MataKuliah("Kompleksitas Algoritma", 3, 3, "ARL", 35),
    MataKuliah("Interaksi Manusia dan Komputer", 3, 3, "LCK", 35),
    MataKuliah("Analisis dan Desain Perangkat Lunak", 3, 3, "ASS", 35),
    # Semester 5 (30 mhs)
    MataKuliah("Metodologi Penelitian", 5, 3, "FS", 30),
    MataKuliah("Technopreneurship", 5, 3, "JDP", 30),
    MataKuliah("Keamanan Data dan Informasi", 5, 3, "LHH", 30),
    MataKuliah("Jaringan Syaraf Tiruan", 5, 3, "NVK", 30),
    MataKuliah("Pengolahan Citra Digital", 5, 3, "NVK", 30),
    MataKuliah("Data Mining", 5, 3, "ARL", 30),
]
N_MK = len(MATKUL)                           # 20


# ----------------------------------------------------------------------
# 2. REPRESENTASI KROMOSOM
#    gen ke-i (0..99) = sesi mata kuliah ke-i
#    slot = g // N_RUANG (0..19)  -> hari = slot // N_JAM, jam = slot % N_JAM
#    ruang = g % N_RUANG
# ----------------------------------------------------------------------
def decode(g):
    return g // N_RUANG, g % N_RUANG


def hari_jam(slot):
    return slot // N_JAM, slot % N_JAM


def buat_individu(rng):
    return [rng.randrange(N_GEN_NILAI) for _ in range(N_MK)]


# ----------------------------------------------------------------------
# 3. FUNGSI FITNESS
# ----------------------------------------------------------------------
def pelanggaran_keras(kr):
    """Kembalikan dict {H1..H4} = jumlah pelanggaran kendala keras."""
    h = {"H1": 0, "H2": 0, "H3": 0, "H4": 0}
    for i in range(N_MK):
        si, ri = decode(kr[i])
        if MATKUL[i].mhs > KAP[ri]:
            h["H4"] += 1                                  # kapasitas
        for j in range(i + 1, N_MK):
            sj, rj = decode(kr[j])
            if si != sj:
                continue
            if ri == rj:
                h["H2"] += 1                              # ruang bentrok
            if MATKUL[i].dosen == MATKUL[j].dosen:
                h["H1"] += 1                              # dosen bentrok
            if MATKUL[i].sem == MATKUL[j].sem:
                h["H3"] += 1                              # kelas bentrok
    return h


def pelanggaran_lunak(kr):
    """Hanya dilaporkan pada UTS (belum masuk fitness)."""
    s = {"S1": 0, "S2": 0, "S3": 0, "S4": 0}
    per_dosen_hari = defaultdict(int)
    per_sem_hari = defaultdict(list)
    for i in range(N_MK):
        slot, _ = decode(kr[i])
        hari, jam = hari_jam(slot)
        if hari == 4 and jam == 2:                        # Jumat 11-13
            s["S1"] += 1
        if jam == 3:                                      # 13-17
            s["S4"] += 1
        per_dosen_hari[(MATKUL[i].dosen, hari)] += 1
        per_sem_hari[(MATKUL[i].sem, hari)].append(jam)
    for n in per_dosen_hari.values():
        if n > 2:
            s["S2"] += n - 2
    for jams in per_sem_hari.values():
        jams = sorted(jams)
        for a, b in zip(jams, jams[1:]):
            if b - a > 1:
                s["S3"] += 1
    return s


def total_pelanggaran(kr):
    return sum(pelanggaran_keras(kr).values())


def fitness(kr):
    return 1.0 / (1.0 + total_pelanggaran(kr))


# ----------------------------------------------------------------------
# 4. OPERATOR GENETIKA
# ----------------------------------------------------------------------
def seleksi_roulette(pop, fit, rng, **_):
    return rng.choices(pop, weights=fit, k=1)[0]


def seleksi_turnamen(pop, fit, rng, k=3, **_):
    idx = rng.sample(range(len(pop)), k)
    return pop[max(idx, key=lambda i: fit[i])]


def crossover_satu_titik(a, b, rng):
    t = rng.randint(1, N_MK - 1)
    return a[:t] + b[t:], b[:t] + a[t:]


def crossover_uniform(a, b, rng):
    c1, c2 = a[:], b[:]
    for i in range(N_MK):
        if rng.random() < 0.5:
            c1[i], c2[i] = b[i], a[i]
    return c1, c2


def mutasi(kr, pm, rng):
    for i in range(N_MK):
        if rng.random() < pm:
            kr[i] = rng.randrange(N_GEN_NILAI)


SELEKSI = {"roulette": seleksi_roulette, "turnamen": seleksi_turnamen}
CROSSOVER = {"satu_titik": crossover_satu_titik, "uniform": crossover_uniform}


# ----------------------------------------------------------------------
# 5. LOOP EVOLUSI
# ----------------------------------------------------------------------
def jalankan_ag(seed=1, pop_size=100, max_gen=200, pc=0.8, pm=0.05,
                elit=2, k_turnamen=3, seleksi="turnamen", crossover="uniform",
                berhenti_saat_valid=True):
    rng = random.Random(seed)
    sel = SELEKSI[seleksi]
    cx = CROSSOVER[crossover]
    pop = [buat_individu(rng) for _ in range(pop_size)]

    riwayat_terbaik, riwayat_rata = [], []
    gen_valid_pertama = None
    terbaik, fit_terbaik = None, -1.0
    t0 = time.perf_counter()

    for gen in range(1, max_gen + 1):
        fit = [fitness(ind) for ind in pop]
        i_best = max(range(pop_size), key=lambda i: fit[i])
        if fit[i_best] > fit_terbaik:
            fit_terbaik, terbaik = fit[i_best], pop[i_best][:]
        riwayat_terbaik.append(fit[i_best])
        riwayat_rata.append(sum(fit) / pop_size)

        if fit[i_best] == 1.0 and gen_valid_pertama is None:
            gen_valid_pertama = gen
            if berhenti_saat_valid:
                break

        # elitisme
        urut = sorted(range(pop_size), key=lambda i: fit[i], reverse=True)
        baru = [pop[i][:] for i in urut[:elit]]
        # reproduksi
        while len(baru) < pop_size:
            a = sel(pop, fit, rng, k=k_turnamen)
            b = sel(pop, fit, rng, k=k_turnamen)
            if rng.random() < pc:
                c1, c2 = cx(a, b, rng)
            else:
                c1, c2 = a[:], b[:]
            mutasi(c1, pm, rng)
            mutasi(c2, pm, rng)
            baru.append(c1)
            if len(baru) < pop_size:
                baru.append(c2)
        pop = baru

    return {
        "seed": seed,
        "kromosom": terbaik,
        "fitness_terbaik": fit_terbaik,
        "fitness_rata_akhir": riwayat_rata[-1],
        "gen_valid_pertama": gen_valid_pertama,
        "riwayat_terbaik": riwayat_terbaik,
        "riwayat_rata": riwayat_rata,
        "waktu_detik": time.perf_counter() - t0,
    }


# ----------------------------------------------------------------------
# 6. KELUARAN: tabel hari x slot, CSV/Excel, grafik konvergensi
# ----------------------------------------------------------------------
def tabel_jadwal(kr):
    import pandas as pd
    sel = [["" for _ in HARI] for _ in JAM]
    for i, g in enumerate(kr):
        slot, r = decode(g)
        h, j = hari_jam(slot)
        teks = f"{MATKUL[i].nama} (Sem {MATKUL[i].sem}, {MATKUL[i].dosen}, {NAMA_RUANG[r]})"
        sel[j][h] = (sel[j][h] + "\n" + teks).strip()
    return pd.DataFrame(sel, index=JAM, columns=HARI)


def daftar_sesi(kr):
    import pandas as pd
    baris = []
    for i, g in enumerate(kr):
        slot, r = decode(g)
        h, j = hari_jam(slot)
        baris.append({
            "Mata Kuliah": MATKUL[i].nama, "Semester": MATKUL[i].sem,
            "SKS": MATKUL[i].sks, "Dosen": DOSEN[MATKUL[i].dosen],
            "Hari": HARI[h], "Jam": JAM[j], "Ruang": NAMA_RUANG[r],
            "Jumlah Mhs": MATKUL[i].mhs, "Kapasitas": KAP[r],
        })
    df = pd.DataFrame(baris)
    df["_h"] = df["Hari"].map({h: n for n, h in enumerate(HARI)})
    df["_j"] = df["Jam"].map({j: n for n, j in enumerate(JAM)})
    return df.sort_values(["_h", "_j", "Ruang"]).drop(columns=["_h", "_j"])


def simpan_hasil(hasil, folder="keluaran", awalan="jadwal"):
    os.makedirs(folder, exist_ok=True)
    kr = hasil["kromosom"]
    tabel_jadwal(kr).to_csv(f"{folder}/{awalan}_tabel.csv", encoding="utf-8-sig")
    daftar_sesi(kr).to_csv(f"{folder}/{awalan}_daftar.csv", index=False, encoding="utf-8-sig")
    try:
        with __import__("pandas").ExcelWriter(f"{folder}/{awalan}.xlsx") as w:
            tabel_jadwal(kr).to_excel(w, sheet_name="Tabel Hari x Jam")
            daftar_sesi(kr).to_excel(w, sheet_name="Daftar Sesi", index=False)
    except ImportError:
        print("openpyxl belum terpasang: ekspor Excel dilewati (CSV tetap dibuat).")
    grafik_konvergensi(hasil, f"{folder}/{awalan}_konvergensi.png")


def grafik_konvergensi(hasil, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.figure(figsize=(7, 4))
    plt.plot(hasil["riwayat_terbaik"], label="Fitness terbaik")
    plt.plot(hasil["riwayat_rata"], label="Fitness rata-rata")
    plt.xlabel("Generasi")
    plt.ylabel("Fitness")
    plt.title(f"Grafik konvergensi (seed {hasil['seed']})")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def cetak_ringkas(hasil):
    kr = hasil["kromosom"]
    print(f"Seed {hasil['seed']:>3} | fitness terbaik {hasil['fitness_terbaik']:.4f} | "
          f"rata akhir {hasil['fitness_rata_akhir']:.4f} | "
          f"gen valid pertama {hasil['gen_valid_pertama']} | "
          f"{hasil['waktu_detik']:.2f} dtk")
    print("   keras :", pelanggaran_keras(kr), "| lunak:", pelanggaran_lunak(kr))


# ----------------------------------------------------------------------
# 7. EKSPERIMEN (10 run / perbandingan operator)
# ----------------------------------------------------------------------
def ringkas(daftar_hasil):
    valid = [h["gen_valid_pertama"] for h in daftar_hasil if h["gen_valid_pertama"]]
    return {
        "run": len(daftar_hasil),
        "run_valid": len(valid),
        "fitness_terbaik_maks": max(h["fitness_terbaik"] for h in daftar_hasil),
        "fitness_terbaik_rata": statistics.mean(h["fitness_terbaik"] for h in daftar_hasil),
        "fitness_rata_akhir_rata": statistics.mean(h["fitness_rata_akhir"] for h in daftar_hasil),
        "gen_valid_pertama_rata": statistics.mean(valid) if valid else None,
    }


def eksperimen(n_run, folder="keluaran", **param):
    import pandas as pd
    os.makedirs(folder, exist_ok=True)
    hasil = [jalankan_ag(seed=s, **param) for s in range(1, n_run + 1)]
    for h in hasil:
        cetak_ringkas(h)
    df = pd.DataFrame([{k: h[k] for k in ("seed", "fitness_terbaik", "fitness_rata_akhir",
                                          "gen_valid_pertama", "waktu_detik")} for h in hasil])
    df.to_csv(f"{folder}/hasil_{n_run}_run.csv", index=False)
    print("\nRingkasan:", ringkas(hasil))
    terbaik = max(hasil, key=lambda h: (h["fitness_terbaik"],
                                        -(h["gen_valid_pertama"] or 10 ** 9)))
    simpan_hasil(terbaik, folder)
    return hasil


def bandingkan_operator(n_run=10, folder="keluaran", **param):
    import pandas as pd
    os.makedirs(folder, exist_ok=True)
    baris = []
    for sel in SELEKSI:
        for cx in CROSSOVER:
            p = dict(param, seleksi=sel, crossover=cx)
            hasil = [jalankan_ag(seed=s, **p) for s in range(1, n_run + 1)]
            baris.append({"seleksi": sel, "crossover": cx, **ringkas(hasil)})
    df = pd.DataFrame(baris)
    df.to_csv(f"{folder}/perbandingan_operator.csv", index=False)
    print(df.to_string(index=False))


# ----------------------------------------------------------------------
# 8. MAIN
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# 8. ANTARMUKA GRAFIS (GUI)
# ----------------------------------------------------------------------
def jalankan_gui():
    """GUI desktop: training, hasil jadwal, grafik, perbandingan dan ekspor."""
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    from threading import Thread
    import pandas as pd
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    root = tk.Tk()
    root.title("Optimasi Penjadwalan Kuliah - Algoritma Genetika")
    root.geometry("1200x780")
    root.minsize(950, 650)

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    hasil_aktif = {"hasil": None}
    folder_var = tk.StringVar(value="keluaran")
    status_var = tk.StringVar(value="Siap. Atur parameter, lalu tekan Mulai Training.")
    progress_var = tk.StringVar(value="Belum ada proses training.")

    def pilih_folder():
        path = filedialog.askdirectory(title="Pilih folder keluaran")
        if path:
            folder_var.set(path)

    # Menu aplikasi
    menubar = tk.Menu(root)
    menu_file = tk.Menu(menubar, tearoff=0)
    menu_file.add_command(label="Ekspor hasil...", command=lambda: ekspor_hasil())
    menu_file.add_command(label="Buka folder keluaran", command=lambda: buka_folder())
    menu_file.add_separator()
    menu_file.add_command(label="Keluar", command=root.destroy)
    menubar.add_cascade(label="File", menu=menu_file)
    menu_proses = tk.Menu(menubar, tearoff=0)
    menu_proses.add_command(label="Mulai training", command=lambda: mulai_training())
    menu_proses.add_command(label="Bandingkan operator", command=lambda: bandingkan())
    menu_proses.add_command(label="Tampilkan hasil terakhir", command=lambda: tampilkan_hasil())
    menubar.add_cascade(label="Proses", menu=menu_proses)
    menu_bantuan = tk.Menu(menubar, tearoff=0)
    menu_bantuan.add_command(label="Tentang", command=lambda: messagebox.showinfo(
        "Tentang", "Optimasi Penjadwalan Kuliah menggunakan Algoritma Genetika.\\n"
        "Operator seleksi, crossover, mutasi, dan elitisme dibuat sendiri."))
    menubar.add_cascade(label="Bantuan", menu=menu_bantuan)
    root.config(menu=menubar)

    header = ttk.Frame(root, padding=(12, 10))
    header.pack(fill="x")
    ttk.Label(header, text="OPTIMASI PENJADWALAN KULIAH",
              font=("Segoe UI", 17, "bold")).pack(anchor="w")
    ttk.Label(header, text="Algoritma Genetika • Training, visualisasi, dan evaluasi",
              font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

    main = ttk.Frame(root, padding=(12, 0, 12, 8))
    main.pack(fill="both", expand=True)

    left = ttk.LabelFrame(main, text="Parameter training", padding=10)
    left.pack(side="left", fill="y", padx=(0, 10))
    right = ttk.Frame(main)
    right.pack(side="left", fill="both", expand=True)

    def add_entry(parent, label, default, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        var = tk.StringVar(value=str(default))
        ent = ttk.Entry(parent, textvariable=var, width=12)
        ent.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=4)
        return var

    v_seed = add_entry(left, "Seed", 1, 0)
    v_pop = add_entry(left, "Ukuran populasi", 100, 1)
    v_gen = add_entry(left, "Maks. generasi", 200, 2)
    v_pc = add_entry(left, "Prob. crossover", 0.8, 3)
    v_pm = add_entry(left, "Prob. mutasi", 0.05, 4)
    v_elit = add_entry(left, "Elitisme", 2, 5)
    ttk.Label(left, text="Metode seleksi").grid(row=6, column=0, sticky="w", pady=4)
    v_sel = tk.StringVar(value="turnamen")
    ttk.Combobox(left, textvariable=v_sel, values=list(SELEKSI),
                 state="readonly", width=11).grid(row=6, column=1, sticky="ew", padx=(8, 0))
    ttk.Label(left, text="Crossover").grid(row=7, column=0, sticky="w", pady=4)
    v_cx = tk.StringVar(value="uniform")
    ttk.Combobox(left, textvariable=v_cx, values=list(CROSSOVER),
                 state="readonly", width=11).grid(row=7, column=1, sticky="ew", padx=(8, 0))
    ttk.Label(left, text="Folder keluaran").grid(row=8, column=0, sticky="w", pady=4)
    ttk.Entry(left, textvariable=folder_var, width=12).grid(row=8, column=1, sticky="ew", padx=(8, 0))
    ttk.Button(left, text="Pilih folder", command=pilih_folder).grid(
        row=9, column=0, columnspan=2, sticky="ew", pady=(2, 6))
    btn_train = ttk.Button(left, text="▶ Mulai Training", command=lambda: mulai_training())
    btn_train.grid(row=10, column=0, columnspan=2, sticky="ew", pady=4)
    btn_compare = ttk.Button(left, text="Bandingkan Operator", command=lambda: bandingkan())
    btn_compare.grid(row=11, column=0, columnspan=2, sticky="ew", pady=4)
    ttk.Button(left, text="Ekspor Hasil", command=lambda: ekspor_hasil()).grid(
        row=12, column=0, columnspan=2, sticky="ew", pady=4)
    ttk.Button(left, text="Tampilkan Hasil", command=lambda: tampilkan_hasil()).grid(
        row=13, column=0, columnspan=2, sticky="ew", pady=4)
    ttk.Separator(left).grid(row=14, column=0, columnspan=2, sticky="ew", pady=10)
    ttk.Label(left, textvariable=progress_var, wraplength=210,
              justify="left").grid(row=15, column=0, columnspan=2, sticky="w")
    left.columnconfigure(1, weight=1)

    tabs = ttk.Notebook(right)
    tabs.pack(fill="both", expand=True)
    tab_ringkasan = ttk.Frame(tabs, padding=10)
    tab_grafik = ttk.Frame(tabs, padding=8)
    tab_jadwal = ttk.Frame(tabs, padding=8)
    tab_operator = ttk.Frame(tabs, padding=8)
    tabs.add(tab_ringkasan, text="Ringkasan")
    tabs.add(tab_grafik, text="Grafik Training")
    tabs.add(tab_jadwal, text="Jadwal Kuliah")
    tabs.add(tab_operator, text="Perbandingan Operator")

    summary = tk.Text(tab_ringkasan, height=12, wrap="word", font=("Consolas", 10),
                      state="disabled")
    summary.pack(fill="both", expand=True)
    fig = Figure(figsize=(7, 4.2), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_title("Grafik konvergensi akan tampil setelah training")
    ax.set_xlabel("Generasi")
    ax.set_ylabel("Fitness")
    canvas = FigureCanvasTkAgg(fig, master=tab_grafik)
    canvas.get_tk_widget().pack(fill="both", expand=True)

    tree_frame = ttk.Frame(tab_jadwal)
    tree_frame.pack(fill="both", expand=True)
    cols = ("Mata Kuliah", "Semester", "SKS", "Dosen", "Hari", "Jam",
            "Ruang", "Jumlah Mhs", "Kapasitas")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=115 if col in ("Mata Kuliah", "Dosen") else 85, anchor="w")
    sy = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    sx = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
    tree.grid(row=0, column=0, sticky="nsew")
    sy.grid(row=0, column=1, sticky="ns")
    sx.grid(row=1, column=0, sticky="ew")
    tree_frame.rowconfigure(0, weight=1)
    tree_frame.columnconfigure(0, weight=1)

    op_text = tk.Text(tab_operator, wrap="none", font=("Consolas", 10), state="disabled")
    op_text.pack(fill="both", expand=True)

    def set_text(widget, content):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    def baca_param():
        seed = int(v_seed.get())
        pop = int(v_pop.get())
        gen = int(v_gen.get())
        pc = float(v_pc.get())
        pm = float(v_pm.get())
        elit = int(v_elit.get())
        if seed < 0 or pop < 2 or gen < 1 or not (0 <= pc <= 1) or not (0 <= pm <= 1):
            raise ValueError("Pastikan populasi ≥ 2, generasi ≥ 1, dan pc/pm antara 0 sampai 1.")
        if elit < 0 or elit >= pop:
            raise ValueError("Elitisme harus ≥ 0 dan lebih kecil dari ukuran populasi.")
        return dict(seed=seed, pop_size=pop, max_gen=gen, pc=pc, pm=pm, elit=elit,
                    seleksi=v_sel.get(), crossover=v_cx.get())

    def tampilkan_hasil():
        h = hasil_aktif["hasil"]
        if not h:
            messagebox.showinfo("Belum ada hasil", "Jalankan training terlebih dahulu.")
            return
        hk = pelanggaran_keras(h["kromosom"])
        hl = pelanggaran_lunak(h["kromosom"])
        valid_text = f"Generasi {h['gen_valid_pertama']}" if h["gen_valid_pertama"] else "Belum ditemukan"
        isi = (
            f"SEED                    : {h['seed']}\\n"
            f"FITNESS TERBAIK         : {h['fitness_terbaik']:.4f}\\n"
            f"FITNESS RATA-RATA AKHIR : {h['fitness_rata_akhir']:.4f}\\n"
            f"GENERASI VALID PERTAMA  : {valid_text}\\n"
            f"WAKTU TRAINING          : {h['waktu_detik']:.3f} detik\\n\\n"
            f"Pelanggaran kendala keras: {hk}\\n"
            f"Total kendala keras      : {sum(hk.values())}\\n"
            f"Pelanggaran kendala lunak (informasi): {hl}\\n\\n"
            "Keterangan fitness: 1.0 berarti tidak ada pelanggaran kendala keras.\\n"
            "Kendala lunak pada versi UTS hanya dilaporkan dan belum masuk fitness."
        )
        set_text(summary, isi)
        df = daftar_sesi(h["kromosom"])
        for item in tree.get_children():
            tree.delete(item)
        for _, row in df.iterrows():
            tree.insert("", "end", values=tuple(row[c] for c in cols))
        ax.clear()
        ax.plot(range(1, len(h["riwayat_terbaik"]) + 1), h["riwayat_terbaik"],
                label="Fitness terbaik")
        ax.plot(range(1, len(h["riwayat_rata"]) + 1), h["riwayat_rata"],
                label="Fitness rata-rata")
        ax.set_xlabel("Generasi")
        ax.set_ylabel("Fitness")
        ax.set_title("Konvergensi Algoritma Genetika")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        canvas.draw_idle()
        tabs.select(tab_ringkasan)
        status_var.set("Hasil training siap ditampilkan.")

    def mulai_training():
        try:
            param = baca_param()
            out = folder_var.get().strip() or "keluaran"
        except Exception as exc:
            messagebox.showerror("Parameter tidak valid", str(exc))
            return
        btn_train.configure(state="disabled")
        btn_compare.configure(state="disabled")
        progress_var.set("Training sedang berjalan...")
        status_var.set("Algoritma sedang mencari jadwal terbaik.")
        def worker():
            try:
                h = jalankan_ag(**param)
                simpan_hasil(h, out, "jadwal")
                def selesai():
                    hasil_aktif["hasil"] = h
                    tampilkan_hasil()
                    progress_var.set(f"Selesai: fitness {h['fitness_terbaik']:.4f}")
                    status_var.set(f"Training selesai dalam {h['waktu_detik']:.2f} detik.")
                    btn_train.configure(state="normal")
                    btn_compare.configure(state="normal")
                root.after(0, selesai)
            except Exception as exc:
                def gagal():
                    btn_train.configure(state="normal")
                    btn_compare.configure(state="normal")
                    progress_var.set("Training gagal.")
                    messagebox.showerror("Training gagal", str(exc))
                root.after(0, gagal)
        Thread(target=worker, daemon=True).start()

    def bandingkan():
        try:
            p = baca_param()
            out = folder_var.get().strip() or "keluaran"
            n_run = 10
            os.makedirs(out, exist_ok=True)
        except Exception as exc:
            messagebox.showerror("Parameter tidak valid", str(exc))
            return
        btn_train.configure(state="disabled")
        btn_compare.configure(state="disabled")
        progress_var.set("Menguji 4 kombinasi operator, masing-masing 10 run...")
        def worker():
            try:
                rows = []
                for sel in SELEKSI:
                    for cx in CROSSOVER:
                        param = dict(pop_size=p["pop_size"], max_gen=p["max_gen"],
                                     pc=p["pc"], pm=p["pm"], elit=p["elit"],
                                     seleksi=sel, crossover=cx)
                        hs = [jalankan_ag(seed=i, **param) for i in range(1, n_run + 1)]
                        rows.append({"Seleksi": sel, "Crossover": cx, **ringkas(hs)})
                df = pd.DataFrame(rows)
                df.to_csv(os.path.join(out, "perbandingan_operator.csv"), index=False,
                          encoding="utf-8-sig")
                def selesai():
                    set_text(op_text, df.to_string(index=False))
                    tabs.select(tab_operator)
                    progress_var.set("Perbandingan selesai. File CSV telah disimpan.")
                    btn_train.configure(state="normal")
                    btn_compare.configure(state="normal")
                root.after(0, selesai)
            except Exception as exc:
                def gagal():
                    btn_train.configure(state="normal")
                    btn_compare.configure(state="normal")
                    messagebox.showerror("Perbandingan gagal", str(exc))
                root.after(0, gagal)
        Thread(target=worker, daemon=True).start()

    def ekspor_hasil():
        h = hasil_aktif["hasil"]
        if not h:
            messagebox.showinfo("Belum ada hasil", "Jalankan training terlebih dahulu.")
            return
        out = filedialog.askdirectory(title="Pilih folder untuk menyimpan hasil")
        if not out:
            return
        try:
            simpan_hasil(h, out, "jadwal")
            messagebox.showinfo("Ekspor berhasil",
                f"Hasil disimpan di:\\n{os.path.abspath(out)}\\n\\n"
                "File: jadwal_tabel.csv, jadwal_daftar.csv, jadwal.xlsx (jika tersedia), "
                "dan jadwal_konvergensi.png.")
        except Exception as exc:
            messagebox.showerror("Ekspor gagal", str(exc))

    def buka_folder():
        out = folder_var.get().strip() or "keluaran"
        os.makedirs(out, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(os.path.abspath(out))
            else:
                messagebox.showinfo("Folder keluaran", os.path.abspath(out))
        except Exception as exc:
            messagebox.showerror("Tidak dapat membuka folder", str(exc))

    ttk.Label(root, textvariable=status_var, relief="sunken", anchor="w",
              padding=(8, 4)).pack(fill="x", side="bottom")
    root.mainloop()


if __name__ == "__main__":
    jalankan_gui()



