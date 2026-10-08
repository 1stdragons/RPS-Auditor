# RPS-Auditor V6 - STRUCTURE - POLTAS - MEMORY

**Project:** RPS-Auditor-fardianpoltas
**Version:** V6 FINAL FIX - POLTAS
**Owner:** FardianSyah @fardianpoltas - D3 TI Poltas

## Explorer (dari screenshot Bos)
```
RPS-Auditor-fardianpoltas/
├── .streamlit/
│   └── secrets.toml
├── docs/
│   ├── index.html (V6 - 23 AKTIF + 15 DICABUT + BLOOM + SAWIT)
│   ├── config_prompt_v6.txt
│   └── panduan/ (18 file PDF + JSON)
│       ├── SKKNI 2005-094.pdf.pdf (DIGANTI 56/2018)
│       ├── SKKNI 2005-142_.pdf.pdf (DIGANTI 282/2016)
│       ├── SKKNI 2006-269.pdf.pdf (DIGANTI 321/2016)
│       ├── SKKNI 2006-272.pdf.pdf (DIGANTI 285/2016)
│       ├── SKKNI 2007-115.pdf.pdf (DIGANTI 107/2018)
│       ├── SKKNI 2008-114.pdf.pdf (DIGANTI 140/2019)
│       ├── SKKNI 2010-142.pdf.pdf
│       ├── SKKNI 2011-273.pdf.pdf
│       ├── SKKNI 2012-610.pdf.pdf (DICABUT 2025-030 -> 30/2025)
│       ├── SKKNI 2012-615.pdf.pdf (DICABUT -> 282/2016)
│       ├── SKKNI 2012-717.pdf.pdf (DIGANTI 101/2018)
│       ├── SKKNI 2014-118.pdf.pdf
│       ├── SKKNI 2014-165.pdf.pdf
│       ├── SKKNI 2014-352.pdf.pdf
│       ├── SKKNI 2014-400.pdf.pdf (DICABUT 2020-173)
│       ├── SKKNI 2014-419.pdf.pdf (DICABUT 2019-030)
│       ├── SKKNI 2014-424.pdf.pdf (DICABUT 2019-029)
│       ├── SKKNI 2015-045.pdf.pdf (Pengelolaan Pusat Data BERLAKU)
│       ├── SKKNI 2015-055.pdf.pdf (DICABUT 2024-191 -> 191/2024)
│       └── INDEX_SKKNI_LENGKAP_2026.json (135 IT)
├── panduan/ (source)
│   ├── INDEX_10_SKKNI_BERLAKU.json (23 kritis)
│   ├── INDEX_SKKNI_LENGKAP_2026.json (135 IT)
│   ├── PENCABUTAN_MAP.json + LENGKAP (27 entries)
│   ├── Mapping_MK_SKKNI_D3_TI.json
│   └── *.md (10 SKKNI)
├── processor/
│   ├── __init__.py
│   ├── auditor.py (KALIMAT_VERIFIKASI_GAGAL='' - portal dihilangkan)
│   ├── extractor.py
│   ├── generator.py (REAL DOCX + XLSX 4 sheet + Log DICABUT)
│   ├── validator.py (14 poin + Bloom + Sawit + DICABUT check)
│   └── __pycache__/
├── app.py (V6 FINAL FIX - 22 SKKNI VERIFIED + BLOOM + SAWIT - POLTAS)
├── config_prompt.txt (U = V6 content)
├── config_prompt_v6.txt (MASTER PROMPT V6 FINAL)
├── fixture_RPS_Keamanan_OPSI_C.docx (4 RPS contoh)
├── opsi_c.py, probe_reasoning.py, test_opsi_c.py
├── requirements.txt
├── skkni-2026-10-08.xlsx (1240 baris - sumber utama)
└── MEMORY_PROJECT_STRUCTURE_V6_POLTAS.json (file ini)
```

## BANK SKKNI V6

### 23 AKTIF [BERLAKU]

- 285/2016 Computer Technical Support Mencabut 2006-272 [BERLAKU]
- 282/2016 Software Development Mencabut 2012-615 dan 2006-142 [BERLAKU]
- 321/2016 Jaringan Komputer Mencabut 2006-269 [BERLAKU]
- 56/2018 Pengoperasian Komputer Mencabut 2005-094 [BERLAKU]
- 107/2018 Multimedia Mencabut 2007-115 [BERLAKU]
- 101/2018 Instalasi Fiber Optik Mencabut 2012-717 [BERLAKU]
- 27/2019 Programming and Software Development [BERLAKU]
- 90/2015 Enterprise Architecture Design [BERLAKU]
- 45/2015 Pengelolaan Pusat Data [BERLAKU]
- 191/2024 Keamanan Informasi Mencabut 2015-55 [BERLAKU]
- 236/2024 Kesadaran Keamanan Informasi [BERLAKU]
- 103/2023 Perlindungan Data Pribadi [BERLAKU]
- 102/2023 Cloud Computing Mencabut 2015-456 [BERLAKU]
- 30/2025 Manajemen Layanan TI Mencabut 2012-610 [BERLAKU]
- 200/2026 ICT Project Management Mencabut 2025-345 [BERLAKU]
- 103/2026 AI Knowledge Based System Mencabut 2021-123 [BERLAKU]
- 299/2020 AI Data Science [BERLAKU]
- 268/2020 AI Data Management [BERLAKU]
- 300/2020 IoT [BERLAKU]
- 391/2020 Security Operations Center [BERLAKU]
- 4/2023 Kriptografi [BERLAKU]
- 120/2025 Tanggap Insiden Siber [BERLAKU]
- 47/2022 Digital Forensik [BERLAKU]
- 24/2022 Audit Keamanan Informasi [BERLAKU]
- 23/2022 Uji Keamanan Siber [BERLAKU]

### 15 DICABUT JANGAN DIPAKAI

- 142/2005 DICABUT 2016-282
- 269/2006 DICABUT 2016-321
- 272/2006 DICABUT
- 115/2007 DICABUT 2018-107
- 114/2008 DICABUT 2019-140
- 610/2012 DICABUT 2025-030 -> ganti 30/2025
- 717/2012 DICABUT 2018-101 -> ganti 101/2018
- 615/2012 DICABUT 2016-282 -> ganti 282/2016
- 400/2014 DICABUT 2020-173
- 55/2015 DICABUT 2024-191 -> ganti 191/2024
- 456/2015 DICABUT 2023-102 -> ganti 102/2023
- 94/2005 DICABUT 2018-056 -> ganti 56/2018
- 345/2025 DICABUT 2026-200 -> ganti 200/2026
- 18/2022 DICABUT 2024-172
- 123/2021 DICABUT 2026-103 -> ganti 103/2026

## Rules V6
- Portal DIHILANGKAN
- Polsel -> Poltas (Politeknik Aceh Selatan)
- Bloom C3-C6 60-80%
- Sawit PKS prioritas
- Output DOCX + XLSX 4 sheet + anti-gagal
