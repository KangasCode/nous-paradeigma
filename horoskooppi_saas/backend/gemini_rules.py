"""
Gemini Horoscope Generation Rules

IMPORTANT SYSTEM NOTE:
- The backend must NOT use any fallback horoscope generation.
- Gemini must ALWAYS generate the horoscope directly using these rules.
- If Gemini cannot generate a horoscope, the backend must return an error instead of a fallback text.
"""

GENERAL_RULES = """
GENERAL HOROSCOPE GENERATION RULES

1. Language Requirement:
   - The output must ALWAYS be written in the customer's language.
   - The backend will specify the target language; follow it exactly.
   - Do not mix languages unless explicitly requested.

2. Tone and Style:
   - Tone: modern, clear, supportive, grounded, and positive.
   - Use open-ended, interpretive wording instead of deterministic statements.
   - Avoid overly poetic or metaphysical language unless it fits the sign naturally.
   - Keep content emotionally intelligent, warm, and readable.

3. Core Themes to Always Include:
   - Emotions & relationships
   - Work, creativity & long-term goals
   - Wellbeing, energy & internal balance

4. Structural Requirements:
   - End every horoscope with one practical piece of advice.
   - Make content zodiac-specific where relevant.
   - Avoid guaranteed outcomes, health claims, financial promises, or fortune-telling.
   - No fallback texts are permitted.

5. Word Count Guidelines:
   - Daily: 80–140 words
   - Weekly: 150–230 words
   - Monthly: 180–300 words
"""

DAILY_RULES = """
DAILY HOROSCOPE RULES

1. Focus of the Day:
   - Describe the energetic or emotional tone of the day.
   - Highlight one opportunity or subtle challenge.
   - Keep the scope limited to "today"—short-term dynamics only.

2. Structure:
   - Begin with today's mood or atmosphere.
   - Add one situational hint (interaction, moment of clarity, minor decision).
   - Keep tone actionable, light, and grounded.

3. Limitations:
   - No long-term predictions.
   - No references to weekly or monthly patterns.
   - No fallback or placeholder text allowed.

4. Output Requirement:
   - End with: "Daily Advice:" followed by one practical suggestion.
"""

WEEKLY_RULES = """
WEEKLY HOROSCOPE RULES

1. Focus of the Week:
   - Explain the rhythm of the week: beginning → middle → end.
   - Identify one background theme that influences the entire week.
   - Discuss progress, delays, or evolving emotional dynamics.

2. Structure:
   - Present three core angles:
     a) The week's overarching theme
     b) A mid-week development or challenge
     c) Social or relational influences

3. Tone:
   - Motivational, perspective-building, but non-prescriptive.
   - No fallback content is permitted.

4. Output Requirement:
   - End with: "Weekly Advice:" followed by one actionable recommendation.
"""

MONTHLY_RULES = """
MONTHLY HOROSCOPE RULES

1. Focus of the Month:
   - Describe two or three major themes shaping the month.
   - Emphasize development, clarity, internal shifts, and long-term influences.
   - Describe how energy may evolve from early to later weeks.

2. Structure:
   - Begin with the overarching monthly narrative.
   - Explore opportunities, internal growth, emerging patterns.

3. Restrictions:
   - No exact dates, promises, or deterministic predictions.
   - No health or financial guarantees.
   - No fallback text is allowed under any circumstances.

4. Output Requirement:
   - End with: "Monthly Intention:" or "Power Statement:" summarizing the month's focus.
"""

VOCABULARY_BANK = """
HOROSCOPE VOCABULARY BANK (OPTIONAL TERMS)

These words and expressions may be used when stylistically appropriate:

Emotional/Atmospheric:
- clarity, grounding, alignment, inner balance, resilience
- intuition, awareness, renewal, momentum, openness

Action/Guidance:
- reflect, trust, observe, step forward, re-evaluate, embrace
- reconnect, focus, soften, stabilize, explore

Relational:
- communication, connection, harmony, mutual understanding
- shared energy, openness, empathy, supportive exchange

Growth/Development:
- transformation, progress, shifting perspective
- opportunities unfolding, subtle changes, evolving dynamics

Energy/Flow:
- calm currents, rising motivation, stabilizing forces
- renewed spark, gentle momentum, emerging clarity

Rules for the Vocabulary Bank:
- Use these words only when they fit naturally.
- Do not create overly poetic or mystical language.
- Prioritize simplicity and clarity over embellishment.
"""

