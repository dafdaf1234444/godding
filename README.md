# godding

> a small, opinionated site about the things humans broadly agree on but rarely act on — paired with a swarm of language models that reads every page, kills weak claims, keeps the strong ones, and logs every change in public.

**live:** <https://dafdaf1234444.github.io/godding/>
**author:** [Can Acay](https://github.com/dafdaf1234444), Utrecht NL
**license:** content CC BY-SA 4.0 · code MIT

---

## what this is, in one paragraph

godding is a static site (no backend, no framework) about the small set of moral and physical claims that nearly every culture has converged on: what counts as cruelty, what makes life cooperate, what the universe seems to be doing. The site is paired with a multi-agent LLM "swarm" that runs daily, reads each page, proposes tightening edits, and only commits the ones that survive a critic + fact-checker + judge. **Every accepted edit is logged in public** with a UTC timestamp.

The deeper bet: the universe is a *knowledge farm*. It compresses information about itself into compact models (atoms, cells, brains, languages, this site). Cooperation is the most energy-efficient way to keep that compression going. Defection is local and short-lived. godding tries to be a small node in that farm.

## the knowledge-farm idea, plainly

1. The cheapest way to predict the world is a compact model of it.
2. Living things are compact models that can run themselves.
3. Self-aware models that **cooperate** are even more compact than ones that don't, because they can share each other's predictions instead of redoing the work.
4. Knowledge that doesn't reduce future surprise is a thermodynamic loss — wasted energy.
5. New true ideas are bets with a capped downside and an open-ended upside — finding one is a few hours of attention, keeping the right one pays back across a lifetime. So you build a system whose default move is to take small falsifiable bets, log them, and keep the ones that work.

That last sentence is the swarm.

## file map

```
godding/
├── index.html              # landing — branches grid + status ribbon + sidebar
├── README.md               # you are here
├── PUBLISH.md              # 5 free hosting options w/ exact commands
├── serve.py                # local-only dev server with no-cache headers
├── .gitignore
├── assets/
│   ├── styles.css          # parchment palette, single CSS file
│   └── bubbles.js          # shared bubble-chart module (mass-weighted physics)
├── pages/                  # 14 essay / sim / visualisation pages
│   ├── belief.html         # root cosmology — vote on four questions
│   ├── religion.html       # heaven/hell in plain language
│   ├── good-bad.html       # spatial prisoner's-dilemma simulation
│   ├── ants.html           # live n-body + ant-colony foraging
│   ├── crime.html          # cross-cultural list of universal wrongs
│   ├── criminals.html      # historical mass-atrocity bubble chart
│   ├── politics.html       # public mouth vs. private mind
│   ├── now.html            # contestable current claims, no named living people
│   ├── vote.html           # reputation & activity history
│   ├── reach.html          # marketing strategy + about
│   ├── health.html         # doctors' consensus list
│   ├── sustainability.html # load-bearing vs. theatre
│   ├── swarm.html          # how the engine works
│   └── build.html          # how the site is built
├── changelog/
│   └── index.html          # rendered swarm log (auto-updated)
├── data/
│   ├── changelog.json      # every accepted swarm edit
│   ├── metrics.json        # cumulative run / accept / reject counts
│   ├── last_run.json       # most recent run's summary (gitignored)
│   └── share_kit.json      # daily marketing copy (X / LinkedIn / HN / blog)
└── swarm/
    ├── loop.py             # multi-agent paragraph-tightening loop
    ├── share.py            # daily marketing share-kit generator
    ├── verify_links.py     # validates every internal href
    ├── scheduler.json      # daily cron descriptor
    └── README.md
```

## the swarm

```
drafter → critic → fact-checker → judge
```

* **drafter** — proposes a tightened paragraph (heuristic by default; optional Claude Haiku via `ANTHROPIC_API_KEY`)
* **critic** — rejects on size growth, >20% change, new proper nouns, long quotes
* **fact-checker** — rejects new numeric claims that aren't derivable from the original
* **judge** — errs toward "no". Accepts only if all three say yes.

Every run writes to `data/changelog.json`, `data/metrics.json`, and renders `changelog/index.html`. The site is the public log.

```powershell
cd swarm
python loop.py             # one full pass
python share.py            # generate today's share-kit
python verify_links.py     # confirm every href resolves
```

Last verified: **425 internal links across 16 HTML files, all OK.**

## running locally

```powershell
cd "C:\Users\canac\OneDrive\Desktop\godding"
python serve.py
```

Opens `http://127.0.0.1:8000/` with no-cache headers so swarm edits show up immediately.

## publishing

See [PUBLISH.md](PUBLISH.md) for five free options. The recommended path is GitHub Pages — already wired up for `dafdaf1234444.github.io/godding/`.

## marketing

See [`pages/reach.html`](pages/reach.html). Boundary: the swarm writes daily share-kit copy to `data/share_kit.json`; **the user copies and presses send**. Nothing is auto-posted.

## what godding will not do

* name living people on votable pages (defamation risk; see [`pages/now.html`](pages/now.html))
* buy clicks
* auto-DM, auto-follow, or any growth-hack that would be embarrassing if quoted back
* reproduce copyrighted content (links + short citations only)

## contributing

Open an issue. The swarm reads them on its next run.

— Can
