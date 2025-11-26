import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Optional
from aiogram import Bot
from aiogram.types import InputFile

logger = logging.getLogger(__name__)


class PresentationWorker:
    """
    Background worker - prezentatsiya yaratish uchun
    Bot qotib qolmasligi uchun alohida task'larda ishlaydi
    """

    def __init__(self, bot: Bot, user_db, content_generator, gamma_api):
        self.bot = bot
        self.user_db = user_db
        self.content_generator = content_generator
        self.gamma_api = gamma_api
        self.is_running = False
        self.worker_task = None

    async def start(self):
        """Worker'ni ishga tushirish"""
        if not self.is_running:
            self.is_running = True
            self.worker_task = asyncio.create_task(self._process_queue())
            logger.info("✅ Presentation Worker ishga tushdi")

    async def stop(self):
        """Worker'ni to'xtatish"""
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.info("❌ Presentation Worker to'xtatildi")

    async def _process_queue(self):
        """Queue'dan task'larni olish va ishga tushirish"""
        logger.info("Worker queue processing boshlandi")

        while self.is_running:
            try:
                # Kutilayotgan task'larni olish
                pending_tasks = self.user_db.get_pending_tasks()

                if pending_tasks:
                    logger.info(f"🔄 {len(pending_tasks)} ta task topildi")

                    # Har bir taskni parallel ishlatish
                    tasks = []
                    for task_data in pending_tasks:
                        tasks.append(self._process_task(task_data))

                    # Barcha task'larni parallel bajarish
                    await asyncio.gather(*tasks, return_exceptions=True)

                # Keyingi tekshirishgacha kutish
                await asyncio.sleep(5)  # 5 sekund

            except Exception as e:
                logger.error(f"Worker queue xato: {e}")
                await asyncio.sleep(10)

    async def _process_task(self, task_data: dict):
        """Bitta taskni qayta ishlash"""
        task_uuid = task_data.get('task_uuid')
        task_type = task_data.get('type')
        user_id = task_data.get('user_id')

        try:
            logger.info(f"🎯 Task boshlandi: {task_uuid} (Type: {task_type})")

            # Status'ni 'processing' ga o'zgartirish
            self.user_db.update_task_status(task_uuid, 'processing', progress=5)

            # User'ga xabar berish
            telegram_id = self._get_telegram_id(user_id)
            if telegram_id:
                await self.bot.send_message(
                    telegram_id,
                    f"⚙️ <b>Prezentatsiya yaratilmoqda...</b>\n\n"
                    f"🔑 Task ID: <code>{task_uuid}</code>\n"
                    f"📊 Progress: 5%",
                    parse_mode='HTML'
                )

            # 1. OpenAI bilan content yaratish
            logger.info(f"📝 OpenAI: Content yaratish - {task_uuid}")
            content = await self._generate_content(task_data)

            if not content:
                raise Exception("OpenAI content yaratilmadi")

            self.user_db.update_task_status(task_uuid, 'processing', progress=30)

            if telegram_id:
                await self.bot.send_message(
                    telegram_id,
                    f"⚙️ <b>Content tayyor!</b>\n\n"
                    f"📊 Progress: 30%\n"
                    f"🎨 Gamma API bilan dizayn qilinmoqda...",
                    parse_mode='HTML'
                )

            # 2. Gamma API'ga yuborish
            logger.info(f"🎨 Gamma API: Prezentatsiya yaratish - {task_uuid}")

            # Content formatlash
            formatted_text = self.gamma_api.format_content_for_gamma(
                content,
                task_type
            )

            # Gamma API'ga yuborish
            gamma_result = await self.gamma_api.create_presentation_from_text(
                formatted_text,
                title=content.get('project_name') or content.get('title', 'Prezentatsiya')
            )

            if not gamma_result:
                raise Exception("Gamma API prezentatsiya yaratilmadi")

            document_id = gamma_result.get('document_id')

            self.user_db.update_task_status(task_uuid, 'processing', progress=50)

            if telegram_id:
                await self.bot.send_message(
                    telegram_id,
                    f"⚙️ <b>Gamma API bilan ishlanyapti!</b>\n\n"
                    f"📊 Progress: 50%\n"
                    f"⏳ Tayyor bo'lishini kutmoqda...",
                    parse_mode='HTML'
                )

            # 3. Tayyor bo'lishini kutish
            logger.info(f"⏳ Gamma: Kutilmoqda - {document_id}")

            is_ready = await self.gamma_api.wait_for_completion(
                document_id,
                timeout_seconds=300,  # 5 daqiqa
                check_interval=10
            )

            if not is_ready:
                raise Exception("Gamma API timeout yoki xato")

            self.user_db.update_task_status(task_uuid, 'processing', progress=80)

            if telegram_id:
                await self.bot.send_message(
                    telegram_id,
                    f"✅ <b>Prezentatsiya tayyor!</b>\n\n"
                    f"📊 Progress: 80%\n"
                    f"📥 PPTX yuklab olinyapti...",
                    parse_mode='HTML'
                )

            # 4. PPTX yuklab olish
            logger.info(f"📥 Gamma: PPTX yuklab olish - {document_id}")

            # Fayl yo'lini aniqlash
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"presentation_{task_type}_{user_id}_{timestamp}.pptx"
            output_path = f"/tmp/{filename}"

            download_success = await self.gamma_api.download_pptx(document_id, output_path)

            if not download_success or not os.path.exists(output_path):
                raise Exception("PPTX yuklab olinmadi")

            self.user_db.update_task_status(
                task_uuid,
                'processing',
                progress=95,
                file_path=output_path
            )

            # 5. User'ga yuborish
            logger.info(f"📤 User'ga yuborish - {telegram_id}")

            if telegram_id:
                try:
                    with open(output_path, 'rb') as f:
                        caption = f"""
🎉 <b>Sizning prezentatsiyangiz tayyor!</b>

🔑 Task ID: <code>{task_uuid}</code>
📦 Turi: {task_type}
✨ AI optimizatsiyasi: ✅
🎨 Professional dizayn: ✅

Muvaffaqiyatlar! 🚀
"""

                        await self.bot.send_document(
                            telegram_id,
                            document=InputFile(f, filename=filename),
                            caption=caption,
                            parse_mode='HTML'
                        )

                    logger.info(f"✅ PPTX yuborildi - {telegram_id}")

                except Exception as e:
                    logger.error(f"User'ga yuborishda xato: {e}")
                    raise

            # 6. Task'ni 'completed' ga o'zgartirish
            self.user_db.update_task_status(
                task_uuid,
                'completed',
                progress=100,
                file_path=output_path
            )

            # 7. Temporary faylni o'chirish (ixtiyoriy)
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
                    logger.info(f"🗑 Temporary fayl o'chirildi: {output_path}")
            except:
                pass

            logger.info(f"✅ Task tugallandi: {task_uuid}")

        except Exception as e:
            logger.error(f"❌ Task xato: {task_uuid} - {e}")

            # Task'ni 'failed' ga o'zgartirish
            self.user_db.update_task_status(
                task_uuid,
                'failed',
                error_message=str(e)
            )

            # User'ga xabar berish
            telegram_id = self._get_telegram_id(user_id)
            if telegram_id:
                try:
                    await self.bot.send_message(
                        telegram_id,
                        f"❌ <b>Xatolik yuz berdi!</b>\n\n"
                        f"🔑 Task ID: <code>{task_uuid}</code>\n"
                        f"⚠️ Xato: {str(e)}\n\n"
                        f"Iltimos, qaytadan urinib ko'ring yoki support bilan bog'laning.",
                        parse_mode='HTML'
                    )
                except:
                    pass

    async def _generate_content(self, task_data: dict) -> Optional[dict]:
        """OpenAI bilan content yaratish"""
        task_type = task_data.get('type')
        answers_json = task_data.get('answers', '{}')

        try:
            answers_data = json.loads(answers_json)

            if task_type == 'pitch_deck':
                # Pitch deck
                answers = answers_data.get('answers', [])
                content = await self.content_generator.generate_pitch_deck_content(
                    answers,
                    use_gpt4=True  # Pitch deck uchun GPT-4
                )
            else:
                # Oddiy prezentatsiya
                topic = answers_data.get('topic', '')
                details = answers_data.get('details', '')
                slide_count = answers_data.get('slide_count', 10)

                content = await self.content_generator.generate_presentation_content(
                    topic,
                    details,
                    slide_count,
                    use_gpt4=False  # Prezentatsiya uchun GPT-3.5
                )

            return content

        except Exception as e:
            logger.error(f"Content generation xato: {e}")
            return None

    def _get_telegram_id(self, user_id: int) -> Optional[int]:
        """Database user_id dan telegram_id olish"""
        try:
            user = self.user_db.execute(
                "SELECT telegram_id FROM Users WHERE id = ?",
                parameters=(user_id,),
                fetchone=True
            )

            return user[0] if user else None

        except Exception as e:
            logger.error(f"Telegram ID olishda xato: {e}")
            return None