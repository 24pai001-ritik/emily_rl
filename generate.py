# generate.py

from rl_agent import select_action
from prompt_template import TOPIC_GENERATOR,PROMPT_GENERATOR, TRENDY_TOPIC_PROMPT, classify_trend_style
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import json
import os
import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


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


def call_grok(prompt: str) -> str | dict:
    """
    Grok HTTP client.
    - Reads env vars at RUNTIME (no import-time freeze)
    - Works with paid API keys
    - Returns JSON if possible, else raw text
    """

    GROK_API_KEY = os.getenv("GROK_API_KEY")
    GROK_API_URL = os.getenv("GROK_API_URL")

    if not GROK_API_KEY:
        raise ValueError("GROK_API_KEY not found in environment variables")

    if not GROK_API_URL:
        raise ValueError("GROK_API_URL not found in environment variables")

    try:
        response = requests.post(
            GROK_API_URL,
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                # safest + cheapest + API-enabled
                "model": "grok-4-1-fast-non-reasoning",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            },
            timeout=30
        )
    except requests.RequestException as e:
        raise RuntimeError(f"Grok request failed: {e}")

    if response.status_code != 200:
        raise RuntimeError(
            f"Grok API error {response.status_code}: {response.text}"
        )

    content = response.json()["choices"][0]["message"]["content"]

    # Prompt-generation → JSON
    # Topic-generation → plain text
    try:
        return json.loads(content)
    except Exception:
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
    print(f"Business context: {business_context}")
    filled_prompt = TOPIC_GENERATOR
    filled_prompt = filled_prompt.replace("{{BUSINESS_CONTEXT}}", business_context)
    filled_prompt = filled_prompt.replace("{{PLATFORM}}", platform)
    filled_prompt = filled_prompt.replace("{{DATE}}", date)

    try:
        response = call_grok(filled_prompt)
        return {
        "topic": response
    }

    except Exception as e:
        print(f"Error generating topic: {e}")
        return {
            "topic": "Get to know our brand and what we do, Give a brief introduction to the business and what we do "
        }

    

# ============================================================
# EMBED TOPIC
# ============================================================

_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_topic(topic_text: str):
    return _model.encode(topic_text).tolist()


# ============================================================
# CONTEXT BUILDER 
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
    day_of_week: int,
    topic_text: str,profile_data: dict,
    business_context: str
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

        # Format business context as structured JSON-like data for better prompt understanding
        business_context_formatted = f"""
Business Name: {profile_data.get('business_name', 'Business')}
Industry: {', '.join(profile_data.get('industries', ['General']))}
Business Type: {', '.join(profile_data.get('business_types', ['General']))}
Description: {profile_data.get('business_description', 'A business focused on growth and success')}
Brand Voice: {profile_data.get('brand_voice', 'Professional and approachable')}
Target Audience: {profile_data.get('target_audience', 'General audience')}
Unique Value Proposition: {profile_data.get('unique_value_proposition', 'Delivering quality solutions')}
Primary Color: {profile_data.get('primary_color', '#000000')}
Secondary Color: {profile_data.get('secondary_color', '#FFFFFF')}
"""

        filled_prompt = TRENDY_TOPIC_PROMPT
        merged_with_style = {
            **merged,
            "selected_style": selected_style,
            "BUSINESS_CONTEXT": business_context_formatted,
            "BUSINESS_AESTHETIC": profile_data["brand_voice"],
            "BUSINESS_TYPES": profile_data["business_types"],
            "INDUSTRIES": profile_data["industries"],
            "topic_text": topic_text
        }

        for k, v in merged_with_style.items():
            if isinstance(v, list):
                v = ", ".join(v)
            filled_prompt = filled_prompt.replace(f"{{{{{k}}}}}", str(v))

        print(f"📝 Sending to Grok (Trendy Topic): {filled_prompt[:200]}...")
        llm_response = call_grok(filled_prompt)

        if not isinstance(llm_response, dict):
            print("⚠️ Grok returned non-JSON output. Raw response:")
            print(llm_response)
            raise ValueError("Invalid Grok response format")

        if "caption_prompt" not in llm_response or "image_prompt" not in llm_response:
            raise ValueError(f"Incomplete Grok response: {llm_response}")

        print(f"📝 Generated Caption Prompt: {llm_response['caption_prompt']}\n")
        print(f"📝 Generated Image Prompt: {llm_response['image_prompt']}\n")

        return {
            "mode": "trendy",
            "caption_prompt": llm_response["caption_prompt"],
            "image_prompt": llm_response["image_prompt"],
            "business_context_formatted": business_context_formatted,
            "style": selected_style,
            "action": action,
            "context": context,
            "ctx_vec": ctx_vec
        }


    # =====================================================
    # ✅ NON-TRENDY → GPT-4o MINI
    # =====================================================
    filled_prompt = PROMPT_GENERATOR

    # Format business context as structured JSON-like data for better prompt understanding
    business_context_formatted = f"""
Business Name: {profile_data.get('business_name', 'Business')}
Industry: {', '.join(profile_data.get('industries', ['General']))}
Business Type: {', '.join(profile_data.get('business_types', ['General']))}
Description: {profile_data.get('business_description', 'A business focused on growth and success')}
Brand Voice: {profile_data.get('brand_voice', 'Professional and approachable')}
Target Audience: {profile_data.get('target_audience', 'General audience')}
Unique Value Proposition: {profile_data.get('unique_value_proposition', 'Delivering quality solutions')}
Primary Color: {profile_data.get('primary_color', '#000000')}
Secondary Color: {profile_data.get('secondary_color', '#FFFFFF')}
"""

    merged = {
    **inputs,
    **action,
    "BUSINESS_CONTEXT": business_context_formatted,
    "BUSINESS_AESTHETIC": profile_data["brand_voice"],
    "BUSINESS_TYPES": profile_data["business_types"],
    "INDUSTRIES": profile_data["industries"],
    "topic_text": topic_text
}

    for k, v in merged.items():
        if isinstance(v, list):
            v = ", ".join(v)
        filled_prompt = filled_prompt.replace(f"{{{{{k}}}}}", str(v))

    print(f"📝 Sending to GPT-4o-mini (Standard)")
    llm_response = call_gpt_4o_mini(filled_prompt)
    print(f"📝 Generated Caption Prompt: {llm_response['caption_prompt'][:180]}...")
    print(f"📝 Generated Image Prompt: {llm_response['image_prompt'][:180]}...")

    return {
        "mode": "standard",
        "caption_prompt": llm_response["caption_prompt"],
        "image_prompt": llm_response["image_prompt"],
        "business_context_formatted": business_context_formatted,
        "action": action,
        "context": context,
        "ctx_vec": ctx_vec
    }