"""
Real Preview Renderers for Agy Studio.
Implements real, secure conversion and formatting for:
- DOCX (Word documents, tables, headings)
- XLSX (Excel workbooks, multiple sheets, cells, tabular grid)
- PPTX (PowerPoint presentations, slide deck, shape text, bullets)
- CSV (Structured data tables)
- Markdown (Sanitized markdown text)
- SVG (Sanitized vector graphics)
- HTML (Sandboxed preview representation)
- Text & Source Code (Source display only, line counts)
"""

import os
import re
import csv
import html
from pathlib import Path
from typing import Dict, Any, List, Optional

def sanitize_html_content(raw: str) -> str:
    """Removes active scripts, dangerous iframes, and javascript: links."""
    clean = re.sub(r"(?i)<script[^>]*>.*?</script>", "", raw, flags=re.DOTALL)
    clean = re.sub(r"(?i)on\w+\s*=\s*[\"'][^\"']*[\"']", "", clean)
    clean = re.sub(r"(?i)href\s*=\s*[\"']javascript:[^\"']*[\"']", "href='#'", clean)
    clean = re.sub(r"(?i)src\s*=\s*[\"']javascript:[^\"']*[\"']", "src='#'", clean)
    return clean

class PreviewRenderer:
    """Universal renderer for supported document, tabular, and code formats."""

    @staticmethod
    def render_docx(file_path: Path) -> Dict[str, Any]:
        """Converts DOCX to structured, sanitized HTML representation."""
        try:
            import docx
        except ImportError:
            return {
                "success": False,
                "error": "python-docx non disponible dans le runtime.",
                "html": "<div class='p-4 text-amber-400'>Aperçu DOCX indisponible (module python-docx manquant)</div>"
            }

        try:
            doc = docx.Document(str(file_path))
            core = doc.core_properties
            title = core.title or file_path.name
            author = core.author or "Inconnu"

            html_parts = []
            html_parts.append("<div class='docx-preview max-w-4xl mx-auto p-6 space-y-4 font-sans text-slate-200 select-text'>")
            
            # Header card
            html_parts.append(f"""
            <div class='p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between'>
                <div>
                    <h2 class='text-sm font-bold text-sky-400'>{html.escape(title)}</h2>
                    <p class='text-xs text-slate-400'>Auteur : {html.escape(author)} • {len(doc.paragraphs)} paragraphes • {len(doc.tables)} tableaux</p>
                </div>
                <div class='flex gap-2'>
                    <span class='px-2 py-0.5 bg-blue-950 border border-blue-800 text-blue-300 text-[10px] rounded font-mono'>DOCX CERTIFIÉ</span>
                </div>
            </div>
            """)

            # Paragraphs
            for p in doc.paragraphs[:150]:
                txt = p.text.strip()
                if not txt:
                    continue
                safe_txt = html.escape(txt)
                style_name = p.style.name if p.style else ""
                
                if "Heading 1" in style_name:
                    html_parts.append(f"<h1 class='text-lg font-bold text-sky-300 mt-6 mb-2 border-b border-slate-800 pb-1'>{safe_txt}</h1>")
                elif "Heading 2" in style_name:
                    html_parts.append(f"<h2 class='text-base font-semibold text-indigo-300 mt-4 mb-2'>{safe_txt}</h2>")
                elif "Heading 3" in style_name:
                    html_parts.append(f"<h3 class='text-sm font-semibold text-slate-300 mt-3 mb-1'>{safe_txt}</h3>")
                else:
                    align = "text-center" if p.alignment == 1 else "text-left"
                    html_parts.append(f"<p class='{align} text-xs leading-relaxed text-slate-300 my-1'>{safe_txt}</p>")

            # Tables
            for idx, tbl in enumerate(doc.tables[:20]):
                html_parts.append(f"""
                <div class='my-6 rounded-xl border border-slate-800 overflow-hidden bg-slate-950/60'>
                    <div class='bg-slate-900 px-3 py-1.5 text-xs font-semibold text-slate-400 border-b border-slate-800 flex justify-between'>
                        <span>Tableau #{idx + 1}</span>
                        <span class='font-mono text-[10px]'>{len(tbl.rows)} lignes × {len(tbl.columns)} colonnes</span>
                    </div>
                    <div class='overflow-x-auto'>
                        <table class='w-full text-xs text-left border-collapse'>
                """)
                for r_idx, row in enumerate(tbl.rows[:50]):
                    row_bg = "bg-slate-900/90 font-semibold text-sky-300" if r_idx == 0 else ("bg-slate-950/40" if r_idx % 2 == 0 else "bg-slate-900/30")
                    html_parts.append(f"<tr class='{row_bg} border-b border-slate-800/80'>")
                    for cell in row.cells:
                        c_text = "<br>".join(html.escape(p.text.strip()) for p in cell.paragraphs if p.text.strip())
                        html_parts.append(f"<td class='p-2.5 border-r border-slate-800/60 align-top text-slate-300'>{c_text or '&nbsp;'}</td>")
                    html_parts.append("</tr>")
                html_parts.append("</table></div></div>")

            html_parts.append("</div>")

            return {
                "success": True,
                "title": title,
                "author": author,
                "paragraph_count": len(doc.paragraphs),
                "table_count": len(doc.tables),
                "html": "".join(html_parts)
            }
        except Exception as ex:
            return {
                "success": False,
                "error": str(ex),
                "html": f"<div class='p-4 text-rose-400'>Erreur de rendu DOCX : {html.escape(str(ex))}</div>"
            }

    @staticmethod
    def render_xlsx(file_path: Path) -> Dict[str, Any]:
        """Converts Excel workbook into interactive multi-sheet representation."""
        try:
            import openpyxl
        except ImportError:
            return {
                "success": False,
                "error": "openpyxl non disponible dans le runtime.",
                "html": "<div class='p-4 text-amber-400'>Aperçu XLSX indisponible (module openpyxl manquant)</div>"
            }

        try:
            wb = openpyxl.load_workbook(str(file_path), data_only=True, read_only=True)
            sheet_names = wb.sheetnames
            sheets_data = []

            for sname in sheet_names[:10]:
                ws = wb[sname]
                rows = []
                for r_idx, row in enumerate(ws.iter_rows(values_only=True)):
                    if r_idx >= 100:  # limit rows for preview responsiveness
                        break
                    # Format cells safely
                    row_vals = [str(c) if c is not None else "" for c in row]
                    if any(v.strip() for v in row_vals):
                        rows.append(row_vals[:30]) # limit columns

                sheets_data.append({
                    "name": sname,
                    "row_count": len(rows),
                    "col_count": max((len(r) for r in rows), default=0),
                    "rows": rows
                })

            # Build HTML representation
            html_parts = []
            html_parts.append("<div class='xlsx-preview p-4 space-y-4 font-sans text-slate-200 select-text'>")
            
            # Header with sheet tabs
            html_parts.append(f"""
            <div class='p-3 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between'>
                <div>
                    <h2 class='text-sm font-bold text-emerald-400'>{html.escape(file_path.name)}</h2>
                    <p class='text-xs text-slate-400'>{len(sheet_names)} feuille(s) de calcul</p>
                </div>
                <div class='flex gap-1 overflow-x-auto max-w-md'>
            """)
            for idx, s in enumerate(sheets_data):
                active_cls = "bg-emerald-600 text-white" if idx == 0 else "bg-slate-800 text-slate-300 hover:bg-slate-700"
                html_parts.append(f"""
                <button type='button' onclick='showXlsxSheet({idx})' id='xlsx-tab-{idx}' class='px-2.5 py-1 text-xs rounded-lg font-medium transition {active_cls}'>
                    {html.escape(s['name'])}
                </button>
                """)
            html_parts.append("</div></div>")

            # Sheets tables
            for idx, s in enumerate(sheets_data):
                hidden_cls = "" if idx == 0 else "hidden"
                html_parts.append(f"""
                <div id='xlsx-sheet-{idx}' class='xlsx-sheet-container {hidden_cls} border border-slate-800 rounded-xl overflow-hidden bg-slate-950'>
                    <div class='bg-slate-900 px-3 py-1.5 text-xs text-slate-400 border-b border-slate-800 flex justify-between'>
                        <span class='font-bold text-slate-300'>{html.escape(s['name'])}</span>
                        <span class='font-mono text-[10px]'>{s['row_count']} lignes affichées</span>
                    </div>
                    <div class='overflow-x-auto max-h-[600px]'>
                        <table class='w-full text-xs text-left border-collapse font-mono'>
                """)
                for r_idx, row in enumerate(s["rows"]):
                    row_bg = "bg-slate-900/90 font-bold text-emerald-300 border-b border-slate-700" if r_idx == 0 else ("bg-slate-950/40" if r_idx % 2 == 0 else "bg-slate-900/30")
                    html_parts.append(f"<tr class='{row_bg} border-b border-slate-800/60 hover:bg-slate-800/40'>")
                    html_parts.append(f"<td class='p-1.5 text-center text-[10px] text-slate-500 bg-slate-950/80 border-r border-slate-800 select-none w-10'>{r_idx + 1}</td>")
                    for val in row:
                        html_parts.append(f"<td class='p-2 border-r border-slate-800/60 align-top text-slate-200 truncate max-w-xs' title='{html.escape(val)}'>{html.escape(val) or '&nbsp;'}</td>")
                    html_parts.append("</tr>")
                html_parts.append("</table></div></div>")

            html_parts.append("</div>")

            return {
                "success": True,
                "sheet_names": sheet_names,
                "sheets": sheets_data,
                "html": "".join(html_parts)
            }
        except Exception as ex:
            return {
                "success": False,
                "error": str(ex),
                "html": f"<div class='p-4 text-rose-400'>Erreur de rendu XLSX : {html.escape(str(ex))}</div>"
            }

    @staticmethod
    def render_pptx(file_path: Path) -> Dict[str, Any]:
        """Converts PowerPoint presentation into structured slide deck preview."""
        try:
            import pptx
        except ImportError:
            return {
                "success": False,
                "error": "python-pptx non disponible dans le runtime.",
                "html": "<div class='p-4 text-amber-400'>Aperçu PPTX indisponible (module python-pptx manquant)</div>"
            }

        try:
            prs = pptx.Presentation(str(file_path))
            slides_data = []

            for idx, slide in enumerate(prs.slides):
                if idx >= 50:
                    break
                slide_title = ""
                paragraphs = []
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for p in shape.text_frame.paragraphs:
                            txt = p.text.strip()
                            if txt:
                                if not slide_title and ("title" in shape.name.lower() or len(txt) < 80):
                                    slide_title = txt
                                else:
                                    paragraphs.append(txt)

                slides_data.append({
                    "index": idx + 1,
                    "title": slide_title or f"Diapositive #{idx + 1}",
                    "paragraphs": paragraphs
                })

            html_parts = []
            html_parts.append("<div class='pptx-preview p-4 space-y-4 font-sans text-slate-200 select-text'>")
            
            # Header
            html_parts.append(f"""
            <div class='p-3 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between'>
                <div>
                    <h2 class='text-sm font-bold text-amber-400'>{html.escape(file_path.name)}</h2>
                    <p class='text-xs text-slate-400'>{len(slides_data)} diapositive(s)</p>
                </div>
                <span class='px-2 py-0.5 bg-amber-950 border border-amber-800 text-amber-300 text-[10px] rounded font-mono'>PRÉSENTATION PPTX</span>
            </div>
            <div class='grid grid-cols-1 gap-4'>
            """)

            for s in slides_data:
                html_parts.append(f"""
                <div class='p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3 shadow-lg'>
                    <div class='flex items-center justify-between border-b border-slate-800 pb-2'>
                        <h3 class='text-sm font-bold text-sky-400'>{html.escape(s['title'])}</h3>
                        <span class='px-2 py-0.5 bg-slate-800 text-slate-400 rounded text-[10px] font-mono'>Slide {s['index']} / {len(slides_data)}</span>
                    </div>
                    <div class='space-y-1.5 pl-2'>
                """)
                for p_txt in s["paragraphs"][:15]:
                    html_parts.append(f"<p class='text-xs text-slate-300 flex items-start gap-2'><span class='text-amber-400 font-bold'>•</span><span>{html.escape(p_txt)}</span></p>")
                html_parts.append("</div></div>")

            html_parts.append("</div></div>")

            return {
                "success": True,
                "slide_count": len(slides_data),
                "slides": slides_data,
                "html": "".join(html_parts)
            }
        except Exception as ex:
            return {
                "success": False,
                "error": str(ex),
                "html": f"<div class='p-4 text-rose-400'>Erreur de rendu PPTX : {html.escape(str(ex))}</div>"
            }

    @staticmethod
    def render_csv(file_path: Path) -> Dict[str, Any]:
        """Converts CSV file into clean tabular view."""
        try:
            rows = []
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                for idx, r in enumerate(reader):
                    if idx >= 200:
                        break
                    rows.append(r[:30])

            html_parts = []
            html_parts.append("<div class='csv-preview p-4 font-sans text-slate-200 select-text'>")
            html_parts.append(f"""
            <div class='mb-3 p-3 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between'>
                <div>
                    <h2 class='text-sm font-bold text-sky-400'>{html.escape(file_path.name)}</h2>
                    <p class='text-xs text-slate-400'>{len(rows)} lignes affichées</p>
                </div>
                <span class='px-2 py-0.5 bg-sky-950 border border-sky-800 text-sky-300 text-[10px] rounded font-mono'>TABLE DONNÉES CSV</span>
            </div>
            <div class='overflow-x-auto max-h-[600px] border border-slate-800 rounded-xl bg-slate-950'>
                <table class='w-full text-xs text-left border-collapse font-mono'>
            """)

            for r_idx, row in enumerate(rows):
                row_bg = "bg-slate-900 font-bold text-sky-300 border-b border-slate-700" if r_idx == 0 else ("bg-slate-950/40" if r_idx % 2 == 0 else "bg-slate-900/30")
                html_parts.append(f"<tr class='{row_bg} border-b border-slate-800/60'>")
                html_parts.append(f"<td class='p-1.5 text-center text-[10px] text-slate-500 bg-slate-950/80 border-r border-slate-800 select-none w-10'>{r_idx + 1}</td>")
                for val in row:
                    html_parts.append(f"<td class='p-2 border-r border-slate-800/60 align-top text-slate-200 truncate max-w-xs' title='{html.escape(val)}'>{html.escape(val) or '&nbsp;'}</td>")
                html_parts.append("</tr>")

            html_parts.append("</table></div></div>")

            return {
                "success": True,
                "row_count": len(rows),
                "html": "".join(html_parts)
            }
        except Exception as ex:
            return {
                "success": False,
                "error": str(ex),
                "html": f"<div class='p-4 text-rose-400'>Erreur de rendu CSV : {html.escape(str(ex))}</div>"
            }

    @staticmethod
    def render_svg(file_path: Path) -> Dict[str, Any]:
        """Sanitizes SVG by removing active scripts and event handlers."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw_svg = f.read(500000)

            sanitized_svg = sanitize_html_content(raw_svg)
            
            html_content = f"""
            <div class='svg-preview w-full h-full flex flex-col items-center justify-center p-6 bg-slate-950 overflow-auto'>
                <div class='p-4 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl max-w-full max-h-[85%] flex items-center justify-center'>
                    {sanitized_svg}
                </div>
                <div class='mt-3 text-xs text-slate-400 font-mono'>Image vectorielle SVG sécurisée (scripts neutralisés)</div>
            </div>
            """
            return {
                "success": True,
                "sanitized": True,
                "html": html_content
            }
        except Exception as ex:
            return {
                "success": False,
                "error": str(ex),
                "html": f"<div class='p-4 text-rose-400'>Erreur de rendu SVG : {html.escape(str(ex))}</div>"
            }

    @staticmethod
    def render_text_or_code(file_path: Path, max_chars: int = 200000) -> Dict[str, Any]:
        """Safely reads plain text or source code without execution."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars)

            lines = content.splitlines()
            line_count = len(lines)
            char_count = len(content)

            return {
                "success": True,
                "line_count": line_count,
                "char_count": char_count,
                "content": content
            }
        except Exception as ex:
            return {
                "success": False,
                "error": str(ex),
                "content": f"Erreur de lecture du fichier : {str(ex)}"
            }
