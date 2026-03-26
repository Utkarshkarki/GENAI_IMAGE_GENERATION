"""
services/agent.py — AI Agent for AdSnap Studio
Parses natural-language instructions into ordered Bria API call plans
and executes them, chaining outputs between steps.
"""

from __future__ import annotations
import json
import re
import requests
from dataclasses import dataclass, field
from typing import Optional

# ─── Data models ─────────────────────────────────────────────────────────────

@dataclass
class AgentStep:
    service_name: str           # e.g. "lifestyle_shot_by_text"
    params: dict = field(default_factory=dict)
    use_previous_output: bool = False  # if True, previous URL → this step's image_data


@dataclass
class AgentPlan:
    steps: list[AgentStep]
    original_request: str


# ─── Known services the agent can choose from ────────────────────────────────

KNOWN_SERVICES = [
    "generate_image",
    "lifestyle_shot_by_text",
    "lifestyle_shot_by_image",
    "add_shadow",
    "create_packshot",
    "generative_fill",
    "erase_foreground",
]

# ─── Ollama intent parser ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the planning module for an AI product-photography assistant called AdSnap Studio.
Given a user request, produce a JSON plan with the exact services to call (in order) and their parameters.

Available services:
- generate_image: params: prompt (str), num_results (int, default 1), aspect_ratio (str, default "1:1")
- lifestyle_shot_by_text: params: scene_description (str), num_results (int, default 4), placement_type (str, default "automatic"), fast (bool, default true)
- lifestyle_shot_by_image: params: num_results (int, default 4), placement_type (str, default "automatic")
- add_shadow: params: shadow_type ("natural" or "drop"), shadow_intensity (0-100, default 60), shadow_blur (0-50, default 15)
- create_packshot: params: background_color (hex, default "#FFFFFF"), force_rmbg (bool, default false)
- generative_fill: params: prompt (str), num_results (int, default 1)
- erase_foreground: params: (no extra params needed)

