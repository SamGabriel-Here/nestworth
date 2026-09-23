/* The home, drawn live: a section cut through the house the form describes.
   Every piece is keyed, so a change moves, adds or removes only what changed. */
const Scene = (() => {
  const NS = "http://www.w3.org/2000/svg";
  const W = 800, GROUND = 266, FLOOR = 58, SLAB = 6, CLEAR = FLOOR - SLAB, LABEL = 12;

  // Furniture in side elevation: [width, height, markup], drawn standing on y = height.
  const F = {
    bed: [64, 30, '<rect class="wd" width="5" height="30"/><rect class="wd" y="17" width="64" height="9"/><rect class="wd" x="3" y="26" width="3" height="4"/><rect class="wd" x="58" y="26" width="3" height="4"/><rect class="wh" x="4" y="11" width="59" height="7"/><rect class="mg" x="25" y="10" width="38" height="9"/><rect class="wh" x="7" y="7" width="13" height="5"/>'],
    wardrobe: [24, 48, '<rect class="wd" width="24" height="45"/><rect class="dk" x="11.5" y="3" width="1" height="39"/><rect class="dk" x="8" y="20" width="2" height="5"/><rect class="dk" x="14" y="20" width="2" height="5"/><rect class="dk" x="2" y="45" width="3" height="3"/><rect class="dk" x="19" y="45" width="3" height="3"/>'],
    sofa: [58, 26, '<rect class="fb" x="5" width="48" height="14"/><rect class="fl" x="3" y="12" width="52" height="8"/><rect class="fb" y="6" width="8" height="16"/><rect class="fb" x="50" y="6" width="8" height="16"/><rect class="mg" x="12" y="4" width="10" height="8"/><rect class="dk" x="3" y="22" width="3" height="4"/><rect class="dk" x="52" y="22" width="3" height="4"/>'],
    tv: [36, 38, '<rect class="sc" x="3" width="30" height="19"/><rect class="gl" x="6" y="3" width="6" height="13" opacity=".35"/><rect class="mt" x="16" y="19" width="4" height="4"/><rect class="wd" y="23" width="36" height="12"/><rect class="dk" x="17.5" y="25" width="1" height="8"/><rect class="dk" x="2" y="35" width="3" height="3"/><rect class="dk" x="31" y="35" width="3" height="3"/>'],
    lamp: [14, 46, '<path class="mg" d="M3 0H11L14 12H0Z"/><rect class="mt" x="6.2" y="12" width="1.6" height="31"/><rect class="mt" x="2" y="43" width="10" height="3"/>'],
    plant: [18, 32, '<path class="lf" d="M9 20C1 16 0 6 4 2 8 6 10 13 9 20Z"/><path class="ld" d="M9 20C17 16 18 6 14 1 10 6 8 13 9 20Z"/><path class="lf" d="M9 20C7.5 12 8 5 9.5 0 11.5 7 11 14 9 20Z"/><path class="pt" d="M3 20H15L13 32H5Z"/>'],
    rug: [56, 3, '<rect class="rg" width="56" height="3"/>'],
    dining: [48, 30, '<rect class="wd" x="8" y="12" width="32" height="3"/><rect class="dk" x="11" y="15" width="2.5" height="15"/><rect class="dk" x="34.5" y="15" width="2.5" height="15"/><path class="mg" d="M19 12A5 4.5 0 0 1 29 12Z"/><rect class="fb" y="4" width="3" height="26"/><rect class="fb" y="17" width="9" height="3"/><rect class="fb" x="7" y="20" width="2" height="10"/><rect class="fb" x="45" y="4" width="3" height="26"/><rect class="fb" x="39" y="17" width="9" height="3"/><rect class="fb" x="39" y="20" width="2" height="10"/>'],
    kitchen: [46, 50, '<rect class="wh" width="46" height="13"/><rect class="ln" x="15" y="2" width="1" height="9"/><rect class="ln" x="30" y="2" width="1" height="9"/><rect class="mg" x="32" y="17" width="7" height="8"/><rect class="mt" x="4" y="22" width="12" height="3"/><rect class="ct" y="25" width="46" height="3"/><rect class="wh" x="1" y="28" width="44" height="22"/><rect class="ln" x="15.5" y="30" width="1" height="18"/><rect class="ln" x="30.5" y="30" width="1" height="18"/>'],
    bath: [48, 34, '<rect class="mt" x="42" width="2" height="16"/><rect class="mt" x="35" width="9" height="2"/><path class="wh" d="M0 18H48V22C48 30 42 32 36 32H12C6 32 0 30 0 22Z"/><rect class="ln" y="18" width="48" height="1.5"/><rect class="mt" x="6" y="31" width="4" height="3"/><rect class="mt" x="38" y="31" width="4" height="3"/>'],
    basin: [18, 36, '<rect class="gl" x="3" width="12" height="13"/><rect class="mt" x="8" y="14" width="2" height="3"/><rect class="wh" y="17" width="18" height="5"/><rect class="wh" x="6.5" y="22" width="5" height="14"/>'],
    car: [64, 25, '<path class="cb" d="M2 15L9 14 18 5C20 3 22 2 25 2H41C44 2 46 3 48 5L55 12 61 13C63 13.5 64 15 64 17V20H2Z"/><path class="gl" d="M16 12L21 6.5C22 5 23.5 4.5 25.5 4.5H31V12Z"/><path class="gl" d="M33 4.5H40.5C42.5 4.5 44 5 45.5 6.5L51 12H33Z"/><rect class="mg" x="61" y="14" width="3" height="2"/><circle class="ty" cx="16" cy="20" r="5"/><circle class="hb" cx="16" cy="20" r="2"/><circle class="ty" cx="50" cy="20" r="5"/><circle class="hb" cx="50" cy="20" r="2"/>'],
    tree: [34, 60, '<rect class="dk" x="15" y="34" width="4" height="26"/><circle class="lf" cx="17" cy="22" r="14"/><circle class="ld" cx="9" cy="31" r="9"/><circle class="lf" cx="25" cy="31" r="9"/>'],
  };

  // What each room holds, by furnishing. Fixtures stay; loose furniture comes and goes.
  const ROOMS = {
    living: { w: 2.3, furnished: ["plant", "sofa", "lamp", "tv"], "semi-furnished": ["sofa", "tv"], unfurnished: ["sofa"] },
    kitchen: { w: 1.5, furnished: ["kitchen", "dining"], "semi-furnished": ["kitchen"], unfurnished: ["kitchen"] },
    bed: { w: 1.7, furnished: ["wardrobe", "bed", "plant"], "semi-furnished": ["wardrobe", "bed"], unfurnished: ["bed"] },
    bath: { w: 1.0, furnished: ["bath", "basin"], "semi-furnished": ["bath", "basin"], unfurnished: ["bath", "basin"] },
    studio: { w: 3.2, furnished: ["bed", "sofa", "kitchen"], "semi-furnished": ["bed", "kitchen"], unfurnished: ["bed", "kitchen"] },
  };
  const LOOSE = new Set(["sofa", "bed"]); // drawn as floor-tape outlines when unfurnished
  const NAMES = { living: () => "LIVING", kitchen: () => "KITCHEN", bed: (k) => "BED " + k.split("-")[1], bath: (k) => "BATH " + k.split("-")[1], studio: () => "STUDIO" };
  const narrow = matchMedia("(max-width: 560px)"), still = matchMedia("(prefers-reduced-motion: reduce)");

  // The drafter's pen: a new piece is inked along its outline, then its fill washes in.
  function pen(g) {
    if (still.matches) { g.classList.replace("draw", "fade"); return; }
    const shapes = g.querySelectorAll("path, rect, circle");
    shapes.forEach((s) => s.setAttribute("pathLength", "1"));
    g.style.setProperty("--d", g.style.animationDelay);
    g.addEventListener("animationend", () => { // hand the outline back to normal styling (floor-tape dashes need real units)
      shapes.forEach((s) => s.removeAttribute("pathLength"));
      g.classList.remove("draw");
    }, { once: true });
  }

  // Landmarks in the far distance, one per city: [width, height, markup].
  const MARKS = {
    Mumbai: [90, 70, '<path d="M10 70V20H80V70H55V48A10 10 0 0 0 35 48V70Z"/><rect x="10" y="6" width="10" height="14"/><rect x="70" y="6" width="10" height="14"/><circle cx="15" cy="6" r="5"/><circle cx="75" cy="6" r="5"/><rect x="32" y="12" width="26" height="8"/><path d="M38 12A7 7 0 0 1 52 12Z"/>'],
    Delhi: [52, 92, '<path d="M6 92V20H46V92H33V56A7 7 0 0 0 19 56V92Z"/><rect x="3" y="14" width="46" height="6"/><rect x="16" y="6" width="20" height="8"/><path d="M19 6A7 6 0 0 1 33 6Z"/>'],
    Bangalore: [124, 62, '<rect y="32" width="124" height="30"/><rect x="40" y="24" width="44" height="8"/><rect x="52" y="13" width="20" height="11"/><path d="M50 13A12 12 0 0 1 74 13Z"/><rect x="6" y="25" width="12" height="7"/><circle cx="12" cy="25" r="5"/><rect x="106" y="25" width="12" height="7"/><circle cx="112" cy="25" r="5"/>'],
    Chennai: [60, 92, '<path d="M0 92L4 74H8L11 58H15L18 42H22L25 28H35L38 42H42L45 58H49L52 74H56L60 92Z"/><rect x="22" y="18" width="16" height="10"/><path d="M22 18A8 6 0 0 1 38 18Z"/><circle cx="24" cy="10" r="2"/><circle cx="30" cy="8" r="2"/><circle cx="36" cy="10" r="2"/>'],
    Hyderabad: [80, 80, '<path d="M10 80V34H70V80H48V58A8 8 0 0 0 32 58V80Z"/><rect x="4" y="6" width="8" height="74"/><rect x="68" y="6" width="8" height="74"/><circle cx="8" cy="6" r="5"/><circle cx="72" cy="6" r="5"/><rect x="6" y="34" width="68" height="4"/>'],
    Pune: [80, 60, '<path d="M0 60V20H14V10H26V20H54V10H66V20H80V60H48V38A8 8 0 0 0 32 38V60Z"/>'],
    Ahmedabad: [90, 70, '<rect x="10" y="40" width="70" height="30"/><path d="M28 40A17 17 0 0 1 62 40Z"/><rect x="4" y="10" width="6" height="60"/><rect x="80" y="10" width="6" height="60"/><circle cx="7" cy="10" r="4"/><circle cx="83" cy="10" r="4"/>'],
    Chandigarh: [60, 70, '<rect x="28" y="38" width="4" height="32"/><path d="M18 40L14 14 20 14 22 30 24 8 30 8 31 28 34 6 40 6 39 30 44 14 50 16 44 40Z"/>'],
    Kochi: [80, 60, '<path class="st" d="M5 60L40 10 75 60M40 10V60M20 38Q40 30 60 38M12 50Q40 40 68 50"/>'],
    Jaipur: [80, 70, '<path d="M0 70V40H8V30H16V20H24V10H56V20H64V30H72V40H80V70Z"/>'],
    Lucknow: [80, 70, '<path d="M0 70V20H10V8H70V20H80V70H56V40A16 16 0 0 0 24 40V70Z"/><path d="M34 8A6 6 0 0 1 46 8Z"/>'],
    Indore: [80, 70, '<path d="M0 70V30H6V22H74V30H80V70Z"/><rect x="14" y="14" width="52" height="8"/><rect x="24" y="6" width="32" height="8"/>'],
    Kolkata: [170, 70, '<rect x="20" width="8" height="70"/><rect x="142" width="8" height="70"/><path class="st" d="M0 50L24 4 85 34 146 4 170 50M0 50H170M24 4V50M146 4V50M54 19V50M85 34V50M116 19V50M24 50L54 19 85 50 116 19 146 50"/>'],
  };

  // Seeded random so each locality always draws the same skyline.
  const rng = (seed) => () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
  const hash = (s) => [...s].reduce((h, c) => (h * 31 + c.charCodeAt(0)) % 2147483647, 7);

  function skyline(loc) {
    const r = rng(hash(loc)), out = [];
    const tower = (x, w, h) => {
      let win = "";
      for (let wy = GROUND - h + 8; wy < GROUND - 10; wy += 12)
        for (let wx = x + 5; wx < x + w - 6; wx += 9) if (r() > 0.55) win += `<rect class="wn" x="${wx}" y="${wy}" width="4" height="5"/>`;
      return `<rect x="${x}" y="${GROUND - h}" width="${w}" height="${h}"/>${win}`;
    };
    const house = (x, w, h) => `<rect x="${x}" y="${GROUND - h}" width="${w}" height="${h}"/><path d="M${x - 3} ${GROUND - h}L${x + w / 2} ${GROUND - h - 12}L${x + w + 3} ${GROUND - h}Z"/>`;
    const tree = (x, s) => `<circle class="ft" cx="${x}" cy="${GROUND - 14 * s}" r="${11 * s}"/>`;
    if (loc === "City Centre") for (let x = 0; x < W;) { const w = 26 + r() * 26; out.push(tower(x, w, 110 + r() * 80)); x += w + 3 + r() * 5; }
    else if (loc === "Prime Suburb") for (let x = 0; x < W;) { const w = 28 + r() * 22; out.push(tower(x, w, 60 + r() * 60)); x += w + 8 + r() * 14; }
    else if (loc === "Premium Township") for (let x = 10; x < W; x += 92) out.push(tower(x, 44, 128), tree(x + 68, 1.2));
    else if (loc === "Suburb") for (let x = 0; x < W;) { const w = 30 + r() * 20; out.push(r() > 0.3 ? house(x, w, 22 + r() * 30) : tower(x, w, 60 + r() * 30)); if (r() > 0.5) out.push(tree(x + w + 10, 0.9)); x += w + 18 + r() * 18; }
    else if (loc === "Gated Community") for (let x = 0; x < W;) { const w = 34 + r() * 10; out.push(house(x, w, 30 + r() * 10), tree(x + w + 12, 0.8)); x += w + 34; }
    else if (loc === "Near Metro") {
      for (let x = 0; x < W;) { const w = 26 + r() * 24; out.push(tower(x, w, 80 + r() * 70)); x += w + 10 + r() * 12; }
      out.push(`<rect x="0" y="${GROUND - 46}" width="${W}" height="7"/>`); // the elevated line
      for (let x = 40; x < W; x += 120) out.push(`<rect x="${x}" y="${GROUND - 40}" width="6" height="40"/>`);
    }
    else if (loc === "Waterfront") {
      for (let x = 0; x < W;) { const w = 24 + r() * 20; out.push(tower(x, w, 70 + r() * 70)); x += w + 16 + r() * 16; }
      out.push(`<path class="wv" d="M0 ${GROUND - 8}q20 -6 40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0t40 0"/>`);
    }
    else { out.push(`<path d="M0 ${GROUND}C120 ${GROUND - 70} 260 ${GROUND - 40} 380 ${GROUND - 10}S640 ${GROUND - 90} ${W} ${GROUND - 30}V${GROUND}Z"/>`);
      for (let x = 30; x < W; x += 110 + r() * 60) out.push(tree(x, 0.8 + r() * 0.5)); }
    return out.join("");
  }

  let svg, layers, first = true;
  function init(el) {
    svg = el;
    svg.innerHTML = '<rect class="sky" width="800" height="266"/>'
      + ["far", "ground", "rooms", "rugs", "furniture", "shell", "front", "annot"].map((n) => `<g data-layer="${n}"></g>`).join("");
    layers = Object.fromEntries([...svg.querySelectorAll("[data-layer]")].map((g) => [g.dataset.layer, { g, map: new Map() }]));
  }

  // Reconcile one layer: move what stays, animate in what is new, fade out what is gone.
  function sync(name, nodes) {
    const layer = layers[name], seen = new Set();
    for (const n of nodes) {
      seen.add(n.key);
      let el = layer.map.get(n.key);
      const t = `translate(${n.x}px, ${n.y}px) scale(${n.sx ?? n.s ?? 1}, ${n.sy ?? n.s ?? 1})`;
      if (!el) {
        el = document.createElementNS(NS, "g");
        el.style.transform = t;
        el.innerHTML = `<g class="in ${n.anim || "drop"}">${n.html}</g>`;
        el.firstChild.style.animationDelay = (first ? n.delay || 0 : 0) + "ms";
        if (n.anim === "draw") pen(el.firstChild);
        layer.g.append(el);
        layer.map.set(n.key, el);
      } else {
        el.style.transform = t;
        if (el._html !== n.html) el.firstChild.innerHTML = n.html;
      }
      el._html = n.html;
      el.classList.toggle("ghost", !!n.ghost);
    }
    for (const [k, el] of layer.map) if (!seen.has(k)) {
      layer.map.delete(k);
      el.classList.add("gone");
      setTimeout(() => el.remove(), 400);
    }
  }

  let last;
  narrow.addEventListener("change", () => last && paint(last));
  function paint(p) {
    last = p;
    const kind = p.property_type, floors = p.stories;
    const tower = kind === "Apartment" || kind === "Studio" || kind === "Penthouse";
    const below = tower ? (kind === "Penthouse" ? 2 : 1) : 0;          // stilt parking, and flats under a penthouse
    const above = kind === "Apartment" || kind === "Studio" ? 1 : 0;     // the flat upstairs
    const levels = below + floors + above;
    const bw = Math.round(Math.min(Math.max(250 + 2.4 * Math.sqrt(p.area), 290), 480));
    const x0 = kind === "Row House" ? 110 : 70, iw = bw - 12, roofY = GROUND - levels * FLOOR;
    const surface = (i) => GROUND - (i + below) * FLOOR - SLAB, ceiling = (i) => GROUND - (i + below + 1) * FLOOR;
    const kindText = kind === "Studio" ? "Studio" : `${p.bedrooms} BHK ${kind.toLowerCase()}`;

    // Share rooms across the home's floors: living and kitchen on its lowest, the rest wherever there is least.
    const plan = Array.from({ length: floors }, () => []), load = Array(floors).fill(0);
    const firstRooms = kind === "Studio" ? [{ t: "studio", k: "studio" }] : [{ t: "living", k: "living" }, { t: "kitchen", k: "kitchen" }];
    plan[0].push(...firstRooms);
    load[0] = firstRooms.reduce((w, r) => w + ROOMS[r.t].w, 0);
    const queue = [];
    for (let i = 1; i <= Math.max(p.bedrooms, p.bathrooms); i++) {
      if (i <= p.bedrooms && kind !== "Studio") queue.push({ t: "bed", k: "bed-" + i });
      if (i <= p.bathrooms) queue.push({ t: "bath", k: "bath-" + i });
    }
    for (const room of queue) {
      let best = floors - 1;
      for (let f = floors - 1; f >= 0; f--) if (load[f] < load[best]) best = f;
      plan[best].push(room);
      load[best] += ROOMS[room.t].w;
    }

    const rooms = [], parts = [], rugs = [], furniture = [], labels = [];
    let n = 0;
    plan.forEach((list, f) => {
      let x = x0 + 6;
      list.forEach((room, j) => {
        const rw = (iw * ROOMS[room.t].w) / load[f], floorY = surface(f);
        rooms.push({ key: "room-" + room.k, x, y: ceiling(f), sx: rw, sy: CLEAR, anim: "rise", delay: (f + below) * 140,
          html: `<rect class="${room.t === "bath" ? "tile" : "room"}" width="1" height="1"/>` });
        const name = NAMES[room.t](room.k);
        if (rw > name.length * 4.4 + 10) // a label only where its room can hold it
          labels.push({ key: "label-" + room.k, x: x + 4, y: ceiling(f) + 9, anim: "fade", delay: 420,
            html: `<text class="tag">${name}</text>` });
        if (j < list.length - 1) parts.push({ key: "part-" + room.k, x: x + rw - 1.5, y: ceiling(f), anim: "rise", delay: (f + below) * 140,
          html: '<rect class="ct" width="3" height="15"/>' });
        const items = ROOMS[room.t][p.furnishing_status];
        const total = items.reduce((s, it) => s + F[it][0], 0) + 6 * (items.length - 1);
        const tallest = Math.max(...items.map((it) => F[it][1]));
        const s = Math.min(1, (rw - 10) / total, (CLEAR - LABEL) / tallest), gap = (rw - total * s) / 2; // clear the label band
        let ix = x + gap;
        for (const it of items) {
          const [w, h, html] = F[it];
          const ghost = p.furnishing_status === "unfurnished" && LOOSE.has(it);
          const node = { key: `${room.k}:${it}`, x: ix, y: floorY - h * s, s, html, ghost, anim: ghost ? "fade" : "draw",
            delay: 420 + Math.min(n++ * 35, 900) }; // the whole house is inked within about 1.3s
          furniture.push(node);
          if (it === "sofa" && p.furnishing_status === "furnished")
            rugs.push({ key: room.k + ":rug", x: ix + (w * s - F.rug[0] * s) / 2, y: floorY - 3 * s, s, html: F.rug[2], anim: "draw", delay: node.delay });
          ix += (w + 6) * s;
        }
        x += rw;
      });
    });

    // the rest of the building: other flats, stilt parking, a row's neighbours
    const others = [];
    for (let L = 0; L < levels; L++) {
      const mine = L >= below && L < below + floors;
      if (mine || (tower && L === 0)) continue;
      others.push({ key: "nb-" + L, x: x0 + 6, y: GROUND - (L + 1) * FLOOR, sx: iw, sy: CLEAR, anim: "rise", delay: L * 140,
        html: '<rect class="nbr" width="1" height="1"/>' });
      labels.push({ key: "nblabel-" + L, x: x0 + 10, y: GROUND - (L + 1) * FLOOR + 9, anim: "fade", delay: 420, html: '<text class="tag">OTHER FLATS</text>' });
    }
    if (tower) {
      let cols = "";
      for (let cx = 6; cx <= bw - 10; cx += Math.max(80, (bw - 16) / 4)) cols += `<rect class="ct" x="${cx}" y="0" width="4" height="${CLEAR}"/>`;
      others.push({ key: "stilt", x: x0, y: GROUND - FLOOR, anim: "rise", html: cols + `<rect class="ct" x="${bw - 10}" y="0" width="4" height="${CLEAR}"/>` });
      labels.push({ key: "stiltlabel", x: x0 + 14, y: GROUND - FLOOR + 9, anim: "fade", delay: 420, html: '<text class="tag">STILT PARKING</text>' });
    }
    if (kind === "Row House")
      for (const [key, nx] of [["row-l", x0 - 58], ["row-r", x0 + bw + 6]]) {
        others.push({ key, x: nx, y: GROUND - floors * FLOOR, sx: 52, sy: floors * FLOOR, anim: "rise", html: '<rect class="nbr" width="1" height="1"/>' });
        labels.push({ key: key + "-label", x: nx + 4, y: GROUND - floors * FLOOR + 9, anim: "fade", delay: 420, html: '<text class="tag">NEIGHBOUR</text>' });
      }

    const carX = tower ? x0 + 24 : x0 + bw + (kind === "Row House" ? 74 : 16);
    const cars = Array.from({ length: p.parking }, (_, j) => ({
      key: "car-" + j, x: carX + j * 70, y: GROUND - 25, html: F.car[2].replace('class="cb"', `class="cb c${j}"`),
      anim: "roll", delay: 900 + j * 140 }));

    const year = new Date().getFullYear() - p.house_age;
    const [mw, mh, mark] = MARKS[p.city];
    sync("far", [
      { key: "sky-" + p.location, x: 0, y: 0, html: `<g class="far">${skyline(p.location)}</g>`, anim: "fade" },
      { key: "mark-" + p.city, x: 790 - mw, y: GROUND - mh - 4, html: `<g class="lm">${mark}</g>`, anim: "fade" },
    ]);
    sync("ground", [p.main_road === "yes"
      ? { key: "road", x: 0, y: GROUND, anim: "fade", html: '<rect class="kerb" width="800" height="5"/><rect class="road" y="5" width="800" height="29"/><path class="lane" d="M0 20H800"/>' }
      : { key: "lane", x: 0, y: GROUND, anim: "fade", html: '<rect class="grass" width="800" height="34"/><rect class="path" y="12" width="800" height="8"/>' }]);
    sync("rooms", [...others, ...rooms, ...parts]);
    sync("rugs", rugs);
    sync("furniture", furniture);
    const pitch = kind === "Villa" ? 34 : 0;
    sync("shell", [
      ...Array.from({ length: levels + 1 }, (_, i) => ({ key: "slab-" + i, x: x0, y: GROUND - i * FLOOR - SLAB, sx: bw, anim: "rise", delay: i * 140,
        html: `<rect class="ct" width="1" height="${SLAB}"/>` })),
      { key: "wall-l", x: x0, y: roofY, sy: levels * FLOOR, html: '<rect class="ct" width="6" height="1"/>', anim: "rise" },
      { key: "wall-r", x: x0 + bw - 6, y: roofY, sy: levels * FLOOR, html: '<rect class="ct" width="6" height="1"/>', anim: "rise" },
      { key: "roof", x: x0 - 5, y: roofY - 14, sx: bw + 10, html: '<rect class="ct" width="1" height="14"/>', anim: "rise", delay: levels * 140 },
      ...(pitch ? [{ key: "pitch", x: x0 - 12, y: roofY - 14, anim: "rise", delay: levels * 140 + 100,
        html: `<path class="ct" d="M0 0L${(bw + 24) / 2} -${pitch}L${bw + 24} 0Z"/>` }] : []),
      ...(kind === "Penthouse" ? [{ key: "terrace", x: x0, y: roofY - 14, anim: "fade", delay: levels * 140 + 100,
        html: `<path class="rail" d="${Array.from({ length: 9 }, (_, i) => `M${bw * 0.55 + i * bw * 0.45 / 8} 0V-12`).join("")}M${bw * 0.55} -12H${bw}"/>` }] : []),
    ]);
    sync("front", [...(kind === "Row House" ? [] : [{ key: "tree", x: 0, y: GROUND - 60, html: F.tree[2], anim: "rise", delay: 200 }]), ...cars]);

    // frame: the full sheet on wide screens; on a phone, just the building and its parking so the furniture reads
    const lift = pitch + (kind === "Penthouse" ? 14 : 0);
    const top = narrow.matches ? roofY - 140 - lift : Math.min(roofY - 70 - lift, 120); // phone: headroom for the enlarged title
    const left = narrow.matches ? (kind === "Row House" ? x0 - 64 : 34) : 0;
    const right = narrow.matches ? Math.max(x0 + bw + (kind === "Row House" ? 64 : 12), p.parking && !tower ? carX + p.parking * 70 : 0) : W;
    svg.setAttribute("viewBox", `${left} ${top} ${right - left} ${300 - top}`);

    // drafting: level datums, the built-up area as a dimension string, room labels, a title block
    const datums = Array.from({ length: levels + 1 }, (_, i) => ({
      key: "datum-" + i, x: x0 - (kind === "Row House" ? 64 : 6), y: GROUND - i * FLOOR - SLAB, anim: "fade", delay: 300 + i * 140,
      html: `<g class="datum"><path class="dim" d="M0 0H-4M-4 0L-7 -4H-1Z"/><text class="lvl" x="-9" y="2" text-anchor="end">${i ? "+" + (i * 3).toFixed(2) : "±0.00"}</text></g>` }));
    const dimY = roofY - lift - (narrow.matches ? 34 : 22);
    const dimension = { key: "dimension", x: x0, y: dimY, anim: "fade", delay: levels * 140 + 200,
      html: `<path class="dim" d="M0 0H${bw}M0 -4V4M${bw} -4V${4}"/><text class="lvl" x="${bw / 2}" y="-3" text-anchor="middle">${p.area.toLocaleString("en-IN")} sq ft built-up</text>` };
    const k = narrow.matches ? 2.3 : 1; // the phone crop shrinks the sheet; set its words big enough to read
    const title = { key: "title", x: right - 8, y: top + 14 * k, anim: "fade",
      html: `<text class="ttl" text-anchor="end">SECTION A–A</text>`
        + `<text class="lvl" y="${11 * k}" text-anchor="end">${kindText} · ${floors} floor${floors > 1 ? "s" : ""} · ${p.house_age === 0 ? "new build" : "built " + year}</text>`
        + `<text class="lvl" y="${21 * k}" text-anchor="end">Schematic, not to scale</text>` };
    sync("annot", [...labels, ...datums, dimension, title]);

    svg.setAttribute("aria-label", `Illustration: a ${kindText.toLowerCase()}, ${floors} floor${floors > 1 ? "s" : ""}, with ${p.bathrooms} `
      + `bathroom${p.bathrooms > 1 ? "s" : ""}, ${p.furnishing_status}, ${p.parking} parking spot${p.parking === 1 ? "" : "s"}, `
      + `${p.main_road === "yes" ? "on a main road" : "off the main road"} in ${p.location}, ${p.city}; built ${p.house_age === 0 ? "new" : "in " + year}.`);
    first = false;
  }

  return { init, paint };
})();
