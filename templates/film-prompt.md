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
Reference: <the film or frames we match, and what we take: shot lengths, transitions, type entrances, energy target (its mean motion)>.
<The feel in 3 short lines, in the product's own voice.>
Ingredients (from the interview): <brand element> · <how words appear> · <how scenes connect> · <extras>.
The product's screens use only its own surfaces, colors, borders and effects. The idea's world and any featured partner bring their own look.
Banned: <from BRAND.md, plus anything the product's language does not use, words the product avoids, false claims>.
Claims: <what the product does and never does, as the user states it>.
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
Energy: <the curve you chose, and where the peak is>.
| Time | Bar or word | On screen | Camera | Heard |
|---|---|---|---|---|
| 0.0 | frame 0 (the cover) | <a still that names the subject> | <...> | |
| | | <...> | <...> | <...> |
</beat-sheet>

<start>
Before any scene code, show the chosen idea, the beat sheet (and the voice script, read aloud once for fit), style frames of the opening and one key scene, and a motion test of the peak. Wait for OK.
</start>
