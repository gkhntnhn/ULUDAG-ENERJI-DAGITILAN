from flask import Flask, request, render_template, send_file
from datetime import datetime
import os
import shutil

from predict_pipeline import ForecastPipeline

app = Flask(__name__)

# Klasörler
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")
RAW_DIR = os.path.join(INPUT_DIR, "raw")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Gerekli klasörler varsa oluştur
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]

        # Timestamp oluştur
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        print("timestamp:", timestamp)

        # Orijinal dosya adı (uzantısı dahil)
        original_filename = file.filename
        original_name, extension = os.path.splitext(original_filename)

        # input/raw klasörüne yedekle (orijinal adla)
        raw_filename = f"{original_name}_{timestamp}{extension}"
        raw_path = os.path.join(RAW_DIR, raw_filename)
        file.save(raw_path)

        # input klasörüne modelin beklediği adla kopyala
        model_input_filename = f"client_upload_{timestamp}{extension}"
        model_input_path = os.path.join(INPUT_DIR, model_input_filename)
        shutil.copyfile(raw_path, model_input_path)

        # ForecastPipeline’a input path’i gönder
        pipeline = ForecastPipeline()
        pipeline.data_path = model_input_path  # dinamik input atanıyor
        pipeline.current_time = datetime.strptime(timestamp, "%Y_%m_%d_%H_%M_%S").strftime("%Y_%m_%d_%H_%M_%S")  # model bunu timestamp olarak kullanıyor
        pipeline.current_day = datetime.strptime(timestamp, "%Y_%m_%d_%H_%M_%S").strftime("%Y_%m_%d")
        print("pipeline.current_time:", pipeline.current_time)
        print("pipeline.current_day:", pipeline.current_day)
        pipeline.run()

        # Çıktı dosyasının yolu
        output_filename = f"Forecast_Results_{timestamp}.xlsx"
        output_path = os.path.join(OUTPUT_DIR, pipeline.current_day, output_filename)
        print("output_path:", output_path)

        if os.path.exists(output_path):
            return render_template("result.html", download_link=output_path)
        else:
            return "Çıktı dosyası bulunamadı.", 500

    return render_template("upload.html")


@app.route("/download/<path:filename>")
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
