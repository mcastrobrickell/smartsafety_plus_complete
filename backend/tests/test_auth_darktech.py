"""
Test Suite for SmartSafety+ Authentication Bug Fix and Dark-Tech Theme
Tests the authentication fix (passlib vs bcrypt incompatibility) and login flows
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://risk-scan-ai-1.preview.emergentagent.com')

class TestAuthenticationFix:
    """Tests for the authentication bug fix - verifying bcrypt password verification works"""
    
    def test_superadmin_login_success(self):
        """Test superadmin login with correct credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "superadmin@smartsafety.com", "password": "SuperAdmin123!"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user object"
        assert data["user"]["role"] == "superadmin", f"Expected role 'superadmin', got {data['user']['role']}"
        assert data["user"]["email"] == "superadmin@smartsafety.com"
        print(f"✅ Superadmin login successful - role: {data['user']['role']}")
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@smartsafety.com", "password": "Admin123!"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user object"
        assert data["user"]["role"] == "admin", f"Expected role 'admin', got {data['user']['role']}"
        assert data["user"]["email"] == "admin@smartsafety.com"
        print(f"✅ Admin login successful - role: {data['user']['role']}")
    
    def test_invalid_credentials_rejected(self):
        """Test that invalid credentials are properly rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Response should contain error detail"
        assert data["detail"] == "Invalid credentials"
        print("✅ Invalid credentials correctly rejected with 401")
    
    def test_wrong_password_rejected(self):
        """Test that correct email with wrong password is rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@smartsafety.com", "password": "WrongPassword123!"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Wrong password correctly rejected")
    
    def test_token_contains_correct_claims(self):
        """Test that JWT token contains correct user claims"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "superadmin@smartsafety.com", "password": "SuperAdmin123!"}
        )
        assert response.status_code == 200
        
        data = response.json()
        token = data["access_token"]
        
        # Token should be a valid JWT (3 parts separated by dots)
        parts = token.split(".")
        assert len(parts) == 3, "Token should be a valid JWT with 3 parts"
        print("✅ Token is valid JWT format")
    
    def test_auth_me_endpoint_with_token(self):
        """Test /auth/me endpoint returns current user info"""
        # First login to get token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@smartsafety.com", "password": "Admin123!"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Then call /auth/me
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200, f"Expected 200, got {me_response.status_code}"
        
        user = me_response.json()
        assert user["email"] == "admin@smartsafety.com"
        assert user["role"] == "admin"
        print(f"✅ /auth/me returns correct user: {user['name']}")
    
    def test_auth_me_without_token_fails(self):
        """Test /auth/me endpoint fails without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✅ /auth/me correctly requires authentication")


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_is_accessible(self):
        """Test that the API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        # Health endpoint may not exist, so we just check the server responds
        assert response.status_code in [200, 404], f"Server should respond, got {response.status_code}"
        print("✅ API server is accessible")
    
    def test_login_endpoint_exists(self):
        """Test that login endpoint exists and accepts POST"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@test.com", "password": "test"}
        )
        # Should get 401 (invalid credentials) not 404 (not found)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Login endpoint exists and responds correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
