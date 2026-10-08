"""Validasi 14 poin RPS Final sebelum diterbitkan (§9 / Master Prompt V5 bagian I)."""

from __future__ import annotations

import re
from typing import Any

from .auditor import KALIMAT_VERIFIKASI_GAGAL
from .generator import parse_tables

# Kalimat wajib anti-gagal — JANGAN DIUBAH (§7).
PESAN_ANTI_GAGAL = "Alat pembuat dokumen gagal pada percobaan ini, berikut isi lengkap dalam teks, dan saya akan coba terbitkan ulang file pada percobaan berikutnya."

EMOJI = {"LULUS": "✅ LULUS", "PERHATIAN": "⚠️ PERHATIAN", "GAGAL": "❌ GAGAL"}


def tabel_markdown(baris: list[dict[str, Any]]) -> str:
    """Ubah daftar hasil validasi menjadi tabel markdown untuk ditampilkan."""
    kolom = ["No", "Poin", "Status", "Catatan"]
    md = ["| " + " | ".join(kolom) + " |", "|" + "---|" * len(kolom)]
    for b in baris:
        sel = [str(b.get(k, "")).replace("|", "/").replace("\n", " ") for k in kolom]
        md.append("| " + " | ".join(sel) + " |")
    return "\n".join(md)


def _cari_tabel(tables: list[dict], *ciri: str, tolak: tuple[str, ...] = ()) -> dict | None:
    """Cari tabel markdown berdasarkan kata kunci pada header (tolak = hindari kecocokan salah)."""
    for tb in tables:
        h = " ".join(tb["header"]).lower()
        if all(c in h for c in ciri) and not any(x in h for x in tolak):
            return tb
    return None


def _v1_lengkap(t: str) -> tuple[bool, str]:
    """Poin 1: kelengkapan format acuan RPS."""
    tl = t.lower()
    syarat = {
        "Cover logo placeholder": "[LOGO POLSEL" in t or "LOGO POLSEL" in t,
        "Tabel Otorisasi": "otorisasi" in tl,
        "Deskripsi": "deskripsi" in tl,
        "Tabel Bloom": "bloom" in tl,
        "CPL": re.search(r"\bCPL\b", t) is not None,
        "CPMK": re.search(r"\bCPMK\b", t) is not None,
        "Sub-CPMK": "sub-cpmk" in tl,
        "Matriks": "matriks" in tl,
        "Pustaka": "pustaka" in tl,
        "Tabel 1 (16 Pertemuan)": ("tabel 1" in tl and "pertemuan" in tl) or "16 pertemuan" in tl,
        "Tabel 2 (Penilaian)": ("tabel 2" in tl and "penilaian" in tl) or "tabel penilaian" in tl,
    }
    dapat = [k for k, v in syarat.items() if v]
    hilang = [k for k, v in syarat.items() if not v]
    catatan = f"Terpenuhi {len(dapat)}/{len(syarat)} komponen format acuan"
    if hilang:
        catatan += f"; hilang: {', '.join(hilang)}"
    return not hilang, catatan


def _v2_bloom(bloom: dict) -> tuple[bool, str]:
    """Poin 2: distribusi Bloom >= target."""
    tipe = "MK Keahlian Smt 3+" if bloom["target"] == 80 else "MK Dasar Smt 1-2"
    catatan = f"{bloom['rumus']} | target {bloom['target']:.0f}% ({tipe}) | metode: {bloom['metode']}"
    return bool(bloom["lulus_target"]), catatan


def _v3_sawit(sawit: dict) -> tuple[bool, str]:
    """Poin 3: prioritas konteks sawit (atau tanda [KONTEKS UMUM - JUSTIFIKASI])."""
    ok = sawit["persen"] > 0 or sawit["ada_tanda_umum"]
    catatan = f"{sawit['rumus']} baris mengandung konteks sawit"
    if sawit["ada_tanda_umum"]:
        catatan += " | ada tanda [KONTEKS UMUM - JUSTIFIKASI]"
    if sawit["kata_ditemukan"]:
        catatan += f" | kata: {', '.join(sawit['kata_ditemukan'][:8])}"
    return ok, catatan


