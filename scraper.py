import asyncio
import re
import urllib.parse
import sys
import subprocess
from typing import List, Dict, Optional, Set
from playwright.async_api import async_playwright

_browser_lock = None

def _get_browser_lock():
    global _browser_lock
    if _browser_lock is None:
        _browser_lock = asyncio.Lock()
    return _browser_lock

async def ensure_playwright_browsers() -> bool:
    """
    Ensures that Playwright Chromium browser binaries are installed.
    Runs 'python -m playwright install chromium' if missing.
    """
    lock = _get_browser_lock()
    async with lock:
        loop = asyncio.get_running_loop()
        def _install():
            print("[Playwright] Checking/installing Chromium browser binary...", flush=True)
            try:
                res = subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                print(f"[Playwright] Install completed with exit code: {res.returncode}", flush=True)
                if res.stdout:
                    print(f"[Playwright] stdout: {res.stdout.strip()}", flush=True)
                if res.stderr:
                    print(f"[Playwright] stderr: {res.stderr.strip()}", flush=True)
                return res.returncode == 0
            except Exception as e:
                print(f"[Playwright] Install failed: {e}", flush=True)
                return False

        return await loop.run_in_executor(None, _install)


# Official Brand Mapping
OFFICIAL_BRANDS = {
    "apple": {"name": "Apple", "domains": ["apple.com", "apple.com/newsroom"]},
    "iphone": {"name": "Apple", "domains": ["apple.com", "apple.com/newsroom"]},
    "samsung": {"name": "Samsung", "domains": ["samsung.com", "news.samsung.com"]},
    "galaxy": {"name": "Samsung", "domains": ["samsung.com", "news.samsung.com"]},
    "nothing": {"name": "Nothing", "domains": ["nothing.tech"]},
    "oneplus": {"name": "OnePlus", "domains": ["oneplus.com"]},
    "one plus": {"name": "OnePlus", "domains": ["oneplus.com"]},
    "xiaomi": {"name": "Xiaomi", "domains": ["mi.com"]},
    "redmi": {"name": "Redmi", "domains": ["mi.com"]},
    "poco": {"name": "POCO", "domains": ["po.co"]},
    "realme": {"name": "Realme", "domains": ["realme.com"]},
    "vivo": {"name": "Vivo", "domains": ["vivo.com"]},
    "iqoo": {"name": "iQOO", "domains": ["iqoo.com"]},
    "motorola": {"name": "Motorola", "domains": ["motorola.com", "motorola.in"]},
    "moto": {"name": "Motorola", "domains": ["motorola.com"]},
    "nokia": {"name": "Nokia", "domains": ["hmd.com", "nokia.com"]},
    "hmd": {"name": "HMD", "domains": ["hmd.com"]},
    "infinix": {"name": "Infinix", "domains": ["infinixmobility.com"]},
    "oppo": {"name": "Oppo", "domains": ["oppo.com"]},
    "google": {"name": "Google", "domains": ["store.google.com", "blog.google"]},
    "pixel": {"name": "Google", "domains": ["store.google.com"]},
    "tecno": {"name": "Tecno", "domains": ["tecno-mobile.com"]},
    "honor": {"name": "Honor", "domains": ["honor.com"]},
    "asus": {"name": "Asus", "domains": ["asus.com", "rog.asus.com"]},
    "rog": {"name": "Asus", "domains": ["rog.asus.com"]},
    "sony": {"name": "Sony", "domains": ["sony.com"]},
    "xperia": {"name": "Sony", "domains": ["sony.com"]}
}

KNOWN_COLORS = [
    # Apple Titanium & Classic
    "Desert Titanium", "Natural Titanium", "White Titanium", "Black Titanium", "Blue Titanium",
    "Space Black", "Deep Purple", "Sierra Blue", "Alpine Green", "Pacific Blue",
    "Space Gray", "Midnight", "Starlight", "Silver", "Gold", "Rose Gold", "Product Red",
    "Ultramarine", "Teal", "Pink", "Yellow", "Green", "Blue", "Black", "White", "Purple",
    # Samsung
    "Titanium Gray", "Titanium Black", "Titanium Violet", "Titanium Yellow", "Titanium Silver",
    "Marble Gray", "Onyx Black", "Cobalt Violet", "Amber Yellow", "Jade Green", "Sandstone Orange",
    "Phantom Black", "Phantom White", "Phantom Silver", "Bora Purple", "Cream", "Lavender",
    # Google Pixel
    "Obsidian", "Porcelain", "Hazel", "Rose", "Bay", "Mint", "Snow", "Stormy Black",
    "Lemongrass", "Kinda Coral", "Sorta Sunny", "Peony", "Wintergreen",
    # OnePlus / Nothing / Realme / Vivo / Oppo / Infinix
    "Flowy Emerald", "Silky Black", "Eternal Green", "Titan Black", "Emerald Green", "Glacial White",
    "Dark Gray", "Dark Grey", "Milk White", "Milk", "Grey", "Orange", "Racing Grey",
    "Titan Gold", "Vintage Green", "Obsidian Black", "Sunset Gold", "Sunrise Orange",
    "Oasis Green", "Pioneer Green", "Dreamy Purple", "Feather Green", "Emerald Green",
    "Mirror Black", "Dazzling Gold", "Aurora Green", "Cosmic Black", "Frost Blue", "Starlight Blue",
    "Forest Green", "Shadow Black", "Cyan", "Coral", "Midnight Blue"
]


def sanitize_token(s: str) -> str:
    """Sanitizes text for filesystem compatibility."""
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s-]+', '_', s)
    return s.strip('_')


def detect_brand_info(query: str, title: str = "") -> Dict[str, str]:
    """Detects brand name and official primary domain prioritizing query."""
    q_lower = query.lower()
    for key, data in OFFICIAL_BRANDS.items():
        if re.search(rf"\b{re.escape(key)}\b", q_lower):
            return {"name": data["name"], "domain": data["domains"][0]}

    t_lower = title.lower()
    for key, data in OFFICIAL_BRANDS.items():
        if re.search(rf"\b{re.escape(key)}\b", t_lower):
            return {"name": data["name"], "domain": data["domains"][0]}

    return {"name": "", "domain": ""}


FACE_SEQUENCE = ["Front", "Back", "Camera", "Side", "Angle_3D", "Display_On", "Profile_Left", "Profile_Right", "Packaging"]


def clean_search_query(q: str) -> str:
    """Cleans phone search terms by removing parentheses, RAM specifications, and extra commas."""
    q = re.sub(r'\([^\)]*RAM[^\)]*\)', '', q, flags=re.I)
    q = re.sub(r'\b\d+\s*GB\s*RAM\b', '', q, flags=re.I)
    q = re.sub(r'[\(\),]', ' ', q)
    return re.sub(r'\s+', ' ', q).strip()


