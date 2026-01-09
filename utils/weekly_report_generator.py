"""
🤖 WEEKLY REPORT AI GENERATOR
ChatGPT orqali haftalik ish rejasi contentini yaratadi

Faylni utils/ papkasiga joylashtiring
"""

import json
import logging
import traceback
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
        """

        # Foydalanuvchi kiritgan vazifalarni formatlash
        user_tasks = ""
        for day, task_list in tasks.items():
            if task_list and task_list.strip():
                user_tasks += f"\n{day.upper()}:\n{task_list}\n"

        if not user_tasks.strip():
            user_tasks = "Foydalanuvchi vazifa kiritmagan - standart vazifalar yarat"

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

MUHIM QOIDALAR:
1. Foydalanuvchi kiritgan vazifalarni SAQLA va professional tilda yoz
2. Har bir vazifa uchun ANIQ vaqt ko'rsat (masalan: 08:30-09:00)
3. Vazifalarni RASMIY HUJJAT uslubida yoz
4. O'tkazilish joyi ustuniga aniq joyni yoz
5. Har kun uchun kamida 3-5 ta vazifa bo'lsin

⚠️ JUDA MUHIM - MAS'ULLAR USTUNI:
- "Mahalla yoshlar yetakchisi" deb YOZMA!
- "{mahalla} yoshlar yetakchisi" deb yoz (mahalla nomi bilan)
- Masalan: "{mahalla} yoshlar yetakchisi, mahalla raisi"
- Masalan: "{mahalla} yoshlar yetakchisi, hokim yordamchisi"
- Har doim mahalla nomini ({mahalla}) ishlatib yoz!

JAVOBNI FAQAT JSON FORMATDA BER (boshqa hech narsa yozma):
{{
    "dushanba": [
        {{
            "tartib": 1,
            "vazifa": "Vazifa tavsifi to'liq yozilsin",
            "vaqt": "08:30-09:00",
            "joy": "Mahalla idorasi",
            "masul": "{mahalla} yoshlar yetakchisi"
        }},
        {{
            "tartib": 2,
            "vazifa": "Yana bir vazifa",
            "vaqt": "09:00-10:00",
            "joy": "Mahalla hududi",
            "masul": "{mahalla} yoshlar yetakchisi, mahalla raisi"
        }}
    ],
    "seshanba": [...],
    "chorshanba": [...],
    "payshanba": [...],
    "juma": [...],
    "shanba": [...]
}}

Eslatma: Mas'ullar ustunida ALBATTA "{mahalla}" nomini yoz!
"""

        try:
            logger.info(f"🚀 AI so'rov yuborilmoqda: {full_name}, {mahalla}")

            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Sen O'zbek tilida professional hujjatlar yaratuvchi AI yordamchisan. Faqat JSON formatda javob berasan, boshqa hech qanday matn yozma."
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
            logger.info(f"📥 AI javob olindi, uzunlik: {len(content)}")

            # JSON tozalash
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            content = content.strip()

            # Debug uchun
            logger.info(f"📄 Tozalangan content (200 ta belgi): {content[:200]}...")

            # JSON parse
            result = json.loads(content)

            # ═══════════════════════════════════════════════════════════
            # QOSHIMCHA TEKSHIRUV - Mahalla nomini qo'shish
            # Agar AI "Mahalla yoshlar yetakchisi" deb yozgan bo'lsa, tuzatamiz
            # ═══════════════════════════════════════════════════════════
            for day_key, day_tasks in result.items():
                if isinstance(day_tasks, list):
                    for task in day_tasks:
                        if isinstance(task, dict) and 'masul' in task:
                            masul = task['masul']
                            # Agar "Mahalla yoshlar" bilan boshlansa, tuzatamiz
                            if masul.lower().startswith('mahalla yoshlar'):
                                task['masul'] = masul.replace('Mahalla yoshlar', f'{mahalla} yoshlar', 1)
                                task['masul'] = task['masul'].replace('mahalla yoshlar', f'{mahalla} yoshlar', 1)
                            # Agar "Mahalla" so'zi bor, lekin aniq nom yo'q
                            elif 'mahalla' in masul.lower() and mahalla.lower() not in masul.lower():
                                task['masul'] = masul.replace('Mahalla', mahalla)
                                task['masul'] = task['masul'].replace('mahalla', mahalla)

            logger.info(f"✅ AI content muvaffaqiyatli yaratildi: {full_name}, {mahalla}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse xato: {e}")
            logger.error(f"❌ Raw content: {content[:500] if content else 'BOSH'}")
            return None

        except Exception as e:
            logger.error(f"❌ AI generatsiya xato: {type(e).__name__}: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None