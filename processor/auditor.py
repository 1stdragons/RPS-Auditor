"""AUDITOR RPS D3 TEKNIK INFORMATIKA POLITEKNIK ACEH SELATAN
VERSI COMPACT COMPLIANT A-S FINAL
- Mengacu Aturan Pemeriksaan dan Perbaikan RPS Compact (A-S)
- Hierarki: Profil Lulusan → CPL → CPMK → Sub-CPMK → Materi → Aktivitas → Asesmen → Bukti → SKKNI
- 12 Tahap Audit + 10 SKKNI Inti Berlaku + Matriks Antarsemester P-K-A-M + Status FIX/REVISI
- Prinsip: pertahankan yang benar, perbaiki yang lemah, tambahkan yang kurang, hapus tidak relevan
- SKKNI adalah rujukan, bukan daftar wajib - jangan memaksakan
"""

from __future__ import annotations

import re
from typing import Iterable, Dict, List, Tuple
from urllib.parse import unquote
import requests

# ===== §6 KALIMAT WAJIB - JANGAN DIUBAH =====
KALIMAT_VERIFIKASI_GAGAL = "Sumber resmi tidak berhasil diverifikasi pada percobaan ini, CPL/SKKNI ditandai sebagai usulan auditor"

# ===== C. KKO BLOOM VOKASI =====
KKO_BLOOM: dict[str, list[str]] = {
    "C1": ["menyebutkan", "mendefinisikan", "mengidentifikasi", "mengenali"],
    "C2": ["menjelaskan", "mengklasifikasikan", "menguraikan", "memahami"],
    "C3": ["menerapkan", "mengkonfigurasi", "mengamankan", "mengimplementasikan", "menggunakan"],
    "C4": ["menganalisis", "mengaudit", "membedakan", "membandingkan", "menguji"],
    "C5": ["mengevaluasi", "memvalidasi", "menilai", "mengoptimasi"],
    "C6": ["merancang", "membuat sop", "membuat dashboard", "membuat program", "membuat aplikasi", "membangun"],
}

# Kata kunci konteks sawit (§4 - khusus POLTAS)
KATA_SAWIT: tuple[str, ...] = (
    "sawit", "pks", "kebun", "blok", "tph", "tbs", "sortasi", "grade",
    "pupuk", "ton/ha", "ritase", "rendemen", "premi", "panen", "timbangan",
    "janjang",
)

