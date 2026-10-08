"""
RPS-AUDITOR V12 - AUDITOR BLOOM REAL + SKKNI + SAWIT
- Fix kritik Bos: selama ini cuma tambah [BERLAKU], untuk apa buat aplikasi?
- Sekarang: Cek kesesuaian kata-kata Taksonomi Bloom (KKO) secara masuk akal
- Aturan dari config_prompt_v6.txt:
  C1 Menyebutkan (20%), C2 Menjelaskan (20%), C3 Menerapkan/Mengkonfigurasi/Mengamankan 40% UTAMA, C4 Menganalisis/Mengaudit/Membedakan 30% UTAMA, C5 Mengevaluasi/Menguji/Memvalidasi 15%, C6 Merancang/Membuat SOP/Dashboard 15%
  Target: Smtr 1-2 min 60% C3-C6, Smtr 3+ min 80% C3-C6
  Format Sub-CPMK: Sub-CPMK X.X [C-Level] - KKO + objek + konteks sawit + [Kode SKKNI]
- Fitur: Audit Bloom distribusi, deteksi KKO tidak sesuai level, saran perbaikan KKO vokasi, track changes readable
streamlit run app.py
"""

import streamlit as st
import io, pathlib, re, difflib
from collections import Counter
from datetime import datetime
from docx import Document

st.set_page_config(page_title="RPS-Auditor V12 - Bloom Real Auditor", page_icon="📄", layout="wide", initial_sidebar_state="expanded")

# === KKO BLOOM VOKASI - dari config_prompt_v6.txt + standar ===
BLOOM_KKO = {
    "C1": ["menyebutkan", "mendefinisikan", "mengidentifikasi", "menamai", "menuliskan", "menyebut", "mendaftar", "mengenal"],
    "C2": ["menjelaskan", "menguraikan", "menginterpretasikan", "memberi contoh", "mengklasifikasikan", "merangkum", "memahami", "memaparkan"],
    "C3": ["menerapkan", "mengimplementasikan", "menggunakan", "mengkonfigurasi", "mengamankan", "menjalankan", "mengoperasikan", "memasang", "menginstalasi", "membuat enkripsi", "menerapkan enkripsi"],
    "C4": ["menganalisis", "mengaudit", "membedakan", "mengorganisasikan", "membandingkan", "menguraikan", "mendiagnosis", "menginvestigasi", "menganalisa", "mengaudit kerentanan"],
    "C5": ["mengevaluasi", "menguji", "memvalidasi", "menilai", "mengkritik", "mengukur", "memverifikasi", "menguji validasi", "mengevaluasi keamanan"],
    "C6": ["merancang", "membuat", "membangun", "menyusun", "merencanakan", "menciptakan", "mengembangkan", "merancang sop", "membuat dashboard", "merancang arsitektur", "membuat laporan"]
}

BLOOM_LEVEL = {"C1":1, "C2":2, "C3":3, "C4":4, "C5":5, "C6":6}

def detect_bloom_level(text):
    """Deteksi level Bloom dari KKO dalam teks"""
    text_lower = text.lower()
    for level in ["C6","C5","C4","C3","C2","C1"]:  # Cek dari tinggi ke rendah
        for kko in BLOOM_KKO[level]:
            if kko in text_lower:
                return level, kko
    return None, None

def extract_c_level_tag(text):
    """Ekstrak [C3] atau [C4] atau (C3) dari Sub-CPMK - FIX IndexError no such group"""
    m = re.search(r'\[C(\d)\]', text, re.IGNORECASE)
    if m:
        return f"C{m.group(1)}"
    m = re.search(r'\(C(\d)\)', text, re.IGNORECASE)
    if m:
        return f"C{m.group(1)}".upper()
    # Fallback tanpa group
    m2 = re.search(r'\(C\d\)', text, re.IGNORECASE)
    if m2:
        # Ambil C + angka dari match
        txt = m2.group(0)
        num = re.search(r'\d', txt)
        if num:
            return f"C{num.group(0)}"
    return None

