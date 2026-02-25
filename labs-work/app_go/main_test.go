package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestMainHandler_ReturnsOK(t *testing.T) {
	req, err := http.NewRequest("GET", "/", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(mainHandler)
	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("mainHandler returned wrong status code: got %v want %v", status, http.StatusOK)
	}
}

func TestMainHandler_ReturnsJSON(t *testing.T) {
	req, err := http.NewRequest("GET", "/", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(mainHandler)
	handler.ServeHTTP(rr, req)

	contentType := rr.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("mainHandler returned wrong content type: got %v want %v", contentType, "application/json")
	}
}

func TestMainHandler_ContainsServiceInfo(t *testing.T) {
	req, err := http.NewRequest("GET", "/", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(mainHandler)
	handler.ServeHTTP(rr, req)

	var response MainResponse
	if err := json.NewDecoder(rr.Body).Decode(&response); err != nil {
		t.Errorf("failed to decode response body: %v", err)
	}

	if response.Service.Name != "devops-info-service" {
		t.Errorf("unexpected service name: got %v want %v", response.Service.Name, "devops-info-service")
	}

	if response.Service.Framework != "net/http" {
		t.Errorf("unexpected framework: got %v want %v", response.Service.Framework, "net/http")
	}
}

func TestMainHandler_ContainsSystemInfo(t *testing.T) {
	req, err := http.NewRequest("GET", "/", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(mainHandler)
	handler.ServeHTTP(rr, req)

	var response MainResponse
	if err := json.NewDecoder(rr.Body).Decode(&response); err != nil {
		t.Errorf("failed to decode response body: %v", err)
	}

	if response.System.Hostname == "" {
		t.Error("system hostname should not be empty")
	}

	if response.System.CPUCount <= 0 {
		t.Errorf("cpu count should be positive: got %v", response.System.CPUCount)
	}
}

func TestMainHandler_ContainsRuntimeInfo(t *testing.T) {
	req, err := http.NewRequest("GET", "/", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(mainHandler)
	handler.ServeHTTP(rr, req)

	var response MainResponse
	if err := json.NewDecoder(rr.Body).Decode(&response); err != nil {
		t.Errorf("failed to decode response body: %v", err)
	}

	if response.Runtime.Timezone != "UTC" {
		t.Errorf("unexpected timezone: got %v want %v", response.Runtime.Timezone, "UTC")
	}

	if response.Runtime.UptimeSeconds < 0 {
		t.Errorf("uptime should be non-negative: got %v", response.Runtime.UptimeSeconds)
	}
}

func TestMainHandler_ContainsEndpoints(t *testing.T) {
	req, err := http.NewRequest("GET", "/", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(mainHandler)
	handler.ServeHTTP(rr, req)

	var response MainResponse
	if err := json.NewDecoder(rr.Body).Decode(&response); err != nil {
		t.Errorf("failed to decode response body: %v", err)
	}

	if len(response.Endpoints) < 2 {
		t.Errorf("expected at least 2 endpoints, got %v", len(response.Endpoints))
	}
}

func TestHealthHandler_ReturnsOK(t *testing.T) {
	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(healthHandler)
	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("healthHandler returned wrong status code: got %v want %v", status, http.StatusOK)
	}
}

func TestHealthHandler_ReturnsJSON(t *testing.T) {
	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(healthHandler)
	handler.ServeHTTP(rr, req)

	contentType := rr.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("healthHandler returned wrong content type: got %v want %v", contentType, "application/json")
	}
}

func TestHealthHandler_StatusIsHealthy(t *testing.T) {
	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(healthHandler)
	handler.ServeHTTP(rr, req)

	var response HealthResponse
	if err := json.NewDecoder(rr.Body).Decode(&response); err != nil {
		t.Errorf("failed to decode response body: %v", err)
	}

	if response.Status != "healthy" {
		t.Errorf("unexpected health status: got %v want %v", response.Status, "healthy")
	}
}

func TestHealthHandler_UptimeIsNonNegative(t *testing.T) {
	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(healthHandler)
	handler.ServeHTTP(rr, req)

	var response HealthResponse
	if err := json.NewDecoder(rr.Body).Decode(&response); err != nil {
		t.Errorf("failed to decode response body: %v", err)
	}

	if response.UptimeSeconds < 0 {
		t.Errorf("uptime should be non-negative: got %v", response.UptimeSeconds)
	}
}

func TestMainHandler_Returns404ForInvalidPath(t *testing.T) {
	req, err := http.NewRequest("GET", "/nonexistent", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(mainHandler)
	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusNotFound {
		t.Errorf("mainHandler returned wrong status code for invalid path: got %v want %v", status, http.StatusNotFound)
	}
}

func TestNotFoundHandler_ReturnsJSON(t *testing.T) {
	req, err := http.NewRequest("GET", "/nonexistent", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(notFoundHandler)
	handler.ServeHTTP(rr, req)

	contentType := rr.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("notFoundHandler returned wrong content type: got %v want %v", contentType, "application/json")
	}
}

func TestNotFoundHandler_ContainsErrorInfo(t *testing.T) {
	req, err := http.NewRequest("GET", "/nonexistent", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(notFoundHandler)
	handler.ServeHTTP(rr, req)

	var response ErrorResponse
	if err := json.NewDecoder(rr.Body).Decode(&response); err != nil {
		t.Errorf("failed to decode response body: %v", err)
	}

	if response.Error != "Not Found" {
		t.Errorf("unexpected error message: got %v want %v", response.Error, "Not Found")
	}

	if response.Path != "/nonexistent" {
		t.Errorf("unexpected path in error response: got %v want %v", response.Path, "/nonexistent")
	}
}

func TestGetUptime_ReturnsNonNegativeSeconds(t *testing.T) {
	seconds, human := getUptime()

	if seconds < 0 {
		t.Errorf("uptime seconds should be non-negative: got %v", seconds)
	}

	if human == "" {
		t.Error("uptime human string should not be empty")
	}
}
