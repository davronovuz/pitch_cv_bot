"""
📄 PROFESSIONAL WEEKLY REPORT DOCX GENERATOR
Haftalik ish rejasini Word formatida yaratadi - MUKAMMAL VERSIYA

Faylni utils/ papkasiga joylashtiring

pip install python-docx --break-system-packages
"""

import logging
from docx import Document
from docx.shared import Inches, Pt, Cm, Twips, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn, nsdecls
from docx.oxml import OxmlElement, parse_xml

logger = logging.getLogger(__name__)


class WeeklyReportDocx:
    """Professional haftalik ish rejasi DOCX yaratuvchi"""

    def __init__(self):
        self.days_uz = {
            'dushanba': 'DUSHANBA',
            'seshanba': 'SESHANBA',
            'chorshanba': 'CHORSHANBA',
            'payshanba': 'PAYSHANBA',
            'juma': 'JUMA',
            'shanba': 'SHANBA'
        }

        self.day_themes = {
            'dushanba': 'Yoshlar muammolarini o\'rganish',
            'seshanba': 'Kitobxonlik',
            'chorshanba': 'Tadbirkorlik va bandlik masalalari kuni',
            'payshanba': 'Profilaktika tadbirlari',
            'juma': 'Harbiy vatanparvarlik va Zakovat',
            'shanba': 'Yetakchining shaxsiy tashabbusi'
        }

    def set_cell_border(self, cell, border_color="000000", border_size="4"):
        """
        Yacheyka chegaralarini professional qilish
        """
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()

        tcBorders = OxmlElement('w:tcBorders')

        for border_name in ['top', 'left', 'bottom', 'right']:
            border = OxmlElement(f'w:{border_name}')
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), border_size)
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), border_color)
            tcBorders.append(border)

        tcPr.append(tcBorders)

    def set_cell_shading(self, cell, color):
        """Yacheyka fon rangini o'rnatish"""
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()

        # Eski shading ni olib tashlash
        for shading in tcPr.findall(qn('w:shd')):
            tcPr.remove(shading)

        shading = OxmlElement('w:shd')
        shading.set(qn('w:val'), 'clear')
        shading.set(qn('w:color'), 'auto')
        shading.set(qn('w:fill'), color)
        tcPr.append(shading)

    def set_cell_margins(self, cell, top=50, bottom=50, left=80, right=80):
        """Yacheyka ichki marginlarini o'rnatish"""
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()

        tcMar = OxmlElement('w:tcMar')

        for margin_name, margin_value in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
            margin = OxmlElement(f'w:{margin_name}')
            margin.set(qn('w:w'), str(margin_value))
            margin.set(qn('w:type'), 'dxa')
            tcMar.append(margin)

        tcPr.append(tcMar)

    def set_cell_width(self, cell, width_cm):
        """Yacheyka kengligini aniq o'rnatish"""
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()

        tcW = OxmlElement('w:tcW')
        # 1 cm = 567 twips (DXA)
        tcW.set(qn('w:w'), str(int(width_cm * 567)))
        tcW.set(qn('w:type'), 'dxa')

        # Eski width ni olib tashlash
        for w in tcPr.findall(qn('w:tcW')):
            tcPr.remove(w)

        tcPr.append(tcW)

    def set_row_height(self, row, height_cm, rule='atLeast'):
        """Qator balandligini o'rnatish"""
        tr = row._tr
        trPr = tr.get_or_add_trPr()

        trHeight = OxmlElement('w:trHeight')
        trHeight.set(qn('w:val'), str(int(height_cm * 567)))
        trHeight.set(qn('w:hRule'), rule)
        trPr.append(trHeight)

    def format_cell_text(self, cell, text, bold=False, size=10, align='left', font='Times New Roman'):
        """Yacheyka matnini professional formatlash"""
        cell.text = ""

        paragraph = cell.paragraphs[0]

        # Alignment
        if align == 'center':
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif align == 'right':
            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Paragraph spacing
        paragraph.paragraph_format.space_before = Pt(2)
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.line_spacing = 1.0

        run = paragraph.add_run(text)
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold

        # Times New Roman uchun
        run._element.rPr.rFonts.set(qn('w:eastAsia'), font)

    def add_multi_line_text(self, cell, lines, size=10, font='Times New Roman'):
        """Ko'p qatorli matn qo'shish"""
        cell.text = ""

        for i, line in enumerate(lines):
            if i == 0:
                paragraph = cell.paragraphs[0]
            else:
                paragraph = cell.add_paragraph()

            paragraph.paragraph_format.space_before = Pt(1)
            paragraph.paragraph_format.space_after = Pt(1)
            paragraph.paragraph_format.line_spacing = 1.0

            run = paragraph.add_run(line)
            run.font.name = font
            run.font.size = Pt(size)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), font)

    def create_weekly_report(
            self,
            content: dict,
            output_path: str,
            full_name: str,
            mahalla: str,
            tuman: str,
            week_date: str
    ) -> bool:
        """
        Professional haftalik ish rejasi DOCX yaratish
        """

        try:
            doc = Document()

            # ═══════════════════════════════════════════════════════════
            # SAHIFA SOZLAMALARI - A4 Landscape
            # ═══════════════════════════════════════════════════════════
            section = doc.sections[0]
            section.orientation = 1  # Landscape
            section.page_width = Cm(29.7)
            section.page_height = Cm(21.0)
            section.left_margin = Cm(1.5)
            section.right_margin = Cm(1.5)
            section.top_margin = Cm(1.0)
            section.bottom_margin = Cm(1.0)

            # ═══════════════════════════════════════════════════════════
            # SARLAVHA
            # ═══════════════════════════════════════════════════════════
            title_para = doc.add_paragraph()
            title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            title_para.paragraph_format.space_after = Pt(6)

            title_run = title_para.add_run(
                f"MAHALLADAGI YOSHLAR YETAKCHISI {full_name.upper()}NING"
            )
            title_run.font.name = 'Times New Roman'
            title_run.font.size = Pt(14)
            title_run.font.bold = True
            title_run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')

            # Ikkinchi qator
            subtitle_para = doc.add_paragraph()
            subtitle_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            subtitle_para.paragraph_format.space_after = Pt(12)

            subtitle_run = subtitle_para.add_run(
                f"{week_date} YILDAGI HAFTALIK ISH REJASI"
            )
            subtitle_run.font.name = 'Times New Roman'
            subtitle_run.font.size = Pt(14)
            subtitle_run.font.bold = True
            subtitle_run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')

            # ═══════════════════════════════════════════════════════════
            # JADVAL - 4 ustun
            # ═══════════════════════════════════════════════════════════
            # Ustun kengliklari (jami ~26.7 cm - sahifa eni minus marginlar)
            col_widths = [1.2, 13.5, 5.5, 6.5]  # T/r, Vazifa, Vaqt/Joy, Mas'ullar

            table = doc.add_table(rows=1, cols=4)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False

            # Jadval kengligini o'rnatish
            tbl = table._tbl
            tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement('w:tblPr')

            tblW = OxmlElement('w:tblW')
            tblW.set(qn('w:w'), '5000')
            tblW.set(qn('w:type'), 'pct')  # 100% kenglik
            tblPr.append(tblW)

            # ═══════════════════════════════════════════════════════════
            # SARLAVHA QATORI
            # ═══════════════════════════════════════════════════════════
            header_row = table.rows[0]
            headers = ['T/r', 'Loyiha va tadbirlar', 'O\'tkazilish vaqti va joyi', 'Mas\'ul va hamkorlar']

            for i, (header, width) in enumerate(zip(headers, col_widths)):
                cell = header_row.cells[i]

                # Kenglik
                self.set_cell_width(cell, width)

                # Chegaralar
                self.set_cell_border(cell, "000000", "6")

                # Fon rangi - ko'k
                self.set_cell_shading(cell, "D6DCE5")

                # Marginlar
                self.set_cell_margins(cell, 60, 60, 100, 100)

                # Matn
                self.format_cell_text(cell, header, bold=True, size=11, align='center')

                # Vertikal align
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

            # Qator balandligi
            self.set_row_height(header_row, 0.8)

            # ═══════════════════════════════════════════════════════════
            # MA'LUMOTLAR
            # ═══════════════════════════════════════════════════════════
            task_number = 1

            for day_key, day_name in self.days_uz.items():
                tasks = content.get(day_key, [])

                if not tasks:
                    continue

                # ─────────────────────────────────────────────────────
                # KUN SARLAVHASI (birlashtirilgan qator)
                # ─────────────────────────────────────────────────────
                day_row = table.add_row()

                # Yacheykalarni birlashtirish
                day_row.cells[0].merge(day_row.cells[3])
                merged_cell = day_row.cells[0]

                # Kenglik
                self.set_cell_width(merged_cell, sum(col_widths))

                # Chegaralar
                self.set_cell_border(merged_cell, "000000", "6")

                # Fon rangi - sariq
                self.set_cell_shading(merged_cell, "FFF2CC")

                # Marginlar
                self.set_cell_margins(merged_cell, 40, 40, 100, 100)

                # Matn - kun nomi va mavzusi
                day_theme = self.day_themes.get(day_key, '')
                self.add_multi_line_text(merged_cell, [day_name, day_theme], size=11)

                # Bold qilish
                for para in merged_cell.paragraphs:
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.font.bold = True

                # ─────────────────────────────────────────────────────
                # VAZIFALAR
                # ─────────────────────────────────────────────────────
                for task in tasks:
                    row = table.add_row()
                    cells = row.cells

                    # Har bir yacheyka uchun formatlash
                    for i, width in enumerate(col_widths):
                        self.set_cell_width(cells[i], width)
                        self.set_cell_border(cells[i], "000000", "4")
                        self.set_cell_margins(cells[i], 40, 40, 80, 80)
                        cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

                    # T/r - tartib raqami
                    self.format_cell_text(cells[0], str(task_number), size=10, align='center')

                    # Vazifa tavsifi
                    vazifa = task.get('vazifa', '')
                    self.format_cell_text(cells[1], vazifa, size=10, align='left')

                    # Vaqt va joy
                    vaqt = task.get('vaqt', '')
                    joy = task.get('joy', 'Mahalla idorasi')
                    self.add_multi_line_text(cells[2], [vaqt, '', joy], size=10)
                    cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                    if len(cells[2].paragraphs) > 2:
                        cells[2].paragraphs[2].alignment = WD_ALIGN_PARAGRAPH.CENTER

                    # Mas'ullar
                    masul = task.get('masul', 'Mahalla yoshlar yetakchisi')
                    self.format_cell_text(cells[3], masul, size=10, align='left')

                    task_number += 1

            # ═══════════════════════════════════════════════════════════
            # IZOH
            # ═══════════════════════════════════════════════════════════
            doc.add_paragraph()  # Bo'sh qator

            note_para = doc.add_paragraph()
            note_para.paragraph_format.space_before = Pt(12)

            note_run = note_para.add_run(
                "Izoh: mahalladagi yoshlarning qiziqishlari va mahalla infratuzilmasiga qarab, "
                "mazkur tadbirlar rejasining kunlari yoki vaqtlari o'zgarishi mumkin."
            )
            note_run.font.name = 'Times New Roman'
            note_run.font.size = Pt(10)
            note_run.font.italic = True
            note_run._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')

            # ═══════════════════════════════════════════════════════════
            # SAQLASH
            # ═══════════════════════════════════════════════════════════
            doc.save(output_path)
            logger.info(f"✅ Professional DOCX yaratildi: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ DOCX yaratishda xato: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False