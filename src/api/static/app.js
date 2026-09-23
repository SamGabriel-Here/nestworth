const $ = (s) => document.querySelector(s);
const form = $("#form");
const calm = matchMedia("(prefers-reduced-motion: reduce)");

function inr(v) {
  const a = Math.abs(v);
  if (a >= 1e7) return "₹" + (v / 1e7).toFixed(2) + " Cr";
  if (a >= 1e5) return "₹" + (v / 1e5).toFixed(1) + " L";
  return "₹" + Math.round(v).toLocaleString("en-IN");
}
const signed = (v) => (v >= 0 ? "+" : "−") + inr(Math.abs(v));
const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);

/* ---- theme ---- */
function setTheme(name) {
  document.documentElement.dataset.theme = name;
  document.querySelectorAll("[data-theme-set]").forEach((b) =>
    b.setAttribute("aria-checked", String(b.dataset.themeSet === name)));
  try { localStorage.setItem("nw-theme", name); } catch (e) {}
}
document.querySelectorAll("[data-theme-set]").forEach((b) =>
  b.addEventListener("click", () => setTheme(b.dataset.themeSet)));
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
    li.querySelector(".fv").textContent = signed(f.delta);
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
    + `<td>${c.age} yrs</td><td class="p">${inr(c.price)}</td><td class="d">${signed(c.price - d.estimate)}</td></tr>`).join("");
}

function render(d, p) {
  const where = `${p.location}, ${p.city}`;
  $("#price-label").textContent = `${p.bedrooms} BHK, ${p.area.toLocaleString("en-IN")} sq ft in ${where}`;
  paintPrice(d.estimate);
  $("#ppsf").textContent = `₹${Math.round(d.price_per_sqft).toLocaleString("en-IN")} per sq ft`;
  paintRange(d);
  $("#range-cap").textContent = `Track: the middle 80% of ${d.segment.n} listings near ${where}. Band: this home's ${d.interval.coverage}% range. Mark: the estimate.`;
  paintFactors(d.factors);
  paintComps(d);
  $("#rate-sub").textContent = `The five closest in size among ${d.segment.n} listings near ${where}.`;
  $("#r2").textContent = d.r2.toFixed(3);
  $("#mae").textContent = inr(d.mae);
  $("#cov").textContent = d.interval.coverage + "%";
  $("#dock-price").textContent = inr(d.estimate);
  $("#dock-range").textContent = `${d.interval.coverage}% range ${inr(d.interval.lo)} – ${inr(d.interval.hi)}`;
  $("#said").textContent = `Estimated ${inr(d.estimate)}. ${d.interval.coverage}% likely between ${inr(d.interval.lo)} and ${inr(d.interval.hi)}.`;
}

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
value();

/* ---- page motion: the top bar over the photograph, a slow parallax on the hero ---- */
const topBar = $(".top"), hero = $(".hero"), media = $(".hero-media");
new IntersectionObserver(([e]) => topBar.classList.toggle("over", e.isIntersecting), { rootMargin: "-64px 0px 0px 0px" }).observe(hero);
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
