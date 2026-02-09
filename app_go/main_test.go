package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRootOK(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	rr := httptest.NewRecorder()

	mainHandler(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}

	var data map[string]any
	if err := json.Unmarshal(rr.Body.Bytes(), &data); err != nil {
		t.Fatalf("invalid json: %v", err)
	}

	// top-level keys
	for _, k := range []string{"service", "system", "runtime", "request", "endpoints"} {
		if _, ok := data[k]; !ok {
			t.Fatalf("missing key: %s", k)
		}
	}
}

func TestHealthOK(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	rr := httptest.NewRecorder()

	healthHandler(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}

	var data map[string]any
	if err := json.Unmarshal(rr.Body.Bytes(), &data); err != nil {
		t.Fatalf("invalid json: %v", err)
	}

	for _, k := range []string{"status", "timestamp", "uptime_seconds"} {
		if _, ok := data[k]; !ok {
			t.Fatalf("missing key: %s", k)
		}
	}
	if data["status"] != "healthy" {
		t.Fatalf("expected status healthy, got %v", data["status"])
	}
}
