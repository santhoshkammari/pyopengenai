from langchain_ollama import ChatOllama
from ....custom_ollama import CustomChatOllama

database = {
    "list_prompt":"\n\nalways return python list directly, i will directly use your response to Json.parse() expecting List example like ['first','second'...]"
}

class LLMPrompt:
    def __init__(
            self,
            template: str,
            model: str = "qwen2:7b-instruct",
            base_url: str = "http://192.168.162.49:8888",
            temperature: float = 0.0,
            device = "GPU"
    ):
        self.template = template
        self.llm = CustomChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature
        ) if device=="GPU" else ChatOllama(model=model,temperature=temperature)

    def get_formatted_prompt(self,**variables):
        formatted_prompt = self.template.format(**variables)
        return formatted_prompt + (database.get("list_prompt") if variables.get("return_type") == list else "")

    def __call__(self, **variables):
        return self.run(**variables)

    def run(self,**variables):
        p = self.get_formatted_prompt(**variables)
        response = self.llm.invoke(p).content
        return response

    def stream(self, **variables):
        for response in self.llm.stream(self.get_formatted_prompt(**variables)):
            yield response.content