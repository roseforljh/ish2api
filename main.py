# main.py (v10.0.0 - The Isolation Test)
print("--- LOADING PROXY SERVER V10.0.0 (ISOLATION TEST) ---")

import os
import httpx
import json
import time
import traceback
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# --- Pydantic 模型 ---
class ChatMessage(BaseModel):
    role: str
    content: str

class OpenAIChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = Field(4000, alias='max_tokens')
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = True

# --- FastAPI 应用实例 ---
app = FastAPI(
    title="Multi-Provider OpenAI-Compatible Proxy",
    description="一个将请求动态转发到多个后端提供商的代理服务，内置Puter.js适配器。",
    version="10.0.0"
)

# --- 提供商配置 ---
PROVIDER_URLS = {
    "pollinations": "https://text.pollinations.ai/openai",
    "puter": "https://api.puter.com/drivers/call",
}
PROVIDER_KEYS = {
    "puter": os.getenv("PUTER_API_KEY", None),
}
COMMON_HEADERS = {
    'Accept': '*/*',
    'Content-Type': 'application/json',
    'Origin': 'https://ish.junioralive.in',
    'Referer': 'https://ish.junioralive.in/',
}

# --- 核心代理函数 ---
async def stream_proxy(provider: str, request_body: dict):
    provider = provider.strip()
    
    # --- Puter.js 隔离测试逻辑 ---
    if provider == "puter":
        print("--- PUTER ISOLATION TEST ACTIVATED ---")
        try:
            # 1. 创建一个假的回复内容
            full_content = "这是一个来自代理服务器的测试信号。如果能看到这条消息，说明流媒体本身是通的。"
            
            # 2. 手动模拟OpenAI流式响应
            chunk_id = f"chatcmpl-{''.join(str(time.time()).split('.'))}"
            model_name = request_body.get("model")

            content_chunk = {
                "id": chunk_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
                "choices": [{"index": 0, "delta": {"content": full_content}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(content_chunk)}\n\n".encode('utf-8')
            print("--- YIELDED TEST DATA ---")

            finish_chunk = {
                "id": chunk_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(finish_chunk)}\n\n".encode('utf-8')
            yield "data: [DONE]\n\n".encode('utf-8')
            print("--- FINISHED YIELDING TEST DATA ---")
            return
        except Exception as e:
            print(f"--- FATAL ERROR IN PUTER ISOLATION TEST: {e} ---")
            return
    
    # --- 其他提供商的通用流式逻辑 ---
    target_url = PROVIDER_URLS.get(provider)
    if not target_url:
        return
    
    request_headers = COMMON_HEADERS.copy()
    final_request_body = request_body
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", target_url, json=final_request_body, headers=request_headers, timeout=120.0) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk
    except Exception as e:
        print(f"Error during streaming request for {provider}: {e}")

# --- FastAPI 路由 ---
@app.post("/{provider}/v1/chat/completions")
async def chat_completions_proxy(provider: str, payload: OpenAIChatRequest):
    request_body_dict = payload.dict(by_alias=True)
    request_body_dict['stream'] = True
    request_body_dict['temperature'] = 0
    return StreamingResponse(stream_proxy(provider, request_body_dict), media_type="text/event-stream")

@app.get("/")
def read_root():
    return {"message": "Multi-Provider OpenAI-Compatible Proxy is running."}

# --- 运行服务器的入口 ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Multi-Provider Proxy Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
