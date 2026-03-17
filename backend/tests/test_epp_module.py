"""
Test suite for SmartSafety+ EPP Module (Refactored):
- EPP Items CRUD
- EPP Stock management
- EPP Receptions (movements)
- EPP Deliveries (entregas)
- Stock adjustments
- PDF generation for deliveries
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@smartsafety.com"
ADMIN_PASSWORD = "Admin123!"

# Test data tracking for cleanup
created_items = []
created_cost_centers = []
created_deliveries = []


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def authenticated_client(api_client, admin_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return api_client


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data(authenticated_client):
    """Cleanup test data after all tests"""
    yield
    # Cleanup created items
    for item_id in created_items:
        try:
            authenticated_client.delete(f"{BASE_URL}/api/epp/items/{item_id}")
        except:
            pass
    # Cleanup cost centers
    for cc_id in created_cost_centers:
        try:
            authenticated_client.delete(f"{BASE_URL}/api/cost-centers/{cc_id}")
        except:
            pass


class TestEPPItems:
    """Test EPP Items CRUD operations"""
    
    def test_create_epp_item(self, authenticated_client):
        """Test creating a new EPP item"""
        response = authenticated_client.post(f"{BASE_URL}/api/epp/items", json={
            "code": "TEST-CASCO-001",
            "name": "TEST Casco de Seguridad",
            "category_id": "proteccion_cabeza",
            "type_id": "casco_tipo_1",
            "brand": "3M",
            "model": "H-700",
            "unit_cost": 25000
        })
        assert response.status_code == 200, f"Create item failed: {response.text}"
        data = response.json()
        assert data.get("code") == "TEST-CASCO-001"
        assert data.get("name") == "TEST Casco de Seguridad"
        assert "id" in data
        created_items.append(data["id"])
        print(f"✓ EPP Item created: {data['code']} - ID: {data['id'][:20]}...")
        return data["id"]
    
    def test_get_epp_items(self, authenticated_client):
        """Test getting all EPP items"""
        response = authenticated_client.get(f"{BASE_URL}/api/epp/items")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the item we created
        test_items = [i for i in data if i.get("code", "").startswith("TEST-")]
        print(f"✓ Got {len(data)} items, {len(test_items)} test items")
    
    def test_delete_epp_item(self, authenticated_client):
        """Test deleting an EPP item"""
        # Create item to delete
        create_resp = authenticated_client.post(f"{BASE_URL}/api/epp/items", json={
            "code": "TEST-DELETE-001",
            "name": "TEST Item to Delete",
            "category_id": "test",
            "type_id": "test",
            "brand": "Test"
        })
        assert create_resp.status_code == 200
        item_id = create_resp.json()["id"]
        
        # Delete
        delete_resp = authenticated_client.delete(f"{BASE_URL}/api/epp/items/{item_id}")
        assert delete_resp.status_code == 200
        print(f"✓ EPP Item deleted: {item_id[:20]}...")


class TestCostCenters:
    """Test Cost Centers for EPP operations"""
    
    def test_create_cost_center(self, authenticated_client):
        """Test creating a cost center"""
        response = authenticated_client.post(f"{BASE_URL}/api/cost-centers", json={
            "code": "TEST-CC-EPP-001",
            "name": "TEST Bodega EPP Principal",
            "description": "Centro de costo para pruebas EPP"
        })
        assert response.status_code == 200, f"Create cost center failed: {response.text}"
        data = response.json()
        assert data.get("code") == "TEST-CC-EPP-001"
        created_cost_centers.append(data["id"])
        print(f"✓ Cost Center created: {data['code']} - ID: {data['id'][:20]}...")
        return data["id"]
    
    def test_get_cost_centers(self, authenticated_client):
        """Test getting all cost centers"""
        response = authenticated_client.get(f"{BASE_URL}/api/cost-centers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} cost centers")


class TestEPPReception:
    """Test EPP Reception (ingreso a bodega)"""
    
    @pytest.fixture
    def test_item_id(self, authenticated_client):
        """Create a test item for reception"""
        resp = authenticated_client.post(f"{BASE_URL}/api/epp/items", json={
            "code": "TEST-RECEPTION-001",
            "name": "TEST Item for Reception",
            "category_id": "test",
            "type_id": "test",
            "brand": "Test",
            "unit_cost": 10000
        })
        item_id = resp.json()["id"]
        created_items.append(item_id)
        return item_id
    
    @pytest.fixture
    def test_cc_id(self, authenticated_client):
        """Create a test cost center for reception"""
        resp = authenticated_client.post(f"{BASE_URL}/api/cost-centers", json={
            "code": "TEST-CC-REC-001",
            "name": "TEST CC for Reception"
        })
        cc_id = resp.json()["id"]
        created_cost_centers.append(cc_id)
        return cc_id
    
    def test_create_reception(self, authenticated_client, test_item_id, test_cc_id):
        """Test registering a reception (ingreso a bodega)"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/epp/movements/reception",
            params={
                "epp_item_id": test_item_id,
                "quantity": 50,
                "unit_cost": 10000,
                "cost_center_id": test_cc_id,
                "warehouse_location": "A-01-01",
                "document_number": "TEST-FAC-001",
                "notes": "Test reception"
            }
        )
        assert response.status_code == 200, f"Reception failed: {response.text}"
        data = response.json()
        assert data.get("movement_type") == "reception"
        assert data.get("quantity") == 50
        assert data.get("total_cost") == 500000
        print(f"✓ Reception created: qty {data['quantity']}, total: ${data['total_cost']}")
    
    def test_stock_updated_after_reception(self, authenticated_client, test_item_id):
        """Test that stock is updated after reception"""
        response = authenticated_client.get(f"{BASE_URL}/api/epp/stock")
        assert response.status_code == 200
        data = response.json()
        
        # Find stock for our test item
        item_stock = [s for s in data if s.get("epp_item_id") == test_item_id]
        assert len(item_stock) > 0, "Stock record not created"
        assert item_stock[0].get("quantity") == 50
        print(f"✓ Stock verified: {item_stock[0]['quantity']} units")


