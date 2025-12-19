"""
Gemini Weekly Horoscope Generation Rules

This file contains ONLY the rules for weekly prediction generation.
Load this file when generating a weekly prediction.
"""

WEEKLY_RULES = """
WEEKLY HOROSCOPE RULES

1. Focus of the Week:
   - Explain the rhythm of the week: beginning, middle, end.
   - Identify one background theme that influences the entire week.
   - Discuss progress, delays, or evolving emotional dynamics.

2. Structure:
   - Internally draft the full weekly horoscope body first.
   - Then create Viikon lause, exactly one complete sentence that summarizes the main theme or learning of the week, clearly connected to the drafted text.
   - Also create The Seven Lights Index:
     * Seven distinct integers between 1 and 40, inclusive.
     * All seven numbers must be different from each other.
     * The numbers are symbolic only, not for gambling or financial use.
     * After choosing the seven numbers, create one short sentence that links the feeling of the numbers to the weekly theme.
   - The final output MUST follow this order:
     1. First line: Viikon lause: <one sentence in the customer language>
     2. Second line: The Seven Lights Index: n1 n2 n3 n4 n5 n6 n7 where n1 to n7 are the seven distinct integers between 1 and 40.
     3. Third line: Index note: <one short sentence in the customer language that connects the numbers to the weekly energy>
     4. After these three lines, output the full weekly horoscope text in paragraph form, addressing the reader directly.

3. Tone:
   - Motivational, perspective-building, non-prescriptive.
   - No fallback content is permitted.
   - Do not describe the numbers as lottery or betting advice. They are symbolic, reflective elements only.

4. Output Requirement:
   - End with an actionable recommendation (in customer's language, e.g. "Viikon neuvo:" for Finnish).

5. Word Count:
   - 150 to 230 words, excluding the Viikon lause line and The Seven Lights Index lines.

6. Formatting:
   - NEVER use markdown formatting symbols like ** or * for bold/italic.
   - All section headers must be in the customer's language.
"""

# Finnish output format
WEEKLY_OUTPUT_FORMAT_FI = """
MUOTO (TÄRKEÄÄ - ÄLÄ KÄYTÄ ** TAI * MERKINTÖJÄ):

Viikon lause: [yksi lause]

The Seven Lights Index: [7 eri numeroa väliltä 1-40]
Index-huomio: [lyhyt lause numeroiden yhteydestä viikon energiaan]

[Ennustuksen teksti 150-230 sanaa, suoraan lukijalle]

Viikon neuvo: [yksi toimintaehdotus]
"""

# English output format
WEEKLY_OUTPUT_FORMAT_EN = """
OUTPUT FORMAT (IMPORTANT - DO NOT USE ** OR * MARKERS):

Weekly Phrase: [one sentence]

The Seven Lights Index: [7 different numbers between 1-40]
Index note: [short sentence connecting numbers to weekly energy]

[Prediction text 150-230 words, addressing reader directly]

Weekly Advice: [one actionable recommendation]
"""

# Swedish output format
WEEKLY_OUTPUT_FORMAT_SV = """
UTMATNINGSFORMAT (VIKTIGT - ANVÄND INTE ** ELLER * MARKERINGAR):

Veckans fras: [en mening]

The Seven Lights Index: [7 olika nummer mellan 1-40]
Index-notering: [kort mening som kopplar numren till veckans energi]

[Förutsägelsetext 150-230 ord, tilltal direkt till läsaren]

Veckans råd: [en handlingsbar rekommendation]
"""

def get_weekly_output_format(language: str) -> str:
    """Get the output format instructions for weekly predictions in the specified language."""
    formats = {
        "fi": WEEKLY_OUTPUT_FORMAT_FI,
        "sv": WEEKLY_OUTPUT_FORMAT_SV,
        "en": WEEKLY_OUTPUT_FORMAT_EN
    }
    return formats.get(language, WEEKLY_OUTPUT_FORMAT_EN)

