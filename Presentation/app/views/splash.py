"""Two-page full-screen intro, injected once per browser page load.

Page 1: SUB MAG 3D hero.  Page 2: "Everything in one place" cards, reached by an explode-and-assemble morph.
Scroll / swipe / double tap / arrow keys move between pages; going past page 2 lifts the intro away.
"""
import json

import streamlit as st

FEATURES = [
    ("Purchases", "Record what you bought and issue its license key in one step."),
    ("Licenses", "Search every license by key, product, vendor or status."),
    ("Allocate", "Assign seats to people and devices, never beyond what you bought."),
    ("Reclaim", "Take seats back from leavers and put them to work again."),
    ("Expiry monitor", "See what lapses in the next 30, 60 and 90 days."),
    ("Renewals", "Extend a license and log the cost, atomically."),
    ("Compliance", "Catch over-allocated, expired and idle licenses."),
    ("Cost analysis", "Spend by vendor and department, plus idle seat value."),
    ("Reports", "Six ready reports, one click to CSV."),
]

CARDS_HTML = "".join(
    f"<div class='c'><div class='n'>{i:02d}</div><h4>{t}</h4><p>{d}</p></div>"
    for i, (t, d) in enumerate(FEATURES, 1))

SPLASH = r"""
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; overflow: hidden; background: #0b0b0b; font-family: 'Inter', sans-serif; }
  #wrap { position: relative; width: 100%; height: 100vh; overflow: hidden; background-color: #0b0b0b; }
  .glow { position: absolute; inset: 0; background: radial-gradient(ellipse at 70% 40%, #2a0a0e 0%, rgba(11,11,11,0) 62%); }
  canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }

  .overlay { position: absolute; left: 6%; top: 46%; transform: translateY(-50%); pointer-events: none; color: #f5ecd7; will-change: transform, opacity; }
  .eyebrow { font-size: 13px; letter-spacing: .34em; text-transform: uppercase; color: #e63946; opacity: 0; animation: rise .9s .1s forwards; }
  h1 { margin: 10px 0 6px; font-family: 'Archivo Black', Impact, sans-serif; font-weight: 400; line-height: .84; font-size: clamp(64px, 13.5vw, 190px); letter-spacing: -.02em; }
  h1 span { display: block; opacity: 0; transform: translateY(60px) rotateX(-40deg); animation: pop .9s cubic-bezier(.2,.8,.2,1) forwards; }
  h1 span:nth-child(1) { animation-delay: .25s; }
  h1 span:nth-child(2) { color: #e63946; animation-delay: .45s; }
  .tag { max-width: 440px; font-size: clamp(14px, 1.5vw, 19px); line-height: 1.5; opacity: 0; animation: rise .9s .8s forwards; }
  .chips { margin-top: 22px; display: flex; gap: 10px; flex-wrap: wrap; opacity: 0; animation: rise .9s 1.05s forwards; }
  .chips b { font-weight: 600; font-size: 12px; letter-spacing: .14em; text-transform: uppercase; padding: 7px 14px; border: 1px solid #f5ecd7; border-radius: 99px; }
  .chips b:first-child { background: #e63946; border-color: #e63946; color: #0b0b0b; }

  .ticker { position: absolute; left: -2%; right: -2%; bottom: 26px; transform: rotate(-2deg); background: #e63946; color: #0b0b0b; overflow: hidden; white-space: nowrap; border-top: 3px solid #0b0b0b; border-bottom: 3px solid #0b0b0b; }
  .ticker div { display: inline-block; padding: 9px 0; font-family: 'Archivo Black', Impact, sans-serif; font-size: 18px; letter-spacing: .08em; animation: scroll 22s linear infinite; }
  .ticker i { font-style: normal; color: #f5ecd7; margin: 0 18px; }

  .s2 { position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: center; align-items: center; pointer-events: none; padding: 0 5vw; }
  .s2 .in { width: min(1180px, 100%); }
  .s2 h2 { margin: 0 0 4px; font-family: 'Archivo Black', Impact, sans-serif; font-weight: 400; font-size: clamp(30px, 4.4vw, 52px); letter-spacing: -.01em; color: #141414; will-change: transform, opacity; opacity: 0; }
  .s2 h2 em { color: #c8102e; font-style: normal; }
  .s2 .sub { margin: 0 0 clamp(12px, 2.4vh, 22px); color: #4a4235; font-size: clamp(13px, 1.3vw, 16px); will-change: transform, opacity; opacity: 0; }
  .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; perspective: 1000px; }
  .c { position: relative; background: #0b0b0b; color: #f5ecd7; border-radius: 6px; padding: clamp(10px, 1.8vh, 18px) 18px clamp(14px, 2.2vh, 22px); overflow: hidden; opacity: 0; will-change: transform, opacity; }
  .c::after { content: ''; position: absolute; left: 0; bottom: 0; height: 4px; width: 28%; background: #e63946; }
  .c .n { font-family: 'Archivo Black', Impact, sans-serif; font-size: clamp(24px, 3.6vh, 36px); color: #e63946; line-height: 1; }
  .c h4 { margin: clamp(6px, 1.2vh, 12px) 0 4px; font-size: clamp(15px, 2.1vh, 19px); }
  .c p { margin: 0; font-size: clamp(12px, 1.7vh, 14px); line-height: 1.45; color: #d9cfb8; }
  @media (max-width: 900px) { .grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
  @media (max-width: 620px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; } .c { padding: 10px 12px 14px; } .c p { display: none; } }

  .enter { position: absolute; left: 50%; bottom: 96px; transform: translateX(-50%); z-index: 5; pointer-events: none; white-space: nowrap;
           font-weight: 600; font-size: 13px; letter-spacing: .3em; text-transform: uppercase; color: #f5ecd7; padding: 12px 22px;
           border: 1px solid rgba(245,236,215,.55); border-radius: 99px; background: rgba(11,11,11,.55);
           opacity: 0; animation: pillin .9s 1.5s forwards; transition: bottom .6s, color .4s, border-color .4s, background .4s; }
  .enter::before { content: ''; display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #e63946; margin-right: 12px; animation: blink 1.4s infinite; }
  .enter.s2on { bottom: 28px; color: #141414; border-color: rgba(20,20,20,.45); background: rgba(245,236,215,.7); }
  .dots { position: absolute; right: 22px; top: 50%; transform: translateY(-50%); z-index: 5; display: flex; flex-direction: column; gap: 12px; pointer-events: none; }
  .dots i { width: 9px; height: 9px; border-radius: 50%; background: rgba(150,150,150,.5); transition: background .4s, transform .4s; }
  .dots i.on { background: #e63946; transform: scale(1.5); }
  @keyframes pop { to { opacity: 1; transform: none; } }
  @keyframes rise { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: none; } }
  @keyframes pillin { from { opacity: 0; transform: translateX(-50%) translateY(18px); } to { opacity: 1; transform: translateX(-50%); } }
  @keyframes scroll { to { transform: translateX(-50%); } }
  @keyframes blink { 50% { opacity: .25; } }
</style>
<div id="wrap">
  <div class="glow" id="glow"></div>
  <canvas id="c"></canvas>
  <div class="overlay" id="hero">
    <div class="eyebrow">License &amp; subscription management</div>
    <h1><span>SUB</span><span>MAG</span></h1>
    <p class="tag">Every license. Every seat. Every renewal. One place, always under control.</p>
    <div class="chips"><b>Track</b><b>Allocate</b><b>Renew</b><b>Comply</b></div>
  </div>
  <div class="ticker" id="ticker"><div id="tk"></div></div>
  <div class="s2"><div class="in">
    <h2 id="s2h">Everything in <em>one place</em></h2>
    <p class="sub" id="s2s">Scroll or swipe up to enter the app.</p>
    <div class="grid" id="grid">__CARDS__</div>
  </div></div>
  <div class="dots"><i class="on" id="d0"></i><i id="d1"></i></div>
  <div class="enter" id="pill">Scroll or double tap</div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
  var words = ['LICENSES', 'SUBSCRIPTIONS', 'RENEWALS', 'ALLOCATIONS', 'COMPLIANCE', 'EXPIRY WATCH', 'COST CONTROL'];
  var seq = words.map(function (w) { return w + '<i>&#9679;</i>'; }).join('');
  document.getElementById('tk').innerHTML = seq + seq + seq + seq;

  function clamp01(x) { return Math.max(0, Math.min(1, x)); }
  function sstep(a, b, x) { var t = clamp01((x - a) / (b - a)); return t * t * (3 - 2 * t); }

  var scene = 0, target = 0, p = 0, lockUntil = 0, interacted = false, exited = false;
  var hero = document.getElementById('hero'), ticker = document.getElementById('ticker'), pill = document.getElementById('pill');
  var wrapEl = document.getElementById('wrap'), glow = document.getElementById('glow');
  var h2 = document.getElementById('s2h'), sub = document.getElementById('s2s');
  var cardEls = Array.prototype.slice.call(document.querySelectorAll('.c'));
  var offs = [];

  function measureCards() {
    var grid = document.getElementById('grid');
    var gw = grid.offsetWidth, gh = grid.offsetHeight;
    offs = cardEls.map(function (el) {
      return { dx: gw / 2 - (el.offsetLeft + el.offsetWidth / 2), dy: gh / 2 - (el.offsetTop + el.offsetHeight / 2) };
    });
  }

  function updateUI() {
    document.getElementById('d0').className = scene === 0 ? 'on' : '';
    document.getElementById('d1').className = scene === 1 ? 'on' : '';
    pill.textContent = scene === 0 ? 'Scroll or double tap' : 'Scroll or swipe up to enter';
    pill.className = 'enter' + (scene === 1 ? ' s2on' : '');
  }

  function exitIntro() {
    if (exited) return; exited = true;
    try {
      var w = parent.document.getElementById('submag-splash');
      if (!w) return;
      w.style.transform = 'translateY(-100%)';
      w.style.opacity = '0';
      setTimeout(function () { w.remove(); }, 1000);
    } catch (e) {}
  }

  function nav(dir) {
    var now = performance.now();
    if (now < lockUntil || exited) return;
    lockUntil = now + 1100;
    interacted = true;
    if (dir > 0) {
      if (scene === 0) { scene = 1; target = 1; } else { exitIntro(); }
    } else if (scene === 1) { scene = 0; target = 0; }
    updateUI();
  }

  window.addEventListener('wheel', function (e) { if (Math.abs(e.deltaY) > 8) nav(e.deltaY > 0 ? 1 : -1); }, { passive: true });
  window.addEventListener('dblclick', function () { nav(1); });
  var startY = 0, lastTap = 0;
  window.addEventListener('touchstart', function (e) { startY = e.touches[0].clientY; }, { passive: true });
  window.addEventListener('touchend', function (e) {
    var dy = startY - e.changedTouches[0].clientY;
    if (Math.abs(dy) > 45) { nav(dy > 0 ? 1 : -1); return; }
    var now = Date.now();
    if (now - lastTap < 350) nav(1);
    lastTap = now;
  });
  window.addEventListener('keydown', function (e) {
    if (['Enter', 'ArrowDown', 'PageDown', ' '].indexOf(e.key) > -1) { e.preventDefault(); nav(1); }
    else if (['ArrowUp', 'PageUp'].indexOf(e.key) > -1) { e.preventDefault(); nav(-1); }
    else if (e.key === 'Escape') exitIntro();
  });
  setTimeout(function () { if (!interacted && scene === 0) nav(1); }, 6500);

  try {
    var canvas = document.getElementById('c');
    var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    var scn = new THREE.Scene();
    scn.fog = new THREE.FogExp2(0x0b0b0b, 0.04);
    var camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    camera.position.set(0, 0, 10);

    scn.add(new THREE.AmbientLight(0xffffff, 0.55));
    var key = new THREE.DirectionalLight(0xf5ecd7, 1.15); key.position.set(4, 5, 6); scn.add(key);
    var redLight = new THREE.PointLight(0xe63946, 2.4, 40); redLight.position.set(-5, -3, 5); scn.add(redLight);
    var rim = new THREE.PointLight(0xf5ecd7, 1.2, 30); rim.position.set(6, 3, -4); scn.add(rim);

    var group = new THREE.Group(); scn.add(group);

    var knot = new THREE.Mesh(new THREE.TorusKnotGeometry(1.25, 0.38, 240, 32, 2, 3),
      new THREE.MeshStandardMaterial({ color: 0xd62828, metalness: 0.65, roughness: 0.22 }));
    group.add(knot);

    var icoMat = new THREE.MeshBasicMaterial({ color: 0xf5ecd7, wireframe: true, transparent: true, opacity: 0.16 });
    var ico = new THREE.Mesh(new THREE.IcosahedronGeometry(2.75, 1), icoMat); group.add(ico);

    var ringMat = new THREE.MeshBasicMaterial({ color: 0xe63946, transparent: true });
    var ring = new THREE.Mesh(new THREE.TorusGeometry(3.6, 0.018, 8, 160), ringMat);
    ring.rotation.x = Math.PI / 2.4; group.add(ring);

    var shockMat = new THREE.MeshBasicMaterial({ color: 0xe63946, transparent: true, opacity: 0, side: THREE.DoubleSide });
    var shock = new THREE.Mesh(new THREE.RingGeometry(0.92, 1, 96), shockMat); group.add(shock);

    var cream = new THREE.MeshStandardMaterial({ color: 0xf5ecd7, metalness: 0.1, roughness: 0.5 });
    var black = new THREE.MeshStandardMaterial({ color: 0x141414, metalness: 0.35, roughness: 0.4 });
    var redM  = new THREE.MeshStandardMaterial({ color: 0xe63946, metalness: 0.3, roughness: 0.35 });
    var cardGeo = new THREE.BoxGeometry(1.5, 0.95, 0.06), stripeGeo = new THREE.BoxGeometry(1.5, 0.17, 0.07), chipGeo = new THREE.BoxGeometry(0.3, 0.22, 0.07);
    var cards = [];
    for (var i = 0; i < 7; i++) {
      var g = new THREE.Group(), dark = i % 2 === 1;
      g.add(new THREE.Mesh(cardGeo, dark ? black : cream));
      var s = new THREE.Mesh(stripeGeo, dark ? cream : redM); s.position.set(0, 0.26, 0.002); g.add(s);
      var ch = new THREE.Mesh(chipGeo, dark ? redM : black); ch.position.set(-0.45, -0.18, 0.002); g.add(ch);
      g.userData = { a: (i / 7) * Math.PI * 2, r: 3.5 + (i % 3) * 0.32, s: 0.28 + i * 0.018, y: ((i % 3) - 1) * 0.95 };
      group.add(g); cards.push(g);
    }

    var shardMats = [redM, redM, black, black, cream].map(function (m) { var c = m.clone(); c.transparent = true; return c; });
    var shardGeos = [new THREE.TetrahedronGeometry(0.2), new THREE.BoxGeometry(0.2, 0.2, 0.2), new THREE.OctahedronGeometry(0.18)];
    var shards = [];
    for (var j = 0; j < 130; j++) {
      var m = new THREE.Mesh(shardGeos[j % 3], shardMats[j % 5]);
      var dir = new THREE.Vector3(Math.random() - .5, Math.random() - .5, (Math.random() - .5) * 0.6).normalize();
      m.userData = { dir: dir, sp: 2.5 + Math.random() * 7, base: 0.6 + Math.random() * 1.6, ph: Math.random() * 6.28,
                     rx: Math.random() * 2 + .5, ry: Math.random() * 2 + .5 };
      m.scale.setScalar(0); group.add(m); shards.push(m);
    }

    var cubes = [];
    for (var k = 0; k < 14; k++) {
      var cb = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.22, 0.22), k % 3 === 0 ? redM : (k % 3 === 1 ? cream : black));
      cb.position.set((Math.random() - .5) * 13, (Math.random() - .5) * 8, (Math.random() - .5) * 8 - 2);
      cb.userData = { v: Math.random() * .02 + .005, ph: Math.random() * 6 };
      scn.add(cb); cubes.push(cb);
    }

    var h2x = 0, h2y = 0, h2s = 1, edge = { w: 7, h: 5 };
    function makeCard(dark) {
      var g = new THREE.Group();
      g.add(new THREE.Mesh(cardGeo, dark ? black : cream));
      var s = new THREE.Mesh(stripeGeo, dark ? cream : redM); s.position.set(0, 0.26, 0.002); g.add(s);
      var ch = new THREE.Mesh(chipGeo, dark ? redM : black); ch.position.set(-0.45, -0.18, 0.002); g.add(ch);
      return g;
    }
    function backOut(t) { var c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); }

    var hero2 = new THREE.Group(); scn.add(hero2);
    var knot2 = new THREE.Mesh(new THREE.TorusKnotGeometry(1.0, 0.3, 200, 28, 2, 3),
      new THREE.MeshStandardMaterial({ color: 0xd62828, metalness: 0.65, roughness: 0.22 }));
    var ico2 = new THREE.Mesh(new THREE.IcosahedronGeometry(2.1, 1),
      new THREE.MeshBasicMaterial({ color: 0x141414, wireframe: true, transparent: true, opacity: 0.22 }));
    var ring2 = new THREE.Mesh(new THREE.TorusGeometry(2.7, 0.016, 8, 140), new THREE.MeshBasicMaterial({ color: 0xe63946 }));
    ring2.rotation.x = Math.PI / 2.4;
    hero2.add(knot2, ico2, ring2);
    var cards2 = [];
    for (var u = 0; u < 5; u++) {
      var cg = makeCard(u % 2 === 1);
      cg.userData = { a: (u / 5) * Math.PI * 2, r: 2.9 + (u % 2) * 0.3, s: 0.3 + u * 0.02, y: ((u % 3) - 1) * 0.7 };
      hero2.add(cg); cards2.push(cg);
    }
    var metalDark = new THREE.MeshStandardMaterial({ color: 0x141414, metalness: 0.6, roughness: 0.3 });
    var metalRed = new THREE.MeshStandardMaterial({ color: 0xc8102e, metalness: 0.55, roughness: 0.25 });
    var sat1 = new THREE.Mesh(new THREE.DodecahedronGeometry(0.95), metalDark); scn.add(sat1);
    var sat2 = new THREE.Mesh(new THREE.TorusGeometry(0.7, 0.26, 24, 64), metalRed); scn.add(sat2);
    var sat3 = new THREE.Mesh(new THREE.OctahedronGeometry(0.8), metalRed); scn.add(sat3);
    var sat4 = new THREE.Mesh(new THREE.IcosahedronGeometry(0.6, 0), metalDark); scn.add(sat4);
    var deco = [hero2, sat1, sat2, sat3, sat4];
    deco.forEach(function (o) { o.visible = false; o.scale.setScalar(0); });

    var N = 600, pos = new Float32Array(N * 3);
    for (var n = 0; n < N; n++) { pos[n*3] = (Math.random()-.5)*26; pos[n*3+1] = (Math.random()-.5)*16; pos[n*3+2] = (Math.random()-.5)*16 - 3; }
    var pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    var ptsMat = new THREE.PointsMaterial({ color: 0xf5ecd7, size: 0.035, transparent: true, opacity: 0.7 });
    var pts = new THREE.Points(pg, ptsMat); scn.add(pts);

    var bgA = new THREE.Color(0x0b0b0b), bgB = new THREE.Color(0xf5ecd7), ptsA = new THREE.Color(0xf5ecd7), ptsB = new THREE.Color(0x141414);
    var tmp = new THREE.Color();
    var wide = true;

    var mx = 0, my = 0;
    window.addEventListener('mousemove', function (e) { mx = (e.clientX / innerWidth - .5) * 2; my = (e.clientY / innerHeight - .5) * 2; });

    function resize() {
      var w = wrapEl.clientWidth, h = wrapEl.clientHeight;
      renderer.setSize(w, h, false);
      camera.aspect = w / h; camera.updateProjectionMatrix();
      wide = w > 820;
      edge.h = Math.tan(22.5 * Math.PI / 180) * 13; edge.w = edge.h * camera.aspect;
      if (wide) { h2x = edge.w * 0.27; h2y = -edge.h * 0.56; h2s = 0.62; }
      else { h2x = edge.w * 0.5; h2y = -edge.h * 0.8; h2s = 0.42; }
      measureCards();
    }
    window.addEventListener('resize', resize); resize();
    setTimeout(measureCards, 400);

    var clock = new THREE.Clock(), prev = 0;
    (function loop() {
      var t = clock.getElapsedTime(), dt = Math.min(t - prev, 0.05); prev = t;
      p += (target - p) * (1 - Math.exp(-dt * 2.7));
      if (Math.abs(target - p) < 0.0005) p = target;

      var swell = 1 + 0.45 * sstep(0, .14, p);
      knot.scale.setScalar(Math.max(0.0001, swell * (1 - sstep(.12, .36, p))));
      knot.rotation.x = t * (0.35 + p * 2); knot.rotation.y = t * (0.5 + p * 3);
      ico.rotation.y = -t * 0.12; ico.rotation.x = t * 0.07;
      ico.scale.setScalar(1 + p * 2.4); icoMat.opacity = 0.16 * (1 - sstep(.1, .7, p));
      ring.rotation.z = t * 0.2; ring.scale.setScalar(1 + p * 3); ringMat.opacity = 1 - sstep(0, .5, p);
      var sw = clamp01(p / 0.7);
      shock.scale.setScalar(0.3 + sw * 13); shockMat.opacity = Math.sin(Math.PI * sw) * 0.85;

      var ease = sstep(0.03, 0.92, p), drift = sstep(.8, 1, p);
      shards.forEach(function (m) {
        var d = m.userData;
        m.position.copy(d.dir).multiplyScalar(d.sp * ease);
        m.position.y += Math.sin(t * .6 + d.ph) * 0.35 * drift;
        m.position.x += Math.cos(t * .5 + d.ph) * 0.3 * drift;
        m.rotation.x = t * d.rx; m.rotation.y = t * d.ry;
        m.scale.setScalar(d.base * sstep(.04, .2, p));
      });
      shardMats.forEach(function (mt) { mt.opacity = 1 - 0.5 * sstep(.6, 1, p); });

      var spread = 1 + p * 2.8;
      cards.forEach(function (g) {
        var d = g.userData, a = d.a + t * d.s * (1 + p * 1.5);
        g.position.set(Math.cos(a) * d.r * spread, d.y * (1 + p * 2) + Math.sin(t * 1.1 + d.a) * 0.28, Math.sin(a) * d.r * 0.62 * spread - p * 4);
        g.rotation.set(Math.sin(t * .7 + d.a) * .35, -a + Math.PI / 2, Math.cos(t * .5 + d.a) * .25);
      });
      cubes.forEach(function (c) { c.rotation.x += c.userData.v * 2; c.rotation.y += c.userData.v * 3; c.position.y += Math.sin(t + c.userData.ph) * 0.003; });
      pts.rotation.y = t * 0.02;
      ptsMat.color.copy(ptsA).lerp(ptsB, sstep(.2, .7, p)); ptsMat.opacity = 0.7 - 0.35 * p;

      var bg = sstep(.18, .62, p);
      tmp.copy(bgA).lerp(bgB, bg);
      wrapEl.style.backgroundColor = '#' + tmp.getHexString();
      scn.fog.color.copy(tmp); scn.fog.density = 0.04 - 0.022 * p;
      glow.style.opacity = 1 - bg;

      group.position.x = (wide ? 3.1 : 0) * (1 - sstep(0, .5, p));
      group.position.y = (wide ? 0.1 : 1.6) * (1 - sstep(0, .5, p));
      group.scale.setScalar(wide ? 1 : 0.7);
      redLight.position.x = -5 + Math.sin(t * .6) * 3;
      camera.position.z = 10 + p * 3;
      camera.position.x += (mx * 1.2 * (1 - 0.6 * p) - camera.position.x) * 0.04;
      camera.position.y += (-my * 0.8 * (1 - 0.6 * p) - camera.position.y) * 0.04;

      var a2 = sstep(.5, .98, p), s2 = a2 > 0 ? backOut(a2) : 0, on = s2 > 0.002;
      deco.forEach(function (o) { o.visible = on; });
      if (on) {
        hero2.position.set(h2x, h2y + Math.sin(t * .9) * 0.14, -1);
        hero2.scale.setScalar(h2s * s2);
        knot2.rotation.x = t * 0.35; knot2.rotation.y = t * 0.5;
        ico2.rotation.y = -t * 0.12; ico2.rotation.x = t * 0.07; ring2.rotation.z = t * 0.2;
        cards2.forEach(function (g) {
          var d = g.userData, a = d.a + t * d.s;
          g.position.set(Math.cos(a) * d.r, d.y + Math.sin(t * 1.1 + d.a) * 0.25, Math.sin(a) * d.r * 0.62);
          g.rotation.set(Math.sin(t * .7 + d.a) * .35, -a + Math.PI / 2, Math.cos(t * .5 + d.a) * .25);
        });
        sat1.position.set(edge.w * 0.86, edge.h * 0.74 + Math.sin(t * .8) * 0.2, -1.5); sat1.scale.setScalar(s2);
        sat1.rotation.set(t * 0.4, t * 0.55, 0);
        sat2.position.set(-edge.w * 0.9, -edge.h * 0.66 + Math.sin(t * .7 + 1) * 0.2, -1); sat2.scale.setScalar(s2 * 1.1);
        sat2.rotation.set(t * 0.5, t * 0.3, t * 0.2);
        sat3.position.set(edge.w * 0.42, edge.h * 0.93 + Math.sin(t * .9 + 2) * 0.15, -3); sat3.scale.setScalar(s2 * 0.9);
        sat3.rotation.set(t * 0.3, t * 0.6, 0);
        sat4.position.set(-edge.w * 0.55, edge.h * 0.86 + Math.sin(t * .6 + 3) * 0.2, -2); sat4.scale.setScalar(s2);
        sat4.rotation.set(t * 0.6, t * 0.4, t * 0.1);
      }
      camera.lookAt(0, 0, 0);
      renderer.render(scn, camera);

      var ho = 1 - sstep(0, .38, p);
      hero.style.opacity = ho;
      hero.style.transform = 'translateY(-50%) translateX(' + (-p * 180) + 'px) scale(' + (1 + p * .18) + ')';
      hero.style.filter = p > 0.01 ? 'blur(' + (p * 6) + 'px)' : 'none';
      ticker.style.opacity = 1 - sstep(0, .3, p);
      ticker.style.transform = 'rotate(-2deg) translateY(' + (p * 90) + 'px)';

      var ht = sstep(.42, .78, p);
      h2.style.opacity = ht; h2.style.transform = 'translateY(' + ((1 - ht) * 40) + 'px)';
      var st = sstep(.5, .85, p);
      sub.style.opacity = st; sub.style.transform = 'translateY(' + ((1 - st) * 30) + 'px)';
      for (var q = 0; q < cardEls.length; q++) {
        var ct = sstep(.34 + q * .032, .72 + q * .032, p), inv = 1 - ct, o = offs[q] || { dx: 0, dy: 0 };
        var el = cardEls[q];
        el.style.opacity = ct;
        el.style.transform = 'translate3d(' + (o.dx * inv) + 'px,' + (o.dy * inv) + 'px,' + (-650 * inv) + 'px) rotateX(' + (inv * 70) + 'deg) rotateY(' + (inv * (q % 2 ? -80 : 80)) + 'deg) rotateZ(' + (inv * (q % 3 - 1) * 40) + 'deg) scale(' + (0.4 + 0.6 * ct) + ')';
      }
      requestAnimationFrame(loop);
    })();
  } catch (err) {
    document.getElementById('c').style.display = 'none';
  }
</script>
""".replace("__CARDS__", CARDS_HTML)

INJECTOR = """
<script>
(function () {
  try {
    var P = window.parent;
    if (P.__submagSplash) return;
    P.__submagSplash = true;
    var doc = P.document;
    var wrap = doc.createElement('div');
    wrap.id = 'submag-splash';
    wrap.style.cssText = 'position:fixed;inset:0;z-index:2147483000;background:#0b0b0b;' +
      'transition:transform .95s cubic-bezier(.77,0,.18,1),opacity .95s ease;';
    var f = doc.createElement('iframe');
    f.title = 'SUB MAG intro';
    f.style.cssText = 'width:100%;height:100%;border:0;display:block;';
    f.srcdoc = __HTML__;
    f.addEventListener('load', function () { try { f.contentWindow.focus(); } catch (e) {} });
    wrap.appendChild(f);
    doc.body.appendChild(wrap);
  } catch (e) {}
})();
</script>
""".replace("__HTML__", json.dumps(SPLASH).replace("</", "<\\/"))


def inject():
    """Mount the intro once per browser page load (a refresh resets it; reruns don't)."""
    if hasattr(st, "iframe"):
        st.iframe(INJECTOR, height=1)
    else:
        import streamlit.components.v1 as components
        components.html(INJECTOR, height=0)
