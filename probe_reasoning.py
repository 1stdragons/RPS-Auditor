"""Probe respons gpt-oss-20b: finish_reason + reasoning_effort — dihapus setelah validasi."""

import pathlib
import re

from groq import Groq

toml = pathlib.Path(".streamlit/secrets.toml").read_text(encoding="utf-8")
key = re.search(r'GROQ_API_KEY\s*=\s*"([^"]+)"', toml).group(1)
client = Groq(api_key=key, timeout=60.0, max_retries=1)

MASTER = (
    "Auditor RPS Vokasi D3 Polsel. Perbaiki CPMK/Sub-CPMK: dominan Bloom C3-C6 "
    "+ konteks sawit (PKS, Blok A1, TPH, TBS, Timbangan, Sortasi Grade, Premi). "
    "Format keluaran: setiap rumusan satu baris diawali 'CPMK n:' atau 'Sub-CPMK n.n [Cn] - '. "
    "Akhiri dengan kalimat persis: Sumber resmi tidak berhasil diverifikasi pada percobaan ini, "
    "CPL/SKKNI ditandai sebagai usulan auditor."
)
MSGS = [
    {"role": "system", "content": MASTER},
    {"role": "user", "content": "META: {'kode_mk': 'TI 305', 'sks': '3', 'dosen': 'Ahmad Fauzi'}\nPOTONGAN:\nCPMK 1: memahami ancaman.\nSub-CPMK 1.1 enkripsi data panen."},
]


def coba(label: str, extra: dict) -> None:
    try:
        r = client.chat.completions.create(
            model="openai/gpt-oss-20b", messages=MSGS, max_tokens=2500, temperature=0.2, **extra
        )
        ch = r.choices[0]
        msg = ch.message
        alasan = getattr(msg, "reasoning_content", None) or ""
        print(
            f"{label}: finish={ch.finish_reason} len_content={len(msg.content or '')} "
            f"len_reasoning={len(alasan)}"
        )
    except Exception as e:
        print(f"{label}: ERROR {e!r}")


coba("tanpa-param       ", {})
coba("reasoning_effort=low", {"reasoning_effort": "low"})
coba("ulang tanpa-param ", {})
