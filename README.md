# phone_img_scraper 📱✨
> Comprehensive Smartphone Multi-Source & All-Color Image Extraction Engine with Detailed Model and Color Filenaming.

---

## 🌟 Highlights

- **Luminous Light Theme UI**: Crisp, modern light-mode design with clean white cards, soft shadows, and color metadata tags.
- **Multi-Source Engine**:
  - **Flipkart Deep Crawler** (All color variants + multi-angle product galleries in `1200x1200` / `834x834` HD)
  - **Amazon India** (Unscaled high-res assets)
  - **Cashify** (Official refurbished catalog & `xxhdpi` studio plates)
  - **Official Brand Portals & Newsrooms** (Apple Newsroom, Samsung Newsroom, Google Press, etc.)
  - **GSMArena Official Studio Gallery**
- **Intelligent Model & Color Filenaming**:
  - Automatically identifies brand, exact model, colorway, and angle.
  - Generates detailed, filesystem-safe filenames:
    - `Apple_iPhone_16_Pro_Desert_Titanium_Back_01.jpg`
    - `Apple_iPhone_16_Pro_Black_Titanium_Angle_01.jpg`
    - `Samsung_Galaxy_S24_Ultra_Titanium_Gray_Camera_02.jpg`
- **1-Click Batch ZIP Export**: Bundles all images into a single `.zip` archive retaining all detailed model and color filenames.
- **Anti-CORS Proxy Download**: Single-click downloads direct to your device without CDN or CORS blocking.
- **Interactive Lightbox**: Fullscreen preview showing color tag, camera angle, and exact target filename.

---

## 🚀 Running the App

```powershell
python app.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## 💻 Python CLI Usage

```python
import asyncio
from scraper import scrape_phones

async def main():
    # sources: 'all', 'flipkart', 'amazon', 'cashify', 'official', 'gsmarena'
    results = await scrape_phones("Samsung Galaxy S24 Ultra", limit=24, source="all")
    for phone in results:
        print(f"[{phone['source']}] Color: {phone['color']}")
        print(f"  Target File: {phone['filename']}")
        print(f"  Image URL:   {phone['url']}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📂 Project Structure

```
phoneimg scraper/
├── app.py              # FastAPI server (search, proxy download, ZIP export)
├── scraper.py          # Multi-source scraper (Official, Flipkart, GSMArena, Amazon)
├── requirements.txt    # Project dependencies
├── render.yaml         # Render Blueprint for automatic backend deployment
├── build.sh            # Render native Linux build script
├── Dockerfile          # Production Playwright container for Render
├── vercel.json         # Vercel static routing & API proxy configuration
├── package.json        # Frontend project definition
├── static/             # Light-theme UI (HTML, CSS, JS)
│   ├── index.html      # UI structure
│   ├── index.css       # Clean light-mode design system & animations
│   └── app.js          # Interactive gallery, modal, and download logic
└── README.md           # Documentation
```

---

## 🌐 Deploying to Production

### 1. Backend on Render (Web Service)
1. Go to **[dashboard.render.com](https://dashboard.render.com/)** and click **New + > Web Service**.
2. Select your connected repository: `konal01/phone-image-scraper`.
3. Choose **Python** (or **Docker**):
   - **Name**: `phoneimg-scraper-api`
   - **Runtime**: `Python`
   - **Build Command**: `./build.sh` (or `pip install -r requirements.txt && playwright install --with-deps chromium`)
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
4. Click **Deploy Web Service**.
5. Once deployed, copy your Render URL: e.g. `https://phoneimg-scraper-api.onrender.com`.

### 2. Frontend on Vercel
1. Import repository `konal01/phone-image-scraper` into Vercel.
2. Vercel automatically detects the static build settings via `vercel.json` and `package.json`.
3. Click **Deploy**.
4. To connect the frontend to your live Render backend:
   - **Option A (UI)**: Click the **Backend: Auto** button in the top navbar on your Vercel site and paste your Render URL.
   - **Option B (Proxy)**: Update `vercel.json` with your Render backend URL so requests to `/api/*` are automatically forwarded.

