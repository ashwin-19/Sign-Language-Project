import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import whisper
import urllib.parse
import os
import json
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog

# ─── MODE SELECTOR ─────────────────────────────────────────────
def choose_mode():
    root = tk.Tk()
    root.title("ASL Sign Language Viewer")
    root.geometry("440x280")
    root.configure(bg="#0D0D1A")
    root.resizable(False, False)
    root.wm_attributes("-topmost", True)
    chosen = {"mode": None}

    tk.Label(root, text="🤟 ASL Sign Language Viewer",
             font=("Georgia", 16, "bold"),
             bg="#0D0D1A", fg="#F0EEFF").pack(pady=(28, 6))
    tk.Label(root, text="Choose your input mode",
             font=("Helvetica", 11),
             bg="#0D0D1A", fg="#9A94CC").pack(pady=(0, 22))

    cfg = dict(width=24, height=2, font=("Helvetica", 12, "bold"),
               bd=0, cursor="hand2", relief="flat")

    def pick_file():
        chosen["mode"] = "file"
        root.destroy()

    def pick_mic():
        chosen["mode"] = "mic"
        root.destroy()

    tk.Button(root, text="📂   Audio File",
              bg="#7C6DFA", fg="white", command=pick_file, **cfg).pack(pady=7)
    tk.Button(root, text="🎤   Live Microphone",
              bg="#1D9E75", fg="white", command=pick_mic, **cfg).pack(pady=7)
    root.mainloop()
    return chosen["mode"]


# ─── FILE MODE ─────────────────────────────────────────────────
def transcribe_file():
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", True)
    print("\nSelect your audio file...")
    audio_file = filedialog.askopenfilename(
        title="Select audio file",
        filetypes=[("Audio files", "*.mp3 *.wav *.m4a *.ogg *.flac"),
                   ("All files", "*.*")]
    )
    root.destroy()
    if not audio_file:
        print("❌ No file selected.")
        exit()
    print(f"✅ Selected: {audio_file}")
    print("Loading Whisper AI model...")
    model = whisper.load_model("base")
    print("Transcribing...")
    result = model.transcribe(audio_file)
    text = result["text"]
    print(f"\n--- TRANSCRIPT ---\n{text}\n")
    return text


