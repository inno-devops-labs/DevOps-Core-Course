import base64
import http.cookiejar
import json
import os
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


OUTPUT_DIR = Path("/workspace/monitoring/docs/screenshots/lab08")
PS_TXT = OUTPUT_DIR / "docker-compose-ps.txt"


def save_full_page(driver: webdriver.Remote, path: Path) -> None:
    metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
    content_size = metrics["contentSize"]
    width = max(1400, int(content_size["width"]))
    height = max(900, min(2600, int(content_size["height"]) + 120))
    driver.set_window_size(width, height)
    png = driver.execute_cdp_cmd(
        "Page.captureScreenshot",
        {"format": "png", "captureBeyondViewport": True, "fromSurface": True},
    )
    path.write_bytes(base64.b64decode(png["data"]))


def open_and_capture(driver: webdriver.Remote, url: str, path: Path, wait_text: str | None = None) -> None:
    driver.get(url)
    if wait_text:
        WebDriverWait(driver, 20).until(lambda d: wait_text in d.page_source)
    else:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)
    save_full_page(driver, path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1600,1400")

    driver = webdriver.Remote(
        command_executor="http://selenium:4444/wd/hub",
        options=options,
    )

    try:
        open_and_capture(
            driver,
            "http://app-python:8000/metrics",
            OUTPUT_DIR / "screenshot_01_metrics_endpoint.png",
            wait_text="http_requests_total",
        )

        open_and_capture(
            driver,
            "http://prometheus:9090/targets",
            OUTPUT_DIR / "screenshot_02_prometheus_targets.png",
            wait_text="app-python:8000",
        )

        open_and_capture(
            driver,
            "http://prometheus:9090/graph?g0.expr=up&g0.tab=1&g0.show_exemplars=0&g0.range_input=1h",
            OUTPUT_DIR / "screenshot_03_promql_up_query.png",
            wait_text="app-python:8000",
        )

        cookie_jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
        login_data = json.dumps({"user": "admin", "password": "admin"}).encode()
        opener.open(
            urllib.request.Request(
                "http://grafana:3000/login",
                data=login_data,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
        )

        driver.get("http://grafana:3000/login")
        for cookie in cookie_jar:
            driver.add_cookie(
                {
                    "name": cookie.name,
                    "value": cookie.value,
                    "path": cookie.path,
                    "domain": "grafana",
                }
            )

        driver.get("http://grafana:3000/d/devops-app-metrics/devops-app-metrics?orgId=1")
        WebDriverWait(driver, 30).until(lambda d: "DevOps App Metrics" in d.page_source and "Request Rate by Endpoint" in d.page_source)
        driver.execute_script("document.body.style.zoom='67%';")
        time.sleep(4)
        save_full_page(driver, OUTPUT_DIR / "screenshot_04_grafana_dashboard.png")

        if PS_TXT.exists():
            open_and_capture(
                driver,
                f"file://{PS_TXT}",
                OUTPUT_DIR / "screenshot_05_docker_compose_ps.png",
                wait_text="prometheus",
            )
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
