import networkx as nx
from typing import List, Dict, Any
from models import CyberEvent

class AttackGraphEngine:
    def __init__(self):
        self.graph = nx.DiGraph()

    def build(self, events: List[CyberEvent]):
        for event in events:
            self.add_event(event)

    def add_event(self, event: CyberEvent):
        # 1. Add Event Node
        self.graph.add_node(event.event_id, type="EVENT", label=event.event_type)

        # 2. Add Host Node and connects to Event
        self.graph.add_node(event.host_id, type="HOST", label=event.host_id)
        self.graph.add_edge(event.host_id, event.event_id, relationship="generates")

        # 3. Add Process Node
        if event.process_id:
            # Prefix process ID to make it unique across hosts if needed, but for prototype keep it simple
            self.graph.add_node(event.process_id, type="PROCESS", label=event.process_name or event.process_id)
            self.graph.add_edge(event.process_id, event.host_id, relationship="runs_on")

        # 4. Add User Node
        if event.user_id:
            self.graph.add_node(event.user_id, type="USER", label=event.user_id)
            if event.process_id:
                self.graph.add_edge(event.user_id, event.process_id, relationship="executes")

        # 5. Add Technique Node
        if event.technique_id:
            tech_label = f"{event.technique_id}: {event.technique_name}" if event.technique_name else event.technique_id
            self.graph.add_node(event.technique_id, type="TECHNIQUE", label=tech_label)
            self.graph.add_edge(event.event_id, event.technique_id, relationship="maps_to")
            
        # 6. Add parent process relationships if exists
        if event.parent_process_id and event.process_id:
            self.graph.add_node(event.parent_process_id, type="PROCESS", label=event.parent_process_id)
            self.graph.add_edge(event.parent_process_id, event.process_id, relationship="spawns")
            
        # 7. Add Network Destination
        if event.destination_host:
            self.graph.add_node(event.destination_host, type="HOST", label=event.destination_host)
            self.graph.add_edge(event.event_id, event.destination_host, relationship="connects_to")

    def get_nodes(self) -> List[Dict[str, Any]]:
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "type": data.get("type", "UNKNOWN"),
                "label": data.get("label", str(node_id))
            })
        return nodes

    def get_edges(self) -> List[Dict[str, Any]]:
        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "relationship": data.get("relationship", "unknown")
            })
        return edges

    def get_neighbors(self, node_id: str) -> List[str]:
        if self.graph.has_node(node_id):
            return list(self.graph.neighbors(node_id))
        return []

    def serialize(self) -> Dict[str, Any]:
        return {
            "nodes": self.get_nodes(),
            "edges": self.get_edges()
        }
