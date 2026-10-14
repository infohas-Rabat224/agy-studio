import asyncio
import json
from playwright.async_api import async_playwright

async def verify():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        console_errors = []
        page_errors = []
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda m: console_errors.append(f"[{m.type}] {m.text}") if m.type == "error" else None)
        
        print("Navigating to http://127.0.0.1:8000...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        
        print(f"Initial page errors: {page_errors}")
        print(f"Initial console errors: {console_errors}")
        assert len(page_errors) == 0, f"Page errors found: {page_errors}"
        assert len(console_errors) == 0, f"Console errors found: {console_errors}"
        
        # 1. Test clicking Workspace Selector button
        ws_btn = await page.query_selector("#headerWsBtn")
        assert ws_btn is not None, "Workspace button not found"
        await ws_btn.click()
        await page.wait_for_timeout(200)
        ws_visible = await page.evaluate("""() => {
            const m = document.getElementById('wsDropdownMenu');
            return !m.classList.contains('hidden') && m.offsetHeight > 0 && m.offsetWidth > 0;
        }""")
        print(f"Workspace dropdown visible on click: {ws_visible}")
        assert ws_visible, "Workspace dropdown not visible!"
        await page.screenshot(path="data/forensics/screenshots/fixed_ws_dropdown.png")
        
        # Click outside to close
        await page.mouse.click(100, 100)
        await page.wait_for_timeout(200)
        ws_closed = await page.evaluate("() => document.getElementById('wsDropdownMenu').classList.contains('hidden')")
        print(f"Workspace dropdown closed on outside click: {ws_closed}")
        assert ws_closed, "Workspace dropdown did not close on outside click!"
        
        # 2. Test clicking Mode Selector button
        mode_btn = await page.query_selector("#headerModeBtn")
        assert mode_btn is not None, "Mode button not found"
        await mode_btn.click()
        await page.wait_for_timeout(200)
        mode_visible = await page.evaluate("""() => {
            const m = document.getElementById('modeDropdownMenu');
            return !m.classList.contains('hidden') && m.offsetHeight > 0 && m.offsetWidth > 0;
        }""")
        print(f"Mode dropdown visible on click: {mode_visible}")
        assert mode_visible, "Mode dropdown not visible!"
        await page.screenshot(path="data/forensics/screenshots/fixed_mode_dropdown.png")
        
        # Click outside to close
        await page.mouse.click(100, 100)
        await page.wait_for_timeout(200)

        # 3. Test clicking Intelligence button
        intel_btn = await page.query_selector("#headerIntelligenceBtn")
        assert intel_btn is not None, "Intelligence button not found"
        await intel_btn.click()
        await page.wait_for_timeout(200)
        intel_visible = await page.evaluate("""() => {
            const m = document.getElementById('intelDropdownMenu');
            return !m.classList.contains('hidden') && m.offsetHeight > 0 && m.offsetWidth > 0;
        }""")
        print(f"Intelligence dropdown visible on click: {intel_visible}")
        assert intel_visible, "Intelligence dropdown not visible!"
        await page.screenshot(path="data/forensics/screenshots/fixed_intel_dropdown.png")
        
        # Click outside to close
        await page.mouse.click(100, 100)
        await page.wait_for_timeout(200)

        # 4. Test clicking Agent button
        agent_btn = await page.query_selector("#headerAgentBtn")
        assert agent_btn is not None, "Agent button not found"
        await agent_btn.click()
        await page.wait_for_timeout(200)
        agent_visible = await page.evaluate("""() => {
            const m = document.getElementById('agentDropdownMenu');
            return !m.classList.contains('hidden') && m.offsetHeight > 0 && m.offsetWidth > 0;
        }""")
        print(f"Agent dropdown visible on click: {agent_visible}")
        assert agent_visible, "Agent dropdown not visible!"
        await page.screenshot(path="data/forensics/screenshots/fixed_agent_dropdown.png")
        
        # Click outside to close
        await page.mouse.click(100, 100)
        await page.wait_for_timeout(200)

        # 5. Test clicking Session button
        session_btn = await page.query_selector("#headerSessionBtn")
        assert session_btn is not None, "Session button not found"
        await session_btn.click()
        await page.wait_for_timeout(200)
        session_visible = await page.evaluate("""() => {
            const m = document.getElementById('sessionDropdownMenu');
            return !m.classList.contains('hidden') && m.offsetHeight > 0 && m.offsetWidth > 0;
        }""")
        print(f"Session dropdown visible on click: {session_visible}")
        assert session_visible, "Session dropdown not visible!"
        await page.screenshot(path="data/forensics/screenshots/fixed_session_dropdown.png")
        
        # Click outside to close
        await page.mouse.click(100, 100)
        await page.wait_for_timeout(200)

        # 6. Test Settings button (gear)
        settings_btn = await page.query_selector("header button[title*='Paramètres']")
        assert settings_btn is not None, "Settings button not found"
        await settings_btn.click()
        await page.wait_for_timeout(200)
        settings_open = await page.evaluate("() => !document.getElementById('settingsModal').classList.contains('hidden')")
        print(f"Settings modal open: {settings_open}")
        assert settings_open, "Settings modal did not open!"
        # Click backdrop to close
        await page.mouse.click(20, 20)
        await page.wait_for_timeout(200)
        settings_closed = await page.evaluate("() => document.getElementById('settingsModal').classList.contains('hidden')")
        print(f"Settings modal closed via backdrop click: {settings_closed}")
        assert settings_closed, "Settings modal did not close on backdrop click!"

        # 7. Test Command Palette (Ctrl+K button)
        ctrlk_btn = await page.query_selector("header button[title*='Ctrl+K']")
        assert ctrlk_btn is not None, "Ctrl+K button not found"
        await ctrlk_btn.click()
        await page.wait_for_timeout(200)
        cp_open = await page.evaluate("() => !document.getElementById('commandPaletteModal').classList.contains('hidden')")
        print(f"Command palette modal open: {cp_open}")
        assert cp_open, "Command palette did not open!"
        # Click backdrop to close
        await page.mouse.click(20, 20)
        await page.wait_for_timeout(200)
        cp_closed = await page.evaluate("() => document.getElementById('commandPaletteModal').classList.contains('hidden')")
        print(f"Command palette modal closed via backdrop click: {cp_closed}")
        assert cp_closed, "Command palette did not close on backdrop click!"

        # 8. Test Layer 2 "Actions" dropdown
        actions_btn = await page.query_selector("div.h-9 button:has-text('Actions')")
        assert actions_btn is not None, "Actions button in Layer 2 not found"
        await actions_btn.click()
        await page.wait_for_timeout(200)
        actions_visible = await page.evaluate("""() => {
            const m = document.getElementById('moreActionsDropdown');
            return !m.classList.contains('hidden') && m.offsetHeight > 0 && m.offsetWidth > 0;
        }""")
        print(f"Actions dropdown in Layer 2 visible: {actions_visible}")
        assert actions_visible, "Actions dropdown in Layer 2 not visible!"
        await page.screenshot(path="data/forensics/screenshots/fixed_actions_dropdown.png")
        
        # Click outside to close
        await page.mouse.click(100, 100)
        await page.wait_for_timeout(200)
        actions_closed = await page.evaluate("() => document.getElementById('moreActionsDropdown').classList.contains('hidden')")
        print(f"Actions dropdown closed: {actions_closed}")
        assert actions_closed, "Actions dropdown did not close!"

        # 9. Test remaining Layer 2 buttons
        l2_buttons = ["Recherche", "Fichiers", "Mémoire", "Plan", "Vérifier", "Artefacts"]
        for btn_text in l2_buttons:
            b = await page.query_selector(f"div.h-9 button:has-text('{btn_text}')")
            assert b is not None, f"Button '{btn_text}' not found in Layer 2"
            box = await b.bounding_box()
            assert box is not None and box['width'] > 0 and box['height'] > 0
            # Test that element at point is clickable and not blocked
            at_point = await page.evaluate(f"""(txt) => {{
                const btns = Array.from(document.querySelectorAll('div.h-9 button'));
                const target = btns.find(x => x.textContent.includes(txt));
                const r = target.getBoundingClientRect();
                const top = document.elementFromPoint(r.x + r.width/2, r.y + r.height/2);
                return top === target || target.contains(top);
            }}""", btn_text)
            print(f"Button '{btn_text}' clickable directly: {at_point}")
            assert at_point, f"Button '{btn_text}' is blocked by an overlay!"

        print("\nALL HEADER MENU AND ACTION BAR BUTTONS VERIFIED FUNCTIONAL AND UNBLOCKED!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify())
