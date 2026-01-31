package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

// TestGetEnv tests the environment variable helper function
func TestGetEnv(t *testing.T) {
	// Test default value
	result := getEnv("NONEXISTENT_VAR_12345", "default")
	if result != "default" {
		t.Errorf("Expected 'default', got '%s'", result)
	}

	// Test actual env var
	t.Setenv("TEST_VAR", "test_value")
	result = getEnv("TEST_VAR", "default")
	if result != "test_value" {
		t.Errorf("Expected 'test_value', got '%s'", result)
	}
}

// TestGetUptime tests the uptime calculation function
func TestGetUptime(t *testing.T) {
	seconds, human := getUptime()

	if seconds < 0 {
		t.Errorf("Expected non-negative uptime, got %d", seconds)
	}

	if len(human) == 0 {
		t.Error("Expected non-empty human-readable uptime")
	}
}

// TestGetSystemInfo tests system information collection
func TestGetSystemInfo(t *testing.T) {
	info := getSystemInfo()

	if info.Hostname == "" {
		t.Error("Expected non-empty hostname")
	}

	if info.Platform == "" {
		t.Error("Expected non-empty platform")
	}

	if info.Architecture == "" {
		t.Error("Expected non-empty architecture")
	}

	if info.CPUCount <= 0 {
		t.Errorf("Expected positive CPU count, got %d", info.CPUCount)
	}

	if info.GoVersion == "" {
		t.Error("Expected non-empty Go version")
	}
}

// TestGetEndpoints tests endpoint list function
func TestGetEndpoints(t *testing.T) {
	endpoints := getEndpoints()

	if len(endpoints) != 2 {
		t.Errorf("Expected 2 endpoints, got %d", len(endpoints))
	}

	foundIndex := false
	foundHealth := false
	for _, ep := range endpoints {
		if ep.Path == "/" {
			foundIndex = true
		}
		if ep.Path == "/health" {
			foundHealth = true
		}
	}

	if !foundIndex {
		t.Error("Expected / endpoint in list")
	}
	if !foundHealth {
		t.Error("Expected /health endpoint in list")
	}
}

// TestHandleIndex tests the main endpoint handler
func TestHandleIndex(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()

	handleIndex(w, req)

	resp := w.Result()
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	contentType := resp.Header.Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("Expected Content-Type 'application/json', got '%s'", contentType)
	}

	var response ServiceInfo
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode JSON response: %v", err)
	}

	if response.Service.Name != "devops-info-service" {
		t.Errorf("Expected service name 'devops-info-service', got '%s'", response.Service.Name)
	}
	if response.Service.Framework != "Go (http)" {
		t.Errorf("Expected framework 'Go (http)', got '%s'", response.Service.Framework)
	}

	if response.System.Hostname == "" {
		t.Error("Expected non-empty hostname in response")
	}
	if response.System.CPUCount <= 0 {
		t.Error("Expected positive CPU count in response")
	}

	if response.Runtime.Timezone != "UTC" {
		t.Errorf("Expected timezone 'UTC', got '%s'", response.Runtime.Timezone)
	}

	if response.Request.Method != "GET" {
		t.Errorf("Expected method 'GET', got '%s'", response.Request.Method)
	}
	if response.Request.Path != "/" {
		t.Errorf("Expected path '/', got '%s'", response.Request.Path)
	}

	if len(response.Endpoints) != 2 {
		t.Errorf("Expected 2 endpoints, got %d", len(response.Endpoints))
	}
}

// TestHandleIndexReturnsJSON tests that index returns proper JSON structure
func TestHandleIndexReturnsJSON(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()

	handleIndex(w, req)

	resp := w.Result()
	defer resp.Body.Close()

	var response map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Response is not valid JSON: %v", err)
	}

	requiredSections := []string{"service", "system", "runtime", "request", "endpoints"}
	for _, section := range requiredSections {
		if _, exists := response[section]; !exists {
			t.Errorf("Missing required section: %s", section)
		}
	}
}

// TestHandleHealth tests the health check endpoint
func TestHandleHealth(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	handleHealth(w, req)

	resp := w.Result()
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	contentType := resp.Header.Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("Expected Content-Type 'application/json', got '%s'", contentType)
	}

	var response HealthResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode JSON response: %v", err)
	}

	if response.Status != "healthy" {
		t.Errorf("Expected status 'healthy', got '%s'", response.Status)
	}
	if response.Timestamp == "" {
		t.Error("Expected non-empty timestamp")
	}
	if response.UptimeSeconds < 0 {
		t.Errorf("Expected non-negative uptime, got %d", response.UptimeSeconds)
	}
}

// TestHandleHealthReturnsJSON tests health endpoint JSON structure
func TestHandleHealthReturnsJSON(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()

	handleHealth(w, req)

	resp := w.Result()
	defer resp.Body.Close()

	var response map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Response is not valid JSON: %v", err)
	}

	requiredFields := []string{"status", "timestamp", "uptime_seconds"}
	for _, field := range requiredFields {
		if _, exists := response[field]; !exists {
			t.Errorf("Missing required field: %s", field)
		}
	}
}

