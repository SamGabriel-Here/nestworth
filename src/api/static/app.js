const $ = (s) => document.querySelector(s);
const form = $("#form");
const calm = matchMedia("(prefers-reduced-motion: reduce)");

function inr(v) {
  const a = Math.abs(v);
  if (a >= 1e7) return "₹" + (v / 1e7).toFixed(2) + " Cr";
  if (a >= 1e5) return "₹" + (v / 1e5).toFixed(1) + " L";
  return "₹" + Math.round(v).toLocaleString("en-IN");
}
const signed = (v) => `<span class="sg">${v >= 0 ? "+" : "−"}</span>${inr(Math.abs(v))}`; // the sign in the text face: the display face draws it faint and tight
const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);

/* ---- theme ---- */
function setTheme(name) {
  document.documentElement.dataset.theme = name;
  document.querySelectorAll("[data-theme-set]").forEach((b) =>
    b.setAttribute("aria-pressed", String(b.dataset.themeSet === name)));
  try { localStorage.setItem("nw-theme", name); } catch (e) {}
}
document.querySelectorAll("[data-theme-set]").forEach((b) => b.addEventListener("click", () => {
  const name = b.dataset.themeSet, root = document.documentElement;
  if (name === root.dataset.theme) return;
  if (!document.startViewTransition || calm.matches) return setTheme(name);
  const r = b.getBoundingClientRect(); // night falls (or day breaks) from the switch that was pressed
  root.style.setProperty("--vx", r.left + r.width / 2 + "px");
  root.style.setProperty("--vy", r.top + r.height / 2 + "px");
  root.classList.add("vt");
  const t = document.startViewTransition(() => setTheme(name));
  t.ready.catch(() => {}); // skipped in a hidden tab: the theme still changes, only the wipe is dropped
  t.finished.finally(() => root.classList.remove("vt"));
}));
setTheme(document.documentElement.dataset.theme || "light");

/* ---- inputs ---- */
const area = $("#area"), areaRange = $("#area-range"), hint = $("#area-hint");
areaRange.addEventListener("input", () => { area.value = areaRange.value; });
area.addEventListener("input", () => { areaRange.value = area.value; });
$("#age").addEventListener("input", (e) => {
  const n = +e.target.value;
  $("#age-out").textContent = n === 0 ? "New" : n + (n === 1 ? " year" : " years");
});

function readForm() {
  const p = Object.fromEntries(new FormData(form));
  for (const k of ["area", "bedrooms", "bathrooms", "stories", "house_age", "parking"]) p[k] = +p[k];
  return p;
}

function areaOk(p) {
  const ok = area.value !== "" && p.area >= 300 && p.area <= 9000;
  area.setAttribute("aria-invalid", String(!ok));
  hint.textContent = ok ? "300 to 9,000 sq ft" : "Enter an area between 300 and 9,000 sq ft";
  hint.classList.toggle("err", !ok);
  return ok;
}

/* ---- the price repaints: count from the old figure to the new one ---- */
let shown = 0;
function paintPrice(target) {
  const el = $("#price"), from = shown;
  shown = target;
  if (calm.matches) { el.textContent = inr(target); return; }
  const t0 = performance.now(), dur = from ? 450 : 1100; // the first figure counts up from zero
  (function step(t) {
    const k = Math.min((t - t0) / dur, 1), e = 1 - Math.pow(2, -10 * k);
    el.textContent = inr(from + (target - from) * (k === 1 ? 1 : e));
    if (k < 1 && shown === target) requestAnimationFrame(step);
  })(t0);
}

