import asyncio
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage
from pydantic import BaseModel
from typing import List

app = FastAPI()

class ChatInput(BaseModel):
    text: str
    model: str
    temperature: float
    num_predict: float


class BatchChatInput(BaseModel):
    messages: List[str]
    model: str
    temperature: float

async def chat_stream(text: str, model: str, temp: float,num_predict):
    chat_model = ChatOllama(model=model, temperature=temp,num_predict = num_predict)
    async for chunk in chat_model.astream([HumanMessage(content=text)]):
        yield chunk.content

async def process_batch(messages: List[str], model: str, temp: float):
    chat_model = ChatOllama(model=model, temperature=temp)
    # Convert messages to HumanMessage objects
    human_messages = [HumanMessage(content=msg) for msg in messages]
    # Use the batch method for efficient processing
    responses = await chat_model.abatch(human_messages)
    # Extract content from responses
    return [response.content for response in responses]

@app.post("/chat")
async def chat_endpoint(chat_input: ChatInput):
    return StreamingResponse(chat_stream(chat_input.text, chat_input.model, chat_input.temperature,chat_input.num_predict), media_type="text/event-stream")

@app.post("/batch-chat")
async def batch_chat_endpoint(batch_input: BatchChatInput):
    results = await process_batch(batch_input.messages, batch_input.model, batch_input.temperature)
    return JSONResponse(content={"results": results})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)


