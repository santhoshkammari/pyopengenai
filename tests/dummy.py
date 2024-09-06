import tiktoken
from langchain_ollama import ChatOllama
from opengenai.langchain_ollama import CustomChatOllama
from transformers import AutoTokenizer

class ChatQwen2Instruct:
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2-7B-Instruct")

    def get_text_chat_template(self,system,prompt):
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        return text


# Load the tiktoken model
encoding = tiktoken.get_encoding("o200k_base")

# Read the text from the file
with open('results.txt', 'r', encoding='utf-8') as file:
    text = file.read()

text = text[:30000]
print(text)

# Encode the text to tokens
tokens = encoding.encode(text)

# Count the number of tokens
num_tokens = len(tokens)
print(f"Number of tokens: {num_tokens}")

# Initialize the ChatOllama model
# llm = ChatOllama(model="qwen2:0.5b-instruct",
#                  temperature = 0,
#                  num_predict =1024
#                  )
llm = CustomChatOllama(
    model = "qwen2:7b-instruct",
    base_url = "http://192.168.162.49:8888",
    temperature = 0
)
SYSTEM = f"You are a helpful assistant. Answer the question based on the given context. <context>{text}</context>"
QUESTION = "what did you understand"

chat_qwen2 = ChatQwen2Instruct()
prompt = chat_qwen2.get_text_chat_template(SYSTEM,QUESTION)

# Stream the response
for chunk in llm.stream(prompt):
    print(chunk.content, end="", flush=True)