# generate.py

from datetime import datetime
from rl_agent import select_action

# ============================================================
# ORIGINAL PROMPT TEMPLATE (UNCHANGED LOGIC)
# ============================================================

PROMPT_TEMPLATE = """
You are a Prompt Generator.

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

Topic embedding : {{TOPIC_EMBEDDING}}

Hook type: {{HOOK_TYPE}}
Length : {{LENGTH}}
Tone: {{TONE}}
Creativity : {{CREATIVITY}}

Text in image : {{TEXT_IN_IMAGE}}
Visual style : {{VISUAL_STYLE}}

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

- Write a caption aligned with {{BUSINESS_CONTEXT}}, {{BUSINESS_AESTHETIC}}, and {{TOPIC_EMBEDDING}}
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

- Use {{CAPTION}} as the PRIMARY semantic reference for the visual
- Use {{BUSINESS_CONTEXT}} as a SECONDARY reference to ensure:
  • industry relevance  
  • brand appropriateness  
  • compliance with the business domain
- Use {{BUSINESS_AESTHETIC}} to guide colors, mood, and visual language
- Translate the intent, emotion, and message of {{CAPTION}} into a visual concept
- Respect {{TEXT_IN_IMAGE}} rules strictly
- Align with {{VISUAL_STYLE}}
- NOT repeat the full caption verbatim inside the image
- NOT introduce concepts, symbols, or claims that are not supported by {{CAPTION}} or {{BUSINESS_CONTEXT}}
- NOT visually depict business details unless clearly implied by {{CAPTION}}

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



# ============================================================
# GROK TREND PROMPT BUILDER
# ============================================================

def build_grok_trend_prompt(
    business_context,
    business_types,
    industries,
    business_description,
    selected_style,
    length,
    tone,
    creativity
):
    return f"""
You are a real-time Twitter (X) trend analyst and expert brand copywriter.

Your task:
1. Analyze CURRENTLY trending topics on Twitter (India + Global)
2. Select ONE high-velocity, culturally relevant, brand-safe trend
3. Generate TWO PROMPTS based on this trend using the STRICT rules below

────────────────────────
BUSINESS CONTEXT
────────────────────────
{business_context}

Business Types: {business_types}
Industry: {industries}

Description:
{business_description}

────────────────────────
MANDATORY CONTENT STYLE
────────────────────────
{selected_style}

You MUST strictly follow this style.
Do NOT mix styles.
Do NOT explain the style.

────────────────────────
CREATIVE CONTROLS (STRICT)
────────────────────────
Length: {length}
Tone: {tone}
Creativity Level: {creativity}

Interpretation:
- Short → punchy, scroll-stopping
- Medium → concise but explanatory
- Low creativity → safe, literal
- Medium creativity → clever but controlled
- High creativity → bold, witty (brand-safe)

────────────────────────
OUTPUT REQUIREMENTS
────────────────────────
Return a JSON object with exactly TWO keys:

{{
  "image_prompt": "...",
  "caption_prompt": "..."
}}

Both prompts must:
- Be optimized for their respective AI models (Gemini for images, GPT-4o mini for text)
- Follow the mandatory content style above
- Respect the creative controls (length, tone, creativity)
- NOT mention tools, APIs, or analysis
- NOT sound salesy
- Use emojis ONLY if tone is casual or humorous

The image_prompt should describe a visual concept for the trend.
The caption_prompt should describe how to write engaging caption text for the trend.

Do NOT add any extra text, explanations, or markdown.
Do NOT include the JSON keys inside the prompts themselves.
Output must be deterministic and structured.

Your job ends after producing the two prompts.
"""


# ============================================================
# CONTEXT BUILDER (UNCHANGED)
# ============================================================

def build_context(business_embedding, topic_embedding, platform, date, time):
    # Convert date string to day of week (0=Monday, 6=Sunday)
    from datetime import datetime
    try:
        date_obj = datetime.fromisoformat(date)
        day_of_week = date_obj.weekday()
    except:
        # Fallback to current day if date parsing fails
        day_of_week = datetime.utcnow().weekday()

    return {
        "platform": platform,
        "time_bucket": time,
        "day_of_week": day_of_week,
        "business_embedding": business_embedding,
        "topic_embedding": topic_embedding
    }


# ============================================================
# MAIN GENERATION FUNCTION
# ============================================================

def generate_prompts(inputs, business_embedding, topic_embedding, platform, date, time): #add else after trendy
    """
    REQUIRED inputs keys:
    BUSINESS_embedding
    TOPIC_EMBEDDING (embedding vector)
    platform
    date
    time
    """

    context = build_context(business_embedding, topic_embedding, platform, date, time)

    # RL decides creative controls
    action, ctx_vec = select_action(context)

    hook_type = action.get("HOOK_TYPE")

    # =====================================================
    # 🔥 TRENDY HOOK → TREND-BASED GENERATION
    # =====================================================
    if hook_type == "trendy":

        selected_style = classify_trend_style(
            inputs["BUSINESS_TYPES"],
            inputs["INDUSTRIES"]
        )

        # Generate trend-based prompts using embeddings
        image_prompt = f"""Create a trendy social media visual in the style: {selected_style}.
Platform: {inputs['PLATFORM']}
Creative controls: {action['LENGTH']} length, {action['TONE']} tone, {action['CREATIVITY']} creativity level.
Visual style preference: {action['VISUAL_STYLE']}
Text in image: {action['TEXT_IN_IMAGE']}
Make it engaging and brand-appropriate for {inputs['BUSINESS_TYPES']} in {inputs['INDUSTRIES']}."""

        caption_prompt = f"""Write a trendy social media caption following this style: {selected_style}.
Platform: {inputs['PLATFORM']}
Creative controls: {action['LENGTH']} length, {action['TONE']} tone, {action['CREATIVITY']} creativity level.
Make it engaging and brand-appropriate for {inputs['BUSINESS_TYPES']} in {inputs['INDUSTRIES']}.
Focus on creating viral-worthy content that resonates with current trends."""

        return {
            "mode": "trendy",
            "image_prompt": image_prompt,
            "caption_prompt": caption_prompt,
            "style": selected_style,
            "action": action,
            "context": context,
            "ctx_vec": ctx_vec
        }


    # =====================================================
    # ✅ NON-TRENDY → EXISTING FLOW (UNCHANGED)
    # =====================================================
    filled_prompt = PROMPT_TEMPLATE
    merged = {**inputs, **action}

    for k, v in merged.items():
        # Convert lists and other non-string types to strings
        if isinstance(v, list):
            v = ", ".join(v)
        elif not isinstance(v, str):
            v = str(v)
        filled_prompt = filled_prompt.replace(f"{{{{{k}}}}}", v)

    return {
        "mode": "standard",
        "prompt": filled_prompt,
        "action": action,
        "context": context,
        "ctx_vec": ctx_vec
    }



