from http.server import BaseHTTPRequestHandler
import json
import requests
import os

# 从Vercel环境变量读取API Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

class handler(BaseHTTPRequestHandler):

    # 新增：浏览器直接访问就能测试，确认路径通没通
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({
            "success": True,
            "message": "接口路径通了！可以正常使用AI分析功能了"
        }, ensure_ascii=False).encode('utf-8'))
        return

    # 处理前端的POST请求（核心AI分析功能）
    def do_POST(self):
        # 读取前端传来的账单数据
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        bill_data = json.loads(post_data.decode('utf-8'))

        # 提取核心字段
        year = bill_data.get('year', 2026)
        month = bill_data.get('month', 3)
        total_income = bill_data.get('total_income', 0)
        total_expense = bill_data.get('total_expense', 0)
        record_count = bill_data.get('record_count', 0)

        # 贴合大学生场景的Prompt，可随时修改
        system_prompt = f"""
        你是「极账」APP专属的大学生理财助手，语言亲切接地气，符合大学生说话习惯，不说教、不制造焦虑。
        基于账单数据输出内容：
        1. 一句话总结当月消费概况
        2. 2条完全贴合校园场景的可落地省钱建议
        账单数据：{year}年{month}月，总收入{total_income}元，总支出{total_expense}元，共{record_count}笔账单。
        """

        try:
            # 调用DeepSeek大模型
            response = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": system_prompt}],
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=15
            )
            ai_result = response.json()
            reply_content = ai_result["choices"][0]["message"]["content"]

            # 给前端返回结果，自动解决跨域问题
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "analysis": reply_content
            }, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            # 出错时返回详细错误，方便排查
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False).encode('utf-8'))

    # 处理前端跨域预检，避免调用报错
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return
