"""
Gemini Horoscope Generation Rules - SHARED BASE

This file contains GENERAL rules that apply to ALL prediction types.
Type-specific rules are in separate files:
- gemini_rules_daily.py  - Daily prediction rules
- gemini_rules_weekly.py - Weekly prediction rules  
- gemini_rules_monthly.py - Monthly prediction rules

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
   - Tone: modern, clear, supportive, grounded, positive.
   - Use open-ended, interpretive wording instead of deterministic statements.
   - Avoid overly poetic or metaphysical language unless it fits the sign naturally.
   - Keep content emotionally intelligent, warm, and readable.
   - Always address the reader directly in second person, as if the horoscope is written specifically for them.
   - Do NOT address the zodiac sign by name inside the text body. The sign can be present in metadata or headings only.

3. Core Themes to Always Include:
   - Emotions and relationships.
   - Work, creativity and long-term goals.
   - Wellbeing, energy and internal balance.

4. Structural Requirements:
   - End every horoscope with one practical piece of advice.
   - Make content zodiac-specific where relevant.
   - Avoid guaranteed outcomes, health claims, financial promises, or fortune-telling.
   - No fallback texts are permitted.
   - NEVER use markdown formatting symbols like ** or * for bold/italic. Email clients do not support them.
   - All section headers must be in the customer's language (e.g. "Päivän sana:" not "Word of the Day:").

5. Age-specific voice: Age is ALWAYS known and given as an integer.
   - Age 13 to 17:
     * Typical focus: school life, friends, hobbies, digital life, family everyday routines.
     * Language: simple, clear sentences, you form, gentle and encouraging tone.
     * Avoid heavy focus on career, money, adult responsibilities and complex psychological terminology.
     * Emphasize emotional self-awareness, boundaries with friends, study rhythm, sleep, recovery, use of time.
   
   - Age 18 to 24:
     * Typical focus: studies, early work life, identity, social circles, first serious relationships, moving away from home.
     * Language: relaxed, modern, still clear and respectful. You form, can use light everyday expressions but avoid heavy slang unless backend explicitly requests it.
     * Normalize uncertainty about the future. Emphasize experimenting, learning, trying directions without pressure for perfect choices.
     * Avoid strong instructions about life decisions. Offer perspective and gentle guidance instead.
   
   - Age 25 to 34:
     * Typical focus: building career, maybe starting family, living with partner, independent life, finances, big life choices.
     * Language: modern, direct but warm. You form, neutral adult tone, not too formal.
     * Emphasize balance between ambition and recovery, boundaries at work, long-term wellbeing, room for personal needs alongside responsibilities.
     * Mention concrete everyday themes like work structure, studies, home life, friendships and time management when suitable.
   
   - Age 35 to 49:
     * Typical focus: established work role, family life, parenting or step-parenting, long-term goals, possible midlife questions.
     * Language: clear, respectful, emotionally intelligent, no youth slang. You form, adult level.
     * Emphasize meaning, realistic planning, balancing family demands and personal space, managing stress and expectations.
     * Recognize existing experience. Do not write as if the reader is just starting everything from zero.
   
   - Age 50 to 64:
     * Typical focus: long work experience, grown or growing children, changing body and energy, possible career changes, caring for older relatives, preparing for retirement.
     * Language: calm and respectful, grounded, supportive. You form, no condescending tone.
     * Emphasize meaning, values, sustainable routines and relationships without medical claims.
     * Acknowledge that many structures are already built and changes are often about fine-tuning, not starting over.
   
   - Age 65 and above:
     * Typical focus: retirement or transition to retirement, free time, health-supporting routines, grandchildren, friendships, personal interests, life review.
     * Language: warm, respectful, dignified. Avoid calling the reader old, avoid youth slang.
     * Emphasize meaning, enjoyment, gentle curiosity, mental and emotional activity, social contact.
     * Avoid medical advice or promises. Speak about balance, pacing, listening to body and emotions in general terms.
   
   General formality rule:
   - Under 30: tone may be slightly more relaxed and light, still clear and respectful.
   - 30 and above: neutral, adult, calm tone without slang, but not stiff or bureaucratic.

6. Implementation note for summary elements:
   - For all horoscope types, Gemini must FIRST form the full main text of the horoscope internally.
   - Only AFTER the full text is internally clear, Gemini creates the summary element.
   - These summary elements must clearly reflect the main message of the longer text and must NOT introduce new, unrelated topics.
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


def load_prediction_rules(prediction_type: str):
    """
    Load the appropriate rules file for the given prediction type.
    
    Args:
        prediction_type: 'daily', 'weekly', or 'monthly'
    
    Returns:
        Tuple of (specific_rules, get_output_format_func)
    """
    if prediction_type == "daily":
        from gemini_rules_daily import DAILY_RULES, get_daily_output_format
        return DAILY_RULES, get_daily_output_format
    elif prediction_type == "weekly":
        from gemini_rules_weekly import WEEKLY_RULES, get_weekly_output_format
        return WEEKLY_RULES, get_weekly_output_format
    elif prediction_type == "monthly":
        from gemini_rules_monthly import MONTHLY_RULES, get_monthly_output_format
        return MONTHLY_RULES, get_monthly_output_format
    else:
        # Default to daily
        from gemini_rules_daily import DAILY_RULES, get_daily_output_format
        return DAILY_RULES, get_daily_output_format
