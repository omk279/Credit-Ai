import re
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io

def parse_pdf_with_local_parser(pdf_stream, bank_hint="Auto-Detect"):
    """
    Analyzes a PDF page by page, using both text extraction and OCR,
    then applies a comprehensive set of regex patterns to find key data.
    """
    full_text = ""
    try:
        pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            full_text += page.get_text("text", sort=True) + "\n"
            
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                try:
                    image = Image.open(io.BytesIO(image_bytes))
                    full_text += pytesseract.image_to_string(image) + "\n"
                except Exception as e:
                    print(f"Warning: Could not process an image on page {page_num}. Error: {e}")

    except Exception as e:
        raise ValueError(f"Fatal error while processing PDF: {e}")

    data = {
        "card_provider": "Not Found",
        "total_balance": "Not Found",
        "payment_due_date": "Not Found",
        "card_last_4": "Not Found",
        "billing_period": "Not Found"
    }

    # --- Step 1: Provider Identification ---
    if bank_hint != "Auto-Detect":
        data["card_provider"] = bank_hint
    else:
        provider_keywords = {
            "ICICI Bank": [r"ICICI\s+Bank"], "HDFC Bank": [r"HDFC\s+Bank"],
            "IDFC FIRST Bank": [r"IDFC\s+FIRST\s+Bank"], "SBI": [r"SBI\s+Card", r"State\s+Bank\s+of\s+India"],
            "American Express": [r"American\s+Express", r"AMEX"],
        }
        for provider, keywords in provider_keywords.items():
            for keyword in keywords:
                if re.search(keyword, full_text, re.IGNORECASE):
                    data["card_provider"] = provider
                    break
            if data["card_provider"] != "Not Found":
                break
            
    # --- Step 2: Comprehensive Regex Library ---
    patterns = {
        "total_balance": [
            r"New\s+Balance\s*[:\s]*\$?([\d,]+\.\d{2})",
            r"Total\s+Amount\s+Due\s*[:\s]*\$?([\d,]+\.\d{2})",
            r"Total\s+amount\s+owing\s*[:\s]*\$?([\d,]+\.\d{2})",
            r"Closing\s+balance\s*[:\s]*\$?([\d,]+\.\d{2})",
        ],
        "payment_due_date": [
            r"Payment\s+Due\s+Date\s*[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})",
            r"Payment\s+due\s+by\s*[:\s]*(\d{1,2}\s+\w+\s+\d{4})",
            r"Scheduled\s+Payment\s+Due\s+Date\s*[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})",
        ],
        "card_last_4": [
            r"Account\s+Number\s*[:\s]*((?:\d{4}[\s-]?){3}\d{4})",
            r"Card\s+Number\s*[:\s]*((?:\d{4}[\s-]?){3}\d{4})",
            r"Account\s+Number\s*[:\s]*(\d{4}-\d{6}-\d{5})",
            r"Account\s+Number\s+Ending\s+In\s*[:\s]*(\d{4})",
        ],
        "billing_period": [
            r"Statement\s+Period\s*[:\s]*(\d{1,2}\s+\w+\s+\d{4}\s+-\s+\d{1,2}\s+\w+\s+\d{4})",
            r"Billing\s+period\s*(\d{2}/\d{2}/\d{2}\s+-\s+\d{2}/\d{2}/\d{2})",
            r"Opening/Closing\s+Date\s*[:\s]*(\d{1,2}/\d{1,2}/\w+\s+-\s+\d{1,2}/\d{1,2}/\w+)",
        ]
    }

    # --- Step 3: Multi-Pass Data Extraction ---
    for key, regex_list in patterns.items():
        for regex in regex_list:
            match = re.search(regex, full_text, re.IGNORECASE | re.DOTALL)
            if match:
                if key == "card_last_4":
                    cleaned_number = re.sub(r'\D', '', match.group(1))
                    if len(cleaned_number) >= 4:
                        data[key] = cleaned_number[-4:]
                else:
                    data[key] = match.group(1).strip()
                break
    
    return data