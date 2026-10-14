import pypdf
import sys
import re
import json

sys.stdout.reconfigure(encoding='utf-8')

eval_pdf = r"D:\Piopi\Cahier text\Planning année 2026-2028\Accueil transports Aerien ET Maritime-PF et Guides\Guide_Eval ATAM(5).pdf"
gopm_pdf = r"D:\Piopi\Cahier text\Planning année 2026-2028\Accueil transports Aerien ET Maritime-PF et Guides\GOPM_ATAM (6).pdf"
rdc_pdf = r"D:\Piopi\Cahier text\Planning année 2026-2028\Accueil transports Aerien ET Maritime-PF et Guides\RDC ATAM 04 09 (2).pdf"

reader_eval = pypdf.PdfReader(eval_pdf)
reader_gopm = pypdf.PdfReader(gopm_pdf)
reader_rdc = pypdf.PdfReader(rdc_pdf)

print(f"Guide_Eval Pages: {len(reader_eval.pages)}")
print(f"GOPM Pages: {len(reader_gopm.pages)}")
print(f"RDC Pages: {len(reader_rdc.pages)}")

# 1. Extract 22 Modules from Guide_Eval Page 7
page7 = reader_eval.pages[6].extract_text()
print("=== GUIDE EVAL SYNTHESIS ===")
print(page7)

# 2. Extract detailed evaluation info for each module
mod_eval = {}
for p_idx, page in enumerate(reader_eval.pages):
    txt = page.extract_text() or ''
    m_match = re.search(r'(?:NO et titre du module|N° et titre du module|Titre du module)\s*[:\-]?\s*(\d{1,2})\s*–\s*([^,\n\r]+)', txt, re.IGNORECASE)
    if m_match:
        num = int(m_match.group(1))
        title = m_match.group(2).strip()
        if num not in mod_eval:
            mod_eval[num] = {
                'title': title,
                'pages': [],
                'durations': [],
                'exam_types': [],
                'seuils': [],
                'sample_criteria': []
            }
        mod_eval[num]['pages'].append(p_idx + 1)
        
        # Check exam types
        for et in [
            'TABLEAU DE SPÉCIFICATIONS – EPREUVE PRATIQUE',
            'TABLEAU DE SPECIFICATIONS EPREUVE PRATIQUE',
            'TABLEAU DE SPÉCIFICATIONS  EPREUVE PRATIQUE',
            'TABLEAU DE SPÉCIFICATIONS – CONNAISSANCES PRATIQUES',
            'TABLEAU DE SPECIFICATIONS CONNAISSANCES PRATIQUES',
            'TABLEAU DE SPÉCIFICATIONS  CONNAISSANCES PRATIQUES',
            'TABLEAU D’ANALYSE DU PROGRAMME'
        ]:
            if et.lower() in txt.lower() and et not in mod_eval[num]['exam_types']:
                mod_eval[num]['exam_types'].append(et)

        # Durations
        dur_matches = re.findall(r'Durée\s*[:]?\s*([0-9\sA-Za-z]+(?:heure|h|min)[^\n\r]*)', txt, re.IGNORECASE)
        for d in dur_matches:
            d_clean = d.strip()
            if d_clean not in mod_eval[num]['durations']:
                mod_eval[num]['durations'].append(d_clean)

        # Seuils
        seuil_m = re.findall(r'Seuil de r[ée]ussite\s*[:]?\s*([^\n\r]+)', txt, re.IGNORECASE)
        for s in seuil_m:
            s_clean = s.strip()
            if s_clean not in mod_eval[num]['seuils']:
                mod_eval[num]['seuils'].append(s_clean)

print("\n=== MODULE BY MODULE EVALUATION SPECIFICATIONS ===")
for num in sorted(mod_eval.keys()):
    v = mod_eval[num]
    print(f"\n--- M{num:02d} : {v['title']} (Pages Guide Eval: {v['pages']}) ---")
    print(f"Exam Types: {v['exam_types']}")
    print(f"Durations mentioned: {v['durations']}")
    print(f"Seuil de réussite: {v['seuils']}")
