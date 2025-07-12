# main.py (v4.0.0 - Puter.js Format Adapter)

import os
import httpx
import json
from fastapi import FastAPI, Request
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
    description="一个将请求动态转发到多个后端提供商的代理服务，内置Puter.js格式转换器。",
    version="4.0.0"
)

# --- 提供商和目标地址映射 ---
PROVIDER_URLS = {
    "pollinations": "https://text.pollinations.ai/openai",
    "puter": "https://api.puter.com/drivers/call",
    "chatwithmono": "https://api.chatwithmono.com/v1/chat/completions", # 示例地址
}

# --- 提供商认证密钥 ---
PROVIDER_KEYS = {
    "puter": os.getenv("PUTER_API_KEY", None),
    "chatwithmono": os.getenv("CHATWITHMONO_API_KEY", None)
}

# --- 通用 Headers ---
COMMON_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Content-Type': 'application/json',
    'Origin': 'https://ish.junioralive.in',
    'Referer': 'https://ish.junioralive.in/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
}

# --- 核心：流式代理函数 ---
async def stream_proxy(provider: str, request_body: dict):
    target_url = PROVIDER_URLS.get(provider)
    if not target_url:
        error_details = {"error": {"message": f"Unknown provider: {provider}", "type": "proxy_error"}}
        yield f"data: {json.dumps(error_details)}\n\n".encode('utf-8')
        return

    # --- 动态添加认证头 ---
    request_headers = COMMON_HEADERS.copy()
    api_key = PROVIDER_KEYS.get(provider)
    if api_key:
        request_headers['Authorization'] = f"Bearer {api_key}"

    # --- Puter.js 请求格式转换 ---
    final_request_body = request_body
    if provider == "puter":
        # 将标准OpenAI请求体转换为Puter.js的特殊格式
        final_request_body = {
            "interface": "puter-chatcompletion",
            "driver": "operadriver",
            "method": "complete",
            "args": request_body
        }
        print("Converted request body for Puter.js format.")

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                target_url,
                json=final_request_body,
                headers=request_headers,
                timeout=120.0
            ) as response:
                if response.status_code >= 400:
                    error_content = await response.aread()
                    details = error_content.decode('utf-8', errors='ignore')
                    error_details = {
                        "error": {
                            "message": f"Upstream API error: {response.status_code}",
                            "type": "upstream_error",
                            "provider": provider,
                            "details": details
                        }
                    }
                    yield f"data: {json.dumps(error_details)}\n\n".encode('utf-8')
                    print(f"Error from upstream API [{provider}]: {response.status_code} - {details}")
                    return

                async for chunk in response.aiter_bytes():
                    yield chunk

    except httpx.RequestError as e:
        error_details = {"error": {"message": f"Request to upstream failed: {str(e)}", "type": "request_error"}}
        yield f"data: {json.dumps(error_details)}\n\n".encode('utf-8')
        print(f"An httpx.RequestError occurred for provider {provider}: {e}")
    except Exception as e:
        error_details = {"error": {"message": f"An unexpected error occurred: {str(e)}", "type": "proxy_error"}}
        yield f"data: {json.dumps(error_details)}\n\n".encode('utf-8')
        print(f"An unexpected error occurred for provider {provider}: {e}")

# --- FastAPI 路由 ---
@app.post("/{provider}/v1/chat/completions")
async def chat_completions_proxy(provider: str, payload: OpenAIChatRequest):
    request_body_dict = payload.dict(by_alias=True)
    
    # 强制 stream 为 true
    request_body_dict['stream'] = True
    
    # 强制 temperature 为 0
    original_temp = request_body_dict.get('temperature')
    request_body_dict['temperature'] = 0
    print(f"Forcing temperature to 0. Original value was: {original_temp}")

    print(f"Forwarding request for model '{payload.model}' to provider '{provider}'")
    print(f"Original Request Body: {json.dumps(request_body_dict, indent=2)}")
    
    return StreamingResponse(
        stream_proxy(provider, request_body_dict),
        media_type="text/event-stream"
    )

@app.get("/")
def read_root():
    return {"message": "Multi-Provider OpenAI-Compatible Proxy is running. Use /{provider}/v1/chat/completions endpoint."}

# --- 运行服务器的入口 ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Multi-Provider Proxy Server...")
    print("Available providers:")
    for p in PROVIDER_URLS:
        print(f"- {p}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