Rules:
- Use "use_previous_output": true when this step should use the image produced by the previous step.
- Only include services that are relevant to the request.
- Respond ONLY with valid JSON in this exact schema, no commentary:
{
  "steps": [
    {"service": "<service_name>", "params": {<param_key>: <param_value>}, "use_previous_output": false},
    ...
  ]
}
"""


def _call_ollama(user_text: str, model: str, ollama_url: str) -> Optional[dict]:
    """Call the local Ollama server and return parsed JSON plan, or None on failure."""
    try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            "stream": False,
            "format": "json",
        }
        resp = requests.post(
            f"{ollama_url.rstrip('/')}/api/chat",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        # Strip markdown code fences if present
        content = re.sub(r"```(?:json)?", "", content).strip("` \n")
        return json.loads(content)
    except Exception:
        return None


# ─── Rule-based keyword fallback ─────────────────────────────────────────────

_KEYWORD_RULES = [
    # (regex_pattern, service_name, extra_params_fn)
    (r"\b(packshot|white\s+background|product\s+shot)\b",
     "create_packshot", lambda _: {"background_color": "#FFFFFF"}),
    (r"\b(shadow|drop\s+shadow|natural\s+shadow)\b",
     "add_shadow", lambda t: {"shadow_type": "drop" if "drop" in t else "natural"}),
    (r"\b(lifestyle|scene|environment|background(?!\s+remov))\b",
     "lifestyle_shot_by_text",
     lambda t: {"scene_description": t, "num_results": 2, "fast": True}),
    (r"\b(generate|create|make|draw)\b",
     "generate_image", lambda t: {"prompt": t, "num_results": 1}),
    (r"\b(fill|inpaint|replace\s+area)\b",
     "generative_fill", lambda t: {"prompt": t}),
    (r"\b(erase|remove\s+foreground|remove\s+object)\b",
     "erase_foreground", lambda _: {}),
]


_QUESTION_PATTERNS = [
    r"^(how|what|where|why|when|who|which|can you|could you|do i|should i|is there|is it|are there|tell me|explain|help me understand)",
    r"\b(how (do|can|to)|what is|what are|where (is|can)|why (is|does)|how (should|would))\b",
    r"\?\s*$",  # ends with a question mark
    r"\b(api key|bira key|find.*key|get.*key|sign up|register|account|pricing|cost|free|documentation|docs)\b",
]


def is_question(text: str) -> bool:
    """Return True if the text looks like a conversational question rather than an image task."""
    t = text.strip().lower()
    for pattern in _QUESTION_PATTERNS:
        if re.search(pattern, t):
            return True
    return False


def _rule_based_parse(user_text: str, image_provided: bool) -> AgentPlan:
    """Simple keyword-matching fallback when Ollama is unavailable."""
    text_lower = user_text.lower()
    steps: list[AgentStep] = []

    for pattern, service, params_fn in _KEYWORD_RULES:
        if re.search(pattern, text_lower):
            params = params_fn(user_text)
            use_prev = bool(steps) and image_provided  # chain if we already have a step
            steps.append(AgentStep(service_name=service, params=params,
                                   use_previous_output=use_prev))

    # Default to lifestyle shot if nothing matched and an image is provided
    if not steps and image_provided:
        steps.append(AgentStep(
            service_name="lifestyle_shot_by_text",
            params={"scene_description": user_text, "num_results": 2, "fast": True},
            use_previous_output=False,
        ))
    elif not steps:
        # Nothing matched and no image — don't force a generate_image call
        # Return an empty plan so the caller treats it as a no-op / conversational
        pass

    return AgentPlan(steps=steps, original_request=user_text)


# ─── Public: parse_intent ─────────────────────────────────────────────────────

def parse_intent(
    user_text: str,
    image_provided: bool = False,
    preferences: dict | None = None,
    model: str = "llama3",
    ollama_url: str = "http://localhost:11434",
) -> tuple[Optional[AgentPlan], bool]:
    """
    Parse natural-language user request into an AgentPlan.

    Returns
    -------
    (plan, used_llm)
        plan     : AgentPlan ready to execute, or None if the message is
                   a conversational question (should get a text reply instead)
        used_llm : True if Ollama was used, False if rule-based fallback was used
    """
    preferences = preferences or {}

    # ① Detect conversational / informational questions — don't try to run image services
    if is_question(user_text):
        return None, False

    # ② Try Ollama first
    llm_data = _call_ollama(user_text, model, ollama_url)

    if llm_data and "steps" in llm_data:
        steps: list[AgentStep] = []
        for raw in llm_data["steps"]:
            svc = raw.get("service", "")
            if svc not in KNOWN_SERVICES:
                continue
            params = raw.get("params", {})
            # Merge stored preferences (only fill gaps, don't override)
            merged = {**preferences, **params}
            use_prev = raw.get("use_previous_output", False)
            steps.append(AgentStep(service_name=svc, params=merged,
                                   use_previous_output=use_prev))

        if steps:
            return AgentPlan(steps=steps, original_request=user_text), True

    # ③ Ollama failed / empty — fall back to rule-based
    plan = _rule_based_parse(user_text, image_provided)
    # Merge preferences into each step's params
    for step in plan.steps:
        step.params = {**preferences, **step.params}

    # If the rule-based parse also produced no steps, treat as conversational
    if not plan.steps:
        return None, False

    return plan, False


# ─── Public: execute_plan ─────────────────────────────────────────────────────

def _url_to_bytes(url: str) -> Optional[bytes]:
    """Download an image from a URL and return raw bytes."""
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.content
    except Exception:
        return None


def execute_plan(
    plan: AgentPlan,
    initial_image_data: Optional[bytes],
    api_key: str,
    progress_callback=None,  # optional callable(step_index, total, step_name)
) -> list[str]:
    """
    Execute an AgentPlan step by step.

    Parameters
    ----------
    plan               : AgentPlan from parse_intent()
    initial_image_data : raw bytes of the user-uploaded image (or None)
    api_key            : Bria API key
    progress_callback  : optional fn(step_index, total, step_name) for UI updates

    Returns
    -------
    List of result URLs produced across all steps.
    """
    # Lazy imports to avoid circular dependencies (services import from each other sometimes)
    from services.lifestyle_shot import lifestyle_shot_by_text, lifestyle_shot_by_image
    from services.shadow import add_shadow
    from services.packshot import create_packshot
    from services.generative_fill import generative_fill
    from services.hd_image_generation import generate_hd_image
    from services.erase_foreground import erase_foreground

    SERVICE_MAP = {
        "generate_image": generate_hd_image,
        "lifestyle_shot_by_text": lifestyle_shot_by_text,
        "lifestyle_shot_by_image": lifestyle_shot_by_image,
        "add_shadow": add_shadow,
        "create_packshot": create_packshot,
        "generative_fill": generative_fill,
        "erase_foreground": erase_foreground,
    }

    all_urls: list[str] = []
    previous_url: Optional[str] = None
    current_image_data = initial_image_data

    total = len(plan.steps)

    for i, step in enumerate(plan.steps):
        if progress_callback:
            progress_callback(i, total, step.service_name)

        # Chain: download previous step output to use as this step's input
        if step.use_previous_output and previous_url:
            chained_bytes = _url_to_bytes(previous_url)
            if chained_bytes:
                current_image_data = chained_bytes

        fn = SERVICE_MAP.get(step.service_name)
        if fn is None:
            continue

        params = dict(step.params)  # shallow copy
        result = None

        try:
            if step.service_name == "generate_image":
                result = fn(
                    prompt=params.get("prompt", ""),
                    api_key=api_key,
                    num_results=params.get("num_results", 1),
                    aspect_ratio=params.get("aspect_ratio", "1:1"),
                    sync=True,
                )
            elif step.service_name in ("lifestyle_shot_by_text",):
                result = fn(
                    api_key=api_key,
                    image_data=current_image_data,
                    scene_description=params.get("scene_description", ""),
                    placement_type=params.get("placement_type", "automatic"),
                    num_results=params.get("num_results", 2),
                    sync=True,
                    fast=params.get("fast", True),
                )
            elif step.service_name == "lifestyle_shot_by_image":
                result = fn(
                    api_key=api_key,
                    image_data=current_image_data,
                    reference_image=params.get("reference_image", current_image_data),
                    placement_type=params.get("placement_type", "automatic"),
                    num_results=params.get("num_results", 2),
                    sync=True,
                )
            elif step.service_name == "add_shadow":
                result = fn(
                    api_key=api_key,
                    image_data=current_image_data,
                    shadow_type=params.get("shadow_type", "natural"),
                    shadow_intensity=params.get("shadow_intensity", 60),
                    shadow_blur=params.get("shadow_blur", 15),
                    shadow_offset=params.get("shadow_offset", [0, 15]),
                )
            elif step.service_name == "create_packshot":
                result = fn(
                    api_key=api_key,
                    image_data=current_image_data,
                    background_color=params.get("background_color", "#FFFFFF"),
                    force_rmbg=params.get("force_rmbg", False),
                )
            elif step.service_name == "generative_fill":
                result = fn(
                    api_key=api_key,
                    image_data=current_image_data,
                    mask_data=params.get("mask_data", b""),
                    prompt=params.get("prompt", ""),
                    num_results=params.get("num_results", 1),
                    sync=True,
                )
            elif step.service_name == "erase_foreground":
                result = fn(
                    api_key=api_key,
                    image_data=current_image_data,
                )
        except Exception:
            continue

        # Extract URL(s) from result
        step_urls = _extract_urls(result)
        all_urls.extend(step_urls)
        if step_urls:
            previous_url = step_urls[0]

    return all_urls


def _extract_urls(result) -> list[str]:
    """Robustly extract image URL(s) from various Bria API response shapes."""
    if not result:
        return []
    if isinstance(result, str) and result.startswith("http"):
        return [result]
    if isinstance(result, list):
        urls = []
        for item in result:
            urls.extend(_extract_urls(item))
        return urls
    if isinstance(result, dict):
        # Common keys, in priority order
        for key in ("result_url", "url"):
            if key in result and isinstance(result[key], str):
                return [result[key]]
        for key in ("result_urls", "urls"):
            if key in result and isinstance(result[key], list):
                return [u for u in result[key] if isinstance(u, str)]
        if "result" in result:
            return _extract_urls(result["result"])
    return []
