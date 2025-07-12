# main.py (v1.0.3 - With Sponsor Adblock)

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
    title="Pollinations OpenAI-Compatible Proxy",
    description="一个将 OpenAI API 请求转发到 Pollinations 服务的代理，并内置广告过滤。",
    version="1.0.3"
)

# --- 关键的 Headers ---
POLLINATIONS_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Content-Type': 'application/json',
    'Origin': 'https://ish.junioralive.in',
    'Referer': 'https://ish.junioralive.in/',
    'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
}

TARGET_URL = os.getenv("TARGET_URL", "https://text.pollinations.ai/openai")

# --- 核心：流式代理函数 ---
async def stream_proxy(request_body: dict):
    """
    一个异步生成器，用于请求目标API并流式返回响应内容。
    内置了对 "Sponsor" 关键词的检测和过滤。
    """
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream(
                "POST",
                TARGET_URL,
                json=request_body,
                headers=POLLINATIONS_HEADERS,
                timeout=120.0
            ) as response:
                response.raise_for_status()
                
                # =================== 广告过滤逻辑开始 ===================
                async for chunk in response.aiter_bytes():
                    # 将二进制块解码为字符串以便检查内容，使用 errors='ignore' 避免解码错误
                    chunk_str = chunk.decode('utf-8', errors='ignore')

                    # 检查解码后的字符串是否包含 "Sponsor" 关键词
                    if "Sponsor" in chunk_str:
                        print("Sponsor content detected. Stopping the stream to the client.")
                        # 发现广告，立即中断循环，不再向客户端发送任何数据
                        break
                    
                    # 如果没有广告，将原始的二进制块转发给客户端
                    yield chunk
                # =================== 广告过滤逻辑结束 ===================

        except httpx.HTTPStatusError as e:
            response_content = await e.response.aread()
            try:
                details = response_content.decode('utf-8')
            except UnicodeDecodeError:
                details = "Error response could not be decoded."

            error_details = {
                "error": {
                    "message": f"Upstream API error: {e.response.status_code}",
                    "type": "upstream_error",
                    "details": details
                }
            }
            error_message = f"data: {json.dumps(error_details)}\n\n"
            yield error_message.encode('utf-8')
            print(f"Error from upstream API: {e.response.status_code} - {details}")
        except Exception as e:
            error_details = {"error": {"message": f"An unexpected error occurred: {str(e)}", "type": "proxy_error"}}
            error_message = f"data: {json.dumps(error_details)}\n\n"
            yield error_message.encode('utf-8')
            print(f"An unexpected error occurred: {e}")

# --- FastAPI 路由 ---
@app.post("/v1/chat/completions")
async def chat_completions_proxy(payload: OpenAIChatRequest):
    request_body_dict = payload.dict(by_alias=True)
    request_body_dict['stream'] = True
    print(f"Forwarding request for model '{payload.model}' to {TARGET_URL}")
    return StreamingResponse(
        stream_proxy(request_body_dict),
        media_type="text/event-stream"
    )

@app.get("/")
def read_root():
    return {"message": "Pollinations OpenAI-Compatible Proxy is running. Use the /v1/chat/completions endpoint."}

# --- 运行服务器的入口 ---
if __name__ == "__main__":
    import uvicorn
    print("Starting server...")
    print(f"Forwarding requests to: {TARGET_URL}")
    print("OpenAI compatible endpoint available at: http://127.0.0.1:8000/v1/chat/completions")
    uvicorn.run(app, host="0.0.0.0", port=8000)
