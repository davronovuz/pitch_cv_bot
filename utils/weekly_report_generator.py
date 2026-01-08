"""
🤖 WEEKLY REPORT AI GENERATOR
ChatGPT orqali haftalik ish rejasi contentini yaratadi

Faylni utils/ papkasiga joylashtiring
"""

import json
import logging
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class WeeklyReportGenerator:
    """ChatGPT orqali haftalik ish rejasi yaratuvchi"""

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_weekly_report(
            self,
            full_name: str,
            mahalla: str,
            tuman: str,
            week_date: str,
            tasks: dict
    ) -> dict:
        """
        Haftalik ish rejasi contentini yaratish

        Args:
            full_name: To'liq FIO
            mahalla: Mahalla nomi
            tuman: Tuman/shahar
            week_date: Hafta sanasi
            tasks: Kunlik vazifalar dict

        Returns:
            dict: Strukturalangan content
        """

        # Foydalanuvchi kiritgan vazifalarni formatlash
        user_tasks = ""
        for day, task_list in tasks.items():
            if task_list.strip():
                user_tasks += f"\n{day.upper()}:\n{task_list}\n"

        prompt = f"""
Sen mahalla yoshlar yetakchisi uchun professional haftalik ish rejasi yaratuvchisan.

YETAKCHI MA'LUMOTLARI:
- FIO: {full_name}
- Mahalla: {mahalla}
- Tuman: {tuman}
- Hafta: {week_date}

FOYDALANUVCHI KIRITGAN VAZIFALAR:
{user_tasks}

VAZIFA:
Yuqoridagi ma'lumotlar asosida professional haftalik ish rejasi yarat. 

QOIDALAR:
1. Foydalanuvchi kiritgan vazifalarni SAQLA va professional tilda yoz
2. Har bir vazifa uchun ANIQ vaqt ko'rsat (masalan: 08:30-09:00)
3. Vazifalarni RASMIY HUJJAT uslubida yoz
4. Mas'ullar ustuniga tegishli shaxslarni yoz
5. O'tkazilish joyi ustuniga aniq joyni yoz
6. Agar foydalanuvchi vaqt ko'rsatmagan bo'lsa, mantiqiy vaqt qo'y

JAVOBNI FAQAT JSON FORMATDA BER:
{{
    "dushanba": [
        {{
            "tartib": 1,
            "vazifa": "Vazifa tavsifi",
            "vaqt": "08:30-09:00",
            "joy": "Mahalla idorasi",
            "masul": "Mahalla yoshlar yetakchisi"
        }}
    ],
    "seshanba": [...],
    "chorshanba": [...],
    "payshanba": [...],
    "juma": [...],
    "shanba": [...]
}}

Faqat JSON qaytar, boshqa hech narsa yozma.
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Sen O'zbek tilida professional hujjatlar yaratuvchi AI yordamchisan. Faqat JSON formatda javob berasan."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000
            )

            content = response.choices[0].message.content.strip()

            # JSON tozalash
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            content = content.strip()

            # JSON parse
            result = json.loads(content)

            logger.info(f"✅ AI content yaratildi: {full_name}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse xato: {e}")
            logger.error(f"Raw content: {content[:500]}")
            return None

        except Exception as e:
            logger.error(f"AI generatsiya xato: {e}")
            return None