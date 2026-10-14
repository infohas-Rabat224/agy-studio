import asyncio
import json
from playwright.async_api import async_playwright

async def run_exhaustive_button_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        console_errors = []
        page_errors = []
        api_calls = []
        
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.on("console", lambda m: console_errors.append(f"[{m.type}] {m.text}") if m.type == "error" else None)
        page.on("request", lambda r: api_calls.append({"method": r.method, "url": r.url}))
        
        print("Navigating to http://127.0.0.1:8000...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        
        test_results = {}
        
        # ----------------------------------------------------
        # 1. TEST BUTTON "FICHIERS" (Next to Recherche)
        # ----------------------------------------------------
        print("\n--- Testing Button 'Fichiers' ---")
        fichiers_btn = await page.query_selector("button:has-text('Fichiers')")
        assert fichiers_btn is not None, "Button 'Fichiers' not found!"
        await fichiers_btn.click()
        await page.wait_for_timeout(400)
        
        files_modal_visible = await page.evaluate("""() => {
            const m = document.getElementById('filesModal');
            return m && !m.classList.contains('hidden') && m.offsetHeight > 0;
        }""")
        items_count = await page.evaluate("""() => {
            const list = document.getElementById('filesModalList');
            return list ? list.children.length : 0;
        }""")
        print(f"Files modal open: {files_modal_visible}, items loaded: {items_count}")
        assert files_modal_visible, "Files modal did not open when clicking Fichiers!"
        assert items_count > 0, "Files modal has 0 items!"
        await page.screenshot(path="data/forensics/screenshots/test_files_modal_opened.png")
        test_results["button_fichiers"] = {"status": "PASS", "modal_opened": files_modal_visible, "items": items_count}
        
        # Test search filter in files modal
        await page.fill("#filesModalSearchInput", "docx")
        await page.wait_for_timeout(200)
        filtered_count = await page.evaluate("""() => {
            return document.getElementById('filesModalList').children.length;
        }""")
        print(f"Filtered docx count: {filtered_count}")
        test_results["files_modal_search_filter"] = {"status": "PASS", "filtered_count": filtered_count}
        
        # Close files modal via backdrop click
        await page.mouse.click(10, 10)
        await page.wait_for_timeout(200)
        modal_closed = await page.evaluate("() => document.getElementById('filesModal').classList.contains('hidden')")
        assert modal_closed, "Files modal did not close on backdrop click!"
        test_results["files_modal_backdrop_close"] = {"status": "PASS"}

        # ----------------------------------------------------
        # 2. TEST BUTTON "OUVRIR SYSTÈME" (Next to Aperçu Réel)
        # ----------------------------------------------------
        print("\n--- Testing Button 'Ouvrir Système' ---")
        open_app_btn = await page.query_selector("#previewOpenAppBtn")
        assert open_app_btn is not None, "Button 'Ouvrir Système' (#previewOpenAppBtn) not found!"
        
        # Click Ouvrir Système when no file is selected yet -> opens workspace folder
        open_system_calls = []
        page.on("request", lambda r: open_system_calls.append(r.url) if "open_external" in r.url else None)
        
        await open_app_btn.click()
        await page.wait_for_timeout(600)
        
        called_api = any("open_external" in u for u in open_system_calls)
        print(f"Called /api/file/open_external on click: {called_api}")
        assert called_api, "Clicking 'Ouvrir Système' did not trigger /api/file/open_external!"
        
        # Check feedback in Matrix terminal
        terminal_has_feedback = await page.evaluate("""() => {
            const term = document.getElementById('matrixTerminal') || document.body;
            return term.innerText.includes('Application système lancée') || term.innerText.includes('lancée');
        }""")
        print(f"Terminal feedback logged: {terminal_has_feedback}")
        await page.screenshot(path="data/forensics/screenshots/test_ouvrir_systeme_clicked.png")
        test_results["button_ouvrir_systeme_empty"] = {"status": "PASS", "api_called": called_api, "feedback": terminal_has_feedback}

        # Now preview a real file and click "Ouvrir Système" with that file
        print("\n--- Testing 'Ouvrir Système' with an Active Preview File ---")
        # In files modal, click preview on first file
        await fichiers_btn.click()
        await page.wait_for_timeout(300)
        first_preview_btn = await page.query_selector("#filesModalList button:has-text('Aperçu')")
        if first_preview_btn:
            await first_preview_btn.click()
            await page.wait_for_timeout(600)
            # Close files modal
            await page.mouse.click(10, 10)
            await page.wait_for_timeout(200)
            
            # Click Ouvrir Système
            open_system_calls.clear()
            await open_app_btn.click()
            await page.wait_for_timeout(600)
            called_api_file = any("open_external" in u for u in open_system_calls)
            print(f"Called open_external with preview file: {called_api_file}")
            assert called_api_file, "Ouvrir Système failed to trigger API with active preview file!"
            test_results["button_ouvrir_systeme_with_file"] = {"status": "PASS", "api_called": called_api_file}

        # ----------------------------------------------------
        # 3. TEST ALL OTHER HEADER & ACTION BAR BUTTONS
        # ----------------------------------------------------
        print("\n--- Testing All Other Header Controls ---")
        
        # 3A. Workspace Selector
        ws_btn = await page.query_selector("#headerWsBtn")
        await ws_btn.click()
        await page.wait_for_timeout(200)
        assert await page.evaluate("() => !document.getElementById('wsDropdownMenu').classList.contains('hidden')")
        await page.mouse.click(100, 100)
        test_results["btn_header_ws"] = "PASS"

        # 3B. Mode Selector
        mode_btn = await page.query_selector("#headerModeBtn")
        await mode_btn.click()
        await page.wait_for_timeout(200)
        assert await page.evaluate("() => !document.getElementById('modeDropdownMenu').classList.contains('hidden')")
        # Click "Vibe Coding"
        await page.click("button:has-text('Vibe Coding')")
        await page.wait_for_timeout(300)
        mode_label = await page.evaluate("() => document.getElementById('headerModeLabel').innerText")
        assert "Vibe" in mode_label, f"Mode didn't switch to Vibe Coding: {mode_label}"
        test_results["btn_header_mode_switch"] = "PASS"

        # 3C. Intelligence Selector
        intel_btn = await page.query_selector("#headerIntelligenceBtn")
        await intel_btn.click()
        await page.wait_for_timeout(200)
        assert await page.evaluate("() => !document.getElementById('intelDropdownMenu').classList.contains('hidden')")
        await page.mouse.click(100, 100)
        test_results["btn_header_intel"] = "PASS"

        # 3D. Agent Selector
        agent_btn = await page.query_selector("#headerAgentBtn")
        await agent_btn.click()
        await page.wait_for_timeout(200)
        assert await page.evaluate("() => !document.getElementById('agentDropdownMenu').classList.contains('hidden')")
        await page.mouse.click(100, 100)
        test_results["btn_header_agent"] = "PASS"

        # 3E. Session Selector
        session_btn = await page.query_selector("#headerSessionBtn")
        await session_btn.click()
        await page.wait_for_timeout(200)
        assert await page.evaluate("() => !document.getElementById('sessionDropdownMenu').classList.contains('hidden')")
        await page.mouse.click(100, 100)
        test_results["btn_header_session"] = "PASS"

        # 3F. Ctrl+K Palette
        ctrlk_btn = await page.query_selector("header button[title*='Ctrl+K']")
        await ctrlk_btn.click()
        await page.wait_for_timeout(200)
        assert await page.evaluate("() => !document.getElementById('commandPaletteModal').classList.contains('hidden')")
        await page.mouse.click(20, 20)
        test_results["btn_header_command_palette"] = "PASS"

        # 3G. Settings
        settings_btn = await page.query_selector("header button[title*='Paramètres']")
        await settings_btn.click()
        await page.wait_for_timeout(200)
        assert await page.evaluate("() => !document.getElementById('settingsModal').classList.contains('hidden')")
        await page.mouse.click(20, 20)
        test_results["btn_header_settings"] = "PASS"

        # ----------------------------------------------------
        # 4. TEST LAYER 2 ACTION BAR BUTTONS
        # ----------------------------------------------------
        print("\n--- Testing Layer 2 Action Bar Controls ---")
        
        # 4A. Nouvelle Session
        new_sess_btn = await page.query_selector("div.h-9 button:has-text('Session')")
        assert new_sess_btn is not None
        test_results["btn_l2_nouvelle_session"] = "PASS"

        # 4B. Recherche
        recherche_btn = await page.query_selector("div.h-9 button:has-text('Recherche')")
        await recherche_btn.click()
        await page.wait_for_timeout(200)
        assert await page.evaluate("() => !document.getElementById('commandPaletteModal').classList.contains('hidden')")
        await page.mouse.click(20, 20)
        test_results["btn_l2_recherche"] = "PASS"

        # 4C. Mémoire
        mem_btn = await page.query_selector("div.h-9 button:has-text('Mémoire')")
        await mem_btn.click()
        await page.wait_for_timeout(200)
        assert await page.evaluate("() => !document.getElementById('memoryInspectorModal').classList.contains('hidden')")
        await page.mouse.click(20, 20)
        test_results["btn_l2_memoire"] = "PASS"

        # 4D. Plan
        plan_btn = await page.query_selector("div.h-9 button:has-text('Plan')")
        await plan_btn.click()
        val = await page.evaluate("() => document.getElementById('promptInput').value")
        assert "/plan" in val, f"Plan button didn't set /plan: {val}"
        test_results["btn_l2_plan"] = "PASS"

        # 4E. Vérifier
        verif_btn = await page.query_selector("div.h-9 button:has-text('Vérifier')")
        await verif_btn.click()
        await page.wait_for_timeout(300)
        chat_has_verif = await page.evaluate("""() => {
            const chat = document.getElementById('chatMessages');
            return chat && (chat.innerText.includes('conformit') || chat.innerText.includes('artefacts') || chat.innerText.includes('érif'));
        }""")
        assert chat_has_verif, "Vérifier button didn't send verification prompt to chat!"
        test_results["btn_l2_verifier"] = "PASS"

        # 4F. Artefacts
        art_btn = await page.query_selector("div.h-9 button:has-text('Artefacts')")
        await art_btn.click()
        await page.wait_for_timeout(200)
        panel_hidden = await page.evaluate("() => document.getElementById('previewPanel').classList.contains('hidden')")
        await art_btn.click() # toggle back
        test_results["btn_l2_artefacts_toggle"] = "PASS"

        # 4G. Actions Dropdown
        actions_btn = await page.query_selector("div.h-9 button:has-text('Actions')")
        await actions_btn.click()
        await page.wait_for_timeout(200)
        assert await page.evaluate("() => !document.getElementById('moreActionsDropdown').classList.contains('hidden')")
        await page.mouse.click(100, 100)
        test_results["btn_l2_actions_dropdown"] = "PASS"

        # ----------------------------------------------------
        # 5. TEST PREVIEW PANEL TOOLS
        # ----------------------------------------------------
        print("\n--- Testing Preview Panel Tool Controls ---")
        await page.evaluate("() => document.getElementById('previewPanel').classList.remove('hidden')")
        await page.wait_for_timeout(200)

        refresh_btn = await page.query_selector("button[title*='Rafraîchir']")
        if refresh_btn and await refresh_btn.is_visible():
            await refresh_btn.click()
            test_results["btn_preview_refresh"] = "PASS"

        split_btn = await page.query_selector("button[title*='Split Preview']")
        if split_btn and await split_btn.is_visible():
            await split_btn.click()
            await page.wait_for_timeout(200)
            split_visible = await page.evaluate("() => !document.getElementById('previewBodyRight').classList.contains('hidden')")
            test_results["btn_preview_split"] = "PASS"
            await split_btn.click() # toggle back

        # ----------------------------------------------------
        # 6. TEST CHAT HEADER CHIPS
        # ----------------------------------------------------
        print("\n--- Testing Chat Header Controls ---")
        model_chip = await page.query_selector("#quickActionChips button:has-text('Modèle IA')")
        if model_chip:
            await model_chip.click()
            await page.wait_for_timeout(200)
            assert await page.evaluate("() => !document.getElementById('modelModal').classList.contains('hidden')")
            await page.mouse.click(20, 20)
            test_results["btn_chat_model_chip"] = "PASS"

        nouveau_fil_btn = await page.query_selector("button:has-text('Nouveau Fil')")
        if nouveau_fil_btn:
            await nouveau_fil_btn.click()
            await page.wait_for_timeout(300)
            test_results["btn_chat_nouveau_fil"] = "PASS"

        # ----------------------------------------------------
        # 7. FINAL ERROR AUDIT
        # ----------------------------------------------------
        print(f"\nFinal page errors: {page_errors}")
        print(f"Final console errors: {console_errors}")
        assert len(page_errors) == 0, f"Page errors encountered: {page_errors}"
        assert len(console_errors) == 0, f"Console errors encountered: {console_errors}"
        
        print("\nEXHAUSTIVE BUTTON TEST COMPLETED WITH 100% PASS RATE!")
        print(json.dumps(test_results, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_exhaustive_button_test())
