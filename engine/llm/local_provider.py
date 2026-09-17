from .base import LLMProvider
from .context import InvestigationLLMContext
from .parser import StructuredLLMResponse, parse_llm_response
from .prompts import build_prompt
from . import config
import os
import json
import hashlib
from pathlib import Path

class LocalLLMProvider(LLMProvider):
    def __init__(self):
        self.model_path = config.DEFAULT_MODEL_PATH
        self.model = None
        self.is_loaded = False
        self.last_error = None
        self.manifest = self._load_manifest()

    def _load_manifest(self):
        manifest_path = self.model_path.parent / "model_manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _verify_hash(self):
        expected_hash = self.manifest.get("sha256")
        if not expected_hash:
            return True # Not strictly enforced if missing in this phase, though we'd prefer it
        
        sha256_hash = hashlib.sha256()
        try:
            with open(self.model_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest() == expected_hash
        except Exception as e:
            self.last_error = f"Hash verification failed: {e}"
            return False

    def _load_model(self):
        if self.is_loaded:
            return
            
        if not self.model_path.exists():
            self.last_error = "Model file not found"
            return
            
        try:
            # We skip full hash verification here to speed up boot in dev, but in prod we'd check it.
            # Actually, per prompt: "verify model SHA-256 against an optional trusted manifest"
            # Since it's a 1.12 GB file, hashing takes a few seconds. We'll do it.
            if self.manifest and self.manifest.get("sha256"):
                if not self._verify_hash():
                    self.last_error = "Model SHA-256 mismatch"
                    return

            from llama_cpp import Llama
            self.model = Llama(model_path=str(self.model_path), n_ctx=2048, verbose=False)
            self.is_loaded = True
            self.last_error = None
        except ImportError:
            self.last_error = "llama_cpp not installed"
        except Exception as e:
            self.last_error = str(e)

    def generate(self, context: InvestigationLLMContext, instruction: str) -> StructuredLLMResponse:
        if not self.is_loaded:
            self._load_model()
            
        if not self.is_loaded:
            raise RuntimeError(f"LLM_UNAVAILABLE: {self.last_error}")
            
        prompt = build_prompt(context, instruction)
        prompt += "\n\nEnsure you output exactly in the requested JSON format."
        
        try:
            res = self.model(
                prompt,
                max_tokens=1024,
                temperature=0.0,
                stop=["```\n", "---"]
            )
            raw_text = res["choices"][0]["text"]
            parsed = parse_llm_response(raw_text)
            parsed.provider = "local"
            parsed.model_version = self.manifest.get("model_name", self.model_path.name)
            return parsed
        except Exception as e:
            raise RuntimeError(f"Local inference failed: {e}")

    def get_status(self) -> dict:
        return {
            "enabled": True,
            "available": self.model_path.exists(),
            "provider": "local",
            "model_id": self.manifest.get("model_id", "unknown"),
            "model_name": self.manifest.get("model_name", self.model_path.name),
            "model_hash": self.manifest.get("sha256", "unknown"),
            "runtime": "llama.cpp",
            "backend": "metal/cpu",
            "hardware_capability": "M1 8GB",
            "estimated_memory_requirement": "1.5 GB",
            "model_loaded": self.is_loaded,
            "offline": True,
            "last_error": self.last_error,
            "validation_status": self.manifest.get("validated", False)
        }
