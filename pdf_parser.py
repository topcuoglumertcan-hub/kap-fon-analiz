import pdfplumber
import re


def parse_pdf(pdf_file):

    text = ""

    with pdfplumber.open(pdf_file) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    result = {}

    # Fon Kodu (PHE, TLY, THF vb.)
    match = re.search(r"\b([A-Z]{3})-([^\n]+)", text)
    if match:
        result["Fon Kodu"] = match.group(1)
        result["Fon Adı"] = match.group(2).strip()

    # Dönem (Haziran-2026 gibi)
    period = re.search(
        r"(Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)-20\d{2}",
        text
    )

    if period:
        result["Dönem"] = period.group(0)

    # Fon Toplam Değeri
    total = re.search(
        r"FON TOPLAM DEĞERİ\s+([\d\.,]+)",
        text
    )

    if total:
        result["Fon Toplam Değeri"] = total.group(1)

    return result
