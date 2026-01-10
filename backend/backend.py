import base64
import json
import traceback  # 用于打印详细报错
import os
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from volcengine.visual.VisualService import VisualService

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# 初始化字节 SDK
visual_service = VisualService()

# 替换之前的硬编码
visual_service.set_ak(os.getenv('VOLC_AK'))
visual_service.set_sk(os.getenv('VOLC_SK'))


def call_seedream_api(image_base64: str, mode: str):
    # 【核心修正 1】：回归到你拥有权限的 4.0 正确 Key
    current_req_key = "jimeng_t2i_v40" 
    
    # 根据写真或表情包调整提示词
    if mode == "portrait":
        prompt = "Professional pet photography, Christmas theme, pet wearing a red Santa hat, cozy fireplace background, soft lighting, 8k resolution, highly detailed fur"
        strength = 0.6  # 4.0 模型的重绘强度建议在 0.5-0.7
    else:
        prompt = (
            "High-quality pet lifestyle photography, soft natural lighting, "
            "clean pastel cream background, pet looking at camera with innocent eyes, "
            "soft fluffy fur texture, heartwarming atmosphere, "
            "minimalist aesthetic, extremely detailed, 8k resolution, professional studio shot"
        )
        strength = 0.45 # 降低重绘强度，保证“还是你家那只猫”

    # 【核心修正 2】：参数完全对齐 4.0 规范
    body = {
        "req_key": current_req_key,
        "prompt": prompt,
        "binary_data_base64": [image_base64],
        "image_num": 1,
        "strength": strength,  # 强度参数，保持 i2i 逻辑
        "seed": -1,
        "width": 1024,         # 必须是整数，4.0 建议 1024
        "height": 1024         # 必须是整数
    }

    print(f"\n[DEBUG] 正在通过 4.0 T2I 接口运行图生图逻辑，req_key: {current_req_key}")

    try:
        resp = visual_service.cv_process(body)
        
        # 打印完整返回，如果成功我们会看到 image_list
        print("\n" + "="*50)
        print("字节 API 返回结果:")
        print(json.dumps(resp, indent=2, ensure_ascii=False))
        print("="*50 + "\n")

        # 检查状态码
        if resp.get("code") != 10000:
            return None, f"API报错: {resp.get('message')}"

        data = resp.get("data", {})
        
        # 4.0 模型的图片返回路径
        if "image_list" in data and len(data["image_list"]) > 0:
            return data["image_list"][0], None
        
        # 备选路径
        if "binary_data_base64" in data and len(data["binary_data_base64"]) > 0:
            return data["binary_data_base64"][0], None

        return None, "接口未返回图片数据"
        
    except Exception as e:
        print("[ERROR] 接口调用过程中崩溃:")
        import traceback
        print(traceback.format_exc())
        return None, str(e)

# def call_seedream_api(image_base64: str, mode: str):
#     # 这里请务必确认你的 req_key。
#     # 如果你是“图片生成4.0”，尝试用 high_aes_general_v20
#     # 如果你是“即梦AI-图片生成”，尝试用 doubao_seedream
#     current_req_key = "jimeng_t2i_v40" 
    
#     prompt = "Professional pet photography, Christmas theme, pet wearing Santa hat" if mode == "portrait" else "Funny pet meme"
    
#     body = {
#         "req_key": current_req_key,
#         "prompt": prompt,
#         "binary_data_base64": [image_base64],
#         "image_num": 1,
#         "strength": 0.5,
#         "seed": -1,
#         "size": "512x512" 
#     }

#     print(f"\n[DEBUG] 准备发送请求，req_key: {current_req_key}")

#     try:
#         resp = visual_service.cv_process(body)
#         print("\n" + "="*50)
#         print("字节 API 返回结果:")
#         print(json.dumps(resp, indent=2, ensure_ascii=False))
#         print("="*50 + "\n")

#         if resp.get("code") != 10000:
#             return None, f"API报错: {resp.get('message')}"

#         data = resp.get("data", {})
#         # 兼容不同接口的返回字段
#         result_img = data.get("image") or (data.get("image_list", [None])[0])
#         return result_img, None
#     except Exception as e:
#         print("[ERROR] call_seedream_api 内部崩溃:")
#         print(traceback.format_exc())
#         return None, str(e)

