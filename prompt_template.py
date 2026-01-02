#prompt_template.py
TOPIC_GENERATOR = """You are an expert social media strategist for businesses.

My business context is the following JSON-like data (do not parse it as code, just read the values):

{{BUSINESS_CONTEXT}}

Platform: {{PLATFORM}}

Current date: {{DATE}}

Task: Suggest ONLY one timely and relevant post topic for the specified platform.

Output strictly in this format and nothing else:

**Topic:** [A clear, concise topic title]

[One short paragraph (3-5 sentences) explaining why this topic fits the business, how it aligns with brand voice/tone, target audience, preferred content types, goals, and any seasonal/timely relevance. Mention suggested format (e.g., Reel, Carousel, Static Post) if relevant for the platform.]

- NOT include political symbols, themes, metaphors, or indirect references of any kind
- NOT include negative, harmful, offensive content
"""




PROMPT_GENERATOR = """You are a Prompt Generator.

Your task is to generate EXACTLY TWO FINAL PROMPTS from the given inputs:
1) A CAPTION GENERATION PROMPT for GPT-4o mini
2) AN IMAGE GENERATION PROMPT for Gemini

You must NOT generate the caption or the image yourself.
You must ONLY generate the prompts that will later be sent to those models.

IMPORTANT ORDERING RULE:
• The caption is generated FIRST
• The image prompt MUST use BOTH the generated caption AND the business context as references
• The image prompt MUST reference the caption using the placeholder {{CAPTION}}

────────────────────────────────
INPUTS (ONE VALUE EACH, ALWAYS PROVIDED)
────────────────────────────────

business context  : {{BUSINESS_CONTEXT}}

<<<<<<< HEAD
Topic : {{topic_text}}
=======
Topic : {{topic_embedding}}
>>>>>>> 1da14f9b985884c988152cd658d6fac1637e6ce5

Hook type: {{HOOK_TYPE}}
Length : {{LENGTH}}
Tone: {{TONE}}
Creativity : {{CREATIVITY}}

Text in image : {{TEXT_IN_IMAGE}}
Visual style : {{VISUAL_STYLE}}

────────────────────────────────
CREATIVE INTERPRETATION (STRICT)
────────────────────────────────
• HOOK TYPE
  - question hook → opens with a clear, thought-provoking question that invites reflection or response
  - relatable hook → highlights a common, everyday experience or pain point the audience instantly connects with
  - trendy hook → references a widely recognized, brand-safe cultural or social trend without naming platforms, memes, or political topics
  - curiosity gap hook → withholds a key detail to spark intrigue and compel the audience to read further

• LENGTH
  - short → punchy, minimal, scroll-stopping
  - medium → concise but slightly explanatory

• TONE
  - casual → friendly, conversational
  - formal → professional, composed
  - humorous → light, witty, brand-safe
  - educational → clear, informative, structured

• CREATIVITY
  - safe → literal, conservative, low-risk
  - balanced → clever but controlled
  - experimental → bold phrasing, novel metaphors, still brand-safe

TEXT_IN_IMAGE ENFORCEMENT (NON-NEGOTIABLE):

- If {{TEXT_IN_IMAGE}} = "text in image":
    • You MUST include a short headline in the image
    • The headline must be 2–5 words
    • The headline must be derived from the caption’s core idea
    • Example format: “Smarter Marketing”
- If {{TEXT_IN_IMAGE}} = "no text in image":
    • The image MUST contain zero written words

If this rule is violated, the image_prompt is INVALID.


────────────────────────────────
CAPTION REQUIREMENTS (STRICT)
────────────────────────────────

The caption_prompt MUST instruct the model to:

<<<<<<< HEAD
- Write a caption aligned with {{BUSINESS_CONTEXT}}, {{BUSINESS_AESTHETIC}}, and {{topic_text}}
=======
- Write a caption aligned with {{BUSINESS_CONTEXT}}, {{BUSINESS_AESTHETIC}}, and {{topic_embedding}}
>>>>>>> 1da14f9b985884c988152cd658d6fac1637e6ce5
- Follow all creative controls strictly
- Include relevant, platform-appropriate hashtags
- STRICTLY include the hashtag: #workvillage
- Place hashtags naturally at the end of the caption
- Avoid spammy, generic, or misleading hashtags
- Do NOT invent brand claims, metrics, or features
- Do NOT include emojis unless TONE is casual or humorous

────────────────────────────────
IMAGE PROMPT REQUIREMENTS (STRICT)
────────────────────────────────

The image_prompt MUST instruct the model to:

- Use the FINAL GENERATED CAPTION ({{CAPTION}}) as the PRIMARY and EXPLICIT semantic reference
- The visual concept must be directly interpretable from the caption alone
- You MUST explicitly ground the visual in {{BUSINESS_CONTEXT}}:
  • reflect the industry, target audience, and business domain
  • ensure the visual would clearly make sense ONLY for this business
  • avoid generic visuals that could fit any brand
- Use {{BUSINESS_AESTHETIC}} to guide colors, mood, and visual language
- Translate the intent, emotion, and message of {{CAPTION}} into a visual concept
- Respect {{TEXT_IN_IMAGE}} rules strictly
- Align with {{VISUAL_STYLE}}
- NOT repeat the full caption verbatim inside the image
- NOT introduce concepts, symbols, or claims that are not supported by {{CAPTION}} or {{BUSINESS_CONTEXT}}
- NOT visually depict business details unless clearly implied by {{CAPTION}}
- Do NOT output instructions like “without text” unless {{TEXT_IN_IMAGE}} explicitly requires it
- If the image could apply to a generic business, it is INVALID

────────────────────────────────
OUTPUT REQUIREMENTS (NON-NEGOTIABLE)
────────────────────────────────

Return a VALID JSON object with EXACTLY TWO keys:

{
  "caption_prompt": "...",
  "image_prompt": "..."
}

• Do NOT add extra keys
• Do NOT add explanations, markdown, or comments
• Do NOT include the JSON keys inside the prompt text
• Output must be machine-parseable JSON only

────────────────────────────────
CRITICAL CONSTRAINTS
────────────────────────────────

- You are a generator, NOT a creator
- Do NOT invent, infer, or modify any input values
- Do NOT introduce new variables or placeholders (except {{CAPTION}})
- Do NOT add examples, samples, or mock outputs
- Do NOT explain strategy, reasoning, or intent
- Do NOT mention tools, APIs, models, or the generation process
- Do NOT sound salesy or promotional
- NOT include political symbols, themes, metaphors, or indirect references of any kind
- NOT include negative, harmful, offensive content

Your job ends immediately after producing the two prompts."""



