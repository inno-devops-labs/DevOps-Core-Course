import asyncio
import base64

from playwright.async_api import async_playwright

GRAFANA = "http://localhost:3000"
USER = "admin"
PASS = "admin"
OUT = "k8s/screenshots"

# Full dashboard paths (uid/slug from /api/search)
DASH = {
    "pod": "6581e46e4e5c7ba40a07646395ef7b23/kubernetes-compute-resources-pod",
    "namespace": "85a562078cdf77779eaa1add43ccec1e/kubernetes-compute-resources-namespace-pods",
    "node": "7d57716318ee0dddbac5a7f451fb7753/node-exporter-nodes",
    "kubelet": "3138fa155d5915769fbded898ac09fd9/kubernetes-kubelet",
}

AUTH = base64.b64encode(f"{USER}:{PASS}".encode()).decode()


async def shot(page, name, wait=7000):
    await page.wait_for_timeout(wait)
    path = f"{OUT}/{name}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"  -> saved {path}")


async def goto_dash(page, uid, params=""):
    url = f"{GRAFANA}/d/{uid}?orgId=1&from=now-1h&to=now{params}"
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(2000)
    print(f"  url: {page.url[:80]}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Inject Basic Auth header on every request
        ctx = await browser.new_context(
            viewport={"width": 1600, "height": 900},
            extra_http_headers={"Authorization": f"Basic {AUTH}"},
        )
        page = await ctx.new_page()

        # Q1 — Pod CPU/Memory (namespace=default)
        print("Q1: Pod resources...")
        await goto_dash(
            page,
            DASH["pod"],
            "&var-datasource=prometheus&var-cluster=&var-namespace=default"
            "&var-pod=app-python-6d99b79d85-ck9zc",
        )
        await shot(page, "grafana_pod_resources")

        # Q2 — Namespace CPU most/least
        print("Q2: Namespace CPU...")
        await goto_dash(
            page,
            DASH["namespace"],
            "&var-datasource=prometheus&var-cluster=&var-namespace=default",
        )
        await shot(page, "grafana_namespace_cpu")

        # Q3 — Node metrics
        print("Q3: Node metrics...")
        await goto_dash(page, DASH["node"], "&var-datasource=prometheus")
        await shot(page, "grafana_node_metrics")

        # Q4 — Kubelet
        print("Q4: Kubelet...")
        await goto_dash(
            page, DASH["kubelet"], "&var-datasource=prometheus&var-cluster="
        )
        await shot(page, "grafana_kubelet")

        # Q5 — Network (scrolled to bottom)
        print("Q5: Network traffic...")
        await goto_dash(
            page,
            DASH["namespace"],
            "&var-datasource=prometheus&var-cluster=&var-namespace=default",
        )
        await page.wait_for_timeout(5000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await shot(page, "grafana_network", wait=3000)

        # Q6 — Alertmanager
        print("Q6: Alertmanager...")
        await page.goto("http://localhost:9093")
        await page.wait_for_load_state("networkidle")
        await shot(page, "grafana_alerts", wait=2000)

        await browser.close()
        print("\nDone! All screenshots in k8s/screenshots/")


asyncio.run(main())