def extract_detailed_naming(
    title: str,
    query: str,
    index: int = 1,
    angle_hint: str = "",
    source_hint: str = ""
) -> Dict[str, str]:
    """
    Extracts brand, model, storage size, colour, and angle.
    Returns: {Brand}_{Model}_{Storage}_{Colour}_{View}_{Index}.jpg
    """
    # 1. Detect Brand
    brand_info = detect_brand_info(query, title)
    detected_brand = brand_info["name"]

    # 2. Extract Storage Size (e.g. 128GB, 256GB, 512GB, 1TB)
    detected_storage = ""
    storage_match = re.search(r'\b(128\s*GB|256\s*GB|512\s*GB|1\s*TB|64\s*GB|2\s*TB|128GB|256GB|512GB|1TB|64GB)\b', title, re.I)
    if not storage_match:
        storage_match = re.search(r'\b(128\s*GB|256\s*GB|512\s*GB|1\s*TB|64\s*GB|2\s*TB|128GB|256GB|512GB|1TB|64GB)\b', query, re.I)

    if storage_match:
        detected_storage = re.sub(r'\s+', '', storage_match.group(1)).upper()

    # 3. Extract Colour
    detected_color = ""
    # Try Flipkart / ecommerce pattern: "(Color, Storage)"
    paren_match = re.search(r'\(([^,]+),\s*\d+\s*(?:GB|TB)', title, re.I)
    if paren_match:
        cand = paren_match.group(1).strip()
        if len(cand) > 1 and not re.search(r'^\d', cand):
            detected_color = cand

    if not detected_color:
        for c in KNOWN_COLORS:
            if re.search(rf"\b{re.escape(c)}\b", title, re.I):
                detected_color = c
                break

    if not detected_color:
        for c in KNOWN_COLORS:
            if re.search(rf"\b{re.escape(c)}\b", query, re.I):
                detected_color = c
                break

    # 4. Clean Model Name
    clean_model_str = title if title and len(title) > len(query) else query
    # Strip parentheses with specs/colors
    base_model = re.sub(r'\([^\)]*\)', '', clean_model_str)
    # Strip RAM e.g. 12 GB RAM
    base_model = re.sub(r'\b\d+\s*GB\s*RAM\b', '', base_model, flags=re.I)
    # Strip storage
    base_model = re.sub(r'\b(?:64|128|256|512|1024)\s*(?:GB|TB)\b', '', base_model, flags=re.I)
    # Strip detected color if present in base_model string
    if detected_color:
        base_model = re.sub(rf'\b{re.escape(detected_color)}\b', '', base_model, flags=re.I)
    # Strip trailing commas, dashes, symbols
    base_model = re.sub(r'[\(\),-]', ' ', base_model)
    base_model = re.sub(r'\s+', ' ', base_model).strip()

    if len(base_model) < 2:
        base_model = re.sub(r'[\(\),]', ' ', query)
        base_model = re.sub(r'\s+', ' ', base_model).strip()

    if detected_brand and not base_model.lower().startswith(detected_brand.lower()):
        full_model = f"{detected_brand} {base_model}"
    else:
        full_model = base_model

    # 5. Angle / View detection
    detected_angle = angle_hint
    if not detected_angle:
        if re.search(r'\b(back|rear)\b', title, re.I):
            detected_angle = "Back"
        elif re.search(r'\b(front|display|screen|face)\b', title, re.I):
            detected_angle = "Front"
        elif re.search(r'\b(side|edge|profile)\b', title, re.I):
            detected_angle = "Side"
        elif re.search(r'\b(camera|lens|bump)\b', title, re.I):
            detected_angle = "Camera"
        elif re.search(r'\b(all\s*colors|palette|lineup|group)\b', title, re.I):
            detected_angle = "All_Colors"
        else:
            detected_angle = "Front" if index == 1 else f"View_{index:02d}"

    # Build detailed filename: {Brand_Model}_{Storage}_{Color}_{Angle}_{Index}.jpg
    parts = []
    parts.append(sanitize_token(full_model))

    if detected_storage:
        parts.append(detected_storage)

    if detected_color:
        parts.append(sanitize_token(detected_color))

    if detected_angle:
        parts.append(sanitize_token(detected_angle))

    parts.append(f"{index:02d}")
    filename = "_".join(parts) + ".jpg"

    return {
        "filename": filename,
        "brand": detected_brand or "Smartphone",
        "model": full_model,
        "storage": detected_storage or "All",
        "color": detected_color or "Standard / Official",
        "angle": detected_angle
    }


def upgrade_flipkart_url(url: str) -> str:
    """Upgrades Flipkart thumbnail URLs to uncompressed master high-res (1200x1200 or 834x834)."""
    return re.sub(r'/image/\d+/\d+/', '/image/1200/1200/', url)


def upgrade_amazon_url(url: str) -> str:
    """Upgrades Amazon thumbnail URLs to high-resolution unscaled master assets."""
    return re.sub(r'\._[A-Za-z0-9_,-]+_\.', '.', url)


def upgrade_ebay_url(url: str) -> str:
    """Upgrades eBay thumbnail URLs to maximum uncompressed resolution (s-l1600.jpg)."""
    return re.sub(r's-l\d+\.(?:jpg|jpeg|webp|png)', 's-l1600.jpg', url)


def upgrade_alamy_url(url: str) -> str:
    """Upgrades Alamy zoom levels to highest tier (zooms/9/)."""
    return re.sub(r'/zooms/[0-8]/', '/zooms/9/', url)


def upgrade_indiamart_url(url: str) -> str:
    """Upgrades IndiaMART thumbnail dimensions to 1000x1000 master images."""
    return re.sub(r'/(?:125x125|250x250|300x300|500x500)/', '/1000x1000/', url)


