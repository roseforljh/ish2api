# main.py (v11.0.0 - The Background Task Fix)
print("--- LOADING PROXY SERVER V11.0.0 (BACKGROUND TASK FIX) ---")

import os
import httpx
import json
import time
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
    description="一个将请求动态转发到多个后端提供商的代理服务，内置Puter.js后台任务适配器。",
    version="11.0.0"
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

# --- Puter.js 后台任务 ---
async def fetch_puter_response(request_body: dict, api_key: str):
    puter_args = request_body.copy()
    puter_args["test_mode"] = False
    final_request_body = {
        "interface": "puter-chat-completion", "driver": "openrouter",
        "method": "complete", "args": puter_args
    }
    headers = COMMON_HEADERS.copy()
    headers['Authorization'] = f"Bearer {api_key}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(PROVIDER_URLS["puter"], json=final_request_body, headers=headers, timeout=120.0)
            response.raise_for_status()
            response_text = response.text
            response_list = json.loads(response_text)
            full_content = "".join(item.get("text", "") for item in response_list if item.get("type") == "text")
            return full_content
    except Exception as e:
        print(f"Error in fetch_puter_response: {e}")
        return f"Error fetching response from Puter: {e}"

# --- 核心代理函数 ---
async def stream_proxy(provider: str, request_body: dict):
    provider = provider.strip()
    
    if provider == "puter":
        api_key = PROVIDER_KEYS.get("puter")
        if not api_key:
            yield "data: {\"error\": \"Puter.js API Key not configured.\"}\n\n".encode('utf-8')
            return

        # 1. 立即发送一个“正在处理”的消息
        yield "data: {\"content\": \"正在请求Puter.js，请稍候...\"}\n\n".encode('utf-8')
        
        # 2. 在后台获取真实响应
        full_content = await fetch_puter_response(request_body, api_key)
        
        # 3. 将真实响应包装成流发送
        chunk_id = f"chatcmpl-{''.join(str(time.time()).split('.'))}"
        model_name = request_body.get("model")

        content_chunk = {
            "id": chunk_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
            "choices": [{"index": 0, "delta": {"content": full_content}, "finish_reason": None}]
        }
        yield f"data: {json.dumps(content_chunk)}\n\n".encode('utf-8')

        finish_chunk = {
            "id": chunk_id, "object": "chat.completion.chunk", "created": int(time.time()), "model": model_name,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }
        yield f"data: {json.dumps(finish_chunk)}\n\n".encode('utf-8')
        yield "data: [DONE]\n\n".encode('utf-8')
        return
    
    # --- 其他提供商的通用流式逻辑 ---
    target_url = PROVIDER_URLS.get(provider)
    # ... (generic logic)

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
