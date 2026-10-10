# Pro prompt: Bushra's School, "Learn languages by levels" (Instagram Reel)

Use this prompt to rebuild or re-roll the ad. It replaces the QR-code explainer prompt.

---

<inputs>
Ask me for:
1. The exact voice-over lines (default: the script in `VOICEOVER.md`).
2. My recorded voice as a WAV/MP3/M4A (record it against the timings in `VOICEOVER.md`; if I skip it, deliver the video with burned-in subtitles and a voice-ready music bed).
3. 4 to 6 vertical clips of the school (corridors, classrooms, posters, windows). Default: the 7 WhatsApp walkthrough clips already supplied.
4. The crest as a clean PNG/SVG. Default: the supplied BUSHRA'S SCHOOL crest.
5. Price and duration. Default: 6000 DA for 3 months.
6. Contacts. Default: Instagram @bushrasschool40 · Facebook Bushra's School · WhatsApp 0669 65 45 15 · Khenchela.
Never show the supplied teacher photos in this ad: those teachers do not teach the language-level course.
</inputs>

<direction>
A 32.5-second vertical Instagram Reel, 1080x1920 at 60fps, Arabic, RTL. One continuous 2D take: no cuts, no crossfades, no blur-ins.
Each scene grows out of the previous one: words converge into a gold dot, the dot climbs the level steps,
the top step becomes the language panel, the French card grows into a window onto the real school,
the window folds into a price ticket, and the price floods the frame in gold before shrinking into the crest's medallion.
Text rises from a mask line. Pops and settles use closed-form damped springs.
The camera makes one eased move per scene, only pushes in or pans (it never zooms out and never reverses direction),
and it resets only while the gold flood covers the whole frame.

Look: the brand's own palette. Cream canvas (#FBF6EA) with a warm radial light and a faint static paper grain,
deep indigo (#2B1666) for UI, gold (#F5B82E) as the single accent. Markazi Text for everything, Arabic and Latin.
Real footage of the school inside a rounded indigo frame with a thin gold hairline. Flags drawn as clean circles.
Mood: soft, calm, confident and premium. Nothing loud, nothing that feels like a template.

Banned: crossfades, blur, 3D, particles, emoji, stock teachers, invented claims (no "best", no "limited places", no fake numbers),
keyboard/typing sounds, holds longer than one second without some motion, camera direction reversals.
</direction>

<structure>
96 BPM, D major, 52 beats (32.5 s). Each section starts on a downbeat.

0.0-5.0, hello: "مرحبًا" rises at the centre with a hand-drawn gold swash. Bonjour, Hello, Hola and Hallo pop in around it on the off-beats.
At 4.3 everything converges into one gold dot.

5.0-8.75, levels: four indigo steps rise right to left (RTL): A1 مبتدئ, A2 أساسي, B1 متوسط, B2 متقدّم.
The dot hops onto each step on the beat, with a soft squash, and the label rises as it lands. Title: "تعلّم اللغة / بالمستويات".

8.75-13.75, languages: A1 to B1 fold down; B2 morphs into a 900x900 indigo panel. Title "أربع لغات".
Four cream cards pop in on the beats: الفرنسية Bonjour, الإنجليزية Hello, الإسبانية Hola, الألمانية Hallo.
The dot travels to the French card and becomes a gold ring that draws around it.

13.75-21.25, the school: the French card grows into a tall window. Its flag floods outward (blue, white, red), and the real footage opens inside it.
Each next clip is revealed by a growing circle with a gold edge: corridor with the Eiffel shelf → alphabet poster → THINK poster → window over Khenchela → classroom rows.
Chips rise in the top corner: أقسام مريحة · جوّ هادئ للتعلّم · متابعة مستمرة · هنا في خنشلة.

21.25-25.6, price: the window folds into a ticket with side notches and a dashed perforation that draws itself.
"3 أشهر / من الدراسة" rises in. 6000 rolls up like an odometer, "دج" rises beside it, then a "فقط" pill pops in. A light sheen crosses the ticket.

25.6-32.5, end card: the price floods the frame in gold. The gold shrinks into a medallion on indigo, and the crest springs onto it. A cream ring draws around it.
"مدرسة بشرى" rises from behind the medallion, then the BUSHRA'S SCHOOL wordmark, then the gold "سجّل الآن" pill.
Then the contacts: WhatsApp 0669 65 45 15 · خنشلة · @bushrasschool40 · Bushra's School.
</structure>

<subtitles>
Burned-in, screen-space (not affected by the camera), centred at y≈1600 to stay out of Instagram's caption area.
Markazi Text 600, 66px, cream on a 93% indigo pill. 2-5 words per chunk. Each word rises from a mask with a 70 ms stagger,
and the chunk exits upward. Keep each chunk on screen for at least 0.3 s per word. Also deliver an .srt file.
</subtitles>

<sound>
One piece of music: felt piano, a warm detuned pad, soft sub bass, a brushed groove (kick on 1 and 3, brushes on 2 and 4) from the levels scene to the price,
and marimba arpeggios under the footage. Every effect is in D major and goes through the same room reverb as the music:
plucks climb the scale as the dot climbs the levels, bells mark the four language cards, soft airy whooshes mark the reveals,
a rising run then a three-note bell chord lands the price, a low boom and a cymbal wash mark the gold flood, and a bell sparkle marks the crest.
No typing sounds. Effects sit under the music. Master at -14 LUFS, true peak -1.5 dBTP.
Also deliver a voice-ready bed that dips the music 6 dB under every voice line.
</sound>

<build>
1. One HTML file, 1080x1920. Compute every style inside seek(t) from time alone: no CSS transitions, no timers, no state carried between frames.
2. One camera transform on a world container, keyed by [t, zoom, x, y] with eased segments and log-space zoom.
3. Closed-form spring step responses for every pop and settle.
4. Shared elements for every handoff: the dot, the B2 step that becomes the panel, the French card that becomes the window and then the ticket, the gold ring, and the price flood that becomes the medallion.
5. Footage is pre-extracted to frames (cropped, sharpened, warm grade) and swapped per frame, waiting for each frame to decode.
6. Render with Playwright at 60fps in parallel workers, then mux with the soundtrack. Check stills from every scene and mid-transition before the final render.
</build>
