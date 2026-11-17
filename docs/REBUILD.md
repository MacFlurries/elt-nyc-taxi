# Cara membangun ulang (ringkas)

Rantai data: TLC parquet -> `data/raw` -> DuckDB `raw` -> `clean` -> dbt `analytics`
-> `warehouse/marts.duckdb` -> `warehouse/marts_parquet` -> `metabase_data/marts.duckdb` -> Metabase.
Semua folder data diabaikan Git. Lama proses belum terukur.

## 1. Data mentah (Airflow)
- `docker compose up -d`, buka http://localhost:8080, nyalakan DAG `download_tlc_yellow`
  (12 bulan 2025-01..2025-12, melewati file yang sudah ada).

## 2. Raw, clean, dbt
- DAG `taxi_transform` (picu manual): raw_clean -> dbt_seed -> dbt_run -> dbt_test.
- Lokal: `python scripts/local/elt.py`, lalu di `dbt_taxi/`: `dbt seed`, `dbt run`, `dbt test`.
- Seed zona (gitignored): unduh `taxi_zone_lookup.csv` dari TLC ke `dbt_taxi/seeds/`.
- Aturan clean: hapus duplikat; `trip_distance > 0` ATAU (jarak 0 dan `total_amount > 0`);
  dropoff >= pickup; bulan pickup = bulan file.

## 3. Mart untuk Metabase (jalankan urut, dari folder proyek)
1. `python scripts/local/export_marts.py` (di `.venv`) -> `warehouse/marts.duckdb`
2. `python scripts/local/export_marts_parquet.py` (di `.venv`) -> `warehouse/marts_parquet/`
3. `.venv-metabase/Scripts/python scripts/local/build_metabase_db.py` -> `metabase_data/marts.duckdb`
   (DuckDB 1.5.6; skrip menghapus .wal lama dan memanggil CHECKPOINT)
4. Metabase: `docker compose -f docker-compose.metabase.yml up -d`, lalu Admin -> Databases -> Sync.
- Peta wilayah: Admin -> Settings -> Maps, GeoJSON NYC Open Data (dataset "NYC Taxi Zones"),
  region key `locationid`, region name `zone`. Di query, ubah zone_id ke teks (`CAST(... AS VARCHAR)`).

## 4. BigQuery (sandbox)
- `export GCP_PROJECT_ID=...`; `scripts/bigquery/export_clean.py` -> `load_bq.py` -> `verify_bq.py`;
  lalu `dbt run` dan `dbt test` dengan `--target bq`. Tabel sandbox kedaluwarsa 60 hari.

## 5. Metabase: data aplikasi
- Pertanyaan dan peta tersimpan di dalam container (`/home/metabase/metabase.db.mv.db`),
  BUKAN di folder proyek. Jangan hapus container. Cadangan: `../metabase_backup` (belum teruji restore).

## 6. Asumsi analisis armada
- Utilisasi 0,7 (asumsi), durasi 1 menit s.d. 3 jam, `fare_amount > 0`.
- Hanya taksi kuning, tanpa ID kendaraan: hasil adalah estimasi kebutuhan, bukan jumlah armada nyata.

## 7. Yang sengaja dihapus (bisa dibuat ulang)
`warehouse/export` (ekspor BigQuery lama), `warehouse/marts.duckdb`, `warehouse/marts_parquet`,
`../tmp_marts_test` (percobaan). Cara membangun ulang: bagian 3 dan 4.

## 8. Jangan
- `docker system prune -a`, `docker compose down --volumes`, atau `rm -rf` tanpa memahami isinya.
