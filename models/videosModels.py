from pydantic import BaseModel 
from typing import Optional


class Video(BaseModel):
        idVideo: Optional[str] = None
        nombreVideo: str
        url: Optional[str]
        anomalia: bool
