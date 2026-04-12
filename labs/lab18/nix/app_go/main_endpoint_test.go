package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestMainEndpoint(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	w := httptest.NewRecorder()

	mainHandler(w, req)

	res := w.Result()
	defer res.Body.Close()

	if res.StatusCode != http.StatusOK {
		t.Fatalf("expected status 200, got %d", res.StatusCode)
	}

	var data map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&data); err != nil {
		t.Fatalf("failed to decode json: %v", err)
	}

	if _, ok := data["service"]; !ok {
		t.Fatal("missing 'service' field")
	}
	if _, ok := data["system"]; !ok {
		t.Fatal("missing 'system' field")
	}
	if _, ok := data["runtime"]; !ok {
		t.Fatal("missing 'runtime' field")
	}
	if _, ok := data["request"]; !ok {
		t.Fatal("missing 'request' field")
	}
	if _, ok := data["endpoints"]; !ok {
		t.Fatal("missing 'endpoints' field")
	}

	service := data["service"].(map[string]interface{})
	if service["name"] != "info-service" {
		t.Fatalf("expected service name 'info-service', got %v", service["name"])
	}
}
