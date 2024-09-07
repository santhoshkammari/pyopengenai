import asyncio

from opengenai.langchain_ollama import CustomChatOllama
from opengenai.web_search import CrewAIWebSearchQASystem

llm = CustomChatOllama(
    model="qwen2:7b-instruct",
    base_url="http://192.168.162.49:8888",
    temperature=0
)
questions = [
            "what are latest papers related to gemini1.5 flash",
            "who is pawan kalyan?",
            "latest advancements in generative ai",
            "what things came in pydantic new version"
            ]
for q in questions:
    crew = CrewAIWebSearchQASystem(llm=llm)
    answer = crew.run_question_answering(q)
    print(f"question : {q}\n")
    print('#'*40)
    print(answer)
    print('-'*40)