def audit_bloom_distribution(sub_cpmk_list):
    """Hitung distribusi Bloom"""
    levels = []
    for item in sub_cpmk_list:
        tag = extract_c_level_tag(item["text"])
        if tag:
            levels.append(tag)
        else:
            lvl, _ = detect_bloom_level(item["text"])
            if lvl:
                levels.append(lvl)
    
    counter = Counter(levels)
    total = len(sub_cpmk_list) if sub_cpmk_list else 1
    c3_c6 = sum(counter.get(f"C{i}",0) for i in [3,4,5,6])
    percent_c3_c6 = (c3_c6 / total * 100) if total else 0
    
    return counter, total, c3_c6, percent_c3_c6

def suggest_bloom_fix(original_text, mk_name):
    """Saran perbaikan KKO Bloom agar lebih vokasi (C3-C6)"""
    text_lower = original_text.lower()
    
    # Deteksi level sekarang
    current_level, current_kko = detect_bloom_level(original_text)
    declared_tag = extract_c_level_tag(original_text)
    
    # Jika sudah C3-C6 dan tag sesuai, tidak perlu fix besar, hanya tambah konteks sawit + SKKNI
    if declared_tag in ["C3","C4","C5","C6"] and current_level == declared_tag:
        # Cek apakah ada konteks sawit
        if "sawit" not in text_lower and "blok" not in text_lower and "tph" not in text_lower and "tbs" not in text_lower:
            # Tambah konteks sawit di akhir
            if "menerapkan" in text_lower:
                return original_text + " pada data panen Blok A1 sesuai SOP PKS [Selaras SKKNI 282/2016]", f"Tambah konteks sawit PKS"
            elif "menganalisis" in text_lower:
                return original_text + " data timbangan PKS Blok A1-A2 [Selaras SKKNI 191/2024]", f"Tambah konteks sawit"
        return None, None  # Sudah bagus
    
    # Jika C1 atau C2, naikkan ke C3 atau C4 (vokasi butuh C3-C6)
    if current_level in ["C1","C2"] or declared_tag in ["C1","C2"]:
        # Contoh: "Memahami algoritma" -> "Menerapkan algoritma untuk..."
        # "Menjelaskan enkripsi" -> "Menerapkan enkripsi file data panen Blok A1 dengan VeraCrypt"
        
        if "memahami" in text_lower or "menjelaskan" in text_lower or "menyebutkan" in text_lower:
            # Ubah KKO
            new_text = original_text
            # Ganti KKO
            new_text = re.sub(r'(?i)memahami|menjelaskan|menyebutkan|menguraikan', 'Menerapkan', new_text, count=1)
            # Ganti tag C1/C2 jadi C3
            new_text = re.sub(r'\[C[12]\]', '[C3]', new_text)
            new_text = re.sub(r'\(C[12]\)', '(C3)', new_text)
            # Jika belum ada tag, tambah
            if "[C" not in new_text:
                new_text = new_text.replace("Sub-CPMK", "Sub-CPMK [C3] -")
            
            # Tambah konteks sawit + SKKNI
            if "sawit" not in new_text.lower():
                if "enkripsi" in new_text.lower() or "keamanan" in new_text.lower():
                    new_text += " file data panen Blok A1 dengan VeraCrypt sesuai SOP PKS [Selaras SKKNI 191/2024 Unit J.620100.XXX]"
                elif "algoritma" in new_text.lower() or "pemrograman" in new_text.lower():
                    new_text += " data panen Blok A1-A2 TPH TBS Grade A/B/C sesuai alur PKS [Selaras SKKNI 282/2016 Unit J.620100.009.02]"
                else:
                    new_text += " sesuai SOP PKS Blok A1-A2 [Selaras SKKNI 282/2016]"
            
            return new_text, f"Naikkan {current_level or declared_tag or 'C1/C2'} → C3 (vokasi butuh C3-C6) + tambah konteks sawit PKS"
    
    # Jika tag tidak ada, deteksi dan tambah
    if not declared_tag and current_level:
        new_text = original_text.replace("Sub-CPMK", f"Sub-CPMK [{current_level}] -")
        return new_text, f"Tambah tag Bloom [{current_level}] dari KKO '{current_kko}'"
    
    # Jika tag dan KKO tidak sesuai (misal tag C3 tapi KKO C1)
    if declared_tag and current_level and declared_tag != current_level:
        new_text = original_text.replace(f"[{declared_tag}]", f"[{current_level}]")
        new_text = new_text.replace(f"({declared_tag})", f"({current_level})")
        return new_text, f"Perbaiki tag: {declared_tag} tidak sesuai KKO '{current_kko}' ({current_level}), ganti jadi [{current_level}]"
    
    return None, None