async def scrape_official_brand_portals(page, query: str, limit: int = 40) -> List[Dict[str, str]]:
    """
    Deep crawl of official brand websites, newsrooms, and press kits.
    Covers Apple, Samsung, Nothing, OnePlus, Xiaomi, Vivo, iQOO, Realme,
    Motorola, Nokia/HMD, Infinix, Oppo, Google Pixel, etc.
    """
    clean_q = clean_search_query(query)
    brand_info = detect_brand_info(query)
    brand_name = brand_info["name"]
    brand_domain = brand_info["domain"]

    search_queries = [
        f"{brand_name} {clean_q} front back camera view render" if brand_name else f"{clean_q} front back view render",
        f"{clean_q} official product press renders all colors",
        f"{clean_q} official press images angles"
    ]
    if brand_domain:
        search_queries.insert(0, f"site:{brand_domain} {clean_q} official press")
        search_queries.append(f"{brand_name} {clean_q} press kit renders")

    results = []
    seen = set()

    for q in search_queries:
        if len(results) >= limit:
            break
        encoded = urllib.parse.quote_plus(q)
        url = f"https://www.bing.com/images/search?q={encoded}&qft=+filterui:imagesize-large"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(700)

            items = await page.eval_on_selector_all(
                'a.iusc',
                """elements => {
                    const list = [];
                    for (const el of elements) {
                        const m = el.getAttribute('m');
                        if (!m) continue;
                        try {
                            const data = JSON.parse(m);
                            if (data.murl) {
                                list.push({
                                    url: data.murl,
                                    title: data.t || el.getAttribute('aria-label') || 'Official Press Asset',
                                    domain: data.purl || 'Official Source'
                                });
                            }
                        } catch(e) {}
                    }
                    return list;
                }"""
            )

            for item in items:
                img_url = item["url"]
                if img_url in seen:
                    continue
                if any(x in img_url.lower() for x in ["icon", "logo", "avatar", "sprite", "blank-face"]):
                    continue

                seen.add(img_url)

                t_lower = (item["title"] or "").lower()
                detected_angle = ""
                if "back" in t_lower or "rear" in t_lower:
                    detected_angle = "Back"
                elif "camera" in t_lower or "lens" in t_lower:
                    detected_angle = "Camera"
                elif "side" in t_lower or "profile" in t_lower:
                    detected_angle = "Side"
                elif "front" in t_lower or "display" in t_lower:
                    detected_angle = "Front"
                elif "angle" in t_lower or "isometric" in t_lower:
                    detected_angle = "Angle_3D"

                meta = extract_detailed_naming(
                    title=item["title"],
                    query=query,
                    index=len(results) + 1,
                    angle_hint=detected_angle,
                    source_hint="Official"
                )
                source_label = f"Official ({brand_name})" if brand_name else "Official Press"
                results.append({
                    "title": item["title"],
                    "url": img_url,
                    "source": source_label,
                    "filename": meta["filename"],
                    "color": meta["color"],
                    "storage": meta["storage"],
                    "angle": meta["angle"],
                    "model": meta["model"]
                })
                if len(results) >= limit:
                    break
        except Exception as e:
            print(f"[!] Official brand crawl error for '{q}': {e}")
            continue

    return results


