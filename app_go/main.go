package main

import (
	"log"
	"net/http"
	"os"

	"devops-info-service-go/internal/config"
	"devops-info-service-go/internal/server"
)

func main() {
	logger := log.New(os.Stdout, "devops-go ", log.LstdFlags|log.LUTC|log.Lshortfile)

	cfg := config.FromEnv()
	logger.Printf("Loaded config: port=%s", cfg.Port)

	handler := server.New(logger)

	addr := ":" + cfg.Port
	logger.Printf("Starting Go devops-info-service on %s", addr)

	if err := http.ListenAndServe(addr, handler); err != nil {
		logger.Fatalf("server error: %v", err)
	}
}
