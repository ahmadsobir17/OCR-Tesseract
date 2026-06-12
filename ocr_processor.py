import os
# Limit Tesseract (OpenMP) to use a maximum of 4 threads/cores
os.environ["OMP_THREAD_LIMIT"] = "2"
os.environ["OMP_NUM_THREADS"] = "2"

import sys
import json
import time
import subprocess
import html
from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
import re

# Configuration
OUTPUT_DIR = "hasil_ocr"
TESSDATA_DIR = os.path.abspath("tessdata")

def compile_to_pdf(html_path, pdf_path, output_dir):
    if not os.path.exists(html_path):
        return
    print("\nCompiling current progress to PDF...", end="", flush=True)
    try:
        cmd = [
            "libreoffice", "--headless", 
            "--convert-to", "pdf", 
            html_path, 
            "--outdir", output_dir
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(" Done.")
        print(f"PDF saved to: {pdf_path}")
    except Exception as e:
        print(f"\nError compiling PDF: {e}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Check if tesseract is installed
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        print("\nError: Tesseract OCR is not installed on your system!")
        print("Please open your terminal and install it using this command:")
        print("  sudo apt update && sudo apt install -y tesseract-ocr tesseract-ocr-ind tesseract-ocr-ara\n")
        sys.exit(1)

    # Determine which PDF file to use
    if len(sys.argv) > 1:
        pdf_to_use = sys.argv[1]
    else:
        # Default to Jilid 02 if no argument is provided
        pdf_to_use = "Tafsir_Thabari_Jilid02.pdf"
        if not os.path.exists(pdf_to_use):
            # Fallback to Jilid 01 if 02 doesn't exist
            pdf_to_use = "Tafsir Thabari 01.pdf"
            if not os.path.exists(pdf_to_use):
                pdf_to_use = "Tafsir Thabari 01_original.pdf"
                if not os.path.exists(pdf_to_use):
                    print("Error: No Tafsir Thabari PDF found in this directory!")
                    sys.exit(1)

    # Verify file size
    size_mb = os.path.getsize(pdf_to_use) / (1024 * 1024)
    if size_mb < 10:
        print(f"Error: The file '{pdf_to_use}' is only {size_mb:.1f}MB.")
        print("OCR requires the original scanned PDF, not the lightweight text-only version.")
        sys.exit(1)

    # Construct dynamic output filenames
    base_name = os.path.splitext(os.path.basename(pdf_to_use))[0]
    output_html_path = os.path.join(OUTPUT_DIR, f"{base_name}_OCR.html")
    output_pdf_path = os.path.join(OUTPUT_DIR, f"{base_name}.pdf")
    progress_path = os.path.join(OUTPUT_DIR, f"{base_name}_progress.json")

    print(f"Using PDF file: {pdf_to_use} ({size_mb:.1f} MB)")
    print(f"Outputs will be saved to: {OUTPUT_DIR}/")
    
    try:
        reader = PdfReader(pdf_to_use)
        total_pages = len(reader.pages)
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        sys.exit(1)
        
    print(f"Total pages to process: {total_pages}")

    # Load progress
    start_page = 1
    if os.path.exists(progress_path):
        try:
            with open(progress_path, 'r') as f:
                progress = json.load(f)
                start_page = progress.get("last_page", 0) + 1
                print(f"Resuming from page {start_page}")
        except Exception as e:
            print(f"Error loading progress file: {e}. Starting from page 1.")

    if start_page > total_pages:
        print("All pages have already been processed!")
        compile_to_pdf(output_html_path, output_pdf_path, OUTPUT_DIR)
        sys.exit(0)

    # Open output file in append mode if resuming, write mode if starting fresh
    mode = "a" if start_page > 1 else "w"
    
    print("-" * 50)
    print("Starting OCR process via Local Tesseract... (Press Ctrl+C to pause/stop)")
    print("Progress will be saved, and PDF will be compiled automatically.")
    print("-" * 50)
    
    try:
        with open(output_html_path, mode, encoding="utf-8") as f_out:
            # Write HTML header if starting fresh
            if mode == "w":
                f_out.write(f"<html><head><meta charset='utf-8'><title>{base_name} OCR</title></head><body>\n")
                f_out.flush()

            for page_num in range(start_page, total_pages + 1):
                print(f"Processing page {page_num}/{total_pages}...", end="", flush=True)
                
                retries = 3
                success = False
                while retries > 0:
                    try:
                        # Convert only this specific page to image in memory at 150 DPI
                        images = convert_from_path(pdf_to_use, dpi=150, first_page=page_num, last_page=page_num)
                        if not images:
                            raise Exception("pdf2image returned empty image list")
                        img = images[0]

                        # Run local Tesseract OCR with Arabic and Indonesian language packs
                        custom_config = f'--tessdata-dir "{TESSDATA_DIR}"'
                        extracted_text = pytesseract.image_to_string(img, lang="ara+ind", config=custom_config)
                        
                        # Remove all Arabic characters (Unicode block)
                        arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+')
                        cleaned_text = arabic_pattern.sub('', extracted_text)
                        
                        # Normalize multiple newlines and spaces
                        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text).strip()
                        
                        if not cleaned_text:
                            cleaned_text = "[Halaman Kosong / Hanya Teks Arab]"
                        
                        # Escape HTML to prevent markup issues
                        escaped_text = html.escape(cleaned_text)

                        # Write structured HTML page
                        f_out.write(
                            f"<div style='page-break-after: always; font-family: \"DejaVu Sans\", \"Arial\", sans-serif; font-size: 12pt; line-height: 1.6; margin-bottom: 30px;'>\n"
                            f"  <div style='color: #888888; font-size: 10pt; border-bottom: 1px solid #eeeeee; padding-bottom: 3px; margin-bottom: 15px;'>=== HALAMAN {page_num} ===</div>\n"
                            f"  <pre style='white-space: pre-wrap; font-family: inherit; font-size: 12pt; line-height: 1.6; margin: 0; padding: 0;'>{escaped_text}</pre>\n"
                            f"</div>\n"
                        )
                        f_out.flush()

                        # Save progress
                        with open(progress_path, 'w') as f_prog:
                            json.dump({"last_page": page_num}, f_prog)

                        print(" Done.")
                        success = True
                        break
                    except Exception as e:
                        retries -= 1
                        print(f"\nError processing page {page_num} (Retries left: {retries}): {e}")
                        if retries > 0:
                            time.sleep(3)
                        else:
                            print("Failed to process page after all retries. Exiting.")
                            sys.exit(1)
                
                # Small pause to let CPU breathe
                time.sleep(0.1)

        # Close body tags if we reached the end
        with open(output_html_path, "a", encoding="utf-8") as f_out:
            f_out.write("\n</body></html>")

    except KeyboardInterrupt:
        print("\nOCR paused by user (Ctrl+C).")
        compile_to_pdf(output_html_path, output_pdf_path, OUTPUT_DIR)
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        compile_to_pdf(output_html_path, output_pdf_path, OUTPUT_DIR)
        sys.exit(1)

    # Normal completion compilation
    compile_to_pdf(output_html_path, output_pdf_path, OUTPUT_DIR)

if __name__ == "__main__":
    main()
