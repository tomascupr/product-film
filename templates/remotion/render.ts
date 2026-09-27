import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, rmSync, statSync } from "node:fs";
import { join } from "node:path";

/**
 * Final render: a 240 fps master (4 subframes per 60 fps frame), blended with
 * ffmpeg tmix into 60 fps motion blur, then the deliverables.
 *
 *   node scripts/render.ts <CompositionId> <file-name> --duration 52.8 --poster 48.4   (from the film folder)
 *
 * The composition must take `fps` as a prop (calculateMetadata sets fps and
 * durationInFrames from it). ffmpeg comes from imageio-ffmpeg through uv:
 * Remotion's own build has no tmix, select or tile filters. Audio is audio/mix.wav
 * from mix.py (the composition itself renders muted), muxed when it exists.
 */
const args = process.argv.slice(2);
const flag = (name: string) => {
  const index = args.indexOf(name);
  return index === -1 ? undefined : args[index + 1];
};
const [composition, name] = args;
const duration = Number(flag("--duration"));
const posterSeconds = Number(flag("--poster") ?? duration / 2);
if (!composition || !name || !duration) throw new Error("Usage: node scripts/render.ts <CompositionId> <file-name> --duration <s> [--poster <s>]");

const root = process.cwd();
const out = join(root, "out", name);
mkdirSync(out, { recursive: true });
const run = (command: string, list: string[]) => execFileSync(command, list, { cwd: root, stdio: "inherit" });
const ffmpeg = execFileSync("uv", ["run", "--quiet", "--with", "imageio-ffmpeg", "python3", "-c", "import imageio_ffmpeg as i; print(i.get_ffmpeg_exe())"], { encoding: "utf8" }).trim();

const master = join(out, "master-240.mp4");
const audio = join(root, "audio", "mix.wav");
const blurred = join(out, "blurred-60.mov");
const frames = Math.round(duration * 60);

// 1. The 240 fps master: lossless-ish PNG frames, 4:4:4 so fine textures keep their edges. No audio.
//    --color-space bt709 (Remotion's default from v5) so the matrix is known below.
run("npx", ["remotion", "render", "src/index.ts", composition, master, "--props", JSON.stringify({ fps: 240 }), "--codec", "h264", "--crf", "8", "--pixel-format", "yuv444p", "--image-format", "png", "--color-space", "bt709", "--muted", "--concurrency", "8", "--log", "error"]);

// 2. Motion blur: average each group of 4 subframes, keep one per group -> 60 fps.
//    Read the master as BT.709 limited range. If verify.py reports a lifted or crushed
//    background, this Remotion version tags the master differently: check with
//    `ffmpeg -i master-240.mp4` and match in_range / in_color_matrix to what it says.
run(ffmpeg, [
  "-v", "error", "-y", "-i", master,
  "-vf", "tmix=frames=4:weights='1 1 1 1',select='not(mod(n+1\\,4))',setpts=N/(60*TB),scale=in_range=tv:out_range=tv:in_color_matrix=bt709:out_color_matrix=bt709,format=yuv444p10le",
  "-r", "60", "-c:v", "prores_ks", "-profile:v", "4444", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
  blurred,
]);

const h264 = ["-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-x264-params", "colorprim=bt709:transfer=bt709:colormatrix=bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv", "-movflags", "+faststart"];

// 3. A muted loop for the page, one with the music, a WebM, the poster.
run(ffmpeg, ["-v", "error", "-y", "-i", blurred, ...h264, "-an", join(out, `${name}-1080p60.mp4`)]);
if (existsSync(audio)) run(ffmpeg, ["-v", "error", "-y", "-i", blurred, "-i", audio, ...h264, "-c:a", "aac", "-b:a", "256k", "-shortest", join(out, `${name}-1080p60-audio.mp4`)]);
run(ffmpeg, ["-v", "error", "-y", "-i", blurred, "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "32", "-row-mt", "1", "-pix_fmt", "yuv420p", "-an", join(out, `${name}-1080p60.webm`)]);
run(ffmpeg, ["-v", "error", "-y", "-ss", String(posterSeconds), "-i", blurred, "-frames:v", "1", "-q:v", "2", join(out, "poster.jpg")]);

// 4. Loop seam: the last 8 and first 8 frames, played twice back to back, in one sheet.
run(ffmpeg, ["-v", "error", "-y", "-stream_loop", "1", "-i", join(out, `${name}-1080p60.mp4`), "-vf", `select='between(n\\,${frames - 8}\\,${frames + 7})',scale=320:180,tile=8x2`, "-frames:v", "1", "-fps_mode", "vfr", join(out, "loop-seam.png")]);

rmSync(master);
rmSync(blurred);
for (const file of [`${name}-1080p60.mp4`, `${name}-1080p60-audio.mp4`, `${name}-1080p60.webm`, "poster.jpg"].filter((file) => existsSync(join(out, file)))) {
  console.log(`${file}: ${(statSync(join(out, file)).size / 1e6).toFixed(1)} MB`);
}
