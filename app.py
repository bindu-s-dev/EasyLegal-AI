from click import File
from flask import Flask, render_template, request,send_file
from pdf_reader import read_pdf
from backend.ai_engine import analyze_contract
import os

app = Flask(__name__)

# Store latest analysis result
result_data = {}

# Home Page
@app.route("/")
def home():
    return render_template("index.html")


# Analyze Contract
@app.route("/analyze", methods=["POST"])
def analyze():

    global result_data

    uploaded_file = request.files["contract"]
    if uploaded_file.filename == "":
       return "No file selected."

    if not uploaded_file.filename.lower().endswith(".pdf"):
       return "Only PDF files are allowed."
    # Create uploads folder if it doesn't exist
    os.makedirs("uploads", exist_ok=True)

    file_path = os.path.join("uploads", uploaded_file.filename)

    uploaded_file.save(file_path)

    # Read PDF
    contract_text = read_pdf(file_path)

    # Analyze Contract
    result = analyze_contract(contract_text)

    # Save result
    result_data = result

    # Show Loading Page
    return render_template("loading.html")


# Final Result Page
@app.route("/result")
def result():

    global result_data

    return render_template(
        "result.html",
        result=result_data
    )

@app.route("/download-report")
def download_report():
    return send_file(
        "analysis_report.txt",
        as_attachment=True
    )
if __name__ == "__main__":
    app.run(debug=True)