# ===== J. 10 SKKNI INTI BERLAKU + 2 TAMBAHAN (HASIL RISET JDIH) =====
SKKNI_LAYERS: dict[str, dict] = {
    "PEMPROGRAMAN": {
        "prioritas": 1,
        "sk": "Kepmenaker No. 282 Tahun 2016 – Pemrograman / Software Development",
        "nomor": "282/2016",
        "status": "Berlaku",
        "bidang": "Pemrograman / Rekayasa Perangkat Lunak",
        "relevansi": "Sangat tinggi - Tulang punggung D3 TI",
        "units": [
            "J.620100.004.02 — Menggunakan Struktur Data",
            "J.620100.005.02 — Mengimplementasikan User Interface",
            "J.620100.007.01 — Mengimplementasikan Rancangan Entitas dan Keterkaitan Antar Entitas",
            "J.620100.008.01 — Merancang Arsitektur Aplikasi",
            "J.620100.009.01 — Menggunakan Spesifikasi Program",
            "J.620100.010.01 — Menerapkan Perintah Eksekusi Bahasa Pemrograman",
            "J.620100.013.01 — Menerapkan Pemecahan Permasalahan Menjadi Subrutin",
            "J.620100.014.01 — Menerapkan Metode dan Praktik Penggunaan Kembali Subrutin",
            "J.620100.016.01 — Menulis Kode dengan Prinsip Guidelines dan Best Practices",
            "J.620100.017.02 — Mengimplementasikan Pemrograman Terstruktur",
            "J.620100.018.02 — Mengimplementasikan Pemrograman Berorientasi Objek",
            "J.620100.019.02 — Menggunakan Library atau Komponen Pre-Existing",
            "J.620100.020.02 — Menggunakan SQL",
            "J.620100.021.02 — Menerapkan Akses Basis Data",
            "J.620100.022.02 — Mengimplementasikan Algoritma Pemrograman",
            "J.620100.023.02 — Membuat Dokumen Kode Program",
            "J.620100.025.02 — Melakukan Debugging",
            "J.620100.026.01 — Menggunakan Source Code Versioning",
            "J.620100.027.01 — Mengimplementasikan Network Programming",
        ],
        "mk_relevan": ["algoritma", "pemrograman terstruktur", "oop", "struktur data", "pemrograman web", "rpl", "pemrograman"],
        "jdih": "https://ppkpijakarta.com/skkni/SKKNI%202016-282.pdf",
        "catatan": "J.620100.017.02 mencakup tipe data, syntax, kontrol, I/O, percabangan, pengulangan, prosedur/fungsi, array",
        "cpl_terkait": ["CPL-2 Pengetahuan", "CPL-3 Keterampilan Umum", "CPL-4 Keterampilan Khusus"]
    },
    "JARINGAN": {
        "prioritas": 2,
        "sk": "Kepmenaker No. 321 Tahun 2016 – Jaringan Komputer",
        "nomor": "321/2016",
        "status": "Berlaku - Mencabut KEP.269/MEN/VII/2006",
        "bidang": "Jaringan Komputer - Kategori Informasi dan Komunikasi Golongan Pokok Telekomunikasi",
        "relevansi": "Sangat tinggi",
        "ditetapkan": "24 November 2016",
        "mk_relevan": ["jaringan komputer", "jaringan komputer lanjut", "administrasi jaringan", "praktikum jaringan", "teknologi jaringan"],
        "jdih": "https://jdih.kemnaker.go.id/peraturan/detail/1464/keputusan-menaker-nomor-321-tahun-2016",
        "jdih_cabut": "https://jdih.kemnaker.go.id/peraturan/detail/665/keputusan-menteri-tenaga-kerja-dan-transmigrasi-nomor-269-tahun-2006",
        "cpl_terkait": ["CPL-3", "CPL-4"]
    },
    "DATA": {
        "prioritas": 3,
        "sk": "Kepmenaker No. 268 Tahun 2020 – Data Management System / Data Management",
        "nomor": "268/2020",
        "status": "Berlaku",
        "bidang": "Data Management System - Kategori Informasi dan Komunikasi Aktivitas Pemrograman, Konsultasi Komputer dan YBDI",
        "relevansi": "Sangat tinggi - Gabung dengan 282/2016 untuk Basis Data",
        "units": [
            "J.62DMS00.006.1 — Merancang Basis Data",
            "J.62DMS00.010.1 — Membuat Basis Data",
            "J.62DMS00.011.1 — Membuat Integrasi Data",
            "J.62DMS00.012.1 — Mengelola Kualitas Data",
            "J.62DMS00.016.1 — Mengelola Dokumen dan Konten",
        ],
        "kombinasi": "282/2016 J.620100.020.02 SQL + J.620100.021.02 Akses DB + 268/2020 Merancang/Membuat DB",
        "mk_relevan": ["basis data", "sistem basis data", "administrasi basis data", "manajemen data", "data warehouse"],
        "jdih": "https://jdih.kemnaker.go.id/peraturan?hal=23&tag%5B0%5D=skkni",
        "cpl_terkait": ["CPL-3", "CPL-4", "CPL-5"]
    },
    "AI": {
        "prioritas": 4,
        "sk": "Kepmenaker No. 299 Tahun 2020 – Artificial Intelligence / Data Science",
        "nomor": "299/2020",
        "status": "Berlaku",
        "bidang": "Artificial Intelligence / Data Science",
        "relevansi": "Tinggi untuk AI, Data Science, ML",
        "mk_relevan": ["data science", "artificial intelligence", "machine learning", "analitik data", "kecerdasan buatan"],
        "jdih": "https://jdih.kemnaker.go.id/peraturan?tag%5B0%5D=skkni",
        "cpl_terkait": ["CPL-4", "CPL-5"]
    },
    "IOT": {
        "prioritas": 4,
        "sk": "Kepmenaker No. 300 Tahun 2020 – Internet of Things",
        "nomor": "300/2020",
        "status": "Berlaku",
        "bidang": "Internet of Things",
        "relevansi": "Tinggi untuk IoT, embedded",
        "mk_relevan": ["iot", "internet of things", "embedded system", "sensor", "perangkat iot"],
        "jdih": "https://jdih.kemnaker.go.id/peraturan?tag%5B0%5D=skkni",
        "cpl_terkait": ["CPL-4", "CPL-5"]
    },
    "CLOUD": {
        "prioritas": 5,
        "sk": "Kepmenaker No. 102 Tahun 2023 – Cloud Computing",
        "nomor": "102/2023",
        "status": "Berlaku - Mencabut Kepmenaker 456 Tahun 2015",
        "bidang": "Cloud Computing",
        "relevansi": "Tinggi untuk cloud/infrastruktur",
        "mk_relevan": ["cloud computing", "komputasi awan", "infrastruktur", "cloud infrastructure", "deployment"],
        "jdih": "https://jdih.kemnaker.go.id/peraturan/detail/2359/keputusan-menteri-nomor-102-tahun-2023",
        "cpl_terkait": ["CPL-4", "CPL-5"]
    },
    "PDP": {
        "prioritas": 5,
        "sk": "Kepmenaker No. 103 Tahun 2023 – Pelindungan Data Pribadi",
        "nomor": "103/2023",
        "status": "Berlaku",
        "bidang": "Pelindungan Data Pribadi",
        "relevansi": "Tinggi untuk keamanan/data/privacy",
        "mk_relevan": ["pelindungan data pribadi", "perlindungan data", "privacy", "data protection", "keamanan data pribadi"],
        "jdih": "https://jdih.kemnaker.go.id/peraturan/?hal=69",
        "cpl_terkait": ["CPL-1", "CPL-6"]
    },
    "SECURITY_UJI": {
        "prioritas": 6,
        "sk": "Kepmenaker No. 23 Tahun 2022 – Bidang Uji Keamanan Siber",
        "nomor": "23/2022",
        "status": "Berlaku",
        "bidang": "Uji Keamanan Siber",
        "relevansi": "Tinggi untuk keamanan",
        "mk_relevan": ["keamanan informasi", "keamanan jaringan", "cyber security", "uji keamanan", "keamanan siber"],
        "jdih": "https://jdih.kemnaker.go.id/peraturan/detail/2231/keputusan-menteri-ketenagakerjaan-nomor-23-tahun-2022",
        "cpl_terkait": ["CPL-4", "CPL-6"]
    },
    "SECURITY_AUDIT": {
        "prioritas": 6,
        "sk": "Kepmenaker No. 24 Tahun 2022 – Bidang Audit Keamanan Informasi",
        "nomor": "24/2022",
        "status": "Berlaku",
        "bidang": "Audit Keamanan Informasi",
        "relevansi": "Tinggi untuk audit",
        "mk_relevan": ["audit sistem informasi", "audit keamanan", "pemeriksaan keamanan", "assessment keamanan"],
        "jdih": "https://jdih.kemnaker.go.id/peraturan/detail/2231/keputusan-menteri-ketenagakerjaan-nomor-23-tahun-2022",
        "cpl_terkait": ["CPL-5", "CPL-6"]
    },
    "TANGGAP_INSIDEN": {
        "prioritas": 6,
        "sk": "Kepmenaker No. 120 Tahun 2025 – Tanggap Insiden Siber",
        "nomor": "120/2025",
        "status": "Berlaku - Terbaru 2025",
        "bidang": "Tanggap Insiden Siber - Aktivitas Pemrograman, Konsultasi Komputer dan YBDI",
        "relevansi": "Tinggi untuk incident response",
        "units": ["Identifikasi & analisis insiden", "Pengelolaan respons", "Koordinasi internal/eksternal", "Pemulihan sistem & data", "Pelaporan & dokumentasi"],
        "mk_relevan": ["tanggap insiden", "incident response", "forensik digital"],
        "jdih": "https://www.apindokabupatenbogor.com/regulasi/39/download",
        "cpl_terkait": ["CPL-4", "CPL-6"]
    },
    "ITSERVICE": {
        "prioritas": 7,
        "sk": "Kepmenaker No. 30 Tahun 2025 – Manajemen Layanan Teknologi Informasi",
        "nomor": "30/2025",
        "status": "Berlaku - Mencabut Kepmenakertrans No. 610 Tahun 2012",
        "bidang": "Manajemen Layanan TI",
        "relevansi": "Tinggi untuk IT service/helpdesk/IT management",
        "mk_relevan": ["manajemen layanan ti", "it service management", "helpdesk", "tata kelola ti", "pengelolaan layanan ti", "service operation"],
        "jdih": "https://jdih.kemnaker.go.id/peraturan/detail/2634/keputusan-menteri-ketenagakerjaan-nomor-30-tahun-2025",
        "cpl_terkait": ["CPL-5", "CPL-6"]
    },
    "DASAR": {
        "prioritas": 8,
        "sk": "Kepmenaker No. 56 Tahun 2018 – Pengoperasian Komputer",
        "nomor": "56/2018",
        "status": "Berlaku - Pendukung/dasar",
        "bidang": "Pengoperasian Komputer",
        "relevansi": "Pendukung/dasar",
        "mk_relevan": ["pengantar ti", "literasi digital", "komputer dasar", "etika profesi"],
        "jdih": "https://jdih.kemnaker.go.id/peraturan?tag%5B0%5D=skkni",
        "cpl_terkait": ["CPL-1"]
    }
}

