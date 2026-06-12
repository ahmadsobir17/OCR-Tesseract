import os
import re
import html
import subprocess

INPUT_HTML = "hasil_ocr/Tafsir Thabari 01_OCR.html"
OUTPUT_HTML = "hasil_ocr/Tafsir Thabari 01_OCR_clean.html"
OUTPUT_PDF = "hasil_ocr/Tafsir Thabari 01_OCR.pdf" # Overwrite the mixed one

def clean_html():
    print("Reading mixed HTML file...")
    with open(INPUT_HTML, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by the page wrapper div
    # Each page starts with: <div style='page-break-after: always;
    page_marker = "<div style='page-break-after: always;"
    parts = content.split(page_marker)
    
    header = parts[0] # HTML head and opening body
    pages_data = parts[1:]
    
    print(f"Total raw page blocks found: {len(pages_data)}")
    
    # Dictionary to store the best version of each page
    # Key: page number (int), Value: clean HTML block (str)
    cleaned_pages = {}
    
    # Arabic regex
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+')
    
    for part in pages_data:
        # Find the page number
        match = re.search(r'=== HALAMAN (\d+) ===', part)
        if not match:
            continue
        page_num = int(match.group(1))
        
        # Clean the block by stripping out any Arabic characters
        # This guarantees that even if we process a block that had Arabic, the Arabic is removed
        # Reconstruct the div block
        full_block = page_marker + part
        
        # Remove Arabic characters from this block
        cleaned_block = arabic_pattern.sub('', full_block)
        
        # Clean up multiple newlines inside the pre tag of this block
        # Find the text between <pre ...> and </pre>
        pre_match = re.search(r'(<pre[^>]*>)(.*?)(</pre>)', cleaned_block, re.DOTALL)
        if pre_match:
            pre_start = pre_match.group(1)
            pre_content = pre_match.group(2)
            pre_end = pre_match.group(3)
            
            # Normalize consecutive newlines
            clean_pre_content = re.sub(r'\n\s*\n', '\n\n', pre_content).strip()
            if not clean_pre_content:
                clean_pre_content = "[Halaman Kosong / Hanya Teks Arab]"
                
            cleaned_block = cleaned_block.replace(
                pre_match.group(0),
                f"{pre_start}{clean_pre_content}{pre_end}"
            )
            
        # We prefer versions that are already clean (had less Arabic to begin with)
        # or we just store it. If we already have a version for this page, we can compare.
        # But since we strip Arabic from all versions, they will be very similar.
        # We can prefer the version that is longer (more Indonesian text captured)
        if page_num not in cleaned_pages:
            cleaned_pages[page_num] = cleaned_block
        else:
            # If we already have it, keep the one that has more Indonesian characters (length of block)
            if len(cleaned_block) > len(cleaned_pages[page_num]):
                cleaned_pages[page_num] = cleaned_block

    print(f"Unique page numbers extracted: {len(cleaned_pages)}")
    
    # Sort and write the clean pages in order from page 1 to the max page
    max_page = max(cleaned_pages.keys()) if cleaned_pages else 0
    print(f"Max page number: {max_page}")
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f_out:
        # Write clean header
        if "<html>" not in header:
            f_out.write("<html><head><meta charset='utf-8'><title>Tafsir Thabari OCR</title></head><body>\n")
        else:
            f_out.write(header)
            
        # Write pages in sequential order
        for p in range(1, max_page + 1):
            if p in cleaned_pages:
                f_out.write(cleaned_pages[p])
                if not cleaned_pages[p].endswith("\n"):
                    f_out.write("\n")
            else:
                # Placeholder for missing pages (should not happen, but just in case)
                f_out.write(
                    f"<div style='page-break-after: always; font-family: \"DejaVu Sans\", \"Arial\", sans-serif; font-size: 12pt; line-height: 1.6; margin-bottom: 30px;'>\n"
                    f"  <div style='color: #888888; font-size: 10pt; border-bottom: 1px solid #eeeeee; padding-bottom: 3px; margin-bottom: 15px;'>=== HALAMAN {p} ===</div>\n"
                    f"  <pre style='white-space: pre-wrap; font-family: inherit; font-size: 12pt; line-height: 1.6; margin: 0; padding: 0;'>[Halaman Hilang / Tidak Terproses]</pre>\n"
                    f"</div>\n"
                )
                
        f_out.write("\n</body></html>")
        
    print(f"Cleaned HTML file saved to: {OUTPUT_HTML}")
    
    # Compile to PDF using LibreOffice
    print("Compiling clean PDF...")
    try:
        cmd = [
            "libreoffice", "--headless", 
            "--convert-to", "pdf", 
            OUTPUT_HTML, 
            "--outdir", "hasil_ocr"
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Rename output PDF to the standard name
        clean_pdf_path = OUTPUT_HTML.replace(".html", ".pdf")
        if os.path.exists(clean_pdf_path):
            if os.path.exists(OUTPUT_PDF):
                os.remove(OUTPUT_PDF)
            os.rename(clean_pdf_path, OUTPUT_PDF)
            print(f"Successfully compiled clean PDF: {OUTPUT_PDF}")
            
            # Print page count of clean PDF
            pdfinfo_cmd = ["pdfinfo", OUTPUT_PDF]
            res = subprocess.run(pdfinfo_cmd, capture_output=True, text=True)
            for line in res.stdout.split("\n"):
                if line.startswith("Pages:"):
                    print(line)
        else:
            print("Error: Compiled PDF not found!")
    except Exception as e:
        print(f"Error compiling clean PDF: {e}")

if __name__ == "__main__":
    clean_html()
