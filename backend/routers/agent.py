"""
backend/routers/agent.py — AI Agent: parse intent, execute plan, memory management
"""
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from services.agent import parse_intent, execute_plan, answer_question, AgentPlan, AgentStep
from backend import memory_store
from backend.utils import extract_urls
import json

router = APIRouter(tags=["Agent"])


# ── Memory endpoints ─────────────────────────────────────────────────────────

@router.get("/agent/memory")
def get_memory():
    return memory_store.get_preferences()


@router.post("/agent/memory")
def save_memory(key: str, value: str):
    memory_store.save_preference(key, value)
    return {"ok": True}


@router.delete("/agent/memory/{key}")
def delete_memory(key: str):
    memory_store.clear_preference(key)
    return {"ok": True}


@router.delete("/agent/memory")
def clear_memory():
    memory_store.clear_all_preferences()
    return {"ok": True}


# ── Agent parse + execute ────────────────────────────────────────────────────

class ParseRequest(BaseModel):
    user_text: str
    image_provided: bool = False
    model: str = "llama3"
    ollama_url: str = "http://localhost:11434"


class ExecuteRequest(BaseModel):
    plan: dict          # serialized AgentPlan
    model: str = "llama3"
    ollama_url: str = "http://localhost:11434"


class QuestionRequest(BaseModel):
    user_text: str
    history: list = []
    model: str = "llama3"
    ollama_url: str = "http://localhost:11434"


def _deserialize_plan(plan_dict: dict) -> AgentPlan:
    steps = [
        AgentStep(
            service_name=s["service_name"],
            params=s.get("params", {}),
            use_previous_output=s.get("use_previous_output", False),
        )
        for s in plan_dict.get("steps", [])
    ]
    return AgentPlan(steps=steps, original_request=plan_dict.get("original_request", ""))


def _serialize_plan(plan: AgentPlan) -> dict:
    return {
        "original_request": plan.original_request,
        "steps": [
            {
                "service_name": s.service_name,
                "params": s.params,
                "use_previous_output": s.use_previous_output,
            }
            for s in plan.steps
        ],
    }


@router.post("/agent/parse")
async def agent_parse(req: ParseRequest):
    prefs = memory_store.get_preferences()
    plan, used_llm = parse_intent(
        user_text=req.user_text,
        image_provided=req.image_provided,
        preferences=prefs,
        model=req.model,
        ollama_url=req.ollama_url,
    )
    if plan is None:
        return {"type": "question", "plan": None, "used_llm": used_llm}
    return {"type": "plan", "plan": _serialize_plan(plan), "used_llm": used_llm}


@router.post("/agent/execute")
async def agent_execute(
    plan_json: str = Form(...),
    model: str = Form("llama3"),
    ollama_url: str = Form("http://localhost:11434"),
    file: Optional[UploadFile] = File(None),
    x_api_key: str = Header(...),
):
    plan_dict = json.loads(plan_json)
    plan = _deserialize_plan(plan_dict)
    image_data = await file.read() if file else None
    try:
        urls = execute_plan(
            plan=plan,
            initial_image_data=image_data,
            api_key=x_api_key,
        )
        return {"result_urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/answer")
async def agent_answer(req: QuestionRequest):
    answer = answer_question(
        user_text=req.user_text,
        history=req.history,
        model=req.model,
        ollama_url=req.ollama_url,
    )
    return {"answer": answer}
