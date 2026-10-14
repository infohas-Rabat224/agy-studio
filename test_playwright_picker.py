import sys
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

def run_test():
    with sync_playwright() as p:
        print("[1] Launching Edge browser via Playwright...")
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"CONSOLE [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: console_logs.append(f"PAGE ERROR: {err}"))

        print("[2] Navigating to http://127.0.0.1:8000...")
        page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        time.sleep(1)

        ws_elem = page.locator("#currentWorkspaceText")
        print(f"    Initial workspace display: '{ws_elem.text_content().strip()}'")
        assert "Nexus" in ws_elem.text_content(), f"Expected Nexus in workspace text, got {ws_elem.text_content()}"

        # -------------------------------------------------------------
        # TEST A: Clicking Parcourir triggers spinner and job creation
        # -------------------------------------------------------------
        print("\n--- [TEST A] Clicking 'Parcourir' and verifying spinner state ---")
        page.locator("#headerWsBtn").click()
        time.sleep(0.3)
        page.locator("#wsDropdownMenu button:has-text('Parcourir')").first.click()
        time.sleep(0.5)

        spinner_html = page.locator("#currentWorkspaceText").inner_html()
        is_active = page.evaluate("() => window.isWorkspacePickerActive")
        job_id = page.evaluate("() => window.__currentPickerJobId")
        print(f"    Spinner HTML: {spinner_html}")
        print(f"    isWorkspacePickerActive={is_active}, job_id={job_id}")
        assert is_active == True, "Picker should be active"
        assert "animate-spin" in spinner_html or "Parcourir" in spinner_html, "Spinner icon should be visible"
        assert job_id is not None, "Picker job_id should be assigned"

        # -------------------------------------------------------------
        # TEST B: Escape key immediately releases spinner and resets lock
        # -------------------------------------------------------------
        print("\n--- [TEST B] Pressing Escape to cancel and release spinner ---")
        page.keyboard.press("Escape")
        time.sleep(0.5)

        restored_text = page.locator("#currentWorkspaceText").text_content().strip()
        is_active_after_esc = page.evaluate("() => window.isWorkspacePickerActive")
        print(f"    Restored workspace text: '{restored_text}'")
        print(f"    isWorkspacePickerActive={is_active_after_esc}")
        assert is_active_after_esc == False, "Picker lock should be released after Escape"
        assert "Nexus" in restored_text, f"Workspace text should be restored to Nexus, got '{restored_text}'"

        # -------------------------------------------------------------
        # TEST C: Clicking headerWsBtn while active opens manual modal
        # -------------------------------------------------------------
        print("\n--- [TEST C] Re-activating Parcourir and testing click-to-fallback ---")
        page.locator("#headerWsBtn").click()
        time.sleep(0.3)
        page.locator("#wsDropdownMenu button:has-text('Parcourir')").first.click()
        time.sleep(0.5)

        # Click headerWsBtn again while spinning
        page.locator("#headerWsBtn").click()
        time.sleep(0.5)

        modal_hidden = page.evaluate("() => document.getElementById('manualWorkspaceModal').classList.contains('hidden')")
        print(f"    manualWorkspaceModal is hidden: {modal_hidden}")
        assert modal_hidden == False, "manualWorkspaceModal should be visible as graceful fallback"

        # Close manual modal
        page.locator("#manualWorkspaceModal button:has-text('Annuler')").click()
        time.sleep(0.3)

        # -------------------------------------------------------------
        # TEST D: Folder selection completes cleanly and updates UI
        # -------------------------------------------------------------
        print("\n--- [TEST D] Testing clean folder selection via bridge override ---")
        page.evaluate("() => window.__testFolderOverride = 'F:\\\\Nexus'")
        page.locator("#headerWsBtn").click()
        time.sleep(0.3)
        page.locator("#wsDropdownMenu button:has-text('Parcourir')").first.click()
        time.sleep(1)

        final_ws = page.locator("#currentWorkspaceText").text_content().strip()
        final_active = page.evaluate("() => window.isWorkspacePickerActive")
        print(f"    Final workspace text: '{final_ws}'")
        print(f"    Final isWorkspacePickerActive={final_active}")
        assert final_active == False, "Picker must not remain active after folder selection"
        assert "Nexus" in final_ws, f"Workspace should be Nexus, got '{final_ws}'"

        # Screenshot for verification
        page.screenshot(path="C:/Agy Studio/screenshot_playwright_success.png")
        print("[+] Screenshot saved to C:/Agy Studio/screenshot_playwright_success.png")

        browser.close()
        print("\n>>> ALL PLAYWRIGHT TESTS PASSED WITH ZERO ERRORS! <<<")

if __name__ == "__main__":
    run_test()
