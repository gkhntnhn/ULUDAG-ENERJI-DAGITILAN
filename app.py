from flask import Flask, request, render_template, send_file#, redirect, url_for
from datetime import datetime
import os
import shutil

from predict_pipeline import ForecastPipeline

app = Flask(__name__)

# Klasör yolları
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")
RAW_DIR = os.path.join(INPUT_DIR, "raw")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Gerekli klasörler oluşturuluyor
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Yardımcı: klasörden dosya isimlerini getir
def get_file_list(folder_path, prefix=None):
    files = []
    if os.path.exists(folder_path):
        for fname in os.listdir(folder_path):
            if prefix and not fname.startswith(prefix):
                continue
            if fname.endswith(".xlsx"):
                files.append(fname)
    # Tarihe göre ters sıralama (en yeni dosya en üstte)
    files.sort(reverse=True)
    return files

@app.route("/", methods=["GET", "POST"])
def upload_file():
    error_message = None  # Default hata mesajı boş

    if request.method == "POST":
        file = request.files["file"]
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        original_filename = file.filename
        original_name, extension = os.path.splitext(original_filename)

        raw_filename = f"{original_name}_{timestamp}{extension}"
        raw_path = os.path.join(RAW_DIR, raw_filename)
        file.save(raw_path)

        model_input_filename = f"client_upload_{timestamp}{extension}"
        model_input_path = os.path.join(INPUT_DIR, model_input_filename)
        shutil.copyfile(raw_path, model_input_path)

        try:
            pipeline = ForecastPipeline()
            pipeline.data_path = model_input_path
            pipeline.current_time = datetime.strptime(timestamp, "%Y_%m_%d_%H_%M_%S").strftime("%Y_%m_%d_%H_%M_%S")
            pipeline.current_day = datetime.strptime(timestamp, "%Y_%m_%d_%H_%M_%S").strftime("%Y_%m_%d")
            pipeline.run()

        except Exception as e:
            print(f"Hata oluştu: {e}")
            if os.path.exists(model_input_path):
                os.remove(model_input_path)
            if os.path.exists(raw_path):
                os.remove(raw_path)

            # Hata mesajını template'e ilet
            error_message = f"İşlem sırasında hata oluştu: {str(e)}. Lütfen tekrar deneyiniz."

    input_files = get_file_list(INPUT_DIR, prefix="client_upload")
    today_output_folder = os.path.join(OUTPUT_DIR, datetime.now().strftime("%Y_%m_%d"))
    output_files = get_file_list(today_output_folder)

    return render_template(
        "dashboard.html",
        input_files=input_files,
        output_files=output_files,
        error_message=error_message
    )


@app.route("/download/<folder>/<filename>")
def download_file(folder, filename):
    if folder == "input":
        path = os.path.join(INPUT_DIR, filename)
    elif folder == "output":
        output_subdir = os.path.join(OUTPUT_DIR, datetime.now().strftime("%Y_%m_%d"))
        path = os.path.join(output_subdir, filename)
    else:
        return "Geçersiz klasör adı", 400

    if not os.path.exists(path):
        return "Dosya bulunamadı", 404

    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