/* ---- factors: five stable rows so bars glide between valuations ---- */
const rows = Array.from({ length: 5 }, () => {
  const li = document.createElement("li");
  li.innerHTML = '<span class="fl"></span><span class="fbar"><i class="up"></i><i class="down"></i></span><span class="fv"></span>';
  $("#factors").append(li);
  return li;
});
function paintFactors(factors) {
  const max = Math.max(...factors.map((f) => Math.abs(f.delta)), 1);
  rows.forEach((li, i) => {
    const f = factors[i], w = f.delta ? Math.max(Math.abs(f.delta) / max, 0.04) : 0; // small effects still draw as a bar
    li.querySelector(".fl").textContent = f.label;
    li.querySelector(".fv").innerHTML = signed(f.delta);
    li.querySelector(".up").style.transform = `scaleX(${f.delta >= 0 ? w : 0})`;
    li.querySelector(".down").style.transform = `scaleX(${f.delta < 0 ? w : 0})`;
  });
}

/* ---- the range, drawn on the locality's own 10th-to-90th percentile scale ---- */
function paintRange(d) {
  const { lo, hi, coverage } = d.interval, s = d.segment;
  const span = Math.max(s.high - s.low, 1), at = (v) => clamp((v - s.low) / span, 0, 1);
  $("#range-pct").textContent = coverage + "%";
  $("#range-lo").textContent = inr(lo);
  $("#range-hi").textContent = inr(hi);
  $("#band").style.transform = `translateX(${at(lo) * 100}%) scaleX(${Math.max(at(hi) - at(lo), 0.01)})`;
  $("#pin").style.setProperty("--x", at(d.estimate) * 100 + "%");
  const mid = at(s.mid) * 100;
  $("#t-low").style.left = "0";
  $("#t-high").style.right = "0";
  $("#t-mid").style.left = clamp(mid, 30, 70) + "%";
  $("#t-mid").style.transform = "translateX(-50%)";
  $("#t-low").innerHTML = `Bottom 10% <b>${inr(s.low)}</b>`;
  $("#t-mid").innerHTML = `Median <b>${inr(s.mid)}</b>`;
  $("#t-high").innerHTML = `Top 10% <b>${inr(s.high)}</b>`;
}

function paintComps(d) {
  $("#comps").innerHTML = d.comparables.map((c) =>
    `<tr><td>${c.area.toLocaleString("en-IN")} sq ft<span class="bhk"> · ${c.bedrooms} BHK</span></td><td>${c.bedrooms} BHK</td>`
    + `<td>${c.age} yrs</td><td>${c.type}</td><td class="p">${inr(c.price)}</td><td class="d">${signed(c.price - d.estimate)}</td></tr>`).join("");
}

function render(d, p) {
  const where = `${p.location}, ${p.city}`;
  $("#price-label").textContent = `${kindOf(p)}, ${p.area.toLocaleString("en-IN")} sq ft in ${where}`;
  paintPrice(d.estimate);
  $("#ppsf").textContent = `₹${Math.round(d.price_per_sqft).toLocaleString("en-IN")} per sq ft`;
  paintRange(d);
  $("#range-cap").textContent = `Track: the middle 80% of ${d.segment.n} listings near ${where}. Band: this home's ${d.interval.coverage}% range. Mark: the estimate.`;
  paintFactors(d.factors);
  paintComps(d);
  $("#rate-sub").textContent = `The five closest in size among ${d.segment.n} similar listings near ${where}.`;
  paintCurve(d, p);
  paintCities(d, p);
  answers = p;
  $("#r2").textContent = d.r2.toFixed(3);
  $("#mae").textContent = inr(d.mae);
  $("#cov").textContent = d.interval.coverage + "%";
  $("#dock-price").textContent = inr(d.estimate);
  $("#dock-range").textContent = `${d.interval.coverage}% range ${inr(d.interval.lo)} – ${inr(d.interval.hi)}`;
  $("#said").textContent = `Estimated ${inr(d.estimate)}. ${d.interval.coverage}% likely between ${inr(d.interval.lo)} and ${inr(d.interval.hi)}.`;
}

const kindOf = (p) => p.property_type === "Studio" ? "Studio" : `${p.bedrooms} BHK ${p.property_type.toLowerCase()}`;

