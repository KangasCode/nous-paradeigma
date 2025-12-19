"""
Gemini Daily Horoscope Generation Rules

This file contains ONLY the rules for daily prediction generation.
Load this file when generating a daily prediction.
"""

DAILY_RULES = """
DAILY HOROSCOPE RULES

1. Focus of the Day:
   - Describe the energetic or emotional tone of the day.
   - Highlight one opportunity or subtle challenge.
   - Keep the scope limited to today, short-term dynamics only.

2. Structure:
   - Internally draft the full daily horoscope body first.
   - Then derive one short Päivän sana, one word or very short phrase that clearly captures the core energy or theme of the already drafted text.
   - The final output MUST begin with a separate line: Päivän sana: <word or short phrase>
   - Immediately after this line, output the full daily horoscope text in paragraph form, addressing the reader directly.

3. Limitations:
   - No long-term predictions.
   - No references to weekly or monthly patterns.
   - No fallback or placeholder text allowed.

4. Output Requirement:
   - End with a practical suggestion line (in customer's language, e.g. "Päivän neuvo:" for Finnish).

5. Word Count:
   - 80 to 140 words, excluding the Päivän sana line.

6. Formatting:
   - NEVER use markdown formatting symbols like ** or * for bold/italic.
   - All section headers must be in the customer's language.
"""

# Finnish output format
DAILY_OUTPUT_FORMAT_FI = """
MUOTO (TÄRKEÄÄ - ÄLÄ KÄYTÄ ** TAI * MERKINTÖJÄ):

Päivän sana: [yksi sana tai lyhyt ilmaus]

[Ennustuksen teksti 80-140 sanaa, suoraan lukijalle]

Päivän neuvo: [yksi käytännön vinkki]
"""

# English output format
DAILY_OUTPUT_FORMAT_EN = """
OUTPUT FORMAT (IMPORTANT - DO NOT USE ** OR * MARKERS):

Word of the Day: [one word or short phrase]

[Prediction text 80-140 words, addressing reader directly]

Daily Advice: [one practical tip]
"""

# Swedish output format
DAILY_OUTPUT_FORMAT_SV = """
UTMATNINGSFORMAT (VIKTIGT - ANVÄND INTE ** ELLER * MARKERINGAR):

Dagens ord: [ett ord eller kort fras]

[Förutsägelsetext 80-140 ord, tilltal direkt till läsaren]

Dagens råd: [ett praktiskt tips]
"""

def get_daily_output_format(language: str) -> str:
    """Get the output format instructions for daily predictions in the specified language."""
    formats = {
        "fi": DAILY_OUTPUT_FORMAT_FI,
        "sv": DAILY_OUTPUT_FORMAT_SV,
        "en": DAILY_OUTPUT_FORMAT_EN
    }
    return formats.get(language, DAILY_OUTPUT_FORMAT_EN)

