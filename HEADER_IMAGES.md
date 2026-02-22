# Adding Header Images to Your M3 Parts Finder

Your website now supports custom header images and logos! Here's how to customize them.

## 🎨 Three Ways to Add Images

### Option 1: Environment Variables (Recommended for Deployment)

Set these before running your web server:

```bash
# Full header background image
export HEADER_IMAGE_URL="https://example.com/my-header.jpg"

# Optional: Logo to display in header
export HEADER_LOGO_URL="https://example.com/my-logo.png"

# Then start server
python main.py web --port 5001
```

### Option 2: Local Files (Development)

Place images in `src/static/` folder and reference them:

```bash
# Copy your image
cp ~/Downloads/m3-header.jpg src/static/header-bg.jpg

# Set environment variable
export HEADER_IMAGE_URL="/static/header-bg.jpg"

python main.py web --port 5001
```

### Option 3: Edit Default in Code

Edit [src/web.py](src/web.py) and change:

```python
HEADER_IMAGE_URL = os.getenv('HEADER_IMAGE_URL', '/static/header-bg.svg')
HEADER_LOGO_URL = os.getenv('HEADER_LOGO_URL', None)
```

To:

```python
HEADER_IMAGE_URL = '/static/my-header.jpg'
HEADER_LOGO_URL = '/static/my-logo.png'
```

## 📐 Image Recommendations

**Header Background Image:**
- **Dimensions:** 1920×500px (widescreen) or 1600×400px
- **File Size:** < 500KB (optimize for web)
- **Format:** JPG (faster), PNG (sharper), or SVG (scalable)
- **Content Ideas:**
  - BMW M3 hero shot
  - Track/racecar photos
  - M-crest or M-stripe graphics
  - Automotive textures (gauges, speedometer, parts close-ups)

**Logo Image:**
- **Dimensions:** 80×80px or smaller
- **File Size:** < 50KB
- **Format:** PNG with transparency, or SVG
- **Content Ideas:**
  - M-logo
  - Custom badge
  - Your initials or racing number

## 🖼️ Current Setup

**Default header:** Uses built-in SVG pattern (no external images needed)
- Dark gradient background with speedometer design
- Responsive on mobile
- Red accent color matching BMW M theme

**To keep the default:** Do nothing! It works out of the box.

## 🎯 Example: Add Your Own Header

### Step 1: Download/Create Image
```bash
# Example: use a motorsports image
curl -o src/static/m3-header.jpg \
  "https://images.unsplash.com/photo-1589...jpg"
```

### Step 2: Start Server with Custom Header
```bash
export HEADER_IMAGE_URL="/static/m3-header.jpg"
python main.py web --port 5001
```

### Step 3: View in Browser
Visit `http://127.0.0.1:5001` - header now shows your image!

## 🔧 Troubleshooting

**Header image not showing?**
- Check file exists: `ls -la src/static/header-bg.jpg`
- Check URL is correct (starts with `/` for local files)
- Check file is readable: `chmod 644 src/static/header-bg.jpg`
- Check browser cache: Hard refresh (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)

**Image looks distorted?**
- Image aspect ratio might be wrong
- Try 16:9 or 21:9 ratio for best fit
- Adjust padding in CSS if needed (line ~50 in base.html)

**Performance issues?**
- Compress images: Use `ImageOptim` (Mac) or `TinyJPG` (online)
- Keep under 300KB for fast loads
- Use SVG for vectors or logos

## 📚 Resources for Images

**Free Stock Photos:**
- [Unsplash](https://unsplash.com) - Search "BMW" or "racing"
- [Pexels](https://pexels.com) - High quality free photos
- [Pixabay](https://pixabay.com) - Motors and vehicles

**Image Tools:**
- [ImageOptim](https://imageoptim.com) - Compress JPG/PNG
- [Figma](https://figma.com) - Design logos (free)
- [Inkscape](https://inkscape.org) - Create SVG graphics (free)

## 🎨 Design Tips

To match the **premium automotive look:**
- Use dark/moody colors (dark grays, blacks, deep blues)
- Add red accents (#dc3545 = BMW M red)
- Include racing/motorsports themes
- Keep text overlay contrast high (dark background recommended)
- Use sharp, professional photography

Example color scheme:
```css
Dark background: #0f1419  /* Current dark-bg */
Primary red: #dc3545      /* Current primary */
Accent: #ffc107           /* Golden/yellow highlights */
Text: #ffffff             /* White for contrast */
```

## 📱 Responsive Design

Headers automatically scale on mobile:
- Desktop (1024px+): Full size with parallax effect
- Tablet (768px): Slightly reduced padding
- Mobile (< 768px): Optimized for small screens

Your header will always look good! 🏁

---

**Questions?** Check current settings:
```bash
echo "Header image: $HEADER_IMAGE_URL"
echo "Header logo: $HEADER_LOGO_URL"
```
