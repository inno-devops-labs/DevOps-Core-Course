package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestIndexHandler(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()

	indexHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", w.Code)
	}

	ct := w.Header().Get("Content-Type")
	if ct != "application/json" {
		t.Errorf("expected content-type application/json, got %s", ct)
	}

	var resp Response
	if err := json.NewDecoder(w.Body).Decode(&resp); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if resp.Service.Name != "DevOps Info Service (Go)" {
		t.Errorf("unexpected service name: %s", resp.Service.Name)
	}
	if resp.System.Hostname == "" {
		t.Error("hostname should not be empty")
	}
	if resp.Runtime.Timezone != "UTC" {
		t.Errorf("expected timezone UTC, got %s", resp.Runtime.Timezone)
	}
	if resp.Runtime.UptimeSeconds < 0 {
		t.Error("uptime should be non-negative")
	}
}

func TestIndexHandler404(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/nonexistent", nil)
	w := httptest.NewRecorder()

	indexHandler(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("expected status 404, got %d", w.Code)
	}
}

func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	healthHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", w.Code)
	}

	var resp HealthResponse
	if err := json.NewDecoder(w.Body).Decode(&resp); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if resp.Status != "healthy" {
		t.Errorf("expected status healthy, got %s", resp.Status)
	}
	if resp.Timestamp == "" {
		t.Error("timestamp should not be empty")
	}
	if resp.UptimeSeconds < 0 {
		t.Error("uptime should be non-negative")
	}
}
