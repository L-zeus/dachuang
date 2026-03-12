from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# 加载环境变量（本地测试用，部署时由Vercel环境变量提供）
load_dotenv()

app = FastAPI()

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置：从环境变量读取API Key，绝对不要写死在代码里
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# --- 数据模型定义 ---

# 1. AI账单分析的请求体
class BillAnalysisRequest(BaseModel):
    year: int
    month: int
    total_income: float
    total_expense: float
    record_count: int
    bill_details: str  # 可以传JSON字符串格式的账单明细

# 2. AI对话的请求体
class ChatRequest(BaseModel):
    user_message: str
    context_bills: str = ""  # 可选：传入当前的账单数据作为上下文

# --- 核心接口 ---

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "mom-ledger-backend-python"}

@app.post("/api/ai-analysis")
async def ai_bill_analysis(request: BillAnalysisRequest):
    """
    接收前端传来的账单数据，返回结构化的AI分析报告
    """
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=500, detail="后端API Key未配置")

    # 构造针对大学生的System Prompt（这是AI分析的灵魂，你可以不断优化）
    system_prompt = f"""
    你是一个专业的大学生专属理财助手，擅长分析大学生的消费账单。
    请根据以下账单数据，生成一份结构化的分析报告，语言要亲切、接地气，符合大学生的说话习惯。
    报告请严格分为以下4个部分，用Markdown格式输出：
    1. 本月消费概况（一句话总结）
    2. 消费结构拆解（指出钱花在哪了，非必要消费占比）
    3. 消费行为洞察（比如周末消费是否过高、外卖占比等）
    4. 个性化省钱建议（给出2-3条可落地的、贴合校园场景的建议）
    
    数据：2026年{request.month}月，收入{request.total_income}元，支出{request.total_expense}元，共{request.record_count}笔账单。
    账单明细：{request.bill_details}
    """

    # 调用DeepSeek API
    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "请生成分析报告"}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # 尝试解析为 JSON 格式以兼容前端结构（如果 Prompt 返回的是 Markdown 文本，可能需要前端调整展示逻辑）
        # 这里为了兼容前端 AIAnalysis.tsx 的逻辑，我们将尝试把 AI 的 Markdown 输出包装成前端期望的 JSON 结构
        # 或者，我们需要修改前端代码来直接展示 Markdown。
        # 鉴于用户提供的 Prompt 要求 Markdown 输出，我们最好修改前端直接展示 Markdown，或者让后端把 Markdown 塞进 JSON 的 summary 字段。
        # 为了最小改动前端，我们构造一个符合 AIAnalysisResult 的 JSON
        
        return {
            "summary": content, # 暂时把所有内容放在 summary 中，或者前端需要改造成支持 Markdown 渲染
            "insights": [],
            "suggestions": [],
            "warnings": []
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI分析失败: {str(e)}")

@app.post("/api/chat")
async def ai_chat(request: ChatRequest):
    """
    对话式AI接口：支持用户问“我这个月餐饮花了多少钱”等问题
    """
    # 实现逻辑和上面类似，只是System Prompt不同，你可以自行扩展
    return {"success": True, "reply": "对话功能开发中..."}

# --- 本地测试用 ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