def _v4_keterkaitan(t: str) -> tuple[bool, str]:
    """Poin 4: keterkaitan CPL -> CPMK -> Sub-CPMK."""
    cpl = set(re.findall(r"\bCPL\s*(\d{1,2})\b", t, re.I))
    cpmk = set(re.findall(r"\bCPMK\s*(\d{1,2})\b", t, re.I))
    sub = set(re.findall(r"Sub-CPMK\s*(\d{1,2})\s*\.\s*(\d{1,2})", t, re.I))
    induk = {s[0] for s in sub}
    cocok = induk & cpmk
    ok = bool(cpl and cpmk and sub and cocok)
    catatan = f"CPL: {len(cpl)}, CPMK: {len(cpmk)}, Sub-CPMK: {len(sub)}, induk Sub cocok CPMK: {len(cocok)}"
    if not ok:
        catatan += " | pastikan tiap Sub-CPMK merujuk CPMK dan tiap CPMK merujuk CPL"
    return ok, catatan


def _v5_indikator(t: str) -> tuple[bool, str]:
    """Poin 5: indikator terukur (bernilai numerik)."""
    baris_ind = [b for b in t.splitlines() if "indikator" in b.lower()]
    terukur = [b for b in baris_ind if re.search(r"\d", b)]
    return len(terukur) >= 3, (
        f"{len(terukur)} baris indikator bernilai numerik dari {len(baris_ind)} baris indikator (min. 3)"
    )


def _v6_16_pertemuan(tables: list[dict], t: str) -> tuple[bool, str]:
    """Poin 6: Tabel 1 memuat 16 pertemuan (Minggu 1-16)."""
    angka: set[int] = set()
    t1 = _cari_tabel(tables, "minggu") or _cari_tabel(tables, "pertemuan")
    if t1:
        for row in t1["rows"]:
            if not row:
                continue
            m = re.match(r"\s*(?:minggu\s*)?(\d{1,2})\b", row[0], re.I)
            if m and 1 <= int(m.group(1)) <= 16:
                angka.add(int(m.group(1)))
    if not angka:
        angka = {int(x) for x in re.findall(r"minggu\s*(\d{1,2})", t, re.I) if 1 <= int(x) <= 16}
    kurang = sorted(set(range(1, 17)) - angka)
    if kurang:
        return False, f"Terdeteksi {len(angka)}/16 minggu; hilang: {', '.join(str(x) for x in kurang)}"
    return True, "Terdeteksi 16/16 minggu (Tabel 1 lengkap)"


def _v7_flowchart(t: str) -> tuple[bool, str]:
    """Poin 7: rubrik Pertemuan 6 Flowchart punya 4 kriteria wajib (§5a)."""
    tl = t.lower()
    butir = {
        "1) ketepatan simbol": "simbol" in tl and any(
            k in tl for k in ("terminator", "proses", "keputusan", "i/o", "input/output")
        ),
        "2) kelengkapan Grade/Premi": "grade" in tl and "premi" in tl,
        "3) alur Blok->TPH->Truk->Timbangan->Sortasi": all(
            k in tl for k in ("blok", "tph", "truk", "sortasi")
        ) and ("timbangan" in tl or "timbang" in tl),
        "4) aturan kasus dosen": "kasus dosen" in tl or ("dosen" in tl and "kasus" in tl),
    }
    ok = all(butir.values())
    hilang = [k for k, v in butir.items() if not v]
    catatan = "Semua 4 kriteria rubrik flowchart terdeteksi" if ok else "Kurang: " + "; ".join(hilang)
    return ok, catatan


def _v8_kasus_uji(t: str) -> tuple[bool, str]:
    """Poin 8: 3 kasus uji Sub-CPMK 4.2 & Pertemuan 15 (§5b)."""
    tl = t.lower()
    butir = {
        "Normal (TBS 25 janjang)": "normal" in tl and "25" in tl and "janjang" in tl,
        "Batas (0 janjang)": "batas" in tl and re.search(r"\b0\s*janjang", tl) is not None,
        "Tidak Valid (huruf/simbol)": ("tidak valid" in tl or "invalid" in tl)
        and ("huruf" in tl or "simbol" in tl),
        "Expected vs Actual": "expected" in tl and "actual" in tl,
        "Bug log": "bug" in tl,
        "Fix & Re-test": ("fix" in tl or "perbaikan" in tl)
        and ("re-test" in tl or "retest" in tl or "uji ulang" in tl),
        "Video edukasi 2 menit": "video" in tl and re.search(r"2\s*menit", tl) is not None,
    }
    ok = all(butir.values())
    hilang = [k for k, v in butir.items() if not v]
    catatan = (
        "3 kasus uji + Expected/Actual + Bug log + Fix + Re-test + Video 2 menit lengkap"
        if ok
        else "Kurang: " + "; ".join(hilang)
    )
    return ok, catatan


