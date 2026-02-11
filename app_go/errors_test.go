package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

// TestMainHandler404 tests 404 responses and error handling for non-existent endpoints.
func TestMainHandler404(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(mainHandler))
	defer server.Close()

	resp, err := http.Get(server.URL + "/nonexistent")
	if err != nil {
		t.Fatalf("Failed to make request: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusNotFound {
		t.Errorf("Expected status 404, got %d", resp.StatusCode)
	}
}