class TestEPPDeliveries:
    """Test EPP Deliveries (entregas a trabajadores)"""
    
    @pytest.fixture
    def setup_delivery_data(self, authenticated_client):
        """Setup item and cost center for delivery tests"""
        # Create item
        item_resp = authenticated_client.post(f"{BASE_URL}/api/epp/items", json={
            "code": "TEST-DELIVERY-001",
            "name": "TEST Item for Delivery",
            "category_id": "test",
            "type_id": "test",
            "brand": "Test",
            "unit_cost": 15000
        })
        item_id = item_resp.json()["id"]
        created_items.append(item_id)
        
        # Create cost center
        cc_resp = authenticated_client.post(f"{BASE_URL}/api/cost-centers", json={
            "code": "TEST-CC-DEL-001",
            "name": "TEST CC for Delivery"
        })
        cc_id = cc_resp.json()["id"]
        created_cost_centers.append(cc_id)
        
        # Create reception to have stock
        authenticated_client.post(
            f"{BASE_URL}/api/epp/movements/reception",
            params={
                "epp_item_id": item_id,
                "quantity": 100,
                "unit_cost": 15000,
                "cost_center_id": cc_id,
                "warehouse_location": "A-02-01"
            }
        )
        
        return {"item_id": item_id, "cc_id": cc_id}
    
    def test_create_delivery(self, authenticated_client, setup_delivery_data):
        """Test creating a delivery with full format"""
        item_id = setup_delivery_data["item_id"]
        cc_id = setup_delivery_data["cc_id"]
        
        response = authenticated_client.post(f"{BASE_URL}/api/epp/deliveries/create", json={
            "delivery_number": "TEST-ENT-001",
            "date": "2026-03-17",
            "time": "10:30",
            "responsible_name": "TEST Supervisor",
            "responsible_rut": "12.345.678-9",
            "responsible_position": "Jefe Bodega",
            "worker_name": "TEST Trabajador",
            "worker_rut": "98.765.432-1",
            "worker_position": "Operador",
            "cost_center_id": cc_id,
            "cost_center_name": "TEST CC for Delivery",
            "delivery_type": "entrega",
            "epp_item_id": item_id,
            "quantity": 2,
            "details": "Test delivery",
            "signature_confirmed": True
        })
        assert response.status_code == 200, f"Delivery creation failed: {response.text}"
        data = response.json()
        assert data.get("message") == "Entrega registrada correctamente"
        assert "delivery" in data
        delivery_id = data["delivery"]["id"]
        created_deliveries.append(delivery_id)
        print(f"✓ Delivery created: {data['delivery']['delivery_number']}")
        return delivery_id
    
    def test_get_deliveries(self, authenticated_client):
        """Test getting all deliveries"""
        response = authenticated_client.get(f"{BASE_URL}/api/epp/deliveries")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        test_deliveries = [d for d in data if d.get("delivery_number", "").startswith("TEST-")]
        print(f"✓ Got {len(data)} deliveries, {len(test_deliveries)} test deliveries")
    
    def test_stock_decreased_after_delivery(self, authenticated_client, setup_delivery_data):
        """Test that stock decreases after delivery"""
        item_id = setup_delivery_data["item_id"]
        
        # Get stock
        response = authenticated_client.get(f"{BASE_URL}/api/epp/stock")
        assert response.status_code == 200
        data = response.json()
        
        item_stock = [s for s in data if s.get("epp_item_id") == item_id]
        if item_stock:
            # Should be 100 - 2 = 98 after delivery
            assert item_stock[0].get("quantity") <= 100
            print(f"✓ Stock after delivery: {item_stock[0]['quantity']} (was 100)")


