"""
Unit tests for error handling.
Tests cover 404 responses and error response structure.
"""
import pytest


class TestErrorHandling:
    """Test suite for error handling."""

    def test_404_endpoint(self, client):
        """Test that non-existent endpoint returns 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert data["error"] == "Not Found"

    def test_404_error_structure(self, client):
        """Test 404 error response structure."""
        response = client.get("/invalid/path")
        assert response.status_code == 404
        
        data = response.json()
        assert isinstance(data["error"], str)
        assert isinstance(data["message"], str)

    def test_404_multiple_paths(self, client):
        """Test 404 for various invalid paths."""
        invalid_paths = ["/api", "/v1", "/test", "/unknown/endpoint"]
        
        for path in invalid_paths:
            response = client.get(path)
            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "Not Found"
