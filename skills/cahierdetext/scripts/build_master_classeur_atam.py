# -*- coding: utf-8 -*-
"""
Script to generate the complete, official, accreditation-ready Master Portfolio:
CLASSEUR PÉDAGOGIQUE MAÎTRE DE LA FILIÈRE ATAM (DOSSIER DE SUIVI PÉDAGOGIQUE & D'ACCRÉDITATION)
Promotion 2026–2028 | INFOHAS Rabat
Target length: 15–18 pages, fully structured according to APC & DFP accreditation standards.
"""

import os
import sys
import docx
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import OxmlElement, parse_xml

OUTPUT_DOCX = r"D:\Piopi\Cahier text\Planning année 2026-2028\Classeur formateur\Classeur-Pedagogique-Filiere-ATAM-Global-M1-M21.docx"
OUTPUT_PDF  = r"D:\Piopi\Cahier text\Planning année 2026-2028\Classeur formateur\Classeur-Pedagogique-Filiere-ATAM-Global-M1-M21.pdf"

# ─── COLOR PALETTE ─────────────────────────────────────────────────────────────
NAVY       = "1F3864"   # Primary headers
DEEP_BLUE  = "2F5597"   # Secondary titles
STEEL_BLUE = "418AB3"   # Sub-elements
LIGHT_BG   = "F2F6FA"   # Alternating row shading
ACCENT_RED = "C00000"   # Important callouts
BORDER_COL = "B0C4DE"   # Subtle table borders
AMBER_BG   = "FFF2CC"   # Stages highlight
GREEN_BG   = "E2EFDA"   # 2nd year highlight
HEADER_TXT = "FFFFFF"

# ─── XML & FORMATTING HELPERS ─────────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    """Set cell background color."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_borders(cell, border_specs=None):
    """Set border for an individual cell."""
    if border_specs is None:
        border_specs = {'top': (4, BORDER_COL), 'left': (4, BORDER_COL),
                        'bottom': (4, BORDER_COL), 'right': (4, BORDER_COL)}
    tcPr = cell._tc.get_or_add_tcPr()
    tbl_borders = OxmlElement('w:tcBorders')
    for side, (sz, color) in border_specs.items():
        border_el = OxmlElement(f'w:{side}')
        border_el.set(qn('w:val'), 'single')
        border_el.set(qn('w:sz'), str(sz))
        border_el.set(qn('w:space'), '0')
        border_el.set(qn('w:color'), color)
        tbl_borders.append(border_el)
    tcPr.append(tbl_borders)