/* ---- price against size: the same home at other areas, its band, and a hover readout ---- */
const phone = matchMedia("(max-width: 560px)"), M = { l: 64, r: 16, t: 16, b: 36 };
let CW = 800, CH = 340, curvePts = [], lastCurve;
phone.addEventListener("change", () => lastCurve && paintCurve(...lastCurve));
function paintCurve(d, p) {
  const pts = (curvePts = d.curve), svg = $("#curve");
  lastCurve = [d, p];
  [CW, CH, M.l] = phone.matches ? [400, 300, 72] : [800, 340, 64]; // a phone gets a smaller sheet, so the chart shrinks less and its words stay legible
  svg.setAttribute("viewBox", `0 0 ${CW} ${CH}`);
  const xMax = pts.at(-1).area, yMax = Math.max(...pts.map((q) => q.hi)) * 1.05;
  const x = (a) => M.l + ((a - 300) / (xMax - 300)) * (CW - M.l - M.r);
  const y = (v) => CH - M.b - (v / yMax) * (CH - M.t - M.b);
  if (!svg.firstChild) // built once; later valuations morph these shapes rather than redrawing them
    svg.innerHTML = '<g class="axes"></g><path class="cband"/><path class="line"/><circle class="here" r="6"/><text class="here-label"></text>'
      + `<g id="cross" visibility="hidden"><line class="cross" y1="${M.t}" y2="${CH - M.b}"/><circle class="dot" r="5"/></g>`;
  svg.querySelector(".cross").setAttribute("y2", CH - M.b);
  const step = [1e5, 5e5, 1e6, 2.5e6, 5e6, 1e7, 2.5e7, 5e7, 1e8].find((s) => yMax / s <= 5) || 2e8;
  let g = "";
  for (let v = 0; v <= yMax; v += step)
    g += `<line class="grid" x1="${M.l}" x2="${CW - M.r}" y1="${y(v)}" y2="${y(v)}"/><text class="axis" x="${M.l - 8}" y="${y(v) + 4}" text-anchor="end">${v ? inr(v) : "0"}</text>`;
  const aStep = [250, 500, 1000, 2000].find((s) => (xMax - 300) / s <= 6);
  for (let a = Math.ceil(300 / aStep) * aStep; a <= xMax; a += aStep)
    g += `<text class="axis" x="${x(a)}" y="${CH - M.b + 20}" text-anchor="middle">${a.toLocaleString("en-IN")}</text>`;
  g += `<text class="axis" x="${CW - M.r}" y="${CH - 2}" text-anchor="end">sq ft</text>`;
  svg.querySelector(".axes").innerHTML = g;
  const band = "M" + pts.map((q) => `${x(q.area)},${y(q.hi)}`).join("L") + "L" + [...pts].reverse().map((q) => `${x(q.area)},${y(q.lo)}`).join("L") + "Z";
  svg.querySelector(".cband").style.d = `path("${band}")`;
  svg.querySelector(".line").style.d = `path("M${pts.map((q) => `${x(q.area)},${y(q.estimate)}`).join("L")}")`;
  const me = pts.find((q) => q.area === p.area) || pts[0], mx = x(me.area), my = y(me.estimate);
  svg.querySelector(".here").style.transform = `translate(${mx}px, ${my}px)`;
  const label = svg.querySelector(".here-label"), right = mx > CW - 200; // keep the label inside the plot near the right edge
  label.textContent = `This home · ${inr(me.estimate)}`;
  label.setAttribute("text-anchor", right ? "end" : "start");
  label.style.transform = `translate(${mx + (right ? -12 : 12)}px, ${my - 10}px)`;
  svg.dataset.xmax = xMax; svg.dataset.ymax = yMax;
  $("#curve-table tbody").innerHTML = pts.map((q) =>
    `<tr><td>${q.area.toLocaleString("en-IN")}</td><td>${inr(q.estimate)}</td><td>${inr(q.lo)} – ${inr(q.hi)}</td></tr>`).join("");
  $("#sizes-note").textContent = `This ${p.property_type === "Studio" ? "studio" : kindOf(p)} in ${p.location}, ${p.city} at other sizes, with its 90% range. The mark is your home.`;
}
function showTip(e) {
  const svg = $("#curve"), box = svg.getBoundingClientRect(), tip = $("#tip");
  if (!curvePts.length) return;
  const xMax = +svg.dataset.xmax, yMax = +svg.dataset.ymax;
  const sx = ((e.clientX - box.left) / box.width) * CW;
  const area = 300 + ((sx - M.l) / (CW - M.l - M.r)) * (xMax - 300);
  const q = curvePts.reduce((a, b) => (Math.abs(b.area - area) < Math.abs(a.area - area) ? b : a));
  const px = M.l + ((q.area - 300) / (xMax - 300)) * (CW - M.l - M.r), py = CH - M.b - (q.estimate / yMax) * (CH - M.t - M.b);
  const cross = $("#cross");
  cross.setAttribute("visibility", "visible");
  cross.querySelector("line").setAttribute("x1", px); cross.querySelector("line").setAttribute("x2", px);
  cross.querySelector("circle").setAttribute("cx", px); cross.querySelector("circle").setAttribute("cy", py);
  tip.hidden = false;
  tip.innerHTML = `<b>${q.area.toLocaleString("en-IN")} sq ft</b> · ${inr(q.estimate)}<br>90%: ${inr(q.lo)} – ${inr(q.hi)}`;
  tip.style.left = clamp((px / CW) * box.width, 90, box.width - 90) + "px";
  tip.style.top = Math.max((py / CH) * box.height - 64, 0) + "px";
}
$("#curve").addEventListener("pointermove", showTip);
$("#curve").addEventListener("pointerleave", () => { $("#tip").hidden = true; $("#cross")?.setAttribute("visibility", "hidden"); });

