#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║              OBG APPS  -  AI App Generator               ║
║         ملف واحد يحتوي على كل شيء  Flask + HTML         ║
║   التثبيت:  pip install flask g4f                        ║
║   التشغيل:  python obg_apps.py                           ║
║   المتصفح:  http://localhost:5000                        ║
╚══════════════════════════════════════════════════════════╝
"""

# ─────────────────────────────────────────────────────────────────────────────
#  مكتبات Python القياسية
# ─────────────────────────────────────────────────────────────────────────────
import os
import json
import uuid
import hashlib
import threading
from datetime import datetime
from pathlib import Path
from io import BytesIO

# ─────────────────────────────────────────────────────────────────────────────
#  Flask
# ─────────────────────────────────────────────────────────────────────────────
from flask import (
    Flask, request, session, redirect,
    url_for, send_file, jsonify, Response
)

# ─────────────────────────────────────────────────────────────────────────────
#  g4f  (الذكاء الاصطناعي)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from g4f.client import Client as G4FClient
    G4F_OK = True
except ImportError:
    G4F_OK = False
    print("[!] g4f غير مثبّت  =>  pip install g4f")

# ─────────────────────────────────────────────────────────────────────────────
#  إعداد المسارات والتخزين
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data"
OUT_DIR    = BASE_DIR / "generated"
USERS_FILE = DATA_DIR / "users.json"
APPS_FILE  = DATA_DIR / "apps.json"

DATA_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
#  Flask App
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "OBG_ULTRA_SECRET_2025_XYZ_SECURE"

# تتبع المهام في الذاكرة
JOBS: dict = {}

# ─────────────────────────────────────────────────────────────────────────────
#  أدوات مساعدة
# ─────────────────────────────────────────────────────────────────────────────

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def get_users():  return load_json(USERS_FILE, {})
def save_users(u): save_json(USERS_FILE, u)
def get_apps():   return load_json(APPS_FILE, [])
def save_apps(a): save_json(APPS_FILE, a)

# ─────────────────────────────────────────────────────────────────────────────
#  HTML  ——  صفحة تسجيل الدخول / إنشاء الحساب
# ─────────────────────────────────────────────────────────────────────────────

LOGIN_HTML = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>OBG APPS – الدخول</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
<style>
/* ═══ reset ═══════════════════════════════════════════════════════════════ */
*{margin:0;padding:0;box-sizing:border-box}
/* ═══ variables ═══════════════════════════════════════════════════════════ */
:root{
  --p:#7c3aed;--pl:#a78bfa;--s:#2563eb;--a:#06b6d4;
  --g:#10b981;--r:#ef4444;
  --bg:#030712;--card:rgba(15,10,30,.82);
  --border:rgba(255,255,255,.09);--text:#f1f5f9;--muted:rgba(255,255,255,.5);
}
/* ═══ body & background ═══════════════════════════════════════════════════ */
body{
  font-family:'Cairo',sans-serif;background:var(--bg);
  min-height:100vh;display:flex;align-items:center;
  justify-content:center;overflow:hidden;color:var(--text);
}
.bg{position:fixed;inset:0;z-index:0}
.orb{position:absolute;border-radius:50%;filter:blur(90px);opacity:.28;animation:drift 14s ease-in-out infinite}
.o1{width:560px;height:560px;top:-160px;left:-120px;background:radial-gradient(circle,var(--p),transparent);animation-delay:0s}
.o2{width:420px;height:420px;bottom:-100px;right:-80px;background:radial-gradient(circle,var(--s),transparent);animation-delay:-5s}
.o3{width:300px;height:300px;top:45%;left:45%;background:radial-gradient(circle,var(--a),transparent);animation-delay:-9s}
@keyframes drift{0%,100%{transform:translate(0,0) scale(1)}33%{transform:translate(28px,-22px) scale(1.05)}66%{transform:translate(-18px,26px) scale(.97)}}
.grid{position:fixed;inset:0;z-index:0;opacity:.035;
  background-image:linear-gradient(rgba(255,255,255,1) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,1) 1px,transparent 1px);
  background-size:56px 56px}
/* ═══ card ════════════════════════════════════════════════════════════════ */
.wrap{position:relative;z-index:10;width:100%;max-width:468px;padding:16px;animation:su .7s cubic-bezier(.16,1,.3,1) both}
@keyframes su{from{opacity:0;transform:translateY(38px) scale(.96)}to{opacity:1;transform:none}}
.card{
  background:var(--card);backdrop-filter:blur(32px) saturate(180%);
  border:1px solid rgba(124,58,237,.22);border-radius:28px;padding:44px 40px;
  box-shadow:0 0 0 1px rgba(255,255,255,.04),0 32px 80px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.07)
}
/* ═══ logo ════════════════════════════════════════════════════════════════ */
.logo{text-align:center;margin-bottom:34px}
.logo-ico{
  width:72px;height:72px;margin:0 auto 14px;
  background:linear-gradient(135deg,var(--p),var(--s));
  border-radius:20px;display:flex;align-items:center;justify-content:center;
  font-size:2rem;box-shadow:0 0 40px rgba(124,58,237,.55);
  animation:glow 3s ease-in-out infinite
}
@keyframes glow{0%,100%{box-shadow:0 0 40px rgba(124,58,237,.55)}50%{box-shadow:0 0 64px rgba(124,58,237,.85),0 0 80px rgba(37,99,235,.4)}}
.logo-name{
  font-size:1.85rem;font-weight:900;letter-spacing:3px;
  background:linear-gradient(90deg,var(--pl),var(--a));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent
}
.logo-sub{color:var(--muted);font-size:.82rem;margin-top:4px}
/* ═══ tabs ════════════════════════════════════════════════════════════════ */
.tabs{display:flex;background:rgba(0,0,0,.3);border-radius:12px;padding:4px;margin-bottom:26px;gap:4px}
.tab{
  flex:1;padding:10px;text-align:center;border-radius:9px;cursor:pointer;
  font-size:.93rem;font-weight:600;color:var(--muted);transition:all .3s;
  font-family:'Cairo',sans-serif;border:none;background:transparent
}
.tab.on{background:linear-gradient(135deg,var(--p),var(--s));color:#fff;box-shadow:0 4px 16px rgba(124,58,237,.4)}
/* ═══ panels ══════════════════════════════════════════════════════════════ */
.panel{display:none}.panel.on{display:block;animation:fs .38s ease}
@keyframes fs{from{opacity:0;transform:translateX(10px)}to{opacity:1;transform:none}}
/* ═══ fields ══════════════════════════════════════════════════════════════ */
.fld{margin-bottom:16px}
.fld label{display:block;font-size:.85rem;font-weight:600;color:var(--muted);margin-bottom:7px}
.iw{position:relative}
.iw i{position:absolute;right:13px;top:50%;transform:translateY(-50%);color:var(--muted);font-size:.88rem;pointer-events:none}
.fld input{
  width:100%;padding:13px 40px 13px 14px;
  background:rgba(255,255,255,.055);border:1.5px solid var(--border);
  border-radius:12px;color:var(--text);font-size:.93rem;
  font-family:'Cairo',sans-serif;transition:all .28s;outline:none
}
.fld input:focus{border-color:var(--pl);background:rgba(124,58,237,.07);box-shadow:0 0 0 3px rgba(124,58,237,.14)}
.fld input::placeholder{color:var(--muted)}
/* ═══ button ══════════════════════════════════════════════════════════════ */
.btn{
  width:100%;padding:14px;
  background:linear-gradient(135deg,var(--p),var(--s));
  border:none;border-radius:14px;color:#fff;font-size:1rem;font-weight:700;
  font-family:'Cairo',sans-serif;cursor:pointer;margin-top:8px;
  position:relative;overflow:hidden;transition:transform .2s,box-shadow .3s;
  box-shadow:0 8px 30px rgba(124,58,237,.42)
}
.btn:hover{transform:translateY(-2px);box-shadow:0 12px 40px rgba(124,58,237,.58)}
.btn:active{transform:none}
.btn .sh{
  position:absolute;top:0;left:-100%;width:60%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.2),transparent);
  transform:skewX(-20deg);transition:left .6s
}
.btn:hover .sh{left:150%}
/* ═══ alerts ══════════════════════════════════════════════════════════════ */
.al{padding:11px 14px;border-radius:10px;font-size:.88rem;font-weight:600;margin-bottom:14px;display:none;animation:fi .3s ease}
@keyframes fi{from{opacity:0}to{opacity:1}}
.al.err{background:rgba(239,68,68,.14);border:1px solid rgba(239,68,68,.38);color:#fca5a5}
.al.ok{background:rgba(16,185,129,.14);border:1px solid rgba(16,185,129,.38);color:#6ee7b7}
/* ═══ spinner ══════════════════════════════════════════════════════════════ */
.sp{display:inline-block;width:17px;height:17px;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle;margin-left:7px}
@keyframes spin{to{transform:rotate(360deg)}}
/* ═══ particles ════════════════════════════════════════════════════════════ */
.pts{position:fixed;inset:0;z-index:1;pointer-events:none}
.pt{position:absolute;width:2px;height:2px;border-radius:50%;background:var(--pl);opacity:0;animation:fup linear infinite}
@keyframes fup{0%{opacity:0;transform:translateY(0) scale(0)}10%{opacity:.55;transform:scale(1)}90%{opacity:.25}100%{opacity:0;transform:translateY(-100vh) scale(.5)}}
@media(max-width:500px){.card{padding:32px 22px}}
</style>
</head>
<body>

<div class="bg">
  <div class="orb o1"></div><div class="orb o2"></div><div class="orb o3"></div>
</div>
<div class="grid"></div>
<div class="pts" id="pts"></div>

<div class="wrap">
 <div class="card">

  <!-- LOGO -->
  <div class="logo">
    <div class="logo-ico">⚡</div>
    <div class="logo-name">OBG APPS</div>
    <div class="logo-sub">مولّد التطبيقات بالذكاء الاصطناعي</div>
  </div>

  <!-- TABS -->
  <div class="tabs">
    <button class="tab on" id="t-login"    onclick="sw('login')">تسجيل الدخول</button>
    <button class="tab"    id="t-register" onclick="sw('register')">إنشاء حساب</button>
  </div>

  <!-- LOGIN PANEL -->
  <div class="panel on" id="p-login">
    <div class="al" id="al-login"></div>
    <div class="fld">
      <label>البريد الإلكتروني</label>
      <div class="iw"><i class="fas fa-envelope"></i>
        <input type="email" id="le" placeholder="example@mail.com">
      </div>
    </div>
    <div class="fld">
      <label>كلمة المرور</label>
      <div class="iw"><i class="fas fa-lock"></i>
        <input type="password" id="lp" placeholder="••••••••">
      </div>
    </div>
    <button class="btn" id="btn-login" onclick="doLogin()">
      <span class="sh"></span><i class="fas fa-sign-in-alt"></i> دخول
    </button>
  </div>

  <!-- REGISTER PANEL -->
  <div class="panel" id="p-register">
    <div class="al" id="al-reg"></div>
    <div class="fld">
      <label>الاسم الكامل</label>
      <div class="iw"><i class="fas fa-user"></i>
        <input type="text" id="rn" placeholder="اسمك الكامل">
      </div>
    </div>
    <div class="fld">
      <label>البريد الإلكتروني</label>
      <div class="iw"><i class="fas fa-envelope"></i>
        <input type="email" id="re" placeholder="example@mail.com">
      </div>
    </div>
    <div class="fld">
      <label>كلمة المرور</label>
      <div class="iw"><i class="fas fa-lock"></i>
        <input type="password" id="rp" placeholder="6 أحرف على الأقل">
      </div>
    </div>
    <button class="btn" id="btn-reg" onclick="doReg()">
      <span class="sh"></span><i class="fas fa-rocket"></i> إنشاء الحساب
    </button>
  </div>

 </div>
</div>

<script>
/* particles */
(function(){
  const c=document.getElementById('pts');
  for(let i=0;i<28;i++){
    const p=document.createElement('div');p.className='pt';
    p.style.cssText=`left:${Math.random()*100}%;top:${100+Math.random()*20}%;`+
      `animation-duration:${7+Math.random()*10}s;animation-delay:${Math.random()*12}s;`+
      `width:${1+Math.random()*3}px;height:${1+Math.random()*3}px;opacity:${.2+Math.random()*.4};`;
    c.appendChild(p);
  }
})();

function sw(tab){
  document.getElementById('t-login').classList.toggle('on', tab==='login');
  document.getElementById('t-register').classList.toggle('on', tab==='register');
  document.getElementById('p-login').classList.toggle('on', tab==='login');
  document.getElementById('p-register').classList.toggle('on', tab==='register');
}

function showAl(id,msg,type){
  const el=document.getElementById(id);
  el.textContent=msg;el.className='al '+type;el.style.display='block';
  setTimeout(()=>el.style.display='none',4500);
}

async function doLogin(){
  const e=document.getElementById('le').value.trim();
  const p=document.getElementById('lp').value.trim();
  if(!e||!p){showAl('al-login','يرجى ملء جميع الحقول','err');return;}
  const btn=document.getElementById('btn-login');
  btn.innerHTML='<span class="sh"></span><span class="sp"></span> جارٍ التحقق...';btn.disabled=true;
  const fd=new FormData();fd.append('email',e);fd.append('password',p);
  const r=await fetch('/login',{method:'POST',body:fd});
  const d=await r.json();
  if(d.ok){showAl('al-login','✅ مرحباً بك!','ok');setTimeout(()=>location.href=d.url,700);}
  else{showAl('al-login',d.msg,'err');btn.innerHTML='<span class="sh"></span><i class="fas fa-sign-in-alt"></i> دخول';btn.disabled=false;}
}

async function doReg(){
  const n=document.getElementById('rn').value.trim();
  const e=document.getElementById('re').value.trim();
  const p=document.getElementById('rp').value.trim();
  if(!n||!e||!p){showAl('al-reg','يرجى ملء جميع الحقول','err');return;}
  if(p.length<6){showAl('al-reg','كلمة المرور يجب أن تكون 6 أحرف على الأقل','err');return;}
  const btn=document.getElementById('btn-reg');
  btn.innerHTML='<span class="sh"></span><span class="sp"></span> جارٍ الإنشاء...';btn.disabled=true;
  const fd=new FormData();fd.append('name',n);fd.append('email',e);fd.append('password',p);
  const r=await fetch('/register',{method:'POST',body:fd});
  const d=await r.json();
  if(d.ok){showAl('al-reg','🎉 تم إنشاء الحساب!','ok');setTimeout(()=>location.href=d.url,700);}
  else{showAl('al-reg',d.msg,'err');btn.innerHTML='<span class="sh"></span><i class="fas fa-rocket"></i> إنشاء الحساب';btn.disabled=false;}
}

document.addEventListener('keydown',e=>{
  if(e.key!=='Enter')return;
  if(document.getElementById('p-login').classList.contains('on'))doLogin();else doReg();
});
</script>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
#  HTML  ——  لوحة التحكم الرئيسية
# ─────────────────────────────────────────────────────────────────────────────

def build_dashboard(name: str, apps: list) -> str:
    """بناء صفحة Dashboard ديناميكياً حسب بيانات المستخدم."""

    # بناء بطاقات التطبيقات السابقة
    cards_html = ""
    if apps:
        for a in reversed(apps):
            desc  = a.get("description", "")[:90] + ("…" if len(a.get("description","")) > 90 else "")
            fname = a.get("filename", "")
            lines = a.get("lines", 0)
            cards_html += f"""
        <div class="app-card">
          <div class="ac-icon">⚡</div>
          <div class="ac-desc">{desc}</div>
          <div class="ac-meta">
            <span><i class="fas fa-code" style="margin-left:4px"></i>{lines} سطر</span>
            <a href="/dl/{fname}" class="ac-dl"><i class="fas fa-download"></i> تحميل</a>
          </div>
        </div>"""
    else:
        cards_html = """
        <div class="empty">
          <i class="fas fa-rocket"></i>
          <p>لم تقم بإنشاء أي تطبيق بعد<br>ابدأ الآن من الأداة أعلاه!</p>
        </div>"""

    apps_count = len(apps)

    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>OBG APPS – لوحة التحكم</title>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
<style>
/* ═══ reset / vars ══════════════════════════════════════════════════════════ */
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --p:#7c3aed;--pl:#a78bfa;--s:#2563eb;--a:#06b6d4;
  --g:#10b981;--r:#ef4444;--o:#f59e0b;
  --bg:#030712;--card:rgba(255,255,255,.045);
  --border:rgba(255,255,255,.09);--text:#f1f5f9;--muted:rgba(255,255,255,.5);
}}
html{{scroll-behavior:smooth}}
body{{font-family:'Cairo',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}
/* ═══ bg scene ══════════════════════════════════════════════════════════════ */
.bg{{position:fixed;inset:0;z-index:0;pointer-events:none}}
.orb{{position:absolute;border-radius:50%;filter:blur(100px);opacity:.18;animation:drift 16s ease-in-out infinite}}
.o1{{width:600px;height:600px;top:-200px;right:-100px;background:radial-gradient(circle,var(--p),transparent)}}
.o2{{width:420px;height:420px;bottom:-100px;left:-100px;background:radial-gradient(circle,var(--s),transparent);animation-delay:-7s}}
@keyframes drift{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(40px,-30px)}}}}
/* ═══ nav ════════════════════════════════════════════════════════════════════ */
nav{{
  position:sticky;top:0;z-index:100;
  background:rgba(3,7,18,.88);backdrop-filter:blur(24px);
  border-bottom:1px solid var(--border);
  padding:0 24px;display:flex;align-items:center;justify-content:space-between;height:66px
}}
.nb{{display:flex;align-items:center;gap:12px}}
.nl{{
  width:40px;height:40px;background:linear-gradient(135deg,var(--p),var(--s));
  border-radius:12px;display:flex;align-items:center;justify-content:center;
  font-size:1.2rem;box-shadow:0 0 20px rgba(124,58,237,.4)
}}
.nn{{font-size:1.15rem;font-weight:900;letter-spacing:2px;background:linear-gradient(90deg,var(--pl),var(--a));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.nr{{display:flex;align-items:center;gap:16px}}
.wl{{color:var(--muted);font-size:.88rem}} .wl strong{{color:var(--pl)}}
.logout{{
  padding:7px 16px;border-radius:10px;background:rgba(239,68,68,.14);
  border:1px solid rgba(239,68,68,.3);color:#fca5a5;font-size:.82rem;font-weight:600;
  font-family:'Cairo',sans-serif;cursor:pointer;transition:all .2s;text-decoration:none
}}
.logout:hover{{background:rgba(239,68,68,.24)}}
/* ═══ layout ═════════════════════════════════════════════════════════════════ */
.con{{max-width:980px;margin:0 auto;padding:40px 20px;position:relative;z-index:1}}
/* ═══ hero ════════════════════════════════════════════════════════════════════ */
.hero{{text-align:center;margin-bottom:50px}}
.badge{{
  display:inline-flex;align-items:center;gap:8px;
  background:rgba(124,58,237,.14);border:1px solid rgba(124,58,237,.3);
  border-radius:999px;padding:6px 18px;font-size:.8rem;font-weight:600;
  color:var(--pl);margin-bottom:18px;animation:bp 3s ease-in-out infinite
}}
@keyframes bp{{0%,100%{{box-shadow:0 0 0 0 rgba(124,58,237,.3)}}50%{{box-shadow:0 0 0 8px rgba(124,58,237,0)}}}}
.hero h1{{font-size:clamp(1.8rem,5vw,3rem);font-weight:900;line-height:1.2;margin-bottom:14px}}
.gr{{background:linear-gradient(90deg,var(--pl),var(--a),var(--g));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-size:200%;animation:sg 4s linear infinite}}
@keyframes sg{{0%{{background-position:0%}}100%{{background-position:200%}}}}
.hero p{{color:var(--muted);font-size:1rem;max-width:490px;margin:0 auto}}
/* ═══ generator card ══════════════════════════════════════════════════════════ */
.gen{{
  background:rgba(15,10,30,.72);backdrop-filter:blur(24px);
  border:1px solid rgba(124,58,237,.2);border-radius:24px;padding:38px;
  box-shadow:0 0 0 1px rgba(255,255,255,.03),0 24px 64px rgba(0,0,0,.5);
  margin-bottom:44px
}}
.gh{{display:flex;align-items:center;gap:14px;margin-bottom:26px}}
.gi{{
  width:48px;height:48px;background:linear-gradient(135deg,var(--p),var(--s));
  border-radius:14px;display:flex;align-items:center;justify-content:center;
  font-size:1.4rem;box-shadow:0 0 24px rgba(124,58,237,.4)
}}
.gh h2{{font-size:1.25rem;font-weight:700}} .gh p{{color:var(--muted);font-size:.85rem}}
.tw{{position:relative;margin-bottom:18px}}
textarea{{
  width:100%;min-height:155px;resize:vertical;
  background:rgba(255,255,255,.04);border:1.5px solid var(--border);
  border-radius:16px;padding:17px;color:var(--text);font-family:'Cairo',sans-serif;
  font-size:.97rem;line-height:1.75;outline:none;transition:all .3s
}}
textarea:focus{{border-color:var(--pl);background:rgba(124,58,237,.055);box-shadow:0 0 0 3px rgba(124,58,237,.12)}}
textarea::placeholder{{color:var(--muted)}}
.cc{{position:absolute;bottom:11px;left:13px;font-size:.76rem;color:var(--muted)}}
.gf{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px}}
.tips{{display:flex;gap:7px;flex-wrap:wrap}}
.tip{{
  padding:5px 12px;border-radius:8px;background:rgba(255,255,255,.055);
  border:1px solid var(--border);font-size:.77rem;color:var(--muted);cursor:pointer;transition:all .2s
}}
.tip:hover{{background:rgba(124,58,237,.14);border-color:rgba(124,58,237,.4);color:var(--pl)}}
.btn-gen{{
  padding:13px 30px;background:linear-gradient(135deg,var(--p),var(--s));
  border:none;border-radius:14px;color:#fff;font-size:.97rem;font-weight:700;
  font-family:'Cairo',sans-serif;cursor:pointer;display:flex;align-items:center;gap:9px;
  transition:all .3s;position:relative;overflow:hidden;
  box-shadow:0 8px 28px rgba(124,58,237,.4);white-space:nowrap
}}
.btn-gen:hover{{transform:translateY(-2px);box-shadow:0 12px 36px rgba(124,58,237,.55)}}
.btn-gen:disabled{{opacity:.7;cursor:not-allowed;transform:none}}
.btn-gen .sh{{position:absolute;top:0;left:-100%;width:60%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.2),transparent);transform:skewX(-20deg);transition:left .6s}}
.btn-gen:hover .sh{{left:150%}}
/* ═══ progress overlay ════════════════════════════════════════════════════════ */
.ov{{
  position:fixed;inset:0;z-index:200;
  background:rgba(0,0,0,.78);backdrop-filter:blur(8px);
  display:none;align-items:center;justify-content:center;padding:20px
}}
.ov.on{{display:flex;animation:fi .3s ease}}
@keyframes fi{{from{{opacity:0}}to{{opacity:1}}}}
.pm{{
  background:rgba(15,10,30,.96);border:1px solid rgba(124,58,237,.3);
  border-radius:28px;padding:50px 42px;max-width:470px;width:100%;text-align:center;
  box-shadow:0 40px 80px rgba(0,0,0,.6);animation:pi .4s cubic-bezier(.16,1,.3,1)
}}
@keyframes pi{{from{{opacity:0;transform:scale(.88) translateY(20px)}}to{{opacity:1;transform:none}}}}
.brain{{
  width:90px;height:90px;margin:0 auto 22px;
  background:linear-gradient(135deg,var(--p),var(--s),var(--a));
  border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-size:2.6rem;box-shadow:0 0 60px rgba(124,58,237,.5);
  animation:bs 3s ease-in-out infinite
}}
@keyframes bs{{
  0%,100%{{transform:scale(1) rotate(0deg);box-shadow:0 0 60px rgba(124,58,237,.5)}}
  25%{{transform:scale(1.08) rotate(5deg)}}
  50%{{transform:scale(1.04) rotate(0deg);box-shadow:0 0 80px rgba(6,182,212,.6)}}
  75%{{transform:scale(1.08) rotate(-5deg)}}
}}
.pm h2{{font-size:1.45rem;font-weight:900;margin-bottom:7px}}
.pm .msg{{color:var(--muted);font-size:.93rem;margin-bottom:26px;min-height:26px}}
.pbw{{background:rgba(255,255,255,.07);border-radius:999px;height:8px;margin-bottom:10px;overflow:hidden}}
.pb{{height:100%;border-radius:999px;background:linear-gradient(90deg,var(--p),var(--a));width:0%;transition:width .5s ease;box-shadow:0 0 12px rgba(124,58,237,.6)}}
.pct{{font-size:.83rem;color:var(--pl);font-weight:700}}
/* ═══ download overlay ════════════════════════════════════════════════════════ */
.dl-ov{{
  position:fixed;inset:0;z-index:300;
  background:rgba(0,0,0,.82);backdrop-filter:blur(10px);
  display:none;align-items:center;justify-content:center;padding:20px
}}
.dl-ov.on{{display:flex;animation:fi .3s ease}}
.dm{{
  background:rgba(5,18,12,.97);border:1px solid rgba(16,185,129,.28);
  border-radius:28px;padding:50px 42px;max-width:480px;width:100%;text-align:center;
  box-shadow:0 40px 80px rgba(0,0,0,.7);animation:pi .5s cubic-bezier(.16,1,.3,1)
}}
.dl-ico{{
  width:86px;height:86px;margin:0 auto 20px;
  background:linear-gradient(135deg,#059669,#10b981);
  border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-size:2.4rem;box-shadow:0 0 50px rgba(16,185,129,.45);
  animation:bi .6s cubic-bezier(.16,1,.3,1)
}}
@keyframes bi{{0%{{transform:scale(0)}}60%{{transform:scale(1.18)}}100%{{transform:scale(1)}}}}
.dl-ico-file{{
  width:100px;height:120px;margin:0 auto 20px;position:relative;
  background:linear-gradient(135deg,#1e293b,#0f172a);
  border-radius:8px 16px 8px 8px;border:2px solid rgba(16,185,129,.4);
  display:flex;align-items:center;justify-content:center;flex-direction:column;
  box-shadow:0 0 40px rgba(16,185,129,.3),inset 0 1px 0 rgba(255,255,255,.1);
  animation:bi .6s cubic-bezier(.16,1,.3,1)
}}
.dl-ico-file::before{{
  content:'';position:absolute;top:-1px;right:-1px;
  width:22px;height:22px;
  background:linear-gradient(135deg,rgba(16,185,129,.5),rgba(5,150,105,.5));
  border-radius:0 16px 0 8px;border-bottom:2px solid rgba(16,185,129,.4);border-left:2px solid rgba(16,185,129,.4)
}}
.file-ext{{font-size:1rem;font-weight:900;color:#6ee7b7;letter-spacing:2px}}
.file-lines{{font-size:.7rem;color:var(--muted);margin-top:4px}}
.code-lines{{
  display:flex;flex-direction:column;gap:3px;margin-bottom:8px;width:70%;
  opacity:.5
}}
.code-line{{height:3px;border-radius:2px;background:var(--pl)}}
.dl-title{{font-size:1.4rem;font-weight:900;color:#6ee7b7;margin-bottom:8px}}
.dl-sub{{color:var(--muted);font-size:.88rem;margin-bottom:6px}}
.dl-stats{{
  display:flex;gap:16px;justify-content:center;margin-bottom:26px;margin-top:10px
}}
.stat{{
  background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);
  border-radius:10px;padding:8px 16px;text-align:center
}}
.stat-val{{font-size:1.1rem;font-weight:900;color:#6ee7b7}}
.stat-lbl{{font-size:.72rem;color:var(--muted)}}
.btn-dl{{
  display:inline-flex;align-items:center;gap:10px;
  padding:16px 40px;background:linear-gradient(135deg,#059669,#10b981);
  border:none;border-radius:14px;color:#fff;font-size:1rem;font-weight:700;
  font-family:'Cairo',sans-serif;cursor:pointer;text-decoration:none;
  box-shadow:0 8px 32px rgba(16,185,129,.4);transition:all .3s;
  animation:pdl 2.5s ease-in-out infinite
}}
@keyframes pdl{{0%,100%{{box-shadow:0 8px 32px rgba(16,185,129,.4)}}50%{{box-shadow:0 8px 48px rgba(16,185,129,.7),0 0 0 8px rgba(16,185,129,.1)}}}}
.btn-dl:hover{{transform:translateY(-3px) scale(1.02)}}
.btn-new{{
  margin-top:14px;display:inline-block;color:var(--muted);font-size:.86rem;
  cursor:pointer;text-decoration:underline;background:none;border:none;
  font-family:'Cairo',sans-serif
}}
.btn-new:hover{{color:var(--pl)}}
/* ═══ history section ════════════════════════════════════════════════════════ */
.sec-title{{display:flex;align-items:center;gap:12px;font-size:1.1rem;font-weight:700;margin-bottom:18px}}
.sec-title i{{color:var(--pl)}}
.apps-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(275px,1fr));gap:14px}}
.app-card{{
  background:var(--card);border:1px solid var(--border);
  border-radius:18px;padding:20px;transition:all .3s;position:relative;overflow:hidden
}}
.app-card:hover{{border-color:rgba(124,58,237,.35);background:rgba(124,58,237,.07);transform:translateY(-3px);box-shadow:0 12px 30px rgba(0,0,0,.3)}}
.app-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--p),var(--a));opacity:0;transition:opacity .3s}}
.app-card:hover::before{{opacity:1}}
.ac-icon{{width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,var(--p),var(--s));display:flex;align-items:center;justify-content:center;font-size:1.2rem;margin-bottom:12px;box-shadow:0 0 16px rgba(124,58,237,.3)}}
.ac-desc{{font-size:.88rem;color:var(--text);margin-bottom:12px;line-height:1.6;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.ac-meta{{display:flex;align-items:center;justify-content:space-between;font-size:.76rem;color:var(--muted)}}
.ac-dl{{display:inline-flex;align-items:center;gap:6px;padding:5px 13px;border-radius:8px;background:rgba(16,185,129,.14);border:1px solid rgba(16,185,129,.28);color:#6ee7b7;font-size:.78rem;font-weight:600;text-decoration:none;transition:all .2s}}
.ac-dl:hover{{background:rgba(16,185,129,.24)}}
.empty{{text-align:center;padding:48px 20px;color:var(--muted)}}
.empty i{{font-size:3rem;margin-bottom:14px;opacity:.4;display:block}}
/* ═══ spinner ════════════════════════════════════════════════════════════════ */
.sp{{display:inline-block;width:18px;height:18px;border:2.5px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
/* ═══ responsive ═════════════════════════════════════════════════════════════ */
@media(max-width:600px){{
  .gen{{padding:24px 18px}}
  .gf{{flex-direction:column;align-items:stretch}}
  .btn-gen{{justify-content:center}}
  nav{{padding:0 14px}}
  .wl{{display:none}}
}}
</style>
</head>
<body>

<div class="bg"><div class="orb o1"></div><div class="orb o2"></div></div>

<!-- NAV -->
<nav>
  <div class="nb">
    <div class="nl">⚡</div>
    <span class="nn">OBG APPS</span>
  </div>
  <div class="nr">
    <span class="wl">مرحباً، <strong>{name}</strong></span>
    <a href="/logout" class="logout"><i class="fas fa-sign-out-alt"></i> خروج</a>
  </div>
</nav>

<!-- MAIN -->
<div class="con">

  <!-- hero -->
  <div class="hero">
    <div class="badge"><i class="fas fa-bolt"></i> مدعوم بالذكاء الاصطناعي</div>
    <h1>صِف تطبيقك<br><span class="gr">ونحن نبنيه لك</span></h1>
    <p>اكتب وصفاً لفكرة تطبيقك أو لعبتك وسيقوم الذكاء الاصطناعي ببناء ملف HTML كامل جاهز للتحميل</p>
  </div>

  <!-- generator -->
  <div class="gen">
    <div class="gh">
      <div class="gi">🤖</div>
      <div><h2>مولّد التطبيقات الذكي</h2><p>صِف تطبيقك بالتفصيل للحصول على أفضل نتيجة</p></div>
    </div>
    <div class="tw">
      <textarea id="desc" placeholder="مثال: لعبة ثعبان Snake بتصميم نيون جميل مع مستويات صعوبة ونظام نقاط وأصوات تأثير..." oninput="cc(this)" maxlength="3000"></textarea>
      <span class="cc" id="ccc">0 / 3000</span>
    </div>
    <div class="gf">
      <div class="tips">
        <span class="tip" onclick="fx('game')">🎮 لعبة</span>
        <span class="tip" onclick="fx('notes')">📝 مذكرات</span>
        <span class="tip" onclick="fx('calc')">🔢 حاسبة</span>
        <span class="tip" onclick="fx('shop')">🛒 متجر</span>
        <span class="tip" onclick="fx('draw')">🎨 رسم</span>
        <span class="tip" onclick="fx('quiz')">❓ اختبار</span>
      </div>
      <button class="btn-gen" id="btn-gen" onclick="go()">
        <span class="sh"></span><i class="fas fa-wand-magic-sparkles"></i> ابنِ تطبيقي
      </button>
    </div>
  </div>

  <!-- history -->
  <div class="sec-title">
    <i class="fas fa-history"></i>
    تطبيقاتي السابقة
    <span style="font-size:.78rem;font-weight:400;color:var(--muted)">({apps_count})</span>
  </div>
  <div class="apps-grid" id="apps-grid">{cards_html}</div>

</div><!-- /con -->

<!-- PROGRESS OVERLAY -->
<div class="ov" id="ov-prog">
  <div class="pm">
    <div class="brain">🧠</div>
    <h2>الذكاء الاصطناعي يعمل</h2>
    <div class="msg" id="pmsg">⏳ جارٍ التحضير...</div>
    <div class="pbw"><div class="pb" id="pb"></div></div>
    <div class="pct" id="pct">0%</div>
  </div>
</div>

<!-- DOWNLOAD OVERLAY -->
<div class="dl-ov" id="ov-dl">
  <div class="dm">
    <div class="dl-ico-file">
      <div class="code-lines">
        <div class="code-line" style="width:100%"></div>
        <div class="code-line" style="width:75%"></div>
        <div class="code-line" style="width:90%"></div>
        <div class="code-line" style="width:60%"></div>
        <div class="code-line" style="width:85%"></div>
        <div class="code-line" style="width:45%"></div>
      </div>
      <div class="file-ext">HTML</div>
    </div>
    <div class="dl-title">🎉 تطبيقك جاهز!</div>
    <div class="dl-sub">تم بناء تطبيقك بنجاح بواسطة الذكاء الاصطناعي</div>
    <div class="dl-stats">
      <div class="stat"><div class="stat-val" id="st-lines">0</div><div class="stat-lbl">سطر كود</div></div>
      <div class="stat"><div class="stat-val" id="st-kb">0</div><div class="stat-lbl">كيلوبايت</div></div>
      <div class="stat"><div class="stat-val">HTML</div><div class="stat-lbl">الصيغة</div></div>
    </div>
    <a id="dl-btn" href="#" class="btn-dl"><i class="fas fa-download"></i> تحميل التطبيق</a>
    <br>
    <button class="btn-new" onclick="location.reload()"><i class="fas fa-plus"></i> إنشاء تطبيق جديد</button>
  </div>
</div>

<script>
const EX = {{
  game:  'لعبة ثعبان Snake كلاسيكية بتصميم نيون مضيء على خلفية سوداء، مع نظام نقاط متعددة المستويات وأصوات تأثير عند الأكل والاصطدام وشاشة أعلى النتائج',
  notes: 'تطبيق مذكرات يومية أنيق مع إضافة وتعديل وحذف الملاحظات، تصنيف حسب الألوان، بحث سريع، وحفظ تلقائي في المتصفح',
  calc:  'حاسبة علمية متقدمة بتصميم زجاجي شفاف تدعم العمليات الأساسية والمتقدمة مع تاريخ العمليات وتأثيرات عند الضغط',
  shop:  'واجهة متجر إلكتروني لبيع الملابس مع عرض المنتجات بشبكة جميلة وسلة تسوق وفلترة حسب الفئة والسعر',
  draw:  'لوحة رسم رقمي كاملة مع فرشاة وقلم وممحاة واختيار الألوان وتعديل الحجم والتراجع وتحميل اللوحة كصورة',
  quiz:  'تطبيق اختبار معلومات عامة بـ 20 سؤال متعدد الخيارات مع مؤقت، نظام نقاط، شرح الإجابات، وشاشة نتيجة احترافية',
}};

function fx(k){{
  const ta=document.getElementById('desc');
  ta.value=EX[k]||'';cc(ta);ta.focus();
}}
function cc(el){{ document.getElementById('ccc').textContent=el.value.length+' / 3000'; }}

let poll;
async function go(){{
  const desc=document.getElementById('desc').value.trim();
  if(!desc){{alert('يرجى كتابة وصف التطبيق أولاً');return;}}
  if(desc.length<10){{alert('الوصف قصير جداً، يرجى التفصيل أكثر');return;}}
  document.getElementById('ov-prog').classList.add('on');
  const btn=document.getElementById('btn-gen');
  btn.innerHTML='<span class="sh"></span><span class="sp"></span> جارٍ الإنشاء...';
  btn.disabled=true;
  const fd=new FormData();fd.append('desc',desc);
  const r=await fetch('/gen',{{method:'POST',body:fd}});
  const d=await r.json();
  if(!d.ok){{
    document.getElementById('ov-prog').classList.remove('on');
    alert(d.msg);
    btn.innerHTML='<span class="sh"></span><i class="fas fa-wand-magic-sparkles"></i> ابنِ تطبيقي';
    btn.disabled=false;
    return;
  }}
  pollJob(d.jid);
}}

function pollJob(jid){{
  poll=setInterval(async()=>{{
    const r=await fetch('/job/'+jid);
    const d=await r.json();
    const pct=d.progress||0;
    document.getElementById('pb').style.width=pct+'%';
    document.getElementById('pct').textContent=pct+'%';
    document.getElementById('pmsg').textContent=d.msg||'';
    if(d.status==='done'){{
      clearInterval(poll);
      document.getElementById('ov-prog').classList.remove('on');
      document.getElementById('dl-btn').href='/dl/'+d.filename;
      document.getElementById('st-lines').textContent=d.lines||'—';
      document.getElementById('st-kb').textContent=d.kb||'—';
      document.getElementById('ov-dl').classList.add('on');
    }} else if(d.status==='error'){{
      clearInterval(poll);
      document.getElementById('ov-prog').classList.remove('on');
      alert('حدث خطأ: '+d.msg);
      const btn=document.getElementById('btn-gen');
      btn.innerHTML='<span class="sh"></span><i class="fas fa-wand-magic-sparkles"></i> ابنِ تطبيقي';
      btn.disabled=false;
    }}
  }},1200);
}}
</script>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
#  prompt للذكاء الاصطناعي
# ─────────────────────────────────────────────────────────────────────────────

AI_SYSTEM = """أنت مطور ويب خبير محترف. مهمتك إنشاء ملفات HTML كاملة وضخمة تعمل standalone.

