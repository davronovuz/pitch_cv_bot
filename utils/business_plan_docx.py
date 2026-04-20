# utils/business_plan_docx.py
# Professional biznes reja DOCX generator

import logging
from datetime import datetime
from typing import Dict
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

logger = logging.getLogger(__name__)

# Rang sxemasi
COLOR_PRIMARY = RGBColor(0x1A, 0x73, 0xE8)    # Ko'k
COLOR_DARK = RGBColor(0x1A, 0x1A, 0x2E)        # Qora-ko'k
COLOR_ACCENT = RGBColor(0x0D, 0x47, 0xA1)      # To'q ko'k
COLOR_LIGHT_BG = RGBColor(0xF0, 0xF4, 0xFF)    # Och ko'k fon
COLOR_GRAY = RGBColor(0x60, 0x60, 0x60)         # Kulrang
COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)        # Oq


class BusinessPlanDocx:
    """Professional biznes reja DOCX yaratish"""

    def create(self, content: Dict, output_path: str) -> bool:
        """
        Professional biznes reja DOCX fayl yaratish

        Args:
            content: business_plan_generator.generate() natijasi
            output_path: saqlash yo'li

        Returns:
            bool: muvaffaqiyatli
        """
        try:
            doc = Document()
            self._setup_document(doc)

            business_name = content.get("business_name", "Biznes Reja")
            industry = content.get("industry", "")

            # === MUQOVA ===
            self._add_cover_page(doc, business_name, industry, content)

            # === MUNDARIJA ===
            doc.add_page_break()
            self._add_toc(doc)

            # === BO'LIMLAR ===
            sections = [
                ("1. IJROIYA XULOSASI", content.get("executive_summary", "")),
                ("2. TASHABBUSKOR VA KOMPANIYA TAVSIFI", content.get("company_description", "")),
                ("3. BOZOR TAHLILI", content.get("market_analysis", "")),
                ("4. MAHSULOT VA XIZMATLAR", content.get("product_service_section") or content.get("product_service", "")),
                ("5. MARKETING VA SAVDO STRATEGIYASI", content.get("marketing_strategy", "")),
                ("6. OPERATSION REJA", content.get("operations_plan", "")),
                ("7. MOLIYAVIY PROGNOZ", content.get("financial_projections", "")),
                ("8. BOSHQARUV JAMOASI VA KADRLAR", content.get("team_section", "")),
                ("9. RISK TAHLILI VA BOSHQARUV", content.get("risk_analysis", "")),
                ("10. XULOSA VA INVESTOR/BANKGA MUROJAAT", content.get("conclusion", "")),
            ]

            for section_title, section_text in sections:
                doc.add_page_break()
                self._add_section(doc, section_title, section_text)

            doc.save(output_path)
            logger.info(f"✅ Biznes reja saqlandi: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Biznes reja DOCX xato: {e}")
            return False

    def _setup_document(self, doc: Document):
        """Hujjat sozlamalari"""
        section = doc.sections[0]
        section.page_width = Inches(8.27)    # A4
        section.page_height = Inches(11.69)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.0)
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.0)

        # Normal style
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.line_spacing = Pt(18)

    def _add_cover_page(self, doc: Document, business_name: str, industry: str, content: Dict):
        """Muqova sahifa"""
        # Logo / Dekorativ element
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("━" * 35)
        run.font.color.rgb = COLOR_PRIMARY
        run.font.size = Pt(14)

        doc.add_paragraph()
        doc.add_paragraph()

        # Sana
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run(datetime.now().strftime("%d.%m.%Y"))
        run.font.size = Pt(11)
        run.font.color.rgb = COLOR_GRAY

        doc.add_paragraph()
        doc.add_paragraph()
        doc.add_paragraph()

        # Sarlavha
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("BIZNES REJA")
        run.font.bold = True
        run.font.size = Pt(28)
        run.font.color.rgb = COLOR_DARK
        run.font.name = 'Times New Roman'

        doc.add_paragraph()

        # Biznes nomi
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(business_name.upper())
        run.font.bold = True
        run.font.size = Pt(22)
        run.font.color.rgb = COLOR_PRIMARY
        run.font.name = 'Times New Roman'

        doc.add_paragraph()

        # Soha
        if industry:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(f"Soha: {industry}")
            run.font.size = Pt(14)
            run.font.color.rgb = COLOR_GRAY
            run.font.italic = True

        doc.add_paragraph()
        doc.add_paragraph()

        # Ajratuvchi
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("━" * 35)
        run.font.color.rgb = COLOR_PRIMARY
        run.font.size = Pt(14)

        doc.add_paragraph()
        doc.add_paragraph()

        # Qo'shimcha ma'lumotlar (paspart asosida)
        location = content.get("location") or content.get("target_market", "")
        financing = content.get("financing") or content.get("investment", "")
        initiator_type = content.get("initiator_type", "")
        company_info = content.get("company_info", "")

        info_rows = []
        if location:
            info_rows.append(("Hudud", location))
        if initiator_type:
            info_rows.append(("Tashabbuskor turi", initiator_type))
        if company_info:
            info_rows.append(("Korxona", company_info))
        if financing:
            info_rows.append(("Moliyalashtirish", financing))

        for label, value in info_rows:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(f"{label}: {value}")
            run.font.size = Pt(12)
            run.font.color.rgb = COLOR_DARK

        # Pastki ajratuvchi
        doc.add_paragraph()
        doc.add_paragraph()
        doc.add_paragraph()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("━" * 50)
        run.font.color.rgb = COLOR_ACCENT
        run.font.size = Pt(12)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("MAXFIY HUJJAT — Faqat ishbilarmon maqsadlarda foydalanish uchun")
        run.font.size = Pt(9)
        run.font.color.rgb = COLOR_GRAY
        run.font.italic = True

    def _add_toc(self, doc: Document):
        """Mundarija"""
        p = doc.add_paragraph()
        run = p.add_run("MUNDARIJA")
        run.font.bold = True
        run.font.size = Pt(16)
        run.font.color.rgb = COLOR_DARK
        run.font.name = 'Times New Roman'
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        self._add_horizontal_line(doc, COLOR_PRIMARY)
        doc.add_paragraph()

        toc_items = [
            ("1. Ijroiya Xulosasi", "3"),
            ("2. Tashabbuskor va Kompaniya Tavsifi", "4"),
            ("3. Bozor Tahlili", "6"),
            ("4. Mahsulot va Xizmatlar", "8"),
            ("5. Marketing va Savdo Strategiyasi", "10"),
            ("6. Operatsion Reja", "12"),
            ("7. Moliyaviy Prognoz", "14"),
            ("8. Boshqaruv Jamoasi va Kadrlar", "17"),
            ("9. Risk Tahlili va Boshqaruv", "19"),
            ("10. Xulosa va Investor/Bankga Murojaat", "21"),
        ]

        for title, page in toc_items:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.5)
            # Dots tabstop o'rniga oddiy yozuv
            run = p.add_run(f"  {title}")
            run.font.size = Pt(12)
            run.font.name = 'Times New Roman'
            # Tab
            run2 = p.add_run(f"{'.' * (60 - len(title))} {page}")
            run2.font.size = Pt(12)
            run2.font.color.rgb = COLOR_GRAY
            run2.font.name = 'Times New Roman'
            p.paragraph_format.space_after = Pt(4)

    def _add_section(self, doc: Document, title: str, text: str):
        """Bo'lim sarlavhasi va matni"""
        # Sarlavha
        p = doc.add_paragraph()
        run = p.add_run(title)
        run.font.bold = True
        run.font.size = Pt(16)
        run.font.color.rgb = COLOR_DARK
        run.font.name = 'Times New Roman'

        self._add_horizontal_line(doc, COLOR_PRIMARY)
        doc.add_paragraph()

        # Matn
        if not text:
            return

        paragraphs = text.strip().split('\n')
        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                continue

            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0)
            p.paragraph_format.first_line_indent = Cm(1.25)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = Pt(18)

            # Kichik sarlavha aniqlash (** yoki ko'p bo'sh joy bilan boshlanuvchi)
            is_subheading = (
                para_text.startswith('**') and para_text.endswith('**')
                or (len(para_text) < 80 and para_text.endswith(':') and not para_text.startswith('-'))
            )

            # Jadval satri aniqlash (| bilan)
            is_table_row = '|' in para_text and para_text.count('|') >= 2

            # Bullet point
            is_bullet = para_text.startswith(('-', '•', '*', '→', '✓', '▶'))

            if is_subheading:
                clean = para_text.strip('*').strip()
                run = p.add_run(clean)
                run.font.bold = True
                run.font.size = Pt(13)
                run.font.color.rgb = COLOR_ACCENT
                run.font.name = 'Times New Roman'
                p.paragraph_format.first_line_indent = Cm(0)
                p.paragraph_format.space_before = Pt(10)
            elif is_table_row:
                # Jadval satrlarini matn sifatida
                run = p.add_run(para_text)
                run.font.size = Pt(11)
                run.font.name = 'Courier New'
                p.paragraph_format.first_line_indent = Cm(0)
                p.paragraph_format.left_indent = Cm(1)
            elif is_bullet:
                run = p.add_run(para_text)
                run.font.size = Pt(12)
                run.font.name = 'Times New Roman'
                p.paragraph_format.left_indent = Cm(1.5)
                p.paragraph_format.first_line_indent = Cm(-0.5)
            else:
                # Oddiy paragraf
                # ** ** bold qismlarni ajratish
                self._add_formatted_text(p, para_text)

        doc.add_paragraph()

    def _add_formatted_text(self, paragraph, text: str):
        """** ** bo'lgan bold qismlarni to'g'ri formatlash"""
        parts = text.split('**')
        for i, part in enumerate(parts):
            if not part:
                continue
            run = paragraph.add_run(part)
            run.font.size = Pt(12)
            run.font.name = 'Times New Roman'
            if i % 2 == 1:  # Toq indekslar bold
                run.font.bold = True

    def _add_horizontal_line(self, doc: Document, color: RGBColor = None):
        """Gorizontal chiziq"""
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.space_before = Pt(2)
        run = p.add_run("─" * 70)
        run.font.size = Pt(8)
        if color:
            run.font.color.rgb = color
        else:
            run.font.color.rgb = COLOR_GRAY
