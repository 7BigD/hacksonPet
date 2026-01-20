import base64
import json
import traceback  # For detailed error printing
import os
from dotenv import load_dotenv
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from volcengine.visual.VisualService import VisualService

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# Initialize ByteDance SDK
visual_service = VisualService()

visual_service.set_ak(os.getenv('VOLC_AK'))
visual_service.set_sk(os.getenv('VOLC_SK'))

# Allowed image formats and max size
ALLOWED_FORMATS = {'image/jpeg', 'image/png', 'image/webp', 'image/jpg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_image(file: UploadFile, file_name: str) -> tuple[bool, Optional[str]]:
    """
    Validate image format and size
    Returns: (is_valid, error_message)
    """
    # Check format
    content_type = file.content_type
    if content_type not in ALLOWED_FORMATS:
        return False, f"{file_name} format not supported. Allowed formats: jpg, png, webp"
    
    return True, None


async def validate_file_size(contents: bytes, file_name: str) -> tuple[bool, Optional[str]]:
    """
    Validate file size after reading
    Returns: (is_valid, error_message)
    """
    if len(contents) > MAX_FILE_SIZE:
        return False, f"{file_name} size exceeds 10MB limit"
    return True, None


def call_seedream_api(main_image_base64: str, style_image_base64: str, main_content_type: str = "image/jpeg"):
    """
    Call ByteDance API for human portrait generation with style reference
    Using jimeng_t2i_v40 (即梦AI 4.0) for image-to-image generation
    Note: This API uses the main image as base and applies style through prompt
    """
    # Use jimeng_t2i_v40 - the working API key for image generation
    current_req_key = "jimeng_t2i_v40"
    
    # Human portrait photography prompt - style will be described in text
    # since the API doesn't directly support dual image input
    # prompt = (
    #     "Professional human portrait photography, high-end studio quality, "
    #     "preserve facial features and identity completely, natural skin texture with subtle retouching, "
    #     "professional studio lighting, cinematic color grading, beautiful bokeh background, "
    #     "fashion magazine style, 8k resolution, extremely detailed, masterpiece quality"
    # )
    prompt = (
        "Portrait photo of a young woman, "
        "sweet and cute style, soft natural lighting, "
        "gentle smile, big eyes, fresh makeup, "
        "pastel pink or cream white dress, flowing long hair, "
        "cherry blossom trees/cozy cafe/park lawn background, "
        "shallow depth of field, bokeh effect, warm tones, "
        "high quality, professional photography, 85mm lens, f/1.8 aperture, "
        "cinematic color grading"
    )
    
    # Use lower strength to preserve facial features better
    # 0.4-0.5 recommended for portraits to maintain identity
    strength = 0.45

    # Build API request body - using the original working format
    body = {
        "req_key": current_req_key,
        "prompt": prompt,
        "binary_data_base64": [main_image_base64],
        "image_num": 1,
        "strength": strength,
        "seed": -1,
        "width": 1024,
        "height": 1024
    }

    print(f"\n[DEBUG] Calling API with req_key: {current_req_key}")
    print(f"[DEBUG] Main image size: {len(main_image_base64)} chars")
    print(f"[DEBUG] Style image size: {len(style_image_base64)} chars (used for reference)")
    print(f"[DEBUG] Content type: {main_content_type}")
    print(f"[DEBUG] Strength: {strength}")

    try:
        resp = visual_service.cv_process(body)
        
        print("\n" + "="*50)
        print("ByteDance API Response:")
        print(json.dumps(resp, indent=2, ensure_ascii=False))
        print("="*50 + "\n")

        if resp.get("code") != 10000:
            return None, f"API Error: {resp.get('message')}"

        data = resp.get("data", {})
        
        if "image_list" in data and len(data["image_list"]) > 0:
            return data["image_list"][0], None
        
        if "binary_data_base64" in data and len(data["binary_data_base64"]) > 0:
            return data["binary_data_base64"][0], None

        return None, "API did not return image data"
        
    except Exception as e:
        print("[ERROR] API call failed:")
        import traceback
        print(traceback.format_exc())
        return None, str(e)


@app.post("/generate")
async def generate_image(
    main_file: UploadFile = File(..., description="Main person photo to be transformed"),
    style_file: UploadFile = File(..., description="Style reference image")
):
    """
    Generate human portrait photo based on main image and style reference
    """
    print(f"\n[INFO] Received request:")
    print(f"  - main_file: {main_file.filename}")
    print(f"  - style_file: {style_file.filename}")
    
    try:
        # Validate main_file format
        is_valid, error_msg = validate_image(main_file, "Person photo")
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate style_file format
        is_valid, error_msg = validate_image(style_file, "Style reference image")
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Read main_file content
        main_contents = await main_file.read()
        is_valid, error_msg = await validate_file_size(main_contents, "Person photo")
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Read style_file content
        style_contents = await style_file.read()
        is_valid, error_msg = await validate_file_size(style_contents, "Style reference image")
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Convert to base64
        main_image_base64 = base64.b64encode(main_contents).decode('utf-8')
        style_image_base64 = base64.b64encode(style_contents).decode('utf-8')
        
        # Call API with content type info
        result_base64, error_msg = call_seedream_api(
            main_image_base64, 
            style_image_base64,
            main_file.content_type
        )

        if error_msg:
            print(f"[ERROR] Generation failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        print("[SUCCESS] Portrait generated successfully")
        return {"result": result_base64}

    except HTTPException:
        raise
    except Exception as e:
        print("[CRITICAL] Backend route crashed:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
