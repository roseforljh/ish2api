# main.py

import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# --- Pydantic 模型：定义和验证 OpenAI 格式的请求体 ---

class ChatMessage(BaseModel):
    role: str
    content: str

class OpenAIChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = Field(4000, alias='max_tokens') # 别名和默认值
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = True

# --- FastAPI 应用实例 ---

app = FastAPI(
    title="Pollinations OpenAI-Compatible Proxy",
    description="一个将 OpenAI API 请求转发到 Pollinations 服务的代理",
    version="1.0.0"
)

# --- 关键的 Headers ---
# 这是我们逆向研究的成果，必须精确模拟浏览器行为
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
    # 注意：根据你的抓包结果，可以更新 'Sec-Ch-Ua' 和 'User-Agent' 中的浏览器版本号
}

# 从环境变量读取目标URL，如果不存在则使用默认值
TARGET_URL = os.getenv("TARGET_URL", "https://text.pollinations.ai/openai")

# --- 核心：流式代理函数 ---

async def stream_proxy(request_body: dict):
    """
    一个异步生成器，用于请求目标API并流式返回响应内容。
    """
    # 使用 httpx 异步发起流式请求
    async with httpx.AsyncClient() as client:
        try:
            # `client.stream` 会保持连接，并允许我们迭代接收数据块
            async with client.stream(
                "POST",
                TARGET_URL,
                json=request_body,
                headers=POLLINATIONS_HEADERS,
                timeout=120.0  # 设置一个较长的超时时间以支持长响应
            ) as response:
                # 检查后端服务是否返回了错误
                response.raise_for_status()
                # 异步迭代响应的数据块，并直接 yield 出去
                async for chunk in response.aiter_bytes():
                    yield chunk
        except httpx.HTTPStatusError as e:
            # 如果后端返回错误状态码，则构造一个错误信息流
            error_message = f"data: {{'error': 'Upstream API error: {e.response.status_code}', 'details': '{e.response.text}'}}\n\n"
            yield error_message.encode('utf-8')
            print(f"Error from upstream API: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            error_message = f"data: {{'error': 'An unexpected error occurred: {str(e)}'}}\n\n"
            yield error_message.encode('utf-8')
            print(f"An unexpected error occurred: {e}")


# --- FastAPI 路由 ---
# 我们使用标准的 OpenAI 路径来确保最大兼容性

@app.post("/v1/chat/completions")
async def chat_completions_proxy(payload: OpenAIChatRequest):
    """
    接收 OpenAI 格式的请求，并将其流式转发到 Pollinations API。
    """
    # 将 Pydantic 模型转换为字典，以便作为 JSON 发送
    request_body_dict = payload.dict(by_alias=True)

    # 确保 stream 参数为 true，因为我们的代理是为流式设计的
    request_body_dict['stream'] = True

    print(f"Forwarding request for model '{payload.model}' to {TARGET_URL}")

    # 返回一个 StreamingResponse，它会消耗我们的异步生成器
    return StreamingResponse(
        stream_proxy(request_body_dict),
        media_type="text/event-stream"
    )

@app.get("/")
def read_root():
    return {"message": "Pollinations OpenAI-Compatible Proxy is running. Use the /v1/chat/completions endpoint."}

# --- 运行服务器的入口 (可选) ---
if __name__ == "__main__":
    import uvicorn
    print("Starting server...")
    print(f"Forwarding requests to: {TARGET_URL}")
    print("OpenAI compatible endpoint available at: http://127.0.0.1:8000/v1/chat/completions")
    uvicorn.run(app, host="0.0.0.0", port=8000)