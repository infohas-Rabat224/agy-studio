import asyncio
import json
from playwright.async_api import async_playwright

async def test_clicks():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        errors = []
        page.on("pageerror", lambda e: errors.append(f"PAGE_ERROR: {e}"))
        page.on("console", lambda m: errors.append(f"CONSOLE_{m.type}: {m.text}") if m.type == "error" else None)
        
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        
        click_reports = []
        
        # 1. Header Dropdown Buttons
        dropdown_btns = [
            ("headerWsBtn", "wsDropdownMenu"),
            ("headerModeBtn", "modeDropdownMenu"),
            ("headerIntelligenceBtn", "intelDropdownMenu"),
            ("headerAgentBtn", "agentDropdownMenu"),
            ("headerSessionBtn", "sessionDropdownMenu"),
        ]
        
        for btn_id, menu_id in dropdown_btns:
            btn = await page.query_selector(f"#{btn_id}")
            if not btn:
                click_reports.append({"target": btn_id, "status": "NOT_FOUND"})
                continue
            
            # Check state before
            hidden_before = await page.evaluate(f"() => document.getElementById('{menu_id}').classList.contains('hidden')")
            
            # Click
            await btn.click()
            await page.wait_for_timeout(200)
            
            hidden_after = await page.evaluate(f"() => document.getElementById('{menu_id}').classList.contains('hidden')")
            visible_after = await page.evaluate(f"() => {{ const el = document.getElementById('{menu_id}'); return el.offsetWidth > 0 && el.offsetHeight > 0; }}")
            
            click_reports.append({
                "target": btn_id,
                "menu_id": menu_id,
                "hidden_before": hidden_before,
                "hidden_after": hidden_after,
                "visible_after": visible_after,
                "opened_successfully": (hidden_before and not hidden_after and visible_after)
            })
            
            # Close it
            await page.evaluate("() => closeAllDropdowns()")
            await page.wait_for_timeout(100)
            
        # 2. Settings button (gear)
        settings_btn = await page.query_selector("header button[title*='Paramètres']")
        if settings_btn:
            await settings_btn.click()
            await page.wait_for_timeout(200)
            modal_hidden = await page.evaluate("() => document.getElementById('settingsModal').classList.contains('hidden')")
            click_reports.append({
                "target": "settingsBtn",
                "modal_opened": not modal_hidden
            })
            await page.evaluate("() => document.getElementById('settingsModal').classList.add('hidden')")

        # 3. Ctrl+K button
        ctrlk_btn = await page.query_selector("header button[title*='Ctrl+K']")
        if ctrlk_btn:
            await ctrlk_btn.click()
            await page.wait_for_timeout(200)
            modal_hidden = await page.evaluate("() => document.getElementById('commandPaletteModal').classList.contains('hidden')")
            click_reports.append({
                "target": "ctrlkBtn",
                "modal_opened": not modal_hidden
            })
            await page.evaluate("() => document.getElementById('commandPaletteModal').classList.add('hidden')")
            
        # 4. Layer 2 Action Bar buttons
        l2_buttons = [
            ("Nouvelle Session", "sessionModal or prompt"),
            ("Recherche", "commandPaletteModal"),
            ("Fichiers", "fileManagerTab"),
            ("Mémoire", "memoryInspectorModal"),
            ("Plan", "promptInput has /plan"),
            ("Vérifier", "verificationModal"),
            ("Artefacts", "previewPanel"),
            ("Actions", "moreActionsDropdown")
        ]
        
        for name, expected in l2_buttons:
            # Find button in layer 2
            btn = await page.query_selector(f"div.h-9 button:has-text('{name}')")
            if not btn:
                click_reports.append({"layer2_button": name, "status": "NOT_FOUND"})
                continue
            
            try:
                # Try clicking it
                await btn.click(timeout=2000)
                await page.wait_for_timeout(300)
                click_reports.append({"layer2_button": name, "status": "CLICKED_SUCCESSFULLY"})
            except Exception as e:
                click_reports.append({"layer2_button": name, "status": "CLICK_FAILED", "error": str(e)})

        # 5. Check what user means by "all buttons on header menu not actives seems to be blocked"
        # Let's inspect the entire Header DOM structure and computed styles
        header_styles = await page.evaluate("""() => {
            const h = document.querySelector('header');
            const style = window.getComputedStyle(h);
            return {
                pointerEvents: style.pointerEvents,
                zIndex: style.zIndex,
                position: style.position,
                userSelect: style.userSelect,
                opacity: style.opacity,
                display: style.display,
                visibility: style.visibility
            };
        }""")
        
        print("ERRORS:", errors)
        print("REPORTS:", json.dumps(click_reports, indent=2))
        print("HEADER_STYLES:", header_styles)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_clicks())
