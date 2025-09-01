from typing import Optional, List, Any
from pydantic import BaseModel

class QueryResponse(BaseModel):
    answer: str
    sql_query: Optional[str] = None
    results: Optional[dict[str, list[Any]]] = None