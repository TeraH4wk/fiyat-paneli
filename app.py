from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import os
from dotenv import load_dotenv  # .env dosyasını okumak için

# .env dosyasını yükle
load_dotenv()

UPLOAD_KLASORU = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# Gizli bilgiler .env dosyasından geliyor
app.secret_key = os.getenv("SECRET_KEY")
KULLANICI_ADI = os.getenv("PANEL_KULLANICI")
SIFRE = os.getenv("PANEL_SIFRE")

@app.route("/", methods=["GET"])
def index():
    if "giris" not in session:
        return redirect(url_for("login"))

    try:
        df = pd.read_excel("urunler.xlsx")
        veriler = df.to_dict(orient="records")
        return render_template("index.html", urunler=veriler)
    except Exception as e:
        return f"Hata oluştu: {e}"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        kullanici = request.form.get("kullanici")
        sifre = request.form.get("sifre")

        if kullanici == KULLANICI_ADI and sifre == SIFRE:
            session["giris"] = True
            return redirect(url_for("index"))
        else:
            return render_template("login.html", hata="Kullanıcı adı veya şifre yanlış!")
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
