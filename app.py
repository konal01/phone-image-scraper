import os
import sys
import asyncio
import io
import time
import zipfile
import re
from typing import List, Optional

# On Windows, Playwright requires WindowsProactorEventLoopPolicy to launch browser subprocesses
if sys.platform == "win32" and sys.version_info < (3, 14):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
import httpx
from PIL import Image
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from scraper import scrape_phones, ensure_playwright_browsers

app = FastAPI(title="phone_img_scraper", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
)


@app.on_event("startup")
async def on_startup():
    print("[Startup] Pre-warming / ensuring Playwright Chromium browser binary...", flush=True)
    asyncio.create_task(ensure_playwright_browsers())



def convert_to_jpg_bytes(image_data: bytes, quality: int = 95) -> bytes:
    """Converts any image (PNG, WebP, AVIF, CMYK, etc.) into standard, guaranteed JPEG/JPG format."""
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            # Handle animated GIF / WebP (grab first frame)
            try:
                img.seek(0)
            except Exception:
                pass

            # Convert transparency cleanly onto pure white background
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                rgba = img.convert("RGBA")
                background = Image.new("RGB", rgba.size, (255, 255, 255))
                background.paste(rgba, mask=rgba.split()[3])
                rgb_img = background
            elif img.mode != "RGB":
                rgb_img = img.convert("RGB")
            else:
                rgb_img = img

            output = io.BytesIO()
            rgb_img.save(output, format="JPEG", quality=quality, subsampling=0)
            converted = output.getvalue()
            if converted and converted.startswith(b'\xff\xd8'):
                return converted
            return converted
    except Exception as e:
        print(f"Primary Pillow conversion failed: {e}")
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                rgb_img = img.convert("RGB")
                output = io.BytesIO()
                rgb_img.save(output, format="JPEG", quality=quality)
                return output.getvalue()
        except Exception:
            return image_data


class ImageItem(BaseModel):
    title: str
    url: str
    source: Optional[str] = "Web"
    filename: Optional[str] = None
    color: Optional[str] = None
    storage: Optional[str] = None
    angle: Optional[str] = None
    model: Optional[str] = None
    media_type: Optional[str] = "image"
    thumbnail: Optional[str] = None
    watch_url: Optional[str] = None


class DownloadZipRequest(BaseModel):
    query: str
    items: List[ImageItem]


@app.get("/api/scrape")
async def api_scrape(
    q: str = Query(..., description="Phone search term, e.g. 'iPhone 16 Pro'"),
    source: str = Query("all", description="Source: 'all', 'ecommerce', 'ebay', 'alamy', 'indiamart', 'cashify', 'fonezone', 'gameloot', 'triveniworld', 'vlebazaar', 'refurbished', 'official', 'gsmarena'"),
    limit: int = Query(64, ge=1, le=512, description="Max items to retrieve")
):
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    start_time = time.time()
    try:
        results = await scrape_phones(query=query, limit=limit, source=source)
        elapsed = round(time.time() - start_time, 2)
        return {
            "success": True,
            "query": query,
            "source": source,
            "count": len(results),
            "duration": elapsed,
            "results": results,
        }
    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "query": query,
            "source": source,
            "count": 0,
            "duration": elapsed,
            "error": str(e),
            "results": [],
        }


@app.get("/api/proxy-image")
async def api_proxy_image(url: str, filename: Optional[str] = None):
    """Proxy image download: converts to standard high-quality JPG and enforces .jpg extension."""
    clean_url = url.strip()
    if clean_url.startswith("//"):
        clean_url = "https:" + clean_url
    elif not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        clean_url = "https://" + clean_url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://www.google.com/"
    }
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
            resp = await client.get(clean_url, headers=headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f"Failed to fetch image: HTTP {resp.status_code}")

            # Convert to guaranteed .jpg bytes
            jpg_bytes = convert_to_jpg_bytes(resp.content)

            safe_filename = filename or "phone_image.jpg"
            # Force .jpg extension
            safe_filename = re.sub(r'\.[a-zA-Z0-9]+$', '', safe_filename).strip() + ".jpg"
            safe_filename = re.sub(r'[^\w\s\.-]', '_', safe_filename)

            return Response(
                content=jpg_bytes,
                media_type="image/jpeg",
                headers={
                    "Content-Disposition": f'attachment; filename="{safe_filename}"',
                    "Content-Length": str(len(jpg_bytes)),
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Expose-Headers": "Content-Disposition, Content-Length"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/download-zip")
async def api_download_zip(req: DownloadZipRequest):
    """Downloads all given images, converts all to .jpg format, and packages into a ZIP archive with video links manifest."""
    if not req.items:
        raise HTTPException(status_code=400, detail="No items to download.")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://www.google.com/"
    }

    zip_buffer = io.BytesIO()
    video_entries = []
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, item in enumerate(req.items, start=1):
                # Cleanly handle videos without attempting image conversion
                if getattr(item, "media_type", "image") == "video":
                    watch = getattr(item, "watch_url", "") or item.url
                    video_entries.append(f"{idx:02d}. {item.title}\n    Type: Official Video Trailer / Feature Film\n    Watch Online: {watch}\n")
                    continue

                try:
                    u = item.url.strip()
                    if u.startswith("//"):
                        u = "https:" + u
                    resp = await client.get(u, headers=headers)
                    if resp.status_code == 200:
                        jpg_bytes = convert_to_jpg_bytes(resp.content)

                        target_filename = item.filename
                        if not target_filename:
                            clean_model = re.sub(r'[^\w\s-]', '', item.model or req.query).strip()
                            clean_storage = re.sub(r'[^\w\s-]', '', item.storage or '').strip()
                            clean_color = re.sub(r'[^\w\s-]', '', item.color or 'Standard').strip()
                            clean_angle = re.sub(r'[^\w\s-]', '', item.angle or f'Angle_{idx:02d}').strip()

                            parts = [clean_model]
                            if clean_storage and clean_storage != "All":
                                parts.append(clean_storage)
                            parts.append(clean_color)
                            parts.append(clean_angle)
                            parts.append(f"{idx:02d}")
                            target_filename = "_".join(parts) + ".jpg"
                            target_filename = re.sub(r'[\s-]+', '_', target_filename)

                        # Force target_filename to end with .jpg
                        target_filename = re.sub(r'\.[a-zA-Z0-9]+$', '', target_filename) + ".jpg"

                        zip_file.writestr(target_filename, jpg_bytes)
                except Exception:
                    continue

            if video_entries:
                manifest_txt = (
                    f"Official Videos & Trailers for {req.query}\n"
                    f"{'='*50}\n\n"
                    + "\n".join(video_entries)
                )
                zip_file.writestr("Official_Videos_Watch_List.txt", manifest_txt)

    zip_bytes = zip_buffer.getvalue()
    safe_query = re.sub(r'[^a-zA-Z0-9_\-]', '_', req.query) or "phones"
    zip_filename = f"phone_img_scraper_{safe_query}_all_jpg_images.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"',
            "Content-Length": str(len(zip_bytes)),
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Disposition, Content-Length"
        }
    )


@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "phone_img_scraper", "version": "3.0.0"}


# Serve UI static files
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"status": "ok", "service": "phone_img_scraper", "message": "API is running"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Starting phone_img_scraper on http://{host}:{port} ...")
    loop_target = "asyncio.windows_events:ProactorEventLoop" if sys.platform == "win32" else "auto"
    uvicorn.run("app:app", host=host, port=port, reload=True, loop=loop_target)

