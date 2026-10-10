# montage: Bushra's School ad videos

Vertical Instagram Reels (1080x1920, 60fps, 32.5 s, Arabic RTL) for **مدرسة بشرى / Bushra's School**, a tutoring school in Khenchela, Algeria.
Each video is an HTML page animated frame by frame, rendered with Playwright, and scored by a numpy synth.

## Build

```bash
cd bushra-ad
python3 build.py setup              # once: npm install (Markazi Text font + playwright) in work/
python3 build.py prep               # once: logo/grain/footage/teacher assets -> work/assets/
python3 build.py stills teachers 9 14.2 22.5   # look at frames before a full render
python3 build.py all language       # -> bushra-ad/bushra-ad.mp4
python3 build.py all teachers       # -> bushra-ad/teachers/bushra-teachers.mp4
python3 build.py all school         # -> bushra-ad/school/bushra-school.mp4 (whole-school film)
```

- `render` caches 2-second chunks in `work/out/seg*`. After editing a page, pass `--fresh`, or delete only the chunks covering the times you changed (chunk N = seconds 2N to 2N+2).
- A full render takes about 4 minutes on 4 cores. Run it in the background.
- The build is deterministic: rerunning it reproduces the same bytes.
- Needs python3 with numpy and Pillow, node 18+, ffmpeg, and Chromium. In Claude cloud, Chromium is preinstalled; never run `playwright install`.

## Layout

| Path | What |
|---|---|
| `bushra-ad/build.py` | Single entry point: prep, music, render, mux |
| `bushra-ad/work/ad.html` | Language-levels ad ("تعلّم اللغة بالمستويات", 6000 DA for 3 months) |
| `bushra-ad/work/teachers.html` | Teachers ad ("وراء كل نجاح… أستاذ") |
| `bushra-ad/work/school.html` | Whole-school film ("كل ما تحتاجه في مكان واحد"), built from the website's copy |
| `bushra-ad/work/render.mjs` | Playwright renderer (stills or chunked video); the page is chosen by `AD_HTML` |
| `bushra-ad/work/pops.mjs` | Prints the teacher-card pop times so the music lands on them |
| `bushra-ad/work/music.py`, `music_teachers.py`, `music_school.py` | Soundtrack synths (96 BPM; D, F and G major) |
| `bushra-ad/work/src/` | Original media from the client: walkthrough clips, teacher photos, logo |
| `bushra-ad/brand-notes.md` | Brand facts, palette and verbatim site copy. Read this before writing any copy |
| `bushra-ad/PROMPT.md` | Creative brief for the language ad |
| `bushra-ad/VOICEOVER.md`, `teachers/VOICEOVER.md` | Voice-over scripts with timings |

## How the pages work (keep these rules)

- `seek(t)` computes every style from time alone. No CSS transitions, timers or state carried between frames.
- One camera transform on `#world`, keyed by `[t, zoom, x, y]` with log-space zoom.
  - It only pushes in or pans, and never reverses direction.
  - It resets only while the gold flood covers the whole frame.
- Pops use the closed-form `spring()`. Text rises from `overflow:hidden` masks.
- Every handoff is a shared element. No crossfades, blur, 3D or particles.
- Subtitles live in screen space at y≈1600 (outside Instagram's caption area), in `SUBS` inside each page.
  - The voice windows are `LINES` in `build.py`. Keep the two in sync.
- Hide elements with `display:none` (the `vis()` helper), not `visibility`. A visible child shows through a hidden parent.
- Absolutely positioned elements need explicit `left`/`top`, because the page is `dir=rtl`.
- Don't add live SVG filters (such as feTurbulence): they make each frame take seconds. Use a static image.

## Sound rules

- Every effect is in key and goes through the same reverb as the music. Effects sit under the music.
- No typing or keyboard sounds: the client found them annoying.
- Master at -14 LUFS, true peak -1.5 dBTP. The voice bed is -20 LUFS, dipped 6 dB under each line.

## Content rules from the client

- Font: Markazi Text for everything.
- Palette: cream #FBF6EA, indigo #2B1666, gold #F5B82E.
- Contacts: WhatsApp 0669 65 45 15 · Facebook Bushra's School · Khenchela.
  - Instagram: the website links `instagram.com/bushraschool40`, but the client typed @bushrasschool40.
    The school film uses the website's spelling; the language and teachers ads still use the client's. Confirm with the client and align all three.
- Website source: GitHub `achrafness/Bushra-s-School` (Next.js). Copy is in `lib/i18n.ts`, contacts in `lib/contact.ts`, colours in `app/globals.css`, images in `public/assets/`. Take copy from there.
- Language course: 6000 DA for 3 months, "تعلّم اللغة بالمستويات" (learn the language by levels).
  - The A1–B2 steps are an assumption still to confirm with the client.
- **The teacher photos must never appear in the language ad.** Those teachers do not teach the language-level course.
- The teacher cards carry no names or subjects until the client supplies them, in photo order:
  Arabic-board teacher, grey blazer, maths teacher (Fahd, shown on his own poster), glasses, white polo, lab coat, hat.
- **Classes are in person only, never online.** The website's "دروس بمرونة: حضوريًا أو عبر الإنترنت" card is wrong; never show or say "online" / "عبر الإنترنت".
- Use only claims from the client or their website. Never invent numbers, testimonials or "limited places".
- Keep children and watermarks out of crops.
- The client records the voice-over themselves. Mix it over `bed_for_voice.wav` and re-time `SUBS` to the recording.
