"""
Gemini Monthly Horoscope Generation Rules

This file contains ONLY the rules for monthly prediction generation.
Load this file when generating a monthly prediction.
"""

MONTHLY_RULES = """
MONTHLY HOROSCOPE RULES

1. Focus of the Month:
   - Describe two or three major themes shaping the month.
   - Emphasize development, clarity, internal shifts, and long-term influences.
   - Describe how energy may evolve from early to later weeks.

2. Structure:
   - Internally draft the full monthly horoscope body first.
   - Then create Kuukauden miete, one or two sentences that condense the main themes and emotional focus of the month, clearly derived from the drafted text.
   - The final output MUST begin with a separate line: Kuukauden miete: <one or two sentences in the customer language>
   - Immediately after this line, output the full monthly horoscope text in paragraph form, addressing the reader directly.

3. Restrictions:
   - No exact dates, promises, or deterministic predictions.
   - No health or financial guarantees.
   - No fallback text is allowed under any circumstances.

4. Output Requirement:
   - End with a summary statement (in customer's language, e.g. "Kuukauden aikomus:" for Finnish).

5. Word Count:
   - 180 to 300 words, excluding the Kuukauden miete line.

6. Formatting:
   - NEVER use markdown formatting symbols like ** or * for bold/italic.
   - All section headers must be in the customer's language.

7. Content Areas to Cover:
   - Main theme of the month
   - Work, career, and professional life
   - Relationships and social connections
   - Personal well-being and energy
"""

# Finnish output format
MONTHLY_OUTPUT_FORMAT_FI = """
MUOTO (TÄRKEÄÄ - ÄLÄ KÄYTÄ ** TAI * MERKINTÖJÄ):

Kuukauden miete: [yksi tai kaksi lausetta]

[Ennustuksen teksti 180-300 sanaa kattaen:
- Kuukauden pääteema
- Työ ja ura
- Ihmissuhteet
- Hyvinvointi]

Kuukauden aikomus: [tiivistelmälause]
"""

# English output format
MONTHLY_OUTPUT_FORMAT_EN = """
OUTPUT FORMAT (IMPORTANT - DO NOT USE ** OR * MARKERS):

Monthly Thought: [one or two sentences]

[Prediction text 180-300 words covering:
- Main theme of the month
- Career and work
- Relationships
- Well-being]

Monthly Intention: [summary sentence]
"""

# Swedish output format
MONTHLY_OUTPUT_FORMAT_SV = """
UTMATNINGSFORMAT (VIKTIGT - ANVÄND INTE ** ELLER * MARKERINGAR):

Månadens tanke: [en eller två meningar]

[Förutsägelsetext 180-300 ord som täcker:
- Månadens huvudtema
- Karriär och arbete
- Relationer
- Välbefinnande]

Månadens intention: [sammanfattande mening]
"""

def get_monthly_output_format(language: str) -> str:
    """Get the output format instructions for monthly predictions in the specified language."""
    formats = {
        "fi": MONTHLY_OUTPUT_FORMAT_FI,
        "sv": MONTHLY_OUTPUT_FORMAT_SV,
        "en": MONTHLY_OUTPUT_FORMAT_EN
    }
    return formats.get(language, MONTHLY_OUTPUT_FORMAT_EN)