// TestHandleNotFound tests the 404 handler
func TestHandleNotFound(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/nonexistent", nil)
	w := httptest.NewRecorder()

	handleNotFound(w, req)

	resp := w.Result()
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusNotFound {
		t.Errorf("Expected status 404, got %d", resp.StatusCode)
	}

	contentType := resp.Header.Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("Expected Content-Type 'application/json', got '%s'", contentType)
	}

	var response map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode JSON response: %v", err)
	}

	if response["error"] != "Not Found" {
		t.Errorf("Expected error 'Not Found', got '%s'", response["error"])
	}
	if response["status_code"].(float64) != 404 {
		t.Errorf("Expected status_code 404, got %v", response["status_code"])
	}
}

// TestHandleNotFoundReturnsJSON tests that 404 returns JSON
func TestHandleNotFoundReturnsJSON(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/nonexistent", nil)
	w := httptest.NewRecorder()

	handleNotFound(w, req)

	resp := w.Result()
	defer resp.Body.Close()

	var response map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Response is not valid JSON: %v", err)
	}

	requiredFields := []string{"error", "message", "status_code", "path"}
	for _, field := range requiredFields {
		if _, exists := response[field]; !exists {
			t.Errorf("Missing required field: %s", field)
		}
	}
}

// TestGetRequestInfo tests request information extraction
func TestGetRequestInfo(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("User-Agent", "Test-Agent/1.0")

	info := getRequestInfo(req)

	if info.Method != "GET" {
		t.Errorf("Expected method 'GET', got '%s'", info.Method)
	}
	if info.Path != "/" {
		t.Errorf("Expected path '/', got '%s'", info.Path)
	}
	if info.UserAgent != "Test-Agent/1.0" {
		t.Errorf("Expected user agent 'Test-Agent/1.0', got '%s'", info.UserAgent)
	}
}

// TestNotFoundHandler tests the custom mux wrapper
func TestNotFoundHandler(t *testing.T) {
	mux := http.NewServeMux()
	mux.HandleFunc("/", handleIndex)
	mux.HandleFunc("/health", handleHealth)

	handler := &notFoundHandler{mux: mux}

	t.Run("valid endpoint /", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/", nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)

		if w.Result().StatusCode != http.StatusOK {
			t.Errorf("Expected status 200 for /, got %d", w.Result().StatusCode)
		}
	})

	t.Run("valid endpoint /health", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/health", nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)

		if w.Result().StatusCode != http.StatusOK {
			t.Errorf("Expected status 200 for /health, got %d", w.Result().StatusCode)
		}
	})

	t.Run("invalid endpoint", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/invalid", nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)

		if w.Result().StatusCode != http.StatusNotFound {
			t.Errorf("Expected status 404 for /invalid, got %d", w.Result().StatusCode)
		}
	})
}

// TestSetupRouter tests the router setup function
func TestSetupRouter(t *testing.T) {
	handler := setupRouter()

	if handler == nil {
		t.Fatal("Expected non-nil handler from setupRouter")
	}

	// Test that the router handles requests correctly
	t.Run("routes to index", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/", nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)

		if w.Result().StatusCode != http.StatusOK {
			t.Errorf("Expected status 200, got %d", w.Result().StatusCode)
		}
	})

	t.Run("routes to health", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/health", nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)

		if w.Result().StatusCode != http.StatusOK {
			t.Errorf("Expected status 200, got %d", w.Result().StatusCode)
		}
	})

	t.Run("returns 404 for unknown", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/unknown", nil)
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)

		if w.Result().StatusCode != http.StatusNotFound {
			t.Errorf("Expected status 404, got %d", w.Result().StatusCode)
		}
	})
}

// TestPrintStartupBanner tests that startup banner doesn't panic
func TestPrintStartupBanner(t *testing.T) {
	// Just ensure it doesn't panic
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("printStartupBanner panicked: %v", r)
		}
	}()

	printStartupBanner()
}

// TestDebugMode tests handlers with debug mode enabled
func TestDebugMode(t *testing.T) {
	// Save original debug value and restore after test
	originalDebug := debug
	debug = true
	defer func() { debug = originalDebug }()

	t.Run("index with debug", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/", nil)
		w := httptest.NewRecorder()
		handleIndex(w, req)

		if w.Result().StatusCode != http.StatusOK {
			t.Errorf("Expected status 200, got %d", w.Result().StatusCode)
		}
	})

	t.Run("health with debug", func(t *testing.T) {
		req := httptest.NewRequest(http.MethodGet, "/health", nil)
		w := httptest.NewRecorder()
		handleHealth(w, req)

		if w.Result().StatusCode != http.StatusOK {
			t.Errorf("Expected status 200, got %d", w.Result().StatusCode)
		}
	})
}
