// Echo — a 2nd service introduced in Lab 9 as the companion to the student's
// Python service. Kept deliberately small: HTTP /ping, /echo, /healthz, /metrics.
// Maintained by the course, NOT a student deliverable.
//
// Build:   docker build -t ghcr.io/inno-devops-labs/echo:v1 .
// Run:     docker run -p 8081:8081 ghcr.io/inno-devops-labs/echo:v1
// K8s:     see Lab 9 manifests
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"sync/atomic"
	"time"
)

var requestCounter atomic.Uint64
var startedAt = time.Now()

type response struct {
	Service   string            `json:"service"`
	Version   string            `json:"version"`
	Hostname  string            `json:"hostname"`
	Headers   map[string]string `json:"headers,omitempty"`
	Body      string            `json:"body,omitempty"`
	UptimeSec float64           `json:"uptime_seconds"`
	ReqNo     uint64            `json:"request_number"`
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8081"
	}
	version := os.Getenv("VERSION")
	if version == "" {
		version = "v1.0.0"
	}
	hostname, _ := os.Hostname()

	mux := http.NewServeMux()

	mux.HandleFunc("/ping", func(w http.ResponseWriter, r *http.Request) {
		requestCounter.Add(1)
		w.Header().Set("Content-Type", "text/plain")
		fmt.Fprintln(w, "pong")
	})

	mux.HandleFunc("/echo", func(w http.ResponseWriter, r *http.Request) {
		n := requestCounter.Add(1)
		body, _ := io.ReadAll(r.Body)
		defer r.Body.Close()

		hdrs := make(map[string]string, len(r.Header))
		for k, v := range r.Header {
			if len(v) > 0 {
				hdrs[k] = v[0]
			}
		}
		resp := response{
			Service:   "echo",
			Version:   version,
			Hostname:  hostname,
			Headers:   hdrs,
			Body:      string(body),
			UptimeSec: time.Since(startedAt).Seconds(),
			ReqNo:     n,
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(resp)
	})

	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintln(w, "ok")
	})

	mux.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain; version=0.0.4")
		n := requestCounter.Load()
		fmt.Fprintln(w, "# HELP echo_requests_total Total HTTP requests handled.")
		fmt.Fprintln(w, "# TYPE echo_requests_total counter")
		fmt.Fprintf(w, "echo_requests_total %d\n", n)
		fmt.Fprintln(w, "# HELP echo_uptime_seconds Process uptime in seconds.")
		fmt.Fprintln(w, "# TYPE echo_uptime_seconds gauge")
		fmt.Fprintf(w, "echo_uptime_seconds %.3f\n", time.Since(startedAt).Seconds())
	})

	addr := ":" + port
	log.Printf("echo %s listening on %s (hostname=%s)", version, addr, hostname)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatal(err)
	}
}