async def scrape_flipkart_full_radius(page, query: str, limit: int = 64) -> List[Dict[str, str]]:
    """
    Full-radius deep crawl of Flipkart:
    1. Searches for clean query.
    2. Deep dives into top matching mobile products to extract ALL gallery faces
       (Front, Back, Camera, Side, Angle_3D, Display_On, etc.).
    3. Gathers multiple colorways and storage variants.
    """
    clean_q = clean_search_query(query)
    encoded = urllib.parse.quote_plus(clean_q)
    results = []
    seen = set()

    max_pages = 1 if limit <= 32 else (2 if limit <= 128 else 4)
    all_cards = []

    for page_num in range(1, max_pages + 1):
        search_url = f"https://www.flipkart.com/search?q={encoded}&page={page_num}"
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(800)

            cards = await page.eval_on_selector_all(
                "div[data-id]",
                """elements => {
                    const list = [];
                    for (const el of elements) {
                        const img = el.querySelector('img');
                        const link = el.querySelector('a');
                        const titleEl = el.querySelector('div[class*="4rR01T"], div[class*="KzDlHZ"], a[class*="s1Q9rs"], div[class*="wjcEIp"], a[title]');
                        let title = titleEl ? (titleEl.getAttribute('title') || titleEl.innerText) : '';
                        if (!title && img) title = img.getAttribute('alt') || '';
                        if (img && img.src && !img.src.includes('placeholder')) {
                            list.push({
                                title: title.trim(),
                                src: img.src,
                                href: link ? link.href : null
                            });
                        }
                    }
                    return list;
                }"""
            )

            if not cards:
                break

            all_cards.extend(cards)
            if len(all_cards) >= 30:
                break
        except Exception:
            break

    # Filter out accessories (cases, screen guards, chargers)
    valid_cards = []
    bad_tokens = ['screen guard', 'back cover', 'tempered glass', 'case cover', 'skin', 'pouch', 'protector', 'cable', 'strap', 'charger', 'adapter']
    for c in all_cards:
        t = (c.get('title') or '').lower()
        if any(b in t for b in bad_tokens):
            continue
        if len(c.get('title', '')) > 4 and c.get('href'):
            # Score card relevancy
            score = 10
            q_lower = clean_q.lower()
            for word in q_lower.split():
                if len(word) >= 2 and word in t:
                    score += 20
            valid_cards.append((score, c))

    valid_cards.sort(key=lambda x: x[0], reverse=True)

    # 1. Deep Dive into top matching products to extract ALL faces / angles
    top_targets = valid_cards[:4]
    for score, card in top_targets:
        if len(results) >= limit:
            break
        try:
            await page.goto(card["href"], wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(700)

            detailed_title = await page.eval_on_selector('span.B_NuCI, h1', 'el => el.innerText') or card["title"]

            # Extract gallery faces from product page
            gallery_srcs = await page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('picture img, div[class*="OfydJ4"] img, img')).map(i => i.src);
                const unique = [];
                for (const s of imgs) {
                    if (!s || !s.includes('/mobile/')) continue;
                    // Exclude recommendation carousel (530/710) and tiny swatches (80/80)
                    if (s.includes('/530/710/') || s.includes('/80/80/')) continue;
                    if (s.includes('cms-brand') || s.includes('batman-returns')) continue;
                    if (!unique.includes(s)) unique.push(s);
                }
                return unique;
            }""")

            for face_idx, g_src in enumerate(gallery_srcs):
                high_res = upgrade_flipkart_url(g_src)
                if high_res not in seen:
                    seen.add(high_res)
                    angle = FACE_SEQUENCE[face_idx] if face_idx < len(FACE_SEQUENCE) else f"Angle_{face_idx + 1:02d}"
                    meta = extract_detailed_naming(
                        title=detailed_title,
                        query=query,
                        index=len(results) + 1,
                        angle_hint=angle,
                        source_hint="Flipkart"
                    )
                    results.append({
                        "title": detailed_title,
                        "url": high_res,
                        "source": "Flipkart",
                        "filename": meta["filename"],
                        "color": meta["color"],
                        "storage": meta["storage"],
                        "angle": meta["angle"],
                        "model": meta["model"]
                    })
                    if len(results) >= limit:
                        break
        except Exception as e:
            print(f"[!] Flipkart deep variant error: {e}")

    # 2. Add remaining color variant cards from search results
    for score, card in valid_cards:
        if len(results) >= limit:
            break
        high_res = upgrade_flipkart_url(card["src"])
        if high_res not in seen:
            seen.add(high_res)
            meta = extract_detailed_naming(
                title=card["title"],
                query=query,
                index=len(results) + 1,
                angle_hint="Front",
                source_hint="Flipkart"
            )
            results.append({
                "title": card["title"],
                "url": high_res,
                "source": "Flipkart",
                "filename": meta["filename"],
                "color": meta["color"],
                "storage": meta["storage"],
                "angle": meta["angle"],
                "model": meta["model"]
            })

    return results


async def scrape_gsmarena_full_radius(page, query: str, limit: int = 30) -> List[Dict[str, str]]:
    """
    Scrapes GSMArena official studio pictures, color plates, and specs assets.
    """
    clean_q = clean_search_query(query)
    search_terms = [
        f"{clean_q} site:gsmarena.com official pictures",
        f"{clean_q} gsmarena camera review photos"
    ]
    results = []
    seen = set()

    for st in search_terms:
        if len(results) >= limit:
            break
        encoded = urllib.parse.quote_plus(st)
        url = f"https://www.bing.com/images/search?q={encoded}&qft=+filterui:imagesize-large"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(700)

            items = await page.eval_on_selector_all(
                'a.iusc',
                """elements => {
                    const list = [];
                    for (const el of elements) {
                        const m = el.getAttribute('m');
                        if (!m) continue;
                        try {
                            const data = JSON.parse(m);
                            if (data.murl && data.murl.includes('gsmarena')) {
                                list.push({
                                    url: data.murl,
                                    title: data.t || 'GSMArena Studio Plate'
                                });
                            }
                        } catch(e) {}
                    }
                    return list;
                }"""
            )

            for item in items:
                if item["url"] not in seen:
                    seen.add(item["url"])
                    meta = extract_detailed_naming(
                        title=item["title"],
                        query=query,
                        index=len(results) + 1,
                        source_hint="GSMArena"
                    )
                    results.append({
                        "title": item["title"],
                        "url": item["url"],
                        "source": "GSMArena Studio",
                        "filename": meta["filename"],
                        "color": meta["color"],
                        "storage": meta["storage"],
                        "angle": meta["angle"],
                        "model": meta["model"]
                    })
                    if len(results) >= limit:
                        break
        except Exception as e:
            print(f"[!] GSMArena scrape error: {e}")

    return results


async def scrape_amazon_full_radius(page, query: str, limit: int = 30) -> List[Dict[str, str]]:
    """
    Scrapes Amazon India across color variants and multi-face product galleries.
    """
    clean_q = clean_search_query(query)
    encoded = urllib.parse.quote_plus(clean_q)
    url = f"https://www.amazon.in/s?k={encoded}"
    results = []
    seen = set()

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(900)

        items = await page.eval_on_selector_all(
            "div[data-component-type='s-search-result']",
            """elements => {
                const list = [];
                for (const el of elements) {
                    const img = el.querySelector('img.s-image');
                    if (!img || !img.src) continue;
                    let src = img.src;
                    if (src.includes('sprite') || src.includes('transparent-pixel')) continue;

                    let title = '';
                    const link = el.querySelector('h2 a, a.a-link-normal[href*="/dp/"]');
                    if (link && link.innerText) title = link.innerText;
                    else if (img.alt) title = img.alt;
                    title = title.replace(/^Sponsored Ad - /i, '').trim();

                    const href = link ? link.href : null;
                    if (title && src) {
                        list.push({ title, src, href });
                    }
                }
                return list;
            }"""
        )

        # Filter out covers/cases
        valid_items = []
        bad_tokens = ['case', 'cover', 'screen guard', 'tempered glass', 'skin', 'pouch', 'protector', 'cable', 'strap']
        for it in items:
            t = (it.get("title") or "").lower()
            if any(b in t for b in bad_tokens):
                continue
            valid_items.append(it)

        # 1. Visit top matching Amazon phone product page for multi-angle gallery
        if valid_items and valid_items[0].get("href"):
            top_link = valid_items[0]["href"]
            try:
                await page.goto(top_link, wait_until="domcontentloaded", timeout=12000)
                await page.wait_for_timeout(800)

                az_thumbs = await page.eval_on_selector_all(
                    "#altImages ul li img, #imageBlock img",
                    "elements => elements.map(el => el.src).filter(s => s && !s.includes('sprite') && !s.includes('pixel'))"
                )
                for f_idx, t in enumerate(az_thumbs[:8]):
                    hi_res = upgrade_amazon_url(t)
                    if hi_res not in seen:
                        seen.add(hi_res)
                        angle = FACE_SEQUENCE[f_idx] if f_idx < len(FACE_SEQUENCE) else f"Angle_{f_idx + 1:02d}"
                        meta = extract_detailed_naming(
                            title=valid_items[0]["title"],
                            query=query,
                            index=len(results) + 1,
                            angle_hint=angle,
                            source_hint="Amazon"
                        )
                        results.append({
                            "title": valid_items[0]["title"],
                            "url": hi_res,
                            "source": "Amazon India",
                            "filename": meta["filename"],
                            "color": meta["color"],
                            "storage": meta["storage"],
                            "angle": meta["angle"],
                            "model": meta["model"]
                        })
                        if len(results) >= limit:
                            break
            except Exception as e:
                print(f"[!] Amazon gallery deep error: {e}")

        # 2. Add remaining search result cards
        for item in valid_items:
            if len(results) >= limit:
                break
            high_res = upgrade_amazon_url(item["src"])
            if high_res not in seen and len(item["title"]) > 3:
                seen.add(high_res)
                meta = extract_detailed_naming(
                    title=item["title"],
                    query=query,
                    index=len(results) + 1,
                    angle_hint="Front",
                    source_hint="Amazon"
                )
                results.append({
                    "title": item["title"],
                    "url": high_res,
                    "source": "Amazon India",
                    "filename": meta["filename"],
                    "color": meta["color"],
                    "storage": meta["storage"],
                    "angle": meta["angle"],
                    "model": meta["model"]
                })
    except Exception as e:
        print(f"[!] Amazon scrape error: {e}")

    return results


async def scrape_cashify_full_radius(page, query: str, limit: int = 30) -> List[Dict[str, str]]:
    """
    Crawls Cashify (https://www.cashify.in/) for smartphones:
    1. Uses Cashify's search suggestion system to extract exact matching phones & uncompressed xxhdpi master assets.
    2. Deep-dives into top matching phone pages to extract storage variants & product views.
    3. Supplements with targeted Cashify editorial/catalog index search.
    """
    clean_q = clean_search_query(query)
    results = []
    seen = set()

    suggestion_data = None

    async def on_response(response):
        nonlocal suggestion_data
        if "product/search/suggestion" in response.url and response.status == 200:
            try:
                suggestion_data = await response.json()
            except Exception:
                pass

    page.on("response", on_response)

    # 1. Cashify In-Browser Search Suggestion Engine
    try:
        await page.goto("https://www.cashify.in", wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(800)

        await page.evaluate("""() => {
            const el = document.querySelector("input[placeholder*='Search']");
            if (el) (el.closest('div.h-12') || el.parentElement).click();
        }""")
        await page.wait_for_timeout(400)

        await page.keyboard.type(clean_q, delay=50)

        for _ in range(25):
            if suggestion_data:
                break
            await asyncio.sleep(0.2)

        top_slug = None
        if suggestion_data and "dt" in suggestion_data:
            for item in suggestion_data["dt"]:
                img_name = item.get("img")
                if img_name:
                    hi_res = f"https://s3ng.cashify.in/cashify/product/img/xxhdpi/{img_name}"
                    if hi_res not in seen:
                        seen.add(hi_res)
                        title = item.get("pn") or query
                        if not top_slug and item.get("slug"):
                            top_slug = item.get("slug")
                        meta = extract_detailed_naming(
                            title=title,
                            query=query,
                            index=len(results) + 1,
                            angle_hint="Front",
                            source_hint="Cashify"
                        )
                        results.append({
                            "title": title,
                            "url": hi_res,
                            "source": "Cashify",
                            "filename": meta["filename"],
                            "color": meta["color"],
                            "storage": meta["storage"],
                            "angle": meta["angle"],
                            "model": meta["model"]
                        })
                        if len(results) >= limit:
                            break

        # 2. Deep-dive into top product page for additional variants & angles
        if top_slug and len(results) < limit:
            try:
                phone_url = f"https://www.cashify.in{top_slug}" if top_slug.startswith('/') else f"https://www.cashify.in/{top_slug}"
                await page.goto(phone_url, wait_until="domcontentloaded", timeout=10000)
                await page.wait_for_timeout(1000)

                page_imgs = await page.eval_on_selector_all(
                    "img",
                    """elements => elements.map(e => {
                        const raw = e.getAttribute('data-src') || e.src || '';
                        return {
                            src: raw,
                            alt: e.alt || ''
                        };
                    }).filter(x => x.src && (x.src.includes('cashify/product') || x.src.includes('store/product')) && !x.src.includes('star') && !x.src.includes('assured'))"""
                )

                for p_img in page_imgs:
                    raw_src = p_img["src"]
                    clean_src = re.sub(r'\?.*$', '', raw_src)
                    clean_src = clean_src.replace('/xhdpi/', '/xxhdpi/')
                    if clean_src not in seen:
                        seen.add(clean_src)
                        v_title = p_img["alt"] or query
                        meta = extract_detailed_naming(
                            title=v_title,
                            query=query,
                            index=len(results) + 1,
                            angle_hint="Front" if len(results) == 0 else f"View_{len(results)+1:02d}",
                            source_hint="Cashify"
                        )
                        results.append({
                            "title": v_title,
                            "url": clean_src,
                            "source": "Cashify",
                            "filename": meta["filename"],
                            "color": meta["color"],
                            "storage": meta["storage"],
                            "angle": meta["angle"],
                            "model": meta["model"]
                        })
                        if len(results) >= limit:
                            break
            except Exception as e:
                print(f"[!] Cashify detail page error: {e}")

    except Exception as e:
        print(f"[!] Cashify live search error: {e}")

    # 3. Supplemental: Targeted Cashify Editorial / Catalog Index via Bing Images
    if len(results) < limit:
        search_queries = [
            f"site:cashify.in {clean_q} refurbished",
            f"site:s3ng.cashify.in {clean_q}"
        ]
        for sq in search_queries:
            if len(results) >= limit:
                break
            encoded = urllib.parse.quote_plus(sq)
            b_url = f"https://www.bing.com/images/search?q={encoded}&qft=+filterui:imagesize-large"
            try:
                await page.goto(b_url, wait_until="domcontentloaded", timeout=10000)
                await page.wait_for_timeout(600)
                items = await page.eval_on_selector_all(
                    'a.iusc',
                    """elements => {
                        const list = [];
                        for (const el of elements) {
                            const m = el.getAttribute('m');
                            if (!m) continue;
                            try {
                                const data = JSON.parse(m);
                                if (data.murl && (data.murl.includes('cashify') || (data.purl && data.purl.includes('cashify')))) {
                                    list.push({
                                        url: data.murl,
                                        title: data.t || el.getAttribute('aria-label') || 'Cashify Phone Asset'
                                    });
                                }
                            } catch(e) {}
                        }
                        return list;
                    }"""
                )
                for it in items:
                    u = it["url"]
                    if u not in seen and not any(x in u.lower() for x in ["icon", "logo", "avatar", "sprite"]):
                        seen.add(u)
                        meta = extract_detailed_naming(
                            title=it["title"],
                            query=query,
                            index=len(results) + 1,
                            angle_hint="Front" if len(results) == 0 else f"View_{len(results)+1:02d}",
                            source_hint="Cashify"
                        )
                        results.append({
                            "title": it["title"],
                            "url": u,
                            "source": "Cashify",
                            "filename": meta["filename"],
                            "color": meta["color"],
                            "storage": meta["storage"],
                            "angle": meta["angle"],
                            "model": meta["model"]
                        })
                        if len(results) >= limit:
                            break
            except Exception as e:
                print(f"[!] Cashify index search error: {e}")

    return results


async def scrape_fonezone_full_radius(page, query: str, limit: int = 30) -> List[Dict[str, str]]:
    """Crawls FoneZone (https://fonezone.me/) for refurbished / pre-owned smartphones."""
    clean_q = clean_search_query(query)
    encoded = urllib.parse.quote_plus(clean_q)
    url = f"https://fonezone.me/search?type=product&q={encoded}"
    results = []
    seen = set()

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(900)

        items = await page.eval_on_selector_all(
            "li.grid__item, .product-card, .card-wrapper, .grid-item, div[class*='product']",
            """elements => {
                const list = [];
                for (const el of elements) {
                    const img = el.querySelector('img');
                    if (!img) continue;
                    let src = img.getAttribute('data-src') || img.src;
                    if (!src || src.includes('LOGO') || src.includes('icon') || src.includes('badge')) continue;
                    const link = el.querySelector('.card__heading a, .product-title, h3 a, a');
                    let title = link ? link.innerText.trim() : (img.alt || '');
                    if (title && src) {
                        list.push({ title, src, href: link ? link.href : '' });
                    }
                }
                return list;
            }"""
        )

        for it in items:
            raw_src = it["src"]
            hi_res = re.sub(r'([?&]width=)\d+', r'\g<1>1200', raw_src)
            if not hi_res.startswith('http'):
                hi_res = 'https:' + hi_res if hi_res.startswith('//') else 'https://fonezone.me' + hi_res
            if hi_res not in seen and len(it["title"]) > 2:
                seen.add(hi_res)
                meta = extract_detailed_naming(
                    title=it["title"],
                    query=query,
                    index=len(results) + 1,
                    source_hint="FoneZone"
                )
                results.append({
                    "title": it["title"],
                    "url": hi_res,
                    "source": "FoneZone",
                    "filename": meta["filename"],
                    "color": meta["color"],
                    "storage": meta["storage"],
                    "angle": meta["angle"],
                    "model": meta["model"]
                })
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"[!] FoneZone scrape error: {e}")

    return results


async def scrape_gameloot_full_radius(page, query: str, limit: int = 30) -> List[Dict[str, str]]:
    """Crawls GameLoot (https://gameloot.in/) for pre-owned & refurbished smartphones."""
    clean_q = clean_search_query(query)
    encoded = urllib.parse.quote_plus(clean_q)
    url = f"https://gameloot.in/?s={encoded}&post_type=product"
    results = []
    seen = set()

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(900)

        items = await page.eval_on_selector_all(
            "li.product, div.product_item, .type-product",
            """elements => {
                const list = [];
                for (const el of elements) {
                    const img = el.querySelector('img');
                    if (!img) continue;
                    let src = img.getAttribute('data-src') || img.src;
                    const link = el.querySelector('a.product_item_link, .woocommerce-loop-product__title, h2, h3, a');
                    let title = img.alt || (link ? link.innerText.trim() : '');
                    if (title && src) {
                        list.push({ title, src, href: link ? link.href : '' });
                    }
                }
                return list;
            }"""
        )

        for it in items:
            raw_src = it["src"]
            hi_res = re.sub(r'-\d+x\d+(\.[a-zA-Z]+)$', r'\1', raw_src)
            if hi_res not in seen and len(it["title"]) > 2:
                seen.add(hi_res)
                meta = extract_detailed_naming(
                    title=it["title"],
                    query=query,
                    index=len(results) + 1,
                    source_hint="GameLoot"
                )
                results.append({
                    "title": it["title"],
                    "url": hi_res,
                    "source": "GameLoot",
                    "filename": meta["filename"],
                    "color": meta["color"],
                    "storage": meta["storage"],
                    "angle": meta["angle"],
                    "model": meta["model"]
                })
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"[!] GameLoot scrape error: {e}")

    return results