القواعد الصارمة:
1. أخرج كود HTML فقط — ابدأ بـ <!DOCTYPE html> وأنهِ بـ </html>
2. لا تكتب أي شرح أو نص خارج الكود إطلاقاً
3. الكود يجب أن يكون طويلاً جداً (لا يقل عن 900 سطر)
4. ضمّن كل CSS و JavaScript داخل الملف
5. التطبيق يجب أن يعمل بالكامل بدون خادم أو مكتبات خارجية
6. التصميم عصري واحترافي جداً مع انيميشنات وخطوط Google
7. المحتوى والواجهة بالعربية الفصحى
8. اكتب تعليقات كود طبيعية كما يكتبها مبرمج بشري حقيقي
9. أضف شاشة ترحيب، ميزات كاملة، وشاشة نهاية/نتيجة إن ناسب
10. استخدم localStorage للحفظ حيثما كان مفيداً
11. أضف responsive design يعمل على الموبايل والحاسوب
12. الكود يبدو حقيقياً 100% وكأنه كُتب بيد إنسان متخصص"""


def ai_generate(job_id: str, description: str, email: str):
    """يعمل في خيط منفصل — يستدعي g4f ويكتب ملف HTML."""
    try:
        JOBS[job_id].update(status="running", progress=8, msg="🤖 الذكاء الاصطناعي يحلل فكرتك...")

        prompt = f"""أنشئ تطبيق HTML كامل ومفصّل للفكرة التالية:

