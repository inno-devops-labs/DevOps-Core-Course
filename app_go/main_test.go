package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealthEndpoint(t *testing.T) {
	req, _ := http.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	handleHealth(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("Expected status %d, got %d", http.StatusOK, w.Code)
	}

	var response HealthResponse
	err := json.NewDecoder(w.Body).Decode(&response)
	if err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if response.Status != "healthy" {
		t.Fatalf("Expected status 'healthy', got '%s'", response.Status)
	}

	if response.Timestamp == "" {
		t.Fatal("Expected non-empty timestamp")
	}

	if response.UptimeSeconds < 0 {
		t.Fatalf("Expected non-negative uptime, got %d", response.UptimeSeconds)
	}
}

func TestInfoEndpoint(t *testing.T) {
	req, _ := http.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()

	handleInfo(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("Expected status %d, got %d", http.StatusOK, w.Code)
	}

	var response InfoResponse
	err := json.NewDecoder(w.Body).Decode(&response)
	if err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if response.Service.Name != "devops-info-service-go" {
		t.Fatalf("Expected service name 'devops-info-service-go', got '%s'", response.Service.Name)
	}

	if response.Service.Version != "1.0.0" {
		t.Fatalf("Expected version '1.0.0', got '%s'", response.Service.Version)
	}

	if response.Service.Language != "Go" {
		t.Fatalf("Expected language 'Go', got '%s'", response.Service.Language)
	}

	if response.System.OS == "" {
		t.Fatal("Expected non-empty OS")
	}

	if response.Runtime.UptimeSeconds < 0 {
		t.Fatalf("Expected non-negative uptime, got %d", response.Runtime.UptimeSeconds)
	}
}

func TestHealthEndpointHeaders(t *testing.T) {
	req, _ := http.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	handleHealth(w, req)

	contentType := w.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Fatalf("Expected Content-Type 'application/json', got '%s'", contentType)
	}
}

func TestInfoEndpointHeaders(t *testing.T) {
	req, _ := http.NewRequest("GET", "/", nil)
	w := httptest.NewRecorder()

	handleInfo(w, req)

	contentType := w.Header().Get("Content-Type")
	if contentType != "application/json" {
		t.Fatalf("Expected Content-Type 'application/json', got '%s'", contentType)
	}
}
