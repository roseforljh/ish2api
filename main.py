# main.py (v7.0.0 - The Ultimate Debug)
print("--- LOADING PROXY SERVER V7.0.0 (ULTIMATE DEBUG) ---")

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
    version="7.0.0"
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
    print(f"--- [1] STREAM_PROXY CALLED FOR PROVIDER: '[{provider}]' ---")
    provider = provider.strip()

    target_url = PROVIDER_URLS.get(provider)
    if not target_url:
        print(f"--- [E1] ERROR: UNKNOWN PROVIDER '{provider}' ---")
        return

    request_headers = COMMON_HEADERS.copy()
    api_key = PROVIDER_KEYS.get(provider)
    if api_key:
        request_headers['Authorization'] = f"Bearer {api_key}"

    # --- Puter.js 特殊处理逻辑 ---
    if provider == "puter":
        print("--- [2] PUTER LOGIC ACTIVATED ---")
        puter_args = request_body.copy()
        puter_args["test_mode"] = False
        
        final_request_body = {
            "interface": "puter-chatcompletion", "driver": "operadriver",
            "method": "complete", "args": puter_args
        }
        
        try:
            print("--- [3] PUTER: ENTERING HTTPX CLIENT BLOCK ---")
            async with httpx.AsyncClient() as client:
                print("--- [4] PUTER: SENDING POST REQUEST ---")
                response = await client.post(target_url, json=final_request_body, headers=request_headers, timeout=120.0)
                print(f"--- [5] PUTER: RESPONSE RECEIVED, STATUS: {response.status_code} ---")
                
                response.raise_for_status()
                
                print("--- [6] PUTER: READING RESPONSE BODY ---")
                response_bytes = await response.aread()
                response_text = response_bytes.decode('utf-8')
                print(f"--- [7] PUTER: RAW RESPONSE TEXT: {response_text} ---")

                response_list = json.loads(response_text)
                full_content = "".join(item.get("text", "") for item in response_list if item.get("type") == "text")
                
                print("--- [8] PUTER: STARTING TO YIELD FAKE STREAM ---")
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
                print("--- [9] PUTER: FINISHED YIELDING ---")
                return
        except Exception as e:
            print(f"--- [E2] FATAL ERROR IN PUTER LOGIC: {type(e).__name__}: {e} ---")
            traceback.print_exc()
            return
    else:
        print(f"--- [10] EXECUTING GENERIC (STREAMING) LOGIC FOR PROVIDER: {provider} ---")
        # ... (generic logic)

# --- FastAPI 路由 ---
@app.post("/{provider}/v1/chat/completions")
async def chat_completions_proxy(provider: str, payload: OpenAIChatRequest):
    request_body_dict = payload.dict(by_alias=True)
    request_body_dict['stream'] = True
    request_body_dict['temperature'] = 0
    print(f"--- [0] FORWARDING REQUEST FOR MODEL '{payload.model}' TO PROVIDER '{provider}' ---")
    return StreamingResponse(stream_proxy(provider, request_body_dict), media_type="text/event-stream")

@app.get("/")
def read_root():
    return {"message": "Multi-Provider OpenAI-Compatible Proxy is running."}

# --- 运行服务器的入口 ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Multi-Provider Proxy Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
