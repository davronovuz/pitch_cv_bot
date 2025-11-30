# ==================== GAMMA THEMES DATA ====================
# Theme ma'lumotlari - rasmlar bilan

THEMES = [
    {
        "id": "Chisel",
        "name": "Chisel",
        "emoji": "🤍",
        "description": "Oq, minimalist, professional",
        "file_id": "AgACAgIAAxkBAAISg2kqlcP0M9qlqfLLTskFcNzdggILAAJkDGsbR6lZSQXlPpH1qahPAQADAgADbQADNgQ"
    },
    {
        "id": "Vortex",
        "name": "Vortex",
        "emoji": "🖤",
        "description": "Qora, elegant, zamonaviy",
        "file_id": "AgACAgIAAxkBAAIShWkqleWA-LiECwi2RLSCduv-7D7YAAJlDGsbR6lZSYtNOrvH8fYZAQADAgADbQADNgQ"
    },
    {
        "id": "Stratos",
        "name": "Stratos",
        "emoji": "🔵",
        "description": "To'q ko'k, ishonchli, korporativ",
        "file_id": "AgACAgIAAxkBAAISh2kqlgirHFH5CAfcCbiuaWjXvM-NAAJnDGsbR6lZSSHzg25_94hIAQADAgADbQADNgQ"
    },
    {
        "id": "Prism",
        "name": "Prism",
        "emoji": "💗",
        "description": "Och pushti, ijodiy, yengil",
        "file_id": "AgACAgIAAxkBAAISiWkqlkz0bul1RjhusLaorO7NdBmiAAJoDGsbR6lZSUaXQGw9CR3WAQADAgADbQADNgQ"
    },
    {
        "id": "Seafoam",
        "name": "Seafoam",
        "emoji": "🌊",
        "description": "Moviy-yashil, tinch, tabiiy",
        "file_id": "AgACAgIAAxkBAAISi2kqlneBenRkNRaJNXhrQGPczIwpAAJpDGsbR6lZSUjVHDbWXu2KAQADAgADbQADNgQ"
    },
    {
        "id": "Night Sky",
        "name": "Night Sky",
        "emoji": "🌙",
        "description": "To'q binafsha, sirli, premium",
        "file_id": "AgACAgIAAxkBAAISjWkqlp-GZw3gi0d3vsfm22yQdHPYAAJqDGsbR6lZSSKCy6ojUnJ5AQADAgADbQADNgQ"
    },
    {
        "id": "Coral Glow",
        "name": "Coral Glow",
        "emoji": "🌸",
        "description": "Pushti gradient, iliq, do'stona",
        "file_id": "AgACAgIAAxkBAAISj2kqlsNCa6Kzc99Ge8OVG7NfjaAfAAJrDGsbR6lZSabVBaGA-KVpAQADAgADbQADNgQ"
    },
    {
        "id": "Spectrum",
        "name": "Spectrum",
        "emoji": "🌈",
        "description": "Rang-barang, quvnoq, ijodiy",
        "file_id": "AgACAgIAAxkBAAISkWkqlt44EnWghC1N-pnFkKMvQw71AAJsDGsbR6lZSdD7lcPtmTE5AQADAgADbQADNgQ"
    },
    {
        "id": "Creme",
        "name": "Creme",
        "emoji": "☕",
        "description": "Krem, iliq, klassik",
        "file_id": "AgACAgIAAxkBAAISk2kqlwFepEgQJU7zgqi87ED3jiwoAAJtDGsbR6lZSZqv85jWLTkYAQADAgADbQADNgQ"
    },
    {
        "id": "Nebulae",
        "name": "Nebulae",
        "emoji": "✨",
        "description": "Kosmik, qorong'i, effektli",
        "file_id": "AgACAgIAAxkBAAISlWkqlxsn8vjI0FVusTiqt_drEO37AAJuDGsbR6lZSc0oJ5I12SHJAQADAgADbQADNgQ"
    }
]


def get_theme_by_id(theme_id: str) -> dict:
    """Theme ID bo'yicha olish"""
    for theme in THEMES:
        if theme["id"] == theme_id:
            return theme
    return None


def get_theme_by_index(index: int) -> dict:
    """Index bo'yicha olish (0-9)"""
    if 0 <= index < len(THEMES):
        return THEMES[index]
    return None


def get_all_themes() -> list:
    """Barcha theme'lar"""
    return THEMES


def get_themes_count() -> int:
    """Theme'lar soni"""
    return len(THEMES)