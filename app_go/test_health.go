package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

// Tests cover GET /health endpoint - status, timestamp, and uptime validation.
func TestHealthHandler(t *testing.T) {
	// Create a test server
	server := httptest.NewServer(http.HandlerFunc(healthHandler))
	defer server.Close()

	// Make request to health endpoint
	resp, err := http.Get(server.URL + "/health")
	if err != nil {
		t.Fatalf("Failed to make request: %v", err)
	}
	defer resp.Body.Close()

	// Check status code
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	// Check content type
	contentType := resp.Header.Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("Expected Content-Type application/json, got %s", contentType)
	}

	// Parse response
	var response HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Validate health response
	if response.Status != "healthy" {
		t.Errorf("Expected status 'healthy', got '%s'", response.Status)
	}
	if response.UptimeSeconds < 0 {
		t.Error("UptimeSeconds should be non-negative")
	}
	if response.Timestamp == "" {
		t.Error("Timestamp should not be empty")
	}
}

func TestHealthHandlerMultipleRequests(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(healthHandler))
	defer server.Close()

	// Make multiple requests to verify handler works consistently
	for i := 0; i < 3; i++ {
		resp, err := http.Get(server.URL + "/health")
		if err != nil {
			t.Fatalf("Failed to make request %d: %v", i+1, err)
		}
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusOK {
			t.Errorf("Request %d: Expected status 200, got %d", i+1, resp.StatusCode)
		}

		var response HealthResponse
		if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
			t.Fatalf("Failed to decode response %d: %v", i+1, err)
		}

		// Verify response is valid
		if response.Status != "healthy" {
			t.Errorf("Request %d: Expected status 'healthy', got '%s'", i+1, response.Status)
		}
		if response.UptimeSeconds < 0 {
			t.Errorf("Request %d: UptimeSeconds should be non-negative, got %d", i+1, response.UptimeSeconds)
		}
		if response.Timestamp == "" {
			t.Errorf("Request %d: Timestamp should not be empty", i+1)
		}
	}
}
