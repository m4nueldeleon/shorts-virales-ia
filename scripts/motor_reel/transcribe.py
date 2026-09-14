import json, sys, mlx_whisper
src, out = sys.argv[1], sys.argv[2]
r = mlx_whisper.transcribe(src, path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
    language="es", word_timestamps=True, condition_on_previous_text=False)
json.dump(r, open(out, "w"), ensure_ascii=False, indent=1)
for s in r["segments"]:
    print(f'[{s["start"]:7.2f}-{s["end"]:7.2f}] {s["text"].strip()}')
