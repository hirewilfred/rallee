# DinkIQ — Build Plan

AI pickleball coaching. Phone clip in, measured deviation from a reference corpus out.

---

## Assumptions (challenge any of these)

- Solo founder, evenings and weekends, with budget for contract help
- No outside capital in year one
- Target user: 3.0–4.0 recreational player, 45+, already buys lessons
- Consumer subscription business, standalone entity, no Audcomp connection
- Ontario-first launch, Canadian data residency as a positioning asset
- Reference corpus is filmed and owned, not scraped

---

## Phase 0 — Validation (4 weeks, ~$0)

**Do not build past this phase until all three gates pass.**

| Week | Work | Gate |
|---|---|---|
| 1 | Run 10 of your own clips through the LLM-only POC. Include deliberately bad shots. | Catches the bad ones, stays quiet on the good ones |
| 2 | Blind-review the 10 outputs with a coach. One question: "is this right?" | 7 of 10 defensible |
| 3 | Concierge test — free analysis offer in local pickleball groups. Manual turnaround by email. | 30 clips in, 10 people send a second |
| 4 | Decide | All three pass, or stop |

**Why week 3 matters most:** repeat sends are the only real signal. First clips are curiosity. Second clips are demand.

**Kill criteria:** fewer than 15 clips, or fewer than 4 repeat senders. That's a hobby, not a business.

---

## Phase 1 — Foundation (weeks 5–12)

### 1a. Reference corpus (weeks 5–8)

The asset the company is built on. Get it right or nothing downstream works.

- Recruit 6–8 players at 4.5–5.0 from Hamilton, Burlington, Oakville
- $100 per session, signed likeness and data release
- Fixed rig: tripod, side-on, 1.1m height, 4m from contact point, 60fps minimum
- 20 shots per player per shot type
- **A coach labels every clip** as reference-grade or reject before it enters the corpus

**Target:** 100 clean reference shots for the third shot drop only. One shot type. Resist scope creep.

**Budget:** $800–1,200

### 1b. Pipeline (weeks 7–12, parallel)

```
clip → pose extraction → normalization → feature vector
                                              ↓
                              pgvector nearest-neighbour vs. corpus
                                              ↓
                                   deviation deltas → Claude → coaching
```

**Build order:**
1. Pose extraction — MediaPipe Pose, on-device where possible
2. Normalization — this is the hard part and the real IP:
   - Joint angles: elbow, shoulder, knee, hip at contact
   - Ratios: contact height ÷ hip height, stride ÷ shoulder width
   - Timing: frames from takeback to contact, weight-shift onset
   - Everything scale- and angle-invariant
3. Contact-frame detection — identify the contact frame reliably or every measurement is noise
4. Storage: Supabase, ca-central-1, pgvector index on the feature vector
5. Comparison: nearest-neighbour, output deltas per feature
6. Coaching layer: Claude API turns deltas into ranked faults and a drill

**Gate at week 12:** run the same 10 amateur clips through baseline-grounded and LLM-only. Blind coach review. **Baseline must clearly beat LLM-only.** If it doesn't, the corpus isn't the moat and you rethink the whole thesis.

---

## Phase 2 — Product (weeks 13–24)

### Stack

| Layer | Choice | Why |
|---|---|---|
| Mobile | React Native (Expo) | Camera + on-device inference, one codebase |
| Agent runtime | Vercel eve | Durable workflows survive long video jobs; built-in evals. **Beta — accept the API churn risk** |
| DB / auth / storage | Supabase ca-central-1 | Residency, pgvector, fast |
| Inference | Claude API for coaching language | Pose is commodity, coaching quality is the product |
| Payments | Stripe (App Store IAP for iOS) | Apple takes 15–30%, price for it |

### Build order

1. Capture flow with live framing guide — reject bad clips at capture, not after
2. Upload, processing state, result view
3. Accounts, clip history, progress tracking
4. Subscription and paywall
5. Drill library for the shots you cover
6. Second and third shot types

**Deliberately deferred:** social feed, live game analysis, scorekeeping, court finding, DUPR integration. Every one is a different product.

### Eval suite — non-negotiable

Held-out labelled clips with known faults, run on every deployment. Confident nonsense is the failure mode that kills this product. eve has this built in — use it from day one, not after launch.

---

## Phase 3 — Launch (weeks 25–32)

- TestFlight with the 30 concierge users. They already sent clips; they're your beta.
- Coach partner programme — 5 local coaches use it with students, free, in exchange for feedback and referral
- App Store submission (allow 2–4 weeks for review cycles)
- Pricing at launch: free tier 3 analyses, $14.99/mo CAD unlimited

**Do not launch on all three shot types.** Launch on the third shot drop done extremely well.

---

## Costs

**Pre-revenue**
| Item | Cost |
|---|---|
| Reference filming | $1,000 |
| Incorporation | $1,500 |
| Trademark search + filing | $2,000–3,000 |
| Privacy policy + terms (lawyer) | $1,500 |
| Apple + Google developer | $150/yr |
| Domain | $20 |
| **Subtotal** | **~$6,000–7,000** |

**Running**
- Supabase: $25/mo
- Vercel: $20–100/mo depending on video processing volume
- Claude API: ~$0.02 per analysis

**Unit economics:** at $14.99/mo with 20 analyses per user, inference is ~$0.40. Apple takes ~$4.50. Net ~$10/user/month. Healthy — the constraint is acquisition, not margin.

**Development:** if you build it yourself, add 6 months of evenings. If you contract, budget $40–70K for a competent RN developer through Phase 2.

---

## Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| Phone video quality too poor for reliable pose | **High** | Aggressive capture guidance, auto-reject, framing overlay. Test this in Phase 0. |
| Confident wrong coaching destroys trust | **High** | Eval suite, coach validation, honest "can't read this clip" path |
| Novelty churn — 3 analyses then cancel | **High** | Progress tracking and structured improvement path are the retention mechanic |
| eve beta API changes mid-build | Medium | Keep agent logic thin and portable; don't couple deeply |
| Contact-frame detection unreliable | Medium | Prove it in Phase 1b before building anything on top |
| CV commoditizes, big player enters | Medium | Defensibility is the labelled corpus and coaching quality, not the tech |
| PIPEDA — video of identifiable people | Medium | Delete clips after feature extraction. Store vectors only. Say so publicly. |
| Apple rejects on health/fitness claims | Low | Frame as sports technique, not medical or injury advice |

---

## Decision gates

**Week 4** — Concierge test passed? No → stop, $0 spent.
**Week 12** — Baseline beats LLM-only? No → the corpus isn't a moat, rethink.
**Week 24** — 20 TestFlight users, 50%+ still analysing in week 4? No → retention problem, fix before spending on acquisition.
**Month 9** — 200 paying users? No → reassess whether this deserves more of your time.

---

## Immediate next actions

1. Film 10 of your own third shot drops this week
2. Run them through the POC
3. Book 20 minutes with a coach for week 2
4. Draft the concierge recruitment post

Everything else waits on those four.
