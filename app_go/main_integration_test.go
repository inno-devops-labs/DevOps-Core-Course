package main

import (
    "net/http"
    "testing"
    "time"
)


func TestMainFunction_StartsAndResponds(t *testing.T) {
    host := "127.0.0.1"
    port := "18080"
    srv := newServer(host, port)

    go func() {
        _ = srv.ListenAndServe()
    }()
    defer srv.Close()

    time.Sleep(200 * time.Millisecond)

    resp, err := http.Get("http://127.0.0.1:18080/health")
    if err != nil {
        t.Fatalf("could not GET /health: %v", err)
    }
    if resp.StatusCode != http.StatusOK {
        t.Errorf("expected 200, got %d", resp.StatusCode)
    }

    resp, err = http.Get("http://127.0.0.1:18080/")
    if err != nil {
        t.Fatalf("could not GET /: %v", err)
    }
    if resp.StatusCode != http.StatusOK {
        t.Errorf("expected 200, got %d", resp.StatusCode)
    }
}

func TestMainFunction_BadPort(t *testing.T) {
    host := "127.0.0.1"
    port := "badport"
    srv := newServer(host, port)
    go func() {
        _ = srv.ListenAndServe()
    }()
    time.Sleep(200 * time.Millisecond)
    // No assert: just ensure no panic
}