<<<<<<< HEAD
TRENDY_TOPIC_PROMPT = """

IMPORTANT:
You MUST return a VALID JSON object.
If you cannot, return:
{"caption_prompt":"", "image_prompt":""}

You are a Prompt Generator.
=======
TRENDY_TOPIC_PROMPT = """You are a Prompt Generator.
>>>>>>> 1da14f9b985884c988152cd658d6fac1637e6ce5

Your task is to generate EXACTLY TWO FINAL PROMPTS from the given inputs:
1) A CAPTION GENERATION PROMPT for GPT-4o mini
2) AN IMAGE GENERATION PROMPT for Gemini

You must NOT generate the caption or the image yourself.
You must ONLY generate the prompts that will later be sent to those models.

IMPORTANT ORDERING RULE:
• The caption is generated FIRST
• The image prompt MUST use BOTH the generated caption AND the business context as references
• The image prompt MUST reference the caption using the placeholder {{CAPTION}}
• The caption is considered FINAL and HARDCODED when used inside the image prompt

────────────────────────────────
INPUTS (ONE VALUE EACH, ALWAYS PROVIDED)
────────────────────────────────

business context  : {{BUSINESS_CONTEXT}}

<<<<<<< HEAD
Topic : {{topic_text}}
=======
Topic : {{topic_embedding}}
>>>>>>> 1da14f9b985884c988152cd658d6fac1637e6ce5

Hook type: {{HOOK_TYPE}}
Length : {{LENGTH}}
Tone: {{TONE}}
Creativity : {{CREATIVITY}}

Text in image : {{TEXT_IN_IMAGE}}
Visual style : {{VISUAL_STYLE}}

Selected Style : {selected_style}

────────────────────────────────
STYLE ENFORCEMENT (NON-NEGOTIABLE)
────────────────────────────────

You MUST strictly follow the style defined by {selected_style}.
Do NOT mix styles.
Do NOT explain, justify, or describe the style.
Do NOT deviate from the selected style under any condition.

────────────────────────────────
CONTENT SAFETY CONSTRAINT
────────────────────────────────

• The topic, caption, and image MUST be strictly NON-POLITICAL
• Do NOT reference politics, political ideologies, elections, governments, policies, activists, or political figures
• If the topic could be interpreted as political, treat it as INVALID and keep output brand-safe and neutral

