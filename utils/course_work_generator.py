# utils/course_work_generator.py
# MUSTAQIL ISH / REFERAT CONTENT GENERATOR
# OpenAI bilan professional akademik matn yaratish

import asyncio
import json
import logging
from typing import Dict, List, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class CourseWorkGenerator:
    """
    OpenAI API bilan mustaqil ish / referat yaratish
    """

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_course_work_content(
            self,
            work_type: str,
            topic: str,
            subject: str,
            details: str,
            page_count: int,
            language: str = 'uz',
            use_gpt4: bool = True
    ) -> Dict:
        """
        Mustaqil ish uchun professional content yaratish

        Args:
            work_type: Ish turi (referat, kurs_ishi, ...)
            topic: Mavzu
            subject: Fan nomi
            details: Qo'shimcha ma'lumotlar
            page_count: Sahifalar soni
            language: Til (uz, ru, en)
            use_gpt4: GPT-4 ishlatish

        Returns:
            Professional content (dict)
        """
        model = "gpt-4" if use_gpt4 else "gpt-3.5-turbo"

        # Til bo'yicha prompt
        lang_instructions = self._get_language_instructions(language)

        # Ish turi bo'yicha struktura
        structure = self._get_work_structure(work_type, page_count)

        prompt = f"""
{lang_instructions}

Siz professor darajasidagi akademik yozuvchisiz. Quyidagi parametrlar asosida professional {structure['name']} yozing.

📋 PARAMETRLAR:
- Ish turi: {structure['name']}
- Mavzu: {topic}
- Fan: {subject}
- Sahifalar: {page_count}
- Til: {lang_instructions}

📝 QO'SHIMCHA TALABLAR:
{details if details else "Maxsus talablar yo'q"}

📚 STRUKTURA:
{structure['outline']}

⚠️ MUHIM QOIDALAR:
1. Har bir bo'lim {structure['paragraphs_per_section']} ta paragrafdan iborat bo'lsin
2. Har bir paragraf 20-50 ta gapdan iborat bo'lsin
3. Akademik uslubda yozing
4. Ilmiy atamalarni to'g'ri ishlating
5. Mantiqiy bog'lanish bo'lsin
6. Plagiatdan xoli bo'lsin
7. Manbalar ro'yxati bo'lsin

JSON formatida qaytaring:
{{
    "title": "To'liq sarlavha",
    "subtitle": "Qo'shimcha sarlavha (ixtiyoriy)",
    "author_info": {{
        "institution": "O'quv muassasasi nomi",
        "faculty": "Fakultet",
        "department": "Kafedra"
    }},
    "abstract": "Qisqacha annotatsiya (1500-2000 so'z)",
    "keywords": ["kalit", "so'zlar", "ro'yxati"],
    "table_of_contents": [
        {{"title": "KIRISH", "page": 3}},
        {{"title": "1-BOB. ...", "page": 5}}
    ],
    "introduction": {{
        "title": "KIRISH",
        "content": "Kirish matni (3-4 paragraf)"
    }},
    "chapters": [
        {{
            "number": 1,
            "title": "Bob sarlavhasi",
            "sections": [
                {{
                    "number": "1.1",
                    "title": "Bo'lim sarlavhasi",
                    "content": "Bo'lim matni (4-6 paragraf)"
                }}
            ]
        }}
    ],
    "conclusion": {{
        "title": "XULOSA",
        "content": "Xulosa matni (3-4 paragraf)"
    }},
    "recommendations": [
        "Birinchi tavsiya",
        "Ikkinchi tavsiya"
    ],
    "references": [
        "1. Muallif I.I. Kitob nomi. – T.: Nashriyot, 2023. – 256 b.",
        "2. ..."
    ],
    "appendix": null
}}

Jami {page_count} sahifaga mos kontent yarating. Har bir sahifa taxminan 1000-3500 so'z.
"""

        try:
            logger.info(f"📝 OpenAI: {structure['name']} content yaratish boshlandi")

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Siz {subject} fani bo'yicha professor darajasidagi akademik yozuvchisiz. {lang_instructions}"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=8000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            content = json.loads(response.choices[0].message.content)
            logger.info(f"✅ OpenAI: {structure['name']} content yaratildi")

            # Validatsiya
            content = self._validate_and_fix_content(content, structure)

            return content

        except Exception as e:
            logger.error(f"❌ OpenAI xato: {e}")
            return self._generate_fallback_content(work_type, topic, subject, page_count, language)

    def _get_language_instructions(self, language: str) -> str:
        """Til bo'yicha ko'rsatmalar"""
        instructions = {
            'uz': "O'ZBEK TILIDA yozing. Lotin alifbosida, zamonaviy o'zbek adabiy tilida.",
            'ru': "РУССКОМ ЯЗЫКЕ пишите. Используйте академический стиль русского языка.",
            'en': "Write in ENGLISH. Use academic English with proper terminology."
        }
        return instructions.get(language, instructions['uz'])

    def _get_work_structure(self, work_type: str, page_count: int) -> Dict:
        """Ish turi bo'yicha struktura"""
        structures = {
            'referat': {
                'name': "Referat",
                'outline': """
1. KIRISH (1-2 sahifa)
   - Mavzuning dolzarbligi
   - Maqsad va vazifalar

2. ASOSIY QISM (3-4 bob)
   - Nazariy asoslar
   - Tahlil
   - Misollar

3. XULOSA (1 sahifa)
   - Asosiy xulosalar

4. FOYDALANILGAN ADABIYOTLAR (5-10 ta manba)
""",
                'paragraphs_per_section': 3,
                'chapters': 2
            },
            'kurs_ishi': {
                'name': "Kurs ishi",
                'outline': """
1. KIRISH (2-3 sahifa)
   - Mavzuning dolzarbligi
   - Maqsad va vazifalar
   - Tadqiqot ob'ekti va predmeti
   - Tadqiqot metodlari

2. I BOB. NAZARIY ASOSLAR (8-10 sahifa)
   - 1.1. Asosiy tushunchalar
   - 1.2. Nazariy yondashuvlar
   - 1.3. Xorijiy tajriba

3. II BOB. AMALIY TAHLIL (10-15 sahifa)
   - 2.1. Hozirgi holat tahlili
   - 2.2. Muammolar va yechimlar
   - 2.3. Tavsiyalar

4. XULOSA (2-3 sahifa)

5. FOYDALANILGAN ADABIYOTLAR (15-20 ta manba)

6. ILOVALAR (ixtiyoriy)
""",
                'paragraphs_per_section': 5,
                'chapters': 3
            },
            'mustaqil_ish': {
                'name': "Mustaqil ish",
                'outline': """
1. KIRISH (1 sahifa)
   - Mavzu haqida qisqacha
   - Maqsad

2. ASOSIY QISM (2-3 bo'lim)
   - Nazariy ma'lumotlar
   - Amaliy misollar

3. XULOSA (1 sahifa)

4. ADABIYOTLAR RO'YXATI
""",
                'paragraphs_per_section': 3,
                'chapters': 2
            },
            'ilmiy_maqola': {
                'name': "Ilmiy maqola",
                'outline': """
1. ANNOTATSIYA (150-200 so'z)
   - Maqola mazmuni
   - Kalit so'zlar

2. KIRISH
   - Muammo bayoni
   - Tadqiqot maqsadi

3. MATERIALAR VA METODLAR
   - Tadqiqot usullari

4. NATIJALAR
   - Asosiy topilmalar

5. MUHOKAMA
   - Natijalar tahlili

6. XULOSA

7. ADABIYOTLAR
""",
                'paragraphs_per_section': 4,
                'chapters': 2
            },
            'hisobot': {
                'name': "Hisobot",
                'outline': """
1. KIRISH
   - Hisobot maqsadi

2. ASOSIY QISM
   - Bajarilgan ishlar
   - Natijalar
   - Muammolar

3. XULOSA VA TAVSIYALAR

4. ILOVALAR (jadvallar, grafiklar)
""",
                'paragraphs_per_section': 3,
                'chapters': 2
            }
        }

        return structures.get(work_type, structures['mustaqil_ish'])

    def _validate_and_fix_content(self, content: Dict, structure: Dict) -> Dict:
        """Kontentni tekshirish va to'g'rilash"""
        # Asosiy maydonlar mavjudligini tekshirish
        required_fields = ['title', 'introduction', 'chapters', 'conclusion', 'references']

        for field in required_fields:
            if field not in content:
                logger.warning(f"⚠️ '{field}' maydoni yo'q, default qo'shilmoqda")
                if field == 'title':
                    content['title'] = "Mavzu"
                elif field == 'introduction':
                    content['introduction'] = {'title': 'KIRISH', 'content': ''}
                elif field == 'chapters':
                    content['chapters'] = []
                elif field == 'conclusion':
                    content['conclusion'] = {'title': 'XULOSA', 'content': ''}
                elif field == 'references':
                    content['references'] = []

        return content

    def _generate_fallback_content(
            self,
            work_type: str,
            topic: str,
            subject: str,
            page_count: int,
            language: str
    ) -> Dict:
        """Fallback content"""
        structure = self._get_work_structure(work_type, page_count)

        return {
            'title': topic,
            'subtitle': f"{subject} fanidan {structure['name'].lower()}",
            'author_info': {
                'institution': "O'zbekiston Milliy Universiteti",
                'faculty': "Fakultet",
                'department': "Kafedra"
            },
            'abstract': f"Ushbu {structure['name'].lower()} {topic} mavzusiga bag'ishlangan. Ishda mavzuning nazariy va amaliy jihatlari o'rganilgan.",
            'keywords': [topic.split()[0] if topic else "mavzu", subject, "tadqiqot"],
            'table_of_contents': [
                {'title': 'KIRISH', 'page': 3},
                {'title': '1-BOB. NAZARIY ASOSLAR', 'page': 5},
                {'title': 'XULOSA', 'page': page_count - 1},
                {'title': 'ADABIYOTLAR', 'page': page_count}
            ],
            'introduction': {
                'title': 'KIRISH',
                'content': f"""
{topic} mavzusi bugungi kunda dolzarb hisoblanadi. {subject} fanida bu masala keng o'rganilgan bo'lib, turli yondashuvlar mavjud.

Ushbu ishning maqsadi - {topic} mavzusini chuqur o'rganish va tahlil qilishdir. Buning uchun nazariy adabiyotlar o'rganildi va amaliy misollar tahlil qilindi.

Ishning vazifalari quyidagilardan iborat:
- Mavzuning nazariy asoslarini o'rganish
- Hozirgi holatni tahlil qilish  
- Xulosalar va tavsiyalar ishlab chiqish
"""
            },
            'chapters': [
                {
                    'number': 1,
                    'title': 'NAZARIY ASOSLAR',
                    'sections': [
                        {
                            'number': '1.1',
                            'title': 'Asosiy tushunchalar va ta\'riflar',
                            'content': f'{topic} tushunchasi akademik adabiyotlarda turlicha talqin qilinadi. Zamonaviy yondashuvlarga ko\'ra...'
                        },
                        {
                            'number': '1.2',
                            'title': 'Mavzuning rivojlanish tarixi',
                            'content': f'{topic} masalasi tarixiy jihatdan katta ahamiyatga ega...'
                        }
                    ]
                },
                {
                    'number': 2,
                    'title': 'AMALIY TAHLIL',
                    'sections': [
                        {
                            'number': '2.1',
                            'title': 'Hozirgi holat tahlili',
                            'content': f'Bugungi kunda {topic} sohasida muhim o\'zgarishlar kuzatilmoqda...'
                        },
                        {
                            'number': '2.2',
                            'title': 'Muammolar va yechimlar',
                            'content': f'{topic} sohasidagi asosiy muammolar va ularning yechimlarini ko\'rib chiqamiz...'
                        }
                    ]
                }
            ],
            'conclusion': {
                'title': 'XULOSA',
                'content': f"""
Ushbu ishda {topic} mavzusi bo'yicha tadqiqot olib borildi. Quyidagi xulosalarga kelindi:

Birinchidan, {topic} masalasi dolzarb bo'lib, chuqur o'rganishni talab qiladi.

Ikkinchidan, mavjud muammolarni hal qilish uchun kompleks yondashuv zarur.

Uchinchidan, kelgusida bu sohada yanada chuqurroq tadqiqotlar olib borish lozim.
"""
            },
            'recommendations': [
                f'{topic} sohasida qo\'shimcha tadqiqotlar olib borish',
                'Xalqaro tajribani o\'rganish',
                'Amaliy loyihalarni amalga oshirish'
            ],
            'references': [
                f'1. Karimov I.A. {subject} asoslari. – T.: Fan, 2023. – 256 b.',
                f'2. Rahimov B.B. {topic}. – T.: O\'qituvchi, 2022. – 180 b.',
                f'3. Smith J. Introduction to {subject}. – London: Academic Press, 2021.',
                f'4. www.ziyonet.uz - O\'zbekiston ta\'lim portali',
                f'5. www.scholar.google.com - Ilmiy maqolalar bazasi'
            ],
            'appendix': None
        }