def set_cell_text(cell, new_text):
    if not cell.paragraphs:
        cell.text = new_text
        return
    cell.paragraphs[0].text = new_text
    for p in cell.paragraphs[1:]:
        p.text = ""

def generate_changes_bloom(doc, mk_name):
    changes = []
    sub_cpmk_items = []
    
    # Kumpulkan Sub-CPMK dari Table1
    if len(doc.tables) >= 2:
        for t_idx in range(1, len(doc.tables)):
            t = doc.tables[t_idx]
            if len(t.rows) < 10:
                continue
            header = " ".join([c.text for c in t.rows[0].cells]).lower()
            if "minggu" not in header and "kompetensi" not in header and "sub-cpmk" not in header:
                continue
            for ri in range(1, len(t.rows)):
                if ri >= len(t.rows):
                    break
                row = t.rows[ri]
                if len(row.cells) < 2:
                    continue
                try:
                    cell = row.cells[1]
                    txt = cell.text
                    if txt.strip() and ("Sub-CPMK" in txt or "Mampu" in txt or len(txt) > 20):
                        sub_cpmk_items.append({"table": t_idx, "row": ri, "col": 1, "text": txt, "location": f"Minggu {ri}"})
                except:
                    pass
    
    # Audit distribusi Bloom
    counter, total, c3_c6, percent = audit_bloom_distribution(sub_cpmk_items)
    
    # Generate perbaikan Bloom per Sub-CPMK
    for item in sub_cpmk_items:
        orig = item["text"]
        new, reason = suggest_bloom_fix(orig, mk_name)
        if new and new != orig:
            changes.append({
                "id": f"bloom-t{item['table']}-r{item['row']}",
                "table": item["table"],
                "row": item["row"],
                "col": item["col"],
                "location": f"{item['location']} - {reason}",
                "original": orig,
                "revised": new,
                "type": "Perbaikan Bloom Taksonomi",
                "accepted": True
            })
    
    # Tambah juga perbaikan SKKNI dan Sawit + Wajib Flowchart/Testing (seperti sebelumnya tapi lebih presisi)
    # ... (logika SKKNI dan sawit tetap)
    if len(doc.tables) >= 2:
        for t_idx in range(1, len(doc.tables)):
            t = doc.tables[t_idx]
            if len(t.rows) < 10:
                continue
            header = " ".join([c.text for c in t.rows[0].cells]).lower()
            if "minggu" not in header:
                continue
            for ri in [6,15]:
                if ri >= len(t.rows):
                    continue
                row = t.rows[ri]
                if len(row.cells) < 2:
                    continue
                try:
                    cell = row.cells[1]
                    orig = cell.text
                    if ri == 6 and "Rubrik 4 kriteria" not in orig:
                        new = orig + " → FIX: Rubrik 4 kriteria: Simbol terminator/process/decision/I/O, Kondisi Grade/Premi, Alur Blok->TPH->Truk->Timbangan->Sortasi, Kesesuaian kasus - WAJIB [191/2024]"
                        changes.append({
                            "id": f"flowchart-t{t_idx}-r{ri}",
                            "table": t_idx,
                            "row": ri,
                            "col": 1,
                            "location": f"Minggu {ri} - Wajib Flowchart Rubrik 4",
                            "original": orig,
                            "revised": new,
                            "type": "Wajib Flowchart",
                            "accepted": True
                        })
                    if ri == 15 and "3 kasus uji" not in orig.lower():
                        new = orig + " → FIX: 3 kasus uji: Normal 25 janjang / Batas 0 / Tidak Valid huruf + Expected vs Actual + Bug log + Fix + Re-test + Video 2 menit - WAJIB [24/2022]"
                        changes.append({
                            "id": f"testing-t{t_idx}-r{ri}",
                            "table": t_idx,
                            "row": ri,
                            "col": 1,
                            "location": f"Minggu {ri} - Wajib Testing 3 Kasus",
                            "original": orig,
                            "revised": new,
                            "type": "Wajib Testing",
                            "accepted": True
                        })
                except:
                    pass
    
    return changes, counter, total, c3_c6, percent

