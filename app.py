"""1Money: aplikasi pencatatan kas organisasi (Flask + SQLite).

Dipakai sebagai studi kasus UTS Pengembangan dan Operasi (container + CI/CD).
"""
import os
import sqlite3
from datetime import date

from flask import Flask, g, jsonify, redirect, render_template, request, url_for

SKEMA = """
CREATE TABLE IF NOT EXISTS transaksi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal TEXT NOT NULL,
    jenis TEXT NOT NULL CHECK (jenis IN ('masuk', 'keluar')),
    keterangan TEXT NOT NULL,
    jumlah INTEGER NOT NULL CHECK (jumlah > 0)
);
"""

def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or os.environ.get("DB_PATH", "kas.db")
    app.config["APP_VERSION"] = os.environ.get("APP_VERSION", "dev")

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def tutup_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().executescript(SKEMA)
        get_db().commit()

    def hitung_saldo():
        row = get_db().execute(
            "SELECT COALESCE(SUM(CASE WHEN jenis='masuk' THEN jumlah ELSE -jumlah END), 0) AS saldo "
            "FROM transaksi"
        ).fetchone()
        return row["saldo"]

    @app.route("/")
    def index():
        rows = get_db().execute(
            "SELECT * FROM transaksi ORDER BY tanggal DESC, id DESC"
        ).fetchall()
        return render_template(
            "index.html",
            transaksi=rows,
            saldo=hitung_saldo(),
            hari_ini=date.today().isoformat(),
            versi=app.config["APP_VERSION"],
            error=request.args.get("error"),
        )

    @app.route("/tambah", methods=["POST"])
    def tambah():
        jenis = request.form.get("jenis", "")
        keterangan = request.form.get("keterangan", "").strip()
        tanggal = request.form.get("tanggal") or date.today().isoformat()
        try:
            jumlah = int(request.form.get("jumlah", "0"))
        except ValueError:
            jumlah = 0
        if jenis not in ("masuk", "keluar") or not keterangan or jumlah <= 0:
            return redirect(url_for("index", error="Data tidak valid"))
        db = get_db()
        db.execute(
            "INSERT INTO transaksi (tanggal, jenis, keterangan, jumlah) VALUES (?, ?, ?, ?)",
            (tanggal, jenis, keterangan, jumlah),
        )
        db.commit()
        return redirect(url_for("index"))

    @app.route("/hapus/<int:trx_id>", methods=["POST"])
    def hapus(trx_id):
        db = get_db()
        db.execute("DELETE FROM transaksi WHERE id = ?", (trx_id,))
        db.commit()
        return redirect(url_for("index"))

    @app.route("/health")
    def health():
        return jsonify(status="ok", versi=app.config["APP_VERSION"])

    @app.route("/api/saldo")
    def api_saldo():
        return jsonify(saldo=hitung_saldo())

    @app.route("/api/transaksi")
    def api_transaksi():
        rows = get_db().execute("SELECT * FROM transaksi ORDER BY id").fetchall()
        return jsonify([dict(r) for r in rows])

    # ==========================================
    # FITUR BARU: DASHBOARD RINGKASAN SALDO
    # ==========================================
    @app.route("/dashboard")
    def dashboard():
        db = get_db()
        
        # Hitung total pemasukan
        row_masuk = db.execute("SELECT COALESCE(SUM(jumlah), 0) as total FROM transaksi WHERE jenis='masuk'").fetchone()
        total_masuk = row_masuk["total"]
        
        # Hitung total pengeluaran
        row_keluar = db.execute("SELECT COALESCE(SUM(jumlah), 0) as total FROM transaksi WHERE jenis='keluar'").fetchone()
        total_keluar = row_keluar["total"]

        # Hitung saldo berdasarkan total pemasukan dikurangi total pengeluaran.
        saldo = total_masuk - total_keluar

        return render_template(
            "dashboard.html",
            masuk=total_masuk,
            keluar=total_keluar,
            saldo=saldo,
            versi=app.config["APP_VERSION"]
        )
    # ==========================================

    return app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000)