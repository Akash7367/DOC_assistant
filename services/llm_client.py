# services/llm_client.py
import os
import requests
from typing import Optional, List

# Use v1beta for now (you tested with v1beta earlier). We'll call ListModels on both if needed.
LIST_MODELS_V1BETA = "https://generativelanguage.googleapis.com/v1beta/models"
LIST_MODELS_V1 = "https://generativelanguage.googleapis.com/v1/models"
BASE_V1 = "https://generativelanguage.googleapis.com/v1"
BASE_V1BETA = "https://generativelanguage.googleapis.com/v1beta"

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, prefer_model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")

        # Optionally let user prefer a model (GEMINI_MODEL in .env)
        self.prefer_model = prefer_model or os.environ.get("GEMINI_MODEL")
        self.headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}

        # caching chosen model to avoid repeated ListModels calls in same process
        self._chosen_generate_model = None
        self._chosen_base = None

    def _call_list_models(self, url: str):
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            return r.status_code, r.text, r.json() if r.status_code == 200 else None
        except Exception as e:
            return None, str(e), None

    def _list_all_models(self) -> List[dict]:
        """Return combined model lists from v1beta and v1 (if available)."""
        models = []

        for url in (LIST_MODELS_V1BETA, LIST_MODELS_V1):
            status, text, js = self._call_list_models(url)
            if status == 200 and js:
                # JS expected to have "models" list
                for m in js.get("models", []):
                    # annotate with which endpoint returned it
                    m["_source_list_url"] = url
                    models.append(m)
        return models

    def _choose_model_from_list(self, models: List[dict]) -> Optional[tuple]:
        """
        Choose a model that supports generateContent.
        Returns tuple (model_name, base_url_prefix) where model_name is like 'models/xyz'
        and base_url_prefix is the base (v1 or v1beta) to use for generateContent.
        """
        # prefer explicit GEMINI_MODEL if available in the list
        if self.prefer_model:
            for m in models:
                name = m.get("name", "")
                # allow prefer_model either as 'models/...' or bare name
                if self.prefer_model == name or self.prefer_model == name.replace("models/", ""):
                    # check supportedMethods if present and accept if generateContent present or absent (best-effort)
                    return name, (BASE_V1 if LIST_MODELS_V1 in m.get("_source_list_url", "") else BASE_V1BETA)

        # First, try to find any model that declares support for generateContent
        for m in models:
            name = m.get("name")
            if not name:
                continue
            supported = m.get("supportedMethods") or m.get("features") or []
            # supportedMethods may be a list of strings like ["generateContent", ...]
            if any("generateContent" in str(s).lower() for s in supported):
                base = BASE_V1 if LIST_MODELS_V1 in m.get("_source_list_url", "") else BASE_V1BETA
                return name, base

        # Second: prefer models that contain 'gemini' in the name (best-effort)
        for m in models:
            name = m.get("name", "")
            if "gemini" in name.lower():
                base = BASE_V1 if LIST_MODELS_V1 in m.get("_source_list_url", "") else BASE_V1BETA
                return name, base

        # Third: pick any model that looks like 'models/...'
        for m in models:
            name = m.get("name")
            if name and name.startswith("models/"):
                base = BASE_V1 if LIST_MODELS_V1 in m.get("_source_list_url", "") else BASE_V1BETA
                return name, base

        return None

    def _build_generate_url(self, model_name: str, base: str) -> str:
        """
        Ensure full generate URL: {base}/{model_name}:generateContent
        model_name may already be 'models/...' or just 'xyz', handle both.
        """
        if not model_name:
            raise ValueError("empty model_name")
        if model_name.startswith("models/"):
            model_path = model_name
        else:
            model_path = f"models/{model_name}"
        return f"{base}/{model_path}:generateContent"

    def _ensure_chosen_model(self):
        """Ensure we have a chosen model (cached). Returns (generate_url, model_name)."""
        if self._chosen_generate_model and self._chosen_base:
            return self._build_generate_url(self._chosen_generate_model, self._chosen_base), self._chosen_generate_model

        models = self._list_all_models()
        if not models:
            raise RuntimeError("Unable to list models. Check API key, permissions, or network. ListModels returned nothing.")

        chosen = self._choose_model_from_list(models)
        if not chosen:
            raise RuntimeError(f"No suitable model discovered from ListModels. Raw models count: {len(models)}. Sample: {models[:5]}")

        model_name, base = chosen
        self._chosen_generate_model = model_name
        self._chosen_base = base
        return self._build_generate_url(model_name, base), model_name

    def complete(self, prompt: str, max_tokens: int = 512) -> str:
        """
        Auto-discovers a model that supports generateContent and calls it.
        Returns text or raises a helpful exception string.
        """
        try:
            generate_url, model_name = self._ensure_chosen_model()
        except Exception as e:
            return f"Error discovering model: {e}"

        body = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        try:
            r = requests.post(generate_url, json=body, headers=self.headers, timeout=30)
        except Exception as e:
            return f"Request error calling {model_name}: {e}"

        # handle quota / permission / not found clearly
        if r.status_code != 200:
            # If quota error, return full message (user saw this earlier)
            return f"{r.status_code} for model {model_name}: {r.text}"

        try:
            data = r.json()
            cand = (data.get("candidates") or [None])[0]
            if cand:
                # typical shape: candidates[0].content.parts[0].text
                content = cand.get("content") or {}
                parts = content.get("parts") or []
                if parts and isinstance(parts, list) and len(parts) > 0:
                    return parts[0].get("text", "")
                # fallback fields
                return cand.get("output") or cand.get("text") or str(data)
            return str(data)
        except Exception as e:
            return f"Failed to parse response from {model_name}: {e} -- raw: {r.text}"
