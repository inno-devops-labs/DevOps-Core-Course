package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

// Tests cover 404 responses and error handling.
func TestMainHandler404(t *testing.T) {
	// Create a test server
	server := httptest.NewServer(http.HandlerFunc(mainHandler))
	defer server.Close()

	// Make request to non-existent endpoint
	resp, err := http.Get(server.URL + "/nonexistent")
	if err != nil {
		t.Fatalf("Failed to make request: %v", err)
	}
	defer resp.Body.Close()

	// Check status code (should be 404)
	if resp.StatusCode != http.StatusNotFound {
		t.Errorf("Expected status 404, got %d", resp.StatusCode)
	}
}
