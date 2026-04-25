"""Minimal Gemini client wrapper (google-genai SDK).

Three modes:
  - text(...) : free-form text response
  - structured(...) : JSON conforming to a Pydantic model (response_schema)
  - grounded_search(...) : Google Search grounding tool, returns text
"""
import json
import os
from typing import Type, TypeVar
from dotenv import load_dotenv
from google import genai
from google.genai import types as gtypes
from pydantic import BaseModel, ValidationError

load_dotenv()
_API_KEY = os.environ.get("GOOGLE_API_KEY")
_client: genai.Client | None = genai.Client(api_key=_API_KEY) if _API_KEY else None

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiError(RuntimeError):
    pass


def _require_client() -> genai.Client:
    if _client is None:
        raise GeminiError("GOOGLE_API_KEY not configured")
    return _client


def text(prompt: str, system: str | None = None, model: str = DEFAULT_MODEL) -> str:
    client = _require_client()
    cfg = gtypes.GenerateContentConfig(system_instruction=system) if system else None
    resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
    return resp.text


def _structured_once(client, prompt: str, schema: Type[T], system: str | None, model: str) -> T:
    try:
        cfg = gtypes.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=schema,
        )
        resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
        parsed = resp.parsed
        if isinstance(parsed, schema):
            return parsed
        raw = resp.text or ""
    except Exception:
        cfg = gtypes.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
        )
        resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
        raw = resp.text or ""

    raw = raw.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise GeminiError(f"Gemini returned non-JSON: {raw[:500]}") from e
    try:
        return schema(**data)
    except ValidationError as e:
        raise GeminiError(f"Gemini JSON failed schema validation: {e}\nRaw: {raw[:500]}") from e


def structured(prompt: str, schema: Type[T], system: str | None = None, model: str = DEFAULT_MODEL) -> T:
    """Send prompt expecting JSON matching the given Pydantic schema. Retries
    once on parse/schema errors since Gemini occasionally streams garbled JSON."""
    client = _require_client()
    try:
        return _structured_once(client, prompt, schema, system, model)
    except GeminiError:
        return _structured_once(client, prompt, schema, system, model)


def grounded_search(prompt: str, system: str | None = None, model: str = DEFAULT_MODEL) -> str:
    """Use Google Search grounding tool. Returns raw text response."""
    client = _require_client()
    cfg = gtypes.GenerateContentConfig(
        system_instruction=system,
        tools=[gtypes.Tool(google_search=gtypes.GoogleSearch())],
    )
    resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
    return resp.text