# Mapping MK ke SKKNI - OBE: jangan memaksakan, pilih yang relevan
MAPPING_MK_SKKNI = {
    "algoritma": ["PEMPROGRAMAN"],
    "pemrograman terstruktur": ["PEMPROGRAMAN"],
    "struktur data": ["PEMPROGRAMAN"],
    "pemrograman berorientasi objek": ["PEMPROGRAMAN"],
    "oop": ["PEMPROGRAMAN"],
    "pemrograman web": ["PEMPROGRAMAN"],
    "rekayasa perangkat lunak": ["PEMPROGRAMAN"],
    "rpl": ["PEMPROGRAMAN"],
    "pemrograman": ["PEMPROGRAMAN"],
    "basis data": ["PEMPROGRAMAN", "DATA"],
    "sistem basis data": ["DATA"],
    "administrasi basis data": ["DATA"],
    "manajemen data": ["DATA"],
    "data warehouse": ["DATA"],
    "jaringan komputer": ["JARINGAN"],
    "administrasi jaringan": ["JARINGAN"],
    "jaringan komputer lanjut": ["JARINGAN"],
    "cloud": ["CLOUD"],
    "komputasi awan": ["CLOUD"],
    "keamanan informasi": ["SECURITY_UJI", "SECURITY_AUDIT", "PDP", "TANGGAP_INSIDEN"],
    "keamanan jaringan": ["SECURITY_UJI", "TANGGAP_INSIDEN", "JARINGAN"],
    "cyber security": ["SECURITY_UJI", "SECURITY_AUDIT", "TANGGAP_INSIDEN"],
    "keamanan siber": ["SECURITY_UJI", "TANGGAP_INSIDEN"],
    "audit sistem informasi": ["SECURITY_AUDIT"],
    "forensik": ["TANGGAP_INSIDEN"],
    "pelindungan data pribadi": ["PDP"],
    "perlindungan data pribadi": ["PDP"],
    "manajemen layanan ti": ["ITSERVICE"],
    "it service management": ["ITSERVICE"],
    "tata kelola ti": ["ITSERVICE", "SECURITY_AUDIT"],
    "helpdesk": ["ITSERVICE"],
    "data science": ["AI", "DATA"],
    "artificial intelligence": ["AI"],
    "machine learning": ["AI"],
    "kecerdasan buatan": ["AI"],
    "iot": ["IOT", "JARINGAN"],
    "internet of things": ["IOT"],
    "pengantar ti": ["DASAR"],
}

# L. Matriks Antarsemester P-K-A-M
MASTER_MATRIX_TEMPLATE = {
    "Algoritma":       ["P", "K", "A", "",  "",  ""],
    "Pemrograman":     ["P", "K", "A", "M", "",  ""],
    "Database":        ["P", "K", "A", "M", "A", "M"],
    "Jaringan":        ["P", "K", "A", "M", "",  ""],
    "Security":        ["",  "P", "K", "A", "M", "M"],
    "Cloud":           ["",  "",  "P", "K", "A", "M"],
    "AI/Data":         ["",  "",  "P", "K", "A", "M"],
    "Software Dev":    ["",  "P", "K", "A", "M", "M"],
    "IoT":             ["",  "",  "P", "K", "A", "M"],
    "IT Service":      ["",  "",  "",  "P", "K", "A"],
}

# ==================== TAHAP 1-12 AUDIT SESUAI ATURAN COMPACT P ====================

def tahap1_identitas(teks: str) -> dict:
    """Tahap 1 - Identitas: Nama, kode, SKS, semester, dosen, prasyarat."""
    nama = re.search(r"mata kuliah\s*:\s*(.+)", teks, re.I)
    kode = re.search(r"kode\s*:\s*([A-Z0-9]+)", teks, re.I)
    sks = re.search(r"(\d+)\s*sks", teks, re.I)
    smt = re.search(r"semester\s*[:\-]?\s*(\d)", teks, re.I)
    dosen = re.search(r"dosen\s*:\s*(.+)", teks, re.I)
    prasyarat = re.search(r"prasyarat\s*:\s*(.+)", teks, re.I)
    return {
        "nama": nama.group(1).strip() if nama else "Tidak terdeteksi",
        "kode": kode.group(1).strip() if kode else "Tidak terdeteksi",
        "sks": sks.group(1) if sks else "Tidak terdeteksi",
        "semester": int(smt.group(1)) if smt else None,
        "dosen": dosen.group(1).strip() if dosen else "Tidak terdeteksi",
        "prasyarat": prasyarat.group(1).strip() if prasyarat else "-",
        "lengkap": bool(nama and kode and sks and smt)
    }

