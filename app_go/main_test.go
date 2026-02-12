package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	rr := httptest.NewRecorder()

	healthHandler(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}

	var data HealthResponse
	if err := json.Unmarshal(rr.Body.Bytes(), &data); err != nil {
		t.Fatalf("invalid json: %v", err)
	}

	if data.Status != "healthy" {
		t.Fatalf("expected healthy, got %s", data.Status)
	}
	if data.UptimeSeconds < 0 {
		t.Fatalf("expected uptime >= 0")
	}
}

func TestRootHandler(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("User-Agent", "go-test")
	rr := httptest.NewRecorder()

	rootHandler(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}

	var data RootResponse
	if err := json.Unmarshal(rr.Body.Bytes(), &data); err != nil {
		t.Fatalf("invalid json: %v", err)
	}

	if data.Service.Name != "devops-info-service" {
		t.Fatalf("unexpected service name: %s", data.Service.Name)
	}
	if data.Request.Path != "/" {
		t.Fatalf("expected path '/', got %s", data.Request.Path)
	}
}