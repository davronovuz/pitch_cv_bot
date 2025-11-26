import aiohttp
import asyncio
import logging
from typing import Optional, Dict
import json

logger = logging.getLogger(__name__)


class GammaAPI:
    """
    Gamma API client - professional prezentatsiya yaratish
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.gamma.app/api/v1"
        self.timeout = aiohttp.ClientTimeout(total=600)  # 10 daqiqa

    async def create_presentation_from_text(
        self,
        text_content: str,
        title: str = "Prezentatsiya"
    ) -> Optional[Dict]:
        """
        Matn asosida prezentatsiya yaratish

        Args:
            text_content: OpenAI dan kelgan content (formatli matn)
            title: Prezentatsiya sarlavhasi

        Returns:
            {'document_id': '...', 'status': '...'} yoki None
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "text": text_content,
            "type": "presentation",
            "title": title
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                logger.info(f"Gamma API: Prezentatsiya yaratish boshlandi - {title}")

                async with session.post(
                    f"{self.base_url}/documents",
                    headers=headers,
                    json=payload
                ) as response:

                    if response.status in (200, 201):
                        result = await response.json()
                        document_id = result.get('id') or result.get('document_id')

                        logger.info(f"Gamma API: Yaratildi - ID: {document_id}")

                        return {
                            'document_id': document_id,
                            'status': 'processing',
                            'result': result
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Gamma API xato ({response.status}): {error_text}")
                        return None

        except asyncio.TimeoutError:
            logger.error("Gamma API: Timeout (10 daqiqa)")
            return None
        except Exception as e:
            logger.exception(f"Gamma API xato: {e}")
            return None

    async def check_status(self, document_id: str) -> Optional[Dict]:
        """
        Prezentatsiya holatini tekshirish

        Returns:
            {'status': 'processing' | 'completed' | 'failed', 'progress': 0-100} yoki None
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.base_url}/documents/{document_id}",
                    headers=headers
                ) as response:

                    if response.status == 200:
                        result = await response.json()

                        status = result.get('status', 'unknown')
                        progress = result.get('progress', 0)

                        logger.info(f"Gamma API status: {status} ({progress}%)")

                        return {
                            'status': status,
                            'progress': progress,
                            'result': result
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Status tekshirish xato ({response.status}): {error_text}")
                        return None

        except Exception as e:
            logger.exception(f"Status xato: {e}")
            return None

    async def download_pptx(self, document_id: str, output_path: str) -> bool:
        """
        Tayyor prezentatsiyani PPTX formatda yuklab olish

        Args:
            document_id: Gamma document ID
            output_path: Saqlash yo'li (/path/to/file.pptx)

        Returns:
            True - muvaffaqiyatli, False - xato
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                logger.info(f"Gamma API: PPTX yuklab olish - {document_id}")

                # Export endpoint
                async with session.get(
                    f"{self.base_url}/documents/{document_id}/export?format=pptx",
                    headers=headers
                ) as response:

                    if response.status == 200:
                        content = await response.read()
                        with open(output_path, 'wb') as f:
                            f.write(content)

                        logger.info(f"Gamma API: PPTX saqlandi - {output_path}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Download xato ({response.status}): {error_text}")
                        return False

        except Exception as e:
            logger.exception(f"Download xato: {e}")
            return False

    async def wait_for_completion(
        self,
        document_id: str,
        timeout_seconds: int = 600,
        check_interval: int = 10
    ) -> bool:
        """
        Prezentatsiya tayyor bo'lishini kutish

        Args:
            document_id: Gamma document ID
            timeout_seconds: Maksimal kutish vaqti (sekundlarda)
            check_interval: Tekshirish intervali (sekundlarda)

        Returns:
            True - tayyor, False - xato yoki timeout
        """
        elapsed = 0

        while elapsed < timeout_seconds:
            status_info = await self.check_status(document_id)

            if not status_info:
                logger.error("Status tekshirib bo'lmadi")
                await asyncio.sleep(check_interval)
                elapsed += check_interval
                continue

            status = status_info.get('status', '').lower()
            progress = status_info.get('progress', 0)

            if status in ('completed', 'done'):
                logger.info(f"Prezentatsiya tayyor! (Progress: {progress}%)")
                return True

            if status in ('failed', 'error'):
                logger.error("Prezentatsiya yaratishda xato!")
                return False

            logger.info(f"Kutilmoqda... Status: {status} ({progress}%)")
            await asyncio.sleep(check_interval)
            elapsed += check_interval

        logger.error(f"Timeout! {timeout_seconds} sekund o'tdi")
        return False

    def format_content_for_gamma(self, content: Dict, content_type: str) -> str:
        """
        OpenAI contentini Gamma uchun formatlash

        Args:
            content: OpenAI dan kelgan JSON
            content_type: 'pitch_deck' yoki 'presentation'

        Returns:
            Gamma API uchun formatli matn
        """
        if content_type == 'pitch_deck':
            return self._format_pitch_deck(content)
        else:
            return self._format_presentation(content)

    def _format_pitch_deck(self, content: Dict) -> str:
        """Pitch deck formatli matn"""
        formatted = f"""# {content.get('project_name', 'Pitch Deck')}

{content.get('tagline', '')}

Taqdim etmoqda: {content.get('author', '')}

---

## {content.get('problem_title', 'MUAMMO')}

{content.get('problem', '')}

---

## {content.get('solution_title', 'YECHIM')}

{content.get('solution', '')}

---

## {content.get('market_title', 'BOZOR')}

{content.get('market', '')}

---

## {content.get('business_title', 'BIZNES MODEL')}

{content.get('business_model', '')}

---

## {content.get('competition_title', 'RAQOBAT')}

{content.get('competition', '')}

---

## {content.get('advantage_title', 'USTUNLIKLAR')}

{content.get('advantage', '')}

---

## {content.get('financials_title', 'MOLIYA')}

{content.get('financials', '')}

---

## {content.get('team_title', 'JAMOA')}

{content.get('team', '')}

---

## {content.get('milestones_title', "YO'L XARITASI")}

{content.get('milestones', '')}

---

## KELING, BIRGALIKDA ISHLAYMIZ!

{content.get('cta', '')}
"""
        return formatted.strip()

    def _format_presentation(self, content: Dict) -> str:
        """Oddiy prezentatsiya formatli matn"""
        formatted = f"# {content.get('title', 'Prezentatsiya')}\n\n{content.get('subtitle', '')}\n\n---\n\n"

        slides = content.get('slides', [])

        for slide in slides:
            slide_title = slide.get('title', '')
            slide_content = slide.get('content', '')
            bullet_points = slide.get('bullet_points', [])

            formatted += f"## {slide_title}\n\n{slide_content}\n\n"

            if bullet_points:
                for point in bullet_points:
                    formatted += f"• {point}\n"

            formatted += "\n---\n\n"

        return formatted.strip()
