#!/usr/bin/env python3
"""Librería de transiciones/efectos virales con ffmpeg. Recetas como funciones que
devuelven el comando ffmpeg. Convención: 1080x1920, 30fps. Importar o usar el CLI.

CLI:  python transitions.py xfade A.mp4 B.mp4 out.mp4 --type wiperight --dur 0.25   (offset: auto = durA−dur)
      python transitions.py punch in.mp4 out.mp4 --at 2.0 --zoom 1.15
      python transitions.py flash A.mp4 B.mp4 out.mp4 --color white
      python transitions.py shake in.mp4 out.mp4 --at 1.5
      python transitions.py rgbsplit in.mp4 out.mp4 --at 2.0
      python transitions.py kenburns in.mp4 out.mp4 --dur 5
"""
import argparse, subprocess, sys

def _dur(path):
    """Duración en segundos vía ffprobe (None si no se puede leer, p. ej. una imagen)."""
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                      "-of","csv=p=0",path],capture_output=True,text=True)
    try: return float(r.stdout.strip())
    except ValueError: return None

# --- xfade entre dos clips (fade, wipeleft/right/up/down, slideX, circleopen/close, dissolve,
#     pixelize, radial, smoothleft, fadewhite/black, diagtl ...) ---
def xfade(a, b, out, ttype="fade", dur=0.3, offset=None):
    # offset correcto = durA - dur; si difiere, el acrossfade deja el audio más largo
    # que el video (desync). Sin --offset se calcula solo.
    da=_dur(a)
    if offset is None:
        if da is None: raise SystemExit(f"No pude leer la duración de {a}; pasa --offset")
        offset=max(da-dur,0)
    elif da is not None and abs(offset-(da-dur))>0.05:
        print(f"⚠️  offset={offset} pero durA−dur={da-dur:.2f}; el audio quedará desincronizado",file=sys.stderr)
    return ["ffmpeg","-y","-i",a,"-i",b,"-filter_complex",
            f"[0][1]xfade=transition={ttype}:duration={dur}:offset={offset},format=yuv420p[v];"
            f"[0:a][1:a]acrossfade=d={dur}[a]",
            "-map","[v]","-map","[a]","-c:v","libx264","-crf","18","-c:a","aac",out]

# --- flash (blanco/negro) en el corte ---
def flash(a, b, out, offset=None, color="white"):
    t = "fadewhite" if color=="white" else "fadeblack"
    return xfade(a,b,out,t,0.2,offset)

# --- zoom punch / punch-in en un instante ---
def punch(inp, out, at=2.0, zoom=1.15, hold=0.5):
    # zoom pulsado: escala arriba durante [at, at+hold] y vuelve.
    # zoompan NO tiene variable t: el reloj es 'it' (in_time).
    z=f"if(between(it,{at},{at+hold}),{zoom},1.0)"
    return ["ffmpeg","-y","-i",inp,"-vf",
            f"scale=1620:2880,zoompan=z='{z}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,setsar=1",
            "-c:v","libx264","-crf","18","-c:a","copy",out]

# --- impact shake (sacudida amortiguada en 'at') ---
def shake(inp, out, at=1.5, amp=24):
    vf=(f"scale=ceil(iw*1.08/2)*2:ceil(ih*1.08/2)*2,"
        f"crop=1080:1920:"
        f"x='(in_w-1080)/2+{amp}*sin(t*90)*max(0,1-(t-{at})*8)':"
        f"y='(in_h-1920)/2+{amp}*cos(t*110)*max(0,1-(t-{at})*8)'")
    return ["ffmpeg","-y","-i",inp,"-vf",vf,"-c:v","libx264","-crf","18","-c:a","copy",out]

# --- RGB split / chromatic aberration pulsado ---
def rgbsplit(inp, out, at=2.0, dur=0.2, amt=8):
    en=f"between(t,{at},{at+dur})"
    vf=f"rgbashift=rh={amt}:bh=-{amt}:enable='{en}',noise=alls=14:allf=t+u:enable='{en}'"
    return ["ffmpeg","-y","-i",inp,"-vf",vf,"-c:v","libx264","-crf","18","-c:a","copy",out]

