# MB1125-2 — blocked before publish, 2026-11-26

Title: Creatine Gummies vs Liquid: The US Stability Check
Primary keyword: creatine gummies vs liquid
Template: COMPARISON
Draft: published_drafts/creatine-gummies-vs-liquid-the-us-stability-check.md
Images: tmp_images/creatine-gummies-vs-liquid-the-us-stability-check/{hero,routine-corrected,mixing,storage}.webp

STEP 0: live suggest.json returned zero articles for exact keyword.
STEP 0.5: PASS brand_intent.
Research: WebSearch returned no results. Europe PMC primary abstracts and review full text fetched. Claims log contains 14 checked claims. Catalog title added verbatim following first validator result; title amount is catalog identification, not an independent potency measurement.
Media: four selected images QC PASS; routine-corrected replaces original routine after visual inspection found wrong eye gaze. Curated packaging reference inspected; no fallback product reference. ima2 $0 subscription (standing approval).
Persona: f4049-wh-07; seq 182; hero at-another-person, high-angle-down, 3q-left+chin-down; inline at-lens, profile-left+level. Reservation released because never published; angles returned. Fresh picker reservation required before any future run uses face imagery.
Picker warning verbatim: 1 persona(s) have spent all 15 face angles and are done as heroes: f5059-wh-06 (1 left)

Official GEO lint: zero warnings.
Final draft gate: FAIL exit 1. 1,880 content words. Only hard failures: required internal URL checks; curl with validator browser User-Agent returns 403. Earlier urllib browser-UA checks returned HTTP 200 for every URL. No gate code or threshold changed. QRG unavailable: claude-seo runtime not installed.
Publish: NOT ATTEMPTED. No article ID, ADMIN link, FRONTEND link, published_at, post-publish gate or persona commit exists.
Ticket remains open; tracker unchanged because no article published. No other ticket processed. Current ticket MB1125-2; following ticket MB1125-3.

Resume requires resolving validator HTTP403 access without weakening the gate, rerunning dedup/topic checks and persona assignment, obtaining validator PASS, executing published-today and immediate dedup guards, then publisher --live and both post-publish gates. Existing generated images are not authorization to reuse released angles.

## Resume attempt — 2026-11-26

- Topic fitness rerun: PASS [brand_intent].
- Unmodified validator rerun: exit 1, DO NOT PUBLISH. Required product, both collections, related article and author URL checks failed. QRG unavailable; no scores invented.
- Live exact-keyword suggest.json request with browser User-Agent returned a connection-verification HTML challenge, not article JSON. Duplicate status cannot be established for this attempt.
- Subsequent browser-UA status checks varied: product and both collections HTTP 429; related article and author HTTP 200. These later responses do not override the failed validator or establish a successful duplicate check.
- No new persona pick, generated media, publisher call, live article, tracker row or ticket closure. Existing reservation remains released. Existing 14-claim research log was not reverified in this attempt.
- Run blocked by storefront access checks, not file-count scope. Only MB1125-2 processed; it remains the next open ticket. Gate code and live content unchanged.
