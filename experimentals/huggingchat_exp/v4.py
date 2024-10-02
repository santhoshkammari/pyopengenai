from typing import List

from hugchat import hugchat
from hugchat.login import Login

# Log in to huggingface and grant authorization to huggingchat
EMAIL = "santhoshkammari1999@gmail.com"
PASSWD = "SK99@pass123"
cookie_path_dir = "./cookies/" # NOTE: trailing slash (/) is required to avoid errors
sign = Login(EMAIL, PASSWD)
cookies = sign.login(cookie_dir_path=cookie_path_dir, save_cookies=True)

# Create your ChatBot
qwen_model = "Qwen/Qwen2.5-72B-Instruct"
chatbot = hugchat.ChatBot(cookies=cookies.get_dict(),
                          default_llm=qwen_model)  # or cookie_path="usercookies/<email>.json"

print([x.name for x in chatbot.get_available_llm_models()])
exit()
text = "give me python code to sum two numpy ararys"
# Stream response
for resp in chatbot.chat(
    text,
    stream=True
):
    if resp:
        print(resp['token'],end = "",flush=True)

# Web search
print("WEBSEARCH.................")
query_result = chatbot.chat("Hi!", web_search=True)
print(query_result)
for source in query_result.web_search_sources:
    print(source.link)
    print(source.title)