# --- glitch corto ---
def glitch(inp, out, at=2.0, dur=0.15):
    en=f"between(t,{at},{at+dur})"
    vf=(f"rgbashift=rh=10:bv=-10:enable='{en}',"
        f"noise=alls=24:allf=t+u:enable='{en}'")
    return ["ffmpeg","-y","-i",inp,"-vf",vf,"-c:v","libx264","-crf","18","-c:a","copy",out]

# --- Ken Burns (push-in lento) — imagen fija O video ---
def kenburns(inp, out, dur=5, z=1.18):
    din=_dur(inp)
    if din is not None and din>0.5:
        # VIDEO: d=1 (un frame de salida por frame de entrada) y reloj 'it';
        # con d>1 zoompan repetiría cada frame y estiraría la duración.
        rate=(z-1.0)/max(dur,0.1)
        vf=(f"scale=1620:2880,zoompan=z='min(1+{rate:.5f}*it,{z})':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,setsar=1")
    else:
        # IMAGEN fija: d = frames totales del clip resultante
        frames=int(dur*30)
        vf=(f"scale=1620:2880,zoompan=z='min(zoom+0.0009,{z})':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30,setsar=1")
    return ["ffmpeg","-y","-i",inp,"-vf",vf,"-c:v","libx264","-crf","18","-c:a","copy",out]

# --- overlay alpha (.mov qtrle / png) sobre base, en ventana de tiempo ---
def overlay(base, ovl, out, x=0, y=0, appear=0.0, end=None):
    en = f":enable='gte(t,{appear})'" if end is None else f":enable='between(t,{appear},{end})'"
    return ["ffmpeg","-y","-i",base,"-itsoffset",str(appear),"-i",ovl,"-filter_complex",
            f"[1:v]format=rgba[o];[0:v][o]overlay={x}:{y}:eof_action=pass{en}[v]",
            "-map","[v]","-map","0:a?","-c:v","libx264","-crf","18","-c:a","aac",out]

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="cmd",required=True)
    def add(name,*args):
        s=sub.add_parser(name)
        for a,kw in args: s.add_argument(a,**kw)
        return s
    s=sub.add_parser("xfade"); [s.add_argument(a) for a in ("a","b","out")]
    s.add_argument("--type",default="fade"); s.add_argument("--dur",type=float,default=0.3); s.add_argument("--offset",type=float,default=None)
    s=sub.add_parser("flash"); [s.add_argument(a) for a in ("a","b","out")]; s.add_argument("--offset",type=float,default=None); s.add_argument("--color",default="white")
    s=sub.add_parser("punch"); [s.add_argument(a) for a in ("inp","out")]; s.add_argument("--at",type=float,default=2.0); s.add_argument("--zoom",type=float,default=1.15)
    s=sub.add_parser("shake"); [s.add_argument(a) for a in ("inp","out")]; s.add_argument("--at",type=float,default=1.5)
    s=sub.add_parser("rgbsplit"); [s.add_argument(a) for a in ("inp","out")]; s.add_argument("--at",type=float,default=2.0)
    s=sub.add_parser("glitch"); [s.add_argument(a) for a in ("inp","out")]; s.add_argument("--at",type=float,default=2.0)
    s=sub.add_parser("kenburns"); [s.add_argument(a) for a in ("inp","out")]; s.add_argument("--dur",type=float,default=5)
    s=sub.add_parser("overlay"); [s.add_argument(a) for a in ("base","ovl","out")]; s.add_argument("--x",type=int,default=0); s.add_argument("--y",type=int,default=0); s.add_argument("--appear",type=float,default=0.0)
    a=p.parse_args()
    fn={"xfade":lambda:xfade(a.a,a.b,a.out,a.type,a.dur,a.offset),
        "flash":lambda:flash(a.a,a.b,a.out,a.offset,a.color),
        "punch":lambda:punch(a.inp,a.out,a.at,a.zoom),
        "shake":lambda:shake(a.inp,a.out,a.at),
        "rgbsplit":lambda:rgbsplit(a.inp,a.out,a.at),
        "glitch":lambda:glitch(a.inp,a.out,a.at),
        "kenburns":lambda:kenburns(a.inp,a.out,a.dur),
        "overlay":lambda:overlay(a.base,a.ovl,a.out,a.x,a.y,a.appear)}[a.cmd]()
    print(" ".join(fn)); sys.exit(subprocess.run(fn).returncode)

if __name__=="__main__": main()
