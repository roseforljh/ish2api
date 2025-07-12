# main.py (v16.0.0 - The Hybrid Fix)
print("--- LOADING PROXY SERVER V16.0.0 (HYBRID FIX) ---")

import os
import httpx
import requests
import json
import time
import traceback
import asyncio
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
    description="一个将请求动态转发到多个后端提供商的代理服务，内置Puter.js混合模式适配器。",
    version="16.0.0"
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
}

# --- Puter.js 同步请求函数 ---
def fetch_puter_sync(request_body: dict, api_key: str):
    puter_args = request_body.copy()
    puter_args["test_mode"] = False
    puter_args["driver"] = "openrouter"
    puter_args["interface"] = "puter-chat-completion"
    puter_args["method"] = "complete"
    
    final_request_body = {
        "interface": "puter-chat-completion", "driver": "openrouter",
        "method": "complete", "args": puter_args
    }
    
    headers = COMMON_HEADERS.copy()
    headers['Authorization'] = f"Bearer {api_key}"
    
    response = requests.post(PROVIDER_URLS["puter"], json=final_request_body, headers=headers, stream=True, timeout=120.0)
    response.raise_for_status()
    return response

# --- 核心代理函数 ---
async def stream_proxy(provider: str, request_body: dict):
    provider = provider.strip()
    
    # --- Puter.js 特殊处理逻辑 ---
    if provider == "puter":
        print("--- PUTER HYBRID LOGIC ACTIVATED ---")
        api_key = PROVIDER_KEYS.get("puter")
        if not api_key:
            yield "data: {\"error\": \"Puter.js API Key not configured.\"}\n\n".encode('utf-8')
            return
        
        try:
            # 在后台线程中运行同步的 requests 代码
            response = await asyncio.to_thread(fetch_puter_sync, request_body, api_key)
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        except Exception as e:
            print(f"--- FATAL ERROR IN PUTER HYBRID LOGIC: {e} ---")
            traceback.print_exc()
            return
    
    # --- 其他提供商的通用流式逻辑 ---
    else:
        print(f"--- EXECUTING GENERIC ASYNC (STREAMING) LOGIC FOR PROVIDER: {provider} ---")
        target_url = PROVIDER_URLS.get(provider)
        if not target_url:
            return

        request_headers = COMMON_HEADERS.copy()
        # (可以为其他提供商添加Key的逻辑)

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", target_url, json=request_body, headers=request_headers, timeout=120.0) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except Exception as e:
            print(f"Error during generic streaming request for {provider}: {e}")
            traceback.print_exc()

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
