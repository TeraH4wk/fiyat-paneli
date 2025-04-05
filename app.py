from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import os
from dotenv import load_dotenv  # .env dosyasını okumak için
from datetime import datetime, timedelta



# .env dosyasını yükle
load_dotenv()

UPLOAD_KLASORU = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# Gizli bilgiler .env dosyasından geliyor
app.secret_key = os.getenv("SECRET_KEY")
KULLANICI_ADI = os.getenv("PANEL_KULLANICI")
SIFRE = os.getenv("PANEL_SIFRE")
# 🔧 Hatalı girişleri takip için
YANLIS_GIRIS_SAYISI = {}
ENGELLENEN_KULLANICILAR = {}


@app.route("/", methods=["GET"])
def index():
    if "giris" not in session:
        return redirect(url_for("login"))

    try:
        df = pd.read_excel("urunler.xlsx")

        # KDV Dahil Net Alış sütununu float’a çevir
        df["KDV Dahil Net Alış"] = df["KDV Dahil Net Alış"].replace("₺", "", regex=True).replace(",", ".", regex=True).astype(float)

        # Yeni sütunları hesapla
        df["%5 Kâr"] = (df["KDV Dahil Net Alış"] * 1.05).round(2).astype(str) + " ₺"
        df["%10 Kâr"] = (df["KDV Dahil Net Alış"] * 1.10).round(2).astype(str) + " ₺"

        veriler = df.to_dict(orient="records")

        return render_template("index.html", urunler=veriler)
    except Exception as e:
        return f"Hata oluştu: {e}"

@app.route("/login", methods=["GET", "POST"])
def login():
    kullanici_ip = request.remote_addr

    # 🔧 IP engelli mi kontrol et
    if kullanici_ip in ENGELLENEN_KULLANICILAR:
        engel_zamani = ENGELLENEN_KULLANICILAR[kullanici_ip]
        if datetime.now() < engel_zamani:
            kalan_saniye = int((engel_zamani - datetime.now()).total_seconds())
            dakika = kalan_saniye // 60
            return render_template("login.html", hata=f"Çok fazla deneme! {dakika} dakika bekleyin.")
        else:
            # 🔧 Engel süresi dolduysa sil
            del ENGELLENEN_KULLANICILAR[kullanici_ip]
            YANLIS_GIRIS_SAYISI[kullanici_ip] = 0

    if request.method == "POST":
        kullanici = request.form.get("kullanici")
        sifre = request.form.get("sifre")

        if kullanici == KULLANICI_ADI and sifre == SIFRE:
            session["giris"] = True
            YANLIS_GIRIS_SAYISI[kullanici_ip] = 0  # 🔧 Başarılı girişte sıfırla
            return redirect(url_for("index"))
        else:
            # 🔧 Hatalı girişleri say
            YANLIS_GIRIS_SAYISI[kullanici_ip] = YANLIS_GIRIS_SAYISI.get(kullanici_ip, 0) + 1

            if YANLIS_GIRIS_SAYISI[kullanici_ip] >= 5:
                ENGELLENEN_KULLANICILAR[kullanici_ip] = datetime.now() + timedelta(minutes=5)
                return render_template("login.html", hata="5 hatalı giriş! 5 dakika engellendiniz.")

            kalan = 5 - YANLIS_GIRIS_SAYISI[kullanici_ip]
            return render_template("login.html", hata=f"Hatalı giriş. {kalan} deneme hakkın kaldı.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("giris", None)
    return redirect(url_for("login"))

@app.route("/yukle", methods=["POST"])
def yukle():
    if "giris" not in session:
        return redirect(url_for("login"))

    dosya = request.files.get("dosya")
    if dosya and dosya.filename.endswith(".xlsx"):
        dosya.save(os.path.join(UPLOAD_KLASORU, "urunler.xlsx"))
        flash("✅ Dosya başarıyla yüklendi!", "success")
    else:
        flash("❌ Hatalı dosya türü. Lütfen .xlsx yükleyin.", "danger")

    return redirect(url_for("index"))

# EN SONDA OLMALI
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
