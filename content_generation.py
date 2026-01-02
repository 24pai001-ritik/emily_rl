# content_generator.py
"""
Content Generation Module

This module handles the actual generation of captions and images using the prompts
created by the RL system.

- Caption generation: OpenAI GPT-4o-mini
- Image generation: Gemini 2.5 Flash Image Preview
"""
import os
import json
import base64
import uuid
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from db import SupabaseImageManager
try:
    # Try to use the newer google.genai package
    import google.genai as genai
    USE_NEW_PACKAGE = True
except ImportError:
    # Fall back to deprecated package
    import google.generativeai as genai
    USE_NEW_PACKAGE = False

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class ContentGenerator:
    """Handles caption and image generation using AI models."""

    def __init__(self):
        """Initialize the content generator with API clients."""
        self.openai_client = None
        self.gemini_client = None
        self.image_manager = None

        if OPENAI_API_KEY:
            self.openai_client = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=OPENAI_API_KEY,
                temperature=0.7
            ) 

        if GEMINI_API_KEY:
            if USE_NEW_PACKAGE:
                # New google.genai package
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            else:
                # Legacy google.generativeai package
                genai.configure(api_key=GEMINI_API_KEY)
                try:
                    # Use the requested model for image generation
                    self.gemini_client = genai.GenerativeModel('gemini-2.5-flash-image-preview')
                except Exception as e:
                    print(f"Warning: Could not initialize gemini-2.5-flash-image-preview ({e}), trying fallback")
                    try:
                        self.gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp-image-generation')
                    except Exception:
                        print("Warning: Could not initialize any Gemini image generation model")
                        self.gemini_client = None
        else:
            self.gemini_client = None

        # Initialize Supabase image manager
        try:
            self.image_manager = SupabaseImageManager()
        except Exception as e:
            print(f"Warning: Could not initialize Supabase image manager: {e}")
            self.image_manager = None

    def generate_caption(self, caption_prompt: str) -> str:
        """
        Generate a caption using OpenAI GPT-4o-mini.

        Args:
            caption_prompt: The prompt to generate the caption from

        Returns:
            Plain text caption with hashtags
        """
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        try:
            response = self.openai_client.invoke([
                HumanMessage(content=caption_prompt)
            ])

            # Return the response content directly (should include hashtags as per prompt)
            return response.content.strip()

        except Exception as e:
            raise RuntimeError(f"Failed to generate caption: {e}")

    def generate_image(self, image_prompt: str) -> str:
        """
        Generate an image using Gemini.

        Args:
            image_prompt: The prompt to generate the image from

        Returns:
            Base64 encoded image data URL or placeholder URL
        """
        if not self.gemini_client:
            raise ValueError("Gemini API key not configured")

        # Warn if {{CAPTION}} placeholder is found (should be replaced before calling this)
        if "{{CAPTION}}" in image_prompt:
            print("⚠️  WARNING: {{CAPTION}} placeholder found in image prompt. Use generate_content() instead of generate_image() directly.")

        try:
            if USE_NEW_PACKAGE:
                # New google.genai package API
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash-image-preview',
                    contents=image_prompt
                )

                # Handle new package response format
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        image_data = None
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data is not None:
                                inline_data = part.inline_data
                                if hasattr(inline_data, 'data') and inline_data.data is not None:
                                    image_data = inline_data.data
                                    break  # Found the image data, exit the loop
                                elif hasattr(inline_data, 'blob') and inline_data.blob is not None:
                                    # Try 'blob' attribute instead
                                    image_data = inline_data.blob
                                    break  # Found the image data, exit the loop

                        # Now check if we found image data
                        if image_data is not None:
                            # Upload to Supabase storage and get public URL
                            try:
                                if self.image_manager:
                                    public_url = self.image_manager.save_image(
                                        image_data=image_data,
                                        filename="generated_image.png",
                                        folder="generated"
                                    )
                                    return public_url
                                else:
                                    raise RuntimeError("Image manager not initialized")
                            except Exception as upload_error:
                                print(f"Failed to upload to Supabase: {upload_error}")
                                # Fallback to base64 data URL
                                base64_image = base64.b64encode(image_data).decode('utf-8')
                                return f"data:image/png;base64,{base64_image}"
                # If no image generated, return a placeholder
                return f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

            else:
                # Legacy google.generativeai package API
                response = self.gemini_client.generate_content(image_prompt)

                # Get the generated image data
                if response.candidates and response.candidates[0].content.parts:
                    image_part = response.candidates[0].content.parts[0]

                    if hasattr(image_part, 'inline_data'):
                        # Get image data
                        image_data = image_part.inline_data.data

                        # Upload to Supabase storage and get public URL
                        try:
                            if self.image_manager:
                                public_url = self.image_manager.save_image(
                                    image_data=image_data,
                                    filename="generated_image.png",
                                    folder="generated"
                                )
                                return public_url
                            else:
                                raise RuntimeError("Image manager not initialized")
                        except Exception as upload_error:
                            print(f"Failed to upload to Supabase: {upload_error}")
                            # Fallback to base64 data URL
                            mime_type = image_part.inline_data.mime_type
                            base64_image = base64.b64encode(image_data).decode('utf-8')
                            return f"data:{mime_type};base64,{base64_image}"

                raise RuntimeError("No image generated in response")

        except Exception as e:
            # Return a placeholder image URL if generation fails
            print(f"Warning: Image generation failed ({e}), using placeholder")
            return f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    def generate_content(self, caption_prompt: str, image_prompt: str, business_context: Dict = None) -> Dict[str, Any]:
        """
        Generate both caption and image from their respective prompts.

        Args:
            caption_prompt: Prompt for caption generation
            image_prompt: Prompt for image generation (should already have business context integrated)
            business_context: Optional dict with business data - DEPRECATED, business context should be in image_prompt

        Returns:
            Dict with 'caption' and 'image_url' keys
        """
        try:
            caption = self.generate_caption(caption_prompt)

            # Replace {{CAPTION}} placeholder in image_prompt with actual generated caption
            if caption and "{{CAPTION}}" in image_prompt:
                image_prompt = image_prompt.replace("{{CAPTION}}", caption)
                print(f"🔄 Replaced {{CAPTION}} placeholder in image prompt")

            # NOTE: Business context should already be integrated into image_prompt via template placeholders
            # during prompt generation. No need to append here as it creates duplication.

            # Warn if business_context is still being passed (deprecated usage)
            if business_context:
                print("⚠️  WARNING: business_context parameter is deprecated. Business context should be integrated into image_prompt during prompt generation.")

            image_url = self.generate_image(image_prompt)

            return {
                "caption": caption,
                "image_url": image_url,
                "status": "success"
            }

        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }


# Convenience functions for direct use
def generate_caption(caption_prompt: str) -> str:
    """Generate a caption from a prompt."""
    generator = ContentGenerator()
    return generator.generate_caption(caption_prompt)


def generate_image(image_prompt: str) -> str:
    """Generate an image from a prompt."""
    generator = ContentGenerator()
    return generator.generate_image(image_prompt)


def generate_content(caption_prompt: str, image_prompt: str, business_context: Dict = None) -> Dict[str, Any]:
    """Generate both caption and image from their prompts."""
    generator = ContentGenerator()
    return generator.generate_content(caption_prompt, image_prompt, business_context)


if __name__ == "__main__":
    # Example usage
    caption_prompt = "Write an engaging Instagram caption about productivity tips for entrepreneurs, including relevant hashtags."
    image_prompt = "Create a professional image showing a laptop with coffee and notebooks, modern office setting."

    generator = ContentGenerator()

    try:
        result = generator.generate_content(caption_prompt, image_prompt)
        print("Generated Content:")
        print(f"Caption: {result['caption']}")
        print(f"Image URL: {result['image_url'][:100]}...")
    except Exception as e:
        print(f"Error: {e}")