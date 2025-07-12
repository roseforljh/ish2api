# main.py (v5.0.0 - The Final Fix)
print("--- LOADING PROXY SERVER V5.0.0 (FINAL FIX) ---")
print("--- PUTER.JS NON-STREAMING ADAPTER IS ACTIVE ---")

import os
import httpx
import json
import time
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
    version="5.0.0"
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
    target_url = PROVIDER_URLS.get(provider)
    if not target_url:
        # ... (error handling)
        return

    request_headers = COMMON_HEADERS.copy()
    api_key = PROVIDER_KEYS.get(provider)
    if api_key:
        request_headers['Authorization'] = f"Bearer {api_key}"

    # --- Puter.js 特殊处理逻辑 ---
    if provider == "puter":
        final_request_body = {
            "interface": "puter-chatcompletion", "driver": "operadriver",
            "method": "complete", "args": request_body
        }
        print("--- Converted request body for Puter.js format. ---")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(target_url, json=final_request_body, headers=request_headers, timeout=120.0)
                response.raise_for_status()
                response_data = response.json()
                print(f"--- Received non-streaming response from Puter: {response_data} ---")

                # --- 手动模拟OpenAI流式响应 ---
                chunk_id = f"chatcmpl-{''.join(str(time.time()).split('.'))}"
                model_name = request_body.get("model")
                full_content = response_data.get("content", "")

                # 1. 发送内容块
                content_chunk = {
                    "id": chunk_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
                    "choices": [{"index": 0, "delta": {"content": full_content}, "finish_reason": None}]
                }
                yield f"data: {json.dumps(content_chunk)}\n\n".encode('utf-8')

                # 2. 发送结束块
                finish_chunk = {
                    "id": chunk_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                }
                yield f"data: {json.dumps(finish_chunk)}\n\n".encode('utf-8')

                # 3. 发送 [DONE] 信号
                yield "data: [DONE]\n\n".encode('utf-8')
                return
        except Exception as e:
            print(f"Error during Puter.js non-streaming request: {e}")
            # ... (error handling)
            return
    
    # --- 其他提供商的通用流式逻辑 ---
    final_request_body = request_body
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", target_url, json=final_request_body, headers=request_headers, timeout=120.0) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk
    except Exception as e:
        print(f"Error during streaming request for {provider}: {e}")
        # ... (error handling)

# --- FastAPI 路由 ---
@app.post("/{provider}/v1/chat/completions")
async def chat_completions_proxy(provider: str, payload: OpenAIChatRequest):
    request_body_dict = payload.dict(by_alias=True)
    request_body_dict['stream'] = True
    request_body_dict['temperature'] = 0
    print(f"Forwarding request for model '{payload.model}' to provider '{provider}'")
    return StreamingResponse(stream_proxy(provider, request_body_dict), media_type="text/event-stream")

@app.get("/")
def read_root():
    return {"message": "Multi-Provider OpenAI-Compatible Proxy is running."}

# --- 运行服务器的入口 ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Multi-Provider Proxy Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
