package main

import (
	"fmt"
	"net/http"

	"app_golang/handlers"
)

func main() {
	http.HandleFunc("/", handlers.CurrentTimeHandler)
	fmt.Println("Starting server at :8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		fmt.Println("Error starting server:", err)
	}
}
