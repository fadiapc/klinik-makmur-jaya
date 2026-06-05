from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SettingBase(BaseModel):
    value: str

class SettingUpdate(SettingBase):
    pass

class SettingResponse(SettingBase):
    key: str
    description: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SettingListUpdate(BaseModel):
    settings: dict[str, str]