def tahap2_posisi_mk(nama_mk: str, semester: int | None) -> dict:
    """Tahap 2 - Posisi mata kuliah dalam struktur kurikulum."""
    progression = {
        1: "Dasar - Pengenalan",
        2: "Dasar Lanjut - Pengembangan",
        3: "Keahlian - Aplikasi",
        4: "Keahlian Lanjut - Mahir",
        5: "Integrasi - Aplikasi Lanjut",
        6: "Integrasi - Mahir / TA / Magang"
    }
    return {
        "semester": semester,
        "peran": progression.get(semester, "Tidak diketahui"),
        "karakter": "Teori + Praktik (Vokasi)" if semester and semester >= 2 else "Teori Dasar"
    }

def tahap3_cpl(teks: str) -> dict:
    """Tahap 3 - CPL: 5 check sesuai aturan D."""
    cpl_found = re.findall(r"CPL[-\s]*(\d+)", teks, re.I)
    cpl_unique = list(dict.fromkeys(cpl_found))
    
    # Check 1: CPL berasal dari CPL Prodi?
    # Check 2: Relevan?
    # Check 3: Jumlah masuk akal? (D3: 2-4 CPL per MK ideal)
    jumlah = len(cpl_unique)
    jumlah_masuk_akal = 2 <= jumlah <= 4 if jumlah > 0 else False
    
    # Check 4 & 5: CPL hanya dicantumkan tapi tidak dilatih/dinilai? & CPL sama terlalu banyak?
    # Sederhana: cek apakah ada CPMK yang link ke CPL
    cpl_di_cpmk = re.findall(r"CPL[-\s]*(\d+).*?CPMK|CPMK.*?CPL[-\s]*(\d+)", teks, re.I | re.S)
    
    return {
        "cpl_tercantum": cpl_unique,
        "jumlah": jumlah,
        "jumlah_masuk_akal": jumlah_masuk_akal,
        "rekomendasi_jumlah": "Ideal 2-4 CPL per MK untuk D3" if not jumlah_masuk_akal else "Jumlah OK",
        "perlu_cek_kontribusi_nyata": True,
        "aturan": "Setiap CPL harus memiliki kontribusi nyata dalam pembelajaran dan asesmen (D)"
    }

def tahap4_cpmk(teks: str) -> dict:
    """Tahap 4 - CPMK: spesifik, dapat diamati, diukur, sesuai level, SKS, karakter, kontribusi CPL."""
    # Cari baris CPMK
    baris_cpmk = [b for b in teks.splitlines() if re.search(r"cpmk", b, re.I)]
    cpmk_text = " ".join(baris_cpmk)
    
    # Hindari CPMK buruk: "Mahasiswa memahami pemrograman"
    buruk = re.findall(r"memahami\s+(pemrograman|jaringan|basis data|keamanan)", cpmk_text, re.I)
    
    # Baik: "mampu mengimplementasikan..."
    baik_pattern = r"mampu\s+(mengimplementasikan|membuat|merancang|menganalisis|mengevaluasi|mengkonfigurasi|mengaudit)"
    baik = re.findall(baik_pattern, cpmk_text, re.I)
    
    # Kata kerja operasional
    kko_found = []
    for level, kkos in KKO_BLOOM.items():
        for kko in kkos:
            if kko in cpmk_text.lower():
                kko_found.append((level, kko))
    
    return {
        "jumlah_cpmk": len(baris_cpmk),
        "cpmk_buruk": buruk,
        "cpmk_baik_kko": baik,
        "kko_ditemukan": kko_found,
        "rekomendasi": "Ganti 'memahami' dengan 'mampu mengimplementasikan/membuat/merancang' yang dapat dibuktikan" if buruk else "CPMK sudah spesifik",
        "aturan": "CPMK harus dapat diamati, diukur, sesuai level D3"
    }

def tahap5_sub_cpmk(teks: str) -> dict:
    """Tahap 5 - Sub-CPMK: progression mengenali → menjelaskan → menerapkan → menganalisis → membuat → menguji → memperbaiki"""
    baris_sub = [b for b in teks.splitlines() if re.search(r"sub[-\s]*cpmk", b, re.I)]
    
    # Deteksi progression buruk: semua "memahami konsep"
    memahami_count = sum(1 for b in baris_sub if "memahami" in b.lower() and "konsep" in b.lower())
    total_sub = len(baris_sub)
    
    progression_buruk = memahami_count >= 3 and memahami_count == total_sub if total_sub > 0 else False
    
    # Ideal progression
    ideal = ["mengenali", "menjelaskan", "menerapkan", "menganalisis", "membuat", "menguji", "memperbaiki"]
    praktikum_ideal = ["konsep", "demonstrasi", "latihan", "implementasi", "pengujian", "troubleshooting", "produk"]
    
    bloom_sub = _bloom_dari_kko(baris_sub)
    
    return {
        "jumlah_sub_cpmk": total_sub,
        "memahami_konsep_berulang": memahami_count,
        "progression_buruk": progression_buruk,
        "bloom_sub_cpmk": bloom_sub,
        "ideal_progression": ideal,
        "ideal_praktikum": praktikum_ideal,
        "rekomendasi": "Perbaiki progression: mengenali → menjelaskan → menerapkan → menganalisis → membuat → menguji → memperbaiki" if progression_buruk else "Progression OK",
        "aturan": "Tidak boleh Minggu 1 memahami konsep, Minggu 8 memahami konsep, Minggu 14 memahami konsep tanpa peningkatan"
    }

