"""
SmartSafety+ - EPP Management Router
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timezone
import pandas as pd
import io

from config import db
from models.schemas import EPPItem, EPPStock, EPPMovement, EPPDelivery
from utils.auth import get_current_user
from utils.pdf import SafetyPDF

router = APIRouter(prefix="/epp", tags=["EPP Management"])


# ================== EPP ITEMS ==================

@router.get("/items")
async def get_epp_items(current_user: dict = Depends(get_current_user)):
    items = await db.epp_items.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return items


@router.post("/items")
async def create_epp_item(item: EPPItem, current_user: dict = Depends(get_current_user)):
    existing = await db.epp_items.find_one({"code": item.code})
    if existing:
        raise HTTPException(status_code=400, detail="Item code already exists")
    
    await db.epp_items.insert_one(item.model_dump())
    return item


@router.delete("/items/{item_id}")
async def delete_epp_item(item_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.epp_items.update_one(
        {"id": item_id},
        {"$set": {"is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "deleted"}


# ================== EPP STOCK ==================

@router.get("/stock")
async def get_epp_stock(current_user: dict = Depends(get_current_user)):
    stock = await db.epp_stock.find({}, {"_id": 0}).to_list(1000)
    return stock


@router.get("/stock/inventory")
async def get_stock_inventory(current_user: dict = Depends(get_current_user)):
    """Get consolidated inventory view"""
    items = await db.epp_items.find({"is_active": True}, {"_id": 0}).to_list(1000)
    stock_records = await db.epp_stock.find({}, {"_id": 0}).to_list(1000)
    
    inventory = []
    for item in items:
        item_stocks = [s for s in stock_records if s.get("epp_item_id") == item["id"]]
        total_stock = sum(s.get("quantity", 0) for s in item_stocks)
        min_stock = item_stocks[0].get("min_stock", 10) if item_stocks else 10
        
        inventory.append({
            "id": item["id"],
            "code": item.get("code", ""),
            "name": item.get("name", ""),
            "unit": item.get("unit", "unidad"),
            "unit_cost": item.get("unit_cost", 0),
            "current_stock": total_stock,
            "min_stock": min_stock,
            "stock_value": total_stock * item.get("unit_cost", 0),
            "status": "low" if total_stock < min_stock else "ok"
        })
    
    return inventory


@router.post("/stock/adjust")
async def adjust_stock(
    epp_item_id: str,
    new_stock: int,
    reason: str,
    current_user: dict = Depends(get_current_user)
):
    """Adjust stock quantity manually"""
    stock = await db.epp_stock.find_one({"epp_item_id": epp_item_id})
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock record not found")
    
    old_quantity = stock.get("quantity", 0)
    adjustment = new_stock - old_quantity
    
    # Update stock
    await db.epp_stock.update_one(
        {"id": stock["id"]},
        {"$set": {
            "quantity": new_stock,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Get item info
    item = await db.epp_items.find_one({"id": epp_item_id}, {"_id": 0})
    
    # Record adjustment movement
    movement = EPPMovement(
        epp_item_id=epp_item_id,
        epp_item_name=item.get("name", "") if item else "",
        epp_item_code=item.get("code", "") if item else "",
        movement_type="adjustment",
        quantity=adjustment,
        unit_cost=0,
        total_cost=0,
        notes=f"Ajuste manual: {reason}. Anterior: {old_quantity}, Nuevo: {new_stock}",
        created_by=current_user["name"]
    )
    await db.epp_movements.insert_one(movement.model_dump())
    
    return {
        "status": "adjusted",
        "old_quantity": old_quantity,
        "new_quantity": new_stock,
        "adjustment": adjustment
    }


# ================== EPP MOVEMENTS ==================

@router.get("/movements")
async def get_epp_movements(
    movement_type: Optional[str] = None,
    cost_center_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if movement_type:
        query["movement_type"] = movement_type
    if cost_center_id:
        query["$or"] = [
            {"from_cost_center_id": cost_center_id},
            {"to_cost_center_id": cost_center_id}
        ]
    movements = await db.epp_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich movements with item names if missing
    items_cache = {}
    for movement in movements:
        if not movement.get("epp_item_name"):
            item_id = movement.get("epp_item_id")
            if item_id not in items_cache:
                item = await db.epp_items.find_one({"id": item_id}, {"_id": 0})
                items_cache[item_id] = item
            item = items_cache.get(item_id)
            if item:
                movement["epp_item_name"] = item.get("name", "")
                movement["epp_item_code"] = item.get("code", "")
    
    return movements


@router.post("/movements/reception")
async def create_reception(
    epp_item_id: str,
    quantity: int,
    unit_cost: float,
    cost_center_id: str,
    warehouse_location: str,
    document_number: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Reception of EPP into warehouse"""
    item = await db.epp_items.find_one({"id": epp_item_id}, {"_id": 0})
    item_name = item.get("name", "N/A") if item else "N/A"
    item_code = item.get("code", "") if item else ""
    
    movement = EPPMovement(
        epp_item_id=epp_item_id,
        epp_item_name=item_name,
        epp_item_code=item_code,
        movement_type="reception",
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
        to_cost_center_id=cost_center_id,
        warehouse_location=warehouse_location,
        document_number=document_number,
        notes=notes,
        created_by=current_user["name"]
    )
    await db.epp_movements.insert_one(movement.model_dump())
    
    # Update or create stock
    existing_stock = await db.epp_stock.find_one({
        "epp_item_id": epp_item_id,
        "cost_center_id": cost_center_id,
        "warehouse_location": warehouse_location
    })
    
    if existing_stock:
        await db.epp_stock.update_one(
            {"id": existing_stock["id"]},
            {"$inc": {"quantity": quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        stock = EPPStock(
            epp_item_id=epp_item_id,
            cost_center_id=cost_center_id,
            warehouse_location=warehouse_location,
            quantity=quantity
        )
        await db.epp_stock.insert_one(stock.model_dump())
    
    return movement


# ================== EPP DELIVERIES ==================

@router.get("/deliveries")
async def get_epp_deliveries(current_user: dict = Depends(get_current_user)):
    deliveries = await db.epp_deliveries.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return deliveries


@router.post("/deliveries/create")
async def create_epp_delivery(delivery: EPPDelivery, current_user: dict = Depends(get_current_user)):
    delivery.created_by = current_user["name"]
    
    if not delivery.delivery_number:
        count = await db.epp_deliveries.count_documents({})
        delivery.delivery_number = f"ENT-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
    
    await db.epp_deliveries.insert_one(delivery.model_dump())
    return delivery


@router.get("/delivery/{delivery_id}/pdf")
async def export_single_delivery_pdf(
    delivery_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Export single delivery as PDF document"""
    delivery = await db.epp_deliveries.find_one({"id": delivery_id}, {"_id": 0})
    if not delivery:
        raise HTTPException(status_code=404, detail="Entrega no encontrada")
    
    pdf = SafetyPDF(
        title="Comprobante de Entrega de EPP",
        org_name="SmartSafety+ Enterprise"
    )
    pdf.add_page()
    
    # Delivery info
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, f"N Entrega: {delivery.get('delivery_number', delivery.get('id', '')[:8])}", ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.ln(5)
    
    # Delivery details
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(10, pdf.get_y(), 190, 50, 'F')
    y = pdf.get_y() + 5
    
    pdf.set_xy(15, y)
    pdf.cell(90, 5, f"Fecha: {delivery.get('date', 'N/A')}")
    pdf.cell(90, 5, f"Hora: {delivery.get('time', 'N/A')}", ln=True)
    
    pdf.set_xy(15, pdf.get_y() + 2)
    pdf.cell(90, 5, f"Tipo: {delivery.get('delivery_type', 'Entrega').upper()}")
    pdf.cell(90, 5, f"Centro de Costo: {delivery.get('cost_center_name', 'N/A')}", ln=True)
    
    pdf.ln(15)
    
    # Responsible
    pdf.section_title("Responsable de Entrega")
    pdf.add_field("Nombre", delivery.get('responsible_name'))
    pdf.add_field("RUT", delivery.get('responsible_rut'))
    pdf.add_field("Cargo", delivery.get('responsible_position'))
    pdf.ln(5)
    
    # Worker
    pdf.section_title("Trabajador Receptor")
    pdf.add_field("Nombre", delivery.get('worker_name'))
    pdf.add_field("RUT", delivery.get('worker_rut'))
    pdf.add_field("Cargo", delivery.get('worker_position'))
    pdf.ln(5)
    
    # Items
    pdf.section_title("Articulos Entregados")
    items = delivery.get('items', [])
    if items:
        pdf.add_table_row(['Codigo', 'Descripcion', 'Cantidad', 'Estado'], [30, 90, 30, 40], header=True)
        for item in items:
            pdf.add_table_row([
                item.get('code', ''),
                item.get('name', ''),
                str(item.get('quantity', 1)),
                item.get('status', 'Nuevo')
            ], [30, 90, 30, 40])
    pdf.ln(5)
    
    # Signatures
    pdf.ln(20)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(95, 5, "_" * 30, align='C')
    pdf.cell(95, 5, "_" * 30, align='C', ln=True)
    pdf.cell(95, 5, "Firma Responsable", align='C')
    pdf.cell(95, 5, "Firma Trabajador", align='C', ln=True)
    
    # Signature status
    if delivery.get('signature_confirmed'):
        pdf.ln(5)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(34, 197, 94)
        pdf.cell(0, 5, f"Firma confirmada: {delivery.get('signature_date', 'N/A')}", align='C')
    
    # Output PDF
    pdf_output = io.BytesIO()
    pdf_content = pdf.output()
    pdf_output.write(pdf_content)
    pdf_output.seek(0)
    
    return StreamingResponse(
        pdf_output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=entrega-{delivery.get('delivery_number', delivery_id[:8])}.pdf"}
    )


# ================== IMPORT/EXPORT ==================

@router.post("/import/items")
async def import_epp_items(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Import EPP items from Excel"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo archivos Excel permitidos")
    
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    
    imported = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            item = EPPItem(
                code=str(row.get('codigo', f'EPP-{idx}')),
                name=str(row.get('nombre', 'Sin nombre')),
                category_id=str(row.get('categoria', '')) if pd.notna(row.get('categoria')) else None,
                brand=str(row.get('marca', '')) if pd.notna(row.get('marca')) else None,
                unit_cost=float(row.get('costo_unitario', 0)) if pd.notna(row.get('costo_unitario')) else 0
            )
            await db.epp_items.insert_one(item.model_dump())
            imported += 1
        except Exception as e:
            errors.append(f"Fila {idx + 2}: {str(e)}")
    
    return {"imported": imported, "errors": errors}


@router.post("/import/receptions")
async def import_receptions(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Import receptions from Excel"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo archivos Excel permitidos")
    
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    
    imported = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            code = str(row.get('codigo_epp', ''))
            item = await db.epp_items.find_one({"code": code}, {"_id": 0})
            
            if not item:
                errors.append(f"Fila {idx + 2}: Codigo EPP no encontrado: {code}")
                continue
            
            quantity = int(row.get('cantidad', 0))
            unit_cost = float(row.get('costo_unitario', 0)) if pd.notna(row.get('costo_unitario')) else 0
            
            movement = EPPMovement(
                epp_item_id=item["id"],
                epp_item_name=item.get("name", ""),
                epp_item_code=item.get("code", ""),
                movement_type="reception",
                quantity=quantity,
                unit_cost=unit_cost,
                total_cost=quantity * unit_cost,
                document_number=str(row.get('documento', '')) if pd.notna(row.get('documento')) else None,
                notes=str(row.get('notas', '')) if pd.notna(row.get('notas')) else None,
                created_by=current_user["name"]
            )
            await db.epp_movements.insert_one(movement.model_dump())
            imported += 1
        except Exception as e:
            errors.append(f"Fila {idx + 2}: {str(e)}")
    
    return {"imported": imported, "errors": errors}
