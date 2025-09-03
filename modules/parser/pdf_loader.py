import fitz  # PyMuPDF


def pdf_to_chunks(path: str, max_chars=1200, overlap=150):
    doc = fitz.open(path)
    text = "\n\n".join(page.get_text("text") for page in doc)
    chunks, i = [], 0
    while i < len(text):
        seg = text[i:i+max_chars].strip()
        if seg:
            chunks.append(seg)
        i += max_chars - overlap
    return chunks
