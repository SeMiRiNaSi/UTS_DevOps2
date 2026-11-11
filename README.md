# 1Money

Aplikasi web pencatatan kas organisasi mahasiswa (Flask + SQLite) untuk UTS mata kuliah
**Pengembangan dan Operasi** (IF-B Pagi, Universitas Mikroskil). Aplikasi dikemas dalam container
(Docker dan Podman) dan dirilis otomatis dengan CI/CD GitHub Actions.

**Kelompok 1**

| NIM | Nama |
|---|---|
| 231112195 | Miranda Nadilla Putri |
| 231112334 | Nailah Assyifa |
| 231112918 | Rifky Ghifari Siregar |
| 231112132 | Selamet Riyadi |
| 231112945 | Silvani Chayadi |

## Fitur
- Mencatat transaksi pemasukan dan pengeluaran, menghapus transaksi, dan menampilkan saldo kas.
- Halaman **Dashboard** (`/dashboard`) yang menampilkan total pemasukan, total pengeluaran, dan saldo.
- Endpoint `/health` untuk pemeriksaan kesehatan dan endpoint JSON `/api/saldo` serta `/api/transaksi`.
- Data disimpan di SQLite (`/data/kas.db`) pada volume agar tidak hilang saat container dibuat ulang.

## Struktur proyek
```
.
├── app.py                      aplikasi Flask (route, validasi, akses SQLite)
├── templates/
│   ├── index.html              halaman utama
│   └── dashboard.html          halaman ringkasan saldo
├── tests/test_app.py           unit test pytest
├── Dockerfile                  image berbasis Red Hat UBI 9 (Python 3.11), Gunicorn, user non-root
├── compose.yaml                menjalankan aplikasi dengan Compose
├── deploy/1money.container     Quadlet Podman (service systemd)
├── .github/workflows/ci-cd.yml pipeline CI/CD
├── requirements.txt            dependensi runtime
└── requirements-dev.txt        dependensi pengujian (pytest, flake8)
```

## Jalankan lokal (tanpa container)
```bash
pip install -r requirements-dev.txt
python -m pytest
python app.py          # http://localhost:8000
```

## Jalankan dengan container
```bash
# Docker
docker build -t 1money .
docker run -d --name 1money -p 8080:8000 -v 1money-data:/data 1money

# Podman
podman build -t 1money .
podman run -d --name 1money -p 8080:8000 -v 1money-data:/data:Z 1money

# Compose
docker compose up -d --build
```
Buka http://localhost:8080 dan dashboard di http://localhost:8080/dashboard.
Pemeriksaan kesehatan: http://localhost:8080/health

## Podman Quadlet (service systemd)
Salin `deploy/1money.container` ke `~/.config/containers/systemd/`, lalu:
```bash
systemctl --user daemon-reload
systemctl --user start 1money
```
Quadlet menarik image `ghcr.io/semirinasi/uts_devops2:latest`, memakai port 8080 dan
memperbarui image otomatis (`AutoUpdate=registry`).
Gunakan satu cara saja dalam satu waktu (Docker, Podman, Compose, atau Quadlet) karena semuanya
memakai nama container `1money` dan port yang sama.

## CI/CD
Workflow: `.github/workflows/ci-cd.yml`. Berjalan saat push dan pull request ke `main`, serta manual
(`workflow_dispatch`).

| Job | Fungsi |
|---|---|
| `test` | Lint dengan flake8 dan unit test dengan pytest |
| `build` | Build image dengan Docker, smoke test container, dan build dengan Podman |
| `publish` | Mengirim image ke GHCR (`ghcr.io/semirinasi/uts_devops2`, tag `latest` dan SHA commit); hanya untuk push ke `main` |
| `deploy` | Pada self-hosted runner (label `linux`, `podman`): tarik image, jalankan ulang container dengan `--replace`, lalu health check |

Container hasil deploy CI/CD memakai `--network host`, sehingga aplikasi diakses pada
**port 8000** (`http://localhost:8000`), berbeda dengan port 8080 pada perintah container manual di atas.

## Endpoint
| Method | Path | Fungsi |
|---|---|---|
| GET | `/` | Halaman utama |
| GET | `/dashboard` | Ringkasan total pemasukan, total pengeluaran, dan saldo |
| POST | `/tambah` | Tambah transaksi |
| POST | `/hapus/<id>` | Hapus transaksi |
| GET | `/health` | Health check |
| GET | `/api/saldo` | Saldo (JSON) |
| GET | `/api/transaksi` | Daftar transaksi (JSON) |
