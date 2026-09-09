import os
from PIL import Image
from pypdf import PdfReader, PdfWriter
import pymupdf as fitz

# Multiple photos ko ek PDF me jodna
def convert_multiple_images_to_pdf(image_paths: list[str], output_path: str) -> str:
    if not image_paths:
        return ""
    
    first_img = Image.open(image_paths[0]).convert("RGB")
    other_images = []
    
    for img_path in image_paths[1:]:
        img = Image.open(img_path).convert("RGB")
        other_images.append(img)
    
    first_img.save(output_path, "PDF", save_all=True, append_images=other_images)
    return output_path

# PDF ke sabhi pages ko images banana (Fast, via PyMuPDF)
def convert_pdf_to_images(input_path: str, output_dir: str) -> list[str]:
    doc = fitz.open(input_path)
    output_files = []
    
    for idx, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)
        page_path = os.path.join(output_dir, f"page_{idx + 1}.jpg")
        pix.save(page_path)
        output_files.append(page_path)
        
    doc.close()
    return output_files

# PDF ke sabhi pages ko alag-alag split karna
def split_pdf_all_pages(input_path: str, output_dir: str) -> list[str]:
    reader = PdfReader(input_path)
    output_files = []
    for idx, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        page_path = os.path.join(output_dir, f"page_{idx + 1}.pdf")
        with open(page_path, "wb") as f:
            writer.write(f)
        output_files.append(page_path)
    return output_files

# PyMuPDF (fitz) se fast aur real PDF compression
def compress_pdf_file(input_path: str, output_path: str) -> str:
    doc = fitz.open(input_path)
    # deflate=True aur garbage=4 duplicate fonts/streams ko delete karke file size chhota karta hai
    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()
    return output_path

# Multiple PDFs ko ek me jodna (Merge)
def merge_pdf_files(file_list: list[str], output_path: str) -> str:
    writer = PdfWriter()
    for file in file_list:
        reader = PdfReader(file)
        for page in reader.pages:
            writer.add_page(page)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path

# Image compression to target size
def compress_image_to_target_kb(input_path: str, output_path: str, target_kb: int = 100) -> str:
    img = Image.open(input_path).convert("RGB")
    target_bytes = target_kb * 1024
    
    max_dimension = 1600
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    low, high, best_quality = 10, 95, 50
    while low <= high:
        mid = (low + high) // 2
        img.save(output_path, "JPEG", quality=mid, optimize=True)
        size = os.path.getsize(output_path)
        if size <= target_bytes:
            best_quality = mid
            low = mid + 5
        else:
            high = mid - 5

    img.save(output_path, "JPEG", quality=best_quality, optimize=True)
    return output_path
