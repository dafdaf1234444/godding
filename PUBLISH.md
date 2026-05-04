# publishing godding — copy-paste workflow

**Every option below has a free tier. None of them require a credit card.**
Pick one, run the commands, the site is live in under five minutes.

> I (Claude) can't push to your GitHub on your behalf — that's a privacy
> boundary. Run the commands yourself; everything in this folder is ready.

---

## 0 · sanity check locally first

```powershell
cd "C:\Users\canac\OneDrive\Desktop\godding"
python serve.py
```

Opens `http://127.0.0.1:8000/` in your browser with no-cache headers.
The home's status block should show real metrics (not "checking…"). If
that's good, you're ready to publish.

---

## 1 · GitHub Pages — exact commands (free, recommended)

The commands below are corrected for the issues you hit:

```powershell
cd "C:\Users\canac\OneDrive\Desktop\godding"

# 1) Clean up the broken folder + any partial .git from earlier attempts
Remove-Item -Recurse -Force .\._git_broken_mount_owns_it -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\.git -ErrorAction SilentlyContinue

# 2) Tell git who you are (one-time per machine)
git config --global user.name  "Can Acay"
git config --global user.email "you@example.com"   # use your real email

# 3) Init + first commit
git init -b main
git add .
git commit -m "godding: initial publish"

# 4) Create the EMPTY repo in your browser at:
#       https://github.com/new
#    Owner: dafdaf1234444 · Name: godding · Public · NO README/.gitignore
#    Then push:
git remote add origin https://github.com/dafdaf1234444/godding.git
git branch -M main
git push -u origin main
```

**Then in the GitHub repo's Settings → Pages:**

- **Source:** Deploy from a branch
- **Branch:** `main` · `/ (root)` · click Save

About 30–60 seconds later your site is live at:

> **https://dafdaf1234444.github.io/godding/**

(Already linked from the home page sidebar and footer.)

### keep it deploying automatically

Every git push redeploys. The daily scheduled swarm task already runs
`loop.py` and `share.py` and writes new files to `data/` and the page
HTML. To make those land on the live site, end the scheduled task with:

```powershell
cd "C:\Users\canac\OneDrive\Desktop\godding"
git add data/ pages/ changelog/
git commit -m "swarm: daily run" --quiet
git push --quiet
```

(I can update the scheduled task prompt to do this for you — say the word.)

---

## 2 · Cloudflare Pages (free, fastest CDN, no git required)

```powershell
npm i -g wrangler
wrangler login
cd "C:\Users\canac\OneDrive\Desktop\godding"
wrangler pages deploy . --project-name godding --branch main
```

Live at `https://godding.pages.dev/` immediately.

---

## 3 · Netlify drag-and-drop (free, zero CLI)

Open <https://app.netlify.com/drop>, drag the `godding` folder onto the page.
Done. Get a `*.netlify.app` URL.

---

## 4 · Vercel (free, one CLI command)

```powershell
npm i -g vercel
vercel login
cd "C:\Users\canac\OneDrive\Desktop\godding"
vercel --prod
```

---

## 5 · surge.sh (free, simplest CLI)

```powershell
npm i -g surge
cd "C:\Users\canac\OneDrive\Desktop\godding"
surge .
```

---

## what's in this folder

```
godding/
├── index.html              # landing
├── PUBLISH.md              # this file
├── serve.py                # local-only dev server (NOT deployed)
├── .gitignore
├── assets/
│   ├── styles.css          # one CSS file, no preprocessor
│   └── bubbles.js          # shared bubble-chart module
├── pages/                  # 14 essay/sim/visualisation pages
├── changelog/              # auto-rendered swarm log
├── data/                   # swarm output: changelog, metrics, share_kit
└── swarm/
    ├── loop.py             # multi-agent paragraph-tightening loop
    ├── share.py            # daily marketing share-kit generator
    ├── scheduler.json
    ├── verify_links.py     # checks every internal href resolves
    └── README.md
```

Last verified: **425 internal links across 16 HTML files, all OK.**

---

## after the first deploy

1. Visit the live URL. Confirm the home, sims, and bubble charts work.
2. Share it. The daily `data/share_kit.json` has the copy ready (X / LinkedIn / HN). Read [/reach](pages/reach.html) for the full strategy.
3. Watch [/changelog](changelog/index.html) — every accepted swarm edit shows up there with a UTC timestamp.
4. Tomorrow at 09:04 local the swarm runs again. With the auto-commit-and-push hook above, the new diffs deploy themselves.