async def scrape_triveniworld_full_radius(page, query: str, limit: int = 30) -> List[Dict[str, str]]:
    """Crawls Triveni World (https://www.triveniworld.com/) for pre-owned / refurbished phones."""
    clean_q = clean_search_query(query)
    encoded = urllib.parse.quote_plus(clean_q)
    url = f"https://www.triveniworld.com/search?type=product&q={encoded}"
    results = []
    seen = set()

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(900)

        items = await page.eval_on_selector_all(
            ".grid-product, .product-item, .card, [data-product-id]",
            """elements => {
                const list = [];
                for (const el of elements) {
                    const img = el.querySelector('img');
                    if (!img) continue;
                    let src = img.getAttribute('data-src') || img.src;
                    const titleEl = el.querySelector('.grid-product__title, .product-item__title, h3, a');
                    let title = titleEl ? titleEl.innerText.trim() : (img.alt || '');
                    if (title && src) {
                        list.push({ title, src, href: titleEl ? titleEl.href : '' });
                    }
                }
                return list;
            }"""
        )

        for it in items:
            raw_src = it["src"]
            hi_res = re.sub(r'([?&]width=)\d+', r'\g<1>1200', raw_src)
            if not hi_res.startswith('http'):
                hi_res = 'https:' + hi_res if hi_res.startswith('//') else 'https://www.triveniworld.com' + hi_res
            if hi_res not in seen and len(it["title"]) > 2:
                seen.add(hi_res)
                meta = extract_detailed_naming(
                    title=it["title"],
                    query=query,
                    index=len(results) + 1,
                    source_hint="Triveni World"
                )
                results.append({
                    "title": it["title"],
                    "url": hi_res,
                    "source": "Triveni World",
                    "filename": meta["filename"],
                    "color": meta["color"],
                    "storage": meta["storage"],
                    "angle": meta["angle"],
                    "model": meta["model"]
                })
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"[!] Triveni World scrape error: {e}")

    return results


