from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv
import os
import tempfile
import shutil
from datetime import datetime
import pytz
import smtplib
from email.message import EmailMessage
import traceback

from predict_pipeline import ForecastPipeline

load_dotenv()
# --- Configuration ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

# --- App Initialization ---
app = Flask(__name__, template_folder="templates")

# Ensure base folders exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_DIR = os.getenv("INPUT_DIR", "input")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
SEND_DIR = os.getenv("SEND_DIR", "send")

for folder in (INPUT_DIR, OUTPUT_DIR, SEND_DIR):
    os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)


@app.route("/", methods=["GET"])
def index():
    return render_template("dashboard.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        if "file" not in request.files or request.files["file"].filename == "":
            return jsonify(
                {"status": "error", "message": "Dosya bulunamadı veya adı boş"}
            ), 400
        file = request.files["file"]
        if not file.filename.lower().endswith(".xlsx"):
            return jsonify(
                {"status": "error", "message": "Yalnızca .xlsx dosya yükleyebilirsiniz"}
            ), 400

        email = request.form.get("email")
        if not email:
            return jsonify(
                {"status": "error", "message": "E-posta adresi gerekli"}
            ), 400

        tz = pytz.timezone("Europe/Istanbul")
        timestamp = datetime.now(tz).strftime("%d_%m_%Y_%H_%M")

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_input = os.path.join(tmpdir, "input.xlsx")
            file.save(temp_input)
            pipeline = ForecastPipeline()
            output_df = pipeline.run(temp_input, timestamp)

            msg = EmailMessage()
            msg["Subject"] = "Enerji Tahmin Sonuçlarınız"
            msg["From"] = SENDER_EMAIL
            msg["To"] = email
            msg.set_content(
                "Merhaba,\n\nEnerji tahmin sonuçlarınız ektedir.\n\nİyi çalışmalar."
            )

            output_filename = "{}_output.xlsx".format(timestamp)
            temp_output = os.path.join(tmpdir, output_filename)
            output_df.to_excel(temp_output)  # include index

            with open(temp_output, "rb") as f:
                data = f.read()
            msg.add_attachment(
                data,
                maintype="application",
                subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=output_filename,
            )

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)

            final_input = os.path.join(
                BASE_DIR, "input", "{}_input.xlsx".format(timestamp)
            )
            os.replace(temp_input, final_input)
            final_output = os.path.join(BASE_DIR, "output", output_filename)
            os.replace(temp_output, final_output)

            send_eml = os.path.join(
                BASE_DIR, "send", "{}_send_to_client.eml".format(timestamp)
            )
            with open(send_eml, "wb") as f:
                f.write(msg.as_bytes())
            send_xlsx = os.path.join(
                BASE_DIR, "send", "{}_send_to_client.xlsx".format(timestamp)
            )
            shutil.copyfile(final_output, send_xlsx)

        return jsonify(
            {"status": "ok", "message": "Sonuç iletildi, mailinizi kontrol edin"}
        ), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify(
            {
                "status": "error",
                "message": "İşlem sırasında hata oluştu: {}".format(str(e)),
            }
        ), 500


if __name__ == "__main__":
    app.run(debug=True)
