"""
Comprehensive API tests for refactored Download Portal backend
Tests all endpoints after refactoring from monolithic server.py to modular routers
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestRootAndHealth:
    """Root endpoint and health check tests"""
    
    def test_root_endpoint(self):
        """Test root API endpoint returns correct message"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Download Portal API"


class TestDownloadsEndpoints:
    """Tests for /api/downloads endpoints"""
    
    def test_get_downloads_basic(self):
        """Test GET /api/downloads returns paginated results"""
        response = requests.get(f"{BASE_URL}/api/downloads?page=1&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        assert data["page"] == 1
        assert len(data["items"]) <= 5
    
    def test_get_downloads_pagination(self):
        """Test pagination works correctly"""
        response1 = requests.get(f"{BASE_URL}/api/downloads?page=1&limit=3")
        response2 = requests.get(f"{BASE_URL}/api/downloads?page=2&limit=3")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Pages should have different items
        if data1["total"] > 3:
            ids1 = [item["id"] for item in data1["items"]]
            ids2 = [item["id"] for item in data2["items"]]
            # No overlap between pages
            assert not set(ids1).intersection(set(ids2))
    
    def test_get_downloads_type_filter(self):
        """Test type_filter parameter"""
        response = requests.get(f"{BASE_URL}/api/downloads?type_filter=game&limit=5")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["type"] == "game"
    
    def test_get_downloads_search(self):
        """Test search parameter"""
        response = requests.get(f"{BASE_URL}/api/downloads?search=VLC&limit=5")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert "VLC" in item["name"].upper() or "vlc" in item["name"].lower()
    
    def test_get_downloads_sort_by_downloads(self):
        """Test sorting by download count"""
        response = requests.get(f"{BASE_URL}/api/downloads?sort_by=downloads_desc&limit=5")
        assert response.status_code == 200
        data = response.json()
        if len(data["items"]) > 1:
            counts = [item["download_count"] for item in data["items"]]
            assert counts == sorted(counts, reverse=True)
    
    def test_get_downloads_sort_by_name(self):
        """Test sorting by name"""
        response = requests.get(f"{BASE_URL}/api/downloads?sort_by=name_asc&limit=5")
        assert response.status_code == 200
        data = response.json()
        if len(data["items"]) > 1:
            names = [item["name"].lower() for item in data["items"]]
            assert names == sorted(names)


class TestTopDownloads:
    """Tests for /api/downloads/top endpoint"""
    
    def test_get_top_downloads(self):
        """Test GET /api/downloads/top returns top downloads with sponsored"""
        response = requests.get(f"{BASE_URL}/api/downloads/top")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "items" in data
        assert "sponsored" in data
        assert "total_slots" in data
    
    def test_top_downloads_structure(self):
        """Test top downloads response structure"""
        response = requests.get(f"{BASE_URL}/api/downloads/top")
        assert response.status_code == 200
        data = response.json()
        if data["enabled"] and data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "name" in item
            assert "download_link" in item
            assert "type" in item


class TestTrendingDownloads:
    """Tests for /api/downloads/trending endpoint"""
    
    def test_get_trending_downloads(self):
        """Test GET /api/downloads/trending returns trending items"""
        response = requests.get(f"{BASE_URL}/api/downloads/trending")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "items" in data
    
    def test_trending_downloads_structure(self):
        """Test trending downloads response structure"""
        response = requests.get(f"{BASE_URL}/api/downloads/trending")
        assert response.status_code == 200
        data = response.json()
        if data["enabled"] and data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "name" in item
            assert "download_link" in item


class TestTrackDownload:
    """Tests for /api/downloads/{id}/track endpoint"""
    
    def test_track_download_success(self):
        """Test POST /api/downloads/{id}/track increments count"""
        # First get a valid download ID
        response = requests.get(f"{BASE_URL}/api/downloads?limit=1")
        assert response.status_code == 200
        data = response.json()
        if data["items"]:
            download_id = data["items"][0]["id"]
            
            # Track the download
            track_response = requests.post(f"{BASE_URL}/api/downloads/{download_id}/track")
            assert track_response.status_code == 200
            track_data = track_response.json()
            assert track_data["success"] == True
    
    def test_track_download_not_found(self):
        """Test tracking non-existent download returns 404"""
        response = requests.post(f"{BASE_URL}/api/downloads/non-existent-id/track")
        assert response.status_code == 404


class TestSponsoredClick:
    """Tests for /api/sponsored/{id}/click endpoint"""
    
    def test_track_sponsored_click(self):
        """Test POST /api/sponsored/{id}/click tracks click"""
        response = requests.post(f"{BASE_URL}/api/sponsored/sponsored-premium/click")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


class TestCaptcha:
    """Tests for /api/captcha endpoint"""
    
    def test_generate_captcha(self):
        """Test GET /api/captcha generates a captcha challenge"""
        response = requests.get(f"{BASE_URL}/api/captcha")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "challenge" in data
        assert "expires_at" in data
        # Challenge should be a math problem
        assert "=" in data["challenge"]


class TestSubmissionsRemaining:
    """Tests for /api/submissions/remaining endpoint"""
    
    def test_get_remaining_submissions(self):
        """Test GET /api/submissions/remaining returns rate limit info"""
        response = requests.get(f"{BASE_URL}/api/submissions/remaining")
        assert response.status_code == 200
        data = response.json()
        assert "daily_limit" in data
        assert "used" in data
        assert "remaining" in data
        assert data["remaining"] == data["daily_limit"] - data["used"]


class TestAdminLogin:
    """Tests for /api/admin/login endpoint"""
    
    def test_admin_login_success(self):
        """Test POST /api/admin/login with correct password"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["message"] == "Access granted"
    
    def test_admin_login_failure(self):
        """Test POST /api/admin/login with wrong password"""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"password": "wrongpassword"}
        )
        assert response.status_code == 401


class TestAdminSubmissions:
    """Tests for /api/admin/submissions endpoints"""
    
    def test_get_admin_submissions(self):
        """Test GET /api/admin/submissions returns paginated submissions"""
        response = requests.get(f"{BASE_URL}/api/admin/submissions?page=1&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
    
    def test_get_admin_submissions_status_filter(self):
        """Test GET /api/admin/submissions with status filter"""
        for status in ["pending", "approved", "rejected"]:
            response = requests.get(f"{BASE_URL}/api/admin/submissions?status={status}&limit=5")
            assert response.status_code == 200
            data = response.json()
            for item in data["items"]:
                assert item["status"] == status


class TestSponsoredAnalytics:
    """Tests for /api/admin/sponsored/analytics endpoint"""
    
    def test_get_sponsored_analytics(self):
        """Test GET /api/admin/sponsored/analytics returns click data"""
        response = requests.get(f"{BASE_URL}/api/admin/sponsored/analytics")
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        if data["analytics"]:
            item = data["analytics"][0]
            assert "id" in item
            assert "name" in item
            assert "total_clicks" in item
            assert "clicks_24h" in item
            assert "clicks_7d" in item


class TestTheme:
    """Tests for /api/theme endpoints"""
    
    def test_get_theme(self):
        """Test GET /api/theme returns theme settings"""
        response = requests.get(f"{BASE_URL}/api/theme")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "mode" in data
        assert "accent_color" in data
    
    def test_update_theme(self):
        """Test PUT /api/theme updates theme settings"""
        # Get current theme
        get_response = requests.get(f"{BASE_URL}/api/theme")
        original_theme = get_response.json()
        
        # Update theme
        new_color = "#FF0000" if original_theme["accent_color"] != "#FF0000" else "#00FF41"
        update_response = requests.put(
            f"{BASE_URL}/api/theme",
            json={"accent_color": new_color}
        )
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["accent_color"] == new_color
        
        # Restore original
        requests.put(
            f"{BASE_URL}/api/theme",
            json={"accent_color": original_theme["accent_color"]}
        )


class TestSettings:
    """Tests for /api/settings endpoint"""
    
    def test_get_settings(self):
        """Test GET /api/settings returns public site settings"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        data = response.json()
        # Should have public settings
        assert "daily_submission_limit" in data
        assert "top_downloads_enabled" in data
        assert "site_name" in data
        # Should NOT have sensitive data
        assert "resend_api_key" not in data or data.get("resend_api_key") is None
        assert "recaptcha_secret_key" not in data or data.get("recaptcha_secret_key") is None
        assert "admin_password_hash" not in data or data.get("admin_password_hash") is None


class TestStats:
    """Tests for /api/stats endpoint"""
    
    def test_get_stats(self):
        """Test GET /api/stats returns download statistics"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "games" in data
        assert "software" in data
        assert "movies" in data
        assert "tv_shows" in data
        assert "total_downloads" in data
        # Verify counts are non-negative
        assert data["total"] >= 0
        assert data["games"] >= 0
        assert data["software"] >= 0
        assert data["movies"] >= 0
        assert data["tv_shows"] >= 0


class TestCategories:
    """Tests for /api/categories endpoint"""
    
    def test_get_categories(self):
        """Test GET /api/categories returns all categories"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            category = data[0]
            assert "id" in category
            assert "name" in category
            assert "type" in category
    
    def test_get_categories_type_filter(self):
        """Test GET /api/categories with type filter"""
        response = requests.get(f"{BASE_URL}/api/categories?type_filter=game")
        assert response.status_code == 200
        data = response.json()
        for category in data:
            assert category["type"] in ["game", "all"]


class TestApproveRejectSubmission:
    """Tests for approve/reject submission endpoints"""
    
    def test_approve_submission_not_found(self):
        """Test approving non-existent submission returns 404"""
        response = requests.post(f"{BASE_URL}/api/admin/submissions/non-existent-id/approve")
        assert response.status_code == 404
    
    def test_reject_submission_not_found(self):
        """Test rejecting non-existent submission returns 404"""
        response = requests.post(f"{BASE_URL}/api/admin/submissions/non-existent-id/reject")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
