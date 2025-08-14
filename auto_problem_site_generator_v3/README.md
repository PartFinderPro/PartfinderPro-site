
# Auto Problem → Affiliate Page Generator (v3, Money-Optimized)

What changed in v3
1. Bitly link shortening built in. If `BITLY_TOKEN` is set in GitHub Actions secrets, all affiliate links and share URLs are shortened at build time.
2. Per-page Forum Post Generator. Each page has a ready-to-post snippet with a Copy button and channel tags (reddit, quora, fb, yt). UTM parameters are included.
3. Big prefilled CSV. Hundreds of Year Make Model Problem combos across popular cars.
4. OG images per page. Social cards are generated (Pillow). Fallback if Pillow unavailable.
5. Make and Problem indexes. Users can browse by brand or by symptom, increasing internal linking.
6. robots.txt, sitemap.xml and RSS feed. Better discovery and crawling.
7. Optional analytics. Add Google Tag or Cloudflare Web Analytics IDs in `config.yml`.
8. Weekly Google Sheets refresh is preserved.

Quick start
1. Edit `config.yml` with your brand and affiliate IDs. If you have your public site URL, set `public_base_url` so forum snippets use absolute links.
2. Optional: Add a Google Sheet CSV and set `SHEET_CSV_URL` in GitHub → Settings → Secrets and variables → Actions → Variables.
3. Optional: Add `BITLY_TOKEN` to GitHub → Settings → Secrets and variables → Actions → Secrets to enable shortening.
4. Run locally: `python generator.py` and open `site/index.html`.
5. Deploy on GitHub Pages. Use the included workflow. Push to `main` and it deploys. Weekly auto-rebuild is scheduled.

Money tips
1. Use the forum snippet generator to respond in hot threads with the exact matching page.
2. Watch link clicks in Bitly and shift focus to top earners. Duplicate winning patterns across more years/models.
3. Turn on analytics in config for visibility.
