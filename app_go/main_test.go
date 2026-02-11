package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func setupServer() *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("/", mainHandler)
	mux.HandleFunc("/health", healthHandler)
	return mux
}

func TestHealthEndpoint(t *testing.T) {
	server := httptest.NewServer(setupServer())
	defer server.Close()

	resp, err := http.Get(server.URL + "/health")
	if err != nil {
		t.Fatalf("Failed to make request: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	var data map[string]interface{}
	err = json.NewDecoder(resp.Body).Decode(&data)
	if err != nil {
		t.Fatalf("Invalid JSON response")
	}

	if data["status"] != "healthy" {
		t.Errorf("Expected status 'healthy'")
	}

	if data["uptime_seconds"] == nil {
		t.Errorf("Missing uptime_seconds")
	}
}

func TestMainEndpoint(t *testing.T) {
	server := httptest.NewServer(setupServer())
	defer server.Close()

	req, _ := http.NewRequest(http.MethodGet, server.URL+"/", nil)
	req.Header.Set("User-Agent", "test-agent")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("Request failed: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	var data map[string]interface{}
	err = json.NewDecoder(resp.Body).Decode(&data)
	if err != nil {
		t.Fatalf("Invalid JSON")
	}

	requiredBlocks := []string{
		"service",
		"system",
		"runtime",
		"request",
		"endpoints",
	}

	for _, block := range requiredBlocks {
		if data[block] == nil {
			t.Errorf("Missing block: %s", block)
		}
	}
}