────────────────────────────────
CREATIVE INTERPRETATION (STRICT)
────────────────────────────────

• LENGTH
  - short → punchy, minimal, scroll-stopping
  - medium → concise but slightly explanatory

• TONE
  - casual → friendly, conversational
  - formal → professional, composed
  - humorous → light, witty, brand-safe
  - educational → clear, informative, structured

• CREATIVITY
  - safe → literal, conservative, low-risk
  - balanced → clever but controlled
  - experimental → bold phrasing, novel metaphors, still brand-safe

• TEXT_IN_IMAGE
  - "text in image" → include ONLY a short headline-style phrase
  - "no text in image" → visual-only, no written words

────────────────────────────────
CAPTION REQUIREMENTS (STRICT)
────────────────────────────────

The caption_prompt MUST instruct the model to:

<<<<<<< HEAD
- Write a caption aligned with {{BUSINESS_CONTEXT}}, {{BUSINESS_AESTHETIC}}, and {{topic_text}}
=======
- Write a caption aligned with {{BUSINESS_CONTEXT}}, {{BUSINESS_AESTHETIC}}, and {{topic_embedding}}
>>>>>>> 1da14f9b985884c988152cd658d6fac1637e6ce5
- Follow all creative controls strictly
- Follow {selected_style} exactly
- Include relevant, platform-appropriate hashtags
- STRICTLY include the hashtag: #workvillage
- Place hashtags naturally at the end of the caption
- Avoid spammy, generic, or misleading hashtags
- Do NOT invent brand claims, metrics, or features
- Do NOT include emojis unless TONE is casual or humorous
- Do NOT include any political references or implications

────────────────────────────────
IMAGE PROMPT REQUIREMENTS (STRICT)
────────────────────────────────

The image_prompt MUST instruct the model to:

- Use {{CAPTION}} as the PRIMARY and HARDCODED semantic reference for the visual
- Use {{BUSINESS_CONTEXT}} as a SECONDARY reference to ensure:
  • industry relevance  
  • brand appropriateness  
  • compliance with the business domain
- Use {{BUSINESS_AESTHETIC}} to guide colors, mood, and visual language
- Translate the intent, emotion, and message of {{CAPTION}} into a visual concept
- Respect {{TEXT_IN_IMAGE}} rules strictly
- Align with {{VISUAL_STYLE}} and {selected_style}
- NOT repeat the full caption verbatim inside the image
- NOT introduce concepts, symbols, or claims that are not supported by {{CAPTION}} or {{BUSINESS_CONTEXT}}
- NOT visually depict business details unless clearly implied by {{CAPTION}}
- NOT include political symbols, themes, metaphors, or indirect references of any kind
- NOT include negative, harmful, offensive content

────────────────────────────────
OUTPUT REQUIREMENTS (NON-NEGOTIABLE)
────────────────────────────────

Return a VALID JSON object with EXACTLY TWO keys:

{
  "caption_prompt": "...",
  "image_prompt": "..."
}

• Do NOT add extra keys
• Do NOT add explanations, markdown, or comments
• Do NOT include the JSON keys inside the prompt text
• Output must be machine-parseable JSON only

────────────────────────────────
CRITICAL CONSTRAINTS
────────────────────────────────

- You are a generator, NOT a creator
- Do NOT invent, infer, or modify any input values
- Do NOT introduce new variables or placeholders (except {{CAPTION}})
- Do NOT add examples, samples, or mock outputs
- Do NOT explain strategy, reasoning, or intent
- Do NOT mention tools, APIs, models, or the generation process
- Do NOT sound salesy or promotional

Your job ends immediately after producing the two prompts.