def set_table_borders(table, color=BORDER_COL, size=4):
    """Apply uniform borders to entire table."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="{size}" w:space="0" w:color="{color}"/>\n'
        f'  <w:left w:val="single" w:sz="{size}" w:space="0" w:color="{color}"/>\n'
        f'  <w:bottom w:val="single" w:sz="{size}" w:space="0" w:color="{color}"/>\n'
        f'  <w:right w:val="single" w:sz="{size}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideH w:val="single" w:sz="{size}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideV w:val="single" w:sz="{size}" w:space="0" w:color="{color}"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def set_row_cant_split(row):
    """Prevent table row from breaking across pages."""
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

def set_row_tbl_header(row):
    """Repeat header row on each page if table spans pages."""
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

def cell_para(cell, text, font_size=8.5, bold=False, italic=False,
              align=WD_ALIGN_PARAGRAPH.LEFT, color=None, space_before=30, space_after=30,
              font_name='Arial'):
    """Format or add text inside a table cell."""
    if len(cell.paragraphs) == 0:
        p = cell.add_paragraph()
    else:
        p = cell.paragraphs[0]
        # if cell has text already and this is first call, clear
        if p.text:
            for extra in cell.paragraphs[1:]:
                p_el = extra._element
                p_el.getparent().remove(p_el)
            p.text = ""

    p.alignment = align
    pPr = p._p.get_or_add_pPr()
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:before'), str(space_before))
    spacing.set(qn('w:after'), str(space_after))
    pPr.append(spacing)

    run = p.add_run(text)
    run.font.name = font_name
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(font_size)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    return p

def add_cell_extra_para(cell, text, font_size=8, bold=False, italic=False,
                        align=WD_ALIGN_PARAGRAPH.LEFT, color=None, space_before=10, space_after=20,
                        font_name='Arial'):
    """Add an extra paragraph in the same cell."""
    p = cell.add_paragraph()
    p.alignment = align
    pPr = p._p.get_or_add_pPr()
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:before'), str(space_before))
    spacing.set(qn('w:after'), str(space_after))
    pPr.append(spacing)

    run = p.add_run(text)
    run.font.name = font_name
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(font_size)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    return p

def set_col_widths(table, widths_cm):
    """Set explicit column widths."""
    for row in table.rows:
        set_row_cant_split(row)
        for j, cell in enumerate(row.cells):
            if j < len(widths_cm):
                cell.width = Cm(widths_cm[j])

def format_header_row(table, texts, widths_cm=None, bg_color=NAVY, font_color=HEADER_TXT, font_size=8.5):
    """Format table header row."""
    row = table.rows[0]
    set_row_cant_split(row)
    set_row_tbl_header(row)
    for j, cell in enumerate(row.cells):
        set_cell_bg(cell, bg_color)
        if j < len(texts):
            cell_para(cell, texts[j], font_size=font_size, bold=True,
                      align=WD_ALIGN_PARAGRAPH.CENTER, color=font_color,
                      space_before=40, space_after=40)
    if widths_cm:
        set_col_widths(table, widths_cm)

def add_heading_1(doc, num_str, title_str, page_break=False):
    """Add a prominent Level 1 section header banner."""
    if page_break:
        doc.add_page_break()
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:before'), '180')
    spacing.set(qn('w:after'), '80')
    pPr.append(spacing)

    # Shaded banner look
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run_num = p.add_run(f"{num_str}.  ")
    run_num.font.name = 'Arial'
    run_num.bold = True
    run_num.font.size = Pt(12)
    run_num.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)

    run_title = p.add_run(title_str.upper())
    run_title.font.name = 'Arial'
    run_title.bold = True
    run_title.font.size = Pt(11.5)
    run_title.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

def add_heading_2(doc, title_str, space_before='120', space_after='50'):
    """Add Level 2 subsection header."""
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:before'), space_before)
    spacing.set(qn('w:after'), space_after)
    pPr.append(spacing)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    run = p.add_run(title_str)
    run.font.name = 'Arial'
    run.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x2F, 0x55, 0x97)

def add_body_p(doc, text, bold_prefix="", space_before='40', space_after='40', italic=False):
    """Add standard body paragraph with optional bold prefix."""
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:before'), space_before)
    spacing.set(qn('w:after'), space_after)
    pPr.append(spacing)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = 'Arial'
        r_pre.bold = True
        r_pre.font.size = Pt(9)
        r_pre.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

    run = p.add_run(text)
    run.font.name = 'Arial'
    run.font.size = Pt(8.5)
    run.italic = italic
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    return p

# ─── DATA REPOSITORY ──────────────────────────────────────────────────────────

SCHOOL_INFO = {
    'nom': 'INFOHAS',
    'raison': 'Institut Privé Spécialisé des Hôtesses de l\'Air et Stewards (INFOHAS)',
    'statut': 'Établissement Privé de Formation Professionnelle Accrédité',
    'filiere': 'Accueil dans le Transport Aérien et Maritime (ATAM)',
    'niveau': 'Technicien',
    'adresse': '15, Rue Demnate – Quartier Hassan, Rabat – Maroc',
    'tel': '+212 5 37 70 80 90 / +212 5 37 72 40 50',
    'email': 'infohas@menara.ma',
    'site': 'www.infohas.ma',
    'promo': '2026 – 2028',
    'annees': '1ère Année : 2026 / 2027  |  2ème Année : 2027 / 2028',
    'directeur': 'Directeur Pédagogique Général d\'INFOHAS',
}

TRAINERS = [
    ("Mme AZIZA JOUAIDI",
     "Cadre Formatrice / Ex-Chef de Cabine Principal (RAM) - Spécialiste Secourisme, CRM & Procédures Cabine",
     "M01, M04, M05, M11, M14", "Permanent", "18 ans"),
    ("Mme ILHAM EDDRIOUICH",
     "Formatrice d'Escale & Marine / Spécialiste Relations Clients, Embarquement & Croisières",
     "M07, M12, M16, M20, M18 (Prat.)", "Permanent", "14 ans"),
    ("Mme IMANE MZIOUAD",
     "Formatrice Linguistique & Communication Professionnelle / Spécialiste Français & Espagnol Aérien",
     "M03, M05, M07, M15", "Permanent", "12 ans"),
    ("M. RACHID EL SABAH",
     "Expert Sûreté & Réglementation Internationale / Ancien Inspecteur Sûreté Aérienne & Maritime (ISPS/OACI)",
     "M02, M09, M10, M18, M19", "Permanent", "20 ans"),
    ("M. AHMED BENJAA",
     "Formateur Commercial & Anglais / Spécialiste Vente Duty Free, Négociation & Recrutement Compagnies",
     "M06, M06-2, M08, M17, M21", "Permanent", "15 ans"),
    ("M. TAREQ ECHFIRA",
     "Formateur Anglais Aéronautique & Référent Insertion Professionnelle (Assessment Centers)",
     "M01, M06-1, M21", "Permanent", "11 ans"),
    ("M. ABDELOUAHED BOUIH",
     "Formateur Outils Numériques, Progiciels de Transport Aérien (DCS) & Anglais Technique",
     "M02, M06-2", "Permanent", "10 ans"),
]

# 22 Modules Matrix APC
MODULES_APC = [
    ("M01", "Métier et formation", "CG", "1ère Année (S1)", 12, 15, 3, 30, "M. T. Echfira / Mme A. Jouaidi"),
    ("M02", "Outils informatiques & progiciels transport", "CP", "1ère Année (S2)", 15, 40, 5, 60, "M. R. El Sabah / M. A. Bouih"),
    ("M03", "Communication professionnelle en français", "CG", "1ère Année (S1)", 30, 80, 10, 120, "Mme I. Mziouad"),
    ("M04", "Environnement professionnel aéron. & marit.", "CP", "1ère Année (S1-S2)", 120, 48, 12, 180, "Mme A. Jouaidi"),
    ("M05", "Comportements et attitudes professionnels", "CP", "1ère Année (S1)", 15, 40, 5, 60, "Mme A. Jouaidi / Mme I. Mziouad"),
    ("M06-1","Communication en anglais (1ère Année)", "CG", "1ère Année (S1-S2)", 20, 50, 5, 75, "M. T. Echfira / M. A. Benjaa"),
    ("M07", "Approche client et accueil passagers", "CP", "1ère Année (S1)", 15, 40, 5, 60, "Mme I. Eddriouich / Mme I. Mziouad"),
    ("M08", "Interaction en situations pro. & conflits", "CP", "1ère Année (S1)", 20, 50, 5, 75, "M. A. Benjaa"),
    ("M09", "Mesures de sûreté (OACI / ISPS)", "CP", "1ère Année (S1)", 25, 15, 5, 45, "M. R. El Sabah"),
    ("M10", "Marchandises dangereuses (IATA DGR / IMDG)","CP", "1ère Année (S2)", 25, 15, 5, 45, "M. R. El Sabah"),
    ("M11", "Procédures de pré-départ & armement", "CP", "1ère Année (S2)", 15, 40, 5, 60, "Mme A. Jouaidi"),
    ("M12", "Embarquement et départ passagers", "CP", "1ère Année (S2)", 15, 40, 5, 60, "Mme I. Eddriouich"),
    ("M13", "Stage 1 d'immersion professionnelle", "CI", "1ère Année (Avr 27)", 0, 110, 10, 120, "Commission ATAM & Tuteurs Pro"),
    # 2ème Année
    ("M14", "Premiers secours & secourisme (RCP/DAE)", "CP", "2ème Année (S3-S4)", 45, 110, 10, 165, "Mme A. Jouaidi"),
    ("M15", "Communication en espagnol professionnel", "CG", "2ème Année (S3)", 25, 60, 5, 90, "Mme I. Mziouad"),
    ("M16", "Service durant la croisière & hôtellerie", "CP", "2ème Année (S3)", 30, 80, 10, 120, "Mme I. Eddriouich"),
    ("M17", "Vente de produits à bord (Duty Free)", "CP", "2ème Année (S3)", 15, 40, 5, 60, "M. A. Benjaa"),
    ("M18", "Procédures d'urgence aériennes", "CP", "2ème Année (S3-S4)", 30, 55, 5, 90, "M. El Sabah / Mme Eddriouich"),
    ("M19", "Procédures d'urgence maritimes (SOLAS)", "CP", "2ème Année (S4)", 30, 55, 5, 90, "M. R. El Sabah"),
    ("M20", "Arrivée et débarquement passagers", "CP", "2ème Année (S3)", 20, 65, 5, 90, "Mme I. Eddriouich"),
    ("M21", "Techniques recherche d'emploi & Assessment","CG", "2ème Année (S3)", 10, 18, 2, 30, "M. T. Echfira / M. A. Benjaa"),
    ("M06-2","Communication en anglais (2ème Année)", "CG", "2ème Année (S4)", 20, 50, 5, 75, "M. A. Benjaa / M. A. Bouih"),
    ("M22", "Stage 2 intégration pro. & Soutenance", "CI", "2ème Année (Avr-Juin)", 0, 100, 20, 120, "Jury Mixte & Tuteurs Pro"),
]

# Detailed Didactic Sheets Data (All 22 modules)
MODULE_DETAILS = [
    {
        'code': 'M01', 'titre': 'Métier et Formation', 'vh': '30 h (Théorie: 12h | Pratique: 15h | Éval: 3h)',
        'periode': '1ère Année – Semestre 1', 'formateurs': 'M. Tareq Echfira / Mme Aziza Jouaidi',
        'competence': 'Se situer au regard du métier d\'agent de bord et d\'accueil dans les transports aérien et maritime ainsi que de la démarche de formation selon l\'APC.',
        'elements': [
            'Connaître les réalités du marché de l\'emploi aérien (PNC, escales) et maritime (croisières, ferries).',
            'Comprendre les exigences physiques, médicales, réglementaires et déontologiques du métier.',
            'Identifier les compétences du programme et élaborer son projet personnel et professionnel de formation.'
        ],
        'materiel': 'Support de présentation multimédia, vidéos de témoignages de navigants, référentiel de formation.',
        'evaluation': 'Contrôle continu sommatif : Bilan réflexif individuel et test de positionnement (Note sur 20).'
    },
    {
        'code': 'M02', 'titre': 'Outils Informatiques & Progiciels de Transport', 'vh': '60 h (Théorie: 15h | Pratique: 40h | Éval: 5h)',
        'periode': '1ère Année – Semestre 2', 'formateurs': 'M. Rachid El Sabah / M. Abdelouahed Bouih',
        'competence': 'Exploiter les outils bureautiques et les logiciels professionnels appliqués à la gestion d\'escale et de vol.',
        'elements': [
            'Maîtrise de la bureautique appliquée : traitement de texte pour rapports de vol, tableur pour manifestes.',
            'Initiation aux progiciels de gestion des départs (DCS - Departure Control System) et d\'enregistrement.',
            'Messagerie professionnelle sécurisée, encodage des messages télex IATA (LDM, CPM, PSM).'
        ],
        'materiel': 'Salle informatique connectée, postes équipés de simulateurs DCS et suites bureautiques.',
        'evaluation': 'Épreuve de fin de module pratique (EFCF) sur simulateur : Traitement d\'un vol et édition du manifeste (sur 20).'
    },
    {
        'code': 'M03', 'titre': 'Communication Professionnelle en Français', 'vh': '120 h (Théorie: 30h | Pratique: 80h | Éval: 10h)',
        'periode': '1ère Année – Semestre 1', 'formateurs': 'Mme Imane Mziouad',
        'competence': 'Communiquer avec clarté, aisance et courtoisie en langue française dans l\'ensemble des situations de bord et d\'escale.',
        'elements': [
            'Techniques de pose de voix, articulation, élocution et diction devant passagers.',
            'Lecture irréprochable des annonces de bord officielles (embarquement, sécurité, turbulences, atterrissage).',
            'Rédaction technique et administrative : rapports de vol (Cabin Log), comptes-rendus d\'anomalies et d\'incidents.'
        ],
        'materiel': 'Microphone, sono cabine, enregistreur audio pour débriefing phonétique, livrets d\'annonces de bord.',
        'evaluation': 'Épreuve certificative orale (simulation d\'annonces) et écrite (rapport d\'incident) (EFCF sur 20).'
    },
    {
        'code': 'M04', 'titre': 'Environnement Professionnel Aéronautique & Maritime', 'vh': '180 h (Théorie: 120h | Pratique: 48h | Éval: 12h)',
        'periode': '1ère Année – Semestres 1 et 2', 'formateurs': 'Mme Aziza Jouaidi',
        'competence': 'Maîtriser les contextes géopolitiques, techniques, réglementaires et institutionnels du transport mondial.',
        'elements': [
            'Géographie des transports : codes IATA des aéroports, ports mondiaux, fuseaux horaires et calcul de temps de vol.',
            'Connaissance des aéronefs (monocouloir, gros-porteurs) et navires (liners de croisière, car-ferries).',
            'Réglementation internationale (OACI, OMI, conventions de Varsovie/Montréal, droit maritime et aérien).'
        ],
        'materiel': 'Cartes aéronautiques/maritimes, maquettes d\'aéronefs, guides officiels des fuseaux horaires (OAG).',
        'evaluation': 'Contrôle continu écrit (CC1) et épreuve de synthèse de fin de module (EFCF sur 20).'
    },
    {
        'code': 'M05', 'titre': 'Comportements et Attitudes Professionnels', 'vh': '60 h (Théorie: 15h | Pratique: 40h | Éval: 5h)',
        'periode': '1ère Année – Semestre 1', 'formateurs': 'Mme Aziza Jouaidi / Mme Imane Mziouad',
        'competence': 'Intégrer les standards d\'excellence d\'image de marque, d\'éthique professionnelle et de gestion de soi.',
        'elements': [
            'Normes strictes de présentation physique (grooming) : coiffure, maquillage, maintien, port de l\'uniforme réglementaire.',
            'Gestion de la fatigue, des décalages horaires (jet lag) et hygiène de vie du navigant.',
            'Travail en équipage, synergie de groupe et principes du CRM (Crew Resource Management).'
        ],
        'materiel': 'Miroirs professionnels, vestiaires d\'application, guides de toilettage des grandes compagnies.',
        'evaluation': 'Évaluation continue des attitudes professionnelles et mise en situation réelle notée (sur 20).'
    },
    {
        'code': 'M06-1', 'titre': 'Communication en Anglais (1ère Année)', 'vh': '75 h (Théorie: 20h | Pratique: 50h | Éval: 5h)',
        'periode': '1ère Année – Semestres 1 et 2', 'formateurs': 'M. Tareq Echfira / M. Ahmed Benjaa',
        'competence': 'Communiquer couramment en langue anglaise lors des opérations usuelles au sol et à bord.',
        'elements': [
            'Vocabulaire technique d\'aviation et de navigation maritime en anglais.',
            'Annonces standard de cabine en anglais (Pre-boarding, safety demonstration, in-flight service, descent).',
            'Compréhension et formulation de consignes d\'accueil, d\'orientation et de confort aux passagers anglophones.'
        ],
        'materiel': 'Laboratoire audio de langues, casques multimédia, enregistrements authentiques d\'annonces internationales.',
        'evaluation': 'Épreuve orale individuelle devant jury (EFCF Année 1) : Jeu de rôle en cabine et lecture d\'annonces (sur 20).'
    },
    {
        'code': 'M07', 'titre': 'Approche Client et Accueil Passagers', 'vh': '60 h (Théorie: 15h | Pratique: 40h | Éval: 5h)',
        'periode': '1ère Année – Semestre 1', 'formateurs': 'Mme Ilham Eddriouich / Mme Imane Mziouad',
        'competence': 'Conduire les démarches d\'accueil et de service avec une posture axée sur l\'excellence relationnelle.',
        'elements': [
            'Psychologie du voyageur : accueil personnalisé, écoute active, empathie et détection des besoins.',
            'Prise en charge des passagers à particularités (PMR, enfants non accompagnés UM, VIP, passagers anxieux).',
            'Protocoles d\'accueil haut de gamme en Première Classe et Classe Affaires.'
        ],
        'materiel': 'Plateau cabine de simulation, fauteuils roulants pour simulation PMR, pochettes documents UM.',
        'evaluation': 'Épreuve pratique sous forme de jeu de rôle : Accueil d\'un passager VIP et assistance à un passager PMR (sur 20).'
    },
    {
        'code': 'M08', 'titre': 'Interaction en Situations Professionnelles & Conflits', 'vh': '75 h (Théorie: 20h | Pratique: 50h | Éval: 5h)',
        'periode': '1ère Année – Semestre 1', 'formateurs': 'M. Ahmed Benjaa',
        'competence': 'Gérer les situations relationnelles tendues, les litiges et l\'indiscipline des passagers avec sang-froid.',
        'elements': [
            'Analyse transactionnelle et techniques de désamorçage de l\'agressivité verbale.',
            'Traitement des réclamations : retards, pertes de correspondances, surclassements, pannes de divertissement.',
            'Gestion des passagers indisciplinés ou perturbateurs (Unruly Passengers) selon les échelons de danger ICAO.'
        ],
        'materiel': 'Caméra vidéo pour captation des simulations, grilles d\'analyse comportementale.',
        'evaluation': 'Épreuve de fin de module certificative (EFCF) : Simulation de désamorçage de crise à bord (sur 20).'
    },
    {
        'code': 'M09', 'titre': 'Mesures de Sûreté (Réglementation OACI / ISPS)', 'vh': '45 h (Théorie: 25h | Pratique: 15h | Éval: 5h)',
        'periode': '1ère Année – Semestre 1', 'formateurs': 'M. Rachid El Sabah',
        'competence': 'Appliquer rigoureusement la réglementation de sûreté préventive contre les actes d\'intervention illicite.',
        'elements': [
            'Historique et réglementation internationale : Annexe 17 OACI, Code ISPS maritime, Programme National de Sûreté.',
            'Contrôle d\'accès, badges aéroportuaires/portuaires, inspection filtrage des personnes et des bagages.',
            'Fouille et vérification de sûreté de l\'aéronef et du navire (Security Search), gestion des bagages non accompagnés.'
        ],
        'materiel': 'Détecteur de métaux manuel, scellés de sécurité, maquette didactique des zones sensibles de cabine.',
        'evaluation': 'Épreuve finale écrite et pratique (EFCF) : Procédure de fouille cabine et QCM de sûreté réglementaire (sur 20).'
    },
    {
        'code': 'M10', 'titre': 'Marchandises Dangereuses (IATA DGR / Code IMDG)', 'vh': '45 h (Théorie: 25h | Pratique: 15h | Éval: 5h)',
        'periode': '1ère Année – Semestre 2', 'formateurs': 'M. Rachid El Sabah',
        'competence': 'Identifier les marchandises dangereuses, vérifier leur conformité et réagir aux incidents en cabine.',
        'elements': [
            'Les 9 classes de marchandises dangereuses IATA / OMI et leurs étiquettes normalisées.',
            'Articles acceptables ou interdits dans les bagages de cabine et de soute (batteries lithium, aérosols, etc.).',
            'Procédures d\'urgence en cabine en cas de déversement, feu chimique ou fuite toxique.'
        ],
        'materiel': 'Kits d\'étiquettes IATA DGR, boîte à gants et kit d\'intervention incident marchandises dangereuses.',
        'evaluation': 'Épreuve finale théorique certificative EFCF (norme IATA Catégorie 11/12 - Personnel de bord) (sur 20).'
    },
    {
        'code': 'M11', 'titre': 'Procédures de Pré-départ & Armement Cabine', 'vh': '60 h (Théorie: 15h | Pratique: 40h | Éval: 5h)',
        'periode': '1ère Année – Semestre 2', 'formateurs': 'Mme Aziza Jouaidi',
        'competence': 'Réaliser l\'ensemble des contrôles pré-vol/pré-traversée et s\'assurer de la préparation optimale de la cabine.',
        'elements': [
            'Briefing d\'équipage (Pre-flight briefing) : répartition des postes, mots de passe, particularités du vol.',
            'Vérification des équipements de sécurité et de secours (Pre-flight safety check) à chaque poste affecté.',
            'Contrôle de l\'armement hôtelier (Catering) : galleys, trolleys scellés, eau potable, trousses de confort.'
        ],
        'materiel': 'Mock-up cabine équipée, check-lists de sécurité réglementaires, armoires galley et chariots de service.',
        'evaluation': 'Épreuve certificative pratique (EFCF) : Conduite d\'un check de sécurité pré-vol sans omission (sur 20).'
    },
    {
        'code': 'M12', 'titre': 'Embarquement et Départ Passagers', 'vh': '60 h (Théorie: 15h | Pratique: 40h | Éval: 5h)',
        'periode': '1ère Année – Semestre 2', 'formateurs': 'Mme Ilham Eddriouich',
        'competence': 'Gérer les opérations d\'embarquement, l\'installation en cabine et les procédures de départ en sécurité.',
        'elements': [
            'Contrôle des cartes d\'accès à bord, vérification de concordances et comptage des passagers (Head count).',
            'Gestion des coffres à bagages (Overhead bins), respect de la politique des bagages de cabine.',
            'Fermeture et sécurisation des portes cabine, armement des toboggans d\'évacuation (Arming slides).',
            'Démonstration des équipements de secours (Safety demonstration) en coordination avec le cockpit.'
        ],
        'materiel': 'Porte cabine d\'entraînement avec levier d\'armement, ceintures de démonstration, masques et gilets.',
        'evaluation': 'Épreuve finale pratique en simulateur : Exécution complète de la séquence d\'embarquement et safety demo (sur 20).'
    },
    {
        'code': 'M13', 'titre': 'Stage 1 : Immersion Professionnelle (120 h)', 'vh': '120 h (Immersion entreprise: 110h | Rapport & Bilan: 10h)',
        'periode': '1ère Année – Avril 2027 (4 semaines)', 'formateurs': 'Commission de Suivi ATAM & Tuteurs Entreprises',
        'competence': 'Mettre en pratique les acquis de base d\'accueil, d\'orientation et d\'assistance dans un environnement opérationnel réel.',
        'elements': [
            'Immersion au sein des aéroports (escales, salons VIP, portes d\'embarquement) ou gares maritimes.',
            'Pratique des relations avec les usagers, gestion des flux de passagers et orientation multilingue.',
            'Observation de l\'organisation du travail en équipe et respect des consignes de sûreté de zone réservée.'
        ],
        'materiel': 'Convention tripartite d\'immersion, livret individuel de stage, badge d\'accès temporaire stagiaire.',
        'evaluation': 'Note d\'évaluation du tuteur d\'entreprise (60%) + Rapport de stage et soutenance orale (40%) (sur 20).'
    },
    {
        'code': 'M14', 'titre': 'Premiers Secours & Secourisme (RCP / DAE)', 'vh': '165 h (Théorie: 45h | Pratique: 110h | Éval: 10h)',
        'periode': '2ème Année – Semestres 3 et 4', 'formateurs': 'Mme Aziza Jouaidi',
        'competence': 'Dispenser les premiers secours d\'urgence et pratiquer la réanimation cardio-pulmonaire à bord.',
        'elements': [
            'Prise en charge des urgences vitales : obstruction des voies aériennes, hémorragies, perte de conscience.',
            'Réanimation Cardio-Pulmonaire (RCP) adulte, enfant et nourrisson avec utilisation du Défibrillateur (DAE).',
            'Urgences médicales spécifiques au milieu aérien et maritime : hypoxie, barotraumatismes, mal de mer, hyperventilation.',
            'Prise en charge d\'un accouchement inopiné à bord, brûlures et fractures, utilisation de la trousse médicale d\'urgence.'
        ],
        'materiel': 'Mannequins RCP connectés (adulte/enfant/bébé), DAE de formation, trousse Doctor Kit et First Aid Kit.',
        'evaluation': 'Épreuve pratique certificative standardisée (EFCF) : Cas d\'arrêt cardio-respiratoire et cas de malaise grave (sur 20).'
    },
    {
        'code': 'M15', 'titre': 'Communication en Espagnol Professionnel', 'vh': '90 h (Théorie: 25h | Pratique: 60h | Éval: 5h)',
        'periode': '2ème Année – Semestre 3', 'formateurs': 'Mme Imane Mziouad',
        'competence': 'Communiquer en espagnol avec les passagers hispanophones lors des traversées maritimes et vols internationaux.',
        'elements': [
            'Vocabulaire fondamental d\'accueil, de guidage et d\'information touristique en langue espagnole.',
            'Diffusion d\'annonces de bord courantes et de confort en espagnol.',
            'Traitement des demandes des passagers, des incidents de confort et des consignes simples en espagnol.'
        ],
        'materiel': 'Manuels de conversation appliquée, supports audiovisuels en espagnol maritime et aérien.',
        'evaluation': 'Épreuve orale de fin de module (EFCF) : Dialogue de prise en charge et lecture d\'annonces en espagnol (sur 20).'
    },
    {
        'code': 'M16', 'titre': 'Service durant la Croisière & Hôtellerie Maritime', 'vh': '120 h (Théorie: 30h | Pratique: 80h | Éval: 10h)',
        'periode': '2ème Année – Semestre 3', 'formateurs': 'Mme Ilham Eddriouich',
        'competence': 'Assurer l\'organisation des prestations d\'hébergement, de restauration et d\'animation à bord des navires.',
        'elements': [
            'Organisation de la vie à bord d\'un navire de croisière : cabines, restaurants, salons, ponts promenade.',
            'Techniques de service à table, dressage, service des boissons et règles strictes d\'hygiène alimentaire (HACCP).',
            'Coordination avec la réception de bord (Purser\'s office) et encadrement des activités récréatives en escale.'
        ],
        'materiel': 'Espace d\'application hôtelier, vaisselle et nappage de bord, trolleys de service cabine.',
        'evaluation': 'Épreuve pratique certificative (EFCF) : Organisation d\'un service de restauration en milieu confiné (sur 20).'
    },
    {
        'code': 'M17', 'titre': 'Vente de Produits à Bord (Boutique Duty Free)', 'vh': '60 h (Théorie: 15h | Pratique: 40h | Éval: 5h)',
        'periode': '2ème Année – Semestre 3', 'formateurs': 'M. Ahmed Benjaa',
        'competence': 'Promouvoir et commercialiser les articles hors-taxes en cabine et gérer la trésorerie associée.',
        'elements': [
            'Techniques de vente suggestive, argumentation commerciale des parfums, cosmétiques, tabacs et alcools.',
            'Gestion des caisses multidevises, calcul des taux de change, encaissement par cartes bancaires (TPE embarqués).',
            'Contrôle des stocks scellés, inventaire de début et de fin de service, réglementation douanière des franchises.'
        ],
        'materiel': 'Trolley boutique hors-taxes, fausses devises (EUR, USD, MAD), terminal de paiement TPE de formation.',
        'evaluation': 'Épreuve pratique certificative (EFCF) : Simulation d\'un cycle complet de vente duty free et inventaire (sur 20).'
    },
    {
        'code': 'M18', 'titre': 'Procédures d\'Urgence Aériennes & Sauvetage', 'vh': '90 h (Théorie: 30h | Pratique: 55h | Éval: 5h)',
        'periode': '2ème Année – Semestres 3 et 4', 'formateurs': 'M. Rachid El Sabah / Mme Ilham Eddriouich',
        'competence': 'Gérer les situations d\'urgence critique à bord d\'un aéronef et coordonner l\'évacuation rapide des occupants.',
        'elements': [
            'Dépressurisation cabine lente et explosive : utilisation de l\'oxygène fixe et portable, descente d\'urgence.',
            'Lutte contre le feu et la fumée : localisation, extincteurs Halon et eau, cagoule respiratoire de protection (PBE).',
            'Atterrissage forcé et amerrissage (Ditching) : préparation cabine en 30 secondes et 15 minutes.',
            'Évacuation d\'urgence (90 secondes) : commandes vocales standardisées (Shouting orders), gestion des sorties de secours.'
        ],
        'materiel': 'Simulateur cabine d\'évacuation, portes de type I et issues sur aile, extincteurs de formation, cagoules PBE.',
        'evaluation': 'Épreuve pratique d\'urgence (EFCF) : Simulation d\'évacuation avec feux cabine et commandes vocales (sur 20).'
    },
    {
        'code': 'M19', 'titre': 'Procédures d\'Urgence Maritimes (Sécurité SOLAS)', 'vh': '90 h (Théorie: 30h | Pratique: 55h | Éval: 5h)',
        'periode': '2ème Année – Semestre 4', 'formateurs': 'M. Rachid El Sabah',
        'competence': 'Appliquer les règles de sécurité maritime internationale et conduire les manœuvres d\'abandon de navire.',
        'elements': [
            'Convention SOLAS et Code STCW : organisation de la sécurité à bord, rôle d\'appel et signaux d\'alarme généraux.',
            'Utilisation des engins de sauvetage individuels : gilets de sauvetage SOLAS, combinaisons d\'immersion thermique.',
            'Mise à l\'eau et embarquement dans les radeaux pneumatiques et embarcations de sauvetage.',
            'Techniques de survie en mer, prévention de l\'hypothermie, utilisation des fusées de détresse et balises EPIRB.'
        ],
        'materiel': 'Gilets SOLAS, combinaisons de survie, radeau pneumatique de démonstration, signaux pyrotechniques inertes.',
        'evaluation': 'Épreuve théorique et pratique de fin de module (EFCF) : Exercice d\'abandon de navire et QCM SOLAS (sur 20).'
    },
    {
        'code': 'M20', 'titre': 'Arrivée et Débarquement Passagers', 'vh': '90 h (Théorie: 20h | Pratique: 65h | Éval: 5h)',
        'periode': '2ème Année – Semestre 3', 'formateurs': 'Mme Ilham Eddriouich',
        'competence': 'Organiser et sécuriser les phases d\'arrivée, de débarquement des passagers et de restitution de cabine.',
        'elements': [
            'Préparation de la cabine pour l\'approche et l\'atterrissage / accostage : vérifications des sièges, ceintures, galleys.',
            'Désarmement coordonné des toboggans aux ordres du Chef de Cabine (Disarming doors and cross check).',
            'Débarquement ordonné, assistance prioritaire aux passagers PMR et enfants non accompagnés.',
            'Vérification finale de cabine : recherche d\'objets oubliés (Lost & Found), inspection de sûreté post-vol.'
        ],
        'materiel': 'Plateau cabine, matériel de consignation d\'objets trouvés, formulaires de transmission de bord.',
        'evaluation': 'Épreuve pratique certificative (EFCF) : Gestion complète de la séquence d\'arrivée et débarquement (sur 20).'
    },
    {
        'code': 'M21', 'titre': 'Techniques de Recherche d\'Emploi & Assessment', 'vh': '30 h (Théorie: 10h | Pratique: 18h | Éval: 2h)',
        'periode': '2ème Année – Semestre 3', 'formateurs': 'M. Tareq Echfira / M. Ahmed Benjaa',
        'competence': 'Déployer une stratégie de valorisation professionnelle et réussir les épreuves de sélection des compagnies.',
        'elements': [
            'Conception d\'un CV et portfolio aéronautique/maritime conforme aux normes internationales (photos de plein pied/portrait).',
            'Préparation aux sessions de recrutement (Open Days, Assessment Centers) des compagnies aériennes et croisiéristes.',
            'Simulations d\'entretiens individuels en anglais et français, tests psychométriques et dynamique de groupe.'
        ],
        'materiel': 'Studio vidéo d\'entraînement aux entretiens, grilles d\'évaluation des compétences des compagnies majeures.',
        'evaluation': 'Simulation certificative d\'entretien d\'embauche complet (Assessment Center) devant jury (sur 20).'
    },
    {
        'code': 'M06-2', 'titre': 'Communication en Anglais (2ème Année - Approfondissement)', 'vh': '75 h (Théorie: 20h | Pratique: 50h | Éval: 5h)',
        'periode': '2ème Année – Semestre 4', 'formateurs': 'M. Ahmed Benjaa / M. Abdelouahed Bouih',
        'competence': 'Maîtriser l\'anglais aéronautique et maritime d\'urgence et interagir avec autorité et fluidité.',
        'elements': [
            'Gestion linguistique des urgences vitales : Emergency shouting orders (Brace for impact, Open seatbelts, Evacuate).',
            'Interaction fluide lors des incidents médicaux à bord et communication avec les passagers angoissés.',
            'Préparation aux tests d\'anglais standardisés requis par les compagnies internationales (TOEIC / tests internes).'
        ],
        'materiel': 'Supports audio d\'urgences réelles, simulateur phonétique, banques d\'exercices d\'anglais de spécialité.',
        'evaluation': 'Épreuve certificative finale d\'anglais (EFCF Diplômante) : Écrit technique et simulation d\'urgence orale (sur 20).'
    },
    {
        'code': 'M22', 'titre': 'Stage 2 : Intégration en Milieu de Travail & Soutenance (120 h)', 'vh': '120 h (Immersion entreprise: 100h | Mémoire & Soutenance: 20h)',
        'periode': '2ème Année – Avril à Juin 2028 (4 semaines)', 'formateurs': 'Jury Mixte & Tuteurs Entreprises Partenaires',
        'competence': 'Démontrer l\'intégration autonome et complète de l\'ensemble des compétences du métier d\'agent de bord.',
        'elements': [
            'Stage d\'application professionnelle en compagnie aérienne, maritime ou société d\'assistance aéroportuaire (handling).',
            'Participation effective aux opérations commerciales, d\'embarquement, d\'accueil à bord ou de gestion d\'escale.',
            'Rédaction d\'un Mémoire Professionnel de Fin d\'Études portant sur une problématique opérationnelle vécue.',
            'Soutenance solennelle orale de 30 minutes devant un jury mixte (pédagogique et professionnel).'
        ],
        'materiel': 'Convention officielle de stage de fin d\'études, guide de rédaction du mémoire, grille d\'évaluation du jury.',
        'evaluation': 'Évaluation par le tuteur de stage (40%) + Mémoire écrit (30%) + Soutenance orale devant jury mixte (30%) (sur 20).'
    },
]

# Timetables
TIMETABLE_Y1 = [
    ("Lundi",    "M01 Métier / M04 Env. pro / M05 Comportements / M11 Pré-départ",
                 "M05 Comportements / M07 Approche client / M03 Français pro", "–"),
    ("Mardi",    "M04 Env. pro / M08 Interaction pro / M10 Marchandises / M02 Informatique",
                 "M08 Interaction / M03 Français pro / M11 Pré-départ cabine", "–"),
    ("Mercredi", "M04 Env. pro / M09 Sûreté (OACI) / M06-1 Anglais pro",
                 "M08 Interaction / M03 Français pro / M12 Embarquement passagers", "–"),
    ("Jeudi",    "M04 Env. pro / M10 Marchandises / M02 Informatique",
                 "M08 Interaction / M03 Français pro / M12 Embarquement passagers", "–"),
    ("Vendredi", "M04 Env. pro / M09 Sûreté (OACI) / M06-1 Anglais pro",
                 "M05 Comportements / M07 Approche client / M03 Français pro", "–"),
    ("Samedi",   "–", "–", "Contrôles Continus (CC) & Épreuves de Fin de Module (EFCF) M01 à M12"),
]

TIMETABLE_Y2 = [
    ("Lundi",    "M15 Espagnol pro / M16 Croisière / M14 Secourisme & RCP",
                 "M17 Vente Duty Free / M20 Débarquement / M18 Urgences Aériennes", "–"),
    ("Mardi",    "M15 Espagnol pro / M16 Croisière / M14 Secourisme & RCP",
                 "M17 Vente Duty Free / M21 Recherche Emploi / M19 Urgences Maritimes", "–"),
    ("Mercredi", "M15 Espagnol pro / M16 Croisière / M06-2 Anglais 2",
                 "M17 Vente Duty Free / M20 Débarquement / M18 Urgences Aériennes", "–"),
    ("Jeudi",    "M15 Espagnol pro / M16 Croisière / M14 Secourisme & RCP",
                 "M17 Vente Duty Free / M21 Recherche Emploi / M19 Urgences Maritimes", "–"),
    ("Vendredi", "M15 Espagnol pro / M16 Croisière / M06-2 Anglais 2",
                 "M17 Vente Duty Free / M20 Débarquement / M18 Urgences Aériennes", "–"),
    ("Samedi",   "–", "–", "Contrôles Continus (CC) & Épreuves de Fin de Module (EFCF) M14 à M21"),
]

# Official 21 Evaluations
EVALUATIONS = [
    ("M05",   "CC1 Sommatif",    "Samedi 01 Août 2026",          "09h00 – 12h00", "Mme Aziza Jouaidi",                   "Comportements et attitudes professionnels"),
    ("M07",   "CC1 Sommatif",    "Vendredi 18 Septembre 2026",    "13h00 – 16h00", "Mme Ilham Eddriouich",               "Approche client et accueil passagers"),
    ("M08",   "EFCF Final",      "Vendredi 18 Septembre 2026",    "09h00 – 12h00", "M. Ahmed Benjaa",                    "Interaction en situations professionnelles"),
    ("M04",   "CC1 / EFCF",      "Vendredi 04 Décembre 2026",    "11h00 – 13h00", "Mme Aziza Jouaidi",                   "Environnement professionnel aéronautique & maritime"),
    ("M03",   "EFCF Final",      "Mardi 15 Décembre 2026",       "09h00 – 11h00", "Mme Imane Mziouad",                  "Communication professionnelle en français"),
    ("M09",   "EFCF Final",      "Mercredi 16 Décembre 2026",    "13h00 – 16h00", "M. Rachid El Sabah",                 "Réglementation et mesures de sûreté"),
    ("M10",   "EFCF Final",      "Vendredi 08 Janvier 2027",     "09h00 – 12h00", "M. Rachid El Sabah",                 "Marchandises dangereuses IATA/OACI"),
    ("M11",   "EFCF Pratique",   "Vendredi 22 Janvier 2027",     "09h00 – 12h00", "Mme Aziza Jouaidi",                   "Procédures de pré-départ cabine"),
    ("M12",   "EFCF Final",      "Vendredi 12 Février 2027",     "09h00 – 12h00", "Mme Ilham Eddriouich",               "Embarquement et départ passagers"),
    ("M02",   "EFCF Pratique",   "Vendredi 05 Mars 2027",        "09h00 – 12h00", "M. Rachid El Sabah / M. Bouih",      "Outils informatiques et progiciels de transport"),
    ("M06-1", "EFCF Oral",       "Vendredi 02 Avril 2027",       "09h00 – 12h00", "M. Tareq Echfira / M. Benjaa",       "Communication en anglais (1ère Année)"),
    ("M13",   "Bilan Stage 1",   "Vendredi 23 Avril 2027",       "Journée",        "Tuteurs & Commission ATAM",          "Stage en milieu de travail 1 (120h)"),
    ("M17",   "EFCF Pratique",   "Vendredi 01 Octobre 2027",     "13h00 – 16h00", "M. Ahmed Benjaa",                    "Vente de produits à bord duty free"),
    ("M15",   "EFCF Oral",       "Vendredi 15 Octobre 2027",     "09h00 – 12h00", "Mme Imane Mziouad",                  "Communication en espagnol professionnel"),
    ("M21",   "EFCF Sommatif",   "Vendredi 15 Octobre 2027",     "13h00 – 16h00", "M. Tareq Echfira / M. Benjaa",       "Techniques de recherche d'emploi & Assessment"),
    ("M20",   "EFCF Final",      "Vendredi 26 Novembre 2027",    "13h00 – 16h00", "Mme Ilham Eddriouich",               "Arrivée et débarquement passagers"),
    ("M16",   "EFCF Final",      "Vendredi 17 Décembre 2027",    "09h00 – 12h00", "Mme Ilham Eddriouich",               "Service durant la croisière"),
    ("M18",   "EFCF Pratique",   "Samedi 15 Janvier 2028",       "13h00 – 16h00", "M. El Sabah / Mme Eddriouich",       "Procédures d'urgence aériennes et sauvetage"),
    ("M19",   "EFCF Final",      "Vendredi 04 Février 2028",     "09h00 – 12h00", "M. Rachid El Sabah",                 "Procédures d'urgence maritimes SOLAS"),
    ("M14",   "EFCF Pratique",   "Mardi 15 Mars 2028",           "13h00 – 16h00", "Mme Aziza Jouaidi",                   "Secourisme et réanimation cardio-pulmonaire"),
    ("M06-2", "EFCF Diplôme",    "Vendredi 08 Avril 2028",       "09h00 – 12h00", "M. Benjaa / M. Bouih",               "Communication en anglais (2ème Année)"),
]

# Technical Platforms Equipment
EQUIPMENT_SECTIONS = [
    ("Plateau Simulation Cabine Aérienne (Cabin Mock-up)", [
        "Structure de cabine aéronef reconstituée (Mock-up) avec rangées de sièges passagers et couloir central.",
        "Postes équipage navigant (Jumpseats) équipés de harnais 4 points de sécurité opérationnels.",
        "Coffres à bagages supérieurs (Overhead bins) avec système de fermeture et verrouillage réglementaire.",
        "Module d'interphonie et sono cabine (Public Address System) avec microphone combiné hôtesse.",
        "Porte cabine d'entraînement à l'armement/désarmement (type I) avec levier d'armement de toboggan et pin de sécurité.",
        "Kits de démonstration de sécurité : masques à oxygène passagers, ceintures de rallonge, gilets de sauvetage aéronautiques.",
        "Équipements d'armement galley : chariots de service (trolleys) certifiés ATLAS/KSSU, conteneurs standards de bord scellés.",
        "Matériel d'extinction feu : extincteurs Halon (ou substituts écologiques inertes BCF de formation), extincteurs à eau, cagoules respiratoires anti-fumée (PBE - Protective Breathing Equipment), gants anti-feu en amiante/kevlar."
    ]),
    ("Plateau Sécurité et Sauvetage Maritime (SOLAS / STCW)", [
        "Gilets de sauvetage maritimes approuvés SOLAS avec sifflet, bande rétro-réfléchissante et lampe flash automatique.",
        "Combinaisons d'immersion thermique et de survie en mer (Immersion suits) conformes aux normes OMI.",
        "Radeau de sauvetage pneumatique autogonflable de formation avec tente de protection et trousse de survie intégrée.",
        "Bouées couronnes de sauvetage avec filin et feu à retournement automatique.",
        "Signaux de détresse maritimes inertes de formation : fusées à parachute, feux à main rouges, fumigènes flottants orange.",
        "Matériel de lutte contre les voies d'eau et incendie maritime : lances incendie, raccords storz, haches de sécurité maritimes."
    ]),
    ("Plateau Secourisme Médical et Urgences Vitales (RCP / DAE)", [
        "Mannequins de réanimation cardio-pulmonaire (RCP) haute fidélité adulte avec moniteur de rétroaction de compression.",
        "Mannequins de réanimation pédiatrique (enfant et nourrisson) pour entraînement aux compressions et insufflations.",
        "Défibrillateurs Automatisés Externes (DAE / AED) de formation avec électrodes adultes et pédiatriques et télécommande scénarios.",
        "Bouteilles d'oxygène médical de secours portables avec masques haute concentration et détendeurs.",
        "Trousses médicales réglementaires complètes : First Aid Kit (FAK) et Emergency Medical Kit (Doctor Kit / EMK scellé).",
        "Matériel d'immobilisation : colliers cervicaux multi-tailles, attelles modelables type SAM Splint, couvertures isothermiques de survie."
    ]),
    ("Laboratoire Numérique & Progiciels de Transport Aérien et Maritime", [
        "Parc informatique dédié de 25 postes multimédias connectés en réseau local sécurisé et accès haut débit.",
        "Simulateur de gestion des départs et d'enregistrement des passagers (DCS - Departure Control System de formation).",
        "Logiciel d'initiation aux systèmes globaux de distribution et de réservation (GDS Amadeus / Sabre).",
        "Système de casques micro individuels pour l'entraînement phonétique intensif aux annonces de bord en français, anglais et espagnol.",
        "Fonds documentaire numérique et papier : Manuels d'Opérations de Compagnie (AOM/OM-A), Manuels des Marchandises Dangereuses IATA DGR, Codes Maritimes OMI / SOLAS / MARPOL, dictionnaires aéronautiques bilingues."
    ])
]

# ─── BUILD DOCUMENT FUNCTION ──────────────────────────────────────────────────

def build_master_dossier():
    doc = Document()

    # 1. Page Setup: A4, 1.5 cm margins all around
    section = doc.sections[0]
    section.page_width    = Cm(21.0)
    section.page_height   = Cm(29.7)
    section.left_margin   = Cm(1.5)
    section.right_margin  = Cm(1.5)
    section.top_margin    = Cm(1.5)
    section.bottom_margin = Cm(1.5)

    # Configure Header & Footer
    footer = section.footer
    f_p = footer.paragraphs[0]
    f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    f_run = f_p.add_run(
        f"INFOHAS Rabat — Classeur Pédagogique Maître ATAM (2026–2028)  |  Dossier d'Accréditation DFP"
    )
    f_run.font.name = "Arial"
    f_run.font.size = Pt(7.5)
    f_run.font.color.rgb = RGBColor(0x7F, 0x8C, 0x8D)

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE DE GARDE OFFICIELLE & IDENTIFICATION ÉTABLISSEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    p_gov = doc.add_paragraph()
    p_gov.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_govPr = p_gov._p.get_or_add_pPr()
    sp = OxmlElement('w:spacing'); sp.set(qn('w:before'), '0'); sp.set(qn('w:after'), '40')
    p_govPr.append(sp)

    r_gov = p_gov.add_run(
        "ROYAUME DU MAROC\n"
        "MINISTÈRE DE L'INCLUSION ÉCONOMIQUE, DE LA PETITE ENTREPRISE,\n"
        "DE L'EMPLOI ET DES COMPÉTENCES\n"
        "DIRECTION DE LA FORMATION PROFESSIONNELLE"
    )
    r_gov.font.name = 'Arial'
    r_gov.bold = True
    r_gov.font.size = Pt(8.5)
    r_gov.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

    # Decorative separator bar
    p_bar = doc.add_paragraph()
    p_bar.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_barPr = p_bar._p.get_or_add_pPr()
    sp = OxmlElement('w:spacing'); sp.set(qn('w:before'), '20'); sp.set(qn('w:after'), '40')
    p_barPr.append(sp)
    r_bar = p_bar.add_run("_________________________________________________________________________________")
    r_bar.font.name = 'Arial'; r_bar.bold = True; r_bar.font.size = Pt(8); r_bar.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

    # Major Title
    p_titre = doc.add_paragraph()
    p_titre.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tPr = p_titre._p.get_or_add_pPr()
    sp = OxmlElement('w:spacing'); sp.set(qn('w:before'), '60'); sp.set(qn('w:after'), '30')
    p_tPr.append(sp)
    r_t1 = p_titre.add_run("CLASSEUR PÉDAGOGIQUE MAÎTRE DE LA FILIÈRE\n")
    r_t1.font.name = 'Arial'; r_t1.bold = True; r_t1.font.size = Pt(15); r_t1.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    r_t2 = p_titre.add_run("DOSSIER DE SUIVI PÉDAGOGIQUE & D'ACCRÉDITATION OFFICIELLE\n")
    r_t2.font.name = 'Arial'; r_t2.bold = True; r_t2.font.size = Pt(11); r_t2.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
    r_t3 = p_titre.add_run("RÉFÉRENTIEL CONSOLIDÉ DES 22 MODULES DE FORMATION (M01 À M22)")
    r_t3.font.name = 'Arial'; r_t3.bold = True; r_t3.font.size = Pt(9.5); r_t3.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    # Sub-header details
    p_filiere = doc.add_paragraph()
    p_filiere.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_fPr = p_filiere._p.get_or_add_pPr()
    sp = OxmlElement('w:spacing'); sp.set(qn('w:before'), '40'); sp.set(qn('w:after'), '80')
    p_fPr.append(sp)
    r_f1 = p_filiere.add_run(
        f"FILIÈRE : {SCHOOL_INFO['filiere'].upper()}\n"
        f"NIVEAU : {SCHOOL_INFO['niveau'].upper()}\n"
        f"PROMOTION : {SCHOOL_INFO['promo']}  ({SCHOOL_INFO['annees']})"
    )
    r_f1.font.name = 'Arial'; r_f1.bold = True; r_f1.font.size = Pt(10); r_f1.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

    # Table 0: Identification Signalétique de l'Établissement
    add_heading_2(doc, "FICHE SIGNALÉTIQUE OFFICIELLE DE L'ÉTABLISSEMENT", space_before='60', space_after='40')
    t0 = doc.add_table(rows=6, cols=2)
    t0.style = 'Table Grid'
    set_table_borders(t0, NAVY, 4)
    col_w0 = [5.5, 12.5]
    IDENT_ITEMS = [
        ("Établissement de Formation",  f"{SCHOOL_INFO['raison']} ({SCHOOL_INFO['nom']})"),
        ("Statut Juridique & Agrément", "Établissement Privé de Formation Professionnelle Accrédité par le Ministère"),
        ("Filière Homologuée & Niveau", f"{SCHOOL_INFO['filiere']} — {SCHOOL_INFO['niveau']}"),
        ("Période de la Promotion",     f"Promotion {SCHOOL_INFO['promo']} (1ère Année : 2026/2027 | 2ème Année : 2027/2028)"),
        ("Adresse Géographique & Siège",f"{SCHOOL_INFO['adresse']}"),
        ("Contacts Officiels & Web",    f"Tél : {SCHOOL_INFO['tel']}  |  Courriel : {SCHOOL_INFO['email']}  |  Site Web : {SCHOOL_INFO['site']}"),
    ]
    for idx, (label, val) in enumerate(IDENT_ITEMS):
        row = t0.rows[idx]
        set_row_cant_split(row)
        set_cell_bg(row.cells[0], 'DCE6F1')
        cell_para(row.cells[0], label, font_size=8.5, bold=True, color=NAVY, space_before=30, space_after=30)
        cell_para(row.cells[1], val,   font_size=8.5, bold=False, space_before=30, space_after=30)
    set_col_widths(t0, col_w0)

    # Summary box
    p_desc = doc.add_paragraph()
    p_dPr = p_desc._p.get_or_add_pPr()
    sp = OxmlElement('w:spacing'); sp.set(qn('w:before'), '80'); sp.set(qn('w:after'), '40')
    p_dPr.append(sp)
    r_desc = p_desc.add_run(
        "Ce classeur pédagogique maître constitue le dossier institutionnel d'accréditation et de pilotage "
        "didactique de la filière ATAM au sein de l'institut INFOHAS Rabat. Il regroupe l'ingénierie globale de formation, "
        "la charte déontologique et de grooming, la matrice des compétences APC, le tableau synoptique des 22 modules de formation, "
        "la cartographie didactique détaillée, les emplois du temps de référence, les macro-plannings de réalisation, "
        "le protocole réglementaire et le triptyque d'évaluation des stages, le calendrier officiel des 21 évaluations certificatives, "
        "la procédure de traitement des recours, l'inventaire normatif et la matrice croisée des équipements pédagogiques, "
        "le dispositif d'assurance qualité et de conseil de perfectionnement, ainsi que les visas officiels de gouvernance."
    )
    r_desc.font.name = 'Arial'; r_desc.font.size = Pt(8); r_desc.italic = True; r_desc.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1 : CADRE RÉGLEMENTAIRE & PROFIL PROFESSIONNEL DE LA FILIÈRE
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1(doc, "1", "Cadre Réglementaire, Objectifs de Formation & Profil Métier", page_break=True)

    add_heading_2(doc, "1.1. Contexte Institutionnel et Approche Par Compétences (APC)")
    add_body_p(
        doc,
        "Le programme de formation « Accueil dans les Transports Aérien et Maritime » (ATAM) s'inscrit rigoureusement "
        "dans le cadre de la réforme de la formation professionnelle conduite par le Ministère de tutelle et l'Office de la "
        "Formation Professionnelle et de la Promotion du Travail (OFPPT), avec l'appui des programmes de coopération "
        "(Union Européenne - Projet MEDA) et des représentants institutionnels des secteurs aéronautique et maritime. "
        "La méthodologie d'ingénierie repose intégralement sur l'Approche Par Compétences (APC), garantissant l'adéquation "
        "directe et mesurable entre les enseignements dispensés et les exigences opérationnelles du marché du travail international."
    )

    add_heading_2(doc, "1.2. Profil Métier et Débouchés Professionnels")
    add_body_p(
        doc,
        "Le Technicien ATAM est un professionnel polyvalent de l'accueil, de la sécurité et du service commercial "
        "évoluant à bord des aéronefs, à bord des navires de croisière et car-ferries, ainsi qu'au sein des infrastructures d'escale "
        "(aéroports et terminaux portuaires). Il veille au confort des passagers, garantit leur sécurité conformément aux réglementations "
        "strictes de l'Aviation Civile Internationale (OACI/IATA) et de l'Organisation Maritime Internationale (OMI - Convention SOLAS), "
        "et véhicule l'image de marque de la compagnie qui l'emploie. Les principaux débouchés professionnels ciblés sont :",
        bold_prefix="Champs d'intervention : "
    )

    t_deb = doc.add_table(rows=5, cols=3)
    t_deb.style = 'Table Grid'
    set_table_borders(t_deb, NAVY, 4)
    format_header_row(t_deb, ["Secteur d'Activité", "Métiers & Postes Ciblés", "Principaux Employeurs"],
                      widths_cm=[4.0, 7.5, 6.5], bg_color=NAVY)
    DEBOUCHES = [
        ("Transport Aérien\n(Personnel Navigant)",
         "Hôtesse de l'Air / Steward (PNC - Personnel Navigant Commercial), Chef de Cabine (après promotion).",
         "Compagnies aériennes régulières nationales et internationales (RAM, Emirates, Qatar Airways, Ryanair...), compagnies charter et aviation d'affaires VIP."),
        ("Transport Maritime\n(Personnel Navigant)",
         "Hôte / Hôtesse de bord croisière, Commissaire de bord, Personnel d'accueil et d'animation maritime, Steward de ferry.",
         "Compagnies internationales de croisières maritimes (MSC Croisières, Costa, Royal Caribbean...), compagnies maritimes de car-ferries (AML, FRS, Balearia)."),
        ("Assistance en Escale\n(Services au Sol)",
         "Agent d'escale aéroportuaire, Agent d'accueil et d'embarquement, Agent de comptoir de billetterie, Agent de traitement VIP.",
         "Sociétés de handling aéroportuaire (Swissport, RAM Handling, Dnata), gestionnaires d'aéroports (ONDA), terminaux maritimes."),
        ("Services Touristiques &\nÉvénementiel de Luxe",
         "Chargé d'accueil événementiel international, Coordinateur de transferts VIP, Agent de relations publiques en hôtellerie de transport.",
         "Agences réceptives internationales, gares ferroviaires à grande vitesse, salons VIP et réceptions d'affaires de prestige.")
    ]
    for idx, (sect, posts, empl) in enumerate(DEBOUCHES):
        row = t_deb.rows[idx + 1]
        set_row_cant_split(row)
        if idx % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)
        cell_para(row.cells[0], sect, font_size=8, bold=True, color=NAVY, space_before=25, space_after=25)
        cell_para(row.cells[1], posts, font_size=8, space_before=25, space_after=25)
        cell_para(row.cells[2], empl, font_size=8, space_before=25, space_after=25)
    set_col_widths(t_deb, [4.0, 7.5, 6.5])

    add_heading_2(doc, "1.3. Conditions d'Accès, Sélection et Prérequis Réglementaires")
    add_body_p(
        doc,
        "L'accès à la filière ATAM exige le niveau Baccalauréat (toutes séries) ou équivalent certifié, assorti d'un processus rigoureux "
        "de sélection validant les aptitudes linguistiques (maîtrise du français et de l'anglais), la présentation physique conforme "
        "aux critères de la profession (taille minimale requise par les compagnies, indice de masse corporelle équilibré), une excellente "
        "acuité sensorielle et l'absence de signes distinctifs visibles en uniforme. Une visite médicale d'aptitude physique et mentale "
        "au personnel navigant (délivrée par un médecin agréé de l'aviation civile ou de la médecine maritime) est obligatoire avant l'admission définitive."
    )

    add_heading_2(doc, "1.4. Architecture Globale et Volume Horaire (2040 Heures)")
    add_body_p(
        doc,
        "Le cursus de formation se déploie sur une durée totale de deux années académiques (quatre semestres d'enseignement) "
        "pour un volume global de 2 040 heures de formation réparties équitablement entre enseignements théoriques de base, "
        "ateliers pratiques et mises en situation en cabine simulée, évaluations continues et sommatives, ainsi que 240 heures "
        "de stages obligatoires en milieu de travail professionnel répartis sur les deux années (120 h en 1ère année + 120 h en 2ème année)."
    )

    doc.add_page_break()
    add_heading_2(doc, "1.5. Charte Déontologique, Grooming & Code Vestimentaire Professionnel", space_before='80')
    add_body_p(
        doc,
        "L'exercice des métiers de l'accueil et de la sécurité dans le transport aérien (Personnel Navigant Commercial, agents d'escale) "
        "et maritime (personnel de bord de croisière et ferries) impose une rigueur comportementale, déontologique et vestimentaire absolue. "
        "Le port de l'uniforme officiel d'INFOHAS et le respect scrupuleux des normes de présentation (Grooming) sont obligatoires dès l'entrée dans l'établissement :",
        bold_prefix="Standards d'Excellence : "
    )

    t_groom = doc.add_table(rows=5, cols=3)
    t_groom.style = 'Table Grid'
    set_table_borders(t_groom, NAVY, 4)
    format_header_row(t_groom, ["Axe Déontologique", "Exigences & Normes Professionnelles de Bord", "Règles d'Évaluation & Sanctions"],
                      widths_cm=[4.0, 8.5, 5.5], bg_color=NAVY)
    GROOMING_ITEMS = [
        ("Uniforme Réglementaire\n& Port du Badge",
         "Port obligatoire de la tenue complète de navigant : veste bleu marine cintrée, pantalon droit ou jupe réglementaire (sous le genou), chemisier/chemise blanche repassée, cravate ou foulard noué réglementairement, badge d'identification visible, chaussures de ville en cuir noir cirées (talons de 3 à 5 cm pour hôtesses).",
         "Contrôle journalier d'accès. Tout manquement entraîne l'interdiction d'accès en cabine simulée et une pénalité d'assiduité."),
        ("Grooming, Coiffure\n& Esthétique de Bord",
         "Personnel Féminin : Cheveux relevés en chignon strict avec résille invisible, maquillage sobre et professionnel (teint frais, mascara discret, rouge à lèvres harmonieux), manucure soignée neutre.\nPersonnel Masculin : Coupe courte classique et dégagée, rasage de près quotidien obligatoire (aucune barbe naissante tolérée).",
         "Évaluation hebdomadaire notée dans le cadre du module M05 (Comportements pro). Tolérance zéro pour le négligé."),
        ("Bijoux, Tatouages\n& Signes Distinctifs",
         "Interdiction formelle des piercings visibles, tatouages apparents en uniforme, vernis écaillé ou teintes fantaisies. Tolérance stricte limitée à une montre professionnelle discrète et une bague unique type alliance simple.",
         "Conformité obligatoire avec les règlements de sélection internationale (Compagnies du Golfe, RAM, SkyTeam)."),
        ("Discipline, Ponctualité\n& Règle des 10%",
         "Règle de ponctualité de bord : « Heure de convocation = fermeture des portes ». Tolérance zéro pour les retards en simulation de vol. Le seuil maximal d'absences autorisées est fixé à 10% du volume du module, au-delà duquel l'ajournement aux examens sommatifs (EFCF) est immédiat.",
         "Enregistrement quotidien dans le cahier de texte et rapport hebdomadaire transmis à la Direction Pédagogique.")
    ]
    for idx, (axe, req, sanc) in enumerate(GROOMING_ITEMS):
        row = t_groom.rows[idx + 1]
        set_row_cant_split(row)
        if idx % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)
        cell_para(row.cells[0], axe, font_size=8, bold=True, color=NAVY, space_before=25, space_after=25)
        cell_para(row.cells[1], req, font_size=7.5, space_before=25, space_after=25)
        cell_para(row.cells[2], sanc, font_size=7.5, space_before=25, space_after=25)
    set_col_widths(t_groom, [4.0, 8.5, 5.5])

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2 : COMPOSITION ET HABILITATION DE L'ÉQUIPE PÉDAGOGIQUE
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1(doc, "2", "Composition & Habilitation de l'Équipe Pédagogique", page_break=False)
    add_body_p(
        doc,
        "L'équipe pédagogique d'INFOHAS pour la filière ATAM réunit des formateurs permanents hautement qualifiés, "
        "associant une solide expertise académique à un parcours professionnel approfondi dans les plus prestigieuses compagnies aériennes "
        "(Royal Air Maroc, compagnies internationales du Golfe) et maritimes. Chaque formateur est dûment habilité par la direction "
        "pédagogique conformément aux critères de compétence technique et méthodologique de l'APC."
    )

    t_prof = doc.add_table(rows=len(TRAINERS) + 1, cols=5)
    t_prof.style = 'Table Grid'
    set_table_borders(t_prof, NAVY, 4)
    format_header_row(t_prof, ["Formateur Habilité", "Spécialité & Qualification Professionnelle",
                               "Modules Sous Tutelle", "Statut", "Expérience"],
                      widths_cm=[3.8, 6.8, 3.8, 1.8, 1.8], bg_color=NAVY)

    for i, (name, spec, mods, statut, exp) in enumerate(TRAINERS):
        row = t_prof.rows[i + 1]
        set_row_cant_split(row)
        if i % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)
        cell_para(row.cells[0], name, font_size=8, bold=True, color=NAVY, space_before=25, space_after=25)
        cell_para(row.cells[1], spec, font_size=7.5, space_before=25, space_after=25)
        cell_para(row.cells[2], mods, font_size=7.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=25, space_after=25)
        cell_para(row.cells[3], statut, font_size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=25, space_after=25)
        cell_para(row.cells[4], exp, font_size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=25, space_after=25)
    set_col_widths(t_prof, [3.8, 6.8, 3.8, 1.8, 1.8])

    add_heading_2(doc, "Coordination et Suivi Pédagogique Continu", space_before='80')
    add_body_p(
        doc,
        "La coordination de l'équipe pédagogique est assurée par le Directeur Pédagogique à travers : "
        "(1) Des réunions préparatoires avant chaque rentrée semestrielle pour l'harmonisation des progressions didactiques ; "
        "(2) Le suivi hebdomadaire et le visa systématique des cahiers de texte de chaque module ; "
        "(3) Des conseils pédagogiques de mi-parcours pour le bilan des évaluations formatives et le soutien individualisé des stagiaires ; "
        "(4) Des audits réguliers de conformité des épreuves certificatives avec les référentiels d'évaluation officiels."
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3 : MATRICE APC GLOBALE & TABLEAU SYNOPTIQUE DU PROGRAMME (M01-M22)
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1(doc, "3", "Matrice APC Globale & Tableau Synoptique du Programme (M01 – M22)", page_break=True)
    add_body_p(
        doc,
        "Le tableau synoptique ci-dessous formalise la distribution des 22 unités de formation (modules) constituant l'intégralité "
        "du programme ATAM. Les compétences sont distinguées selon leur nature : Compétence Générale (CG), Compétence Particulière (CP) "
        "et Compétence d'Intégration en milieu professionnel (CI). Les volumes horaires détaillent les heures théoriques, "
        "les heures de travaux pratiques et de simulation, ainsi que les heures d'évaluation certificative."
    )

    t_syn = doc.add_table(rows=len(MODULES_APC) + 2, cols=9)
    t_syn.style = 'Table Grid'
    set_table_borders(t_syn, NAVY, 4)
    format_header_row(t_syn, ["Code", "Intitulé du Module de Formation", "Type", "Période",
                               "Théo.", "Prat.", "Éval.", "Total", "Formateur Responsable"],
                      widths_cm=[1.1, 4.8, 0.9, 2.3, 1.0, 1.0, 1.0, 1.1, 4.8], bg_color=NAVY)

    tot_th = sum(m[4] for m in MODULES_APC)
    tot_pr = sum(m[5] for m in MODULES_APC)
    tot_ev = sum(m[6] for m in MODULES_APC)
    tot_vh = sum(m[7] for m in MODULES_APC)

    for i, (code, titre, ctype, per, th, pr, ev, tot, form) in enumerate(MODULES_APC):
        row = t_syn.rows[i + 1]
        set_row_cant_split(row)
        # Highlight stages and 2nd year
        if "Stage" in titre:
            for c in row.cells: set_cell_bg(c, AMBER_BG)
        elif "2ème" in per:
            for c in row.cells: set_cell_bg(c, GREEN_BG)
        elif i % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)

        cell_para(row.cells[0], code, font_size=7.5, bold=True, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
        cell_para(row.cells[1], titre, font_size=7.5, bold=("Stage" in titre), space_before=20, space_after=20)
        cell_para(row.cells[2], ctype, font_size=7, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
        cell_para(row.cells[3], per, font_size=7, space_before=20, space_after=20)
        cell_para(row.cells[4], str(th), font_size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
        cell_para(row.cells[5], str(pr), font_size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
        cell_para(row.cells[6], str(ev), font_size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
        cell_para(row.cells[7], f"{tot}h", font_size=7.5, bold=True, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
        cell_para(row.cells[8], form, font_size=7, space_before=20, space_after=20)

    # Total Row
    row_tot = t_syn.rows[len(MODULES_APC) + 1]
    set_row_cant_split(row_tot)
    for c in row_tot.cells: set_cell_bg(c, 'DCE6F1')
    cell_para(row_tot.cells[0], "TOTAL", font_size=8, bold=True, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_para(row_tot.cells[1], "VOLUME HORAIRE GLOBAL CONSOLIDÉ (M01 – M22)", font_size=8, bold=True, color=NAVY)
    cell_para(row_tot.cells[2], "–", font_size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_para(row_tot.cells[3], "2 Années", font_size=8, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_para(row_tot.cells[4], f"{tot_th}h", font_size=8, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_para(row_tot.cells[5], f"{tot_pr}h", font_size=8, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_para(row_tot.cells[6], f"{tot_ev}h", font_size=8, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_para(row_tot.cells[7], f"{tot_vh}h", font_size=8.5, bold=True, color=ACCENT_RED, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_para(row_tot.cells[8], "Équipe Pédagogique INFOHAS", font_size=8, bold=True)
    set_col_widths(t_syn, [1.1, 4.8, 0.9, 2.3, 1.0, 1.0, 1.0, 1.1, 4.8])

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4 : CARTOGRAPHIE DIDACTIQUE DÉTAILLÉE DES 22 MODULES (FICHES SYNOPTIQUES)
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1(doc, "4", "Cartographie Didactique Détaillée des 22 Modules de Formation", page_break=True)
    add_body_p(
        doc,
        "Les fiches synoptiques ci-après décrivent l'ingénierie pédagogique opérationnelle de chacun des 22 modules du cursus. "
        "Pour chaque module sont spécifiés : la compétence terminale visée, les éléments de compétence et savoirs clés associés, "
        "les ressources matérielles et équipements mobilisés, ainsi que le dispositif d'évaluation certificative homologué."
    )

    for m_idx, mod in enumerate(MODULE_DETAILS):
        # We group modules gracefully: 2 modules per page or clean cards
        # If it's an even module index after M01, we can add spacing or page breaks
        t_mod = doc.add_table(rows=6, cols=2)
        t_mod.style = 'Table Grid'
        set_table_borders(t_mod, NAVY, 4)
        col_wm = [4.2, 13.8]

        # Row 0: Banner
        r0 = t_mod.rows[0]
        set_row_cant_split(r0)
        r0.cells[0].merge(r0.cells[1])
        set_cell_bg(r0.cells[0], NAVY)
        cell_para(r0.cells[0], f"FICHE MODULE : {mod['code']} — {mod['titre'].upper()}",
                  font_size=9, bold=True, color=HEADER_TXT, space_before=30, space_after=30)

        # Row 1: Identification
        r1 = t_mod.rows[1]
        set_row_cant_split(r1)
        set_cell_bg(r1.cells[0], 'EBF3FB')
        cell_para(r1.cells[0], "Volume Horaire & Période", font_size=7.5, bold=True, color=NAVY)
        cell_para(r1.cells[1], f"{mod['vh']}  |  {mod['periode']}  |  Formateur(s) : {mod['formateurs']}",
                  font_size=7.5, bold=False)

        # Row 2: Compétence Visée
        r2 = t_mod.rows[2]
        set_row_cant_split(r2)
        set_cell_bg(r2.cells[0], 'EBF3FB')
        cell_para(r2.cells[0], "Énoncé de la Compétence", font_size=7.5, bold=True, color=NAVY)
        cell_para(r2.cells[1], mod['competence'], font_size=7.5, italic=True)

        # Row 3: Éléments de Compétence
        r3 = t_mod.rows[3]
        set_row_cant_split(r3)
        set_cell_bg(r3.cells[0], 'EBF3FB')
        cell_para(r3.cells[0], "Éléments de Compétence &\nSavoirs Opérationnels Clés", font_size=7.5, bold=True, color=NAVY)
        r3.cells[1].text = ""
        for elem_idx, elem in enumerate(mod['elements']):
            if elem_idx == 0:
                cell_para(r3.cells[1], f"• {elem}", font_size=7.5, space_before=15, space_after=15)
            else:
                add_cell_extra_para(r3.cells[1], f"• {elem}", font_size=7.5, space_before=10, space_after=15)

        # Row 4: Matériel & Équipements
        r4 = t_mod.rows[4]
        set_row_cant_split(r4)
        set_cell_bg(r4.cells[0], 'EBF3FB')
        cell_para(r4.cells[0], "Plateaux Techniques & Matériel", font_size=7.5, bold=True, color=NAVY)
        cell_para(r4.cells[1], mod['materiel'], font_size=7.5)

        # Row 5: Évaluation Certificative
        r5 = t_mod.rows[5]
        set_row_cant_split(r5)
        set_cell_bg(r5.cells[0], 'EBF3FB')
        cell_para(r5.cells[0], "Modalités d'Évaluation Certificative", font_size=7.5, bold=True, color=NAVY)
        cell_para(r5.cells[1], mod['evaluation'], font_size=7.5, bold=True, color=DEEP_BLUE)

        set_col_widths(t_mod, col_wm)

        # Spacer between cards
        p_sp = doc.add_paragraph()
        p_spPr = p_sp._p.get_or_add_pPr()
        sp = OxmlElement('w:spacing'); sp.set(qn('w:before'), '0'); sp.set(qn('w:after'), '40')
        p_spPr.append(sp)

        # Add page break every 3 modules to keep clean layout
        if (m_idx + 1) % 3 == 0 and m_idx < len(MODULE_DETAILS) - 1:
            doc.add_page_break()

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 5 : EMPLOIS DU TEMPS OFFICIELS & MACRO-PLANNING GANTT (2026–2028)
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1(doc, "5", "Emplois du Temps Officiels & Macro-Planning Annuel (2026 – 2028)", page_break=True)

    add_heading_2(doc, "5.1. Emploi du Temps Hebdomadaire de Référence — 1ère Année (2026 / 2027)")
    add_body_p(
        doc,
        "La grille horaire hebdomadaire de la 1ère année organise 30 heures de cours par semaine, articulées entre séances théoriques "
        "en matinée (09h00–12h00) et ateliers pratiques / mises en situation d'escale et de cabine en après-midi (13h00–16h00). "
        "Les samedis matins sont spécifiquement réservés aux contrôles continus et épreuves sommatives de fin de module."
    )

    t_tt1 = doc.add_table(rows=len(TIMETABLE_Y1) + 1, cols=4)
    t_tt1.style = 'Table Grid'
    set_table_borders(t_tt1, NAVY, 4)
    format_header_row(t_tt1, ["Jour", "Matinée (09h00 – 12h00)", "Après-midi (13h00 – 16h00)", "Samedi (09h00 – 12h00)"],
                      widths_cm=[2.2, 5.8, 5.8, 4.2], bg_color=NAVY)

    for i, (jour, matin, apm, sam) in enumerate(TIMETABLE_Y1):
        row = t_tt1.rows[i + 1]
        set_row_cant_split(row)
        if jour == "Samedi":
            for c in row.cells: set_cell_bg(c, AMBER_BG)
        elif i % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)

        cell_para(row.cells[0], jour, font_size=8, bold=True, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=25, space_after=25)
        cell_para(row.cells[1], matin, font_size=7.5, space_before=25, space_after=25)
        cell_para(row.cells[2], apm,   font_size=7.5, space_before=25, space_after=25)
        cell_para(row.cells[3], sam,   font_size=7.5, space_before=25, space_after=25)
    set_col_widths(t_tt1, [2.2, 5.8, 5.8, 4.2])

    add_heading_2(doc, "5.2. Emploi du Temps Hebdomadaire de Référence — 2ème Année (2027 / 2028)", space_before='100')
    add_body_p(
        doc,
        "L'organisation de la 2ème année intensifie les ateliers de simulation d'urgence (aérienne et maritime), "
        "la formation approfondie au secourisme aéronautique (M14 - 165 h) et la préparation intensive aux recrutements (Assessment Centers)."
    )

    t_tt2 = doc.add_table(rows=len(TIMETABLE_Y2) + 1, cols=4)
    t_tt2.style = 'Table Grid'
    set_table_borders(t_tt2, NAVY, 4)
    format_header_row(t_tt2, ["Jour", "Matinée (09h00 – 12h00)", "Après-midi (13h00 – 16h00)", "Samedi (09h00 – 12h00)"],
                      widths_cm=[2.2, 5.8, 5.8, 4.2], bg_color=NAVY)

    for i, (jour, matin, apm, sam) in enumerate(TIMETABLE_Y2):
        row = t_tt2.rows[i + 1]
        set_row_cant_split(row)
        if jour == "Samedi":
            for c in row.cells: set_cell_bg(c, AMBER_BG)
        elif i % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)

        cell_para(row.cells[0], jour, font_size=8, bold=True, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=25, space_after=25)
        cell_para(row.cells[1], matin, font_size=7.5, space_before=25, space_after=25)
        cell_para(row.cells[2], apm,   font_size=7.5, space_before=25, space_after=25)
        cell_para(row.cells[3], sam,   font_size=7.5, space_before=25, space_after=25)
    set_col_widths(t_tt2, [2.2, 5.8, 5.8, 4.2])

    add_heading_2(doc, "5.3. Macro-Planning Annuel et Chronogramme Gantt de Réalisation Pédagogique", space_before='100')
    add_body_p(
        doc,
        "Le chronogramme annuel ci-dessous récapitule l'ordonnancement séquentiel des modules, des périodes de stage "
        "en entreprise et des sessions d'examens sur les deux années scolaires (2026–2028) :"
    )

    t_gantt = doc.add_table(rows=7, cols=3)
    t_gantt.style = 'Table Grid'
    set_table_borders(t_gantt, NAVY, 4)
    format_header_row(t_gantt, ["Période / Trimestre", "Modules & Activités Pédagogiques Clés", "Objectifs d'Étape / Jalons"],
                      widths_cm=[3.5, 9.5, 5.0], bg_color=NAVY)
    GANTT_ITEMS = [
        ("Année 1 : Trimestre 1\n(Sep – Nov 2026)",
         "M01 Métier, M04 Environnement pro (Partie 1), M05 Comportements, M07 Approche client, M08 Interaction pro, M03 Français, M06-1 Anglais.",
         "Intégration du groupe, maîtrise des attitudes professionnelles et grooming, évaluations CC1 sommatives."),
        ("Année 1 : Trimestre 2\n(Déc 2026 – Fév 2027)",
         "M09 Sûreté (OACI), M10 Marchandises dangereuses, M11 Pré-départ cabine, M12 Embarquement passagers, M04 (Partie 2).",
         "Certifications de sûreté et DGR, maîtrise des checks cabine et safety demo. Épreuves EFCF de mi-parcours."),
        ("Année 1 : Trimestre 3\n(Mar – Juin 2027)",
         "M02 Informatique/DCS, M06-1 Anglais (Oral), M13 STAGE EN MILIEU DE TRAVAIL 1 (Avril 2027 - 120 h). Bilan et remédiation.",
         "Validation du Stage 1, épreuves certificatives fin de 1ère année, Commission de Passage en 2ème année."),
        ("Année 2 : Trimestre 1\n(Sep – Nov 2027)",
         "M15 Espagnol pro, M16 Croisière & hôtellerie maritime, M17 Vente Duty Free, M20 Débarquement, M21 Recherche d'emploi & Assessment.",
         "Ouverture internationale, techniques commerciales, épreuves sommatives EFCF vente et espagnol."),
        ("Année 2 : Trimestre 2\n(Déc 2027 – Mars 2028)",
         "M14 Premiers Secours (RCP/DAE - 165 h), M18 Urgences Aériennes (Evacuation 90s), M19 Urgences Maritimes (SOLAS).",
         "Certifications critiques de sécurité, sauvetage et secourisme. Contrôles pratiques sur plateaux techniques."),
        ("Année 2 : Trimestre 3\n(Avr – Juin 2028)",
         "M06-2 Anglais approfondi, M22 STAGE EN MILIEU DE TRAVAIL 2 (120 h), Rédaction du mémoire, EXAMEN DE FIN DE FORMATION (EFF) & Soutenances.",
         "Diplomation officielle, délibération du Jury Mixte, insertion directe auprès des compagnies partenaires.")
    ]
    for idx, (per, acts, jalons) in enumerate(GANTT_ITEMS):
        row = t_gantt.rows[idx + 1]
        set_row_cant_split(row)
        if "Stage" in acts or "STAGE" in acts:
            for c in row.cells: set_cell_bg(c, AMBER_BG)
        elif idx % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)
        cell_para(row.cells[0], per, font_size=7.5, bold=True, color=NAVY, space_before=20, space_after=20)
        cell_para(row.cells[1], acts, font_size=7.5, space_before=20, space_after=20)
        cell_para(row.cells[2], jalons, font_size=7.5, space_before=20, space_after=20)
    set_col_widths(t_gantt, [3.5, 9.5, 5.0])

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 6 : PROTOCOLE RÉGLEMENTAIRE DES STAGES EN MILIEU PROFESSIONNEL
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1(doc, "6", "Dispositif & Protocole des Stages en Milieu Professionnel", page_break=True)
    add_body_p(
        doc,
        "Les stages en milieu professionnel constituent des composantes obligatoires et incontournables de la certification APC. "
        "Ils sont régis par une convention tripartite officielle (INFOHAS, Entreprise d'accueil, Stagiaire) conforme aux prescriptions "
        "légales de la formation professionnelle au Maroc."
    )

    add_heading_2(doc, "6.1. Objectifs Pédagogiques Comparés des Deux Stages")
    t_stg = doc.add_table(rows=5, cols=3)
    t_stg.style = 'Table Grid'
    set_table_borders(t_stg, NAVY, 4)
    format_header_row(t_stg, ["Paramètre Clé", "Stage 1 : M13 — Immersion Professionnelle",
                               "Stage 2 : M22 — Intégration & Application"],
                      widths_cm=[3.8, 7.1, 7.1], bg_color=NAVY)
    STAGE_SPECS = [
        ("Volume & Période",
         "120 Heures (4 semaines consécutives)\nAvril 2027 (Fin de 1ère Année)",
         "120 Heures (4 semaines consécutives)\nAvril – Mai 2028 (Fin de 2ème Année)"),
        ("Environnement d'Accueil",
         "Aéroports (terminaux d'escale, comptoirs, salons VIP), Gares maritimes, Ports de croisière, Agences de handling.",
         "Compagnies aériennes (vols d'application/observation), compagnies de ferries maritimes, sociétés d'assistance aéroportuaire avancée."),
        ("Objectifs Opérationnels",
         "Observation participative, prise de contact avec les flux réels de passagers, accueil multilingue, orientation, vérification de billets.",
         "Mise en œuvre autonome des procédures d'embarquement, service à bord, gestion de cabine, gestion d'incidents commerciaux, travail en équipage."),
        ("Livrables & Évaluation",
         "• Livret de suivi validé par le tuteur\n• Rapport de stage d'immersion (15 pages)\n• Notation : Tuteur (60%) + Rapport (40%)",
         "• Livret d'évaluation du tuteur d'entreprise\n• Mémoire professionnel de fin d'études (30 pages)\n• Soutenance orale devant Jury Mixte (30 min)")
    ]
    for idx, (param, s1, s2) in enumerate(STAGE_SPECS):
        row = t_stg.rows[idx + 1]
        set_row_cant_split(row)
        if idx % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)
        cell_para(row.cells[0], param, font_size=8, bold=True, color=NAVY, space_before=25, space_after=25)
        cell_para(row.cells[1], s1, font_size=7.5, space_before=25, space_after=25)
        cell_para(row.cells[2], s2, font_size=7.5, space_before=25, space_after=25)
    set_col_widths(t_stg, [3.8, 7.1, 7.1])

    add_heading_2(doc, "6.2. Dispositif de Tutorat et Charte d'Encadrement Tripartite", space_before='80')
    add_body_p(
        doc,
        "Chaque stagiaire bénéficie d'un double encadrement : un Tuteur Professionnel désigné au sein de l'entreprise d'accueil "
        "qui guide et supervise les activités quotidiennes, et un Formateur Référent INFOHAS qui assure le suivi pédagogique, "
        "effectue au moins une visite de contrôle sur site et participe à l'évaluation finale. Le carnet de stage hebdomadaire "
        "consigne les tâches accomplies, les observations du tuteur et l'assiduité du stagiaire."
    )

    add_heading_2(doc, "6.3. Triptyque Opérationnel des Stages & Outils d'Évaluation Standardisés", space_before='80')
    add_body_p(
        doc,
        "L'encadrement et la validation des périodes de stage (Stage M13 d'immersion et Stage M22 d'intégration) reposent "
        "sur un triptyque d'outils didactiques normalisés garantissant la transparence, la rigueur métrologique et la conformité "
        "aux exigences de certification professionnelle :",
        bold_prefix="Dispositif Didactique d'Entreprise : "
    )

    # 1. Grille d'évaluation du tuteur
    add_body_p(
        doc,
        "Ce barème officiel sur 20 points est complété par le tuteur professionnel au terme des 120 heures de stage :",
        bold_prefix="Document 1 — Grille d'Évaluation du Tuteur en Entreprise (Barème /20) : "
    )

    t_tut = doc.add_table(rows=6, cols=4)
    t_tut.style = 'Table Grid'
    set_table_borders(t_tut, NAVY, 4)
    format_header_row(t_tut, ["Critère Évalué", "Éléments Observables & Indicateurs de Performance", "Barème", "Note"],
                      widths_cm=[4.0, 10.5, 1.8, 1.7], bg_color=NAVY)
    TUTEUR_CRIT = [
        ("1. Ponctualité, Assiduité\n& Respect du Règlement",
         "Respect rigoureux des horaires d'équipage/service, assiduité sans faille, respect des règles d'hygiène, sécurité et sûreté.",
         "/ 4 pts", ".... / 4"),
        ("2. Présentation Physique,\nGrooming & Image",
         "Port impeccable de l'uniforme et du badge, coiffure et grooming conformes aux standards de l'entreprise, posture professionnelle digne.",
         "/ 3 pts", ".... / 3"),
        ("3. Rigueur Opérationnelle\n& Procédures de Bord",
         "Exécution fidèle des procédures d'accueil, d'embarquement, de service ou de gestion d'escale ; respect scrupuleux des consignes hiérarchiques.",
         "/ 4 pts", ".... / 4"),
        ("4. Relation Passager,\nCourtoisie & Langues",
         "Sens de l'écoute active, courtoisie constante, prise en charge bienveillante des réclamations, aisance de communication en français et anglais.",
         "/ 5 pts", ".... / 5"),
        ("5. Intégration Équipe\n& Réactivité aux Aléas",
         "Capacité d'adaptation au sein du collectif navigant ou au sol, esprit d'entraide, sang-froid et gestion positive des situations imprévues.",
         "/ 4 pts", ".... / 4"),
    ]
    for idx, (crit, desc, bar, not_val) in enumerate(TUTEUR_CRIT):
        row = t_tut.rows[idx + 1]
        set_row_cant_split(row)
        if idx % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)
        cell_para(row.cells[0], crit, font_size=7.5, bold=True, color=NAVY, space_before=20, space_after=20)
        cell_para(row.cells[1], desc, font_size=7.5, space_before=20, space_after=20)
        cell_para(row.cells[2], bar, font_size=7.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
        cell_para(row.cells[3], not_val, font_size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
    set_col_widths(t_tut, [4.0, 10.5, 1.8, 1.7])

    # 2. Fiche de visite de suivi
    add_body_p(
        doc,
        "Cette fiche consigne le contrôle in situ ou téléphonique effectué par le formateur référent INFOHAS :",
        bold_prefix="Document 2 — Fiche de Visite et de Suivi de Stage en Entreprise : ",
        space_before='60'
    )
    t_vis = doc.add_table(rows=4, cols=2)
    t_vis.style = 'Table Grid'
    set_table_borders(t_vis, NAVY, 4)
    format_header_row(t_vis, ["Rubrique de Suivi Pédagogique", "Modalités & Observations du Formateur Référent"],
                      widths_cm=[5.0, 13.0], bg_color=DEEP_BLUE)
    VISITE_ITEMS = [
        ("Identification & Modalité",
         "Nom Stagiaire : ...................................  |  Entreprise : ...................................\nDate de Visite : ____ / ____ / 202...  |  Modalité : [  ] Visite sur site   [  ] Entretien Tuteur"),
        ("Points d'Étape Pédagogiques",
         "• Adéquation des missions confiées avec le référentiel didactique ATAM : [  ] Conforme   [  ] Partiel\n• Niveau d'intégration au sein de l'équipe opérationnelle : [  ] Excellent   [  ] Satisfaisant   [  ] À renforcer\n• Maîtrise des gestes professionnels observée par le tuteur : [  ] Acquise   [  ] En cours d'acquisition"),
        ("Ajustements & Recommandations",
         "Actions correctives convenues d'un commun accord avec le tuteur de l'entreprise d'accueil pour la suite du stage : ...........................................................................................................................................................\nVisa du Formateur Référent :                                               Visa du Tuteur d'Entreprise :")
    ]
    for idx, (rub, desc) in enumerate(VISITE_ITEMS):
        row = t_vis.rows[idx + 1]
        set_row_cant_split(row)
        if idx % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)
        cell_para(row.cells[0], rub, font_size=7.5, bold=True, color=NAVY, space_before=20, space_after=20)
        cell_para(row.cells[1], desc, font_size=7.5, space_before=20, space_after=20)
    set_col_widths(t_vis, [5.0, 13.0])

    # 3. Grille de soutenance
    add_body_p(
        doc,
        "Grille officielle d'évaluation appliquée par le Jury Mixte lors de la soutenance orale du mémoire de fin d'études (Stage M22) :",
        bold_prefix="Document 3 — Grille d'Évaluation de Soutenance du Mémoire Professionnel (Barème /20) : ",
        space_before='60'
    )
    t_sout = doc.add_table(rows=5, cols=4)
    t_sout.style = 'Table Grid'
    set_table_borders(t_sout, NAVY, 4)
    format_header_row(t_sout, ["Composante d'Évaluation", "Critères d'Appréciation par le Jury Mixte", "Barème", "Note"],
                      widths_cm=[4.0, 10.5, 1.8, 1.7], bg_color=NAVY)
    SOUT_CRIT = [
        ("1. Qualité du Document\nÉcrit (Mémoire)",
         "Structure logique, rigueur méthodologique, clarté rédactionnelle, orthographe, conformité de la bibliographie et des annexes techniques.",
         "/ 5 pts", ".... / 5"),
        ("2. Maîtrise Technique\nde la Problématique",
         "Compréhension approfondie du sujet d'escale ou de bord, pertinence des analyses, propositions d'améliorations opérationnelles réalistes.",
         "/ 6 pts", ".... / 6"),
        ("3. Présentation Orale\n& Dynamisme",
         "Clarté d'élocution, respect du temps imparti (20 min d'exposé), qualité du support visuel (diaporama), posture et aisance scénique.",
         "/ 4 pts", ".... / 4"),
        ("4. Réponses aux Questions\ndu Jury",
         "Pertinence des arguments, sang-froid, capacité d'approfondissement technique face aux professionnels et enseignants du jury.",
         "/ 5 pts", ".... / 5"),
    ]
    for idx, (comp, crit, bar, not_val) in enumerate(SOUT_CRIT):
        row = t_sout.rows[idx + 1]
        set_row_cant_split(row)
        if idx % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)
        cell_para(row.cells[0], comp, font_size=7.5, bold=True, color=NAVY, space_before=20, space_after=20)
        cell_para(row.cells[1], crit, font_size=7.5, space_before=20, space_after=20)
        cell_para(row.cells[2], bar, font_size=7.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
        cell_para(row.cells[3], not_val, font_size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
    set_col_widths(t_sout, [4.0, 10.5, 1.8, 1.7])

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 7 : SYSTÈME D'ÉVALUATION, EXAMENS ET RÉGLEMENTATION DES ÉTUDES
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1(doc, "7", "Dispositif d'Évaluation des Apprentissages & Réglementation des Études", page_break=True)

    add_heading_2(doc, "7.1. Typologie des Évaluations selon l'APC")
    add_body_p(
        doc,
        "Le système d'évaluation d'INFOHAS respecte rigoureusement les normes de la Direction de la Formation Professionnelle : "
        "(1) Évaluations Formatives : menées en continu sans impact certificatif pour réguler les apprentissages ; "
        "(2) Contrôles Continus Sommations (CC) : épreuves périodiques notées sanctionnant les unités d'apprentissage intermédiaires ; "
        "(3) Épreuves de Fin de Module (EFCF) : évaluations certificatives théoriques et/ou pratiques obligatoires sanctionnant l'acquisition "
        "globale de chaque module (seuil d'admissibilité fixé à 10/20) ; "
        "(4) Examen de Fin de Formation (EFF) : examen national/institutionnel synthèse en fin de 2ème année."
    )

    add_heading_2(doc, "7.2. Calendrier Officiel Consolidé des 21 Évaluations Certificatives")
    add_body_p(
        doc,
        "Le tableau officiel ci-dessous consigne les 21 épreuves certificatives (CC & EFCF) programmées pour la promotion 2026–2028 :"
    )

    t_eval = doc.add_table(rows=len(EVALUATIONS) + 1, cols=6)
    t_eval.style = 'Table Grid'
    set_table_borders(t_eval, NAVY, 4)
    format_header_row(t_eval, ["Code", "Nature Épreuve", "Date Officielle", "Horaire",
                               "Formateur Responsable", "Objet & Critère de l'Évaluation"],
                      widths_cm=[1.1, 2.2, 3.4, 2.0, 3.8, 5.5], bg_color=NAVY)

    for i, (mcode, nature, edate, ehor, eform, eobj) in enumerate(EVALUATIONS):
        row = t_eval.rows[i + 1]
        set_row_cant_split(row)
        if "2027" in edate or "2028" in edate:
            set_cell_bg(row.cells[0], GREEN_BG)
        else:
            set_cell_bg(row.cells[0], 'DEEAF1')

        if i % 2 == 1:
            for c in row.cells[1:]: set_cell_bg(c, LIGHT_BG)

        cell_para(row.cells[0], mcode, font_size=8, bold=True, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
        cell_para(row.cells[1], nature, font_size=7.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
        cell_para(row.cells[2], edate, font_size=7.5, space_before=20, space_after=20)
        cell_para(row.cells[3], ehor, font_size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
        cell_para(row.cells[4], eform, font_size=7.5, space_before=20, space_after=20)
        cell_para(row.cells[5], eobj, font_size=7.5, space_before=20, space_after=20)
    set_col_widths(t_eval, [1.1, 2.2, 3.4, 2.0, 3.8, 5.5])

    add_heading_2(doc, "7.3. Règles de Passage en 2ème Année & Diplomation Finale", space_before='80')
    add_body_p(
        doc,
        "• Passage en 2ème Année : La moyenne générale de la 1ère année est calculée à partir des notes de CC, d'EFCF et du stage M13. "
        "Tout stagiaire ayant une moyenne générale >= 10,00 / 20 est admis en 2ème année. Les stagiaires ayant entre 08,00 et 09,99/20 "
        "sont soumis à une session de rattrapage sur les modules non validés (< 10/20). Toute note inférieure à 06/20 dans un module de sécurité "
        "ou de sûreté (M09, M10, M11, M12) est éliminatoire avant rattrapage.\n\n"
        "• Obtention du Diplôme de Technicien ATAM : Le diplôme est conféré aux candidats ayant validé l'ensemble des modules, "
        "effectué les deux stages obligatoires (M13 et M22), soutenu avec succès leur mémoire professionnel et obtenu une moyenne générale "
        "à l'Examen de Fin de Formation (EFF) supérieure ou égale à 10,00 / 20 sans note éliminatoire.\n\n"
        "• Composition du Jury de Délibération : Présidé par le Directeur Pédagogique d'INFOHAS, le jury comprend les 7 formateurs permanents "
        "de la filière ainsi qu'au moins deux représentants professionnels externes (Chef de Cabine RAM, Directeur de station handling)."
    )

    doc.add_page_break()
    add_heading_2(doc, "7.4. Procédure Formalisée de Traitement des Réclamations, Recours & Conservation des Épreuves", space_before='80')
    add_body_p(
        doc,
        "Afin de garantir l'équité totale des évaluations sommatives et de sécuriser les droits académiques des stagiaires, "
        "l'institut INFOHAS applique une procédure officielle de recours gracieux régie par les directives pédagogiques de la DFP :",
        bold_prefix="Garantie d'Équité & Transparence : "
    )

    t_rec = doc.add_table(rows=5, cols=3)
    t_rec.style = 'Table Grid'
    set_table_borders(t_rec, NAVY, 4)
    format_header_row(t_rec, ["Phase de la Procédure", "Dispositions Réglementaires & Délais", "Autorité Responsable"],
                      widths_cm=[4.0, 10.0, 4.0], bg_color=NAVY)
    RECOURS_STEPS = [
        ("1. Dépôt de la Réclamation\n(Délai de 48 heures)",
         "Tout stagiaire contestant une note d'épreuve sommative (CC ou EFCF) dispose d'un délai impératif de 48 heures ouvrables suivant la publication officielle des résultats pour déposer une requête écrite et motivée auprès du secrétariat pédagogique.",
         "Stagiaire / Secrétariat Pédagogique"),
        ("2. Commission d'Arbitrage\nPédagogique",
         "La requête est instruite par une commission paritaire composée du Directeur Pédagogique (président), du Formateur titulaire du module concerné et d'un Formateur référent indépendant extérieur à la discipline pour garantir une totale neutralité.",
         "Direction Pédagogique & Commission d'Arbitrage"),
        ("3. Instruction & Décision\n(Délai de 5 jours)",
         "La commission procède à la vérification matérielle du décompte des points et du barème. En cas de doute légitime, une double correction anonymisée est effectuée. La décision motivée est notifiée par écrit au stagiaire sous 5 jours ouvrables. La décision est souveraine et définitive.",
         "Commission d'Arbitrage Pédagogique"),
        ("4. Archivage Réglementaire\n(Durée légale de 5 ans)",
         "Toutes les copies d'examen (CC et EFCF), épreuves de rattrapage, grilles d'évaluation de soutenance, feuilles d'émargement et procès-verbaux de délibération sont consignés et archivés sous clé pendant une durée obligatoire de cinq (5) ans à la disposition des corps d'inspection de la DFP.",
         "Service des Examens & Archives INFOHAS")
    ]
    for idx, (ph, disp, resp) in enumerate(RECOURS_STEPS):
        row = t_rec.rows[idx + 1]
        set_row_cant_split(row)
        if idx % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)
        cell_para(row.cells[0], ph, font_size=7.5, bold=True, color=NAVY, space_before=20, space_after=20)
        cell_para(row.cells[1], disp, font_size=7.5, space_before=20, space_after=20)
        cell_para(row.cells[2], resp, font_size=7.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=20, space_after=20)
    set_col_widths(t_rec, [4.0, 10.0, 4.0])

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 8 : INVENTAIRE DES ÉQUIPEMENTS PÉDAGOGIQUES ET PLATEAUX TECHNIQUES
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1(doc, "8", "Inventaire Normatif des Équipements & Plateaux Techniques", page_break=True)
    add_body_p(
        doc,
        "Conformément aux directives du Guide d'Organisation Pédagogique et Matérielle (GOPM ATAM) et aux exigences "
        "d'homologation de la Direction de l'Aviation Civile et de la Marine Marchande, l'institut INFOHAS dispose de plateaux techniques "
        "dédiés et d'équipements spécialisés garantissant un entraînement pratique en conditions réelles :"
    )

    for p_title, p_items in EQUIPMENT_SECTIONS:
        add_heading_2(doc, p_title, space_before='60', space_after='30')
        t_eq = doc.add_table(rows=len(p_items) + 1, cols=2)
        t_eq.style = 'Table Grid'
        set_table_borders(t_eq, NAVY, 4)
        format_header_row(t_eq, ["N°", "Désignation & Caractéristiques Techniques du Matériel Réglementaire"],
                          widths_cm=[1.2, 16.8], bg_color=DEEP_BLUE, font_size=8)

        for e_idx, e_desc in enumerate(p_items):
            row = t_eq.rows[e_idx + 1]
            set_row_cant_split(row)
            if e_idx % 2 == 1:
                for c in row.cells: set_cell_bg(c, LIGHT_BG)
            cell_para(row.cells[0], f"{e_idx + 1:02d}", font_size=7.5, bold=True, color=NAVY,
                      align=WD_ALIGN_PARAGRAPH.CENTER, space_before=15, space_after=15)
            cell_para(row.cells[1], e_desc, font_size=7.5, space_before=15, space_after=15)
        set_col_widths(t_eq, [1.2, 16.8])

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 9 : ATTESTATION DE CONFORMITÉ RÉGLEMENTAIRE & VISAS OFFICIELS
    # ═══════════════════════════════════════════════════════════════════════════
    
    add_heading_2(doc, "8.2. Matrice Synoptique de Correspondance Équipements ⟷ Modules du Référentiel Didactique ATAM", space_before='80')
    add_body_p(
        doc,
        "Le tableau synoptique ci-dessous explicite la corrélation didactique directe entre les équipements matériels de nos plateaux "
        "techniques et les compétences opérationnelles développées dans les modules du référentiel APC :",
        bold_prefix="Articulations Didactiques & Pratiques : "
    )

    t_mat = doc.add_table(rows=7, cols=3)
    t_mat.style = 'Table Grid'
    set_table_borders(t_mat, NAVY, 4)
    format_header_row(t_mat, ["Plateau Technique & Matériel", "Modules du Programme Associés", "Travaux Pratiques & Simulations Opérationnelles Conduites"],
                      widths_cm=[4.5, 3.5, 10.0], bg_color=NAVY)
    MATRICE_EQ = [
        ("Maquette Cabine Avion\n(Cabin Mock-up)",
         "M04, M05, M11,\nM12, M16, M20",
         "Armement de cabine, briefing pré-vol, accueil et placement des passagers, service hôtelier à bord (trolleys), démonstrations de sécurité (Safety demo), désarmement des portes et vérifications post-vol."),
        ("Porte d'Évacuation &\nIssues de Secours",
         "M11, M12, M18",
         "Entraînement physique aux manœuvres d'ouverture normale et d'urgence de porte Type I, armement/désarmement des toboggans d'évacuation, simulation d'évacuation d'urgence en 90 secondes."),
        ("Extincteurs, Cagoules PBE\n& Sécurité Incendie",
         "M09, M10, M18",
         "Localisation de feux cabine/toilettes/galley, manipulation des extincteurs Halon et eau de formation, pose de cagoule PBE en moins de 15 secondes, procédures de lutte contre la fumée toxique."),
        ("Mannequins RCP, DAE\n& Oxygène Médical",
         "M14 (Secourisme)",
         "Réanimation cardio-pulmonaire sur mannequin adulte, enfant et nourrisson avec monitoring électronique, pose et délivrance de chocs DAE, administration d'oxygène de secours, prise en charge de malaises de bord."),
        ("Engins de Sauvetage SOLAS\n& Survie Maritime",
         "M18, M19",
         "Capelage des gilets de sauvetage maritimes et combinaisons d'immersion thermique, procédures de mise à l'eau et embarquement en canot de sauvetage, signaux pyrotechniques et exercices de ditching."),
        ("Laboratoire Informatique\n& Simulateurs DCS",
         "M02, M06, M07,\nM08, M12, M21",
         "Simulations d'enregistrement passagers et traitement de vols sur progiciel DCS, gestion de litiges et correspondances, diffusion d'annonces cabine en français, anglais et espagnol au casque."),
    ]
    for idx, (plat, mods, sim) in enumerate(MATRICE_EQ):
        row = t_mat.rows[idx + 1]
        set_row_cant_split(row)
        if idx % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)
        cell_para(row.cells[0], plat, font_size=7.5, bold=True, color=NAVY, space_before=20, space_after=20)
        cell_para(row.cells[1], mods, font_size=7.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, color=DEEP_BLUE, space_before=20, space_after=20)
        cell_para(row.cells[2], sim, font_size=7.5, space_before=20, space_after=20)
    set_col_widths(t_mat, [4.5, 3.5, 10.0])



    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 9 : ASSURANCE QUALITÉ, CONSEIL DE PERFECTIONNEMENT & PILOTAGE DIDACTIQUE
    # ═══════════════════════════════════════════════════════════════════════════
    add_heading_1(doc, "9", "Dispositif d'Assurance Qualité, Conseil de Perfectionnement & Pilotage Didactique", page_break=True)
    add_body_p(
        doc,
        "L'institut INFOHAS inscrit le pilotage de la filière ATAM dans une démarche d'amélioration continue de la qualité, "
        "articulée autour d'un Conseil de Perfectionnement annuel, d'un système semestriel d'évaluation des enseignements par les stagiaires "
        "et d'un Observatoire de suivi de l'insertion professionnelle :",
        bold_prefix="Politique Qualité Institutionnelle : "
    )

    add_heading_2(doc, "9.1. Conseil de Perfectionnement Annuel de la Filière ATAM", space_before='60')
    t_cp = doc.add_table(rows=4, cols=2)
    t_cp.style = 'Table Grid'
    set_table_borders(t_cp, NAVY, 4)
    format_header_row(t_cp, ["Composante Organisationnelle", "Modalités & Dispositions du Conseil de Perfectionnement"],
                      widths_cm=[5.0, 13.0], bg_color=NAVY)
    CP_ITEMS = [
        ("Composition Paritaire",
         "• Direction Générale et Direction Pédagogique d'INFOHAS (Présidence)\n• Formateurs Coordinateurs des pôles cabine, sûreté, secourisme et langues\n• Représentants professionnels externes : Cadres RH & Chefs de cabine (Royal Air Maroc, compagnies du Golfe), Directeurs d'escale aéroportuaire (Swissport, RAM Handling) et représentants des compagnies maritimes."),
        ("Périodicité & Missions",
         "• Réunion plénière annuelle tenue systématiquement en fin d'année académique.\n• Actualisation des contenus didactiques en fonction des évolutions réglementaires internationales (IATA, OACI, OMI) et technologiques (systèmes biométriques d'embarquement, digitalisation de l'accueil).\n• Bilan d'adéquation formation-emploi et validation des investissements en équipements didactiques."),
        ("Livrables Réglementaires",
         "• Procès-verbal officiel du Conseil de Perfectionnement consignant les recommandations.\n• Plan d'actions d'amélioration pédagogique pluriannuel intégré au projet d'établissement.")
    ]
    for idx, (comp, disp) in enumerate(CP_ITEMS):
        row = t_cp.rows[idx + 1]
        set_row_cant_split(row)
        if idx % 2 == 1:
            for c in row.cells: set_cell_bg(c, LIGHT_BG)
        cell_para(row.cells[0], comp, font_size=7.5, bold=True, color=NAVY, space_before=20, space_after=20)
        cell_para(row.cells[1], disp, font_size=7.5, space_before=20, space_after=20)
    set_col_widths(t_cp, [5.0, 13.0])

    add_heading_2(doc, "9.2. Dispositif Semestriel d'Évaluation des Enseignements par les Stagiaires", space_before='60')
    add_body_p(
        doc,
        "À l'issue de chaque semestre de formation, l'ensemble des stagiaires remplit une fiche d'évaluation anonyme et standardisée "
        "portant sur : (1) La clarté pédagogique et la disponibilité des formateurs ; (2) L'adéquation des travaux pratiques et l'état des équipements de simulation ; "
        "(3) L'organisation des évaluations et le respect des plannings ; (4) La qualité de l'encadrement des stages en entreprise. "
        "Les résultats font l'objet d'un traitement statistique formalisé et d'un entretien de régulation avec chaque formateur concerné."
    )

    add_heading_2(doc, "9.3. Observatoire d'Insertion Professionnelle & Suivi des Lauréats", space_before='60')
    add_body_p(
        doc,
        "L'Observatoire d'Insertion Professionnelle d'INFOHAS réalise un suivi rigoureux des lauréats de la filière ATAM à travers :\n"
        "• Des enquêtes systématiques à 6 mois et 12 mois post-diplomation mesurant le taux net d'embauche en compagnie aérienne, maritime et escale.\n"
        "• L'organisation de journées de recrutement exclusives (« Recruitment Days » / Assessment Centers) en partenariat avec les compagnies de transport.\n"
        "• L'animation du réseau actif des anciens lauréats (Alumni INFOHAS) pour faciliter le parrainage professionnel et les opportunités de carrières internationales."
    )


    add_heading_1(doc, "10", "Attestation de Conformité Réglementaire & Visas d'Approbation", page_break=True)

    add_body_p(
        doc,
        "Le présent Classeur Pédagogique Maître de la Filière ATAM pour la Promotion 2026–2028 atteste de la conformité intégrale "
        "des programmes, des plannings, des volumes horaires et des modalités d'évaluation avec le Référentiel de Formation "
        "et les normes d'accréditation édictées par la Direction de la Formation Professionnelle (Ministère de l'Inclusion Économique, "
        "de la Petite Entreprise, de l'Emploi et des Compétences) du Royaume du Maroc."
    )

    # Formal Approval Block
    t_visa = doc.add_table(rows=3, cols=2)
    t_visa.style = 'Table Grid'
    set_table_borders(t_visa, NAVY, 4)
    widths_v = [9.0, 9.0]

    # Row 0: Headers
    format_header_row(t_visa, ["POUR LA DIRECTION GÉNÉRALE DE L'ÉTABLISSEMENT", "POUR LA DIRECTION PÉDAGOGIQUE & JURY PROFESSIONNEL"],
                      widths_cm=widths_v, bg_color=NAVY)

    # Row 1: Directeurs / Représentants
    r1 = t_visa.rows[1]
    set_row_cant_split(r1)
    set_cell_bg(r1.cells[0], 'F2F6FA')
    set_cell_bg(r1.cells[1], 'F2F6FA')
    cell_para(r1.cells[0], "La Direction Générale de l'Institut\nINFOHAS Rabat\n\nNom & Signature :\n\n\n\nDate : ____ / ____ / 2026",
              font_size=8, bold=True, space_before=30, space_after=30)
    cell_para(r1.cells[1], "Le Directeur Pédagogique Général\nINFOHAS Rabat\n\nNom & Signature :\n\n\n\nDate : ____ / ____ / 2026",
              font_size=8, bold=True, space_before=30, space_after=30)

    # Row 2: Equipe pédagogique et professionnels
    r2 = t_visa.rows[2]
    set_row_cant_split(r2)
    set_cell_bg(r2.cells[0], 'FFFFFF')
    set_cell_bg(r2.cells[1], 'FFFFFF')
    cell_para(r2.cells[0], "Représentant de l'Équipe Pédagogique ATAM\nFormateur Coordinateur de Filière\n\nSignature :\n\n\nCachet Officiel de l'Institut :",
              font_size=8, bold=True, space_before=30, space_after=30)
    cell_para(r2.cells[1], "Représentant des Professionnels Partenaires\nCompagnies Aériennes / Maritimes (Jury Mixte)\n\nSignature :\n\n\nVisa de Validation Pédagogique :",
              font_size=8, bold=True, space_before=30, space_after=30)

    set_col_widths(t_visa, widths_v)

    # Save DOCX
    doc.save(OUTPUT_DOCX)
    print(f"[OK] Word document successfully generated: {OUTPUT_DOCX}")
    # Export PDF via Word COM
    try:
        import win32com.client as win32
        word = win32.Dispatch('Word.Application')
        word.Visible = False
        word.DisplayAlerts = False
        w_doc = word.Documents.Open(os.path.abspath(OUTPUT_DOCX))
        page_count = w_doc.ComputeStatistics(2)
        w_doc.SaveAs2(os.path.abspath(OUTPUT_PDF), FileFormat=17)
        w_doc.Close(False)
        word.Quit()
        print(f"[OK] PDF exported ({page_count} pages): {OUTPUT_PDF}")
    except Exception as e:
        print(f"[WARN] PDF export via Word COM failed: {e}")


if __name__ == '__main__':
    build_master_dossier()
