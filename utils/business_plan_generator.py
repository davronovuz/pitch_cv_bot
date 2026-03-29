# utils/business_plan_generator.py
# Professional biznes plan generator - GPT-4o multi-step

import asyncio
import json
import logging
from typing import Dict, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class BusinessPlanGenerator:
    """
    GPT-4o bilan professional biznes plan yaratish.
    Har bir bo'lim alohida API call - sifat va uzunlik uchun.
    """

    CATEGORIES = {
        "IT": "IT va Texnologiya",
        "Savdo": "Savdo va Do'konlar",
        "Qishloq": "Qishloq xo'jaligi",
        "Xizmat": "Xizmat ko'rsatish",
        "Ishlab": "Ishlab chiqarish",
        "Turizm": "Turizm va Mehmonxona",
        "Umumiy": "Boshqa soha",
    }

    LANG_MAP = {
        "uz": "O'zbek tilida (lotin yozuvida)",
        "ru": "Rus tilida",
        "en": "English",
    }

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
            self,
            business_name: str,
            industry: str,
            description: str,
            investment: str,
            target_market: str,
            language: str = "uz",
    ) -> Optional[Dict]:
        """
        To'liq professional biznes plan yaratish.
        Qaytaradi: dict with all sections.
        """
        lang_instr = self.LANG_MAP.get(language, self.LANG_MAP["uz"])
        context = (
            f"Biznes nomi: {business_name}\n"
            f"Soha: {industry}\n"
            f"Tavsif: {description}\n"
            f"Investitsiya hajmi: {investment}\n"
            f"Maqsadli bozor: {target_market}"
        )

        logger.info(f"Biznes plan generatsiya boshlandi: {business_name}")

        try:
            # Step 1: Executive Summary
            logger.info("Step 1: Executive Summary...")
            executive_summary = await self._generate_section(
                section="IJROIYA XULOSASI (EXECUTIVE SUMMARY)",
                instructions=(
                    "Biznes rejaning eng muhim qismi. 400-500 so'z. "
                    "Quyidagilarni qamrab ol: biznes g'oyasi, bozordagi muammo va yechim, "
                    "maqsadli auditoriya, daromad modeli, moliyaviy prognoz xulosa, "
                    "kerakli investitsiya va uning maqsadi. Investor e'tiborini tortadigan "
                    "kuchli, ishontiruvchi uslubda yoz."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=400,
            )
            await asyncio.sleep(0.5)

            # Step 2: Company Description
            logger.info("Step 2: Kompaniya tavsifi...")
            company_description = await self._generate_section(
                section="KOMPANIYA TAVSIFI",
                instructions=(
                    "500-700 so'z. Quyidagilarni batafsil yoz: "
                    "1) Kompaniyaning missiyasi (nima uchun mavjud); "
                    "2) Vizyon (5 yildan keyin qanday bo'ladi); "
                    "3) Asosiy qadriyatlar (4-5 ta); "
                    "4) Yuridik shakl va ro'yxatga olish; "
                    "5) Joylashuv va infratuzilma; "
                    "6) Qisqacha tarix yoki g'oyaning paydo bo'lish tarixi."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=500,
            )
            await asyncio.sleep(0.5)

            # Step 3: Market Analysis
            logger.info("Step 3: Bozor tahlili...")
            market_analysis = await self._generate_section(
                section="BOZOR TAHLILI",
                instructions=(
                    "800-1000 so'z. Quyidagilarni batafsil yoz: "
                    "1) Umumiy bozor hajmi (TAM) - raqamlar bilan; "
                    "2) Manzilli bozor (SAM) - foiz va raqam; "
                    "3) Olinadigan ulush (SOM) - birinchi yil; "
                    "4) Bozor tendensiyalari va o'sish sur'ati; "
                    "5) Asosiy raqobatchilar (3-5 ta, kuchli va zaif tomonlari jadval ko'rinishida); "
                    "6) SWOT tahlili (kuchli, zaif tomonlar, imkoniyatlar, tahdidlar); "
                    "7) Raqobatdosh ustunlik - nima uchun biz yaxshiroqmiz."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=800,
            )
            await asyncio.sleep(0.5)

            # Step 4: Product/Service
            logger.info("Step 4: Mahsulot/Xizmat...")
            product_service = await self._generate_section(
                section="MAHSULOT VA XIZMATLAR",
                instructions=(
                    "600-800 so'z. Quyidagilarni batafsil yoz: "
                    "1) Mahsulot/xizmatning batafsil tavsifi; "
                    "2) Asosiy xususiyatlar va imkoniyatlar; "
                    "3) Noyob qiymat taklifi (USP - Unique Value Proposition); "
                    "4) Texnologiya yoki innovatsiya; "
                    "5) Narx strategiyasi (pricing tiers); "
                    "6) Intellektual mulk (patent, litsenziya, brend); "
                    "7) Mahsulot yo'l xaritasi - kelajak rejalar."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=600,
            )
            await asyncio.sleep(0.5)

            # Step 5: Marketing Strategy
            logger.info("Step 5: Marketing strategiyasi...")
            marketing_strategy = await self._generate_section(
                section="MARKETING VA SAVDO STRATEGIYASI",
                instructions=(
                    "700-900 so'z. Quyidagilarni batafsil yoz: "
                    "1) Maqsadli auditoriya portreti (demografiya, psixografiya); "
                    "2) Marketing kanallari (onlayn va oflayn, har birining ulushi); "
                    "3) Ijtimoiy tarmoqlar strategiyasi; "
                    "4) Mijoz jalb qilish narxi (CAC) va umrbod qiymati (LTV); "
                    "5) Savdo jarayoni (funnel); "
                    "6) Sheriklik va hamkorlik dasturlari; "
                    "7) Brend strategiyasi; "
                    "8) Birinchi 6 oylik marketing rejasi."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=700,
            )
            await asyncio.sleep(0.5)

            # Step 6: Operations Plan
            logger.info("Step 6: Operatsion reja...")
            operations_plan = await self._generate_section(
                section="OPERATSION REJA",
                instructions=(
                    "600-800 so'z. Quyidagilarni batafsil yoz: "
                    "1) Biznes jarayonlari (asosiy operatsiyalar qanday ishlaydi); "
                    "2) Ishlab chiqarish yoki xizmat ko'rsatish jarayoni; "
                    "3) Texnologiya va IT infratuzilma; "
                    "4) Yetkazib beruvchilar va ta'minot zanjiri; "
                    "5) Ish o'rinlari va xodimlar rejasi (staffing plan); "
                    "6) Ofis/omborxona/ishlab chiqarish maydoni; "
                    "7) Sifat nazorati; "
                    "8) Yo'l xaritasi (milestones) - 12 oylik."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=600,
            )
            await asyncio.sleep(0.5)

            # Step 7: Financial Projections
            logger.info("Step 7: Moliyaviy prognoz...")
            financial_projections = await self._generate_section(
                section="MOLIYAVIY PROGNOZ",
                instructions=(
                    "900-1100 so'z. Quyidagilarni RAQAMLAR va JADVALLAR bilan yoz: "
                    "1) Boshlang'ich investitsiya taqsimoti (jadval ko'rinishida); "
                    "2) Oylik xarajatlar tuzilmasi (doimiy + o'zgaruvchan); "
                    "3) Daromad prognozi (1-yil oyma-oy, 2-3 yil yillik); "
                    "4) Foyda va zarar hisobi (P&L) - 3 yillik; "
                    "5) Pul oqimi (Cash Flow) - birinchi yil oyma-oy; "
                    "6) Rentabellik nuqtasi (Break-even point) - qachon erishiladi; "
                    "7) ROI (investitsiyadan qaytim) - 3 yillik; "
                    "8) Asosiy moliyaviy ko'rsatkichlar (KPI). "
                    "Barcha raqamlarni aniq yoz, jadvallarda tartibli ko'rsat."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=900,
            )
            await asyncio.sleep(0.5)

            # Step 8: Team
            logger.info("Step 8: Jamoa...")
            team_section = await self._generate_section(
                section="BOSHQARUV JAMOASI",
                instructions=(
                    "400-500 so'z. Quyidagilarni yoz: "
                    "1) Asosiy lavozimlar va ularning vazifalari; "
                    "2) Har bir kalit pozitsiya uchun talab qilinadigan tajriba; "
                    "3) Kengash a'zolari yoki maslahatchilar (Advisory Board); "
                    "4) Kadrlar rivojlantirish rejasi; "
                    "5) Jamoa madaniyati va qiymatlar."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=400,
            )
            await asyncio.sleep(0.5)

            # Step 9: Risk Analysis
            logger.info("Step 9: Risk tahlili...")
            risk_analysis = await self._generate_section(
                section="RISK TAHLILI VA BOSHQARUV",
                instructions=(
                    "500-600 so'z. Quyidagilarni jadval ko'rinishida yoz: "
                    "1) Asosiy risklar (kamida 6 ta): bozor, moliyaviy, operatsion, raqobat, qonuniy, texnologik; "
                    "2) Har bir riskning ehtimoli (yuqori/o'rta/past); "
                    "3) Har bir riskning ta'sir darajasi; "
                    "4) Har bir risk uchun profilaktika chorasi; "
                    "5) Yuzaga kelsa muqobil harakat rejasi (Contingency Plan); "
                    "6) Sug'urta va himoya choralari."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=500,
            )
            await asyncio.sleep(0.5)

            # Step 10: Conclusion & Call to Action
            logger.info("Step 10: Xulosa...")
            conclusion = await self._generate_section(
                section="XULOSA VA INVESTORGA MUROJAAT",
                instructions=(
                    "300-400 so'z. Quyidagilarni yoz: "
                    "1) Loyihaning asosiy afzalliklari qisqacha xulosa; "
                    "2) Investorga nima taklif etiladi (ulush, foiz, qaytim); "
                    "3) Mablag'lardan foydalanish rejasi; "
                    "4) Keyingi qadamlar; "
                    "5) Aloqa va hamkorlik taklifi. "
                    "Ishontiruvchi, professional va ilhomlantiruvchi ohangda yoz."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=300,
            )

            logger.info("✅ Barcha bo'limlar yaratildi!")
            return {
                "business_name": business_name,
                "industry": industry,
                "investment": investment,
                "target_market": target_market,
                "language": language,
                "executive_summary": executive_summary,
                "company_description": company_description,
                "market_analysis": market_analysis,
                "product_service": product_service,
                "marketing_strategy": marketing_strategy,
                "operations_plan": operations_plan,
                "financial_projections": financial_projections,
                "team_section": team_section,
                "risk_analysis": risk_analysis,
                "conclusion": conclusion,
            }

        except Exception as e:
            logger.error(f"❌ Business plan generator xato: {e}")
            return None

    async def _generate_section(
            self,
            section: str,
            instructions: str,
            context: str,
            lang_instr: str,
            min_words: int,
    ) -> str:
        """Bitta bo'limni GPT-4o bilan yaratish"""
        prompt = f"""Sen professional biznes tahlilchi va strategist.
Quyidagi biznes uchun professional biznes rejaning "{section}" bo'limini yoz.

BIZNES MA'LUMOTLARI:
{context}

KO'RSATMALAR:
{instructions}

TIL: {lang_instr}
MINIMAL SO'Z SONI: {min_words}

MUHIM:
- Faqat matn yoz, ortiqcha izoh yoki sarlavha qo'shma
- Professional va ishbilarmon uslub ishlat
- Aniq raqamlar va faktlar keltir (taxminiy bo'lsa ham mantiqiy bo'lsin)
- Jadvallar kerak bo'lsa, matnda izohlangan holda ko'rsat"""

        for attempt in range(3):
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2500,
                    temperature=0.7,
                )
                text = response.choices[0].message.content.strip()
                word_count = len(text.split())
                logger.info(f"  '{section}': {word_count} so'z")
                return text
            except Exception as e:
                logger.error(f"  '{section}' attempt {attempt + 1} xato: {e}")
                if attempt < 2:
                    await asyncio.sleep(2)

        return f"[{section} bo'limini yaratishda xatolik yuz berdi]"
