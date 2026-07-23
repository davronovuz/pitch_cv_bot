"""
Mahalla tahlili uchun kiritma (input) validatsiyasi.

Ikki tur:
  * parse_number  — raqamli maydonlar (aholi, yoshlar, ...) uchun.
  * is_meaningful — matnli maydonlar (mahalla nomi, ehtiyojlar) uchun,
                    "sdnjkcdecnjec" kabi bema'ni harflar to'plamini rad etadi.

AI chaqirmaydi — tez va bepul, oddiy qoidalar asosida.
"""
import re

# Lotin + kirill unlilari
VOWELS = set("aeiouAEIOU" "аеёиоуўэюяАЕЁИОУЎЭЮЯ")
_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)
# o‘ / g‘ dagi apostrof (turli xil kodlar) — tahlilda tashlab yuboriladi,
# aks holda undosh sifatida sanalib, "Doʻstlik" kabi nomlarni buzadi
_APOSTROPHES = "‘’ʻʼ`´'"
_APOS_RE = re.compile("[" + re.escape(_APOSTROPHES) + "]")


def parse_number(text: str, min_val: int = 0, max_val: int = 100_000_000):
    """
    Matndan butun sonni ajratib oladi. "5000", "5 000", "~5000",
    "taxminan 5000 kishi" — hammasidan 5000 chiqadi.

    Yaroqli bo'lsa int qaytaradi, aks holda None.
    """
    if text is None:
        return None
    digits = re.sub(r"[^\d]", "", str(text))
    if not digits:
        return None
    try:
        value = int(digits)
    except ValueError:
        return None
    if value < min_val or value > max_val:
        return None
    return value


def is_meaningful(text: str, min_len: int = 2) -> bool:
    """
    Matn "mazmunli" ko'rinadimi? Bema'ni klaviatura bosishlarini rad etadi.

    Rad etiladi:
      * juda qisqa (min_len dan kalta)
      * umuman unli yo'q
      * bir xil belgi takrorlangan ("aaaa", "....")
      * 4+ undosh ketma-ket KELIB, ayni paytda unlilar ulushi past
        (masalan "sdnjkcdecnjec")
    """
    if not text:
        return False
    s = str(text).strip()
    if len(s) < min_len:
        return False

    # o‘/g‘ apostrofini olib tashlaymiz (undosh deb sanalmasin)
    s = _APOS_RE.sub("", s)

    letters = _LETTER_RE.findall(s)
    # Harf umuman bo'lmasa: raqam bo'lsa mayli ("7-son"), faqat belgi bo'lsa yo'q
    if not letters:
        return bool(re.search(r"\d", s))

    # Bir xil belgining takrori ("aaaaa")
    if len(set(ch.lower() for ch in letters)) == 1 and len(letters) > 2:
        return False

    vowels = [ch for ch in letters if ch in VOWELS]
    if not vowels:
        return False

    vowel_ratio = len(vowels) / len(letters)

    # Eng uzun undoshlar ketma-ketligi
    max_run = run = 0
    for ch in letters:
        if ch in VOWELS:
            run = 0
        else:
            run += 1
            max_run = max(max_run, run)

    # Klaviatura bosish belgisi: uzun undosh zanjiri + kam unli
    if max_run >= 4 and vowel_ratio < 0.30:
        return False

    return True