# ─── MIC MODE ──────────────────────────────────────────────────
def transcribe_mic():
    try:
        import sounddevice as sd
        import numpy as np
    except ImportError:
        print("❌ Run: pip3 install sounddevice numpy")
        exit()

    SAMPLE_RATE = 16000
    CHUNK_SECS  = 6
    all_text    = []

    print("\nLoading Whisper AI model...")
    model = whisper.load_model("base")
    print("✅ Model ready!\n")

    win = tk.Tk()
    win.title("🎤 Live ASL Viewer")
    win.geometry("500x380")
    win.configure(bg="#0D0D1A")
    win.wm_attributes("-topmost", True)
    win.resizable(False, False)

    tk.Label(win, text="🎤  Live Sign Language Viewer",
             font=("Georgia", 14, "bold"),
             bg="#0D0D1A", fg="#F0EEFF").pack(pady=(20, 4))
    tk.Label(win,
             text=f"Records {CHUNK_SECS}s chunks · Signs open in browser automatically",
             font=("Helvetica", 9), bg="#0D0D1A", fg="#9A94CC").pack()

    status_var = tk.StringVar(value="⏸  Press Start to begin")
    tk.Label(win, textvariable=status_var,
             font=("Helvetica", 11, "bold"),
             bg="#0D0D1A", fg="#1D9E75").pack(pady=(16, 4))

    caption_var = tk.StringVar(value="Transcription will appear here...")
    tk.Label(win, textvariable=caption_var,
             font=("Helvetica", 11), bg="#12121A", fg="#F0EEFF",
             wraplength=450, justify="left", width=52, height=5,
             anchor="nw", padx=10, pady=8).pack(padx=20, pady=6)

    chunk_var = tk.StringVar(value="Chunks processed: 0")
    tk.Label(win, textvariable=chunk_var,
             font=("Helvetica", 9),
             bg="#0D0D1A", fg="#7A7A99").pack()

    btn_frame = tk.Frame(win, bg="#0D0D1A")
    btn_frame.pack(pady=16)

    running     = {"active": False}
    chunk_count = {"n": 0}

    def open_page(text):
        words = [w.lower().strip(".,!?;:\"'")
                 for w in text.strip().split()
                 if len(w.strip(".,!?;:\"'")) >= 2]
        encoded  = urllib.parse.quote(build_html(text, words), safe='')
        data_url = "data:text/html;charset=utf-8," + encoded
        try:
            subprocess.run(["open", "-a", "Safari", data_url], check=True)
        except Exception:
            try:
                subprocess.run(["open", "-a", "Google Chrome", data_url], check=True)
            except Exception:
                subprocess.run(["open", data_url])

    def record_loop():
        while running["active"]:
            status_var.set("🔴  Recording...")
            win.update()
            audio = sd.rec(int(CHUNK_SECS * SAMPLE_RATE),
                           samplerate=SAMPLE_RATE, channels=1, dtype="float32")
            sd.wait()
            if not running["active"]:
                break
            status_var.set("⚙️  Transcribing...")
            win.update()
            result = model.transcribe(audio.flatten(), fp16=False)
            chunk_text = result["text"].strip()
            if chunk_text:
                all_text.append(chunk_text)
                chunk_count["n"] += 1
                full = " ".join(all_text)
                caption_var.set(full[-200:] if len(full) > 200 else full)
                chunk_var.set(f"Chunks processed: {chunk_count['n']}")
                print(f"\n[Chunk {chunk_count['n']}] {chunk_text}")
                open_page(full)
            status_var.set("⏸  Waiting for next chunk...")
            win.update()

    def start_rec():
        if running["active"]:
            return
        running["active"] = True
        start_btn.config(state="disabled", bg="#444466")
        stop_btn.config(state="normal",    bg="#D85A30")
        threading.Thread(target=record_loop, daemon=True).start()

    def stop_rec():
        running["active"] = False
        start_btn.config(state="normal",   bg="#1D9E75")
        stop_btn.config(state="disabled",  bg="#444466")
        status_var.set("⏹  Stopped")
        if all_text:
            open_page(" ".join(all_text))

    start_btn = tk.Button(btn_frame, text="▶  Start",
                          bg="#1D9E75", fg="white",
                          font=("Helvetica", 12, "bold"),
                          width=12, height=2, bd=0,
                          cursor="hand2", relief="flat", command=start_rec)
    start_btn.grid(row=0, column=0, padx=10)

    stop_btn = tk.Button(btn_frame, text="⏹  Stop",
                         bg="#444466", fg="white",
                         font=("Helvetica", 12, "bold"),
                         width=12, height=2, bd=0,
                         cursor="hand2", relief="flat",
                         state="disabled", command=stop_rec)
    stop_btn.grid(row=0, column=1, padx=10)

    win.mainloop()
    return " ".join(all_text) if all_text else ""


