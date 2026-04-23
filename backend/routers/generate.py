"""
backend/routers/generate.py — Text-to-image generation + prompt enhancement
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from services.hd_image_generation import generate_hd_image
from services.prompt_enhancement import enhance_prompt
from backend.utils import extract_urls

router = APIRouter(tags=["Generate"])


class GenerateRequest(BaseModel):
    prompt: str
    num_results: int = 1
    aspect_ratio: str = "1:1"
    enhance_image: bool = True
    style: str = "Realistic"
    prompt_enhancement: bool = False
    content_moderation: bool = True


class EnhanceRequest(BaseModel):
    prompt: str


@router.post("/generate")
async def generate(req: GenerateRequest, x_api_key: str = Header(...)):
    medium = "photography" if req.style == "Realistic" else "art"
    full_prompt = req.prompt if req.style == "Realistic" else f"{req.prompt}, in {req.style.lower()} style"
    try:
        result = generate_hd_image(
            prompt=full_prompt,
            api_key=x_api_key,
            num_results=req.num_results,
            aspect_ratio=req.aspect_ratio,
            sync=True,
            enhance_image=req.enhance_image,
            medium=medium,
            prompt_enhancement=req.prompt_enhancement,
            content_moderation=req.content_moderation,
        )
        urls = extract_urls(result)
        if not urls:
            raise HTTPException(status_code=500, detail="No image URLs returned from Bria API")
        return {"result_urls": urls}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance-prompt")
async def enhance(req: EnhanceRequest, x_api_key: str = Header(...)):
    try:
        enhanced = enhance_prompt(x_api_key, req.prompt)
        return {"enhanced_prompt": enhanced}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
