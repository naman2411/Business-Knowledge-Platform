# app/services/llm_providers.py
import os, json, requests
# ---- Ollama ----
class OllamaProvider:
    def __init__(self, url=None, model=None):
        self.url = url or os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.model = model or os.getenv("LLM_MODEL", "llama3.1:8b")
        # Force generate endpoint if desired: set OLLAMA_USE_GENERATE=1
        self.use_generate = str(os.getenv("OLLAMA_USE_GENERATE", "")).lower() in ("1","true","yes")
    def _compose_prompt(self, messages):
        sys = next((m["content"] for m in messages if m.get("role") == "system"), None)
        users = [m["content"] for m in messages if m.get("role") == "user"]
        prompt = ""
        if sys: prompt += sys.strip() + "\n\n"
        prompt += "\n\n".join(u.strip() for u in users)
        return prompt
    def stream(self, prompt, system=None, timeout=120):
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        if not self.use_generate:
            r = requests.post(
                f"{self.url}/api/chat",
                json={"model": self.model, "messages": msgs, "stream": True},
                stream=True, timeout=timeout,
            )
            if r.status_code == 404:
                self.use_generate = True  # fall back
            else:
                r.raise_for_status()
                for line in r.iter_lines(decode_unicode=True):
                    if not line: continue
                    data = json.loads(line)
                    delta = (data.get("message") or {}).get("content", "")
                    if delta: yield delta
                return
        # /api/generate (stream)
        gen_prompt = self._compose_prompt(msgs)
        r = requests.post(
            f"{self.url}/api/generate",
            json={"model": self.model, "prompt": gen_prompt, "stream": True},
            stream=True, timeout=timeout,
        )
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if not line: continue
            data = json.loads(line)
            delta = data.get("response", "")
            if delta: yield delta
    def complete(self, prompt, system=None, timeout=120):
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        if not self.use_generate:
            r = requests.post(
                f"{self.url}/api/chat",
                json={"model": self.model, "messages": msgs, "stream": False},
                timeout=timeout,
            )
            if r.status_code == 404:
                self.use_generate = True
            else:
                r.raise_for_status()
                data = r.json()
                return (data.get("message") or {}).get("content", "")
        # /api/generate (non-stream)
        gen_prompt = self._compose_prompt(msgs)
        r = requests.post(
            f"{self.url}/api/generate",
            json={"model": self.model, "prompt": gen_prompt, "stream": False},
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("response", "")
# ---- OpenAI (optional primary) ----
class OpenAIProvider:
    def __init__(self, model=None):
        self.model = model or os.getenv("OPENAI_MODEL", "o4-mini")
        from openai import OpenAI  # import here to avoid hard dep at import time
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    def complete(self, prompt, system=None):
        if system:
            input_payload = [
                {"role": "system", "content": [{"type":"text","text": system}]},
                {"role": "user",   "content": [{"type":"text","text": prompt}]},
            ]
        else:
            input_payload = prompt
        resp = self.client.responses.create(model=self.model, input=input_payload)
        parts = getattr(resp, "output", []) or []
        for p in parts:
            for c in getattr(p, "content", []) or []:
                if getattr(c, "type", "") == "output_text":
                    return c.text
        return getattr(resp, "output_text", "")
