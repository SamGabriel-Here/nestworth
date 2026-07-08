const $ = (s) => document.querySelector(s);

function inr(amount) {
  if (amount >= 1e7) return "₹" + (amount / 1e7).toLocaleString("en-IN", { maximumFractionDigits: 2, minimumFractionDigits: 2 }) + " Cr";
  if (amount >= 1e5) return "₹" + (amount / 1e5).toLocaleString("en-IN", { maximumFractionDigits: 1, minimumFractionDigits: 1 }) + " Lakh";
  return "₹" + Math.round(amount).toLocaleString("en-IN");
}
const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);

/* ---- theme ---- */
function setTheme(name) {
  document.documentElement.setAttribute("data-theme", name);
  document.querySelectorAll(".theme-toggle button").forEach((b) => {
    const on = b.dataset.themeSet === name;
    b.classList.toggle("on", on);
    b.setAttribute("aria-checked", on ? "true" : "false");
  });
  try { localStorage.setItem("nw-theme", name); } catch (e) {}
}
document.querySelectorAll(".theme-toggle button").forEach((b) =>
  b.addEventListener("click", () => setTheme(b.dataset.themeSet))
);
try { setTheme(localStorage.getItem("nw-theme") === "dark" ? "dark" : "light"); } catch (e) {}

/* ---- form widgets ---- */
const ageInput = $('input[name="house_age"]');
ageInput.addEventListener("input", () => { $("#age-val").textContent = ageInput.value + " yrs"; });

const roadSeg = $("#main-road");
roadSeg.querySelectorAll("button").forEach((b) =>
  b.addEventListener("click", () => {
    roadSeg.dataset.value = b.dataset.val;
    roadSeg.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
  })
);

/* ---- predict ---- */
function readForm() {
  const f = $("#form");
  return {
    area: +f.area.value,
    bedrooms: +f.bedrooms.value,
    bathrooms: +f.bathrooms.value,
    stories: +f.stories.value,
    city: f.city.value,
    location: f.location.value,
    house_age: +f.house_age.value,
    parking: +f.parking.value,
    main_road: roadSeg.dataset.value,
    furnishing_status: f.furnishing_status.value,
  };
}

function specRows(p) {
  const rows = [
    ["Locality", `${p.location}, ${p.city}`],
    ["Built-up area", `${p.area.toLocaleString("en-IN")} sq ft`],
    ["Configuration", `${p.bedrooms} BHK · ${p.bathrooms} bath`],
    ["Age", `${p.house_age} years`],
    ["Furnishing", p.furnishing_status.charAt(0).toUpperCase() + p.furnishing_status.slice(1)],
  ];
  return rows.map(([k, v]) => `<div class="spec-row"><span class="k">${k}</span><span class="v">${v}</span></div>`).join("");
}

function renderRail(seg, est, lo, hi) {
  const low = seg ? seg.low : lo, high = seg ? seg.high : hi;
  const span = Math.max(high - low, 1);
  const pct = clamp((est - low) / span * 100, 2, 98);
  const bl = clamp((Math.max(lo, low) - low) / span * 100, 0, 100);
  const br = clamp((Math.min(hi, high) - low) / span * 100, 0, 100);
  $("#rail-band").style.left = bl + "%";
  $("#rail-band").style.width = Math.max(br - bl, 1) + "%";
  $("#rail-diamond").style.left = pct + "%";
  $("#rail-flag").style.left = pct + "%";
  $("#rail-flag").textContent = inr(est);
  $("#rail-lo").textContent = inr(low);
  $("#rail-hi").textContent = inr(high);
}

function renderFactors(factors) {
  const maxAbs = Math.max(...factors.map((f) => Math.abs(f.delta)), 1);
  $("#factors").innerHTML = factors.map((f) => {
    const cls = f.delta >= 0 ? "pos" : "neg";
    const sign = f.delta >= 0 ? "+" : "−";
    const w = Math.abs(f.delta) / maxAbs * 100;
    return `<div class="factor"><div class="factor-top"><span class="fl">${f.label}</span>`
      + `<span class="fv ${cls}">${sign}${inr(Math.abs(f.delta))}</span></div>`
      + `<div class="factor-bar"><i class="${cls}" style="width:${w.toFixed(0)}%"></i></div></div>`;
  }).join("");
}

async function estimate(e) {
  e.preventDefault();
  const p = readForm();
  const btn = $(".cta");
  btn.disabled = true; btn.textContent = "Estimating…";
  try {
    const res = await fetch("/api/predict", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(p),
    });
    const d = await res.json();

    $("#kicker").textContent = `Valuation · ${p.city}`;
    $("#spec-rows").innerHTML = specRows(p);
    $("#price").textContent = inr(d.estimate);
    $("#ppsf").textContent = "₹" + Math.round(d.price_per_sqft).toLocaleString("en-IN") + " per sq ft";
    renderRail(d.segment, d.estimate, d.interval.lo, d.interval.hi);
    $("#rail-cap").innerHTML = `<b>${d.interval.coverage}% confidence:</b> ${inr(d.interval.lo)} – ${inr(d.interval.hi)}`
      + ` · shown against typical ${p.city} · ${p.location} prices`;
    $("#badge").textContent = `Model R² ${d.r2.toFixed(2)} on held-out data`;
    $("#r2-inline").textContent = d.r2.toFixed(2);
    renderFactors(d.factors);
    $("#comps-h").textContent = `Comparable homes in ${p.city} · ${p.location}`;
    $("#comps").innerHTML = d.comparables.map((c) =>
      `<div class="comp-row"><span>${c.desc}</span><b>${inr(c.price)}</b></div>`).join("");

    $("#result").hidden = false;
    $("#result").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    alert("Could not reach the model. Try again.");
  } finally {
    btn.disabled = false; btn.textContent = "Estimate price";
  }
}
$("#form").addEventListener("submit", estimate);