def tahap6_materi(teks: str) -> dict:
    """Tahap 6 - Materi: relevansi, kedalaman, urutan, keterkaitan, sesuai D3, tidak pengulangan, tidak hilang."""
    # Deteksi pengulangan materi antarsemester - sederhana: cari kata SQL dasar berulang
    sql_dasar_count = len(re.findall(r"sql\s+dasar", teks, re.I))
    
    # Progression ideal: Algoritma → Pemrograman → Struktur Data → OOP → Pengembangan Aplikasi → Integrasi/Proyek
    progression_ideal = ["algoritma", "pemrograman", "struktur data", "oop", "pengembangan aplikasi", "integrasi"]
    found_progression = [p for p in progression_ideal if p in teks.lower()]
    
    return {
        "sql_dasar_berulang": sql_dasar_count,
        "progression_ideal": progression_ideal,
        "progression_ditemukan": found_progression,
        "rekomendasi": "Hindari pengulangan tanpa peningkatan level - gunakan spiral progression" if sql_dasar_count > 2 else "Materi OK",
        "aturan": "Materi harus menjawab: Apa yang harus dipelajari agar Sub-CPMK tercapai?"
    }

def tahap7_pembelajaran(teks: str) -> dict:
    """Tahap 7 - Pembelajaran: kesesuaian metode dengan karakter kompetensi."""
    metode = re.findall(r"(ceramah|diskusi|praktikum|project|pbl|studi kasus|demonstrasi)", teks, re.I)
    return {
        "metode_ditemukan": list(dict.fromkeys([m.lower() for m in metode])),
        "karakter_vokasi": any(m.lower() in ["praktikum", "project", "pbl"] for m in metode),
        "rekomendasi": "D3 harus dominan praktikum, project, PBL, bukan ceramah hafalan",
        "aturan": "Metode harus sesuai karakter kompetensi"
    }

def tahap8_praktikum(teks: str) -> dict:
    """Tahap 8 - Praktikum: D3 vokasi - apa dikerjakan, alat/software, produk, masalah, cara diuji, cara tunjuk kompetensi."""
    # Cek apakah hanya "latihan sesuai modul" (buruk)
    buruk = re.search(r"melakukan\s+latihan\s+sesuai\s+modul", teks, re.I)
    
    # Cek apakah ada produk/bukti kerja
    produk_keywords = ["program", "aplikasi", "konfigurasi", "dokumentasi", "produk", "bukti kerja", "dashboard", "sop", "laporan"]
    produk_found = [k for k in produk_keywords if k in teks.lower()]
    
    # Alat/software
    tools = re.findall(r"(vscode|mysql|xampp|packet tracer|wireshark|git|docker|aws|python|java)", teks, re.I)
    
    return {
        "praktikum_buruk": bool(buruk),
        "produk_bukti_kerja": produk_found,
        "tools_software": list(dict.fromkeys([t.lower() for t in tools])),
        "mahasiswa_menghasilkan_apa": produk_found if produk_found else "TIDAK JELAS - harus diperbaiki",
        "rekomendasi": "Harus jelas mahasiswa menghasilkan apa? (program, konfigurasi, dokumentasi, demonstrasi)" if buruk or not produk_found else "Praktikum OK - ada produk/bukti",
        "aturan": "Praktikum tidak boleh hanya 'Mahasiswa melakukan latihan sesuai modul' (H)"
    }

def tahap9_asesmen(teks: str) -> dict:
    """Tahap 9 - Asesmen: Sub-CPMK → metode → instrumen → bukti. Harus mengukur CPMK, bukan ingatan."""
    # Cek asesmen
    asesmen_keywords = ["ujian tertulis", "quiz", "tugas", "proyek", "presentasi", "demonstrasi", "praktik", "portofolio"]
    asesmen_found = [k for k in asesmen_keywords if k in teks.lower()]
    
    # Jika CPMK "mampu membuat aplikasi", asesmen tidak cukup ujian tertulis konsep
    cpmk_membuat = re.search(r"mampu\s+membuat\s+(aplikasi|program)", teks, re.I)
    asesmen_hanya_tulis = "ujian tertulis" in teks.lower() and "demonstrasi" not in teks.lower() and "proyek" not in teks.lower()
    
    return {
        "asesmen_ditemukan": asesmen_found,
        "cpmk_membuat_aplikasi": bool(cpmk_membuat),
        "hanya_ujian_tertulis": asesmen_hanya_tulis,
        "rekomendasi": "Jika CPMK membuat aplikasi, harus ada bukti program, konfigurasi, dokumentasi, demonstrasi, bukan hanya ujian tertulis" if cpmk_membuat and asesmen_hanya_tulis else "Asesmen OK",
        "aturan": "Asesmen harus Sub-CPMK → metode → instrumen → bukti (I)"
    }

def tahap10_skkni(nama_mk: str, teks: str) -> dict:
    """Tahap 10 - SKKNI: Pemetaan SKKNI relevan dan masih berlaku - JANGAN MEMAKSAKAN."""
    layers = pilih_skkni_layer(nama_mk)
    
    # Check status berlaku
    berlaku = [l for l in layers if "Berlaku" in l["status"]]
    tidak_berlaku = [l for l in layers if "Berlaku" not in l["status"]]
    
    # Check apakah memaksakan: jika MK Pengantar TI tapi dipaksa pakai SKKNI 282/2016 OOP (tidak relevan)
    memaksakan = False
    alasan_tidak_relevan = []
    if "pengantar" in nama_mk.lower() and any("282" in l["nomor"] and "OOP" in str(l.get("units", [])) for l in layers):
        memaksakan = True
        alasan_tidak_relevan.append("MK Pengantar tidak relevan dengan OOP tingkat lanjut")
    
    # Untuk setiap unit, bisa dijelaskan bagian mana pembelajaran membangun kompetensi tersebut?
    units_dipilih = []
    for layer in layers:
        for unit in layer.get("units", [])[:3]:  # ambil 3 teratas
            # Cek apakah unit tersebut bisa dijelaskan di RPS
            unit_keywords = unit.lower().split("—")[-1].strip().split()[:2]
            if any(kw in teks.lower() for kw in unit_keywords):
                units_dipilih.append({"unit": unit, "bisa_dijelaskan": True, "bagian_rps": "Ditemukan di materi/Sub-CPMK"})
            else:
                units_dipilih.append({"unit": unit, "bisa_dijelaskan": False, "bagian_rps": "Tidak ditemukan - jangan dipaksakan jika tidak relevan (B.2, K)"})
    
    return {
        "skkni_relevan": layers,
        "jumlah_layer": len(layers),
        "berlaku": berlaku,
        "tidak_berlaku": tidak_berlaku,
        "memaksakan_skkni": memaksakan,
        "alasan_tidak_relevan": alasan_tidak_relevan,
        "units_dipilih": units_dipilih,
        "prinsip": "SKKNI → kompetensi → MK → CPMK → asesmen, bukan SKKNI → copy seluruh unit → RPS (K)",
        "catatan_obe": "SKKNI adalah rujukan kompetensi kerja, bukan isi RPS. Hubungan: CPL → CPMK → Sub-CPMK → Unit SKKNI → KUK → Asesmen Praktik",
        "aturan": "Gunakan SKKNI yang masih berlaku, jangan memaksakan jika tidak relevan"
    }

