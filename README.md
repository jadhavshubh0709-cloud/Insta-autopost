# insta-autopost: daily reels for @smartwork.ai.in

Posts one reel every day at about 7 PM IST using the **Instagram API with Instagram Login** (no Facebook Page needed).
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
.github/workflows/refresh-token.yml# keeps the 60-day token alive
```

## One-time setup

### 1. Meta developer app
1. Go to developers.facebook.com, open My Apps and create an app. Choose the use case for managing messaging and content on Instagram.
2. In the app, open **Instagram → API setup with Instagram business login**.
3. Under *Generate access tokens*, add **@smartwork.ai.in** and log in with Instagram. This gives you a **long-lived token** (valid for 60 days) with `instagram_business_basic` and `instagram_business_content_publish`.
   - You're posting only to your own account, so the app can stay in **Development mode**, as long as your account has a role on the app. No App Review is needed.
4. Get your Instagram user ID:
   `curl "https://graph.instagram.com/v25.0/me?fields=user_id,username&access_token=YOUR_TOKEN"`

Meta renames dashboard menus from time to time. If a label doesn't match, look for "Instagram API with Instagram Login".

### 2. GitHub repo
1. Create a **public** repo called `insta-autopost` and push this folder to it. Free GitHub Pages needs a public repo.
2. Go to **Settings → Pages**: Source = *Deploy from a branch*, Branch = `main`, folder `/ (root)`.
   Your videos will then be at `https://<github-user>.github.io/insta-autopost/reels/<date>/reel.mp4`.
3. Under **Settings → Secrets and variables → Actions**, add:
   - Secret `IG_ACCESS_TOKEN`: the token from step 1
   - Secret `IG_USER_ID`: the `user_id` from step 1
   - Secret `GH_PAT`: a fine-grained GitHub token for this repo with *Secrets: Read and write* (used by the token refresher)
   - **Variable** `PAGES_BASE_URL`: `https://<github-user>.github.io/insta-autopost`
4. Test it: go to **Actions → Post daily reel → Run workflow**, enter `2026-11-26`, and check that the reel appears on Instagram.

## Weekly routine (about 2 minutes)
1. Get the week's reels from Claude, already in `reels/YYYY-MM-DD/` folders.
2. Copy them into `reels/`, then commit and push. Push **before 6 PM IST** so Pages has time to deploy.
3. That's it. Each day's workflow posts the folder that matches that day's date and skips days with no folder.

## Notes
- Reels posted through the API can't have Instagram's in-app trending music. The audio baked into the mp4 is what gets posted.
- The Content Publishing API currently allows up to 100 posts in 24 hours, far more than one a day.
- If a post fails, open the failed run under **Actions** to see the API error. Common causes are an expired token or the Pages URL not being deployed yet.
- Keep your token only in GitHub Secrets. Never commit it or paste it in chat.
