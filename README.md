# OCR-Tesseract

A high-performance Python script for local bilingual (Arabic + Indonesian) OCR on scanned PDF files, with built-in logic to strip out Arabic script on-the-fly and generate a clean, text-only Indonesian PDF document. 

This tool is designed to run 100% locally and for free, with robust progress saving and automatic PDF compilation using LibreOffice.

## Features

- **Indonesian-Only Output:** Uses bilingual (Arabic + Indonesian) OCR models to accurately segment the languages, then filters out all Arabic Unicode characters using Regex, leaving a clean Indonesian translation.
- **Auto-Resume:** Progress is saved page-by-page in a JSON file. If interrupted, the script will automatically resume from the last processed page.
- **Resource Control:** Automatically limits CPU core usage (defaults to a maximum of 4 cores) to keep your laptop cool and responsive during long processing runs.
- **Automatic PDF Compilation:** Compiles the formatted page-by-page text layout into a lightweight PDF file using headless LibreOffice.
- **Zero-Admin Setup:** Automatically works with local `tessdata` files without needing system-wide administrator (`sudo`) language pack installations.

## Prerequisites

Ensure you have the following system utilities installed on your Linux machine:

```bash
sudo apt update
sudo apt install -y tesseract-ocr libreoffice poppler-utils
```

- `tesseract-ocr`: The OCR engine.
- `libreoffice`: Used to compile the output HTML to PDF.
- `poppler-utils` (specifically `pdftoppm`): Used by Python to convert PDF pages to images.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/ahmadsobir17/OCR-Tesseract.git
   cd OCR-Tesseract
   ```

2. Create a virtual environment and install the Python dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install pytesseract pdf2image pillow pypdf
   ```

3. Download the required Tesseract trained language models:
   ```bash
   mkdir -p tessdata
   wget -O tessdata/ara.traineddata https://github.com/tesseract-ocr/tessdata_fast/raw/main/ara.traineddata
   wget -O tessdata/ind.traineddata https://github.com/tesseract-ocr/tessdata_fast/raw/main/ind.traineddata
   wget -O tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata
   ```

## Usage

Run the OCR processor by passing the path of the scanned PDF:

```bash
.venv/bin/python3 ocr_processor.py <path_to_pdf>
```

Example:
```bash
.venv/bin/python3 ocr_processor.py Tafsir_Thabari_Jilid02.pdf
```

### Outputs

The script creates a directory named `hasil_ocr/` containing:
- `{pdf_name}_OCR.html`: Structured HTML output with CSS page breaks.
- `{pdf_name}_OCR.pdf`: The final, compiled text-only PDF.
- `{pdf_name}_progress.json`: Progress file for auto-resume.

## License

This project is open-source and available under the [MIT License](LICENSE).