def tahap11_antarsemester(nama_mk: str, semester: int | None) -> dict:
    """Tahap 11 - Antarsemester: Matriks P-K-A-M, deteksi gap/overlap."""
    # Ambil kompetensi dari nama MK
    kompetensi_key = None
    for k in MASTER_MATRIX_TEMPLATE.keys():
        if k.lower() in nama_mk.lower():
            kompetensi_key = k
            break
    
    if not kompetensi_key:
        # Cari via mapping
        for keyword, layers in MAPPING_MK_SKKNI.items():
            if keyword in nama_mk.lower():
                kompetensi_key = keyword.title()
                break
    
    matrix_row = MASTER_MATRIX_TEMPLATE.get(kompetensi_key, [""]*6) if kompetensi_key else [""]*6
    
    # Deteksi masalah
    masalah = []
    if semester and kompetensi_key:
        level = matrix_row[semester-1] if semester <= len(matrix_row) else ""
        if level == "":
            masalah.append(f"Kompetensi {kompetensi_key} tidak diajarkan di Smt {semester} menurut matriks ideal")
        if semester == 1 and level == "M":
            masalah.append(f"Kompetensi {kompetensi_key} level Mahir di Smt 1 - terlalu dini")
    
    return {
        "kompetensi": kompetensi_key or "Tidak terpetakan",
        "semester": semester,
        "level_di_semester": matrix_row[semester-1] if semester and semester <= len(matrix_row) else "Tidak diketahui",
        "matriks_row": matrix_row,
        "master_matrix": MASTER_MATRIX_TEMPLATE,
        "masalah_antarsemester": masalah,
        "keterangan": "P=Pengenalan, K=Pengembangan, A=Aplikasi, M=Mahir/Integrasi",
        "aturan": "Buat matriks untuk menemukan kompetensi tidak pernah diajarkan, muncul terlalu dini, diulang tanpa peningkatan, hanya diajarkan tidak dinilai (L)"
    }

def tahap12_editorial(teks: str) -> dict:
    """Tahap 12 - Editorial: istilah, KKO, kode CPL/CPMK konsisten, format tabel, SKS, referensi."""
    # Cek konsistensi istilah
    istilah = re.findall(r"(CPL|CPMK|Sub-CPMK|Sub CPMK|SubCPMK)", teks)
    istilah_konsisten = len(set(istilah)) <= 2 if istilah else True
    
    # Kode CPL/CPMK konsisten?
    cpl_codes = re.findall(r"CPL[-\s]*\d+", teks)
    cpmk_codes = re.findall(r"CPMK[-\s]*\d+", teks)
    
    # Typo umum
    typos = re.findall(r"(mahasisw|teoritis|pratikum)", teks, re.I)
    
    return {
        "istilah_ditemukan": list(dict.fromkeys(istilah)),
        "istilah_konsisten": istilah_konsisten,
        "cpl_codes": list(dict.fromkeys(cpl_codes)),
        "cpmk_codes": list(dict.fromkeys(cpmk_codes)),
        "typo_mungkin": typos,
        "rekomendasi": "Editorial dilakukan terakhir, bukan pertama (O). Cek konsistensi istilah, kode CPL/CPMK, format tabel, SKS",
        "aturan": "Istilah konsisten, KKO konsisten, kode CPL/CPMK konsisten, nomor pertemuan, bobot penilaian, referensi, format tabel, nama MK & SKS konsisten dengan kurikulum resmi"
    }

# ===== FUNGSI BLOOM & SAWIT (TETAP DARI LAMA) =====

def tentukan_target_bloom(teks: str) -> float:
    m = re.search(r"(?:semester|smstr|smt)\s*[:\-]?\s*(\d)", teks, re.I)
    if m and int(m.group(1)) >= 3:
        return 80.0
    return 60.0

def _bloom_dari_kko(baris: Iterable[str]) -> list[str]:
    hasil: list[str] = []
    for b in baris:
        bl = b.lower()
        for level, daftar in KKO_BLOOM.items():
            if any(k in bl for k in daftar):
                hasil.append(level)
                break
    return hasil

def hitung_bloom(teks: str) -> dict:
    label = [x.upper() for x in re.findall(r"\[\s*(C[1-6])\s*\]", teks, re.I)]
    metode = "label [C-Level]"
    if not label:
        label = _bloom_dari_kko(b for b in teks.splitlines() if re.search(r"sub-cpmk", b, re.I))
        metode = "KKO pada baris Sub-CPMK"
    if not label:
        label = _bloom_dari_kko(teks.splitlines())
        metode = "KKO seluruh teks"
    hitung = {lv: 0 for lv in KKO_BLOOM}
    for lv in label:
        hitung[lv] += 1
    total = sum(hitung.values())
    c3_c6 = sum(hitung[lv] for lv in ("C3", "C4", "C5", "C6"))
    persen = round(c3_c6 / total * 100, 1) if total else 0.0
    target = tentukan_target_bloom(teks)
    return {
        **hitung,
        "total": total,
        "c3_c6": c3_c6,
        "persen_c3_c6": persen,
        "rumus": f"{c3_c6}/{total} = {persen}%" if total else "0/0 = 0% (label Bloom tidak terdeteksi)",
        "target": target,
        "lulus_target": bool(total) and persen >= target,
        "metode": metode,
    }

