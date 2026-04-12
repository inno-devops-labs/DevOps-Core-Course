package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealthEndpoint(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	healthHandler(w, req)

	res := w.Result()
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		t.Fatalf("expected status 200, got %d", res.StatusCode)
	}

	var data map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&data); err != nil {
		t.Fatalf("failed to decode json: %v", err)
	}

	if data["status"] != "healthy" {
		t.Fatalf("expected status 'healthy', got %v", data["status"])
	}

	if _, ok := data["timestamp"]; !ok {
		t.Fatal("missing 'timestamp'")
	}

	if _, ok := data["uptime_seconds"]; !ok {
		t.Fatal("missing 'uptime_seconds'")
	}
}
