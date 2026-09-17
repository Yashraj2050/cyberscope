import json
from pathlib import Path
from typing import Dict, Any

class LocalKnowledgeRetriever:
    def __init__(self, knowledge_dir: Path = None):
        if knowledge_dir is None:
            knowledge_dir = Path(__file__).parent.parent / "knowledge"
        self.transitions_path = knowledge_dir / "transitions.json"
        self._transitions_cache = None

    def _load_transitions(self) -> Dict[str, Any]:
        if self._transitions_cache is None:
            if self.transitions_path.exists():
                with open(self.transitions_path, "r", encoding="utf-8") as f:
                    self._transitions_cache = json.load(f)
            else:
                self._transitions_cache = {}
        return self._transitions_cache

    def get_knowledge_context(self, preceding_event: Dict[str, Any], following_event: Dict[str, Any]) -> str:
        """
        Retrieves local knowledge specific to the transition between two events.
        Does NOT make external HTTP requests.
        """
        transitions = self._load_transitions()
        if not transitions:
            return "No local knowledge base available."

        context_snippets = []
        
        preceding_type = preceding_event.get("event_type", "Unknown") if preceding_event else "None"
        following_type = following_event.get("event_type", "Unknown") if following_event else "None"
        
        transition_key = f"{preceding_type}->{following_type}"
        
        if transition_key in transitions:
            t_data = transitions[transition_key]
            context_snippets.append(f"Transition Knowledge ({transition_key}): {t_data.get('description', '')}")
            if "typical_gaps" in t_data:
                context_snippets.append(f"Typical Missing Events: {', '.join(t_data['typical_gaps'])}")
        else:
            context_snippets.append(f"No specific local knowledge found for transition {transition_key}.")

        return "\n".join(context_snippets)