{description}

المطلوب:
- ملف HTML واحد يعمل standalone (بدون خادم)
- تصميم عربي عصري جميل جداً مع انيميشنات
- كود طويل جداً ومفصّل (900+ سطر)
- جميع الميزات مكتملة وتعمل فعلياً
- ابدأ مباشرة بـ <!DOCTYPE html> بدون أي مقدمة"""

        if not G4F_OK:
            raise RuntimeError("g4f غير مثبّت — نفّذ: pip install g4f")

        JOBS[job_id].update(progress=20, msg="🧠 الذكاء الاصطناعي يصمم الهيكل...")

        client = G4FClient()

        JOBS[job_id].update(progress=35, msg="⌨️  الذكاء الاصطناعي يكتب الكود...")

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": AI_SYSTEM},
                {"role": "user",   "content": prompt},
            ],
        )

        JOBS[job_id].update(progress=78, msg="✨ تنظيف الكود النهائي...")

        raw = response.choices[0].message.content.strip()

        # إزالة أسوار markdown إن وُجدت
        for fence in ("```html", "```"):
            raw = raw.replace(fence, "")
        raw = raw.strip()

        # التحقق من أن المخرج HTML حقيقي
        if "<!DOCTYPE" not in raw and "<html" not in raw:
            raise RuntimeError("لم يُرجع الذكاء الاصطناعي كود HTML صالح")

        JOBS[job_id].update(progress=90, msg="💾 حفظ الملف...")

        fname     = f"obg_{job_id[:10]}.html"
        fpath     = OUT_DIR / fname
        fpath.write_text(raw, encoding="utf-8")

        lines = raw.count("\n")
        kb    = round(len(raw.encode()) / 1024, 1)

        # حفظ سجل التطبيق
        apps_list = get_apps()
        apps_list.append({
            "id":          job_id,
            "email":       email,
            "description": description,
            "filename":    fname,
            "created_at":  datetime.now().isoformat(),
            "lines":       lines,
            "kb":          kb,
        })
        save_apps(apps_list)

        JOBS[job_id].update(status="done", progress=100,
                            msg="✅ تطبيقك جاهز!", filename=fname,
                            lines=lines, kb=kb)

    except Exception as exc:
        JOBS[job_id].update(status="error", msg=f"❌ {exc}")


# ─────────────────────────────────────────────────────────────────────────────
#  Flask Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("dashboard") if "email" in session else url_for("login_page"))


# ── تسجيل الدخول ─────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        return Response(LOGIN_HTML, mimetype="text/html")

    email = request.form.get("email", "").strip().lower()
    pw    = request.form.get("password", "").strip()
    users = get_users()

    if email in users and users[email]["password"] == hash_pw(pw):
        session["email"] = email
        session["name"]  = users[email].get("name", email)
        return jsonify(ok=True, url=url_for("dashboard"))

    return jsonify(ok=False, msg="البريد الإلكتروني أو كلمة المرور غير صحيحة")


# ── إنشاء حساب ────────────────────────────────────────────────────────────────
@app.route("/register", methods=["POST"])
def register():
    name  = request.form.get("name",  "").strip()
    email = request.form.get("email", "").strip().lower()
    pw    = request.form.get("password", "").strip()

    if not all([name, email, pw]):
        return jsonify(ok=False, msg="جميع الحقول مطلوبة")
    if len(pw) < 6:
        return jsonify(ok=False, msg="كلمة المرور يجب أن تكون 6 أحرف على الأقل")

    users = get_users()
    if email in users:
        return jsonify(ok=False, msg="هذا البريد الإلكتروني مسجّل مسبقاً")

    users[email] = {
        "name":       name,
        "password":   hash_pw(pw),
        "created_at": datetime.now().isoformat(),
    }
    save_users(users)
    session["email"] = email
    session["name"]  = name
    return jsonify(ok=True, url=url_for("dashboard"))


# ── تسجيل الخروج ──────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# ── لوحة التحكم ───────────────────────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect(url_for("login_page"))
    user_apps = [a for a in get_apps() if a["email"] == session["email"]]
    html = build_dashboard(session.get("name", ""), user_apps)
    return Response(html, mimetype="text/html")


# ── توليد التطبيق ─────────────────────────────────────────────────────────────
@app.route("/gen", methods=["POST"])
def generate():
    if "email" not in session:
        return jsonify(ok=False, msg="يجب تسجيل الدخول أولاً")

    desc = request.form.get("desc", "").strip()
    if not desc:
        return jsonify(ok=False, msg="يرجى إدخال وصف التطبيق")
    if len(desc) < 10:
        return jsonify(ok=False, msg="الوصف قصير جداً")

    jid = str(uuid.uuid4())
    JOBS[jid] = dict(status="queued", progress=0, msg="⏳ في الطابور...",
                     filename=None, lines=0, kb=0)

    t = threading.Thread(target=ai_generate, args=(jid, desc, session["email"]), daemon=True)
    t.start()

    return jsonify(ok=True, jid=jid)


# ── حالة المهمة ───────────────────────────────────────────────────────────────
@app.route("/job/<jid>")
def job_status(jid: str):
    job = JOBS.get(jid, {"status": "not_found"})
    return jsonify(job)


# ── تحميل الملف ───────────────────────────────────────────────────────────────
@app.route("/dl/<fname>")
def download(fname: str):
    if "email" not in session:
        return redirect(url_for("login_page"))
    # حماية من path traversal
    if not all(c.isalnum() or c in "_.-" for c in fname):
        return "اسم ملف غير صالح", 400
    fpath = OUT_DIR / fname
    if not fpath.exists():
        return "الملف غير موجود", 404
    return send_file(fpath, as_attachment=True,
                     download_name=fname, mimetype="text/html")


# ─────────────────────────────────────────────────────────────────────────────
#  نقطة الدخول
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║              OBG APPS  -  AI App Generator               ║
║      مولّد التطبيقات المدعوم بالذكاء الاصطناعي          ║
╠══════════════════════════════════════════════════════════╣
║  تأكد من تثبيت المكتبات:  pip install flask g4f          ║
║  ثم افتح المتصفح على:     http://localhost:5000          ║
╚══════════════════════════════════════════════════════════╝
""")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
