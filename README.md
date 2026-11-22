# BPIC17 Event Log Analyzer

Aplikasi desktop untuk menganalisis event log **BPI Challenge 2017** (BPIC17)
menggunakan Python, Tkinter, dan PM4Py. Aplikasi memuat file XES, menampilkan
ringkasan log, menjawab latihan proses mining (11.7, 11.15, 11.18, 11.22),
menjelajahi detail case, lalu mengekspor hasil ke CSV.

## Fitur

- **Impor XES** lewat PM4Py dengan validasi atribut wajib
  (`case:concept:name`, `concept:name`, `time:timestamp`), deteksi lifecycle
  dan resource, pesan error yang jelas, worker thread, dan progress bar.
- **Overview**: total case, total event, rentang waktu, rata-rata cycle time,
  frekuensi aktivitas, dan durasi per case.
- **Exercise 11.7 A-E**: jumlah case, rata-rata cycle time, successful
  (`contains O_Accepted`), unsuccessful (`contains O_Refused`), dan canceled
  (`endpoint O_Cancelled`) beserta daftar case dan bukti.
- **Exercise 11.15**: case dengan aktivitas `W_Assess potential fraud`
  berstatus `complete` minimal dua kali.
- **Exercise 11.18**: case dengan aktivitas tersebut diselesaikan minimal dua
  kali oleh resource yang sama (resource kosong tidak dihitung).
- **Exercise 11.22**: case dengan `O_Cancelled` yang muncul sebelum
  `O_Accepted` (eventually follows, posisi `i < j`) beserta persentase dan
  timeline pasangan.
- **Case Explorer**: daftar case, pencarian ID, dan rincian urutan event
  (timestamp, aktivitas, lifecycle, resource).
- **Ekspor CSV**: ringkasan jawaban, daftar case, dan tabel bukti.
- **Hitung ulang / Reset** untuk memproses ulang log atau mengosongkan hasil.
- **About**: versi Python, Tk, PM4Py, pandas, dan NumPy.

## Struktur Folder

```
bpic17-event-log-analyzer/
├── README.md
├── requirements.txt
├── pytest.ini
├── main.py                     # titik masuk: jendela utama, sidebar, tombol Hitung ulang/Reset
├── src/
│   ├── theme.py                # palet warna, font, dan style ttk
│   ├── import_panel.py         # impor XES + progress + worker
│   ├── loader.py               # pm4py.read_xes + cache .pkl
│   ├── validation.py           # validasi file dan atribut wajib
│   ├── worker.py               # background thread
│   ├── columns.py              # nama kolom standar XES
│   ├── about.py                # informasi versi dependency
│   ├── overview.py             # perhitungan overview
│   ├── overview_panel.py       # tampilan overview
│   ├── case_table_panel.py     # tabel durasi per case (panel mandiri)
│   ├── exercise_11_7.py        # logika 11.7 A-E
│   ├── exercise_11_7_panel.py  # tampilan 11.7
│   ├── rework.py               # logika 11.15 dan 11.18
│   ├── rework_panel.py         # tampilan 11.15 dan 11.18
│   ├── ex1122.py               # logika eventually follows
│   ├── ex1122_panel.py         # tampilan 11.22 + timeline
│   ├── case_explorer.py        # logika daftar case dan urutan event
│   ├── case_explorer_panel.py  # tampilan Case Explorer
│   ├── export.py               # pembuatan ringkasan dan file CSV
│   ├── export_panel.py         # panel Ekspor
│   ├── synthetic_log.py        # builder log sintetis untuk unit test
│   └── explore.py              # skrip bantu eksplorasi dataset
├── tests/
│   ├── test_overview.py
│   ├── test_exercise_11_7.py
│   ├── test_rework.py
│   ├── test_ex1122.py
│   ├── test_case_explorer.py
│   └── test_export.py
└── data/                       # tidak ikut repo (dataset besar)
```

## Prasyarat

- Python 3.11 atau lebih baru (proyek diuji dengan Python 3.14).
- Tkinter (biasanya sudah termasuk Python; di Linux perlu paket sistem).
- Dataset BPIC17 dalam format `.xes` atau `.xes.gz`. Dataset tidak disertakan
  di repository karena ukurannya besar.

Di Debian/Ubuntu, Tkinter dapat dipasang dengan:

```bash
sudo apt install python3-tk
```

## Instalasi