# ─── BUILD HTML ────────────────────────────────────────────────
def build_html(transcript, words):
    words_json = json.dumps(words)

    caption_spans = " ".join(
        f'<span class="caption-word" id="cw-{i}" onclick="stopAuto();showWord({i})">'
        f'{w}</span>'
        for i, w in enumerate(words)
    )

    js = """
const WORDS   = """ + words_json + """;
let current   = -1;
let autoTimer = null;
let isPlaying = false;

function showWord(idx) {
  if (idx < 0 || idx >= WORDS.length) return;
  current = idx;
  const word = WORDS[idx];

  document.getElementById('cur-word').textContent  = word.toUpperCase();
  document.getElementById('cur-index').textContent = (idx+1) + ' / ' + WORDS.length;
  document.getElementById('progress-fill').style.width = ((idx+1)/WORDS.length*100) + '%';
  document.getElementById('sign-link-1').href = 'https://www.signasl.org/sign/' + word;
  document.getElementById('sign-link-2').href = 'https://www.handspeak.com/word/search/index.php?id=' + word;
  document.getElementById('sign-link-3').href = 'https://www.signingsavvy.com/search/' + word;

  // Update chip states
  document.querySelectorAll('.chip').forEach((c,i) => {
    if      (i < idx)  c.className = 'chip done';
    else if (i === idx) c.className = 'chip active';
    else                c.className = 'chip';
  });

  // Scroll active chip into view
  const activeChip = document.getElementById('chip-'+idx);
  if (activeChip) activeChip.scrollIntoView({behavior:'smooth', block:'nearest'});

  // Highlight word in transcript
  document.querySelectorAll('.caption-word').forEach((s,i) => {
    s.style.background  = i === idx ? '#7c6dfa44' : 'transparent';
    s.style.color       = i === idx ? '#f0eeff'   : '#9a94cc';
    s.style.fontWeight  = i === idx ? '700'       : '300';
    s.style.borderRadius = '4px';
    s.style.padding      = '0 3px';
  });
}

function buildChips() {
  const box = document.getElementById('chips');
  box.innerHTML = '';
  WORDS.forEach((w,i) => {
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.id = 'chip-' + i;
    chip.textContent = w.toUpperCase();
    chip.onclick = () => { stopAuto(); showWord(i); };
    box.appendChild(chip);
  });
}

function next() { if (current < WORDS.length-1) showWord(current+1); }
function prev() { if (current > 0) showWord(current-1); }

function startAuto() {
  if (isPlaying) return;
  isPlaying = true;
  document.getElementById('btn-play').textContent = '⏸ Pause';
  document.getElementById('btn-play').style.background = '#444466';
  if (current < 0) showWord(0);
  autoTimer = setInterval(() => {
    if (current >= WORDS.length-1) {
      stopAuto();
      document.getElementById('status').textContent = '✅ Signing complete!';
      return;
    }
    showWord(current+1);
  }, 2500);
}

function stopAuto() {
  isPlaying = false;
  clearInterval(autoTimer);
  document.getElementById('btn-play').textContent = '▶ Auto Play';
  document.getElementById('btn-play').style.background = '#7c6dfa';
}

function togglePlay() {
  if (isPlaying) stopAuto();
  else startAuto();
}

function replay() {
  stopAuto();
  current = -1;
  document.getElementById('progress-fill').style.width = '0%';
  buildChips();
  showWord(0);
  document.getElementById('status').textContent = 'Press Auto Play to sign all words';
}

document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); stopAuto(); next(); }
  if (e.key === 'ArrowLeft')                    { e.preventDefault(); stopAuto(); prev(); }
  if (e.key === 'p' || e.key === 'P')           togglePlay();
});

buildChips();
showWord(0);
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>ASL Sign Language Viewer</title>
<style>
* {{margin:0;padding:0;box-sizing:border-box}}
body {{background:#0a0a0f;color:#f0eeff;font-family:'Segoe UI',sans-serif;min-height:100vh}}
#header {{text-align:center;padding:20px 16px 10px;border-bottom:1px solid #1a1a28}}
#header h1 {{font-size:26px;color:#7c6dfa;margin-bottom:4px}}
#header p {{font-size:12px;color:#9a94cc}}
#layout {{display:flex;max-width:1200px;margin:0 auto;padding:16px;gap:16px;min-height:calc(100vh - 80px)}}

/* Left panel */
#left {{display:flex;flex-direction:column;align-items:center;width:520px;flex-shrink:0}}
#sign-card {{width:520px;height:340px;border-radius:16px;border:1px solid #2a2a40;
  background:#12121a;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:20px}}
#cur-word-big {{font-size:80px;font-weight:700;color:#7c6dfa;font-family:monospace;
  letter-spacing:-2px;min-height:90px;text-align:center}}
#sign-links {{display:flex;flex-direction:column;gap:8px;align-items:center;width:100%}}
.sign-btn {{display:block;padding:11px 0;border-radius:10px;font-size:13px;
  font-weight:700;text-decoration:none;text-align:center;transition:all .2s;width:280px}}
.btn-1 {{background:#7c6dfa;color:#fff}}
.btn-1:hover {{background:#9a8dfc}}
.btn-2 {{background:#1a1a28;color:#9a94cc;border:1px solid #2a2a40}}
.btn-2:hover {{border-color:#fa6d9a;color:#fa6d9a}}
#word-meta {{text-align:center;margin-top:10px;width:100%}}
#cur-word {{font-size:32px;font-weight:700;color:#7c6dfa;font-family:monospace;min-height:42px}}
#cur-index {{font-size:12px;color:#9a94cc;margin-top:2px}}
#progress-bar {{width:100%;height:4px;background:#2a2a40;border-radius:2px;margin-top:8px;overflow:hidden}}
#progress-fill {{height:100%;background:linear-gradient(90deg,#7c6dfa,#fa6d9a);
  width:0%;transition:width .4s;border-radius:2px}}
#controls {{display:flex;gap:8px;margin-top:12px;justify-content:center;flex-wrap:wrap}}
button {{padding:9px 18px;border-radius:10px;border:none;font-size:13px;
  font-weight:700;cursor:pointer;transition:all .2s}}
#btn-play {{background:#7c6dfa;color:#fff;min-width:120px}}
#btn-prev,#btn-next,#btn-replay {{background:#1a1a28;color:#9a94cc;border:1px solid #2a2a40}}
#btn-prev:hover,#btn-next:hover,#btn-replay:hover {{border-color:#7c6dfa;color:#7c6dfa}}
#status {{font-size:11px;color:#7a7a99;margin-top:6px;text-align:center}}
#hint {{font-size:10px;color:#444466;text-align:center;margin-top:2px}}

/* Right panel */
#right {{flex:1;display:flex;flex-direction:column;gap:12px;overflow:hidden}}
#caption-box {{background:#12121a;border:1px solid #2a2a40;
  border-left:4px solid #7c6dfa;border-radius:12px;padding:14px;flex-shrink:0}}
#caption-box h3 {{font-size:9px;color:#7c6dfa;letter-spacing:.15em;
  text-transform:uppercase;margin-bottom:8px}}
#caption-words {{font-size:16px;line-height:2.0;font-weight:300;cursor:pointer}}
.caption-word {{padding:0 3px;border-radius:4px;color:#9a94cc;
  transition:all .2s;cursor:pointer}}
.caption-word:hover {{color:#f0eeff}}
#chips-box {{background:#12121a;border:1px solid #2a2a40;border-radius:12px;
  padding:14px;flex:1;overflow-y:auto}}
#chips-box h3 {{font-size:9px;color:#9a94cc;letter-spacing:.15em;
  text-transform:uppercase;margin-bottom:8px}}
#chips {{display:flex;flex-wrap:wrap;gap:6px}}
.chip {{padding:4px 10px;border-radius:999px;font-size:11px;font-family:monospace;
  border:1px solid #2a2a40;color:#9a94cc;background:#1a1a28;
  cursor:pointer;transition:all .2s}}
.chip:hover {{border-color:#7c6dfa;color:#7c6dfa}}
.chip.active {{background:#7c6dfa;color:#fff;border-color:#7c6dfa;font-weight:700;transform:scale(1.05)}}
.chip.done {{background:#1d9e7520;border-color:#1d9e75;color:#1d9e75}}
</style>
</head>
<body>
<div id="header">
  <h1>🤟 ASL Sign Language Viewer</h1>
  <p>Click a sign button to view · Use ← → arrow keys · Click any word or chip to jump</p>
</div>
<div id="layout">
  <div id="left">
    <div id="sign-card">
      <div id="cur-word-big">–</div>
      <div id="sign-links">
        <a id="sign-link-1" class="sign-btn btn-1" href="#" target="_blank">▶ Watch on SignASL</a>
        <a id="sign-link-2" class="sign-btn btn-2" href="#" target="_blank">▶ Watch on HandSpeak</a>
        <a id="sign-link-3" class="sign-btn btn-2" href="#" target="_blank">▶ Watch on Signing Savvy</a>
      </div>
    </div>
    <div id="word-meta">
      <div id="cur-word">–</div>
      <div id="cur-index">0 / {len(words)}</div>
    </div>
    <div id="progress-bar"><div id="progress-fill"></div></div>
    <div id="controls">
      <button id="btn-prev"   onclick="stopAuto();prev()">◀ Prev</button>
      <button id="btn-play"   onclick="togglePlay()">▶ Auto Play</button>
      <button id="btn-next"   onclick="stopAuto();next()">Next ▶</button>
      <button id="btn-replay" onclick="replay()">↺ Restart</button>
    </div>
    <div id="status">Press Auto Play · or ← → keys · or click any word</div>
    <div id="hint">Auto Play advances every 2.5s · P key to pause/resume</div>
  </div>
  <div id="right">
    <div id="caption-box">
      <h3>📢 Full transcript</h3>
      <div id="caption-words">{caption_spans}</div>
    </div>
    <div id="chips-box">
      <h3>Word queue — click any to jump</h3>
      <div id="chips"></div>
    </div>
  </div>
</div>
<script>
{js}
</script>
</body>
</html>"""
    return html


# ─── OPEN BROWSER ──────────────────────────────────────────────
def open_browser(data_url):
    try:
        subprocess.run(["open", "-a", "Safari", data_url], check=True)
    except Exception:
        try:
            subprocess.run(["open", "-a", "Google Chrome", data_url], check=True)
        except Exception:
            subprocess.run(["open", data_url])


# ─── MAIN ──────────────────────────────────────────────────────
print("=" * 50)
print("   ASL SIGN LANGUAGE VIEWER")
print("=" * 50)

mode = choose_mode()

if mode == "file":
    print("\n📂 File mode selected")
    full_text = transcribe_file()
    words = [w.lower().strip(".,!?;:\"'")
             for w in full_text.strip().split()
             if len(w.strip(".,!?;:\"'")) >= 2]
    encoded  = urllib.parse.quote(build_html(full_text, words), safe='')
    data_url = "data:text/html;charset=utf-8," + encoded
    print("\n✅ Opening Sign Language page...")
    open_browser(data_url)
    print("✅ Done! Press ▶ Auto Play to start.")

elif mode == "mic":
    print("\n🎤 Microphone mode selected")
    transcribe_mic()