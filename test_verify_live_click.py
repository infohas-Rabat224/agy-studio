import time
import json
from playwright.sync_api import sync_playwright

def test_live_click():
    with sync_playwright() as p:
        print("[1] Launching Edge browser (channel='msedge')...")
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("[2] Opening http://127.0.0.1:8000...")
        page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        time.sleep(1)

        print("[3] Clicking #headerWsBtn...")
        page.locator("#headerWsBtn").click()
        time.sleep(0.5)

        print("[4] Clicking Parcourir...")
        page.locator("#wsDropdownMenu button:has-text('Parcourir')").first.click()
        time.sleep(1)

        # Capture screenshot immediately after click
        page.screenshot(path="C:/Agy Studio/screenshot_live_now.png")
        print("    Saved C:/Agy Studio/screenshot_live_now.png")

        # Check DOM state
        btn_html = page.locator("#currentWorkspaceText").inner_html()
        is_active = page.evaluate("() => window.isWorkspacePickerActive")
        job_id = page.evaluate("() => window.__currentPickerJobId")
        print(f"    Current Workspace Text HTML: {btn_html}")
        print(f"    isWorkspacePickerActive: {is_active}, job_id: {job_id}")

        # Check backend job status
        if job_id:
            import urllib.request
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:8000/api/workspace/picker/{job_id}", timeout=2) as r:
                    job_st = json.loads(r.read().decode())
                    print("    Backend Job:", json.dumps(job_st, indent=2))
            except Exception as e:
                print("    Error fetching job:", e)

        # Now test cancelling via Escape
        print("[5] Pressing Escape...")
        page.keyboard.press("Escape")
        time.sleep(1)

        btn_after = page.locator("#currentWorkspaceText").text_content().strip()
        is_active_after = page.evaluate("() => window.isWorkspacePickerActive")
        print(f"    After Escape: text='{btn_after}', isWorkspacePickerActive={is_active_after}")

        # Save screenshot after escape
        page.screenshot(path="C:/Agy Studio/screenshot_after_escape.png")
        print("    Saved C:/Agy Studio/screenshot_after_escape.png")

        browser.close()

if __name__ == "__main__":
    test_live_click()