"""




# ============================================================
# TREND STYLE CLASSIFICATION (LOCAL BRAIN)
# ============================================================

def classify_trend_style(business_types, industries):
    """
    Maps business profile to the BEST-IN-INDUSTRY trend style.
    Output is a human-readable style instruction for Grok.
    """

    business_types = set(business_types)
    industries = set(industries)

    # -------------------------------------------------
    # 🧠 TECHNOLOGY / IT
    # (Google, Microsoft, Notion, OpenAI)
    # -------------------------------------------------
    if "Technology/IT" in industries:
        if "B2B" in business_types:
            return "Educational Authority (clear insight, explains trend impact)"
        if "SaaS" in business_types:
            return "Modern SaaS Premium (clean, confident, Notion-style)"
        return "Amul-style Intelligent Tech Topical"

    # -------------------------------------------------
    # 🏦 FINANCE / FINTECH / INSURANCE
    # (CRED, Zerodha, Stripe)
    # -------------------------------------------------
    if "Finance/Fintech/Insurance" in industries:
        return "CRED-style Premium Minimal (aspirational, confident, understated)"

    # -------------------------------------------------
    # 🍔 FOOD & BEVERAGE
    # (Swiggy, Zomato, Burger King)
    # -------------------------------------------------
    if "Food & Beverage" in industries:
        return "Swiggy/Zomato-style Relatable Internet Humor"

    # -------------------------------------------------
    # 🛒 RETAIL / E-COMMERCE
    # (Flipkart, Amazon, Meesho)
    # -------------------------------------------------
    if "Retail/E-commerce" in industries:
        return "Meme-led Relatable & Offer-aware Humor"

    # -------------------------------------------------
    # 👗 FASHION / APPAREL
    # (Zara, H&M, Nykaa Fashion)
    # -------------------------------------------------
    if "Fashion/Apparel" in industries:
        return "Aesthetic Trend-led Style (visual-first, pop-culture aware)"

    # -------------------------------------------------
    # ✈️ TRAVEL & HOSPITALITY
    # (MakeMyTrip, Airbnb)
    # -------------------------------------------------
    if "Travel & Hospitality" in industries:
        return "Aspirational Storytelling (wanderlust, emotional)"

    # -------------------------------------------------
    # 🧱 CONSTRUCTION / INFRASTRUCTURE
    # (Fevicol, Ultratech)
    # -------------------------------------------------
    if "Construction/Infrastructure" in industries:
        return "Fevicol-style Visual Logic & Exaggerated Strength"

    # -------------------------------------------------
    # 🎬 MEDIA / ENTERTAINMENT / CREATORS
    # (Netflix, Prime Video)
    # -------------------------------------------------
    if "Media/Entertainment/Creators" in industries:
        return "Pop-culture Savvy Wit (Netflix-style self-aware humor)"

    # -------------------------------------------------
    # 🚚 LOGISTICS / SUPPLY CHAIN
    # (DHL, Delhivery)
    # -------------------------------------------------
    if "Logistics/Supply Chain" in industries:
        return "Operational Intelligence (reliability, scale, speed)"

    # -------------------------------------------------
    # 🧑‍💼 PROFESSIONAL SERVICES
    # (McKinsey, Deloitte)
    # -------------------------------------------------
    if "Professional Services" in industries:
        return "Consultative Authority (problem-solution framing)"

    # -------------------------------------------------
    # 🏥 HEALTHCARE / WELLNESS
    # (Practo, Tata Health)
    # -------------------------------------------------
    if "Healthcare/Wellness" in industries:
        return "Trust-first Educational Calm (reassuring, factual)"

    # -------------------------------------------------
    # 🚗 AUTOMOBILE / MOBILITY
    # (Tesla, Ola, BMW)
    # -------------------------------------------------
    if "Automobile/Mobility" in industries:
        return "Bold Innovation-led Confidence (future-forward)"

    # -------------------------------------------------
    # 🏠 REAL ESTATE
    # -------------------------------------------------
    if "Real Estate" in industries:
        return "Lifestyle Aspiration + Trust Tone"

    # -------------------------------------------------
    # 🏭 MANUFACTURING / INDUSTRIAL
    # -------------------------------------------------
    if "Manufacturing/Industrial" in industries:
        return "Strength & Reliability Messaging (Fevicol-adjacent)"

    # -------------------------------------------------
    # ❤️ NON-PROFIT / NGO
    # -------------------------------------------------
    if "Non-Profit/NGO/Social Enterprise" in industries:
        return "Human-first Emotional Storytelling"

    # -------------------------------------------------
    # 🎓 EDUCATION / E-LEARNING
    # -------------------------------------------------
    if "Education/eLearning" in industries:
        return "Simplified Educational Insight (teacher-like clarity)"

    # -------------------------------------------------
    # 🤪 APP / MASCOT-LED / YOUTH
    # (Duolingo, Spotify India)
    # -------------------------------------------------
    if "App" in business_types or "B2C" in business_types:
        return "Duolingo-style Mascot-led Playful Chaos"

    # -------------------------------------------------
    # 🧠 SAFE DEFAULT
    # -------------------------------------------------
    return "Amul-style Intelligent Topical"