/* ---- the same home, city by city ---- */
function paintCities(d, p) {
  const max = d.cities[0].estimate, list = $("#city-list");
  if (list.children.length !== d.cities.length)
    list.innerHTML = d.cities.map(() => '<li><span class="cn"></span><span class="cb"><i></i></span><span class="cv"></span></li>').join("");
  [...list.children].forEach((li, i) => {
    const c = d.cities[i];
    li.classList.toggle("me", c.city === p.city);
    li.querySelector(".cn").textContent = c.city;
    li.querySelector(".cv").textContent = inr(c.estimate);
    li.querySelector("i").style.transform = `scaleX(${c.estimate / max})`;
  });
  const rank = d.cities.findIndex((c) => c.city === p.city) + 1;
  $("#cities-note").textContent = `Everything else held equal. ${p.city} ranks ${rank} of ${d.cities.length}.`;
}

/* ---- shareable link: a short URL that reopens this valuation; the address bar itself stays clean ---- */
const FIELDS = ["city", "location", "property_type", "area", "bedrooms", "bathrooms", "stories", "parking", "house_age", "main_road", "furnishing_status"];
const START = Object.fromEntries(FIELDS.map((k) => [k, form.elements[k].value])); // the form as the page first draws it
let answers;
function link(p) { // only the answers that differ from the starting form, so a shared link stays short
  const q = new URLSearchParams(FIELDS.filter((k) => String(p[k]) !== START[k]).map((k) => [k, p[k]]));
  return location.origin + location.pathname + (q.size ? "?" + q : "");
}
function loadFromUrl() {
  const q = new URLSearchParams(location.search);
  for (const k of FIELDS) {
    if (!q.has(k)) continue;
    const el = form.elements[k], v = q.get(k);
    if (el instanceof RadioNodeList) { const r = [...el].find((r) => r.value === v); if (r) r.checked = true; }
    else if (el && v !== "" && !isNaN(+v)) el.value = v;
  }
  areaRange.value = area.value;
  $("#age").dispatchEvent(new Event("input"));
  if (location.search) history.replaceState(null, "", location.pathname + location.hash); // answers read; the address bar stays clean
}
$("#share").addEventListener("click", async () => {
  const status = $("#status");
  const url = link(answers);
  try { await navigator.clipboard.writeText(url); status.textContent = "Link copied. It reopens this exact valuation."; }
  catch { status.textContent = `Copy this link: ${url}`; }
  status.classList.remove("err");
});
$("#report").addEventListener("click", () => {
  $("#print-head").textContent = `NestWorth valuation report · ${new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })} · ${link(answers)}`;
  print();
});