def apply_changes(doc, changes):
    for ch in changes:
        if not ch["accepted"]:
            continue
        try:
            table = doc.tables[ch["table"]]
            cell = table.rows[ch["row"]].cells[ch["col"]]
            set_cell_text(cell, ch["revised"])
        except:
            pass
    return doc

def render_diff(orig, rev):
    s = difflib.SequenceMatcher(None, orig, rev)
    orig_html = ""
    rev_html = ""
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'equal':
            txt = orig[i1:i2]
            orig_html += f"<span style='color:#1A202C'>{txt}</span>"
            rev_html += f"<span style='color:#1A202C'>{txt}</span>"
        elif tag == 'delete':
            txt = orig[i1:i2]
            orig_html += f"<span style='background:#FED7D7;color:#9B2C2C;text-decoration:line-through;padding:1px 3px;border-radius:3px'>{txt}</span>"
        elif tag == 'insert':
            txt = rev[j1:j2]
            rev_html += f"<span style='background:#C6F6D5;color:#22543D;padding:1px 3px;border-radius:3px;font-weight:600;border:1px solid #9AE6B4'>{txt}</span>"
        elif tag == 'replace':
            ot = orig[i1:i2]
            rt = rev[j1:j2]
            orig_html += f"<span style='background:#FED7D7;color:#9B2C2C;text-decoration:line-through;padding:1px 3px;border-radius:3px'>{ot}</span>"
            rev_html += f"<span style='background:#C6F6D5;color:#22543D;padding:1px 3px;border-radius:3px;font-weight:600'>{rt}</span>"
    return orig_html, rev_html

