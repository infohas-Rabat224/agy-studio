import asyncio
import json
import urllib.request
from playwright.async_api import async_playwright

async def test_full_picker_flow():
    print("==================================================")
    print("VERIFYING WORKSPACE PICKER END-TO-END FLOW")
    print("==================================================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        console_events = []
        page.on("console", lambda msg: console_events.append(msg.text) if "WORKSPACE_PICKER" in msg.text else None)

        print("\n--- [Step 1] Loading Agy Studio frontend ---")
        await page.goto("http://127.0.0.1:8000")
        await page.wait_for_selector("#changeWorkspaceBtn")
        
        btn = page.locator("#changeWorkspaceBtn")
        btn_text = page.locator("#currentWorkspaceText")
        initial_text = await btn_text.text_content()
        print(f"Initial workspace: {initial_text}")

        print("\n--- [Step 2] Triggering folder selection (Test Workspace Spaced) ---")
        target_path = r"C:\Agy Studio\Test Workspace Spaced"
        safe_path = target_path.replace("\\", "\\\\")
        await page.evaluate(f'window.__testFolderOverride = "{safe_path}";')
        
        await btn.click()
        await page.wait_for_timeout(1000)

        updated_text = await btn_text.text_content()
        print(f"Updated workspace: {updated_text}")
        assert "Test Workspace Spaced" in updated_text, f"Expected 'Test Workspace Spaced' in {updated_text}"
        
        # Verify disabled state and spinner are cleared
        is_disabled = await btn.is_disabled()
        assert not is_disabled, "Button should be re-enabled after selection"
        btn_html = await btn_text.inner_html()
        assert "animate-spin" not in btn_html, "Spinner must be removed"

        print("\n--- [Step 3] Testing cancellation flow ---")
        await page.evaluate('window.__testFolderOverride = "__CANCEL__";')
        await btn.click()
        await page.wait_for_timeout(1000)
        
        cancelled_text = await btn_text.text_content()
        print(f"Workspace after cancel: {cancelled_text}")
        assert cancelled_text == updated_text, "Workspace must remain unchanged on cancellation"
        btn_html = await btn_text.inner_html()
        assert "animate-spin" not in btn_html, "Spinner must be removed on cancel"

        print("\n--- [Step 4] Checking all 13 Trace Events ---")
        print("Frontend Console Events:")
        for ev in console_events:
            print("  *", ev)

        # Expected frontend events
        expected_fe = [
            "WORKSPACE_PICKER_01_CLICK",
            "WORKSPACE_PICKER_02_NATIVE_SELECT_START",
            "WORKSPACE_PICKER_03_REQUEST_8001",
            "WORKSPACE_PICKER_04_REQUEST_SENT",
            "WORKSPACE_PICKER_11_RESPONSE_RECEIVED",
            "WORKSPACE_PICKER_12_COMPLETE",
            "WORKSPACE_PICKER_13_SPINNER_STOPPED"
        ]
        for fe in expected_fe:
            matched = any(fe in ev for ev in console_events)
            print(f"  [{'PASS' if matched else 'FAIL'}] Event: {fe}")
            assert matched, f"Missing frontend event: {fe}"

        # Expected bridge events from data/bridge_runtime.log
        with open(r"C:\Agy Studio\data\bridge_runtime.log", "r", encoding="utf-8") as f:
            bridge_log = f.read()

        expected_bridge = [
            "WORKSPACE_PICKER_05_BRIDGE_RECEIVED",
            "WORKSPACE_PICKER_06_DIALOG_START",
            "WORKSPACE_PICKER_07_DIALOG_CREATED",
            "WORKSPACE_PICKER_08_DIALOG_VISIBLE",
            "WORKSPACE_PICKER_10_RESPONSE_SENT"
        ]
        print("\nBridge Runtime Events:")
        for be in expected_bridge:
            matched = be in bridge_log
            print(f"  [{'PASS' if matched else 'FAIL'}] Event: {be}")
            assert matched, f"Missing bridge event: {be}"

        # Step 5: Verify persistence in config.json
        with open(r"C:\Agy Studio\data\config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
        print(f"\nPersisted in config.json: {cfg.get('workspace')}")
        assert cfg.get("workspace") == target_path, f"config.json workspace mismatch: {cfg.get('workspace')}"

        await browser.close()
        print("\n==================================================")
        print("ALL END-TO-END TESTS PASSED SUCCESSFULLY!")
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_full_picker_flow())
