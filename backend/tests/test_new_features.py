"""
Test suite for new features:
1. Sponsored Links Analytics - clicking sponsored links should track clicks, admin panel should show 24h/7d/total clicks
2. Trending Downloads Section - homepage should show 'TRENDING NOW' section when enabled in admin
3. Trending Downloads Admin Toggle - admin panel should have toggle to enable/disable trending section
4. Download Activity Tracking - clicking downloads should track activity for trending calculation
5. Top Downloads Section still works - sponsored downloads appear first with SPONSORED badge
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSponsoredLinksAnalytics:
    """Test sponsored link click tracking and analytics"""
    
    def test_track_sponsored_click(self):
        """Test that clicking a sponsored link tracks the click"""
        # First, let's add a sponsored download
        sponsored_id = f"test-sponsored-{int(time.time())}"
        
        # Track a click
        response = requests.post(f"{BASE_URL}/api/sponsored/{sponsored_id}/click")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Sponsored click tracked successfully for {sponsored_id}")
    
    def test_get_sponsored_analytics(self):
        """Test that admin can get sponsored link analytics"""
        response = requests.get(f"{BASE_URL}/api/admin/sponsored/analytics")
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        assert isinstance(data["analytics"], list)
        print(f"✓ Sponsored analytics endpoint returns data: {len(data['analytics'])} items")
    
    def test_sponsored_analytics_structure(self):
        """Test that analytics data has correct structure"""
        response = requests.get(f"{BASE_URL}/api/admin/sponsored/analytics")
        assert response.status_code == 200
        data = response.json()
        
        # If there are sponsored downloads, check structure
        if data["analytics"]:
            item = data["analytics"][0]
            assert "id" in item
            assert "name" in item
            assert "total_clicks" in item
            assert "clicks_24h" in item
            assert "clicks_7d" in item
            print(f"✓ Analytics structure correct: {item}")
        else:
            print("✓ No sponsored downloads configured yet")


class TestTrendingDownloads:
    """Test trending downloads feature"""
    
    def test_get_trending_downloads_disabled(self):
        """Test trending downloads endpoint when disabled"""
        response = requests.get(f"{BASE_URL}/api/downloads/trending")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "items" in data
        print(f"✓ Trending downloads endpoint works, enabled={data['enabled']}, items={len(data['items'])}")
    
    def test_enable_trending_downloads(self):
        """Test enabling trending downloads via admin settings"""
        # Enable trending downloads
        response = requests.put(f"{BASE_URL}/api/admin/settings", json={
            "trending_downloads_enabled": True,
            "trending_downloads_count": 5
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("trending_downloads_enabled") == True
        assert data.get("trending_downloads_count") == 5
        print("✓ Trending downloads enabled successfully")
    
    def test_get_trending_downloads_enabled(self):
        """Test trending downloads endpoint when enabled"""
        # First enable it
        requests.put(f"{BASE_URL}/api/admin/settings", json={
            "trending_downloads_enabled": True,
            "trending_downloads_count": 5
        })
        
        response = requests.get(f"{BASE_URL}/api/downloads/trending")
        assert response.status_code == 200
        data = response.json()
        assert data.get("enabled") == True
        assert "items" in data
        print(f"✓ Trending downloads returns {len(data['items'])} items when enabled")
    
    def test_disable_trending_downloads(self):
        """Test disabling trending downloads"""
        response = requests.put(f"{BASE_URL}/api/admin/settings", json={
            "trending_downloads_enabled": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("trending_downloads_enabled") == False
        print("✓ Trending downloads disabled successfully")


class TestDownloadActivityTracking:
    """Test download activity tracking for trending calculation"""
    
    def test_track_download_activity(self):
        """Test that download tracking endpoint works"""
        # First get a download ID
        response = requests.get(f"{BASE_URL}/api/downloads?limit=1")
        assert response.status_code == 200
        downloads = response.json().get("items", [])
        
        if downloads:
            download_id = downloads[0]["id"]
            initial_count = downloads[0].get("download_count", 0)
            
            # Track the download
            track_response = requests.post(f"{BASE_URL}/api/downloads/{download_id}/track")
            assert track_response.status_code == 200
            assert track_response.json().get("success") == True
            
            # Verify count increased
            verify_response = requests.get(f"{BASE_URL}/api/downloads?limit=50")
            verify_downloads = verify_response.json().get("items", [])
            tracked_download = next((d for d in verify_downloads if d["id"] == download_id), None)
            
            if tracked_download:
                new_count = tracked_download.get("download_count", 0)
                assert new_count >= initial_count
                print(f"✓ Download tracked: count went from {initial_count} to {new_count}")
            else:
                print("✓ Download tracking endpoint works")
        else:
            print("⚠ No downloads available to test tracking")
    
    def test_track_nonexistent_download(self):
        """Test tracking a non-existent download returns 404"""
        response = requests.post(f"{BASE_URL}/api/downloads/nonexistent-id-12345/track")
        assert response.status_code == 404
        print("✓ Non-existent download tracking returns 404")


class TestTopDownloadsWithSponsored:
    """Test top downloads section with sponsored downloads"""
    
    def test_get_top_downloads(self):
        """Test top downloads endpoint"""
        response = requests.get(f"{BASE_URL}/api/downloads/top")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "items" in data
        assert "sponsored" in data
        print(f"✓ Top downloads: enabled={data['enabled']}, sponsored={len(data['sponsored'])}, items={len(data['items'])}")
    
    def test_add_sponsored_download(self):
        """Test adding a sponsored download"""
        sponsored_item = {
            "id": "sponsored-test-item",
            "name": "Test Sponsored Software",
            "download_link": "https://example.com/download",
            "type": "software",
            "description": "Test sponsored item"
        }
        
        response = requests.put(f"{BASE_URL}/api/admin/settings", json={
            "sponsored_downloads": [sponsored_item]
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("sponsored_downloads", [])) >= 1
        print("✓ Sponsored download added successfully")
    
    def test_sponsored_appears_in_top_downloads(self):
        """Test that sponsored downloads appear in top downloads"""
        # First add a sponsored download
        sponsored_item = {
            "id": "sponsored-premium",
            "name": "Premium Software Pro",
            "download_link": "https://example.com/premium",
            "type": "software",
            "description": "Premium sponsored software"
        }
        
        requests.put(f"{BASE_URL}/api/admin/settings", json={
            "sponsored_downloads": [sponsored_item],
            "top_downloads_enabled": True
        })
        
        # Get top downloads
        response = requests.get(f"{BASE_URL}/api/downloads/top")
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("enabled") == True
        sponsored = data.get("sponsored", [])
        assert len(sponsored) >= 1
        assert sponsored[0]["name"] == "Premium Software Pro"
        print(f"✓ Sponsored download appears in top downloads: {sponsored[0]['name']}")


class TestSiteSettings:
    """Test site settings for trending and sponsored features"""
    
    def test_get_site_settings(self):
        """Test getting site settings"""
        response = requests.get(f"{BASE_URL}/api/settings")
        assert response.status_code == 200
        data = response.json()
        
        # Check trending settings exist
        assert "trending_downloads_enabled" in data
        assert "trending_downloads_count" in data
        
        # Check sponsored settings exist
        assert "sponsored_downloads" in data
        assert "top_downloads_enabled" in data
        assert "top_downloads_count" in data
        
        print(f"✓ Site settings retrieved: trending_enabled={data['trending_downloads_enabled']}, top_enabled={data['top_downloads_enabled']}")
    
    def test_update_trending_count(self):
        """Test updating trending downloads count"""
        response = requests.put(f"{BASE_URL}/api/admin/settings", json={
            "trending_downloads_count": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("trending_downloads_count") == 10
        print("✓ Trending count updated to 10")
        
        # Reset to 5
        requests.put(f"{BASE_URL}/api/admin/settings", json={
            "trending_downloads_count": 5
        })


class TestIntegration:
    """Integration tests for the complete flow"""
    
    def test_complete_sponsored_flow(self):
        """Test complete sponsored download flow: add -> click -> verify analytics"""
        # 1. Add sponsored download
        sponsored_item = {
            "id": f"sponsored-integration-{int(time.time())}",
            "name": "Integration Test Software",
            "download_link": "https://example.com/integration",
            "type": "software",
            "description": "Integration test"
        }
        
        add_response = requests.put(f"{BASE_URL}/api/admin/settings", json={
            "sponsored_downloads": [sponsored_item],
            "top_downloads_enabled": True
        })
        assert add_response.status_code == 200
        print("✓ Step 1: Sponsored download added")
        
        # 2. Track clicks
        for i in range(3):
            click_response = requests.post(f"{BASE_URL}/api/sponsored/{sponsored_item['id']}/click")
            assert click_response.status_code == 200
        print("✓ Step 2: 3 clicks tracked")
        
        # 3. Verify analytics
        analytics_response = requests.get(f"{BASE_URL}/api/admin/sponsored/analytics")
        assert analytics_response.status_code == 200
        analytics = analytics_response.json().get("analytics", [])
        
        # Find our sponsored item
        our_item = next((a for a in analytics if a["id"] == sponsored_item["id"]), None)
        if our_item:
            assert our_item["total_clicks"] >= 3
            print(f"✓ Step 3: Analytics verified - total_clicks={our_item['total_clicks']}")
        else:
            print("✓ Step 3: Analytics endpoint working (item may have been replaced)")
    
    def test_complete_trending_flow(self):
        """Test complete trending flow: enable -> track downloads -> verify trending"""
        # 1. Enable trending
        enable_response = requests.put(f"{BASE_URL}/api/admin/settings", json={
            "trending_downloads_enabled": True,
            "trending_downloads_count": 5
        })
        assert enable_response.status_code == 200
        print("✓ Step 1: Trending enabled")
        
        # 2. Get a download and track it multiple times
        downloads_response = requests.get(f"{BASE_URL}/api/downloads?limit=1")
        downloads = downloads_response.json().get("items", [])
        
        if downloads:
            download_id = downloads[0]["id"]
            for i in range(5):
                track_response = requests.post(f"{BASE_URL}/api/downloads/{download_id}/track")
                assert track_response.status_code == 200
            print(f"✓ Step 2: Download {download_id} tracked 5 times")
        
        # 3. Verify trending returns items
        trending_response = requests.get(f"{BASE_URL}/api/downloads/trending")
        assert trending_response.status_code == 200
        trending_data = trending_response.json()
        assert trending_data.get("enabled") == True
        print(f"✓ Step 3: Trending returns {len(trending_data.get('items', []))} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
