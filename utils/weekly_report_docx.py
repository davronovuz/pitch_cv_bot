"""
📄 WEEKLY REPORT DOCX GENERATOR
Haftalik ish rejasini Word formatida yaratadi

Faylni utils/ papkasiga joylashtiring

pip install python-docx --break-system-packages
"""

import logging
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

logger = logging.getLogger(__name__)


class WeeklyReportDocx:
    """Haftalik ish rejasi DOCX yaratuvchi"""

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
            'chorshanba': 'Tadbirkorlik va bandlik masalalari kuни',
            'payshanba': 'Profilaktika tadbirlari',
            'juma': 'Harbiy vatanparvarlik va Zakovat',
            'shanba': 'Yetakchining shaxsiy tashabbusi'
        }

    def set_cell_shading(self, cell, color):
        """Yacheyka rangini o'rnatish"""
        shading = OxmlElement('w:shd')
        shading.set(qn('w:fill'), color)
        cell._tc.get_or_add_tcPr().append(shading)

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
        Haftalik ish rejasi DOCX yaratish

        Args:
            content: AI dan kelgan strukturalangan content
            output_path: Fayl saqlash yo'li
            full_name: Yetakchi FIO
            mahalla: Mahalla nomi
            tuman: Tuman/shahar
            week_date: Hafta sanasi

        Returns:
            bool: Muvaffaqiyatli bo'lsa True
        """

        try:
            doc = Document()

            # Sahifa sozlamalari
            section = doc.sections[0]
            section.page_width = Cm(29.7)  # A4 landscape
            section.page_height = Cm(21)
            section.left_margin = Cm(1.5)
            section.right_margin = Cm(1.5)
            section.top_margin = Cm(1)
            section.bottom_margin = Cm(1)

            # === SARLAVHA ===
            title = doc.add_paragraph()
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER

            run = title.add_run(
                f"MAHALLADAGI YOSHLAR YETAKCHISI {full_name.upper()}NING\n"
                f"{week_date} YILDAGI HAFTALIK ISH REJASI"
            )
            run.bold = True
            run.font.size = Pt(14)
            run.font.name = 'Times New Roman'

            # Mahalla va tuman
            subtitle = doc.add_paragraph()
            subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
            sub_run = subtitle.add_run(f"{mahalla}, {tuman}")
            sub_run.font.size = Pt(12)
            sub_run.font.name = 'Times New Roman'

            doc.add_paragraph()  # Bo'sh qator

            # === JADVAL ===
            # 4 ustun: T/r, Vazifa, Vaqt va joy, Mas'ullar
            table = doc.add_table(rows=1, cols=4)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.style = 'Table Grid'

            # Jadval kengligi
            table.columns[0].width = Cm(1.2)  # T/r
            table.columns[1].width = Cm(14)  # Vazifa
            table.columns[2].width = Cm(5)  # Vaqt va joy
            table.columns[3].width = Cm(6)  # Mas'ullar

            # Sarlavha qatori
            header_cells = table.rows[0].cells
            headers = ['T/r', 'Lоyihа vа tаdbirlаr', 'O\'tkаzilish vаqti vа jоyi', 'Mаs\'ul vа hаmkоrlаr']

            for i, header in enumerate(headers):
                header_cells[i].text = header
                header_cells[i].paragraphs[0].runs[0].bold = True
                header_cells[i].paragraphs[0].runs[0].font.size = Pt(11)
                header_cells[i].paragraphs[0].runs[0].font.name = 'Times New Roman'
                header_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                self.set_cell_shading(header_cells[i], 'D9E2F3')  # Ko'k rang

            # Tartib raqami
            task_number = 1

            # Har bir kun uchun
            for day_key, day_name in self.days_uz.items():
                tasks = content.get(day_key, [])

                if not tasks:
                    continue

                # KUN SARLAVHASI
                day_row = table.add_row()
                day_row.cells[0].merge(day_row.cells[3])

                day_theme = self.day_themes.get(day_key, '')
                day_text = f"{day_name}\n{day_theme}"

                day_row.cells[0].text = day_text
                day_row.cells[0].paragraphs[0].runs[0].bold = True
                day_row.cells[0].paragraphs[0].runs[0].font.size = Pt(11)
                day_row.cells[0].paragraphs[0].runs[0].font.name = 'Times New Roman'
                day_row.cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                self.set_cell_shading(day_row.cells[0], 'FFF2CC')  # Sariq rang

                # VAZIFALAR
                for task in tasks:
                    row = table.add_row()
                    cells = row.cells

                    # T/r
                    cells[0].text = str(task_number)
                    cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

                    # Vazifa
                    cells[1].text = task.get('vazifa', '')

                    # Vaqt va joy
                    vaqt = task.get('vaqt', '')
                    joy = task.get('joy', '')
                    cells[2].text = f"{vaqt}\n\n{joy}"

                    # Mas'ullar
                    cells[3].text = task.get('masul', 'Mahalla yoshlar yetakchisi')

                    # Shrift sozlamalari
                    for cell in cells:
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                run.font.size = Pt(10)
                                run.font.name = 'Times New Roman'

                    task_number += 1

            # === IZOH ===
            doc.add_paragraph()
            note = doc.add_paragraph()
            note_run = note.add_run(
                "Izоh: mаhаllаdаgi yоshlаrning qiziqishlаri vа mаhаllа infrаstrukturаsigа qаrаb, "
                "mаzkur tаdbirlаr rеjаsining kunlаri yoki vаqtlаri o'zgаrishi mumkin."
            )
            note_run.italic = True
            note_run.font.size = Pt(10)
            note_run.font.name = 'Times New Roman'

            # Saqlash
            doc.save(output_path)
            logger.info(f"✅ DOCX yaratildi: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ DOCX yaratishda xato: {e}")
            return False