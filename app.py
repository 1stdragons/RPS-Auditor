"""Streamlit Auditor RPS Polsel V5 — OPSI C FINAL (pasal 11, 12, 13 .clinerules).

Alur: upload RPS asli (.docx 4.3MB) -> tempfile delete=False -> extract_text ->
safe = text[:3500] (anti-413) -> Groq openai/gpt-oss-20b max_tokens=2500 ->
create_docx_preserve_and_replace (struktur 100% sama + Lampiran C) -> tombol
Download OPSI C. Seluruh alur dibungkus try/except dengan os.unlink di finally.
"""

from __future__ import annotations

import os
import tempfile

import streamlit as st
from groq import Groq

from processor.extractor import extract_text
from processor.generator import create_docx_preserve_and_replace, create_xlsx

MODEL_GROQ = "openai/gpt-oss-20b"   # pasal 13: TPM limit 8000
BATAS_AMAN = 3500                   # pasal 13: safe = text[:3500]
MAX_TOKENS = 2500                   # pasal 13: max_tokens=2500
# pasal 13: master prompt < 2500 char (dicek di test)

# Kalimat wajib §7 — JANGAN DIUBAH.
PESAN_ANTI_GAGAL = (
    "Alat pembuat dokumen gagal pada percobaan ini, berikut isi lengkap dalam teks, "
    "dan saya akan coba terbitkan ulang file pada percobaan berikutnya."
)

MASTER = (
    "Auditor RPS Vokasi D3 Polsel. Perbaiki CPMK/Sub-CPMK: dominan Bloom C3-C6 "
    "(Menerapkan, Menganalisis, Menguji, Merancang) + konteks sawit (PKS, Blok A1, TPH, "
    "TBS, Timbangan, Sortasi Grade A/B/C, Premi). Metode: Project Based Learning + praktikum. "
    "Wajib ada: (a) Rubrik flowchart Pertemuan 6, 4 kriteria skor 0-5 — ketepatan simbol "
    "(terminator/process/decision/I/O), kelengkapan Grade/Premi, alur "
    "Blok->TPH->Truk->Timbangan PKS->Sortasi, kesesuaian aturan kasus dosen; "
    "(b) 3 kasus uji Pertemuan 15 — Normal (TBS 25 janjang), Batas (0 janjang), Tidak Valid "
    "(huruf/simbol) lengkap Expected vs Actual, Bug log, Fix, Re-test, Video edukasi 2 menit; "
    "(c) Minggu 8 UTS Praktik dan Minggu 16 UAS Project Demo; (d) bobot penilaian total 100% "
    "tanpa double counting. Akhiri dengan kalimat persis: Sumber resmi tidak berhasil "
    "diverifikasi pada percobaan ini, CPL/SKKNI ditandai sebagai usulan auditor. "
    "Format keluaran: setiap rumusan satu baris diawali 'CPMK n:' atau "
    "'Sub-CPMK n.n [Cn] - ' supaya bisa ditimpa otomatis. DILARANG mengarang identitas. "
    "Tanpa basa-basi."
)

MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

st.set_page_config(page_title="Auditor RPS Polsel V5 - OPSI C", layout="wide")
st.title("Auditor RPS Polsel V5 - OPSI C (Preserve 100% + Timpa Isi + Lampiran C)")


def ambil_api_key() -> str | None:
    """Ambil API key dari st.secrets, lalu environment variable (§10, tanpa hardcode)."""
    try:
        if "GROQ_API_KEY" in st.secrets:
            kunci = str(st.secrets["GROQ_API_KEY"]).strip()
            if kunci:
                return kunci
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY") or None


def tampilkan_hasil(hasil: dict) -> None:
    """Tampilkan tombol download + backup teks (§7) — dipanggil tiap rerun."""
    if hasil.get("docx"):
        st.success(
            "OPSI C SELESAI: struktur 100% sama persis file asli, isi CPMK sudah ditimpa "
            "hasil audit V5, dan LAMPIRAN C Log Audit Perubahan ditambahkan di belakang."
        )
        st.download_button(
            "⬇️ DOWNLOAD RPS FINAL OPSI C (Struktur Sama + Isi Baru + Lampiran)",
            data=hasil["docx"],
            file_name=f"RPS_FINAL_OPSI_C_{hasil['nama']}",
            mime=MIME_DOCX,
            type="primary",
            key="dl_opsi_c",
        )
        if hasil.get("xlsx"):
            st.download_button(
                "⬇️ DOWNLOAD LOG PERUBAHAN (Before-After)",
                data=hasil["xlsx"],
                file_name="Log_Perubahan_OPSI_C.xlsx",
                mime=MIME_XLSX,
                key="dl_log_xlsx",
            )
    else:
        st.error(PESAN_ANTI_GAGAL)

    if hasil.get("teks"):
        st.subheader("Teks hasil audit V5 — backup siap copy-paste (anti-gagal §7)")
        st.text_area("Backup", hasil["teks"], height=420, label_visibility="collapsed")