# === UI ===
st.markdown("""
<style>
.main-header{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:16px 20px;margin-bottom:16px}
.bloom-bar{display:flex;gap:4px;margin:8px 0;height:12px}
.bloom-c1{background:#A0AEC0;border-radius:4px} .bloom-c2{background:#90CDF4;border-radius:4px} .bloom-c3{background:#63B3ED;border-radius:4px} .bloom-c4{background:#48BB78;border-radius:4px} .bloom-c5{background:#ECC94B;border-radius:4px} .bloom-c6{background:#F56565;border-radius:4px}
.card{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:16px;margin:12px 0;color:#1A202C !important}
.card b{color:#1A202C !important}
.orig-box{background:#FFF5F5;border:1px solid #FEB2B2;border-radius:8px;padding:12px;color:#1A202C !important;font-size:13px;line-height:1.6}
.rev-box{background:#F0FFF4;border:1px solid #9AE6B4;border-radius:8px;padding:12px;color:#1A202C !important;font-size:13px;line-height:1.6}
</style>
<div class="main-header">
  <b style="font-size:18px;color:#1A202C">📄 RPS-Auditor V12 - Bloom Real Auditor</b><br>
  <span style="color:#4A5568;font-size:13px">Bukan cuma [BERLAKU] - Cek kesesuaian kata-kata Taksonomi Bloom C1-C6 secara masuk akal - Target Smtr 1-2 min 60% C3-C6, Smtr 3+ min 80%</span>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("📤 UPLOAD RPS")
    uploaded = st.file_uploader("Upload RPS (.docx)", type=["docx"])
    mk = st.selectbox("Mata Kuliah", ["Algoritma Pemrograman","Keamanan Data","Jaringan Komputer","Basis Data","Keamanan Informasi"], index=0)
    semester = st.selectbox("Semester", ["1","2","3","4","5","6"], index=2)
    st.markdown("---")
    st.markdown("**Aturan Bloom Vokasi:** C3 40% + C4 30% + C5 15% + C6 15% = C3-C6 min 60% (Smtr 1-2) atau 80% (Smtr 3+)")

if not uploaded:
    st.info("👈 Upload RPS di Sidebar - Nanti audit Bloom: distribusi C1-C6, deteksi KKO tidak sesuai level, saran naikkan C1/C2 → C3-C6 vokasi")
    st.markdown("""
    **Contoh audit masuk akal:**
    - ❌ `Sub-CPMK 1.1 - Memahami algoritma` → C2, tidak vokasi, objek tidak jelas → Saran: `Sub-CPMK 1.1 [C3] - Menerapkan algoritma sorting untuk data panen Blok A1-A2 TPH TBS Grade A/B/C sesuai alur PKS [282/2016]`
    - ❌ `Sub-CPMK 2.1 [C3] - Menjelaskan enkripsi` → Tag C3 tapi KKO C2 (menjelaskan) tidak sesuai → Saran: `Sub-CPMK 2.1 [C2] - Menjelaskan...` atau ganti KKO jadi `Menerapkan`
    - ✅ `Sub-CPMK 2.2 [C3] - Menerapkan enkripsi file data panen Blok A1 dengan VeraCrypt sesuai SOP PKS [191/2024]` → C3 sesuai, ada objek, ada konteks sawit, ada SKKNI
    """)
else:
    if "changes" not in st.session_state or st.session_state.get("last_file") != uploaded.name:
        doc_temp = Document(io.BytesIO(uploaded.getbuffer()))
        changes, counter, total, c3_c6, percent = generate_changes_bloom(doc_temp, mk)
        st.session_state.changes = changes
        st.session_state.counter = counter
        st.session_state.total = total
        st.session_state.c3_c6 = c3_c6
        st.session_state.percent = percent
        st.session_state.last_file = uploaded.name
    
    changes = st.session_state.changes
    counter = st.session_state.counter
    total = st.session_state.total
    c3_c6 = st.session_state.c3_c6
    percent = st.session_state.percent
    
    target = 60 if semester in ["1","2"] else 80
    status = "LULUS" if percent >= target else "TIDAK LULUS"
    color_status = "#48BB78" if status=="LULUS" else "#F56565"
    
    st.markdown(f"""
    <div class="card">
      <b style="color:#1A202C;font-size:16px">Audit Bloom Taksonomi - Semester {semester}</b><br>
      <div style="display:flex;gap:8px;margin:10px 0">
        <div style="background:#EBF8FF;border:1px solid #90CDF4;padding:8px 12px;border-radius:8px;color:#1A365D">Total Sub-CPMK: <b style="color:#1A365D">{total}</b></div>
        <div style="background:#F0FFF4;border:1px solid #9AE6B4;padding:8px 12px;border-radius:8px;color:#22543D">C3-C6: <b style="color:#22543D">{c3_c6}/{total} = {percent:.1f}%</b></div>
        <div style="background:{color_status}20;border:1px solid {color_status};padding:8px 12px;border-radius:8px;color:#1A202C">Target {target}% → <b style="color:{color_status}">{status}</b></div>
      </div>
      <div class="bloom-bar">
        <div class="bloom-c1" style="width:{counter.get('C1',0)/total*100 if total else 0}%" title="C1 {counter.get('C1',0)}"></div>
        <div class="bloom-c2" style="width:{counter.get('C2',0)/total*100 if total else 0}%" title="C2 {counter.get('C2',0)}"></div>
        <div class="bloom-c3" style="width:{counter.get('C3',0)/total*100 if total else 0}%" title="C3 {counter.get('C3',0)}"></div>
        <div class="bloom-c4" style="width:{counter.get('C4',0)/total*100 if total else 0}%" title="C4 {counter.get('C4',0)}"></div>
        <div class="bloom-c5" style="width:{counter.get('C5',0)/total*100 if total else 0}%" title="C5 {counter.get('C5',0)}"></div>
        <div class="bloom-c6" style="width:{counter.get('C6',0)/total*100 if total else 0}%" title="C6 {counter.get('C6',0)}"></div>
      </div>
      <div style="font-size:12px;color:#4A5568">C1: {counter.get('C1',0)} | C2: {counter.get('C2',0)} | C3: {counter.get('C3',0)} | C4: {counter.get('C4',0)} | C5: {counter.get('C5',0)} | C6: {counter.get('C6',0)} | Rumus: (C3-C6/Total)*100% = ({c3_c6}/{total})*100% = {percent:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
    
    if percent < target:
        st.error(f"🔴 TIDAK LULUS Bloom: {percent:.1f}% < {target}% - Perlu naikkan C1/C2 jadi C3-C6 - Ada {len([c for c in changes if 'Bloom' in c['type']])} saran perbaikan Bloom")
    else:
        st.success(f"✅ LULUS Bloom: {percent:.1f}% >= {target}%")
    
    st.markdown("---")
    colA, colB, colC = st.columns([2,1,1])
    with colA:
        kept = len([c for c in changes if c["accepted"]])
        st.write(f"**{kept} dari {len(changes)} perbaikan dipertahankan** - Termasuk {len([c for c in changes if 'Bloom' in c['type']])} perbaikan Bloom")
    with colB:
        if st.button("✅ Pertahankan semua", use_container_width=True):
            for ch in st.session_state.changes:
                ch["accepted"] = True
            st.rerun()
    with colC:
        if st.button("🔴 Kembalikan semua", use_container_width=True):
            for ch in st.session_state.changes:
                ch["accepted"] = False
            st.rerun()
    
    for idx, ch in enumerate(st.session_state.changes):
        st.markdown(f"""
        <div class="card">
          <b style="color:#1A202C">{ch['location']}</b> - <span style="color:#4A5568">{ch['type']}</span><br>
          <span style="font-size:11px;color:#718096">{ch['id']}</span>
        </div>
        """, unsafe_allow_html=True)
        orig_html, rev_html = render_diff(ch['original'], ch['revised'])
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Sebelum:**")
            st.markdown(f"<div class='orig-box'>{orig_html}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("**Sesudah - Masuk akal Bloom:**")
            st.markdown(f"<div class='rev-box'>{rev_html}</div>", unsafe_allow_html=True)
        b1, b2, b3 = st.columns([1,1,3])
        with b1:
            if st.button("✅ Pertahankan", key=f"k_{idx}", use_container_width=True, type="primary" if ch["accepted"] else "secondary"):
                st.session_state.changes[idx]["accepted"] = True
                st.rerun()
        with b2:
            if st.button("🔴 Kembalikan", key=f"r_{idx}", use_container_width=True):
                st.session_state.changes[idx]["accepted"] = False
                st.rerun()
        with b3:
            st.caption("✅ Dipertahankan" if ch["accepted"] else "🔴 Dikembalikan")
        st.markdown("---")
    
    st.header("📥 Download")
    accepted = len([c for c in changes if c["accepted"]])
    if st.button(f"🚀 Terapkan {accepted} perbaikan dan Download", type="primary", use_container_width=True):
        doc_final = Document(io.BytesIO(uploaded.getbuffer()))
        doc_final = apply_changes(doc_final, st.session_state.changes)
        out = io.BytesIO()
        doc_final.save(out)
        out.seek(0)
        st.download_button(f"📄 DOWNLOAD RPS - Bloom {percent:.1f}% - {accepted} perbaikan", out, file_name=f"V12_BLOOM_{percent:.0f}PERSEN_{mk.replace(' ','_')}_{uploaded.name}", use_container_width=True, type="primary")
        st.balloons()

st.caption("V12 Bloom Real Auditor - Bukan cuma [BERLAKU] - Cek KKO C1-C6, distribusi, kesesuaian tag vs KKO, saran naikkan C1/C2 → C3-C6 vokasi + konteks sawit PKS")
