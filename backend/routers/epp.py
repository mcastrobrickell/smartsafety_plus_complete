"""SmartSafety+ - EPP Full Router (Items, Stock, Movements, Deliveries, Adjustments, Imports)"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
from config import db, logger
from models.schemas import EPPItem, EPPStock, EPPMovement, EPPDelivery, EPPStockAdjustment
from utils.auth import get_current_user
from utils.pagination import paginated_find
from utils.pdf import SafetyPDF
from datetime import datetime, timezone
import uuid
import io
import pandas as pd

router = APIRouter(tags=["epp"])

@router.get("/epp/items")
async def get_epp_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user)
):
    return await paginated_find(
        db.epp_items,
        sort_field="created_at",
        page=page,
        page_size=page_size,
    )

@router.post("/epp/items")
async def create_epp_item(item: EPPItem, current_user: dict = Depends(get_current_user)):
    await db.epp_items.insert_one(item.model_dump())
    return item

@router.put("/epp/items/{item_id}")
async def update_epp_item(item_id: str, updates: dict, current_user: dict = Depends(get_current_user)):
    result = await db.epp_items.update_one({"id": item_id}, {"$set": updates})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item updated"}

@router.delete("/epp/items/{item_id}")
async def delete_epp_item(item_id: str, current_user: dict = Depends(get_current_user)):
    await db.epp_items.delete_one({"id": item_id})
    return {"message": "Item deleted"}

@router.get("/epp/stock")
async def get_epp_stock(cost_center_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if cost_center_id:
        query["cost_center_id"] = cost_center_id
    stocks = await db.epp_stock.find(query, {"_id": 0}).to_list(1000)
    return stocks

@router.get("/epp/stock/summary")
async def get_stock_summary(current_user: dict = Depends(get_current_user)):
    """Get stock summary by cost center with total values"""
    pipeline = [
        {
            "$lookup": {
                "from": "epp_items",
                "localField": "epp_item_id",
                "foreignField": "id",
                "as": "item"
            }
        },
        {"$unwind": {"path": "$item", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "cost_centers",
                "localField": "cost_center_id",
                "foreignField": "id",
                "as": "cost_center"
            }
        },
        {"$unwind": {"path": "$cost_center", "preserveNullAndEmptyArrays": True}},
        {
            "$group": {
                "_id": "$cost_center_id",
                "cost_center_name": {"$first": "$cost_center.name"},
                "total_items": {"$sum": "$quantity"},
                "total_value": {"$sum": {"$multiply": ["$quantity", {"$ifNull": ["$item.unit_cost", 0]}]}},
                "low_stock_count": {
                    "$sum": {"$cond": [{"$lt": ["$quantity", "$min_stock"]}, 1, 0]}
                }
            }
        }
    ]
    summary = await db.epp_stock.aggregate(pipeline).to_list(1000)
    return summary

@router.get("/epp/movements")
async def get_epp_movements(
    movement_type: Optional[str] = None,
    cost_center_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
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
    
    result = await paginated_find(
        db.epp_movements,
        query=query,
        sort_field="created_at",
        page=page,
        page_size=page_size,
    )
    
    # Enrich movements with item names if missing
    items_cache = {}
    for movement in result["items"]:
        if not movement.get("epp_item_name"):
            item_id = movement.get("epp_item_id")
            if item_id not in items_cache:
                item = await db.epp_items.find_one({"id": item_id}, {"_id": 0})
                items_cache[item_id] = item
            item = items_cache.get(item_id)
            if item:
                movement["epp_item_name"] = item.get("name", "")
                movement["epp_item_code"] = item.get("code", "")
    
    return result

@router.post("/epp/movements/reception")
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
    # Get item info for historical reference
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

@router.post("/epp/movements/distribution")
async def create_distribution(
    epp_item_id: str,
    quantity: int,
    from_cost_center_id: str,
    to_cost_center_id: str,
    from_location: str,
    to_location: str,
    document_number: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Distribution between warehouses/locations"""
    # Check stock availability
    from_stock = await db.epp_stock.find_one({
        "epp_item_id": epp_item_id,
        "cost_center_id": from_cost_center_id,
        "warehouse_location": from_location
    })
    
    if not from_stock or from_stock["quantity"] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    # Get item cost
    item = await db.epp_items.find_one({"id": epp_item_id}, {"_id": 0})
    unit_cost = item.get("unit_cost", 0) if item else 0
    
    movement = EPPMovement(
        epp_item_id=epp_item_id,
        movement_type="distribution",
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
        from_cost_center_id=from_cost_center_id,
        to_cost_center_id=to_cost_center_id,
        warehouse_location=to_location,
        document_number=document_number,
        notes=notes,
        created_by=current_user["name"]
    )
    await db.epp_movements.insert_one(movement.model_dump())
    
    # Update stocks
    await db.epp_stock.update_one(
        {"id": from_stock["id"]},
        {"$inc": {"quantity": -quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
    )
    
    to_stock = await db.epp_stock.find_one({
        "epp_item_id": epp_item_id,
        "cost_center_id": to_cost_center_id,
        "warehouse_location": to_location
    })
    
    if to_stock:
        await db.epp_stock.update_one(
            {"id": to_stock["id"]},
            {"$inc": {"quantity": quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        stock = EPPStock(
            epp_item_id=epp_item_id,
            cost_center_id=to_cost_center_id,
            warehouse_location=to_location,
            quantity=quantity
        )
        await db.epp_stock.insert_one(stock.model_dump())
    
    return movement

@router.post("/epp/movements/dispatch")
async def create_dispatch(
    epp_item_id: str,
    quantity: int,
    cost_center_id: str,
    warehouse_location: str,
    document_number: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Dispatch EPP for delivery"""
    # Check stock
    stock = await db.epp_stock.find_one({
        "epp_item_id": epp_item_id,
        "cost_center_id": cost_center_id,
        "warehouse_location": warehouse_location
    })
    
    if not stock or stock["quantity"] < quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    item = await db.epp_items.find_one({"id": epp_item_id}, {"_id": 0})
    unit_cost = item.get("unit_cost", 0) if item else 0
    
    movement = EPPMovement(
        epp_item_id=epp_item_id,
        movement_type="dispatch",
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
        from_cost_center_id=cost_center_id,
        warehouse_location=warehouse_location,
        document_number=document_number,
        notes=notes,
        created_by=current_user["name"]
    )
    await db.epp_movements.insert_one(movement.model_dump())
    
    # Update stock
    await db.epp_stock.update_one(
        {"id": stock["id"]},
        {"$inc": {"quantity": -quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
    )
    
    return movement

@router.post("/epp/movements/delivery")
async def create_delivery(
    epp_item_id: str,
    quantity: int,
    worker_id: str,
    worker_name: str,
    cost_center_id: str,
    document_number: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Deliver EPP to worker"""
    item = await db.epp_items.find_one({"id": epp_item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="EPP item not found")
    
    unit_cost = item.get("unit_cost", 0)
    
    movement = EPPMovement(
        epp_item_id=epp_item_id,
        movement_type="delivery",
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
        to_cost_center_id=cost_center_id,
        worker_id=worker_id,
        worker_name=worker_name,
        document_number=document_number,
        notes=notes,
        created_by=current_user["name"]
    )
    await db.epp_movements.insert_one(movement.model_dump())
    
    # Create delivery record
    delivery = EPPDelivery(
        epp_item_id=epp_item_id,
        epp_item_name=item["name"],
        worker_id=worker_id,
        worker_name=worker_name,
        cost_center_id=cost_center_id,
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
        delivery_date=datetime.now(timezone.utc).isoformat(),
        delivered_by=current_user["name"]
    )
    await db.epp_deliveries.insert_one(delivery.model_dump())
    
    return {"movement": movement.model_dump(), "delivery": delivery.model_dump()}

@router.post("/epp/movements/return")
async def create_return(
    delivery_id: str,
    quantity: int,
    cost_center_id: str,
    warehouse_location: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Return EPP from worker"""
    delivery = await db.epp_deliveries.find_one({"id": delivery_id}, {"_id": 0})
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    movement = EPPMovement(
        epp_item_id=delivery["epp_item_id"],
        movement_type="return",
        quantity=quantity,
        unit_cost=delivery["unit_cost"],
        total_cost=quantity * delivery["unit_cost"],
        from_cost_center_id=delivery["cost_center_id"],
        to_cost_center_id=cost_center_id,
        warehouse_location=warehouse_location,
        worker_id=delivery["worker_id"],
        worker_name=delivery["worker_name"],
        notes=notes,
        created_by=current_user["name"]
    )
    await db.epp_movements.insert_one(movement.model_dump())
    
    # Update delivery status
    await db.epp_deliveries.update_one(
        {"id": delivery_id},
        {"$set": {"status": "returned", "return_date": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Add back to stock
    stock = await db.epp_stock.find_one({
        "epp_item_id": delivery["epp_item_id"],
        "cost_center_id": cost_center_id,
        "warehouse_location": warehouse_location
    })
    
    if stock:
        await db.epp_stock.update_one(
            {"id": stock["id"]},
            {"$inc": {"quantity": quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        new_stock = EPPStock(
            epp_item_id=delivery["epp_item_id"],
            cost_center_id=cost_center_id,
            warehouse_location=warehouse_location,
            quantity=quantity
        )
        await db.epp_stock.insert_one(new_stock.model_dump())
    
    return movement

@router.get("/epp/deliveries")
async def get_deliveries(
    status: Optional[str] = None,
    cost_center_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status
    if cost_center_id:
        query["cost_center_id"] = cost_center_id
    deliveries = await db.epp_deliveries.find(query, {"_id": 0}).sort("delivery_date", -1).to_list(1000)
    return deliveries


@router.get("/epp/reports/costs")
async def get_cost_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cost_center_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get cost report by cost center"""
    match_stage = {}
    if start_date:
        match_stage["created_at"] = {"$gte": start_date}
    if end_date:
        match_stage.setdefault("created_at", {})["$lte"] = end_date
    if cost_center_id:
        match_stage["$or"] = [
            {"from_cost_center_id": cost_center_id},
            {"to_cost_center_id": cost_center_id}
        ]
    
    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {
            "$group": {
                "_id": {
                    "movement_type": "$movement_type",
                    "cost_center": {"$ifNull": ["$to_cost_center_id", "$from_cost_center_id"]}
                },
                "total_quantity": {"$sum": "$quantity"},
                "total_cost": {"$sum": "$total_cost"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"total_cost": -1}}
    ]
    
    report = await db.epp_movements.aggregate(pipeline).to_list(1000)
    return report


@router.post("/epp/deliveries/create")
async def create_delivery_enhanced(
    data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Create delivery with full format (including manual ID for migration)"""
    
    # Get EPP item info
    item = await db.epp_items.find_one({"id": data.get("epp_item_id")}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="EPP item not found")
    
    unit_cost = item.get("unit_cost", 0)
    quantity = data.get("quantity", 1)
    
    delivery = EPPDelivery(
        delivery_number=data.get("delivery_number"),  # Manual ID for migration
        date=data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        time=data.get("time", datetime.now(timezone.utc).strftime("%H:%M")),
        group=data.get("group"),
        user=current_user.get("name"),
        status=data.get("status", "entregado"),
        responsible_name=data.get("responsible_name", current_user.get("name")),
        responsible_rut=data.get("responsible_rut"),
        responsible_position=data.get("responsible_position"),
        worker_name=data.get("worker_name"),
        worker_rut=data.get("worker_rut"),
        worker_position=data.get("worker_position"),
        cost_center_id=data.get("cost_center_id"),
        cost_center_name=data.get("cost_center_name"),
        delivery_type=data.get("delivery_type", "entrega"),
        epp_item_id=data.get("epp_item_id"),
        epp_item_code=item.get("code"),
        epp_item_name=item.get("name"),
        unit=item.get("unit", "unidad"),
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost,
        details=data.get("details"),
        signature_data=data.get("signature_data"),
        signature_confirmed=data.get("signature_confirmed", False),
        created_by=current_user.get("id")
    )
    
    delivery_dict = delivery.model_dump()
    await db.epp_deliveries.insert_one(delivery_dict)
    
    # Decrease stock
    stock = await db.epp_stock.find_one({"epp_item_id": data.get("epp_item_id")})
    if stock:
        await db.epp_stock.update_one(
            {"id": stock["id"]},
            {"$inc": {"quantity": -quantity}, "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}}
        )
    
    delivery_dict.pop("_id", None)
    return {"message": "Entrega registrada correctamente", "delivery": delivery_dict}


@router.get("/epp/deliveries/export-pdf")
async def export_deliveries_pdf(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cost_center_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export deliveries as PDF"""
    
    query = {}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("date", {})["$lte"] = end_date
    if cost_center_id:
        query["cost_center_id"] = cost_center_id
    
    deliveries = await db.epp_deliveries.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    
    pdf = SafetyPDF(
        title="Reporte de Entregas de EPP",
        org_name="SmartSafety+ Enterprise"
    )
    pdf.add_page()
    
    # Stats
    total_deliveries = len(deliveries)
    total_items = sum(d.get("quantity", 0) for d in deliveries)
    total_cost = sum(d.get("total_cost", 0) for d in deliveries)
    
    pdf.add_stat_box("Entregas", total_deliveries, 10, pdf.get_y())
    pdf.add_stat_box("Items", total_items, 60, pdf.get_y())
    pdf.add_stat_box(f"Costo Total", f"${total_cost:,.0f}", 110, pdf.get_y())
    pdf.ln(30)
    
    # Table
    pdf.add_section_title("Detalle de Entregas")
    headers = ["N°", "Fecha", "Trabajador", "EPP", "Cant.", "Tipo"]
    widths = [20, 25, 50, 45, 15, 25]
    pdf.add_table_header(headers, widths)
    
    for i, d in enumerate(deliveries[:50]):
        pdf.add_table_row([
            d.get('delivery_number', str(i+1))[:8],
            d.get('date', '')[:10],
            d.get('worker_name', 'N/A')[:22],
            d.get('epp_item_name', 'N/A')[:20],
            str(d.get('quantity', 0)),
            d.get('delivery_type', 'entrega')[:10]
        ], widths, fill=(i % 2 == 0))
    
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=entregas-epp-{datetime.now().strftime('%Y%m%d')}.pdf"}
    )


@router.get("/epp/delivery/{delivery_id}/pdf")
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
    pdf.cell(0, 8, f"N° Entrega: {delivery.get('delivery_number', delivery.get('id', '')[:8])}", ln=True)
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
    pdf.add_section_title("Responsable de la Entrega", (59, 130, 246))
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f"Nombre: {delivery.get('responsible_name', 'N/A')}", ln=True)
    pdf.cell(0, 6, f"RUT: {delivery.get('responsible_rut', 'N/A')}", ln=True)
    pdf.cell(0, 6, f"Cargo: {delivery.get('responsible_position', 'N/A')}", ln=True)
    pdf.ln(5)
    
    # Worker
    pdf.add_section_title("Trabajador que Recibe", (16, 185, 129))
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f"Nombre: {delivery.get('worker_name', 'N/A')}", ln=True)
    pdf.cell(0, 6, f"RUT: {delivery.get('worker_rut', 'N/A')}", ln=True)
    pdf.cell(0, 6, f"Cargo: {delivery.get('worker_position', 'N/A')}", ln=True)
    pdf.ln(5)
    
    # EPP Details
    pdf.add_section_title("EPP Entregado", (249, 115, 22))
    headers = ["Código", "Artículo", "Unidad", "Cantidad", "Costo Unit.", "Total"]
    widths = [25, 60, 25, 25, 25, 25]
    pdf.add_table_header(headers, widths)
    pdf.add_table_row([
        delivery.get('epp_item_code', 'N/A'),
        delivery.get('epp_item_name', 'N/A')[:25],
        delivery.get('unit', 'unidad'),
        str(delivery.get('quantity', 0)),
        f"${delivery.get('unit_cost', 0):,.0f}",
        f"${delivery.get('total_cost', 0):,.0f}"
    ], widths, fill=True)
    
    pdf.ln(10)
    
    # Details
    if delivery.get('details'):
        pdf.add_section_title("Observaciones")
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 5, delivery.get('details', ''))
        pdf.ln(5)
    
    # Signature
    pdf.ln(15)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(95, 30, "Firma Responsable:", border=1, align='C')
    pdf.cell(95, 30, "Firma Trabajador (Recibe Conforme):", border=1, align='C')
    
    if delivery.get('signature_confirmed'):
        pdf.ln(35)
        pdf.set_fill_color(16, 185, 129)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(50, 8, "  FIRMADO  ", fill=True, align='C')
        pdf.set_text_color(30, 41, 59)
    
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=entrega-{delivery.get('delivery_number', delivery_id[:8])}.pdf"}
    )


@router.get("/epp/stock/inventory")
async def get_stock_inventory(current_user: dict = Depends(get_current_user)):
    """Get complete stock inventory with item details"""
    
    items = await db.epp_items.find({"is_active": True}, {"_id": 0}).to_list(1000)
    stocks = await db.epp_stock.find({}, {"_id": 0}).to_list(1000)
    
    # Aggregate stock by item
    stock_by_item = {}
    for stock in stocks:
        item_id = stock.get("epp_item_id")
        if item_id not in stock_by_item:
            stock_by_item[item_id] = 0
        stock_by_item[item_id] += stock.get("quantity", 0)
    
    inventory = []
    for item in items:
        inventory.append({
            "id": item.get("id"),
            "code": item.get("code"),
            "name": item.get("name"),
            "category_id": item.get("category_id"),
            "unit": item.get("unit", "unidad"),
            "unit_cost": item.get("unit_cost", 0),
            "current_stock": stock_by_item.get(item.get("id"), 0),
            "min_stock": item.get("min_stock", 5),
            "stock_value": stock_by_item.get(item.get("id"), 0) * item.get("unit_cost", 0)
        })
    
    return inventory


@router.post("/epp/stock/adjust")
async def adjust_stock(
    epp_item_id: str,
    new_stock: int,
    reason: str,
    current_user: dict = Depends(get_current_user)
):
    """Adjust stock for inventory corrections"""
    
    item = await db.epp_items.find_one({"id": epp_item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="EPP item not found")
    
    # Get current stock
    stocks = await db.epp_stock.find({"epp_item_id": epp_item_id}, {"_id": 0}).to_list(100)
    current_stock = sum(s.get("quantity", 0) for s in stocks)
    
    adjustment_qty = new_stock - current_stock
    
    # Create adjustment record
    adjustment = EPPStockAdjustment(
        epp_item_id=epp_item_id,
        epp_item_code=item.get("code"),
        epp_item_name=item.get("name"),
        previous_stock=current_stock,
        new_stock=new_stock,
        adjustment_quantity=adjustment_qty,
        reason=reason,
        adjusted_by=current_user.get("name")
    )
    
    await db.epp_adjustments.insert_one(adjustment.model_dump())
    
    # Update or create stock record
    if stocks:
        # Update first stock record
        await db.epp_stock.update_one(
            {"id": stocks[0]["id"]},
            {"$set": {"quantity": new_stock, "last_updated": datetime.now(timezone.utc).isoformat()}}
        )
        # Zero out others if multiple
        for s in stocks[1:]:
            await db.epp_stock.update_one({"id": s["id"]}, {"$set": {"quantity": 0}})
    else:
        new_stock_doc = EPPStock(
            epp_item_id=epp_item_id,
            cost_center_id="general",
            warehouse_location="bodega_principal",
            quantity=new_stock
        )
        await db.epp_stock.insert_one(new_stock_doc.model_dump())
    
    return {
        "message": f"Stock ajustado de {current_stock} a {new_stock}",
        "adjustment": {
            "previous": current_stock,
            "new": new_stock,
            "difference": adjustment_qty
        }
    }


@router.get("/epp/adjustments")
async def get_adjustments(current_user: dict = Depends(get_current_user)):
    """Get stock adjustment history"""
    adjustments = await db.epp_adjustments.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return adjustments


@router.post("/epp/import/items")
async def import_items_excel(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Import EPP items from Excel file"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    
    imported = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            item = {
                "id": str(uuid.uuid4()),
                "code": str(row.get("codigo", row.get("Codigo", ""))),
                "name": str(row.get("nombre", row.get("Nombre", ""))),
                "category_id": str(row.get("categoria", row.get("Categoria", "general"))),
                "type_id": str(row.get("tipo", row.get("Tipo", "general"))),
                "brand": str(row.get("marca", row.get("Marca", ""))),
                "model": str(row.get("modelo", row.get("Modelo", ""))) if pd.notna(row.get("modelo", row.get("Modelo"))) else None,
                "unit_cost": float(row.get("costo", row.get("Costo", row.get("costo_unitario", 0)))) if pd.notna(row.get("costo", row.get("Costo", row.get("costo_unitario")))) else 0,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            if item["code"] and item["name"]:
                await db.epp_items.insert_one(item)
                imported += 1
        except Exception as e:
            errors.append(f"Fila {idx + 2}: {str(e)}")
    
    return {"imported": imported, "errors": errors, "total_rows": len(df)}


@router.post("/epp/import/receptions")
async def import_receptions_excel(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Import EPP receptions from Excel file"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    
    imported = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Find item by code
            code = str(row.get("codigo_epp", row.get("codigo", "")))
            item = await db.epp_items.find_one({"code": code}, {"_id": 0})
            
            if not item:
                errors.append(f"Fila {idx + 2}: Código EPP '{code}' no encontrado")
                continue
            
            quantity = int(row.get("cantidad", 0))
            unit_cost = float(row.get("costo_unitario", item.get("unit_cost", 0)))
            
            movement = {
                "id": str(uuid.uuid4()),
                "epp_item_id": item["id"],
                "movement_type": "reception",
                "quantity": quantity,
                "unit_cost": unit_cost,
                "total_cost": quantity * unit_cost,
                "document_number": str(row.get("documento", "")) if pd.notna(row.get("documento")) else None,
                "notes": str(row.get("notas", "")) if pd.notna(row.get("notas")) else None,
                "created_by": current_user.get("name"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.epp_movements.insert_one(movement)
            
            # Update stock
            stock = await db.epp_stock.find_one({"epp_item_id": item["id"]})
            if stock:
                await db.epp_stock.update_one(
                    {"id": stock["id"]},
                    {"$inc": {"quantity": quantity}}
                )
            else:
                new_stock = {
                    "id": str(uuid.uuid4()),
                    "epp_item_id": item["id"],
                    "cost_center_id": "general",
                    "warehouse_location": "bodega_principal",
                    "quantity": quantity,
                    "min_stock": 5,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
                await db.epp_stock.insert_one(new_stock)
            
            imported += 1
        except Exception as e:
            errors.append(f"Fila {idx + 2}: {str(e)}")
    
    return {"imported": imported, "errors": errors, "total_rows": len(df)}


@router.post("/epp/import/deliveries")
async def import_deliveries_excel(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Import EPP deliveries from Excel file (for migration)"""
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    
    imported = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Find item by code
            code = str(row.get("codigo_epp", row.get("codigo", "")))
            item = await db.epp_items.find_one({"code": code}, {"_id": 0})
            
            if not item:
                errors.append(f"Fila {idx + 2}: Código EPP '{code}' no encontrado")
                continue
            
            quantity = int(row.get("cantidad", 1))
            unit_cost = float(row.get("costo_unitario", item.get("unit_cost", 0)))
            
            # Convert date
            date_val = row.get("fecha", datetime.now())
            if isinstance(date_val, str):
                date_str = date_val
            else:
                date_str = date_val.strftime("%Y-%m-%d") if pd.notna(date_val) else datetime.now().strftime("%Y-%m-%d")
            
            delivery = EPPDelivery(
                delivery_number=str(row.get("numero", row.get("N°", ""))) if pd.notna(row.get("numero", row.get("N°"))) else None,
                date=date_str,
                time=str(row.get("hora", "")) if pd.notna(row.get("hora")) else None,
                group=str(row.get("grupo", "")) if pd.notna(row.get("grupo")) else None,
                user=current_user.get("name"),
                status="entregado",
                responsible_name=str(row.get("responsable", current_user.get("name"))),
                responsible_rut=str(row.get("rut_responsable", "")) if pd.notna(row.get("rut_responsable")) else None,
                responsible_position=str(row.get("cargo_responsable", "")) if pd.notna(row.get("cargo_responsable")) else None,
                worker_name=str(row.get("trabajador", row.get("nombre_trabajador", ""))),
                worker_rut=str(row.get("rut_trabajador", "")) if pd.notna(row.get("rut_trabajador")) else None,
                worker_position=str(row.get("cargo_trabajador", "")) if pd.notna(row.get("cargo_trabajador")) else None,
                cost_center_id=str(row.get("centro_costo_id", "")) if pd.notna(row.get("centro_costo_id")) else None,
                cost_center_name=str(row.get("centro_costo", row.get("faena", ""))) if pd.notna(row.get("centro_costo", row.get("faena"))) else None,
                delivery_type=str(row.get("tipo_entrega", "entrega")).lower(),
                epp_item_id=item["id"],
                epp_item_code=item.get("code"),
                epp_item_name=item.get("name"),
                unit=item.get("unit", "unidad"),
                quantity=quantity,
                unit_cost=unit_cost,
                total_cost=quantity * unit_cost,
                details=str(row.get("detalles", "")) if pd.notna(row.get("detalles")) else None,
                signature_confirmed=bool(row.get("firmado", False)) if pd.notna(row.get("firmado")) else False,
                created_by=current_user.get("id")
            )
            
            await db.epp_deliveries.insert_one(delivery.model_dump())
            imported += 1
        except Exception as e:
            errors.append(f"Fila {idx + 2}: {str(e)}")
    
    return {"imported": imported, "errors": errors, "total_rows": len(df)}


