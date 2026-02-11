package main

import (
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
)

// Tests cover GET / endpoint - JSON structure, service info, system info, and request info validation.
func TestMainHandler(t *testing.T) {
	// Create a test server
	server := httptest.NewServer(http.HandlerFunc(mainHandler))
	defer server.Close()

	// Make request to root endpoint
	resp, err := http.Get(server.URL + "/")
	if err != nil {
		t.Fatalf("Failed to make request: %v", err)
	}
	defer resp.Body.Close()

	// Check status code
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	// Check content type
	contentType := resp.Header.Get("Content-Type")
	if contentType != "application/json" {
		t.Errorf("Expected Content-Type application/json, got %s", contentType)
	}

	// Parse response
	var response InfoResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Validate service info
	if response.Service.Name != "devops-info-service" {
		t.Errorf("Expected service name 'devops-info-service', got '%s'", response.Service.Name)
	}
	if response.Service.Version != "1.0.0" {
		t.Errorf("Expected version '1.0.0', got '%s'", response.Service.Version)
	}
	if response.Service.Framework != "Go net/http" {
		t.Errorf("Expected framework 'Go net/http', got '%s'", response.Service.Framework)
	}

	// Validate system info
	if response.System.GoVersion == "" {
		t.Error("GoVersion should not be empty")
	}
	if response.System.CPUCount <= 0 {
		t.Error("CPUCount should be greater than 0")
	}

	// Validate runtime info
	if response.Runtime.UptimeSeconds < 0 {
		t.Error("UptimeSeconds should be non-negative")
	}
	if response.Runtime.Timezone != "UTC" {
		t.Errorf("Expected timezone 'UTC', got '%s'", response.Runtime.Timezone)
	}

	// Validate endpoints list
	if len(response.Endpoints) < 2 {
		t.Errorf("Expected at least 2 endpoints, got %d", len(response.Endpoints))
	}
}

func TestMainHandlerRequestInfo(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(mainHandler))
	defer server.Close()

	// Test with POST method to verify Request.Method is captured
	req, err := http.NewRequest("POST", server.URL+"/", nil)
	if err != nil {
		t.Fatalf("Failed to create request: %v", err)
	}
	req.Header.Set("User-Agent", "test-agent")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("Failed to make request: %v", err)
	}
	defer resp.Body.Close()

	var response InfoResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Verify request info is captured correctly
	if response.Request.Method != "POST" {
		t.Errorf("Expected method POST, got %s", response.Request.Method)
	}
	if response.Request.UserAgent != "test-agent" {
		t.Errorf("Expected User-Agent 'test-agent', got '%s'", response.Request.UserAgent)
	}
}

func TestMainHandlerSystemInfo(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(mainHandler))
	defer server.Close()

	resp, err := http.Get(server.URL + "/")
	if err != nil {
		t.Fatalf("Failed to make request: %v", err)
	}
	defer resp.Body.Close()

	var response InfoResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Verify system info fields
	if response.System.Platform == "" {
		t.Error("Platform should not be empty")
	}
	if response.System.Architecture == "" {
		t.Error("Architecture should not be empty")
	}
	if response.System.PlatformVersion != "N/A" {
		t.Errorf("Expected PlatformVersion 'N/A', got '%s'", response.System.PlatformVersion)
	}
}

func TestMainHandlerServiceInfo(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(mainHandler))
	defer server.Close()

	resp, err := http.Get(server.URL + "/")
	if err != nil {
		t.Fatalf("Failed to make request: %v", err)
	}
	defer resp.Body.Close()

	var response InfoResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Verify service info details
	if response.Service.Description == "" {
		t.Error("Service description should not be empty")
	}
	if response.Service.Name == "" {
		t.Error("Service name should not be empty")
	}
}

func TestMainHandlerEndpointsList(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(mainHandler))
	defer server.Close()

	resp, err := http.Get(server.URL + "/")
	if err != nil {
		t.Fatalf("Failed to make request: %v", err)
	}
	defer resp.Body.Close()

	var response InfoResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Verify endpoints list structure
	if len(response.Endpoints) != 2 {
		t.Errorf("Expected exactly 2 endpoints, got %d", len(response.Endpoints))
	}

	// Verify endpoint details
	foundRoot := false
	foundHealth := false
	for _, ep := range response.Endpoints {
		if ep.Path == "/" && ep.Method == "GET" {
			foundRoot = true
		}
		if ep.Path == "/health" && ep.Method == "GET" {
			foundHealth = true
		}
	}

	if !foundRoot {
		t.Error("Root endpoint (/) not found in endpoints list")
	}
	if !foundHealth {
		t.Error("Health endpoint (/health) not found in endpoints list")
	}
}

func TestMainHandlerRequestPath(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(mainHandler))
	defer server.Close()

	resp, err := http.Get(server.URL + "/")
	if err != nil {
		t.Fatalf("Failed to make request: %v", err)
	}
	defer resp.Body.Close()

	var response InfoResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Verify request path is captured
	if response.Request.Path != "/" {
		t.Errorf("Expected path '/', got '%s'", response.Request.Path)
	}
	if response.Request.ClientIP == "" {
		t.Error("ClientIP should not be empty")
	}
}

func TestMainHandlerHostnameError(t *testing.T) {
	// Save original function
	originalHostnameFunc := hostnameFunc
	defer func() {
		hostnameFunc = originalHostnameFunc
	}()

	// Mock hostname function to return error
	hostnameFunc = func() (string, error) {
		return "", errors.New("hostname error")
	}

	server := httptest.NewServer(http.HandlerFunc(mainHandler))
	defer server.Close()

	resp, err := http.Get(server.URL + "/")
	if err != nil {
		t.Fatalf("Failed to make request: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	var response InfoResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Verify that hostname is set to "unknown" when os.Hostname() fails
	if response.System.Hostname != "unknown" {
		t.Errorf("Expected hostname 'unknown' when os.Hostname() fails, got '%s'", response.System.Hostname)
	}
}