def hitung_sawit(teks: str) -> dict:
    baris = [b.strip() for b in teks.splitlines() if len(b.strip()) > 3]
    ketemu: set[str] = set()
    jumlah = 0
    for b in baris:
        bl = b.lower()
        cocok = [k for k in KATA_SAWIT if k in bl]
        if cocok:
            jumlah += 1
            ketemu.update(cocok)
    total = len(baris)
    persen = round(jumlah / total * 100, 1) if total else 0.0
    return {
        "jumlah": jumlah,
        "total": total,
        "persen": persen,
        "rumus": f"{jumlah}/{total} = {persen}%" if total else "0/0 = 0%",
        "kata_ditemukan": sorted(ketemu),
        "ada_tanda_umum": "[KONTEKS UMUM" in teks,
    }

def verifikasi_duckduckgo(query: str, batas: int = 3, timeout: int = 15) -> tuple[bool, list[str]]:
    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (compatible; RPS-Auditor/5.0)"},
            timeout=timeout,
        )
        resp.raise_for_status()
        judul = re.findall(r'class="result__a"[^>]*>(.*?)</a>', resp.text, re.S)
        tautan = re.findall(r'class="result__a"[^>]*?href="([^"]+)"', resp.text)
        hasil: list[str] = []
        for idx, j in enumerate(judul[:batas]):
            bersih = re.sub(r"<[^>]+>", "", j).strip()
            url = tautan[idx] if idx < len(tautan) else ""
            m = re.search(r"uddg=([^&]+)", url)
            if m:
                url = unquote(m.group(1))
            if bersih:
                hasil.append(f"{bersih} — {url}")
        if hasil:
            return True, hasil
    except Exception:
        pass
    return False, [KALIMAT_VERIFIKASI_GAGAL]

def pilih_skkni_layer(nama_mk: str) -> list[dict]:
    nama_mk_lower = nama_mk.lower()
    layers_key = []
    for keyword, layer_names in MAPPING_MK_SKKNI.items():
        if keyword in nama_mk_lower:
            layers_key.extend(layer_names)
    if not layers_key:
        layers_key = ["PEMPROGRAMAN", "JARINGAN", "DATA"]
    layers_key = list(dict.fromkeys(layers_key))
    result = [SKKNI_LAYERS[k] for k in layers_key if k in SKKNI_LAYERS]
    result.sort(key=lambda x: x["prioritas"])
    return result

def verifikasi_sumber(mata_kuliah: str | None = None) -> dict:
    if mata_kuliah:
        layers = pilih_skkni_layer(mata_kuliah)
        kueri = {f"skkni_{l['nomor'].replace('/','_')}": f"{l['sk']} JDIH Kemnaker {l['nomor']} {l['status']}" for l in layers}
    else:
        kueri = {
            "kurikulum": "Kurikulum D3 Teknik Informatika Politeknik Aceh Selatan 2024",
            "skkni_282": "SKKNI Kepmenaker 282 2016 Pemrograman JDIH Berlaku",
            "skkni_321": "SKKNI Kepmenaker 321 2016 Jaringan Komputer JDIH Berlaku Mencabut 269 2006",
            "skkni_268": "SKKNI Kepmenaker 268 2020 Data Management System JDIH Berlaku",
            "skkni_299": "SKKNI Kepmenaker 299 2020 Artificial Intelligence Data Science JDIH Berlaku",
            "skkni_300": "SKKNI Kepmenaker 300 2020 Internet of Things JDIH Berlaku",
            "skkni_102": "SKKNI Kepmenaker 102 2023 Cloud Computing Mencabut 456 2015 JDIH Berlaku",
            "skkni_103": "SKKNI Kepmenaker 103 2023 Pelindungan Data Pribadi JDIH Berlaku",
            "skkni_23": "SKKNI Kepmenaker 23 2022 Uji Keamanan Siber JDIH Berlaku",
            "skkni_24": "SKKNI Kepmenaker 24 2022 Audit Keamanan Informasi JDIH Berlaku",
            "skkni_30": "SKKNI Kepmenaker 30 2025 Manajemen Layanan TI Mencabut 610 2012 JDIH Berlaku",
            "skkni_120": "SKKNI Kepmenaker 120 2025 Tanggap Insiden Siber JDIH Berlaku",
        }
    daftar: dict[str, dict] = {}
    for kunci, q in kueri.items():
        ok, r = verifikasi_duckduckgo(q)
        daftar[kunci] = {"kueri": q, "berhasil": ok, "hasil": r}
    return {
        **daftar,
        "pesan_gagal": KALIMAT_VERIFIKASI_GAGAL,
        "semua_gagal": not any(v["berhasil"] for v in daftar.values()),
        "kurikulum": daftar.get("kurikulum", {"berhasil": False}),
        "skkni": {"berhasil": any(v["berhasil"] for k, v in daftar.items() if "skkni" in k)},
    }

# ===== FUNGSI UTAMA SESUAI ATURAN COMPACT Q, R, S =====