/* a studio is one room: keep its answers consistent */
form.addEventListener("change", (e) => {
  if (e.target.name !== "property_type" || e.target.value !== "Studio") return;
  for (const k of ["bedrooms", "bathrooms", "stories"]) [...form.elements[k]].find((r) => r.value === "1").checked = true;
  if (+area.value > 800) area.value = areaRange.value = 450; // studios in the data run 300-650 sq ft
});

/* ---- live valuation: every change repaints the board ---- */
let inflight, timer;
async function value() {
  const p = readForm();
  if (!areaOk(p)) return;
  paintHome(p);
  inflight?.abort();
  const ctl = (inflight = new AbortController());
  const answer = $(".estimate"), status = $("#status");
  const slow = setTimeout(() => { answer.dataset.slow = ""; status.textContent = "Repainting…"; }, 300);
  answer.setAttribute("aria-busy", "true");
  try {
    const res = await fetch("/api/predict", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(p), signal: ctl.signal,
    });
    if (!res.ok) throw new Error(res.status);
    render(await res.json(), p);
    status.textContent = "";
    status.classList.remove("err");
  } catch (err) {
    if (err.name === "AbortError") return;
    status.textContent = "Couldn't reach the model. Check your connection, then change any value to try again.";
    status.classList.add("err");
  } finally {
    clearTimeout(slow);
    if (inflight === ctl) { delete answer.dataset.slow; answer.setAttribute("aria-busy", "false"); }
  }
}
/* ---- the home itself: the room photograph follows furnishing, the section drawing follows everything ---- */
const ROOM = { unfurnished: "Unfurnished", "semi-furnished": "Semi-furnished", furnished: "Furnished" };
let drawingSeen = false;
function paintHome(p) {
  document.querySelectorAll(".room img").forEach((img) => img.classList.toggle("on", img.dataset.room === p.furnishing_status));
  $("#room-cap").textContent = ROOM[p.furnishing_status];
  if (drawingSeen) Scene.paint(p);
}
Scene.init($("#scene"));
// build the drawing the first time it scrolls into view, so its assembly is seen
new IntersectionObserver(([e], io) => {
  if (!e.isIntersecting) return;
  drawingSeen = true; io.disconnect();
  const p = readForm();
  if (area.value !== "" && p.area >= 300 && p.area <= 9000) Scene.paint(p);
}, { threshold: 0.35 }).observe($("#scene"));

form.addEventListener("input", () => {
  const p = readForm();
  if (area.value !== "" && p.area >= 300 && p.area <= 9000) paintHome(p); // the drawing answers at once
  clearTimeout(timer); timer = setTimeout(value, 160);
});
form.addEventListener("submit", (e) => { e.preventDefault(); value(); });
loadFromUrl();
value();

/* ---- page motion: the top bar over the photograph, a slow parallax on the hero ---- */
const topBar = $(".top"), hero = $(".hero"), media = $(".hero-media");
// transparent only while real photograph sits behind it; solid before the hero's fact line slides under
new IntersectionObserver(([e]) => topBar.classList.toggle("over", e.isIntersecting), { rootMargin: "-160px 0px 0px 0px" }).observe(hero);
// one scroll pass per frame: the phone dock (checked by position, so jumps via links count too) and the hero parallax
const dock = $("#dock"), price = $("#price");
let ticking = false;
function onScroll() {
  ticking = false;
  dock.classList.toggle("show", price.getBoundingClientRect().bottom < 0); // only once the price is above the viewport
  if (!calm.matches && scrollY < innerHeight) media.style.transform = `translateY(${scrollY * 0.18}px)`;
}
addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
onScroll();
