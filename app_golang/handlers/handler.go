package handlers

import (
	"html/template"
	"net/http"
	"path/filepath"

	"app_golang/utils"
)

// Handler function to display the current time in Moscow
func CurrentTimeHandler(w http.ResponseWriter, _ *http.Request) {
	currentTime := utils.GetCurrentTimeInMoscow()

	tmplPath := filepath.Join("templates", "index.html")
	tmpl, err := template.ParseFiles(tmplPath)
	if err != nil {
		http.Error(w, "Could not load template", http.StatusInternalServerError)
		return
	}

	err = tmpl.Execute(w, currentTime)
	if err != nil {
		http.Error(w, "Failed to render template", http.StatusInternalServerError)
		return
	}
}
