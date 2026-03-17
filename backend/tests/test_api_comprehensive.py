"""
Comprehensive Backend API Tests for SmartSafety+ Platform
Tests: Auth, Dashboard, Procedures, Risk Matrix, EPP, Incidents
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@smartsafety.com"
ADMIN_PASSWORD = "Admin123!"
SUPERADMIN_EMAIL = "superadmin@smartsafety.com"
SUPERADMIN_PASSWORD = "Admin123!"


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
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def superadmin_token(api_client):
    """Get superadmin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPERADMIN_EMAIL,
        "password": SUPERADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Superadmin authentication failed")


@pytest.fixture(scope="module")
def authenticated_client(api_client, admin_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return api_client


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_admin_login_success(self, api_client):
        """Test admin login with valid credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
    
    def test_superadmin_login_success(self, api_client):
        """Test superadmin login with valid credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPERADMIN_EMAIL,
            "password": SUPERADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "superadmin"
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_get_current_user(self, authenticated_client, admin_token):
        """Test getting current user profile"""
        response = authenticated_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL


class TestDashboard:
    """Dashboard statistics and charts tests"""
    
    def test_dashboard_stats(self, authenticated_client):
        """Test dashboard statistics endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_incidents" in data
        assert "open_incidents" in data
        assert "critical_findings" in data
        assert "scans_today" in data
        assert "total_scans" in data
        assert "pending_actions" in data
        assert "total_epp_cost" in data
    
    def test_recent_activity(self, authenticated_client):
        """Test dashboard recent activity endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/recent-activity")
        assert response.status_code == 200
        data = response.json()
        assert "incidents" in data
        assert "scans" in data
        assert "findings" in data
    
    def test_dashboard_charts(self, authenticated_client):
        """Test dashboard charts data endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/charts")
        assert response.status_code == 200
        data = response.json()
        assert "incidents_by_severity" in data
        assert "findings_by_category" in data
        assert "epp_costs_by_center" in data


class TestProcedures:
    """Procedures CRUD tests"""
    
    def test_get_procedures_list(self, authenticated_client):
        """Test getting procedures list"""
        response = authenticated_client.get(f"{BASE_URL}/api/procedures")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_nonexistent_procedure(self, authenticated_client):
        """Test getting a procedure that doesn't exist"""
        response = authenticated_client.get(f"{BASE_URL}/api/procedures/nonexistent-id")
        assert response.status_code == 404


class TestRiskMatrix:
    """Risk Matrix CRUD tests"""
    
    def test_get_risk_matrices_list(self, authenticated_client):
        """Test getting risk matrices list"""
        response = authenticated_client.get(f"{BASE_URL}/api/risk-matrix")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_risk_matrix(self, authenticated_client):
        """Test creating a new risk matrix"""
        params = {
            "name": "TEST_Risk Matrix - Area Norte",
            "area": "Producción",
            "process": "Soldadura",
            "description": "Test matrix for automated testing"
        }
        response = authenticated_client.post(
            f"{BASE_URL}/api/risk-matrix",
            params=params
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Risk Matrix - Area Norte"
        assert data["area"] == "Producción"
        assert data["process"] == "Soldadura"
        assert "id" in data
        return data["id"]
    
    def test_create_and_view_risk_matrix(self, authenticated_client):
        """Test creating and viewing a risk matrix"""
        # Create
        params = {
            "name": "TEST_Matrix Verificacion",
            "area": "Almacen",
            "process": "Logistica"
        }
        create_response = authenticated_client.post(
            f"{BASE_URL}/api/risk-matrix",
            params=params
        )
        assert create_response.status_code == 200
        matrix_id = create_response.json()["id"]
        
        # View
        get_response = authenticated_client.get(f"{BASE_URL}/api/risk-matrix/{matrix_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["name"] == "TEST_Matrix Verificacion"
    
    def test_get_nonexistent_matrix(self, authenticated_client):
        """Test getting a matrix that doesn't exist"""
        response = authenticated_client.get(f"{BASE_URL}/api/risk-matrix/nonexistent-id")
        assert response.status_code == 404


class TestEPP:
    """EPP Management tests"""
    
    def test_get_epp_items(self, authenticated_client):
        """Test getting EPP items list"""
        response = authenticated_client.get(f"{BASE_URL}/api/epp/items")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_epp_stock(self, authenticated_client):
        """Test getting EPP stock"""
        response = authenticated_client.get(f"{BASE_URL}/api/epp/stock")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_epp_movements(self, authenticated_client):
        """Test getting EPP movements"""
        response = authenticated_client.get(f"{BASE_URL}/api/epp/movements")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_epp_deliveries(self, authenticated_client):
        """Test getting EPP deliveries"""
        response = authenticated_client.get(f"{BASE_URL}/api/epp/deliveries")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestIncidents:
    """Incidents management tests"""
    
    def test_get_incidents_list(self, authenticated_client):
        """Test getting incidents list"""
        response = authenticated_client.get(f"{BASE_URL}/api/incidents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_incidents_stats(self, authenticated_client):
        """Test getting incident statistics"""
        response = authenticated_client.get(f"{BASE_URL}/api/incidents/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "open" in data
        assert "critical" in data
    
    def test_create_incident(self, authenticated_client):
        """Test creating a new incident"""
        incident_data = {
            "title": "TEST_Incident - Caida de material",
            "description": "Material caído en área de producción durante prueba automatizada",
            "severity": "medio",
            "category": "Orden y Aseo",
            "location": "Planta Norte - Sector A"
        }
        response = authenticated_client.post(
            f"{BASE_URL}/api/incidents",
            json=incident_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "TEST_Incident - Caida de material"
        assert data["severity"] == "medio"
        assert "id" in data


class TestScan360:
    """Scan 360 tests"""
    
    def test_get_scans_list(self, authenticated_client):
        """Test getting scans list"""
        response = authenticated_client.get(f"{BASE_URL}/api/scans")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_findings_list(self, authenticated_client):
        """Test getting findings list"""
        response = authenticated_client.get(f"{BASE_URL}/api/findings")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestNotifications:
    """Notifications tests"""
    
    def test_get_notifications(self, authenticated_client):
        """Test getting notifications"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestReports:
    """Reports export tests"""
    
    def test_export_incidents_report(self, authenticated_client):
        """Test exporting incidents report"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/reports/export-pdf",
            params={"report_type": "incidents"}
        )
        assert response.status_code == 200
    
    def test_export_risk_matrix_report(self, authenticated_client):
        """Test exporting risk matrix report"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/reports/export-pdf",
            params={"report_type": "risk-matrix"}
        )
        assert response.status_code == 200


class TestCostCenters:
    """Cost Centers tests"""
    
    def test_get_cost_centers(self, authenticated_client):
        """Test getting cost centers list"""
        response = authenticated_client.get(f"{BASE_URL}/api/cost-centers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestConfiguration:
    """Configuration categories tests"""
    
    def test_get_config_categories(self, authenticated_client):
        """Test getting configuration categories"""
        response = authenticated_client.get(f"{BASE_URL}/api/config/categories")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestUsersManagement:
    """Users management tests (admin only)"""
    
    def test_get_users_list(self, authenticated_client):
        """Test getting users list with admin credentials"""
        response = authenticated_client.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# Cleanup test data
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data(authenticated_client, admin_token):
    """Cleanup TEST_ prefixed data after tests"""
    yield
    # Note: Cleanup would be implemented here for production
    # For testing purposes, we leave test data for verification