async def scrape_vlebazaar_full_radius(page, query: str, limit: int = 30) -> List[Dict[str, str]]:
    """Crawls VleBazaar (https://vlebazaar.in/) via site index for refurbished & unboxed phones."""
    clean_q = clean_search_query(query)
    encoded = urllib.parse.quote_plus(f"site:vlebazaar.in {clean_q}")
    url = f"https://www.bing.com/images/search?q={encoded}&qft=+filterui:imagesize-large"
    results = []
    seen = set()

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(800)

        items = await page.eval_on_selector_all(
            'a.iusc',
            """elements => {
                const list = [];
                for (const el of elements) {
                    const m = el.getAttribute('m');
                    if (!m) continue;
                    try {
                        const data = JSON.parse(m);
                        if (data.murl) {
                            list.push({
                                url: data.murl,
                                title: data.t || 'VleBazaar Phone'
                            });
                        }
                    } catch(e) {}
                }
                return list;
            }"""
        )

        for it in items:
            u = it["url"]
            if u not in seen and len(it["title"]) > 2:
                seen.add(u)
                meta = extract_detailed_naming(
                    title=it["title"],
                    query=query,
                    index=len(results) + 1,
                    source_hint="VleBazaar"
                )
                results.append({
                    "title": it["title"],
                    "url": u,
                    "source": "VleBazaar",
                    "filename": meta["filename"],
                    "color": meta["color"],
                    "storage": meta["storage"],
                    "angle": meta["angle"],
                    "model": meta["model"]
                })
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"[!] VleBazaar scrape error: {e}")

    return results


async def scrape_ebay_full_radius(page, query: str, limit: int = 40) -> List[Dict[str, str]]:
    """
    Crawls eBay smartphone listings and high-resolution product photography.
    Extracts authentic listing photos and upgrades them to master uncompressed resolution (s-l1600.jpg).
    """
    clean_q = clean_search_query(query)
    search_queries = [
        f"site:ebay.com {clean_q} smartphone",
        f"site:i.ebayimg.com {clean_q}",
        f"site:ebay.com {clean_q} phone all colors",
        f"site:ebay.com {clean_q} unboxing render"
    ]
    results = []
    seen = set()

    for q in search_queries:
        if len(results) >= limit:
            break
        encoded = urllib.parse.quote_plus(q)
        url = f"https://www.bing.com/images/search?q={encoded}&qft=+filterui:imagesize-large"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(700)
            items = await page.eval_on_selector_all(
                'a.iusc',
                """elements => {
                    const list = [];
                    for (const el of elements) {
                        try {
                            const m = JSON.parse(el.getAttribute('m'));
                            if (m && m.murl && (m.murl.includes('ebayimg.com') || (m.purl && m.purl.includes('ebay.com')))) {
                                list.push({
                                    title: m.t || m.desc || 'eBay Phone Listing',
                                    url: m.murl
                                });
                            }
                        } catch(e) {}
                    }
                    return list;
                }"""
            )
            for it in items:
                img_url = upgrade_ebay_url(it["url"])
                # Exclude accessories / junk / icons
                lower_title = it["title"].lower()
                if any(x in lower_title for x in ["case only", "screen protector only", "silicone case", "wallet cover", "charger cable"]):
                    continue
                if img_url not in seen and not any(k in img_url.lower() for k in ["icon", "logo", "avatar", "sprite", "1x1"]):
                    seen.add(img_url)
                    meta = extract_detailed_naming(
                        title=it["title"],
                        query=query,
                        index=len(results) + 1,
                        source_hint="eBay"
                    )
                    results.append({
                        "title": it["title"],
                        "url": img_url,
                        "source": "eBay",
                        "filename": meta["filename"],
                        "color": meta["color"],
                        "storage": meta["storage"],
                        "angle": meta["angle"],
                        "model": meta["model"]
                    })
                    if len(results) >= limit:
                        break
        except Exception as e:
            print(f"[!] eBay scrape error: {e}")

    return results


