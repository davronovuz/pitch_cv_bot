import asyncio
import json
import logging
from typing import Dict, List, Optional
from openai import AsyncOpenAI

# Loglarni sozlash
logger = logging.getLogger(__name__)


class ContentGenerator:
    """
    OpenAI API bilan ishlash uchun yagona markazlashgan klass.
    Quyidagi xizmatlarni o'z ichiga oladi:
    1. Pitch Deck generatsiyasi (Startaplar uchun)
    2. Prezentatsiya generatsiyasi (Umumiy mavzular)
    3. AiDA - Mahalla Biznes Tahlili (Yangi funksiya)
    """

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    # =========================================================================
    # 1-BLOK: PITCH DECK (STARTAPLAR UCHUN)
    # =========================================================================

    async def generate_pitch_deck_content(
            self,
            answers: List[str],
            use_gpt4: bool = True
    ) -> Dict:
        """
        Pitch Deck uchun professional content yaratish
        """
        model = "gpt-4o" if use_gpt4 else "gpt-3.5-turbo"

        # 1. Avval bozor tahlilini yaratib olamiz
        market_data = await self._generate_market_analysis(
            project_info=answers[1] if len(answers) > 1 else "",
            target_audience=answers[5] if len(answers) > 5 else "",
            model=model
        )

        # 2. Asosiy promptni yig'amiz
        prompt = self._build_pitch_deck_prompt(answers, market_data)

        try:
            logger.info(f"OpenAI: Pitch deck content yaratish boshlandi (model: {model})")

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Siz O'zbekistondagi eng tajribali va professional investitsion tahlilchi va pitch-deck mutaxassisisiz. Maqsad: Investorni jalb qilish."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            content = json.loads(response.choices[0].message.content)
            logger.info("OpenAI: Pitch deck content muvaffaqiyatli yaratildi")
            return content

        except Exception as e:
            logger.error(f"OpenAI xato (Pitch Deck): {e}")
            return self._generate_fallback_pitch_content(answers)

    async def _generate_market_analysis(self, project_info: str, target_audience: str, model: str) -> Dict:
        """Bozor tahlili (TAM/SAM/SOM) yaratish uchun yordamchi funksiya"""
        prompt = f"""
        Loyiha: {project_info}
        Auditoriya: {target_audience}

        Vazifa: O'zbekiston bozori uchun qisqa tahlil bering.

        Javobni JSON formatida qaytaring:
        {{
          "tam": "Umumiy bozor hajmi (USD)",
          "sam": "O'zlashtirish mumkin bo'lgan bozor (USD)",
          "som": "Real bozor ulushi (USD)",
          "growth_rate": "Yillik o'sish %",
          "trends": "Bozordagi trendlar (ro'yxat)",
          "segments": "Mijoz segmentlari"
        }}
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Siz bozor tahlili ekspertisiz."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except:
            return {
                'tam': "100 mln dollar",
                'sam': "30 mln dollar",
                'som': "5 mln dollar",
                'growth_rate': "20% yillik",
                'trends': "Raqamlashtirish, Mobil ilovalar",
                'segments': "B2B va B2C"
            }

    def _build_pitch_deck_prompt(self, answers: List[str], market_data: Dict) -> str:
        """Pitch deck promptini shakllantirish"""
        return f"""
        Quyidagi ma'lumotlar asosida Startap uchun Pitch Deck matnini yozing.

        STARTUP MA'LUMOTLARI:
        1. Asoschi: {answers[0] if len(answers) > 0 else ""}
        2. Loyiha nomi: {answers[1] if len(answers) > 1 else ""}
        3. Qisqa tavsif: {answers[2] if len(answers) > 2 else ""}
        4. Muammo: {answers[3] if len(answers) > 3 else ""}
        5. Yechim: {answers[4] if len(answers) > 4 else ""}
        6. Auditoriya: {answers[5] if len(answers) > 5 else ""}
        7. Biznes model: {answers[6] if len(answers) > 6 else ""}
        8. Raqobatchilar: {answers[7] if len(answers) > 7 else ""}
        9. Raqobat ustunligi: {answers[8] if len(answers) > 8 else ""}
        10. Moliya: {answers[9] if len(answers) > 9 else ""}

        BOZOR TAHLILI: {json.dumps(market_data, ensure_ascii=False)}

        JSON FORMATDA QAYTARING:
        {{
          "project_name": "Loyiha nomi",
          "tagline": "Jarangdor shior (slogan)",
          "problem_title": "MUAMMO",
          "problem": "Muammoning og'riqli tomonlari (storytelling usulida)",
          "solution_title": "YECHIM",
          "solution": "Bizning yechimimiz qanday ishlaydi?",
          "market_title": "BOZOR IMKONIYATLARI",
          "market": "TAM/SAM/SOM tahlili",
          "business_title": "BIZNES MODEL",
          "business_model": "Qanday pul topamiz?",
          "competition_title": "RAQOBAT",
          "competition": "Raqobatchilardan farqimiz",
          "financials_title": "MOLIYA",
          "financials": "Investitsiya va daromad prognozi",
          "team_title": "JAMOA",
          "team": "Jamoa haqida qisqa",
          "cta": "Call to Action (Investorga taklif)"
        }}
        """

    def _generate_fallback_pitch_content(self, answers: List[str]) -> Dict:
        """Pitch deck uchun zaxira javob"""
        return {
            'project_name': answers[1] if len(answers) > 1 else "Yangi Loyiha",
            'tagline': "Kelajak texnologiyalari",
            'problem': f"Asosiy muammo: {answers[3] if len(answers) > 3 else 'Aniqlanmagan'}",
            'solution': f"Yechim: {answers[4] if len(answers) > 4 else 'Platforma yaratish'}",
            'market': "Bozor o'sib bormoqda.",
            'business_model': "Obuna va xizmat ko'rsatish.",
            'cta': "Bizga qo'shiling!"
        }

    # =========================================================================
    # 2-BLOK: ODDIY PREZENTATSIYA
    # =========================================================================

    async def generate_presentation_content(
            self,
            topic: str,
            details: str,
            slide_count: int,
            use_gpt4: bool = False
    ) -> Dict:
        """
        Oddiy mavzular bo'yicha prezentatsiya contentini yaratish
        """
        model = "gpt-4o" if use_gpt4 else "gpt-3.5-turbo"

        prompt = f"""
        Siz professional spikersiz. O'zbek tilida taqdimot tayyorlang.

        MAVZU: {topic}
        QO'SHIMCHA: {details}
        SLAYDLAR SONI: {slide_count}

        JSON FORMAT:
        {{
          "title": "Taqdimot sarlavhasi",
          "subtitle": "Qisqa izoh",
          "slides": [
            {{
              "slide_number": 1,
              "title": "Slayd sarlavhasi",
              "content": "Asosiy matn (paragraph)",
              "bullet_points": ["Nuqta 1", "Nuqta 2", "Nuqta 3"]
            }}
          ]
        }}
        """

        try:
            logger.info(f"OpenAI: Prezentatsiya yaratish boshlandi (model: {model})")
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Siz taqdimotlar ustasisiz."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"OpenAI xato (Prezentatsiya): {e}")
            return self._generate_fallback_presentation_content(topic, details, slide_count)

    def _generate_fallback_presentation_content(self, topic: str, details: str, slide_count: int) -> Dict:
        """Prezentatsiya uchun zaxira javob"""
        slides = []
        for i in range(1, slide_count + 1):
            slides.append({
                "slide_number": i,
                "title": f"{topic}: {i}-qism",
                "content": f"{details[:50]}... haqida ma'lumot.",
                "bullet_points": ["Muhim nuqta 1", "Muhim nuqta 2"]
            })
        return {"title": topic, "subtitle": "Avtomatik generatsiya", "slides": slides}

    # =========================================================================
    # 3-BLOK: AiDA - MAHALLA BIZNES TAHLILI (YANGI)
    # =========================================================================

    async def generate_mahalla_analysis(
            self,
            mahalla_data: Dict[str, str],
            use_gpt4: bool = True
    ) -> Dict:
        """
        Mahalla ma'lumotlari asosida professional biznes tahlil va g'oyalar (AiDA).
        """
        model = "gpt-4o" if use_gpt4 else "gpt-3.5-turbo"

        # Promptni alohida metod orqali olamiz
        prompt = self._build_mahalla_prompt(mahalla_data)

        try:
            logger.info(f"OpenAI: Mahalla tahlili boshlandi (model: {model})")

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Siz O'zbekiston iqtisodiyoti, mahalliy bozor xususiyatlari va tadbirkorlik muhitini chuqur tushunadigan professional biznes-konsultantsiz. Vazifangiz: Berilgan ma'lumotlardan kelib chiqib, quruq nazariya emas, balki aniq raqamlarga asoslangan, real va daromadli biznes yechimlarini taqdim etish."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2500,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            content = json.loads(response.choices[0].message.content)
            logger.info("OpenAI: Mahalla tahlili muvaffaqiyatli yakunlandi")
            return content

        except Exception as e:
            logger.error(f"OpenAI xato (Mahalla tahlili): {e}")
            return self._generate_fallback_mahalla_content(mahalla_data)

    def _build_mahalla_prompt(self, data: Dict[str, str]) -> str:
        """Mahalla tahlili uchun mukammal prompt strukturasi"""
        return f"""
        Quyidagi mahalla profilini professional tarzda tahlil qiling va eng optimal 3 ta biznes g'oyasini JSON formatida taqdim eting.

        📊 MAHALLA PROFILI:
        1.  📍 Joylashuv: {data.get('mahalla_nomi', 'Nomalum')} (Hudud turi: {data.get('hudud_turi', 'Shahar')})
        2.  👥 Demografiya: Jami aholi {data.get('aholi_soni', '0')}. Yoshlar (14-30): {data.get('yoshlar_soni', '0')}. Ayollar: {data.get('ayollar_soni', '0')}.
        3.  🏫 Ijtimoiy Infratuzilma: Maktablar soni: {data.get('maktablar', '0')}, Bog'chalar soni: {data.get('bogchalar', '0')}.
        4.  🛣 Logistika: Magistral yo'lga {data.get('yol_yaqinligi', 'ortacha')} masofada joylashgan.
        5.  💰 Iqtisodiy holat: Aholining xarid qobiliyati {data.get('xarid_qobiliyati', 'ortacha')}.
        6.  🏢 Mavjud raqobat va bizneslar: Asosan {data.get('tadbirkorlik_turi', 'Aniqlanmagan')} rivojlangan ({data.get('tadbirkorlik_boshqa', '')}).
        7.  ✈️ Turizm salohiyati: {data.get('turizm', 'Yoq')} ({data.get('turizm_batafsil', '')}).
        8.  ⚠️ Aholi eng ko'p ehtiyoj sezayotgan sohalar: {data.get('ehtiyojlar', 'Aniqlanmagan')}.

        🎯 VAZIFA:
        Yuqoridagi demografik va iqtisodiy ko'rsatkichlarni, shuningdek raqobat muhitini chuqur tahlil qilib, shu mahallada ochish eng ko'p foyda keltiradigan 3 ta biznesni taklif qiling.

        TALABLAR:
        - "Reason" (Asos): Nega aynan shu biznes? (Masalan: "Maktablar ko'pligi va yoshlar soni yuqoriligi sababli o'quv markaziga talab katta bo'ladi").
        - "Investment": Taxminiy boshlang'ich sarmoya (USD yoki So'mda).
        - "Profitability": Kutilayotgan oylik sof foyda va loyihaning o'zini qoplash muddati.

        JAVOB FORMATI (JSON SHART):
        {{
          "summary": "Mahalla bozorining qisqacha professional tahlili (2-3 gap)",
          "top_businesses": [
            {{
              "name": "Biznes Nomi (Masalan: O'quv Markazi)",
              "reason": "Asoslovchi sabab (Demografiya va ehtiyojga bog'lang)",
              "investment": "Masalan: $3,000 - $5,000",
              "profitability": "Masalan: Oyiga $500-$800, 6 oyda qoplaydi"
            }},
            {{
              "name": "Biznes Nomi 2",
              "reason": "...",
              "investment": "...",
              "profitability": "..."
            }},
            {{
              "name": "Biznes Nomi 3",
              "reason": "...",
              "investment": "...",
              "profitability": "..."
            }}
          ]
        }}
        """

    def _generate_fallback_mahalla_content(self, data: Dict) -> Dict:
        """API ishlamagan holatda zaxira javob"""
        return {
            "summary": "Tizimda texnik yuklama mavjud, lekin umumiy demografik tahlilga ko'ra quyidagi yo'nalishlar tavsiya etiladi.",
            "top_businesses": [
                {
                    "name": "Oziq-ovqat va kundalik ehtiyojlar do'koni",
                    "reason": "Aholi yashash punktlarida bu eng barqaror va xavfsiz (bankrot bo'lmaydigan) biznes turi hisoblanadi.",
                    "investment": "$5,000 - $15,000",
                    "profitability": "Barqaror, oylik $600-$1200 foyda"
                },
                {
                    "name": "O'quv markazi (IT va Xorijiy tillar)",
                    "reason": f"Hududdagi yoshlar soni ({data.get('yoshlar_soni', 'kop')}) va maktablar mavjudligi ta'limga doimiy yuqori talabni yaratadi.",
                    "investment": "$3,000 - $8,000",
                    "profitability": "Yuqori marjali (6-9 oyda qoplaydi)"
                },
                {
                    "name": "Servis markazi (Sartaroshxona/Tikuvchilik)",
                    "reason": "Aholiga maishiy xizmat ko'rsatish har doim kerak va katta sarmoya talab qilmaydi.",
                    "investment": "$2,000 - $5,000",
                    "profitability": "O'rtacha va doimiy daromad"
                }
            ]
        }