# Forum Scraper Setup Guide

## ✅ What's Working

Your **m3post.com forum scraper** is now live and finding deals! 

### Current Status
- **Forum:** M3Post (vBulletin)
- **Section:** E9x M3 Parts/Sales (f=182)
- **Keywords:** M3, E90, E92, E93, exhaust, wheel, suspension, etc.
- **Update Frequency:** Every 30 minutes (configurable)
- **Results:** 8 found on first test run

## 🚀 How to Run

### 1. **One-time Search**
```bash
python main.py search
```
Shows all available parts across eBay + forums

### 2. **Continuous Daemon (Background)**
```bash
python main.py daemon
```
Runs forever, searching every 30 minutes, sending SMS alerts (if configured)

### 3. **Web Dashboard**
In another terminal:
```bash
python main.py web
```
Visit http://127.0.0.1:5000 to browse all found parts

## 📋 Customize Keywords

Edit `src/config.yaml`:
```yaml
parts:
  - M3           # Finds "M3 e9x lci adaptive headlight"
  - E90          # Finds "E90 M3 Silverstone ZCP"
  - exhaust      # Finds "E90 Full ACM Modded Exhaust"
  - wheel        # Finds wheel posts
  - FS:          # "For Sale:" prefix posts
```

**Tip:** Use shorter keywords (1-2 words) for better forum matches. Forum posts are inconsistent in naming.

## 🔧 Next Steps

### Option A: Wait for eBay API Approval
Once you're approved, replace the web scraper with official API (faster, more reliable)

### Option B: Expand to Other Forums (Optional)
The scraper already supports:
- e90post.com
- m3cutters.com
- bimmerpost.com

These use generic forum parsing and may need CSS selector updates.

### Option C: Add SMS Alerts
Set environment variables:
```bash
export TWILIO_ACCOUNT_SID="your_account_id"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_FROM_PHONE="+1234567890"
export ALERT_PHONE="+your_phone"
```

Then enable in config.yaml:
```yaml
notifications:
  sms_enabled: true  # Gets SMS when new part found
```

## 📊 Monitoring

**Check what's in the database:**
```bash
python -c "
from src.db import get_items, get_category_stats
items = get_items(limit=5)
print(f'Total items: {len(items)}')
stats = get_category_stats()
for cat, count in sorted(stats.items(), key=lambda x: -x[1]):
    print(f'  {cat}: {count}')
"
```

## ⚠️ Current Limitations

1. **Limited Forum Inventory:** m3post's f=182 has ~10-20 threads at any time
   - New listings appear when users post them
   - Scraper will find them automatically
   
2. **eBay Scraper Issue:** Currently failing due to keyword encoding
   - Will fix next (or use official API)
   
3. **Rate Limiting:** Respects forum servers
   - 0.5s delay between forums
   - User-Agent rotated for resilience

## 📈 How Results Flow

```
Forum Scraper (m3post, e90post, etc)  →  Cache/Dedupe  →  Database  →  Web Dashboard
     ↓ finds new listings                              ↓ stores parts
                                                       ↓ prevents duplicates
                                                       ↓ SMS alerts (optional)
```

## ❓ Debugging

**See all forum posts matching keyword:**
```bash
python -c "
from src.sources.forum import search_forums
results = search_forums('M3', max_results=20)
for item in results:
    print(f'{item[\"source\"]}: {item[\"title\"]}')
"
```

**Check if forum is reachable:**
```bash
curl -I https://www.m3post.com/forums/forumdisplay.php?f=182
# Should return HTTP 200
```

## 🎯 Performance Tips

- **Reduce search interval** for more frequent updates:
  ```yaml
  search_interval: 600  # 10 minutes instead of 30
  ```
  ⚠️ Don't go below 300s or forums may block you

- **Focus keywords** - Use 1-2 word terms for best results

- **Monitor database size**:
  ```bash
  ls -lh src/parts.db
  ```

Good luck! Come back once the eBay API is approved. 🏁
