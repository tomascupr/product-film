<context>
<Product> <does what, for whom, in one or two sentences>.
This film plays <where, from the interview>. It must read <with the sound off, if it plays muted>.
Read `../BRAND.md` first. It holds the look, the brand element, the components, the product owner's rulings, the voice and what we may claim. This prompt only adds the story.
</context>

<inputs>
Decided: <width>x<height>, 60 fps, <dark|light>, <seconds> s, engine <HTML | Remotion>.
Voice: <none | voice name, N lines, ~W words>. Music: <composed (audio/music-plan.json) | title, artist, license, edit bars a-b | silent>, grid <BPM>, <meter>. SFX: <list>.
</inputs>

<direction>
Idea: <the premise the user picked, in one line, and its opening image>.
<The feel in 3 short lines, in the product's own voice.>
Ingredients (from the interview): <brand element> · <how words appear> · <how scenes connect> · <extras>.
The product's screens use only its own surfaces, colors, borders and effects. The idea's world and any featured partner bring their own look.
Banned: <from BRAND.md, plus anything the product's language does not use, words the product avoids, false claims>.
</direction>

<voice>
<!-- Only with a voiceover. One line per scene; mark the word each moment lands on. -->
v1 (at ~1.0 s): "<line>"   lands: "<word>" -> <what happens on screen>
v2 (at ~4.5 s): "<line>"   lands: "<word>" -> <...>
</voice>

<cast>
- The brand element: <the logo, a wordmark, a mascot the product has, or none>, and where it appears.
- Cursors: <the user's OS arrow, the product's own cursor, or none>.
- Demo world, from the landing page: <names, data, placeholders>.
</cast>

<beat-sheet>
Energy curve: <hook> -> <build> -> PEAK at <time, word> -> <ride> -> <landing>. The peak gets the drop, the biggest hit, the biggest scale change and the accent color at once.
| Time | Bar or word | On screen | Camera (zoom, move) | Heard |
|---|---|---|---|---|
| 0.0 | frame 0 (the cover) | <a clean still that names the subject, readable at 300 px> | <framed on the subject, whole> | |
| 0.05 | bar 1 | <motion starts at once> | <e.g. snap back to wide> | <music intro, texture> |
| | v1 "<word>" | <...> | <creep 1.0 -> 1.3> | <riser into the peak> |
| **PEAK** | <word> | <...> | <snap to 3x, shake> | <drop, impact + sub> |
| | | <end card> | <slow push, a second reveal on the next bar> | <final hit> |
</beat-sheet>

<gotchas>
Text never travels across text. Keep a slot for every word before it lands. A texture under words stays thin there; behind UI it stays calm. If the film loops, the last frame equals frame 0. Judge the encoded file, and decode its pixels.
<Product claims: what needs a human approval step on screen, what the product never does.>
</gotchas>

<start>
Before any scene code, show the chosen idea, the beat sheet (and the voice script, read aloud once for fit) and three style frames: the opening, one feature scene, the strongest moment. Wait for OK.
</start>
