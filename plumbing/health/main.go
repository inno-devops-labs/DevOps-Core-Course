// Health — a 3rd service introduced in Lab 13 to demonstrate ArgoCD
// ApplicationSet generating multiple Applications. Even smaller than echo.
// Maintained by the course, NOT a student deliverable.
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"runtime"
	"sync/atomic"
	"time"
)

var requestCounter atomic.Uint64
var startedAt = time.Now()

type status struct {
	Service   string  `json:"service"`
	Version   string  `json:"version"`
	Hostname  string  `json:"hostname"`
	GoVersion string  `json:"go_version"`
	UptimeSec float64 `json:"uptime_seconds"`
	ReqNo     uint64  `json:"request_number"`
	Status    string  `json:"status"`
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8082"
	}
	version := os.Getenv("VERSION")
	if version == "" {
		version = "v1.0.0"
	}
	hostname, _ := os.Hostname()

	mux := http.NewServeMux()

	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		n := requestCounter.Add(1)
		s := status{
			Service:   "health",
			Version:   version,
			Hostname:  hostname,
			GoVersion: runtime.Version(),
			UptimeSec: time.Since(startedAt).Seconds(),
			ReqNo:     n,
			Status:    "ok",
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(s)
	})

	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintln(w, "ok")
	})

	mux.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/plain; version=0.0.4")
		n := requestCounter.Load()
		fmt.Fprintln(w, "# HELP health_requests_total Total HTTP requests handled.")
		fmt.Fprintln(w, "# TYPE health_requests_total counter")
		fmt.Fprintf(w, "health_requests_total %d\n", n)
		fmt.Fprintln(w, "# HELP health_uptime_seconds Process uptime in seconds.")
		fmt.Fprintln(w, "# TYPE health_uptime_seconds gauge")
		fmt.Fprintf(w, "health_uptime_seconds %.3f\n", time.Since(startedAt).Seconds())
	})

	addr := ":" + port
	log.Printf("health %s listening on %s (hostname=%s)", version, addr, hostname)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatal(err)
	}
}