async def scrape_alamy_full_radius(page, query: str, limit: int = 40) -> List[Dict[str, str]]:
    """
    Crawls Alamy stock photography catalog for studio product renders, transparent/white cutouts,
    and multi-angle smartphone photos. Upgrades to maximum zoom resolution (/zooms/9/).
    """
    clean_q = clean_search_query(query)
    results = []
    seen = set()

    # 1. Direct Alamy search
    encoded = urllib.parse.quote_plus(clean_q)
    alamy_url = f"https://www.alamy.com/search.html?qt={encoded}"
    try:
        await page.goto(alamy_url, wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(1000)
        # Scroll to load lazy gallery images
        await page.evaluate("window.scrollBy(0, 1500)")
        await page.wait_for_timeout(700)

        items = await page.eval_on_selector_all(
            "img",
            """imgs => {
                const list = [];
                for (const img of imgs) {
                    const src = img.getAttribute('src') || img.getAttribute('data-src') || '';
                    const alt = img.getAttribute('alt') || '';
                    if (src && src.includes('alamy.com') && (src.includes('/zooms/') || src.includes('/comp/')) && !src.includes('logo') && !src.includes('avatar')) {
                        list.push({ title: alt || 'Alamy Stock Photo', url: src });
                    }
                }
                return list;
            }"""
        )
        for it in items:
            img_url = upgrade_alamy_url(it["url"])
            if img_url not in seen:
                seen.add(img_url)
                meta = extract_detailed_naming(
                    title=it["title"],
                    query=query,
                    index=len(results) + 1,
                    source_hint="Alamy"
                )
                results.append({
                    "title": it["title"],
                    "url": img_url,
                    "source": "Alamy",
                    "filename": meta["filename"],
                    "color": meta["color"],
                    "storage": meta["storage"],
                    "angle": meta["angle"],
                    "model": meta["model"]
                })
                if len(results) >= limit:
                    break
    except Exception as e:
        print(f"[!] Alamy direct scrape error: {e}")

    # 2. Supplemental high-res studio cutouts & renders
    if len(results) < limit:
        search_queries = [
            f"site:alamy.com {clean_q} phone cutout isolated render",
            f"site:alamy.com {clean_q} smartphone back front camera"
        ]
        for q in search_queries:
            if len(results) >= limit:
                break
            url = f"https://www.bing.com/images/search?q={urllib.parse.quote_plus(q)}&qft=+filterui:imagesize-large"
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=12000)
                await page.wait_for_timeout(700)
                items = await page.eval_on_selector_all(
                    'a.iusc',
                    """elements => {
                        const list = [];
                        for (const el of elements) {
                            try {
                                const m = JSON.parse(el.getAttribute('m'));
                                if (m && m.murl && (m.murl.includes('alamy.com') || (m.purl && m.purl.includes('alamy.com')))) {
                                    list.push({
                                        title: m.t || m.desc || 'Alamy Stock Photo',
                                        url: m.murl
                                    });
                                }
                            } catch(e) {}
                        }
                        return list;
                    }"""
                )
                for it in items:
                    img_url = upgrade_alamy_url(it["url"])
                    if img_url not in seen:
                        seen.add(img_url)
                        meta = extract_detailed_naming(
                            title=it["title"],
                            query=query,
                            index=len(results) + 1,
                            source_hint="Alamy"
                        )
                        results.append({
                            "title": it["title"],
                            "url": img_url,
                            "source": "Alamy",
                            "filename": meta["filename"],
                            "color": meta["color"],
                            "storage": meta["storage"],
                            "angle": meta["angle"],
                            "model": meta["model"]
                        })
                        if len(results) >= limit:
                            break
            except Exception as e:
                print(f"[!] Alamy index scrape error: {e}")

    return results


async def scrape_indiamart_full_radius(page, query: str, limit: int = 40) -> List[Dict[str, str]]:
    """
    Crawls IndiaMART verified seller and distributor product catalogs.
    Extracts authentic wholesale & retail phone images upgraded to 1000x1000 master plates.
    """
    clean_q = clean_search_query(query)
    search_queries = [
        f"site:indiamart.com {clean_q} mobile phone",
        f"site:imimg.com {clean_q} mobile phone",
        f"site:indiamart.com {clean_q} smartphone 128gb 256gb"
    ]
    results = []
    seen = set()

    for q in search_queries:
        if len(results) >= limit:
            break
        encoded = urllib.parse.quote_plus(q)
        url = f"https://www.bing.com/images/search?q={encoded}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(700)
            items = await page.eval_on_selector_all(
                'a.iusc',
                """elements => {
                    const list = [];
                    for (const el of elements) {
                        try {
                            const m = JSON.parse(el.getAttribute('m'));
                            if (m && m.murl && (m.murl.includes('imimg.com') || (m.purl && m.purl.includes('indiamart.com')))) {
                                list.push({
                                    title: m.t || m.desc || 'IndiaMART Mobile Phone',
                                    url: m.murl
                                });
                            }
                        } catch(e) {}
                    }
                    return list;
                }"""
            )
            for it in items:
                img_url = upgrade_indiamart_url(it["url"])
                # Filter out generic icons, supplier badges, company logos
                if any(x in img_url.lower() for x in ["logo", "icon", "banner", "loader", "spinner", "blank", "default"]):
                    continue
                if img_url not in seen:
                    seen.add(img_url)
                    meta = extract_detailed_naming(
                        title=it["title"],
                        query=query,
                        index=len(results) + 1,
                        source_hint="IndiaMART"
                    )
                    results.append({
                        "title": it["title"],
                        "url": img_url,
                        "source": "IndiaMART",
                        "filename": meta["filename"],
                        "color": meta["color"],
                        "storage": meta["storage"],
                        "angle": meta["angle"],
                        "model": meta["model"]
                    })
                    if len(results) >= limit:
                        break
        except Exception as e:
            print(f"[!] IndiaMART scrape error: {e}")

    return results



