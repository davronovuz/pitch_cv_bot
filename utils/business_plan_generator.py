# utils/business_plan_generator.py
# Professional biznes plan generator - GPT-4o multi-step

import asyncio
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
            business_name: str = "",
            industry: str = "",
            description: str = "",
            investment: str = "",
            target_market: str = "",
            language: str = "uz",
            initiator_type: str = "",
            company_info: str = "",
            personal_info: str = "",
            location: str = "",
            project_info: str = "",
            product_service: str = "",
            expenses: str = "",
            financing: str = "",
            credit_terms: str = "",
            marketing: str = "",
    ) -> Optional[Dict]:
        """
        To'liq professional biznes plan yaratish.
        Qaytaradi: dict with all sections.
        """
        lang_instr = self.LANG_MAP.get(language, self.LANG_MAP["uz"])

        # Project name fallback
        if not project_info and business_name:
            project_info = business_name
        if not product_service and industry:
            product_service = industry

        context = (
            f"=== LOYIHA PASPORTI ===\n"
            f"1. Tashabbuskor turi: {initiator_type or '—'}\n"
            f"2. Korxona nomi va faoliyati: {company_info or '—'}\n"
            f"3. Tashabbuskor (F.I.Sh + tel): {personal_info or '—'}\n"
            f"4. Hudud: {location or '—'}\n"
            f"5. Loyiha nomi va maqsadi: {project_info or '—'}\n"
            f"6. Mahsulot/xizmat: {product_service or '—'}\n"
            f"7. Xarajatlar (uskuna/tovar va qiymat): {expenses or '—'}\n"
            f"8. Moliyalashtirish (o'z mablag' + kredit): {financing or '—'}\n"
            f"9. Kredit shartlari (foiz va muddat): {credit_terms or '—'}\n"
            f"10. Marketing usullari: {marketing or '—'}\n"
        )

        logger.info(f"Biznes plan generatsiya boshlandi: {project_info or business_name}")

        try:
            # Step 1: Executive Summary
            logger.info("Step 1: Ijroiya xulosasi...")
            executive_summary = await self._generate_section(
                section="IJROIYA XULOSASI (EXECUTIVE SUMMARY)",
                instructions=(
                    "Biznes rejaning eng muhim qismi. 450-600 so'z. "
                    "Loyiha pasportidagi ANIQ ma'lumotlardan foydalanib yoz:\n"
                    "1) Loyiha nomi, joylashuvi va tashabbuskor turi aniq ko'rsatilsin.\n"
                    "2) Taklif etiladigan aniq mahsulot/xizmat va u yechadigan muammo.\n"
                    "3) Maqsadli auditoriya va hudud (paspartdagi hudud aniq yozilsin).\n"
                    "4) Kerakli umumiy investitsiya hajmi: o'z mablag' + kredit miqdori ANIQ raqam bilan.\n"
                    "5) Kredit foizi va muddati aniq ko'rsatilsin.\n"
                    "6) Kutilayotgan oylik daromad, sof foyda va qoplanish muddati (payback period).\n"
                    "7) Loyihaning ijtimoiy-iqtisodiy ahamiyati (soliq, ish o'rinlari).\n"
                    "Bankirlar yoki investorlar qiziqadigan, ishontiruvchi, aniq raqamlar asosida yoz."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=450,
            )
            await asyncio.sleep(0.5)

            # Step 2: Company / Initiator Description
            logger.info("Step 2: Tashabbuskor va kompaniya tavsifi...")
            company_description = await self._generate_section(
                section="TASHABBUSKOR VA KOMPANIYA TAVSIFI",
                instructions=(
                    "500-700 so'z. Quyidagilarni LOYIHA PASPORTIDAGI ANIQ MA'LUMOTLAR asosida yoz:\n"
                    "1) Tashabbuskorning turi (jismoniy shaxs / tadbirkorlik subyekti) va shaxsiy ma'lumotlari.\n"
                    "   (Telefon raqam to'liq ochiq yozilmasin, oxirgi 4 raqami * bilan yashirilsin.)\n"
                    "2) Agar tadbirkorlik subyekti bo'lsa — korxona nomi, yuridik shakli va faoliyat turi.\n"
                    "3) Missiya (loyiha nima uchun kerak — maqsaddan kelib chiqib).\n"
                    "4) Vizyon — 3-5 yildan keyingi holat (mavjud loyiha miqyosidan kelib chiqib realistik).\n"
                    "5) Asosiy qadriyatlar (4-5 ta).\n"
                    "6) Joylashuv va infratuzilma — HUDUD paspartdagidek aniq yozilsin.\n"
                    "7) Ro'yxatga olish tartibi (O'zbekiston Respublikasi qonunchiligiga muvofiq).\n"
                    "8) Tashabbuskorning kompetensiyasi va loyihaga tayyorlik darajasi."
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
                    "800-1000 so'z. Loyiha hududi (paspartda ko'rsatilgan) uchun ANIQ ma'lumotlar bilan yoz:\n"
                    "1) O'zbekiston yoki mintaqa bozoridagi umumiy hajm (TAM) — raqamlar bilan.\n"
                    "2) Manzilli bozor (SAM) — paspartdagi hudud uchun ulush va foiz.\n"
                    "3) Olinadigan ulush (SOM) — birinchi yil realistik rejadan.\n"
                    "4) Demografik tahlil (paspartdagi hudud aholisi, daromad, iste'mol).\n"
                    "5) Bozor tendensiyalari va o'sish sur'ati (oxirgi yillar statistikasi).\n"
                    "6) Asosiy raqobatchilar (3-5 ta, aynan shu hududdagi yoki o'xshash loyihalar). "
                    "Har biri uchun kuchli va zaif tomonlari JADVAL ko'rinishida (matnda izohlangan jadval).\n"
                    "7) SWOT tahlili (alohida 4 bandda: Kuchli, Zaif, Imkoniyat, Tahdid — har birida kamida 4 ta band).\n"
                    "8) Raqobatdosh ustunlik — nima uchun bu loyiha yaxshiroq (paspartdagi xususiyatlarga tayanib)."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=800,
            )
            await asyncio.sleep(0.5)

            # Step 4: Product/Service
            logger.info("Step 4: Mahsulot va xizmatlar...")
            product_service_sec = await self._generate_section(
                section="MAHSULOT VA XIZMATLAR",
                instructions=(
                    "600-800 so'z. Paspartdagi 'Mahsulot/xizmat' bandi asosida yoz:\n"
                    "1) Taklif etiladigan mahsulot/xizmatning batafsil tavsifi (assortiment, turkumlar).\n"
                    "2) Asosiy xususiyatlar va iste'molchi uchun imkoniyatlar.\n"
                    "3) Noyob qiymat taklifi (USP) — aynan shu loyihaning farqli tomoni.\n"
                    "4) Texnologiya/uskunalar (paspartdagi 'Xarajatlar' bandidan kelib chiqib, qanday uskunalar va ular qaysi mahsulot/xizmat uchun).\n"
                    "5) NARX STRATEGIYASI — har bir mahsulot/xizmat turi bo'yicha taxminiy narx "
                    "(hudud va raqobat bozori asosida, so'mda). Jadval ko'rinishida ko'rsating.\n"
                    "6) Sifat va standartlar (O'zDst, GOST yoki soha standartlari).\n"
                    "7) Mahsulot/xizmat rivoji — keyingi 1-3 yildagi kengaytirish rejasi."
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
                    "700-900 so'z. Paspartdagi 'Marketing' bandidagi KANALLARDAN asosiy tayanch sifatida foydalan:\n"
                    "1) Maqsadli auditoriya portreti — paspartdagi hudud aholisidan kelib chiqib "
                    "(yosh, daromad, odatlar, sotib olish xatti-harakati).\n"
                    "2) Marketing kanallari — paspartda ko'rsatilgan usullarni asos qilib, "
                    "har biri bo'yicha alohida strategiya (onlayn: Telegram, Instagram, Facebook; oflayn: bannerlar, mahalla e'lonlari, og'zaki tavsiya).\n"
                    "3) Har bir kanal uchun oylik marketing byudjeti taqsimoti (jadval ko'rinishida).\n"
                    "4) Mijoz jalb qilish narxi (CAC) va umrbod qiymati (LTV).\n"
                    "5) Savdo jarayoni (funnel) — mijoz qanday bosqichlardan o'tadi.\n"
                    "6) Sheriklik va hamkorlik dasturlari (yetkazib beruvchilar, korporativ mijozlar).\n"
                    "7) Brend strategiyasi — logo, slogan, brend ohangi.\n"
                    "8) Birinchi 6 oylik marketing rejasi — oyma-oy jadval."
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
                    "600-800 so'z. Paspartdagi hudud va xarajatlar asosida yoz:\n"
                    "1) Biznes jarayonlari — mijoz buyurtma berishdan tortib mahsulot/xizmat yetkazishgacha.\n"
                    "2) Ishlab chiqarish yoki xizmat ko'rsatish jarayoni (bosqichlar jadvalda).\n"
                    "3) Uskunalar va texnologiya — paspartdagi 'Xarajatlar' bandidan aynan qaysi uskunalar, qancha va qayerdan.\n"
                    "4) Yetkazib beruvchilar va ta'minot zanjiri (hudud/O'zbekiston/chetdan).\n"
                    "5) Ish o'rinlari va xodimlar rejasi (staffing plan) — lavozim, soni, oylik maosh JADVAL ko'rinishida.\n"
                    "6) Ofis/do'kon/omborxona/ishlab chiqarish maydoni — paspartdagi hududda.\n"
                    "7) Sifat nazorati va standartlarga muvofiqlik.\n"
                    "8) Loyihani amalga oshirish kalendari (milestones) — 12 oylik bosqichli jadval "
                    "(1-oy: ro'yxatdan o'tish, 2-oy: kredit olish, 3-oy: uskunalar, va hokazo)."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=600,
            )
            await asyncio.sleep(0.5)

            # Step 7: Financial Projections — MUHIM BO'LIM
            logger.info("Step 7: Moliyaviy prognoz...")
            financial_projections = await self._generate_section(
                section="MOLIYAVIY PROGNOZ",
                instructions=(
                    "1000-1300 so'z. BU ENG MUHIM BO'LIM — paspartdagi ANIQ RAQAMLARDAN foydalaning:\n"
                    "- Xarajatlar: paspartdagi '7. Xarajatlar' bandidan aynan qiymatlar va predmetlar.\n"
                    "- Moliyalashtirish: paspartdagi '8. Moliyalashtirish' — o'z mablag' va kredit ANIQ miqdorlari.\n"
                    "- Kredit shartlari: paspartdagi '9. Kredit shartlari' — foiz va muddat aniq qiymatlari.\n\n"
                    "Quyidagi JADVALLAR VA RAQAMLAR bilan yoz:\n\n"
                    "1) BOSHLANG'ICH INVESTITSIYA JADVALI: paspartdagi xarajatlar ro'yxati — "
                    "har bir band, miqdor, narx, jami. Pastki qatorda UMUMIY miqdor.\n\n"
                    "2) MOLIYALASHTIRISH MANBAI JADVALI:\n"
                    "   - O'z mablag': [paspartdagi miqdor], foizi %\n"
                    "   - Kredit: [paspartdagi miqdor], foizi %\n"
                    "   - Jami: 100%\n\n"
                    "3) KREDIT TO'LOV GRAFIGI — paspartdagi foiz va muddatdan kelib chiqib:\n"
                    "   - Yillik foiz: [%], muddat: [yil]\n"
                    "   - Har oylik to'lov miqdori (annuitet formulasi asosida hisoblang)\n"
                    "   - 1-yil oylik to'lov jadvali (oy, asosiy qarz, foiz, jami to'lov, qoldiq qarz).\n"
                    "   Annuitet formulasi: A = P × [r(1+r)^n] / [(1+r)^n - 1], "
                    "bu yerda P — qarz, r — oylik foiz, n — oylar soni.\n\n"
                    "4) OYLIK DOIMIY XARAJATLAR JADVALI (ish haqi, ijara, kommunal, reklama, soliq va boshqalar) — jami oylik xarajat.\n\n"
                    "5) DAROMAD PROGNOZI — 1-yil oyma-oy jadval (birinchi oylar past, keyin o'sadi), 2-3 yil yillik.\n\n"
                    "6) FOYDA VA ZARAR HISOBOTI (P&L) — 3 yillik jadval: Daromad, COGS, Yalpi foyda, Operatsion xarajatlar, "
                    "Kredit foizi, EBITDA, Soliqlar, Sof foyda.\n\n"
                    "7) PUL OQIMI (CASH FLOW) — 1-yil oyma-oy: kirim, chiqim, sof oqim, jamlangan.\n\n"
                    "8) RENTABELLIK NUQTASI (Break-even) — qachon 0 foydaga chiqiladi (oy va so'm).\n\n"
                    "9) QOPLANISH MUDDATI (Payback Period) — investitsiya necha oyda qaytadi.\n\n"
                    "10) ROI (Return on Investment) — 3 yillik foiz.\n\n"
                    "11) NPV va IRR (Net Present Value va Internal Rate of Return) — qisqacha.\n\n"
                    "MUHIM: barcha raqamlarni PASPARTdagi ma'lumotlarga mos va realistik yozing. "
                    "Jadvallarni matn ichida tartibli joylashtiring."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=1000,
            )
            await asyncio.sleep(0.5)

            # Step 8: Team
            logger.info("Step 8: Jamoa...")
            team_section = await self._generate_section(
                section="BOSHQARUV JAMOASI VA KADRLAR",
                instructions=(
                    "400-550 so'z. Quyidagilarni yoz:\n"
                    "1) Tashkiliy tuzilma (sxema matnda izohlangan holda).\n"
                    "2) Asosiy lavozimlar va vazifalari (direktor, hisobchi, xaridor, sotuvchi, va h.k.).\n"
                    "3) Har bir lavozim uchun talablar, ish haqi (paspartdagi hudud o'rtacha oylik maoshiga mos).\n"
                    "4) Kengash/maslahatchilar (agar bo'lsa).\n"
                    "5) Kadrlarni jalb qilish strategiyasi (paspartdagi hududdan).\n"
                    "6) Xodimlarni o'qitish va rivojlantirish rejasi.\n"
                    "7) Ijtimoiy paket va motivatsiya tizimi.\n"
                    "8) Ish o'rinlari soni va ijtimoiy ahamiyati."
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
                    "500-700 so'z. JADVAL ko'rinishida yoz (Risk | Ehtimol | Ta'sir | Profilaktika | Muqobil harakat):\n"
                    "Kamida 8 ta risk qamrab oling:\n"
                    "1) Bozor riski (talab pasayishi).\n"
                    "2) Moliyaviy risk (kredit to'lay olmaslik).\n"
                    "3) Valyuta riski (agar xom ashyo chetdan bo'lsa).\n"
                    "4) Operatsion risk (uskuna buzilishi, ta'minot uzilishi).\n"
                    "5) Raqobat riski (yangi raqobatchi paydo bo'lishi).\n"
                    "6) Qonuniy risk (qonunchilik o'zgarishi, litsenziya).\n"
                    "7) Texnologik risk (eskirgan texnologiya).\n"
                    "8) Inson resurslari riski (kadrlar yetishmasligi).\n"
                    "9) Tabiiy va forc-major risklar.\n\n"
                    "Har bir risk uchun:\n"
                    "- Ehtimol darajasi (Yuqori/O'rta/Past)\n"
                    "- Ta'sir darajasi (Yuqori/O'rta/Past)\n"
                    "- Profilaktika chorasi (aniq, amaliy)\n"
                    "- Muqobil harakat rejasi (Contingency Plan)\n\n"
                    "Oxirida: sug'urta va qo'shimcha himoya choralari."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=500,
            )
            await asyncio.sleep(0.5)

            # Step 10: Conclusion
            logger.info("Step 10: Xulosa...")
            conclusion = await self._generate_section(
                section="XULOSA VA INVESTOR/BANKGA MUROJAAT",
                instructions=(
                    "350-450 so'z. Quyidagilarni PASPORT asosidagi aniq raqamlar bilan yoz:\n"
                    "1) Loyihaning 3 ta asosiy afzalligi (qisqa ro'yxat).\n"
                    "2) Kerakli kredit miqdori va shartlari (paspartda ko'rsatilganicha).\n"
                    "3) Mablag'lardan foydalanish taqsimoti (qaysi xarajatga qancha).\n"
                    "4) Kutilayotgan qaytim va qoplanish muddati (aniq raqam).\n"
                    "5) Loyihaning ijtimoiy-iqtisodiy samarasi (ish o'rinlari, soliq, hudud rivojlanishi).\n"
                    "6) Keyingi qadamlar (loyihani boshlash uchun kerakli harakatlar ketma-ketligi).\n"
                    "7) Bank yoki investorga aniq murojaat va hamkorlik taklifi.\n"
                    "Ishontiruvchi, professional va amaliy ohangda yoz."
                ),
                context=context,
                lang_instr=lang_instr,
                min_words=350,
            )

            logger.info("✅ Barcha bo'limlar yaratildi!")
            return {
                "business_name": project_info or business_name,
                "industry": product_service or industry,
                "investment": financing or investment,
                "target_market": location or target_market,
                "language": language,
                # Paspart ma'lumotlari
                "initiator_type": initiator_type,
                "company_info": company_info,
                "personal_info": personal_info,
                "location": location,
                "project_info": project_info,
                "product_service": product_service,
                "expenses": expenses,
                "financing": financing,
                "credit_terms": credit_terms,
                "marketing": marketing,
                # Generatsiya qilingan bo'limlar
                "executive_summary": executive_summary,
                "company_description": company_description,
                "market_analysis": market_analysis,
                "product_service_section": product_service_sec,
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
        prompt = f"""Sen O'zbekiston bozori bo'yicha professional biznes tahlilchi va moliyaviy strategist.
Sening vazifang — bankka yoki investorga taqdim etish uchun ishonchli, aniq raqamlarga asoslangan biznes reja bo'limini yozish.

LOYIHA PASPORTI (mijoz bergan ANIQ ma'lumotlar):
{context}

YOZISH KERAK BO'LGAN BO'LIM: "{section}"

KO'RSATMALAR:
{instructions}

TIL: {lang_instr}
MINIMAL SO'Z SONI: {min_words}

QAT'IY QOIDALAR:
1. Pasporda berilgan ANIQ raqamlarni ishlat — o'zingdan asossiz raqam o'ylab topma.
2. Agar paspartda aniq miqdor bo'lsa (masalan, kredit 10 mln so'm), ayni shuni yoz.
3. Agar paspartda yo'q raqamlar kerak bo'lsa (masalan, ish haqi, ijara), O'zbekiston 2025-2026 yil hududi bozorga mos realistik qiymat qo'y va "taxminiy" deb ko'rsat.
4. Jadvallar yozganda matnli jadval formati ishlat (| ustun | ustun |) yoki aniq tartibli ro'yxat.
5. Valyuta — so'm (UZB so'm); chet el valyutasi bo'lsa ham so'mga taxminiy aylantir.
6. Matndan boshqa hech narsa qo'shma: sarlavha, izoh, "Quyida..." kabi kirishlar YO'Q.
7. Professional, aniq, ishonchli va amaliy uslub."""

        for attempt in range(3):
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=3000,
                    temperature=0.6,
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
