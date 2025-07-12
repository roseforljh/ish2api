# main.py (v15.0.0 - The Raw Requests Fix)
print("--- LOADING PROXY SERVER V15.0.0 (RAW REQUESTS FIX) ---")

import os
import httpx # Keep for other providers
import requests # Use for Puter.js
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
    description="一个将请求动态转发到多个后端提供商的代理服务，内置Puter.js原始请求适配器。",
    version="15.0.0"
)

# --- 提供商配置 ---
PROVIDER_URLS = {
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
}

# --- 核心代理函数 ---
def stream_proxy_sync(provider: str, request_body: dict):
    provider = provider.strip()
    target_url = PROVIDER_URLS.get(provider)
    if not target_url:
        return

    request_headers = COMMON_HEADERS.copy()
    api_key = PROVIDER_KEYS.get(provider)
    if api_key:
        request_headers['Authorization'] = f"Bearer {api_key}"

    # --- Puter.js 完全模拟适配器 ---
    if provider == "puter":
        puter_args = request_body.copy()
        puter_args["test_mode"] = False
        puter_args["driver"] = "openrouter"
        puter_args["interface"] = "puter-chat-completion"
        puter_args["method"] = "complete"
        
        final_request_body = {
            "interface": "puter-chat-completion",
            "driver": "openrouter",
            "method": "complete",
            "args": puter_args
        }
        
        try:
            # 使用 requests 库进行流式请求
            response = requests.post(target_url, json=final_request_body, headers=request_headers, stream=True, timeout=120.0)
            response.raise_for_status()
            
            print("--- PUTER STREAMING CONNECTION ESTABLISHED ---")
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    print(f"--- YIELDING CHUNK: {chunk.decode('utf-8', errors='ignore')} ---")
                    yield chunk

        except Exception as e:
            print(f"--- FATAL ERROR IN PUTER SYNC STREAMING: {e} ---")
            traceback.print_exc()
            return
    else:
        # ... (其他提供商的通用逻辑)
        pass

# --- FastAPI 路由 ---
@app.post("/{provider}/v1/chat/completions")
async def chat_completions_proxy(provider: str, payload: OpenAIChatRequest):
    request_body_dict = payload.dict(by_alias=True)
    request_body_dict['stream'] = True
    request_body_dict['temperature'] = 0
    return StreamingResponse(stream_proxy_sync(provider, request_body_dict), media_type="text/event-stream")

@app.get("/")
def read_root():
    return {"message": "Multi-Provider OpenAI-Compatible Proxy is running."}

# --- 运行服务器的入口 ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Multi-Provider Proxy Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
