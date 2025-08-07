from pydantic import BaseModel
from typing import List, Dict, Any
from .response import StandardResponse

class KnowledgeGraphNodeData(BaseModel):
    id: str
    label: str

class KnowledgeGraphNode(BaseModel):
    data: KnowledgeGraphNodeData

class KnowledgeGraphEdgeData(BaseModel):
    source: str
    target: str

class KnowledgeGraphEdge(BaseModel):
    data: KnowledgeGraphEdgeData

class KnowledgeGraph(BaseModel):
    nodes: List[KnowledgeGraphNode]
    edges: List[KnowledgeGraphEdge]

KnowledgeGraphResponse = StandardResponse[KnowledgeGraph]