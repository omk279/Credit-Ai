from flask import current_app, request, jsonify, render_template, send_file
from .parser import parse_pdf_with_local_parser
import io
from fpdf import FPDF
# We no longer need the openpyxl library

@current_app.route('/')
def index():
    """Renders and serves the main HTML page to the browser."""
    return render_template('index.html')

@current_app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file upload, gets the bank hint, and calls the parser."""
    if 'statement' not in request.files:
        return jsonify({"error": "No file part in the request."}), 400
    
    file = request.files['statement']
    bank_hint = request.form.get('bank', 'Auto-Detect')
    
    if file.filename == '':
        return jsonify({"error": "No file selected."}), 400
        
    if file and file.filename.lower().endswith('.pdf'):
        try:
            pdf_stream = io.BytesIO(file.read())
            print(f"PDF received, sending to local parser with hint: {bank_hint}")
            
            extracted_data = parse_pdf_with_local_parser(pdf_stream, bank_hint)
            
            print("Successfully parsed data:", extracted_data)
            return jsonify(extracted_data)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400

# Updated route to generate and download a PDF report
@current_app.route('/download_pdf', methods=['POST'])
def download_pdf():
    data = request.json
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt="Credit-AI Statement Results", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    for key, value in data.items():
        label = key.replace('_', ' ').title()
        pdf.cell(60, 10, txt=f"{label}:", border=1)
        pdf.set_font("Arial", '', 12)
        pdf.cell(130, 10, txt=str(value), border=1, ln=True)
        pdf.set_font("Arial", 'B', 12)

    # Create PDF in-memory
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name='statement_results.pdf',
        mimetype='application/pdf'
    )