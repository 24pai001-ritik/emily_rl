from prompt_template import TRENDY_TOPIC_PROMPT
from generate import call_gpt_4o_mini



res = call_gpt_4o_mini(TRENDY_TOPIC_PROMPT)
print(res)

print("/n",res["caption_prompt"])
print(res["image_prompt"])