from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Çevre değişkenlerini yükle
load_dotenv()

UPLOAD_KLASORU = os.path.dirname(os.path.abspath(__file__))
KULLANICI_DOSYA_YOLU = os.path.join(UPLOAD_KLASORU, "kullanicilar.json")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Yanlış girişleri izleme
YANLIS_GIRIS_SAYISI = {}
ENGELLENEN_KULLANICILAR = {}

def kullanici_dogrula(kullanici, sifre):
    with open(KULLANICI_DOSYA_YOLU, "r") as f:
        veriler = json.load(f)
    for kayit in veriler:
        if kayit["kullanici"] == kullanici and kayit["sifre"] == sifre:
            return True
    return False


@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if not (session.get("giris") and session.get("kullanici") == os.getenv("PANEL_KULLANICI")):
        return redirect(url_for("login"))

    if request.method == "POST":
        yeni_kullanici = request.form.get("yeni_kullanici")
        yeni_sifre = request.form.get("yeni_sifre")

        with open(KULLANICI_DOSYA_YOLU, "r") as f:
            veriler = json.load(f)

        veriler.append({"kullanici": yeni_kullanici, "sifre": yeni_sifre})

        with open(KULLANICI_DOSYA_YOLU, "w") as f:
            json.dump(veriler, f)

        flash("Yeni kullanıcı eklendi", "success")
        return redirect(url_for("admin_panel"))

    with open(KULLANICI_DOSYA_YOLU, "r") as f:
        kullanicilar = json.load(f)

    return render_template("admin.html", kullanicilar=kullanicilar)


@app.route("/", methods=["GET"])
def index():
    if "giris" not in session:
        return redirect(url_for("login"))

    try:
        df = pd.read_excel("urunler.xlsx")
        df["KDV Dahil Net Alış"] = df["KDV Dahil Net Alış"].replace("₺", "", regex=True).replace(",", ".", regex=True).astype(float)
        df["%5 Kâr"] = (df["KDV Dahil Net Alış"] * 1.05).round(2).astype(str) + " ₺"
        df["%10 Kâr"] = (df["KDV Dahil Net Alış"] * 1.10).round(2).astype(str) + " ₺"

        kullanici = session.get("kullanici")

        if kullanici == "konak":
            izinli_sutunlar = ["Ürün Adı", "%10 Kâr"]
            mevcut_sutunlar = [s for s in izinli_sutunlar if s in df.columns]
            df = df[mevcut_sutunlar]

        veriler = df.to_dict(orient="records")
        return render_template("index.html", urunler=veriler)

    except Exception as e:
        return f"Hata oluştu: {e}"


@app.route("/login", methods=["GET", "POST"])
def login():
    kullanici_ip = request.remote_addr

    if kullanici_ip in ENGELLENEN_KULLANICILAR:
        engel_zamani = ENGELLENEN_KULLANICILAR[kullanici_ip]
        if datetime.now() < engel_zamani:
            kalan_saniye = int((engel_zamani - datetime.now()).total_seconds())
            dakika = kalan_saniye // 60
            return render_template("login.html", hata=f"Çok fazla deneme! {dakika} dakika bekleyin.")
        else:
            del ENGELLENEN_KULLANICILAR[kullanici_ip]
            YANLIS_GIRIS_SAYISI[kullanici_ip] = 0

    if request.method == "POST":
        kullanici = request.form.get("kullanici")
        sifre = request.form.get("sifre")

        if kullanici_dogrula(kullanici, sifre):
            session["giris"] = True
            session["kullanici"] = kullanici
            YANLIS_GIRIS_SAYISI[kullanici_ip] = 0
            return redirect(url_for("index"))
        else:
            YANLIS_GIRIS_SAYISI[kullanici_ip] = YANLIS_GIRIS_SAYISI.get(kullanici_ip, 0) + 1
            if YANLIS_GIRIS_SAYISI[kullanici_ip] >= 5:
                ENGELLENEN_KULLANICILAR[kullanici_ip] = datetime.now() + timedelta(minutes=5)
                return render_template("login.html", hata="5 hatalı giriş! 5 dakika engellendiniz.")
            kalan = 5 - YANLIS_GIRIS_SAYISI[kullanici_ip]
            return render_template("login.html", hata=f"Hatalı giriş. {kalan} deneme hakkın kaldı.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/yukle", methods=["POST"])
def yukle():
    if "giris" not in session or session.get("kullanici") != os.getenv("PANEL_KULLANICI"):
        return redirect(url_for("login"))

    dosya = request.files.get("dosya")
    if dosya and dosya.filename.endswith(".xlsx"):
        dosya.save(os.path.join(UPLOAD_KLASORU, "urunler.xlsx"))
        flash("✅ Dosya başarıyla yüklendi!", "success")
    else:
        flash("❌ Hatalı dosya türü. Lütfen .xlsx yükleyin.", "danger")

    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