@app.post("/generate")
async def generate_image(
    file: UploadFile = File(...),
    mode: str = Form(...)
):
    print(f"\n[INFO] 收到请求: mode={mode}, filename={file.filename}")
    try:
        # 1. 读取并转换图片
        contents = await file.read()
        image_base64 = base64.b64encode(contents).decode('utf-8')
        
        # 2. 调用 API
        result_base64, error_msg = call_seedream_api(image_base64, mode)

        if error_msg:
            print(f"[ERROR] 业务逻辑错误: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        print("[SUCCESS] 生成成功")
        return {"result": result_base64}

    except Exception as e:
        print("[CRITICAL] 后端路由崩溃:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# import base64
# import json
# from fastapi import FastAPI, UploadFile, File, Form, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from volcengine.visual.VisualService import VisualService

# app = FastAPI()

# # 1. 配置 CORS，允许 Next.js 前端访问
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # 黑客松期间允许所有来源
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 2. 初始化火山引擎 Visual Service
# # 这里的 AK 和 SK 请替换为你的真实密钥
# visual_service = VisualService()

# def call_seedream_api(image_base64: str, mode: str):
#     """调用字节跳动即梦 AI 接口"""
    
#     # 根据模式设定不同的提示词和重绘强度
#     if mode == "portrait":
#         # 写真模式：更强调质感、圣诞氛围
#         prompt = (
#             "Professional pet photography, high quality, Christmas theme, "
#             "the pet is wearing a cute red Santa hat and a small scarf, "
#             "background is a cozy room with a decorated Christmas tree and warm bokeh lights, "
#             "8k resolution, cinematic lighting, highly detailed fur"
#         )
#         strength = 0.55  # 0.5-0.6 之间能保持宠物长相又添加节日元素
#     else:
#         # 表情包模式：更强调搞怪、简洁背景
#         prompt = (
#             "Funny pet meme style, exaggerated expression, "
#             "vibrant solid color background, studio lighting, "
#             "internet humor style, high contrast, crisp and clean"
#         )
#         strength = 0.7  # 强度稍高，让 AI 有更多搞怪空间

#     # 构建请求参数 (参考即梦AI文档)
#     # 注意：req_key 必须与你开通的服务一致，通常为 'doubao_seedream'
#     body = {
#         "req_key": "high_aes_general_v20", 
#         "prompt": prompt,
#         "binary_data_base64": [image_base64],
#         "image_num": 1,
#         "strength": strength,
#         "seed": -1, # 随机种子
#         "size": "512x512" # 也可以设为 1024x1024
#     }

#     try:
#         resp = visual_service.cv_process(body)
        
#         # --- 这里的打印非常重要，请观察终端输出 ---
#         print("\n" + "="*50)
#         print("字节 API 原始返回详情:")
#         print(json.dumps(resp, indent=2, ensure_ascii=False))
#         print("="*50 + "\n")
#         # ----------------------

#         if resp.get("code") != 10000:
#             return None, f"错误码:{resp.get('code')}, 消息:{resp.get('message')}"

#         # 有些接口返回的是 image，有些是 image_list
#         data = resp.get("data", {})
#         result = data.get("image") or data.get("image_list", [None])[0]
        
#         if not result:
#             return None, "接口未返回有效图片数据"
            
#         return result, None
#     except Exception as e:
#         return None, str(e)

# @app.post("/generate")
# async def generate_image(
#     file: UploadFile = File(...),
#     mode: str = Form(...) # 接收前端传来的 "portrait" 或 "meme"
# ):
#     # A. 校验文件类型
#     if not file.content_type.startswith("image/"):
#         raise HTTPException(status_code=400, detail="请上传图片文件")

#     # B. 读取文件并转为 Base64
#     try:
#         contents = await file.read()
#         image_base64 = base64.b64encode(contents).decode('utf-8')
#     except Exception:
#         raise HTTPException(status_code=500, detail="图片处理失败")

#     # C. 调用字节 API
#     result_base64, error_msg = call_seedream_api(image_base64, mode)

#     if error_msg:
#         raise HTTPException(status_code=500, detail=f"AI 生成失败: {error_msg}")

#     return {"result": result_base64}

# @app.get("/")
# def health_check():
#     return {"status": "ok", "message": "PetPulse AI Backend is running"}

# if __name__ == "__main__":
#     import uvicorn
#     # 监听 0.0.0.0 确保局域网内可以访问
#     uvicorn.run(app, host="0.0.0.0", port=8000)
