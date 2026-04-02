"""
Test suite for SmartSafety+ new features:
- Login with admin credentials
- PDF Export (/api/reports/export-pdf)
- Email with Resend (/api/notifications/send-alert)
- Notification config status (/api/notifications/config-status)
- SMS endpoint (mocked - no credentials)
- Configuration categories (/api/config/categories)
- Cost centers (/api/cost-centers)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@smartsafety.com"
ADMIN_PASSWORD = "Admin123!"
TEST_EMAIL = "mcastrobrickell@gmail.com"


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


class TestAdminLogin:
    """Test admin login functionality"""
    
    def test_admin_login_success(self, api_client):
        """Test admin login with correct credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful: {data['user']['name']}")
    
    def test_admin_login_wrong_password(self, api_client):
        """Test admin login with wrong password"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "WrongPassword123"
        })
        assert response.status_code == 401
        print("✓ Wrong password correctly rejected")


class TestPDFExport:
    """Test PDF export functionality"""
    
    def test_export_incidents_pdf(self, authenticated_client):
        """Test PDF export for incidents"""
        response = authenticated_client.get(f"{BASE_URL}/api/reports/export-pdf?report_type=incidents")
        assert response.status_code == 200, f"PDF export failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        assert "content-disposition" in response.headers
        assert "reporte-incidents" in response.headers.get("content-disposition", "")
        # Verify it's a real PDF (starts with %PDF)
        assert response.content[:4] == b'%PDF', "Response is not a valid PDF file"
        print(f"✓ Incidents PDF export successful, size: {len(response.content)} bytes")
    
    def test_export_findings_pdf(self, authenticated_client):
        """Test PDF export for findings"""
        response = authenticated_client.get(f"{BASE_URL}/api/reports/export-pdf?report_type=findings")
        assert response.status_code == 200, f"PDF export failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        assert response.content[:4] == b'%PDF', "Response is not a valid PDF file"
        print(f"✓ Findings PDF export successful, size: {len(response.content)} bytes")
    
    def test_export_epp_pdf(self, authenticated_client):
        """Test PDF export for EPP movements"""
        response = authenticated_client.get(f"{BASE_URL}/api/reports/export-pdf?report_type=epp")
        assert response.status_code == 200, f"PDF export failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        assert response.content[:4] == b'%PDF', "Response is not a valid PDF file"
        print(f"✓ EPP PDF export successful, size: {len(response.content)} bytes")
    
    def test_export_risk_matrix_pdf(self, authenticated_client):
        """Test PDF export for risk matrix"""
        response = authenticated_client.get(f"{BASE_URL}/api/reports/export-pdf?report_type=risk-matrix")
        assert response.status_code == 200, f"PDF export failed: {response.text}"
        assert response.headers.get("content-type") == "application/pdf"
        assert response.content[:4] == b'%PDF', "Response is not a valid PDF file"
        print(f"✓ Risk Matrix PDF export successful, size: {len(response.content)} bytes")


class TestEmailNotifications:
    """Test email notifications with Resend"""
    
    def test_send_alert_email(self, authenticated_client):
        """Test sending alert email with custom message"""
        response = authenticated_client.post(f"{BASE_URL}/api/notifications/send-alert", json={
            "recipient_email": TEST_EMAIL,
            "subject": "TEST - SmartSafety+ Alert",
            "custom_message": "This is a test alert from SmartSafety+ automated testing"
        })
        # Should succeed since Resend API key is configured
        assert response.status_code == 200, f"Email send failed: {response.text}"
        data = response.json()
        assert data.get("status") == "success"
        assert "email_id" in data
        print(f"✓ Alert email sent successfully to {TEST_EMAIL}, email_id: {data['email_id']}")
    
    def test_send_alert_invalid_email(self, authenticated_client):
        """Test sending to invalid email format"""
        response = authenticated_client.post(f"{BASE_URL}/api/notifications/send-alert", json={
            "recipient_email": "not-an-email",
            "subject": "Test",
            "custom_message": "Test"
        })
        # Should fail validation
        assert response.status_code == 422, "Should reject invalid email"
        print("✓ Invalid email correctly rejected")


class TestNotificationConfigStatus:
    """Test notification configuration status endpoint"""
    
    def test_config_status(self, authenticated_client):
        """Test notification config status endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications/config-status")
        assert response.status_code == 200, f"Config status failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "email" in data
        assert "sms" in data
        assert "configured" in data["email"]
        assert "provider" in data["email"]
        assert "configured" in data["sms"]
        assert "provider" in data["sms"]
        
        # Email should be configured (Resend API key is set)
        assert data["email"]["configured"] == True
        assert data["email"]["provider"] == "Resend"
        
        # SMS should NOT be configured (Twilio credentials not set)
        assert data["sms"]["configured"] == False
        assert data["sms"]["provider"] == "Twilio"
        
        print(f"✓ Config status: Email={data['email']['configured']}, SMS={data['sms']['configured']}")