# Tampilan hasil tersimpan di session_state agar tombol download tetap ada saat rerun.
if "opsi_c" not in st.session_state:
    st.session_state["opsi_c"] = None

api_key = ambil_api_key()
if not api_key:
    api_key = st.text_input("Paste Groq API Key gsk_...", type="password").strip() or None
    if not api_key:
        st.info("Masukkan Groq API Key (gratis, tanpa billing) untuk memulai audit OPSI C.")

client = Groq(api_key=api_key, timeout=60.0) if api_key else None

up = st.file_uploader("Upload RPS Asli Polsel (docx, mis. RPS Keamanan.docx 4.3MB)", type=["docx"])

original_path = None
try:
    if up is not None:
        # Hasil lama dari file berbeda dibuang supaya tidak basi.
        if st.session_state["opsi_c"] and st.session_state["opsi_c"].get("nama") != up.name:
            st.session_state["opsi_c"] = None

        # 1. Simpan upload ke tempfile delete=False (dihapus di finally).
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(up.getvalue())
            original_path = tmp.name
        ukuran_mb = os.path.getsize(original_path) / 1024 / 1024

        # 2. Ekstraksi identitas dari dokumen sumber (§2 — dilarang mengarang).
        try:
            up.seek(0)
        except Exception:
            pass
        text, meta = extract_text(up)
        if text.startswith("Gagal ekstrak"):
            st.error(text)
        else:
            meta_tampil = {
                "Kode MK": meta.get("kode_mk") or "Sesuai dokumen sumber",
                "SKS": meta.get("sks") or "Sesuai dokumen sumber",
                "Dosen": meta.get("dosen") or "Sesuai dokumen sumber",
            }
            st.success(
                f"Terbaca {len(text)} char | File asli {ukuran_mb:.1f} MB disimpan 100% "
                f"sebagai template | Identitas: {meta_tampil}"
            )

            if st.button("Mulai Audit OPSI C (Timpa Isi + Lampiran)", type="primary"):
                if client is None:
                    st.warning("API key belum tersedia — isi Groq API Key dulu.")
                else:
                    with st.spinner(
                        "Proses belakang layar: baca struktur asli -> AI perbaiki isi -> "
                        "timpa CPMK di dalam -> tambah Lampiran C log perubahan..."
                    ):
                        # 3. Anti-413 (pasal 13): safe = text[:3500], max_tokens=2500.
                        safe = text[:BATAS_AMAN]
                        try:
                            res = (
                                client.chat.completions.create(
                                    model=MODEL_GROQ,
                                    messages=[
                                        {"role": "system", "content": MASTER},
                                        {"role": "user", "content": f"META: {meta}\nPOTONGAN:\n{safe}"},
                                    ],
                                    max_tokens=MAX_TOKENS,
                                    temperature=0.2,
                                    reasoning_effort="low",  # hemat token penalaran (pasal 13)
                                )
                                .choices[0]
                                .message.content
                                or ""
                            )
                        except Exception as e:
                            st.error(f"Panggilan Groq gagal: {e}")
                            res = ""

                        if not res.strip():
                            st.error(
                                "Model mengembalikan hasil kosong (kemungkinan token habis untuk "
                                "penalaran). Data tidak hilang — klik tombol audit lagi."
                            )

                        if res.strip():
                            try:
                                # 4. OPSI C: file asli jadi template, isi ditimpa, + lampiran.
                                docx_bio = create_docx_preserve_and_replace(original_path, res, meta)
                                xlsx_bio = create_xlsx(res)
                                st.session_state["opsi_c"] = {
                                    "docx": docx_bio.getvalue(),
                                    "xlsx": xlsx_bio.getvalue(),
                                    "teks": res,
                                    "nama": up.name,
                                }
                                st.balloons()
                            except Exception as e:
                                st.error(f"Detail galat alat dokumen: {e}")
                                st.session_state["opsi_c"] = {
                                    "docx": None,
                                    "xlsx": None,
                                    "teks": res,
                                    "nama": up.name,
                                }

    # 5. Tampilkan hasil (jalan juga pada rerun klik download).
    if st.session_state["opsi_c"]:
        tampilkan_hasil(st.session_state["opsi_c"])

except Exception as e:
    # Anti-crash final: jangan pernah memutus Streamlit karena satu kesalahan.
    st.error(f"Terjadi kesalahan tak terduga: {e}")
    st.error(PESAN_ANTI_GAGAL)
    teks_backup = (st.session_state.get("opsi_c") or {}).get("teks", "")
    if teks_backup:
        st.text_area("Backup teks (anti-gagal §7)", teks_backup, height=300, key="backup_error")

finally:
    # Selalu bersihkan tempfile, suka maupun gagal.
    if original_path and os.path.exists(original_path):
        try:
            os.unlink(original_path)
        except OSError:
            pass

