# from prompt_template import TRENDY_TOPIC_PROMPT
# from generate import call_gpt_4o_mini
import db

# res = call_gpt_4o_mini(TRENDY_TOPIC_PROMPT)
# print(res)

# print("/n",res["caption_prompt"])
# print(res["image_prompt"])

profile_data = db.get_profile_business_data("58d91fe2-1401-46fd-b183-a2a118997fc1")

d = profile_data
    

print(d,"\n",type(d))

s = str(d)

print(type(s))