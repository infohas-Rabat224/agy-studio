"""
Converter script for .doc to .docx using Microsoft Word COM automation.
Run with:
  uv run --with pywin32 python convert_doc.py <input.doc> <output.docx>
"""
import sys
import os

def convert_doc_to_docx(doc_path, docx_path):
    import win32com.client
    doc_path = os.path.abspath(doc_path)
    docx_path = os.path.abspath(docx_path)
    
    if not os.path.exists(doc_path):
        raise FileNotFoundError(f"Input file not found: {doc_path}")
        
    os.makedirs(os.path.dirname(docx_path), exist_ok=True)
    
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(doc_path)
        doc.SaveAs2(docx_path, 16) # 16 = wdFormatXMLDocument (.docx)
        doc.Close()
        print(f"[OK] Converted {doc_path} -> {docx_path}")
    finally:
        try:
            word.Quit()
        except Exception:
            pass

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: convert_doc.py <input.doc> <output.docx>")
        sys.exit(1)
    convert_doc_to_docx(sys.argv[1], sys.argv[2])
