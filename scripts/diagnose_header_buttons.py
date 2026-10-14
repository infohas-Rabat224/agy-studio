import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        console_logs = []
        page_errors = []
        page.on("console", lambda m: console_logs.append(f"[{m.type}] {m.text}"))
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        
        print("Navigating to http://127.0.0.1:8000...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        
        print(f"Page errors on load: {page_errors}")
        print(f"Console errors on load: {[l for l in console_logs if 'error' in l.lower()]}")
        
        # Test header buttons
        header_buttons = [
            ("headerWsBtn", "wsDropdownMenu"),
            ("headerModeBtn", "modeDropdownMenu"),
            ("headerIntelligenceBtn", "intelDropdownMenu"),
            ("headerAgentBtn", "agentDropdownMenu"),
            ("headerSessionBtn", "sessionDropdownMenu"),
        ]
        
        results = []
        for btn_id, menu_id in header_buttons:
            btn = await page.query_selector(f"#{btn_id}")
            if not btn:
                results.append((btn_id, "BUTTON_NOT_FOUND"))
                continue
            
            # Check bounding box and elementFromPoint
            box = await btn.bounding_box()
            element_at_point = await page.evaluate(f"""() => {{
                const el = document.getElementById('{btn_id}');
                const rect = el.getBoundingClientRect();
                const topEl = document.elementFromPoint(rect.x + rect.width/2, rect.y + rect.height/2);
                return {{
                    tag: topEl ? topEl.tagName : null,
                    id: topEl ? topEl.id : null,
                    className: topEl ? topEl.className : null,
                    isSame: topEl === el || el.contains(topEl)
                }};
            }}""")
            
            # Click button
            await btn.click()
            await page.wait_for_timeout(300)
            
            menu = await page.query_selector(f"#{menu_id}")
            is_hidden = await page.evaluate(f"() => document.getElementById('{menu_id}').classList.contains('hidden')")
            is_visible = await menu.is_visible() if menu else False
            
            # Check if menu rect is clipped or inside viewport
            menu_rect = await page.evaluate(f"""() => {{
                const el = document.getElementById('{menu_id}');
                if (!el) return null;
                const rect = el.getBoundingClientRect();
                return {{
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    top: rect.top,
                    bottom: rect.bottom,
                    display: window.getComputedStyle(el).display,
                    visibility: window.getComputedStyle(el).visibility,
                    overflow: window.getComputedStyle(el.parentElement).overflow
                }};
            }}""")
            
            results.append({
                "btn_id": btn_id,
                "menu_id": menu_id,
                "element_at_point": element_at_point,
                "is_hidden": is_hidden,
                "is_visible": is_visible,
                "menu_rect": menu_rect
            })
            
            # Close dropdown
            await page.evaluate("() => closeAllDropdowns()")
            await page.wait_for_timeout(200)

        # Also test Layer 2 buttons
        layer2_buttons = [
            "Nouvelle Session",
            "Recherche",
            "Fichiers",
            "Mémoire",
            "Plan",
            "Vérifier",
            "Artefacts"
        ]
        
        l2_results = []
        for text in layer2_buttons:
            el = await page.query_selector(f"button:has-text('{text}')")
            if el:
                box = await el.bounding_box()
                at_point = await page.evaluate(f"""(t) => {{
                    const btns = Array.from(document.querySelectorAll('button'));
                    const b = btns.find(x => x.textContent.includes(t));
                    if (!b) return null;
                    const rect = b.getBoundingClientRect();
                    const topEl = document.elementFromPoint(rect.x + rect.width/2, rect.y + rect.height/2);
                    return {{
                        topTag: topEl ? topEl.tagName : null,
                        topId: topEl ? topEl.id : null,
                        topClass: topEl ? topEl.className : null,
                        isSame: topEl === b || b.contains(topEl)
                    }};
                }}""", text)
                l2_results.append((text, "FOUND", at_point))
            else:
                l2_results.append((text, "NOT_FOUND", None))
        
        # Take full page screenshot
        await page.screenshot(path="data/forensics/screenshots/header_diagnosis.png")
        
        output = {
            "console_logs": console_logs,
            "page_errors": page_errors,
            "header_results": results,
            "layer2_results": l2_results
        }
        print(json.dumps(output, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
