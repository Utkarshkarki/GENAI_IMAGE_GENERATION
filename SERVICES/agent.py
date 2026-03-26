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


# ─── App context for conversational QA ───────────────────────────────────────

APP_QA_SYSTEM_PROMPT = """You are a helpful assistant embedded inside AdSnap Studio, an AI product-photography web app.

=== APP OVERVIEW ===
AdSnap Studio uses the Bria AI API to generate and edit product images. It runs locally as a Streamlit web app.

=== TABS ===
1. 🎨 Generate Image — Generate images from a text prompt. Options: number of images, aspect ratio, style (Realistic, Artistic, Cartoon, etc.), Enhance Image quality toggle.
2. 🖼️ Lifestyle Shot — Upload a product image and place it into a custom scene using either a text description or a reference image. Supports placement types: Original, Automatic, Manual Placement, Manual Padding, Custom Coordinates.
3. 🎨 Generative Fill — Upload an image, draw a mask over an area, and describe what to generate there.
4. 🎨 Erase Elements — Upload an image, draw over what you want removed, and the AI erases it cleanly.
5. 🤖 AI Agent — The intelligent tab. Type what you want in plain English (e.g. "put this product on a white background with a drop shadow") and the agent automatically plans and runs the right Bria API steps in sequence.

=== AI AGENT TAB DETAILS ===
- Quick Presets: Three one-click workflow buttons:
  • 🛍️ Amazon Ready = create_packshot (white background) → add_shadow (natural)
  • 📱 Social Media Kit = lifestyle_shot_by_text with 4 placements
  • 🎯 Ad Creative = lifestyle_shot_by_text with coffee shop scene
- Product Image uploader: Optional. Required for lifestyle shot, packshot, shadow, erase. Not needed for generate_image.
- Chat input: Type any image request in plain English.
- Plan Preview: Before running, the agent shows the planned steps in an expandable section. User clicks "✅ Confirm & Run" to execute.
- Results appear inline in the chat. All results are automatically saved to the Session Gallery at the bottom.

=== SIDEBAR SETTINGS ===
- Enter your API key: The Bria API key (password field). Get it from bria.ai → dashboard → API Keys.
- 🤖 AI Agent — Ollama section:
  • Ollama Model dropdown: llama3 (default), mistral, phi3, gemma3. To change: click the dropdown and select a model.
  • Ollama URL: default is http://localhost:11434. Change only if Ollama runs on a different port/machine.
- 🧠 Agent Memory: Shows preferences the agent has remembered (e.g. background_color). Can delete individual items or clear all.

=== OLLAMA (LOCAL LLM) ===
Ollama is used ONLY for intent parsing in the AI Agent tab. It is NOT needed for the other tabs.
- Install from ollama.com, then run: ollama pull llama3 (or mistral, phi3, gemma3)
- To switch model: use the Ollama Model dropdown in the sidebar.
- If Ollama is not running, the agent falls back to keyword-based planning automatically.

=== SESSION GALLERY ===
Every generated image is automatically saved to the Session Gallery at the bottom of the page. Images can be downloaded individually. The gallery can be cleared with the 🗑️ Clear button.

=== HOW TO GET THE BRIA API KEY ===
1. Go to bria.ai and sign up or log in.
2. Go to your dashboard → API Keys section.
3. Copy the key and paste it into the "Enter your API key" box in the sidebar.
The key is only stored in your browser session — never saved to disk.

=== RULES FOR YOUR ANSWERS ===
- Answer based only on the app context above.
- Be concise and helpful. Use markdown formatting.
- If the user's question is a follow-up, use the conversation history to understand context.
- If you don't know something, say so honestly.
- Never make up features that don't exist in the app.
"""


def answer_question(
    user_text: str,
    history: list[dict],
    model: str = "llama3",
    ollama_url: str = "http://localhost:11434",
) -> str:
    """
    Answer a conversational/informational question about the app using Ollama.
    Injects the full app context and recent conversation history.

    Parameters
    ----------
    user_text : the user's current question
    history   : list of {role, content} dicts from agent_history
    model     : Ollama model name
    ollama_url: Ollama server URL

    Returns
    -------
    A markdown-formatted string answer. Falls back to a short message if Ollama is offline.
    """
    # Build messages: system prompt + last 10 turns of history + current question
    messages = [{"role": "system", "content": APP_QA_SYSTEM_PROMPT}]
    for turn in history[-10:]:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_text})

    try:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        resp = requests.post(
            f"{ollama_url.rstrip('/')}/api/chat",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        answer = data.get("message", {}).get("content", "").strip()
        if answer:
            return answer
    except Exception:
        pass

    # Fallback when Ollama is offline
    return (
        "⚠️ Ollama is not running, so I can't answer questions in detail right now.\n\n"
        "**Quick help:**\n"
        "- **API key** → get it from [bria.ai](https://bria.ai) → dashboard → API Keys → paste in the sidebar\n"
        "- **Change Ollama model** → use the *Ollama Model* dropdown in the sidebar\n"
        "- **Image tasks** → type what you want (e.g. *'white background packshot'*) and I'll plan the steps\n\n"
        "To enable full conversational answers, start Ollama: `ollama serve`"
    )




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
