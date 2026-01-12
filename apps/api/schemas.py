from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    source: str = "upload"
    timestamp: str
    file_type: str = "text"
    file_name: Optional[str] = None


class DocumentEntities(BaseModel):
    people: List[str] = Field(default_factory=list)
    orgs: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)


class DocumentSection(BaseModel):
    chunk_id: str
    index: int
    label: str
    text: str


class NormalizedFields(BaseModel):
    raw_id: int
    section_count: int
    char_count: int


class DocumentSchema(BaseModel):
    metadata: DocumentMetadata
    entities: DocumentEntities
    sections: List[DocumentSection]
    normalized_fields: NormalizedFields
    raw_payload: Dict[str, Any]
    processed_at: Optional[str] = None
