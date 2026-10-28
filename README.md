# AG Penjadwalan Kuliah (UTS)

Algoritma Genetika untuk penjadwalan kuliah Teknik Informatika (20 mata kuliah, 8 dosen, 5 ruang, 5 hari x 5 jam).
Operator AG (seleksi, crossover, mutasi, elitisme) ditulis sendiri tanpa DEAP/PyGAD.

## Instalasi
    pip install -r requirements.txt

## Menjalankan
    python ag_jadwal.py                       # 1 run (seed 1), tabel jadwal dicetak
    python ag_jadwal.py --runs 10             # 10 run seed 1..10 + ringkasan
    python ag_jadwal.py --bandingkan          # 4 kombinasi seleksi x crossover, 10 run each
    python ag_jadwal.py --seleksi roulette --crossover satu_titik --pop 150 --pm 0.1

Opsi: --pop --gen --pc --pm --elit --seleksi {roulette,turnamen} --crossover {satu_titik,uniform} --keluaran

## Keluaran (folder keluaran/)
- jadwal.xlsx, jadwal_tabel.csv (hari x jam), jadwal_daftar.csv (daftar sesi)
- jadwal_konvergensi.png (grafik fitness per generasi)
- hasil_10_run.csv, perbandingan_operator.csv

## Mengubah data
Edit bagian DATA di ag_jadwal.py (RUANG, DOSEN, MATKUL). Kapasitas ruang dan jumlah mahasiswa
saat ini adalah asumsi.