class TestSMSNotification:
    """Test SMS notification (expected to fail - no Twilio credentials)"""
    
    def test_sms_not_configured(self, authenticated_client):
        """Test SMS endpoint returns proper error when not configured"""
        response = authenticated_client.post(f"{BASE_URL}/api/notifications/send-sms", json={
            "phone_number": "+1234567890",
            "message": "Test SMS"
        })
        # Should return 500 with specific error about SMS not configured
        assert response.status_code == 500
        assert "SMS service not configured" in response.text or "not configured" in response.text.lower()
        print("✓ SMS correctly reports not configured (Twilio credentials missing)")


class TestConfigCategories:
    """Test configuration categories CRUD"""
    
    @pytest.fixture(autouse=True)
    def cleanup_test_categories(self, authenticated_client):
        """Cleanup test categories after tests"""
        yield
        # Delete test categories
        response = authenticated_client.get(f"{BASE_URL}/api/config/categories")
        if response.status_code == 200:
            for cat in response.json():
                if cat.get("name", "").startswith("TEST_"):
                    authenticated_client.delete(f"{BASE_URL}/api/config/categories/{cat['id']}")
    
    def test_get_categories(self, authenticated_client):
        """Test getting all configuration categories"""
        response = authenticated_client.get(f"{BASE_URL}/api/config/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} categories")
    
    def test_get_categories_by_type(self, authenticated_client):
        """Test filtering categories by type"""
        response = authenticated_client.get(f"{BASE_URL}/api/config/categories?config_type=risk")
        assert response.status_code == 200
        data = response.json()
        for cat in data:
            assert cat.get("type") == "risk"
        print(f"✓ Filtered by type 'risk': {len(data)} categories")
    
    def test_create_category(self, authenticated_client):
        """Test creating a new category"""
        response = authenticated_client.post(f"{BASE_URL}/api/config/categories", json={
            "name": "TEST_Categoria Nueva",
            "type": "risk",
            "description": "Test category created by automated testing",
            "is_active": True
        })
        assert response.status_code == 200, f"Create category failed: {response.text}"
        data = response.json()
        assert data.get("name") == "TEST_Categoria Nueva"
        assert data.get("type") == "risk"
        assert "id" in data
        print(f"✓ Category created with ID: {data['id']}")
        return data["id"]
    
    def test_update_category(self, authenticated_client):
        """Test updating a category"""
        # First create a category
        create_response = authenticated_client.post(f"{BASE_URL}/api/config/categories", json={
            "name": "TEST_Categoria Update",
            "type": "epp",
            "description": "To be updated"
        })
        assert create_response.status_code == 200
        cat_id = create_response.json()["id"]
        
        # Update it
        update_response = authenticated_client.put(f"{BASE_URL}/api/config/categories/{cat_id}", json={
            "name": "TEST_Categoria Updated",
            "description": "Updated description"
        })
        assert update_response.status_code == 200
        print(f"✓ Category {cat_id} updated successfully")
    
    def test_delete_category(self, authenticated_client):
        """Test deleting a category"""
        # First create a category
        create_response = authenticated_client.post(f"{BASE_URL}/api/config/categories", json={
            "name": "TEST_Categoria Delete",
            "type": "incident"
        })
        assert create_response.status_code == 200
        cat_id = create_response.json()["id"]
        
        # Delete it
        delete_response = authenticated_client.delete(f"{BASE_URL}/api/config/categories/{cat_id}")
        assert delete_response.status_code == 200
        
        # Verify it's gone
        get_response = authenticated_client.get(f"{BASE_URL}/api/config/categories")
        categories = get_response.json()
        assert all(c["id"] != cat_id for c in categories)
        print(f"✓ Category {cat_id} deleted successfully")


