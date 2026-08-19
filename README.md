# DinkIQ

AI pickleball coaching. Phone clip in, measured deviation from a reference corpus out.

Full plan: [`docs/build-plan.md`](docs/build-plan.md).

Currently in **Phase 0/1** scaffolding — see the plan before treating any of this as production-ready. The plan's own gate: don't build past Phase 0 until the validation gates pass.

## What's here

- `mobile/` — Expo (React Native) app. Capture flow with a framing overlay matching the reference-corpus filming rig (side-on, ~1.1m height, ~4m back). `App.tsx` wires capture → results; the upload/analysis call is a `TODO` pending the backend endpoint.
- `pipeline/` — Python analysis pipeline: pose extraction (MediaPipe) → normalization (joint angles, ratios, timing) → contact-frame detection → pgvector nearest-neighbour comparison → Claude-generated coaching. Run end-to-end with `python pipeline/main.py <clip> --shot-type third_shot_drop --paddle-side right`.
- `supabase/schema.sql` — Reference corpus + clip-analysis tables, pgvector index, RLS. No raw video storage by design (PIPEDA: vectors only, clips deleted after feature extraction).
- `docs/build-plan.md` — the full build plan.

## Pipeline setup

```bash
cd pipeline
pip install -r requirements.txt
export SUPABASE_DB_URL="postgresql://..."   # ca-central-1
export ANTHROPIC_API_KEY="sk-ant-..."
python main.py path/to/clip.mp4 --shot-type third_shot_drop --paddle-side right
```

The reference corpus (`reference_shots` table) needs to be seeded before comparison returns anything — see Phase 1a in the build plan.

## Mobile setup

```bash
cd mobile
npm install
npm start
```

## Status

Not yet validated per the plan's Phase 0 gates (concierge test, coach review). Treat the pipeline's contact-frame detection and normalization heuristics as unverified until checked against hand-labelled clips — the plan flags both as the highest-risk pieces.
