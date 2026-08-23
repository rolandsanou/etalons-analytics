# LinkedIn post — ready to paste

Attach in this order: `linkedin-tour.mp4` (or the five stills if you prefer a
carousel). LinkedIn shows video and images separately, so pick one — video gets
more reach, a carousel gets more dwell time.

Every number below is on the site and traceable to a source. Nothing is rounded
in our favour.

---

## Option A — the build story (recommended)

> I spent a few weeks building an open data project about the Étalons, the
> Burkina Faso national football team. It is live, and everything about it is
> public: the code, the data, and the limits of every number.
>
> 129 players. 58 matches since January 2022. Every appearance, minute, goal,
> pass and save, per player, per match.
>
> The finding that stopped me was not a good one. Once this team goes two goals
> down, it has never come back: 0 wins, 1 draw, 13 losses — 0.07 points per
> match. Never trailing, it takes 2.43. Trailing by one, 1.00. The collapse is
> not gradual, it is a cliff.
>
> Some things I decided early and did not compromise on:
>
> → Every rate shows its numerator and denominator. "67%" without "8 of 12" is
> not a statistic, it is a claim.
> → Small samples are gated, not hidden. A greyed row with a dash tells you the
> truth; a confident-looking number does not.
> → No composite index. I could have built an "Étalon Score" out of six
> weighted metrics and it would have looked impressive and meant nothing. You
> cannot argue with a made-up score.
> → Descriptive, never causal. Short rest looks like the best rest — until you
> notice those matches were against the weakest opponents. The site says so, next
> to the number.
>
> It is bilingual FR/EN, works without JavaScript, and is a static site: no
> database, no framework, no build step. Python and vanilla JS, so anyone can
> clone it and run one command.
>
> The biggest gap is not technical. I have 58 matches of detail and only a handful
> of squad announcements, so "called up but did not play" is largely invisible. If
> you have access to Burkinabè federation call-up lists, that single contribution
> would improve this more than anything I could code.
>
> Site: rolandsanou.github.io/etalons-analytics
> Code: github.com/rolandsanou/etalons-analytics
>
> #DataAnalysis #Python #Football #BurkinaFaso #OpenData #DataViz

---

## Option B — shorter, finding-first

> Burkina Faso, 58 matches since 2022:
>
> Never trailed → 2.43 points per match (25W-10D-0L)
> Trailing by one → 1.00 (4W-8D-8L)
> Trailing by two or more → 0.07 (0W-1D-13L)
>
> One draw. Thirteen defeats. No wins.
>
> I built an open data project to find things like this — 129 players, every
> minute and every goal since AFCON 2021, with the source and the sample size
> next to every figure. Bilingual, static, no framework, MIT licensed.
>
> The rule I held to throughout: show the denominator, gate the small samples,
> and never invent a composite score. If a number cannot be argued with, it is
> not doing its job.
>
> rolandsanou.github.io/etalons-analytics
>
> #DataAnalysis #Python #OpenData #Football #BurkinaFaso

---

## If you post the stills as a carousel

Suggested captions, in order:

1. `linkedin-01-home.png` — "129 players, 58 matches, every number sourced."
2. `linkedin-02-style.png` — "Style measured against the opponents actually
   faced — which neutralises the level of opposition."
3. `linkedin-03-resilience.png` — "Two goals down: 0W-1D-13L. The deficit ladder
   is the hardest chart on the site."
4. `linkedin-04-match.png` — "Every match: timeline, team stats, full lineup with
   minutes and ratings."
5. `linkedin-05-management.png` — "Rotation, on-pitch partnerships, substitution
   patterns — each with its sample size."

## Notes before you post

- The video is 22 s, 1280×720, H.264 — within LinkedIn's limits, no re-encode
  needed.
- Post from a desktop browser if you want the link preview to use the social card
  (`og-en.png`); the mobile app sometimes drops it.
- Best window for this audience is a weekday morning, Africa/Ouagadougou.
- The video and stills are dark-theme captures. The site follows the reader's own
  system setting, so a visitor on light mode sees the light version — worth
  knowing if someone asks why it looks different.