class TestCostCenters:
    """Test cost centers CRUD"""
    
    @pytest.fixture(autouse=True)
    def cleanup_test_cost_centers(self, authenticated_client):
        """Cleanup test cost centers after tests"""
        yield
        # Delete test cost centers
        response = authenticated_client.get(f"{BASE_URL}/api/cost-centers")
        if response.status_code == 200:
            for cc in response.json():
                if cc.get("code", "").startswith("TEST-") or cc.get("name", "").startswith("TEST_"):
                    authenticated_client.delete(f"{BASE_URL}/api/cost-centers/{cc['id']}")
    
    def test_get_cost_centers(self, authenticated_client):
        """Test getting all cost centers"""
        response = authenticated_client.get(f"{BASE_URL}/api/cost-centers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} cost centers")
    
    def test_create_cost_center(self, authenticated_client):
        """Test creating a new cost center"""
        response = authenticated_client.post(f"{BASE_URL}/api/cost-centers", json={
            "code": "TEST-001",
            "name": "TEST_Centro de Costo 1",
            "description": "Test cost center from automated testing",
            "is_active": True
        })
        assert response.status_code == 200, f"Create cost center failed: {response.text}"
        data = response.json()
        assert data.get("code") == "TEST-001"
        assert data.get("name") == "TEST_Centro de Costo 1"
        assert "id" in data
        print(f"✓ Cost center created with ID: {data['id']}")
    
    def test_update_cost_center(self, authenticated_client):
        """Test updating a cost center"""
        # First create
        create_response = authenticated_client.post(f"{BASE_URL}/api/cost-centers", json={
            "code": "TEST-002",
            "name": "TEST_Centro Update"
        })
        assert create_response.status_code == 200
        cc_id = create_response.json()["id"]
        
        # Update
        update_response = authenticated_client.put(f"{BASE_URL}/api/cost-centers/{cc_id}", json={
            "name": "TEST_Centro Updated",
            "description": "Updated description"
        })
        assert update_response.status_code == 200
        print(f"✓ Cost center {cc_id} updated successfully")
    
    def test_delete_cost_center(self, authenticated_client):
        """Test deleting a cost center"""
        # First create
        create_response = authenticated_client.post(f"{BASE_URL}/api/cost-centers", json={
            "code": "TEST-003",
            "name": "TEST_Centro Delete"
        })
        assert create_response.status_code == 200
        cc_id = create_response.json()["id"]
        
        # Delete
        delete_response = authenticated_client.delete(f"{BASE_URL}/api/cost-centers/{cc_id}")
        assert delete_response.status_code == 200
        
        # Verify
        get_response = authenticated_client.get(f"{BASE_URL}/api/cost-centers")
        centers = get_response.json()
        assert all(c["id"] != cc_id for c in centers)
        print(f"✓ Cost center {cc_id} deleted successfully")


class TestDashboardStats:
    """Test dashboard statistics endpoint"""
    
    def test_dashboard_stats(self, authenticated_client):
        """Test dashboard stats endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields
        expected_fields = ["total_incidents", "open_incidents", "critical_findings", 
                          "scans_today", "total_scans", "pending_actions", "total_epp_cost"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Dashboard stats: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
