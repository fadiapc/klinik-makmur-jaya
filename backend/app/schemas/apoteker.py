from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class StockBatchCreate(BaseModel):
    product_id: int = Field(..., description="ID of the product")
    batch_number: str = Field(..., min_length=1, max_length=100, description="Batch number from supplier")
    quantity: int = Field(..., gt=0, description="Number of units received")
    purchase_price: float = Field(..., ge=0, description="Purchase price per unit")
    expiry_date: Optional[date] = Field(None, description="Expiration date of the batch")

class StockBatchResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    batch_number: str
    quantity: int
    purchase_price: float
    expiry_date: Optional[date]
    received_at: str

    model_config = {"from_attributes": True}
