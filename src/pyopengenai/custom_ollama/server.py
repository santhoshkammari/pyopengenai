from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import StreamingResponse, JSONResponse
from langchain.chat_models import ChatOllama
from langchain.schema import HumanMessage

app = FastAPI()

class ChatInput(BaseModel):
    text: str
    model: str
    temperature: float
    num_predict: int

class BatchChatInput(BaseModel):
    messages: List[str]
    model: str
    temperature: float

# Store the current model instance
current_model = None
current_model_name = None

async def get_chat_model(model: str, temp: float, num_predict: int):
    global current_model, current_model_name

    # If the requested model is different from the current one, create a new instance
    if model != current_model_name:
        # Delete the previous model instance
        if current_model:
            del current_model


        # Create a new model instance
        current_model = ChatOllama(model=model, temperature=temp, num_predict=num_predict)
        current_model_name = model

    return current_model

async def chat_stream(text: str, model: str, temp: float, num_predict: int):
    chat_model = await get_chat_model(model, temp, num_predict)
    async for chunk in chat_model.astream([HumanMessage(content=text)]):
        yield chunk.content

async def process_batch(messages: List[str], model: str, temp: float):
    chat_model = await get_chat_model(model, temp, 0)  # Use 0 for num_predict in batch mode
    human_messages = [HumanMessage(content=msg) for msg in messages]
    responses = await chat_model.abatch(human_messages)
    return [response.content for response in responses]

@app.post("/chat")
async def chat_endpoint(chat_input: ChatInput):
    return StreamingResponse(chat_stream(chat_input.text, chat_input.model, chat_input.temperature, chat_input.num_predict), media_type="text/event-stream")

@app.post("/batch-chat")
async def batch_chat_endpoint(batch_input: BatchChatInput):
    results = await process_batch(batch_input.messages, batch_input.model, batch_input.temperature)
    return JSONResponse(content={"results": results})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