```bash
git clone <url-repository>
cd bpic17-event-log-analyzer

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

## Menjalankan Aplikasi

```bash
python3 main.py
```

Jalankan dari folder root proyek (folder yang sama dengan `main.py`).

Alur pemakaian:

1. **Impor** – klik `Pilih file XES`, pilih file `.xes` atau `.xes.gz`.
   Aplikasi membaca log di background thread dan menampilkan progress.
2. **Overview** – lihat total case/event, rentang waktu, dan frekuensi aktivitas.
3. **Latihan** – buka menu Exercise 11.7, 11.15, 11.18, dan 11.22 di sidebar.
   Klik baris untuk melihat bukti; klik dua kali untuk membuka case di Case
   Explorer.
4. **Case Explorer** – cari case ID dan lihat urutan event lengkap.
5. **Ekspor** – pilih folder tujuan, lalu klik `Ekspor ke folder...`.

Tombol **Hitung ulang** memproses ulang log yang sedang aktif. Tombol **Reset**
mengosongkan hasil dan kembali ke kondisi awal.

## Format Log

File harus berformat XES (`.xes` atau `.xes.gz`) dan memiliki atribut wajib:

| Atribut | Keterangan |
| --- | --- |
| `case:concept:name` | ID case |
| `concept:name` | nama aktivitas |
| `time:timestamp` | waktu event |

Atribut opsional yang dideteksi: `lifecycle:transition` dan `org:resource`.
Jika atribut wajib tidak ada atau log kosong, aplikasi menampilkan pesan error
dan tidak melanjutkan perhitungan.

Dataset BPIC17 dapat diletakkan di mana saja, misalnya:

```
data/BPI_Challenge_2017.xes.gz
```

File cache `*.pkl` dibuat di folder yang sama dengan file XES agar impor
berikutnya lebih cepat. Hapus file cache tersebut jika ingin membaca ulang XES
dari awal.

## Ekspor CSV

Panel **Ekspor** menulis lima file ke folder yang dipilih:

| File | Isi |
| --- | --- |
| `ringkasan_jawaban.csv` | Ringkasan semua latihan: kode, pertanyaan, aturan, jumlah case, denominator, persentase, mean cycle time |
| `daftar_case.csv` | Gabungan daftar case semua latihan beserta durasi dan keterangan |
| `bukti_11_15.csv` | Event `complete` yang menjadi bukti 11.15 |
| `bukti_11_18.csv` | Event `complete` per resource yang menjadi bukti 11.18 |
| `bukti_11_22.csv` | Pasangan `O_Cancelled` → `O_Accepted` beserta posisi dan waktu |

Semua CSV memakai encoding `utf-8-sig` agar karakter non-ASCII terbaca dengan
benar di Excel.

## Aturan Perhitungan

- **Cycle time** = timestamp event terakhir − timestamp event pertama pada
  seluruh event case tersebut.
- **11.7 C/D** memakai aturan *contains*: case dipilih jika memuat minimal satu
  event `O_Accepted` / `O_Refused`. Satu case tetap dihitung satu kali.
- **11.7 E** memakai aturan *endpoint*: event terakhir case harus
  `O_Cancelled`. `O_Cancelled` di tengah trace tidak dihitung.
- **11.15** hanya menghitung lifecycle `complete`; `schedule`, `start`,
  `suspend`, `resume`, `ate_abort`, dan `withdraw` diabaikan.
- **11.18** hanya menghitung `complete` oleh resource yang sama. Resource kosong
  (`NaN` atau string kosong) tidak pernah dianggap resource yang sama.
- **11.22** memakai posisi `i < j`: `O_Cancelled` harus muncul lebih dulu
  daripada `O_Accepted` pada case yang sama.
- Urutan event ditentukan oleh timestamp; jika timestamp sama, urutan baris di
  file dipakai sebagai pemutus seri.
- Nama aktivitas dicocokkan tanpa membedakan huruf besar/kecil.

## Testing

```bash
pytest
```

Konfigurasi `pytest.ini` menambahkan `src` ke `pythonpath`, sehingga test dapat
diimpor langsung. Test integrasi BPIC17 akan dilewati otomatis jika
`data/BPI_Challenge_2017.xes.gz` tidak tersedia.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'tkinter'`** – pasang paket Tkinter
  sistem (lihat bagian Prasyarat).
- **File XES gagal dibaca** – pastikan ekstensi `.xes` atau `.xes.gz` dan file
  tidak rusak.
- **Hasil lama masih muncul setelah mengganti file** – klik `Reset` lalu impor
  ulang, atau gunakan `Hitung ulang` untuk memproses ulang log aktif.
- **Impor terasa lambat pertama kali** – PM4Py membaca seluruh XES; impor
  berikutnya memakai cache `.pkl`.
