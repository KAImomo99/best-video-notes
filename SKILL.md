---
name: video-notes
description: Generate structured, beautifully formatted HTML notes from a YouTube video. Extracts subtitles via yt-dlp, summarizes content with AI, and produces a self-contained HTML document with SVG diagrams, a sidebar navigation, and a searchable subtitle viewer. This skill should be used when a user provides a YouTube URL and asks to take notes, summarize a video, or create a study document from video content.
---

# Video Notes Skill

Convert any YouTube video into a polished, self-contained HTML notes document with:
- AI-generated structured notes with key takeaways
- Content-specific SVG diagrams and visual summaries
- Fixed sidebar navigation with scroll-spy
- Searchable raw subtitles panel (click any line → jump to that timestamp in YouTube)

## Workflow

### Step 1: Extract Subtitles

Run the extraction script. It handles yt-dlp installation, downloads auto-generated captions, deduplicates the rolling subtitle format, and outputs clean JSON:

```bash
python3 ~/.claude/skills/video-notes/scripts/extract_subtitles.py <youtube_url> --output /tmp/subs.json
```

- Default language: `en`. Pass `--lang zh` or `--lang zh-Hans` for Chinese.
- On HTTP 429 errors, retry after a few seconds or try a different language.
- If the video has no auto-generated captions, inform the user and stop.

The output is a JSON array:
```json
[{"t": "mm:ss", "s": 123.4, "text": "...subtitle text..."}]
```

### Step 2: Read and Understand the Content

Read the subtitle text to understand:
- The video's main topic and structure
- Key concepts, arguments, frameworks, and terminology
- Any notable quotes or memorable lines
- Natural section boundaries (topic shifts)

### Step 3: Generate HTML Notes

Use `assets/note-template.html` as the foundation. Fill in each placeholder:

| Placeholder | Content |
|---|---|
| `{{TITLE}}` | Page `<title>` tag |
| `{{SIDEBAR_NAV}}` | `.sb-logo` block + `.nav-a` links for each section |
| `{{MAIN_CONTENT}}` | All content sections (hero + notes sections) |
| `{{SUBTITLE_SEC_NUM}}` | Section number for the subtitle panel (e.g. `5`) |
| `{{VIDEO_URL}}` | Full YouTube URL |
| `{{VIDEO_ID}}` | YouTube video ID (e.g. `dQw4w9WgXcQ`) |
| `{{SUBTITLE_JSON}}` | The full JSON array from Step 1 |
| `{{SECTION_IDS}}` | JS array of section IDs: `['hero','s1','s2','subtitles']` |

#### Hero Section

Always include a hero section (`id="hero"`) with:
- `.hero-badge`: speaker name + event/source
- `<h1>`: video title (concise, impactful)
- `.hero-sub`: speaker · role · note type
- `.chips`: 3–5 topic tags
- `.hero-quote`: the single most memorable quote from the video

#### Note Sections

For each major topic area, create a `<div class="sec" id="sN">` with:
- `.sec-hd` header (numbered `.sec-n` + `.sec-title`)
- Content using cards (`.card`), grids (`.g2`, `.g3`), diagrams (`.diag`), timelines (`.tl`), or quotes (`.ql`)

#### SVG Diagrams (`.diag` blocks)

Generate SVG diagrams for concepts that benefit from visualization:
- **Comparison/parallel structures** → side-by-side flow with gradient-colored rect blocks
- **Evolution/progression** → bar chart or step-up chart
- **Architecture/pipelines** → box-and-arrow flow diagram
- **Timelines** → vertical `.tl` HTML list (no SVG needed)

SVG style conventions:
```
Background fills: rgba(R,G,B,.4) with matching stroke rgba(R,G,B,.3)
Text: fill="#fff" font-weight="700" for labels; fill="#aaa" font-size="9-10" for sublabels
Arrows: › character in a <text> element, colored to match the row
Connectors: stroke="rgba(255,255,255,.12)" stroke-dasharray="3,3"
```

Color palette:
- Blue flow: `#5b8dee` → `#9b7cf4`
- Green flow: `#3ecf8e` → `#5b8dee`
- Danger/old: `rgba(244,63,94,.4)`
- Warning/mid: `rgba(240,169,70,.4)`
- Success/new: `rgba(62,207,142,.4)`

#### Sidebar Navigation

```html
<div class="sb-logo">
  <div class="sb-logo-icon">🎬</div>
  <h2>{{Short Title}}</h2>
  <p>{{Speaker}} · {{Source}}</p>
</div>
<a class="nav-a active" href="#hero"><span class="nav-icon">🏠</span>概览</a>
<!-- one .nav-a per section -->
<div class="nav-sep"></div>
<a class="nav-a" href="#subtitles"><span class="nav-icon">📄</span>原始字幕</a>
```

### Step 4: Save and Open

Save the completed HTML to a sensible path (default: `/tmp/<video-id>-notes.html`) and open it:

```bash
open /tmp/<video-id>-notes.html   # macOS
# or: xdg-open ...                # Linux
```

Tell the user:
- The save path
- How many subtitle entries were extracted
- The sections covered in the notes

## Quality Guidelines

- **Depth over breadth**: 4–7 well-developed sections beat 12 shallow ones.
- **Diagrams are mandatory** when the content contains comparisons, progressions, or architectures.
- **Every section needs visual texture**: mix cards, grids, and diagrams — avoid walls of text.
- **Subtitle completeness**: always include the subtitle section; it's the user's link back to the source.
- **Language matching**: write notes in the same language as the user's request. If the user writes in Chinese, the notes UI should be in Chinese even if the video is in English.
