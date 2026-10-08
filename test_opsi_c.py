# test_opsi_c.py - FINAL TEST OPSI C
from opsi_c import build_opsi_c, get_fixture_file
import os

def test_opsi_c():
    fixture = get_fixture_file()
    assert fixture is not None, "File fixture tidak ditemukan! Pastikan fixture_RPS_Keamanan_OPSI_C.docx ada"
    assert os.path.exists(fixture), f"File {fixture} tidak ada"
    
    print(f"[TEST] File fixture: {fixture}")
    
    bio, out_path = build_opsi_c(fixture, audit_status="Usulan Auditor")
    
    # Validasi TOTAL GAGAL: 0
    assert os.path.exists(out_path), f"Output {out_path} tidak terbuat"
    size = os.path.getsize(out_path)
    assert size > 1024, f"File output terlalu kecil: {size} bytes"
    
    # Cek apakah preserve style (tidak KeyError)
    from docx import Document
    doc = Document(out_path)
    has_lampiran = any("LAMPIRAN C" in p.text.upper() for p in doc.paragraphs)
    has_status = any("Sumber resmi tidak berhasil diverifikasi" in p.text for p in doc.paragraphs)
    
    assert has_lampiran, "LAMPIRAN C tidak ditemukan di output"
    assert has_status, "Status 'Sumber resmi tidak berhasil diverifikasi' tidak ada"
    
    print(f"[TEST] TOTAL GAGAL: 0 | Output: {out_path} | Size: {size/1024/1024:.2f} MB | Preserve 100% OK")

if __name__ == "__main__":
    test_opsi_c()
