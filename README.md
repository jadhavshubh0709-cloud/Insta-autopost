# insta-autopost: daily reels for @smartwork.ai.in

Posts one reel every day at about 7 PM IST using the Instagram Graph API (no Facebook Page needed).
GitHub Actions runs the Java poster on a schedule, and GitHub Pages hosts the mp4 files on a public HTTPS URL, which Instagram needs in order to download the video.

```
reels/
  2026-11-26/
    reel.mp4
    caption.txt
  2026-11-27/
    ...
src/PostReel.java                  # create container -> wait until FINISHED -> publish
.github/workflows/post-reel.yml    # daily cron, 13:30 UTC = 7 PM IST
```

## One-time setup

Meta now gives new apps "Unified login", so this project uses a **System User token that never expires** (no refresh needed).

Already done:
- Meta app **SmartWork Autopost**, business portfolio **SmartWork AI** (id 1167254632519883)
- @smartwork.ai.in added to the portfolio, system user `autopost-bot` with `instagram_basic` and `instagram_content_publish`

Still to do:
1. **GitHub Pages**: Settings → Pages → Deploy from branch `main`, folder `/ (root)`.
2. **Secret**: Settings → Secrets and variables → Actions → New repository secret → name `IG_ACCESS_TOKEN`, value = the system-user token.
3. **Test**: Actions → *Post daily reel* → Run workflow → date `2026-11-26`.

The Instagram account id is looked up automatically. If the lookup fails, the log says so; then add the id as secret `IG_USER_ID`.

## Weekly routine (about 2 minutes)
1. Get the week's reels from Claude, already in `reels/YYYY-MM-DD/` folders.
2. Copy them into `reels/`, then commit and push. Push **before 6 PM IST** so Pages has time to deploy.
3. That's it. Each day's workflow posts the folder that matches that day's date and skips days with no folder.

## Notes
- Reels posted through the API can't have Instagram's in-app trending music. The audio baked into the mp4 is what gets posted.
- The Content Publishing API currently allows up to 100 posts in 24 hours, far more than one a day.
- If a post fails, open the failed run under **Actions** to see the API error. A common cause is the Pages URL not being deployed yet.
- Keep your token only in GitHub Secrets. Never commit it or paste it in chat.