def _baris_minggu(tables: list[dict], no: str, kata: tuple[str, ...]) -> bool:
    """Cek apakah baris 'no' pada Tabel 1 mengandung semua kata kunci (mis. UTS Praktik)."""
    t1 = _cari_tabel(tables, "minggu") or _cari_tabel(tables, "pertemuan")
    if not t1:
        return False
    for row in t1["rows"]:
        if row and str(row[0]).strip() == no:
            isi = " ".join(row).lower()
            return all(k in isi for k in kata)
    return False


def _v9_uts_uas(tables: list[dict], t: str) -> tuple[bool, str]:
    """Poin 9: Minggu 8 = UTS Praktik, Minggu 16 = UAS Project Demo (§5d)."""
    tl = t.lower()
    uts = "uts" in tl and "praktik" in tl and (
        re.search(r"minggu\s*(?:ke-?\s*)?8|minggu\s*viii", tl) is not None
        or _baris_minggu(tables, "8", ("uts", "praktik"))
    )
    uas = (
        "uas" in tl
        and ("project" in tl or "proyek" in tl)
        and "demo" in tl
        and (
            re.search(r"minggu\s*(?:ke-?\s*)?16|minggu\s*xvi", tl) is not None
            or _baris_minggu(tables, "16", ("uas", "demo"))
        )
    )
    kurang = []
    if not uts:
        kurang.append("Minggu 8 = UTS Praktik")
    if not uas:
        kurang.append("Minggu 16 = UAS Project Demo")
    if kurang:
        return False, "Kurang: " + "; ".join(kurang)
    return True, "Minggu 8 = UTS Praktik & Minggu 16 = UAS Project Demo terdeteksi"


def _v10_bobot(tables: list[dict]) -> tuple[bool, str]:
    """Poin 10: Tabel 2 total bobot 100% tanpa double counting (§5c)."""
    t2 = _cari_tabel(tables, "bobot", tolak=("minggu",))
    if not t2:
        return False, "Tabel penilaian (kolom Bobot) tidak terdeteksi untuk dihitung"
    idx = next((i for i, h in enumerate(t2["header"]) if "bobot" in h.lower()), None)
    if idx is None:
        return False, "Kolom Bobot tidak ditemukan pada tabel penilaian"
    total = 0.0
    for row in t2["rows"]:
        if not row:
            continue
        if re.search(r"jumlah|total", " ".join(row[:2]), re.I):
            continue  # baris jumlah tidak dihitung ganda (anti double counting)
        sel = row[idx] if idx < len(row) else ""
        m = re.search(r"(\d+(?:[.,]\d+)?)", sel)
        if m:
            total += float(m.group(1).replace(",", "."))
    ok = abs(total - 100.0) <= 0.5
    return ok, f"Total bobot terhitung = {total:g}% (syarat = 100%)"


def _v11_kebijakan_ai(t: str) -> tuple[bool, str]:
    """Poin 11: kebijakan AI (tools, batasan, disclosure, verifikasi, privasi)."""
    tl = t.lower()
    ada = any(
        k in tl
        for k in ("kebijakan ai", "kebijakan kecerdasan buatan", "etika ai", "penggunaan ai")
    )
    bukti = any(
        k in tl
        for k in (
            "disclosure", "transparan", "pengungkapan", "verifikasi",
            "tanggung jawab", "privasi", "integritas",
        )
    )
    catatan = (
        "Bagian kebijakan AI + elemen disclosure/verifikasi terdeteksi"
        if ada and bukti
        else "Kebijakan AI belum lengkap (butuh disclosure, verifikasi, tanggung jawab, privasi)"
    )
    return ada and bukti, catatan


def _v12_referensi(t: str, verif_gagal: bool) -> tuple[bool, str]:
    """Poin 12: referensi tidak dikarang (§6 — sitasi browsing atau penandaan usulan)."""
    if verif_gagal:
        return True, "Verifikasi DuckDuckGo gagal -> kalimat wajib ditampilkan & CPL/SKKNI ditandai usulan auditor"
    if KALIMAT_VERIFIKASI_GAGAL in t:
        return True, "Teks RPS memuat kalimat penandaan 'usulan auditor' sesuai §6"
    m = re.search(r"(?:daftar\s+pustaka|pustaka)\s*(?:\n|#)(.*?)(?=\n#{1,4}\s|\Z)", t, re.S | re.I)
    blok = m.group(1) if m else ""
    entri = re.findall(r"^\s*(?:\[\d+\]|\d+[.)])\s+\S", blok, re.M)
    if not entri:
        entri = re.findall(r"^\s*[-*]?\s*\S.*\((?:19|20)\d{2}\)", blok, re.M)
    ok = len(entri) >= 5
    return ok, f"{len(entri)} entri pustaka terdeteksi (min. 5)"