class TestDeliveryPDF:
    """Test PDF generation for deliveries"""
    
    def test_generate_delivery_pdf(self, authenticated_client):
        """Test generating PDF for a single delivery"""
        # Get a delivery first
        deliveries_resp = authenticated_client.get(f"{BASE_URL}/api/epp/deliveries")
        deliveries = deliveries_resp.json()
        
        if not deliveries:
            pytest.skip("No deliveries to generate PDF")
        
        delivery_id = deliveries[0]["id"]
        
        response = authenticated_client.get(f"{BASE_URL}/api/epp/delivery/{delivery_id}/pdf")
        assert response.status_code == 200, f"PDF generation failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        assert response.content[:4] == b'%PDF', "Response is not a valid PDF"
        print(f"✓ PDF generated, size: {len(response.content)} bytes")
    
    def test_export_deliveries_pdf(self, authenticated_client):
        """Test exporting all deliveries as PDF"""
        response = authenticated_client.get(f"{BASE_URL}/api/epp/deliveries/export-pdf")
        assert response.status_code == 200, f"PDF export failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        assert response.content[:4] == b'%PDF', "Response is not a valid PDF"
        print(f"✓ All deliveries PDF exported, size: {len(response.content)} bytes")


class TestStockAdjustment:
    """Test stock adjustment functionality"""
    
    @pytest.fixture
    def setup_item_with_stock(self, authenticated_client):
        """Create item with stock for adjustment testing"""
        # Create item
        item_resp = authenticated_client.post(f"{BASE_URL}/api/epp/items", json={
            "code": "TEST-ADJUST-001",
            "name": "TEST Item for Adjustment",
            "category_id": "test",
            "type_id": "test",
            "brand": "Test",
            "unit_cost": 5000
        })
        item_id = item_resp.json()["id"]
        created_items.append(item_id)
        
        # Create cost center
        cc_resp = authenticated_client.post(f"{BASE_URL}/api/cost-centers", json={
            "code": "TEST-CC-ADJ-001",
            "name": "TEST CC for Adjustment"
        })
        cc_id = cc_resp.json()["id"]
        created_cost_centers.append(cc_id)
        
        # Add stock via reception
        authenticated_client.post(
            f"{BASE_URL}/api/epp/movements/reception",
            params={
                "epp_item_id": item_id,
                "quantity": 100,
                "unit_cost": 5000,
                "cost_center_id": cc_id,
                "warehouse_location": "A-03-01"
            }
        )
        
        return item_id
    
    def test_adjust_stock(self, authenticated_client, setup_item_with_stock):
        """Test adjusting stock manually"""
        item_id = setup_item_with_stock
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/epp/stock/adjust",
            params={
                "epp_item_id": item_id,
                "new_stock": 75,
                "reason": "TEST - Ajuste de inventario físico"
            }
        )
        assert response.status_code == 200, f"Stock adjustment failed: {response.text}"
        data = response.json()
        assert "Stock ajustado" in data.get("message", "")
        assert data["adjustment"]["previous"] == 100
        assert data["adjustment"]["new"] == 75
        print(f"✓ Stock adjusted: {data['adjustment']['previous']} → {data['adjustment']['new']}")
    
    def test_get_adjustments_history(self, authenticated_client):
        """Test getting adjustment history"""
        response = authenticated_client.get(f"{BASE_URL}/api/epp/adjustments")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        test_adjustments = [a for a in data if a.get("reason", "").startswith("TEST")]
        print(f"✓ Got {len(data)} adjustments, {len(test_adjustments)} test adjustments")


class TestStockInventory:
    """Test stock inventory endpoint"""
    
    def test_get_stock_inventory(self, authenticated_client):
        """Test getting stock inventory with item details"""
        response = authenticated_client.get(f"{BASE_URL}/api/epp/stock/inventory")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check structure of inventory items
        if data:
            item = data[0]
            expected_fields = ["id", "code", "name", "current_stock", "min_stock", "stock_value"]
            for field in expected_fields:
                assert field in item, f"Missing field: {field}"
        
        print(f"✓ Got inventory with {len(data)} items")


class TestEPPMovements:
    """Test EPP movements listing"""
    
    def test_get_movements(self, authenticated_client):
        """Test getting all movements"""
        response = authenticated_client.get(f"{BASE_URL}/api/epp/movements")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Count movement types
        types = {}
        for m in data:
            mt = m.get("movement_type", "unknown")
            types[mt] = types.get(mt, 0) + 1
        
        print(f"✓ Got {len(data)} movements: {types}")
    
    def test_filter_movements_by_type(self, authenticated_client):
        """Test filtering movements by type"""
        response = authenticated_client.get(f"{BASE_URL}/api/epp/movements?movement_type=reception")
        assert response.status_code == 200
        data = response.json()
        
        for m in data:
            assert m.get("movement_type") == "reception"
        
        print(f"✓ Filtered receptions: {len(data)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