def audit_lengkap_rps(teks_rps: str, nama_mk: str = "") -> dict:
    """Audit lengkap 12 tahap sesuai aturan compact P."""
    # Tahap 1-12
    identitas = tahap1_identitas(teks_rps)
    posisi = tahap2_posisi_mk(nama_mk, identitas.get("semester"))
    cpl = tahap3_cpl(teks_rps)
    cpmk = tahap4_cpmk(teks_rps)
    sub_cpmk = tahap5_sub_cpmk(teks_rps)
    materi = tahap6_materi(teks_rps)
    pembelajaran = tahap7_pembelajaran(teks_rps)
    praktikum = tahap8_praktikum(teks_rps)
    asesmen = tahap9_asesmen(teks_rps)
    skkni = tahap10_skkni(nama_mk, teks_rps)
    antarsemester = tahap11_antarsemester(nama_mk, identitas.get("semester"))
    editorial = tahap12_editorial(teks_rps)
    
    # Tambahan: Bloom & Sawit (lama)
    bloom = hitung_bloom(teks_rps)
    sawit = hitung_sawit(teks_rps)
    sumber = verifikasi_sumber(nama_mk if nama_mk else None)
    
    # Q. STATUS HASIL
    masalah_kritis = []
    if not identitas["lengkap"]:
        masalah_kritis.append("Identitas tidak lengkap")
    if not cpl["jumlah_masuk_akal"]:
        masalah_kritis.append(f"CPL {cpl['jumlah']} tidak masuk akal (ideal 2-4)")
    if cpmk["cpmk_buruk"]:
        masalah_kritis.append(f"CPMK buruk: {cpmk['cpmk_buruk']} - harus spesifik")
    if sub_cpmk["progression_buruk"]:
        masalah_kritis.append("Sub-CPMK progression buruk - semua memahami konsep")
    if praktikum["praktikum_buruk"] or praktikum["mahasiswa_menghasilkan_apa"] == "TIDAK JELAS - harus diperbaiki":
        masalah_kritis.append("Praktikum tidak jelas produk/bukti kerja")
    if asesmen["hanya_ujian_tertulis"] and asesmen["cpmk_membuat_aplikasi"]:
        masalah_kritis.append("Asesmen hanya ujian tertulis padahal CPMK membuat aplikasi")
    if skkni["memaksakan_skkni"]:
        masalah_kritis.append(f"Memaksakan SKKNI: {skkni['alasan_tidak_relevan']}")
    if not bloom["lulus_target"]:
        masalah_kritis.append(f"Bloom C3-C6 {bloom['persen_c3_c6']}% < target {bloom['target']}%")
    
    # Tentukan status Q
    if not masalah_kritis:
        status = "FIX"
        emoji = "🟢"
    elif len(masalah_kritis) <= 2:
        status = "REVISI"
        emoji = "🟡"
    elif len(masalah_kritis) <= 4:
        status = "REVISI BESAR"
        emoji = "🔴"
    else:
        status = "TUNDA" if not identitas["lengkap"] else "REVISI BESAR"
        emoji = "⚪" if status == "TUNDA" else "🔴"
    
    # S. OUTPUT AKHIR 4 KELUARAN
    # 1. Diagnosis
    diagnosis = {
        "sudah_benar": [k for k, v in {
            "Identitas lengkap": identitas["lengkap"],
            "CPL masuk akal": cpl["jumlah_masuk_akal"],
            "CPMK spesifik": not bool(cpmk["cpmk_buruk"]),
            "Sub-CPMK progression OK": not sub_cpmk["progression_buruk"],
            "Praktikum ada produk": bool(praktikum["produk_bukti_kerja"]),
            "Asesmen sesuai": not asesmen["hanya_ujian_tertulis"],
            "SKKNI tidak memaksakan": not skkni["memaksakan_skkni"],
            "Bloom lulus target": bloom["lulus_target"],
        }.items() if v],
        "bermasalah": masalah_kritis,
        "rekomendasi_prinsip": "pertahankan yang sudah benar, perbaiki yang lemah, tambahkan yang kurang, dan hapus yang tidak relevan (B.1)"
    }
    
    # 2. Matriks Alignment CPL → CPMK → Sub-CPMK → Materi → Asesmen → SKKNI
    matriks_alignment = {
        "cpl": cpl["cpl_tercantum"],
        "cpmk": f"{cpmk['jumlah_cpmk']} CPMK - KKO: {cpmk['kko_ditemukan']}",
        "sub_cpmk": f"{sub_cpmk['jumlah_sub_cpmk']} Sub-CPMK - Bloom: {sub_cpmk['bloom_sub_cpmk']}",
        "materi": materi["progression_ditemukan"],
        "pembelajaran": pembelajaran["metode_ditemukan"],
        "praktikum": praktikum["mahasiswa_menghasilkan_apa"],
        "asesmen": asesmen["asesmen_ditemukan"],
        "skkni": [f"{l['nomor']} {l['sk']} ({l['status']}) - Units: {[u.split('—')[0].strip() for u in l.get('units', [])[:2]]}" for l in skkni["skkni_relevan"]],
        "hubungan": "CPL → CPMK → Sub-CPMK → Materi → Aktivitas → Asesmen → Bukti → SKKNI (C)"
    }
    
    # 3. RPS hasil revisi (placeholder - akan diisi oleh opsi_c.py)
    # 4. Status
    
    return {
        # 12 Tahap
        "tahap1_identitas": identitas,
        "tahap2_posisi": posisi,
        "tahap3_cpl": cpl,
        "tahap4_cpmk": cpmk,
        "tahap5_sub_cpmk": sub_cpmk,
        "tahap6_materi": materi,
        "tahap7_pembelajaran": pembelajaran,
        "tahap8_praktikum": praktikum,
        "tahap9_asesmen": asesmen,
        "tahap10_skkni": skkni,
        "tahap11_antarsemester": antarsemester,
        "tahap12_editorial": editorial,
        # Tambahan lama
        "bloom": bloom,
        "sawit": sawit,
        "sumber": sumber,
        # Q & S
        "status": status,
        "emoji_status": emoji,
        "masalah_kritis": masalah_kritis,
        "diagnosis": diagnosis,
        "matriks_alignment": matriks_alignment,
        "catatan_obe": "CPL menentukan arah. CPMK menentukan kemampuan. Sub-CPMK menentukan tahapan. Materi menyediakan bekal. Praktikum membangun kemampuan. Asesmen membuktikan kemampuan. SKKNI menjadi benchmark. Keseluruhan semester membentuk progression utuh (Prinsip Terakhir)",
        "kkni_level": "D3 setara KKNI Level 5 - Lulusan mampu mengerjakan pekerjaan, bukan hanya tahu tentang pekerjaan",
        "prinsip_vokasi": "teori → penerapan → praktik → pemecahan masalah → produk/bukti kerja (N)",
    }
