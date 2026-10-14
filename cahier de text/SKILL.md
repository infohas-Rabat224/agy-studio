---
name: cahierdetext
description: Automates the production, pagination, date mapping, and verification of "Fiche de Suivi Pédagogique / Cahier de Texte" documents (M3 through M22) from master templates and timetable schedules using python-docx and Word COM automation.
---

# Cahier de Texte / Fiche de Suivi Pédagogique Production Skill

This skill automates the generation and quality assurance of pedagogical follow-up documents ("Fiches de Suivi Pédagogique") for accreditation programs (e.g., 2026–2028).

## 1. Master Template Governance (Strict Rules)

- **Master Template File**: `C:\Users\piopi\Downloads\M3.docx copy.docx`
- **IMMUTABILITY**: **NEVER modify `M3.docx copy.docx` under any circumstances.**
- **ISOLATION**: Every new module document must be created directly from a fresh, independent copy of `M3.docx copy.docx`.
- **NO CHAINING**: Never use a previously generated module as the template for a subsequent module (i.e. `M3 -> M4 -> M5` is forbidden). Always:
  $$\text{M3.docx copy.docx} \xrightarrow{\text{fresh copy}} \text{M}_n\text{.docx}$$

## 2. Authoritative Data Sources

1. **Module Source (Curriculum content)**:
   - Located in: `D:\Piopi\Cahier text\Planning année 2026-2028\Les 22 modules\` (or `Planning année [YYYY-YYYY]\...`).
   - Files are named `M<N>.doc` or `M<N>.docx` or `M<N>-1ere annee.doc`.
   - Authoritative for: Module Title (`Intitulé`), Trainer (`Formateur`), General Objective (`Objectif général`), Sequence & Total Duration (`Séquence / Durée`), Pedagogical Objectives, Descriptions, Observations, Dispositions, Session Durations, and Director Comments.
2. **Timetable Source (Official Dates & Slots)**:
   - Located in: `D:\Piopi\Cahier text\Planning année 2026-2028\1er année\Emploi du temps 01 année acreditation 2026-2027.docx`.
   - Authoritative for: Session Dates, Days of the week, Time slots (e.g. `13h-16h` or `09h-12h`).
   - Sessions must be mapped 1-to-1 in chronological order to the curriculum sessions.

## 3. Template Architecture & Layout Geometry

Each page in the document must contain exactly:
1. **Header Table (3 rows, 2 columns)**:
   - **Row 0**: Title banner (e.g. `ETAT D’AVANCEMENT ET DE REALISATION DU PROGRAMME DE FORMATION M<N> - Fiche de Suivi Pédagogique (2026-2027)`), bold, default font size.
   - **Row 1**:
     - Left: `Intitulé de l'unité de formation : ` (bold) + `[TITLE IN UPPERCASE]` (regular).
     - Right: `Formateur : ` (bold) + `[TRAINER NAME]` (regular).
   - **Row 2**:
     - Left: `Objectif général de l'unité de formation : ` (bold) + `[General Objective]` (regular).
     - Right: Two paragraphs:
       - P1: `Objectif/Intitulé de la séquence pédagogique et volume horaire : ` (bold)
       - P2: `Séquence : [SEQ] / Module : [NN] / Durée : [VH] h` (regular)
2. **Spacer Paragraph (4pt exact)**:
   ```xml
   <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
     <w:pPr>
       <w:spacing w:before="0" w:after="20" w:line="100" w:lineRule="exact"/>
       <w:rPr><w:sz w:val="4"/></w:rPr>
     </w:pPr>
   </w:p>
   ```
3. **Session Table**:
   - Header Row: Date & horaire | Objectif pédagogique | Descriptif du déroulement | Observations du formateur | Dispositions | Nbr heures | Nbr Heures Cumulées | Signature du formateur.
   - 4 session rows per page (except the final page if remaining sessions < 4).
   - Cells: 8pt (`Pt(8)`), bold (`bold=True`), with zero before/after spacing and `line="200" lineRule="auto"`:
     ```xml
     <w:spacing xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:before="0" w:after="0" w:line="200" w:lineRule="auto"/>
     ```
   - Every row MUST have `cantSplit`:
     ```xml
     <w:cantSplit xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>
     ```
4. **Spacer Paragraph (4pt exact)**: Same as above.
5. **Footer Table (2 rows, 2 columns)**:
   - Row 0: Col 0 empty, Col 1: `Taux de réalisation du VH : [XX]%` (8pt, bold).
   - Row 1: Col 0: `Commentaire du directeur sur le degré de réalisation des objectifs` (8pt, bold), Col 1: `.................................................................... [Comment]` (8pt, bold).
6. **Footer Note Paragraph**:
   - Text: `• Le formateur doit joindre à cette fiche de suivi pédagogique l’évaluation diagnostique, les évaluations sommatives, ainsi que la liste des participants signée pour chaque évaluation.` (from M3 template).
7. **Page Break / Section Break**:
   - Intermediate pages (all pages except last):
     ```xml
     <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
       <w:pPr><w:pageBreakBefore/></w:pPr>
     </w:p>
     ```
   - Final page: Spacer paragraph + `sectPr` (preserved from template).

## 4. Production Workflow for any Module M[N]

```
1. Convert M<N>.doc to M<N>_source.docx via Word COM:
   $doc.SaveAs2('...docx', 16)

2. Inspect & Extract:
   - Total sessions, hours per session, cumulative hours, sequence, trainer name, title, objectives.
   - Page comments and completion rates.

3. Extract Timetable:
   - Search Emploi du temps for module name / number / trainer.
   - Confirm session count matches curriculum 1-to-1.
   - Extract exact dates and time slots (e.g. "Lundi 03 Aou 2026 13h-16h").

4. Rebuild Clean Body:
   - Copy M3.docx copy.docx freshly.
   - Extract prototype tables and paragraphs.
   - Clear body and populate N pages.
   - Apply cantSplit, tight cell spacing, and 8pt bold formatting.

5. Verify & Quality Assurance:
   - Grep for obsolete module names (M3, M4, etc.) and obsolete trainers.
   - Verify 0 date/cumul mismatches.
   - Run Word COM: ComputeStatistics(2) == target page count.
   - Export to PDF: $doc.SaveAs2('...pdf', 17) and verify page count.
```

## 5. Automation Scripts

- `scripts/build_module.py`: Automated builder taking module number and source paths.
- `scripts/convert_doc.py`: COM-based batch doc to docx converter.
- `scripts/verify_module.py`: QA validator checking text, dates, page count, and exporting PDF.
