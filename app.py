from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd

app = Flask(__name__)
app.secret_key = "cok_gizli_bir_anahtar"  # rastgele güçlü bir şey yazabilirsin

# Sabit kullanıcı adı/şifre
KULLANICI_ADI = "admin"
SIFRE = "1234"

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

if __name__ == "__main__":
    app.run(debug=True)
