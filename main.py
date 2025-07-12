# main.py (v9.0.0 - The Final Final Fix)
print("--- LOADING PROXY SERVER V9.0.0 (FINAL FIX) ---")

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
    version="9.0.0"
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
    target_url = PROVIDER_URLS.get(provider)
    if not target_url:
        return

    request_headers = COMMON_HEADERS.copy()
    api_key = PROVIDER_KEYS.get(provider)
    if api_key:
        request_headers['Authorization'] = f"Bearer {api_key}"

    # --- Puter.js 特殊处理逻辑 ---
    if provider == "puter":
        print("--- PUTER LOGIC ACTIVATED ---")
        puter_args = request_body.copy()
        puter_args["test_mode"] = False
        
        # 修正了 'interface' 和 'driver' 的值
        final_request_body = {
            "interface": "puter-chat-completion",
            "driver": "openrouter",
            "method": "complete",
            "args": puter_args
        }
        print(f"--- FINAL PUTER REQUEST BODY: {json.dumps(final_request_body, indent=2)} ---")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(target_url, json=final_request_body, headers=request_headers, timeout=120.0)
                response.raise_for_status()
                response_text = response.text
                print(f"--- PUTER RAW RESPONSE: {response_text} ---")

                full_content = ""
                # 修正：Puter的响应可能不是一个标准的JSON数组，而是多个JSON对象拼接的字符串
                # 我们需要找到一种更健壮的方式来解析它
                try:
                    # 尝试解析为JSON数组
                    response_list = json.loads(response_text)
                    full_content = "".join(item.get("text", "") for item in response_list if item.get("type") == "text")
                except json.JSONDecodeError:
                    # 如果失败，尝试按行解析
                    print("--- JSON Array parsing failed, trying line-by-line parsing... ---")
                    for line in response_text.strip().split('\n'):
                        line = line.strip()
                        if line.startswith("data:"):
                            try:
                                json_str = line[5:].strip()
                                if json_str:
                                    data_chunk = json.loads(json_str)
                                    if data_chunk.get("type") == "text":
                                        full_content += data_chunk.get("text", "")
                            except json.JSONDecodeError:
                                continue
                
                print(f"--- PARSED FULL CONTENT: {full_content} ---")

                # --- 手动模拟OpenAI流式响应 ---
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
        except Exception as e:
            print(f"--- FATAL ERROR IN PUTER LOGIC: {type(e).__name__}: {e} ---")
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
    return StreamingResponse(stream_proxy(provider, request_body_dict), media_type="text/event-stream")

@app.get("/")
def read_root():
    return {"message": "Multi-Provider OpenAI-Compatible Proxy is running."}

# --- 运行服务器的入口 ---
if __name__ == "__main__":
    import uvicorn
    print("Starting Multi-Provider Proxy Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
