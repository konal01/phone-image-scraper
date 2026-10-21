import asyncio
from playwright.async_api import async_playwright

async def test_flipkart(query: str):
    print("Testing Flipkart for query:", query)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        try:
            url = f"https://www.flipkart.com/search?q={query}"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)
            
            # Find product cards
            items = await page.eval_on_selector_all(
                "div[data-id]",
                """elements => {
                    const results = [];
                    for (const el of elements) {
                        const img = el.querySelector('img');
                        let title = img ? img.getAttribute('alt') : '';
                        const titleEl = el.querySelector('div[class*="4rR01T"], div[class*="KzDlHZ"], a[class*="s1Q9rs"], div[class*="wjcEIp"]');
                        if (titleEl && titleEl.textContent) {
                            title = titleEl.textContent.trim();
                        }
                        if (img && img.src && !img.src.includes('placeholder') && !img.src.includes('data:image')) {
                            results.push({
                                title: title || 'Phone Image',
                                src: img.src
                            });
                        }
                    }
                    return results;
                }"""
            )
            print(f"Flipkart found {len(items)} items:")
            for it in items[:5]:
                print(it)
        except Exception as e:
            print("Flipkart error:", e)
        finally:
            await browser.close()

async def test_amazon(query: str):
    print("\nTesting Amazon for query:", query)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        try:
            url = f"https://www.amazon.in/s?k={query}"
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)
            
            items = await page.eval_on_selector_all(
                "div[data-component-type='s-search-result']",
                """elements => {
                    const results = [];
                    for (const el of elements) {
                        const img = el.querySelector('img.s-image');
                        const titleEl = el.querySelector('h2 a span, h2 span');
                        const title = titleEl ? titleEl.textContent.trim() : (img ? img.getAttribute('alt') : '');
                        if (img && img.src) {
                            results.push({
                                title: title || 'Phone Image',
                                src: img.src
                            });
                        }
                    }
                    return results;
                }"""
            )
            print(f"Amazon found {len(items)} items:")
            for it in items[:5]:
                print(it)
        except Exception as e:
            print("Amazon error:", e)
        finally:
            await browser.close()

async def test_cashify(query: str):
    print("\nTesting Cashify for query:", query)
    from scraper import scrape_cashify_full_radius
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        try:
            items = await scrape_cashify_full_radius(page, query, limit=8)
            print(f"Cashify found {len(items)} items:")
            for it in items[:5]:
                print(" ", it["filename"], "->", it["url"])
        except Exception as e:
            print("Cashify error:", e)
        finally:
            await browser.close()

async def main():
    await test_cashify("iPhone 15")

if __name__ == "__main__":
    asyncio.run(main())