async def scrape_phones(
    query: str,
    limit: int = 48,
    source: str = "all"
) -> List[Dict[str, str]]:
    """
    High-capacity, wide-radius smartphone image scraper.
    Crawls official brand sites (Samsung, Nothing, Apple, Realme, Nokia, Motorola,
    Xiaomi, Vivo, iQOO, OnePlus, Infinix, Oppo, etc.), Flipkart all-colors & angles,
    Amazon India, Cashify, and GSMArena studio.
    """
    async with async_playwright() as p:
        browser = None
        for attempt in range(2):
            try:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                )
                break
            except Exception as launch_err:
                err_text = str(launch_err).lower()
                if attempt == 0 and ("executable doesn't exist" in err_text or "playwright install" in err_text or "not found" in err_text or "chromium" in err_text):
                    print(f"[Playwright] Chromium missing ({launch_err}). Downloading automatically now...", flush=True)
                    await ensure_playwright_browsers()
                    continue
                raise launch_err

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        results: List[Dict[str, str]] = []
        seen_urls: Set[str] = set()

        def add_items(new_items):
            for it in new_items:
                if it["url"] not in seen_urls:
                    seen_urls.add(it["url"])
                    # Re-index filename
                    meta = extract_detailed_naming(
                        title=it["title"],
                        query=query,
                        index=len(results) + 1,
                        angle_hint=it.get("angle", ""),
                        source_hint=it.get("source", "")
                    )
                    it["filename"] = meta["filename"]
                    it["color"] = meta["color"]
                    it["storage"] = meta["storage"]
                    it["angle"] = meta["angle"]
                    it["model"] = meta["model"]
                    results.append(it)
                if len(results) >= limit:
                    break

        # Support comma-separated sources for multiselect
        raw_sources = [s.strip().lower() for s in source.split(",") if s.strip()]
        if not raw_sources or "all" in raw_sources:
            is_all = True
            sources_set = {"all"}
        else:
            is_all = False
            sources_set = set(raw_sources)

        def matches_source(*candidates):
            if is_all:
                return True
            return any(c.lower() in sources_set for c in candidates)

        # 1. Highest Priority: Flipkart Deep Variant & Multi-Angle Crawler
        if matches_source("flipkart", "ecommerce", "amazon_flipkart", "flipkart_amazon", "ecommerce_cashify"):
            fk_target = limit if (not is_all and len(sources_set) == 1) else max(30, int(limit * 0.6))
            fk_items = await scrape_flipkart_full_radius(page, query, limit=fk_target)
            add_items(fk_items)

        # 2. Second Priority: Amazon India
        if matches_source("amazon", "ecommerce", "amazon_flipkart", "flipkart_amazon", "ecommerce_cashify") and len(results) < limit:
            remaining = limit - len(results)
            az_items = await scrape_amazon_full_radius(page, query, limit=remaining)
            add_items(az_items)

        # 3. Third Priority: Cashify (https://www.cashify.in/)
        if matches_source("cashify", "ecommerce_cashify", "refurbished") and len(results) < limit:
            remaining = limit - len(results)
            cashify_items = await scrape_cashify_full_radius(page, query, limit=remaining)
            add_items(cashify_items)

        # 4. FoneZone (https://fonezone.me/)
        if matches_source("fonezone", "refurbished") and len(results) < limit:
            remaining = limit - len(results)
            fz_items = await scrape_fonezone_full_radius(page, query, limit=remaining)
            add_items(fz_items)

        # 5. GameLoot (https://gameloot.in/)
        if matches_source("gameloot", "refurbished") and len(results) < limit:
            remaining = limit - len(results)
            gl_items = await scrape_gameloot_full_radius(page, query, limit=remaining)
            add_items(gl_items)

        # 6. Triveni World (https://www.triveniworld.com/)
        if matches_source("triveniworld", "triveni", "refurbished") and len(results) < limit:
            remaining = limit - len(results)
            tw_items = await scrape_triveniworld_full_radius(page, query, limit=remaining)
            add_items(tw_items)

        # 7. VleBazaar (https://vlebazaar.in/)
        if matches_source("vlebazaar", "refurbished") and len(results) < limit:
            remaining = limit - len(results)
            vle_items = await scrape_vlebazaar_full_radius(page, query, limit=remaining)
            add_items(vle_items)

        # 8. eBay Marketplace & High-Res Listings
        if matches_source("ebay") and len(results) < limit:
            remaining = limit - len(results)
            ebay_items = await scrape_ebay_full_radius(page, query, limit=remaining)
            add_items(ebay_items)

        # 9. Alamy Studio Photography & Transparent Cutouts
        if matches_source("alamy") and len(results) < limit:
            remaining = limit - len(results)
            alamy_items = await scrape_alamy_full_radius(page, query, limit=remaining)
            add_items(alamy_items)

        # 10. IndiaMART Wholesale & Seller Catalog
        if matches_source("indiamart") and len(results) < limit:
            remaining = limit - len(results)
            im_items = await scrape_indiamart_full_radius(page, query, limit=remaining)
            add_items(im_items)

        # 11. Official Brand Newsrooms & Portals
        if matches_source("official") and len(results) < limit:
            remaining = limit - len(results)
            official_items = await scrape_official_brand_portals(page, query, limit=remaining)
            add_items(official_items)

        # 12. GSMArena Studio Pictures
        if matches_source("gsmarena") and len(results) < limit:
            remaining = limit - len(results)
            gsm_items = await scrape_gsmarena_full_radius(page, query, limit=remaining)
            add_items(gsm_items)

        # Ensure priority ranking
        def source_priority_score(item):
            s = (item.get("source") or "").lower()
            if "flipkart" in s:
                return 0
            if "amazon" in s:
                return 1
            if "cashify" in s:
                return 2
            if "fonezone" in s:
                return 3
            if "gameloot" in s:
                return 4
            if "triveni" in s:
                return 5
            if "vlebazaar" in s:
                return 6
            if "ebay" in s:
                return 7
            if "alamy" in s:
                return 8
            if "indiamart" in s:
                return 9
            if "official" in s:
                return 10
            if "gsmarena" in s:
                return 11
            return 12

        results.sort(key=source_priority_score)

        # Re-index filenames with priority order
        for idx, item in enumerate(results, start=1):
            meta = extract_detailed_naming(
                title=item["title"],
                query=query,
                index=idx,
                angle_hint=item.get("angle", ""),
                source_hint=item.get("source", "")
            )
            item["filename"] = meta["filename"]

        await browser.close()
        return results[:limit]


if __name__ == "__main__":
    async def main():
        for q in ["Infinix Note 40 Pro", "Nothing Phone (2a)"]:
            print(f"\n================ Testing Scraper for '{q}' ================")
            res = await scrape_phones(q, limit=8, source="all")
            print(f"Scraped {len(res)} results:")
            for r in res[:4]:
                print(f"- [{r['source']}] {r['storage']} | {r['color']} | {r['filename']}")

    asyncio.run(main())
