import wave, numpy as np, json, sys
w = wave.open(sys.argv[1]); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)/32768
hop = int(sr*0.02)
n = len(x)//hop
rms = np.sqrt(np.mean(x[:n*hop].reshape(n,hop)**2, axis=1)) + 1e-9
db = 20*np.log10(rms)
p10, p50, p90 = np.percentile(db,[10,50,90])
print(f"p10={p10:.1f} p50={p50:.1f} p90={p90:.1f}")
json.dump({"hop":0.02,"db":[round(float(v),1) for v in db]}, open(sys.argv[2],"w"))
