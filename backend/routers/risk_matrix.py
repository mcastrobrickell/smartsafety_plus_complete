"""SmartSafety+ - Risk Matrix Router"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from config import db
from models.schemas import RiskMatrix, Risk
from utils.auth import get_current_user
from utils.pagination import paginated_find
from datetime import datetime, timezone

router = APIRouter(tags=["risk-matrix"])

@router.get("/risk-matrix")
async def get_risk_matrices(current_user: dict = Depends(get_current_user)):
    return await paginated_find(db.risk_matrices, sort_field="created_at", page=1, page_size=100)

@router.get("/risk-matrix/{matrix_id}")
async def get_risk_matrix(matrix_id: str, current_user: dict = Depends(get_current_user)):
    matrix = await db.risk_matrices.find_one({"id": matrix_id}, {"_id": 0})
    if not matrix:
        raise HTTPException(status_code=404, detail="Matrix not found")
    return matrix

@router.post("/risk-matrix")
async def create_risk_matrix(
    name: str,
    area: str,
    process: str,
    description: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    matrix = RiskMatrix(
        name=name,
        description=description,
        area=area,
        process=process,
        created_by=current_user["name"]
    )
    await db.risk_matrices.insert_one(matrix.model_dump())
    return matrix

@router.post("/risk-matrix/{matrix_id}/risks")
async def add_risk_to_matrix(matrix_id: str, risk: Risk, current_user: dict = Depends(get_current_user)):
    risk_dict = risk.model_dump()
    risk_dict["risk_level"] = risk.probability * risk.severity
    
    result = await db.risk_matrices.update_one(
        {"id": matrix_id},
        {
            "$push": {"risks": risk_dict},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Matrix not found")
    return {"message": "Risk added", "risk": risk_dict}

@router.put("/risk-matrix/{matrix_id}/risks/{risk_id}")
async def update_risk_in_matrix(matrix_id: str, risk_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    if "probability" in updates and "severity" in updates:
        updates["risk_level"] = updates["probability"] * updates["severity"]
    
    result = await db.risk_matrices.update_one(
        {"id": matrix_id, "risks.id": risk_id},
        {
            "$set": {f"risks.$.{k}": v for k, v in updates.items()},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Matrix or risk not found")
    return {"message": "Risk updated"}

@router.delete("/risk-matrix/{matrix_id}/risks/{risk_id}")
async def delete_risk_from_matrix(matrix_id: str, risk_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.risk_matrices.update_one(
        {"id": matrix_id},
        {
            "$pull": {"risks": {"id": risk_id}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Matrix not found")
    return {"message": "Risk deleted"}

@router.put("/risk-matrix/{matrix_id}/status")
async def update_matrix_status(matrix_id: str, status: str, current_user: dict = Depends(get_current_user)):
    result = await db.risk_matrices.update_one(
        {"id": matrix_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Matrix not found")
    return {"message": "Status updated"}