def _v13_identitas(t: str, meta: dict) -> tuple[bool, str]:
    """Poin 13: identitas (Kode MK/SKS/Dosen) sesuai dokumen sumber, tanpa mengarang (§2)."""
    ditemukan = {k: v for k, v in meta.items() if v}
    if not ditemukan:
        return True, "Tidak ada identitas pada sumber -> semua ditulis 'Sesuai dokumen sumber'"
    hilang: list[str] = []
    for k, v in ditemukan.items():
        if k == "kode_mk":
            def norm(s: Any) -> str:
                return re.sub(r"[\s\-.]", "", str(s)).upper()
            if norm(v) not in norm(t):
                hilang.append(str(v))
        elif k == "sks":
            if not re.search(rf"\b{re.escape(str(v))}\s*SKS\b", t, re.I):
                hilang.append(f"{v} SKS")
        elif str(v).lower() not in t.lower():
            hilang.append(str(v))
    if hilang:
        return False, "Identitas sumber tidak muncul di hasil: " + ", ".join(hilang)
    return True, "Identitas konsisten dengan sumber: " + ", ".join(str(v) for v in ditemukan.values())


def _v14_konsisten(docx_ok: bool, xlsx_ok: bool, n_tabel: int) -> tuple[bool, str]:
    """Poin 14: DOCX & XLSX konsisten — keduanya terbit dari teks hasil yang sama."""
    if docx_ok and xlsx_ok:
        return True, f"DOCX & XLSX terbit dari teks yang sama ({n_tabel} tabel terdeteksi)"
    galat = [n for n, ok in (("DOCX", docx_ok), ("XLSX", xlsx_ok)) if not ok]
    return False, f"Gagal terbit: {', '.join(galat)} — {PESAN_ANTI_GAGAL}"


def validasi_14_poin(
    result_text: str,
    meta: dict,
    bloom: dict,
    sawit: dict,
    docx_ok: bool,
    xlsx_ok: bool,
    verif_semua_gagal: bool = False,
) -> list[dict]:
    """Jalankan seluruh 14 poin validasi §9 terhadap hasil RPS Final."""
    tables = parse_tables(result_text)
    daftar = [
        (1, "Lengkap sesuai format acuan", *_v1_lengkap(result_text)),
        (2, "Bloom >= target (% C3-C6)", *_v2_bloom(bloom)),
        (3, "Prioritas konteks sawit", *_v3_sawit(sawit)),
        (4, "Keterkaitan CPL -> CPMK -> Sub-CPMK", *_v4_keterkaitan(result_text)),
        (5, "Indikator terukur", *_v5_indikator(result_text)),
        (6, "16 pertemuan", *_v6_16_pertemuan(tables, result_text)),
        (7, "Rubrik flowchart 4 kriteria", *_v7_flowchart(result_text)),
        (8, "3 kasus uji testing", *_v8_kasus_uji(result_text)),
        (9, "UTS Praktik & UAS Project Demo", *_v9_uts_uas(tables, result_text)),
        (10, "Bobot total 100%", *_v10_bobot(tables)),
        (11, "Kebijakan AI", *_v11_kebijakan_ai(result_text)),
        (12, "Referensi tidak dikarang", *_v12_referensi(result_text, verif_semua_gagal)),
        (13, "Identitas sesuai sumber", *_v13_identitas(result_text, meta)),
        (14, "DOCX & XLSX konsisten", *_v14_konsisten(docx_ok, xlsx_ok, len(tables))),
    ]
    hasil: list[dict[str, Any]] = []
    for no, poin, ok, catatan in daftar:
        if no == 14 and not ok:
            status = "GAGAL"
        else:
            status = "LULUS" if ok else "PERHATIAN"
        hasil.append({"No": no, "Poin": poin, "Status": EMOJI[status], "Catatan": catatan})
    return hasil


def ringkasan_validasi(hasil: list[dict]) -> tuple[int, int]:
    """Hitung (lulus, total) dari hasil validasi 14 poin."""
    lulus = sum(1 for h in hasil if str(h.get("Status", "")).startswith("✅"))
    return lulus, len(hasil)


