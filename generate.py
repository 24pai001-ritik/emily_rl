# generate.py

from rl_agent import select_action
from prompt_template import PROMPT_GENERATOR, TRENDY_TOPIC_PROMPT, classify_trend_style
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import json
import os
import requests
from dotenv import load_dotenv


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROK_API_URL = os.getenv("GROK_API_URL")
GROK_API_KEY = os.getenv("GROK_URL_KEY")


# ============================================================
# LLM CLIENTS (ABSTRACTION LAYER)
# ============================================================
# Note: Models are initialized only when API keys are available

def call_gpt_4o_mini(prompt: str) -> dict:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    # Initialize the model with the API key
    gpt_4o_mini = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=OPENAI_API_KEY,
        temperature=0.7
    )

    response = gpt_4o_mini.invoke([
        HumanMessage(content=prompt)
    ])

    try:
        return json.loads(response.content)
    except Exception:
        raise ValueError("GPT-4o mini did not return valid JSON")


def call_grok(prompt: str):
    """
    Calls Grok via HTTP.
    Returns JSON if possible, else raw text.
    """

    if not GROK_API_KEY:
        raise ValueError("GROK_API_KEY not found in environment variables")

    if not GROK_API_URL:
        raise ValueError("GROK_API_URL not found in environment variables")

    response = requests.post(
        GROK_API_URL,
        headers={
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "grok-2",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        },
        timeout=30
    )

    response.raise_for_status()

    content = response.json()["choices"][0]["message"]["content"]

    # Try JSON parse (for prompt generation)
    try:
        return json.loads(content)
    except Exception:
        # For topic generation (plain text)
        return content
# ============================================================
# TOPIC GENERATOR
# ============================================================



def generate_topic(
    business_context: str,
    platform: str,
    date: str
) -> dict:
    """
    Generates a post topic using Grok.
    Returns:
    {
      "topic": str,
      "reasoning": str
    }
    """

    filled_prompt = TOPIC_GENERATOR
    filled_prompt = filled_prompt.replace("{{BUSINESS_CONTEXT}}", business_context)
    filled_prompt = filled_prompt.replace("{{PLATFORM}}", platform)
    filled_prompt = filled_prompt.replace("{{DATE}}", date)

    response = call_grok(filled_prompt)

    # Grok returns formatted text, not JSON here
    if not isinstance(response, str):
        raise ValueError("Topic generator must return text")

    # Expected format:
    # **Topic:** XYZ
    # <paragraph>

    lines = response.strip().splitlines()

    topic = None
    reasoning = []

    for line in lines:
        if line.strip().startswith("**topic:**"):
            topic = line.replace("**Topic:**", "").strip()
        else:
            reasoning.append(line.strip())

    if not topic:
        raise ValueError("Failed to extract topic from Grok response")

    return {
        "topic": topic,
        "reasoning": " ".join(reasoning).strip()
    }





# ============================================================
# CONTEXT BUILDER (UNCHANGED)
# ============================================================

def build_context(business_embedding, topic_embedding, platform, time, day_of_week):
    """
    Build RL context from embeddings and scheduling info.
    day_of_week: 0=Monday, 6=Sunday (provided directly, not derived from date)
    """
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

def generate_prompts(
    inputs: dict,
    business_embedding,
    topic_embedding,
    platform: str,
    time: str,
    day_of_week: int
) -> dict:
    """
    Single execution point between RL and LLMs.
    """

    print(f"🤖 RL Context: Platform={platform}, Time={time}, Day={day_of_week}")

    # 1️⃣ Build RL context (using your build_context)
    context = build_context(
        business_embedding=business_embedding,
        topic_embedding=topic_embedding,
        platform=platform,
        time=time,
        day_of_week=day_of_week
    )

    # 2️⃣ RL decides creative controls
    action, ctx_vec = select_action(context)
    print(f"🎯 RL Selected Action: {action}")
    hook_type = action.get("HOOK_TYPE", "")

    # 3️⃣ Merge inputs + RL action for placeholders
    merged = {**inputs, **action}

    # =====================================================
    # 🔥 TRENDY → GROK
    # =====================================================
    if hook_type == "trendy topic hook":
        selected_style = classify_trend_style(
            inputs["BUSINESS_TYPES"],
            inputs["INDUSTRIES"]
        )

        filled_prompt = TRENDY_TOPIC_PROMPT
        merged_with_style = {
            **merged,
            "selected_style": selected_style
        }

        for k, v in merged_with_style.items():
            if isinstance(v, list):
                v = ", ".join(v)
            filled_prompt = filled_prompt.replace(f"{{{{{k}}}}}", str(v))

        print(f"📝 Sending to Grok (Trendy Topic): {filled_prompt[:200]}...")
        llm_response = call_grok(filled_prompt)
        print(f"📝 Generated Caption Prompt: {llm_response['caption_prompt'][:200]}...")
        print(f"📝 Generated Image Prompt: {llm_response['image_prompt'][:200]}...")

        return {
            "mode": "trendy",
            "caption_prompt": llm_response["caption_prompt"],
            "image_prompt": llm_response["image_prompt"],
            "style": selected_style,
            "action": action,
            "context": context,
            "ctx_vec": ctx_vec
        }


    # =====================================================
    # ✅ NON-TRENDY → GPT-4o MINI
    # =====================================================
    filled_prompt = PROMPT_GENERATOR
    for k, v in merged.items():
        if isinstance(v, list):
            v = ", ".join(v)
        filled_prompt = filled_prompt.replace(f"{{{{{k}}}}}", str(v))

    print(f"📝 Sending to GPT-4o-mini (Standard): {filled_prompt[:200]}...")
    llm_response = call_gpt_4o_mini(filled_prompt)
    print(f"📝 Generated Caption Prompt: {llm_response['caption_prompt'][:200]}...")
    print(f"📝 Generated Image Prompt: {llm_response['image_prompt'][:200]}...")

    return {
        "mode": "standard",
        "caption_prompt": llm_response["caption_prompt"],
        "image_prompt": llm_response["image_prompt"],
        "action": action,
        "context": context,
        "ctx_vec": ctx_vec
    }