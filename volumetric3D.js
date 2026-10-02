// =====================================================================
// Afficheur volumétrique à persistance rétinienne — panneaux de LED
//
// - 10 panneaux de 180 × 8 LED au pas de 1 cm (bande de 180 cm × 8 cm),
//   posés à plat dans le plan de leur tranche et centrés sur l'axe Z.
// - Les 8 rangées d'un panneau sont parallèles, décalées de 1 cm :
//   l'axe Z passe entre les rangées 4 et 5 et entre les colonnes 90 et 91.
// - Les panneaux sont alignés en enfilade le long de Z (panneau 1 devant).
// - Chaque panneau est décalé de 180° / 10 = 18° par rapport au précédent :
//   les 20 demi-bandes sont réparties régulièrement, tous les 18°.
// - Tous les panneaux tournent ensemble autour de Z.
// - Chaque panneau affiche sa propre tranche d'un volume 3D.
//
// Sources possibles du volume :
// - « Cube fixe » : un cube rouge en fil de fer, centré.
// - « Animation cube_animatio » : la séquence de 300 cubes 3D retrouvés dans les images
//   du dossier cube_animatio (poses dans poses_cube_animatio.js).
// - « Images chargées » : des images choisies sur l'ordinateur, 10 par volume.
// =====================================================================

const SOURCES = ['Cube fixe', 'Animation cube_animatio', 'Images chargées'];

let images = [];          // images chargées (100x100) : 10 images consécutives = 1 volume
let currentVolume = 0;    // volume d'images affiché
let volumeCount = 0;
let imagesLoaded = false;
let isSimulating = false;
let lastFrameTime = 0;
let lastAnimationTime = 0;
let rotationAngle = 0;
let sourceLabel = 'cube';
let voxels = [];          // LED allumées, à leur position dans le volume
let drawnVoxels = [];     // celles qui sont dessinées à l'écran (au plus MAX_DRAWN)
let gui;
let overGui = false;      // évite que la vue 3D tourne quand on clique sur les réglages
const TARGET_SIZE = 100;  // taille des images chargées
const TOTAL_FRAMES = 300; // nombre maximum d'images chargées
const MAX_DRAWN = 60000;  // au-delà, on n'affiche qu'une partie des LED (fluidité)
let infoDiv;              // ligne d'information affichée en bas de l'aperçu
let lastProcessMs = 0;    // durée du dernier calcul de volume (ms)

let params = {
  source: 'Animation cube_animatio',
  frame: 0,               // image de l'animation cube_animatio affichée (0 à 299)
  fps: 30,                // images par seconde de l'animation
  numPanels: 10,          // nombre de panneaux = nombre de tranches
  ledsPerRow: 180,        // colonnes : LED par rangée
  rowsPerPanel: 8,        // rangées par panneau
  ledPitch: 1,            // cm entre deux LED d'une rangée
  rowPitch: 1,            // cm entre deux rangées
  panelGap: 10,           // cm entre deux panneaux (profondeur)
  edgeHalf: 4,            // demi-épaisseur des arêtes des cubes (cm)
  numRefresh: 180,        // rafraîchissements par tour (360° / 180 = 2° entre deux)
  toursParSeconde: 2,     // vitesse de rotation de la simulation
  persistence: 0.3,       // durée de persistance simulée de l'œil (s)
  ledSize: 1.5,           // taille d'affichage d'une LED (cm)
  seuil: 40,              // pixel d'image plus sombre que ce seuil = LED éteinte
  reset: function() { processVolume(); }
};

// ---------- Outils ----------

// Suite 0, 1, ..., n − 1. Les longues boucles du sketch sont écrites en « for...of » sur ces suites :
// l'éditeur p5 coupe les boucles « for (;;) » qui durent plus de 100 ms (il croit à une boucle infinie).
const seqCache = new Map();
function seq(n) {
  let a = seqCache.get(n);
  if (!a) { a = Array.from({ length: n }, (_, i) => i); seqCache.set(n, a); }
  return a;
}

// ---------- Géométrie ----------

// Demi-longueur d'un panneau (cm) : 89,5 cm pour 180 LED à 1 cm
function halfLength() {
  return (params.ledsPerRow - 1) / 2 * params.ledPitch;
}

// Demi-largeur d'un panneau (cm), jusqu'au centre des rangées extrêmes : 3,5 cm pour 8 rangées
function halfWidth() {
  return (params.rowsPerPanel - 1) / 2 * params.rowPitch;
}

// Décalage angulaire du panneau s : 180° / nombre de panneaux
// (un panneau centré a deux demi-bandes, donc 10 panneaux → 20 demi-bandes tous les 18°)
function panelOffset(s) {
  return s * PI / params.numPanels;
}

// Profondeur du panneau s : panneau 0 devant (z positif, côté spectateur)
function panelZ(s) {
  return ((params.numPanels - 1) / 2 - s) * params.panelGap;
}

// Position de la colonne k le long du panneau (cm) : négative = première demi-bande
function ledDist(k) {
  return (k - (params.ledsPerRow - 1) / 2) * params.ledPitch;
}

// Décalage de la rangée j par rapport à l'axe (cm), perpendiculairement au panneau
function rowOffset(j) {
  return (j - (params.rowsPerPanel - 1) / 2) * params.rowPitch;
}

// Profondeur maximale disponible de part et d'autre du centre (cm)
function zMax() {
  return (params.numPanels - 1) / 2 * params.panelGap;
}

// ---------- Interface ----------

function setup() {
  createCanvas(windowWidth, windowHeight, WEBGL);
  // Premier dessin hors boucle : la compilation des shaders WebGL est lente
  // et ne doit pas se faire dans une boucle (sinon l'éditeur croit à une boucle infinie)
  push();
  stroke(0);
  line(0, 0, 0, 0, 0, 1);
  noStroke();
  fill(0);
  box(0.01);
  stroke(0);
  strokeWeight(1);
  beginShape(POINTS);
  vertex(0, 0, 0);
  endShape();
  pop();

  if (!hasAnimation()) {
    console.warn("poses_cube_animatio.js introuvable : l'animation cube_animatio est indisponible");
    params.source = 'Cube fixe';
  }

  gui = new dat.GUI({ autoPlace: false });
  gui.domElement.id = 'gui';
  document.body.appendChild(gui.domElement);
  gui.domElement.addEventListener('mouseenter', () => overGui = true);
  gui.domElement.addEventListener('mouseleave', () => overGui = false);

  gui.add(params, 'source', SOURCES).name('Source').onChange(() => { currentVolume = 0; processVolume(); });
  gui.add(params, 'frame', 0, 299, 1).name('Image n°').listen().onChange(() => processVolume(true));
  gui.add(params, 'fps', 1, 60, 1).name('Images/s');
  gui.add(params, 'edgeHalf', 1, 10, 0.5).name('Demi-épaisseur arêtes (cm)').onChange(params.reset);
  gui.add(params, 'numPanels', 2, 20, 1).name('Panneaux').onChange(params.reset);
  gui.add(params, 'ledsPerRow', 30, 300, 1).name('LED/rangée').onChange(params.reset);
  gui.add(params, 'rowsPerPanel', 1, 16, 1).name('Rangées').onChange(params.reset);
  gui.add(params, 'ledPitch', 0.5, 3, 0.1).name('Pas LED (cm)').onChange(params.reset);
  gui.add(params, 'rowPitch', 0.5, 3, 0.1).name('Pas rangées (cm)').onChange(params.reset);
  gui.add(params, 'panelGap', 1, 30, 1).name('Écart panneaux (cm)').onChange(params.reset);
  gui.add(params, 'numRefresh', 20, 720, 2).name('Rafraîch./tour').onChange(params.reset);
  gui.add(params, 'toursParSeconde', 0.5, 20, 0.5).name('Tours/s');
  gui.add(params, 'persistence', 0.02, 1, 0.01).name('Persistance (s)');
  gui.add(params, 'ledSize', 0.5, 5, 0.5).name('Taille LED');
  gui.add(params, 'seuil', 0, 255, 1).name('Seuil images').onChange(params.reset);
  gui.add(params, 'reset').name('Réinitialiser');

  createLoadButton();
  createSimButton();
  createExportButton();
  createExportAnimationButton();

  infoDiv = createDiv('');
  infoDiv.position(10, 135);
  infoDiv.style('color', '#ccc');
  infoDiv.style('font', '12px sans-serif');
  infoDiv.style('pointer-events', 'none');

  processVolume(); // volume prêt dès le démarrage
  lastFrameTime = millis();
}

// Les boutons p5 ne doivent pas non plus faire tourner la vue
function protectFromOrbit(btn) {
  btn.mouseOver(() => overGui = true);
  btn.mouseOut(() => overGui = false);
}

function createLoadButton() {
  const loadButton = createButton('Charger des images (10 par volume)');
  loadButton.position(10, 10);
  protectFromOrbit(loadButton);
  loadButton.mousePressed(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.multiple = true;
    input.style.display = 'none';
    input.addEventListener('change', (e) => handleFileInput(e.target.files));
    document.body.appendChild(input);
    input.click();
  });
}

function createSimButton() {
  const simButton = createButton('Démarrer la simulation');
  simButton.position(10, 40);
  protectFromOrbit(simButton);
  simButton.mousePressed(() => {
    isSimulating = !isSimulating;
    simButton.html(isSimulating ? 'Arrêter la simulation' : 'Démarrer la simulation');
    lastFrameTime = millis();
    lastAnimationTime = millis();
  });
}

function createExportButton() {
  const exportButton = createButton('Exporter le volume affiché (.bin)');
  exportButton.position(10, 70);
  protectFromOrbit(exportButton);
  exportButton.mousePressed(exportBinaryData);
}

function createExportAnimationButton() {
  const btn = createButton("Exporter l'animation (.json)");
  btn.position(10, 100);
  protectFromOrbit(btn);
  btn.mousePressed(exportAnimationJSON);
}

// ---------- Chargement des images ----------

// Les images sont regroupées par paquets de [nombre de panneaux] :
// image 1 → panneau 1, image 2 → panneau 2... puis le volume suivant.
function handleFileInput(files) {
  if (!files || files.length === 0) {
    console.log("Aucun fichier sélectionné");
    return;
  }
  const list = Array.from(files).filter(f => f.type.startsWith('image/')).slice(0, TOTAL_FRAMES);
  if (list.length === 0) {
    console.warn("Aucune image dans la sélection");
    return;
  }

  console.log(`Chargement de ${list.length} images (${TARGET_SIZE}x${TARGET_SIZE})...`);
  imagesLoaded = false;
  images = new Array(list.length);
  let loadedCount = 0;

  list.forEach((file, i) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const tempImg = new Image();
      tempImg.onload = () => {
        const resized = createGraphics(TARGET_SIZE, TARGET_SIZE);
        // Dessin direct sur le canvas (image() de p5 n'accepte pas une image HTML brute)
        resized.drawingContext.drawImage(tempImg, 0, 0, TARGET_SIZE, TARGET_SIZE);
        images[i] = resized;
        loadedCount++;
        if (loadedCount === list.length) {
          imagesLoaded = true;
          currentVolume = 0;
          console.log(`${list.length} images chargées → ${Math.ceil(list.length / params.numPanels)} volume(s). Choisis la source « Images chargées ».`);
          if (params.source === 'Images chargées') processVolume();
        }
      };
      tempImg.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

// ---------- Animation cube_animatio ----------

function hasAnimation() {
  return typeof CUBE_POSES !== 'undefined' && CUBE_POSES.length > 0;
}

// Échelle de l'animation (cm par demi-largeur d'image) : la plus grande possible
// pour que tous les cubes de la séquence, quelle que soit leur rotation, tiennent dans le volume
function animationScale() {
  const w = params.edgeHalf, zm = zMax(), rm = halfLength();
  let L = Infinity;
  for (const p of CUBE_POSES) {
    const reach = p[2] * Math.sqrt(3);            // demi-diagonale du cube
    L = Math.min(L, (zm - w) / reach, (rm - w) / (Math.hypot(p[0], p[1]) + reach));
  }
  return Math.max(0, L);
}

// Pose d'une image de l'animation dans le volume : centre (cm), demi-côté (cm), rotation
function animationPose(k, L) {
  const p = CUBE_POSES[k];
  const [x, y, z, w] = [p[3], p[4], p[5], p[6]];
  const R = [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
             2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
             2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)];
  // La caméra regarde vers le fond (z vers le fond), le volume a z vers le spectateur :
  // on retourne l'axe z (les termes qui croisent z changent de signe)
  R[2] = -R[2]; R[5] = -R[5]; R[6] = -R[6]; R[7] = -R[7];
  return { cx: L * p[0], cy: L * p[1], cz: 0, h: L * p[2], R: R, interpolated: p[7] === 1 };
}

// Distance (dans le repère du cube, demi-côté = 1) d'un point aux 12 arêtes du cube
function cubeEdgeDistance(X, Y, Z) {
  X = Math.abs(X); Y = Math.abs(Y); Z = Math.abs(Z);
  const dx = X - 1, dy = Y - 1, dz = Z - 1;
  const ex = Math.max(0, dx), ey = Math.max(0, dy), ez = Math.max(0, dz);
  return Math.sqrt(Math.min(ex * ex + dy * dy + dz * dz,
                            dx * dx + ey * ey + dz * dz,
                            dx * dx + dy * dy + ez * ez));
}

// ---------- Contenu du volume ----------

// Renvoie une fonction (panneau, x, y, z) → [r, g, b] ou null si la LED est éteinte
function makeSampler() {
  const H = Math.hypot(halfLength(), halfWidth()); // rayon du disque balayé (coins compris)

  if (params.source === 'Images chargées' && imagesLoaded && images.length > 0) {
    volumeCount = Math.ceil(images.length / params.numPanels);
    currentVolume = currentVolume % volumeCount;
    const slices = [];
    for (let s = 0; s < params.numPanels; s++) {
      const im = images[currentVolume * params.numPanels + s];
      if (!im) { slices.push(null); continue; }
      im.loadPixels();
      const d = Math.round(Math.sqrt(im.pixels.length / (4 * im.width * im.height)));
      slices.push({ px: im.pixels, w: im.width, h: im.height, d: d, rowWidth: im.width * d });
    }
    sourceLabel = `volume d'images ${currentVolume + 1}/${volumeCount}`;
    // L'image couvre le disque balayé par le panneau
    return (s, x, y) => {
      const sl = slices[s];
      if (!sl) return null;
      const u = Math.floor((x + H) / (2 * H) * sl.w);
      const v = Math.floor((y + H) / (2 * H) * sl.h);
      if (u < 0 || u >= sl.w || v < 0 || v >= sl.h) return null;
      const i = 4 * (v * sl.d * sl.rowWidth + u * sl.d);
      const r = sl.px[i], g = sl.px[i + 1], b = sl.px[i + 2];
      return Math.max(r, g, b) < params.seuil ? null : [r, g, b];
    };
  }

  const w = params.edgeHalf;
  const red = [255, 0, 0];

  if (params.source === 'Animation cube_animatio' && hasAnimation()) {
    // Cube 3D retrouvé dans l'image n° params.frame, tourné et placé comme sur l'image
    const k = Math.round(params.frame) % CUBE_POSES.length;
    const P = animationPose(k, animationScale());
    const R = P.R, h = P.h, reach2 = Math.pow(h * Math.sqrt(3) + w, 2);
    sourceLabel = `cube_animatio image ${k}${P.interpolated ? ' (interpolée)' : ''}`;
    return (s, x, y, z) => {
      const dx = x - P.cx, dy = y - P.cy, dz = z - P.cz;
      if (dx * dx + dy * dy + dz * dz > reach2) return null;   // loin du cube : éteinte
      // Coordonnées dans le repère du cube (transposée de R), demi-côté ramené à 1
      const X = (R[0] * dx + R[3] * dy + R[6] * dz) / h;
      const Y = (R[1] * dx + R[4] * dy + R[7] * dz) / h;
      const Z = (R[2] * dx + R[5] * dy + R[8] * dz) / h;
      return cubeEdgeDistance(X, Y, Z) * h <= w ? red : null;
    };
  }

  // Cube fixe en vrai 3D, centré, qui tient dans le disque et dans la profondeur :
  // ses faces avant et arrière tombent sur le premier et le dernier panneau.
  volumeCount = 1;
  sourceLabel = 'cube fixe';
  const a = Math.min(halfLength() / Math.SQRT2 * 0.95, zMax());   // demi-côté du cube (cm)
  return (s, x, y, z) => cubeEdgeDistance(x / a, y / a, z / a) * a <= w ? red : null;
}

// Calcule les LED allumées à leur position dans le volume (pour l'affichage).
// Un panneau centré se retrouve sur lui-même après un demi-tour (rangée j ↔ rangée 7 − j),
// donc un demi-tour de rafraîchissements suffit pour couvrir toute la tranche.
function processVolume(quiet) {
  const t0 = performance.now();
  const sampler = makeSampler();
  const R = params.numRefresh, S = params.numPanels, J = params.rowsPerPanel, N = params.ledsPerRow;
  const rMax = R % 2 === 0 ? R / 2 : R;
  voxels = [];
  for (const r of seq(rMax)) {
    const phi = TWO_PI * r / R;
    for (const s of seq(S)) {
      const ang = panelOffset(s) + phi;
      const c = Math.cos(ang), sn = Math.sin(ang), z = panelZ(s);
      for (const j of seq(J)) {
        const o = rowOffset(j);
        for (const k of seq(N)) {
          const d = ledDist(k);
          const x = d * c - o * sn, y = d * sn + o * c;
          const col = sampler(s, x, y, z);
          if (col) voxels.push({ x: x, y: y, z: z, r: col[0], g: col[1], b: col[2], phi: phi });
        }
      }
    }
  }
  // Pour l'affichage, au plus MAX_DRAWN LED (une sur « step »)
  const step = Math.max(1, Math.ceil(voxels.length / MAX_DRAWN));
  drawnVoxels = step === 1 ? voxels : voxels.filter((v, i) => i % step === 0);
  lastProcessMs = performance.now() - t0;
  if (infoDiv) {
    infoDiv.html(`${sourceLabel}<br>Pas angulaire : ${(360 / R).toFixed(1)}° (${R} rafraîchissements/tour)<br>` +
      `LED allumées : ${voxels.length.toLocaleString('fr-FR')} — affichées : ` +
      (step === 1 ? 'toutes' : `1 sur ${step}`) + `<br>Calcul : ${Math.round(lastProcessMs)} ms par image`);
  }
  if (!quiet) {
    if (voxels.length > MAX_DRAWN) {
      console.warn(`${voxels.length} LED allumées : affichage allégé (1 sur ${Math.ceil(voxels.length / MAX_DRAWN)})`);
    }
    console.log(`${sourceLabel} : ${voxels.length} LED allumées`);
  }
}

// ---------- Export ----------

// Données d'un volume pour un tour complet.
// Ordre : rafraîchissement → panneau → rangée → colonne → R, G, B
// Octet de départ = 3 × (((rafraîchissement × panneaux + panneau) × rangées + rangée) × colonnes + colonne)
function buildFrameData(sampler) {
  const R = params.numRefresh, S = params.numPanels, J = params.rowsPerPanel, N = params.ledsPerRow;
  const data = new Uint8Array(R * S * J * N * 3);
  let o3 = 0;
  for (const r of seq(R)) {
    const phi = TWO_PI * r / R;
    for (const s of seq(S)) {
      const ang = panelOffset(s) + phi;
      const c = Math.cos(ang), sn = Math.sin(ang), z = panelZ(s);
      for (const j of seq(J)) {
        const o = rowOffset(j);
        for (const k of seq(N)) {
          const d = ledDist(k);
          const col = sampler(s, d * c - o * sn, d * sn + o * c, z);
          if (col) {
            data[o3] = col[0];
            data[o3 + 1] = col[1];
            data[o3 + 2] = col[2];
          }
          o3 += 3;
        }
      }
    }
  }
  return data;
}

function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function downloadBinary(data, name) {
  downloadBlob(new Blob([data], { type: 'application/octet-stream' }), name);
}

// Volume affiché (ou tous les volumes d'images chargées)
function exportBinaryData() {
  if (params.source === 'Images chargées' && imagesLoaded && images.length > 0) {
    const saved = currentVolume;
    const count = Math.ceil(images.length / params.numPanels);
    console.log(`Export de ${count} volume(s)...`);
    for (const v of seq(count)) {
      currentVolume = v;
      downloadBinary(buildFrameData(makeSampler()), `volumetric3D_volume${v}.bin`);
    }
    currentVolume = saved;
    makeSampler();
    console.log("Export des volumes terminé");
  } else if (params.source === 'Animation cube_animatio' && hasAnimation()) {
    const k = Math.round(params.frame);
    downloadBinary(buildFrameData(makeSampler()), `volumetric3D_cube_animatio_${String(k).padStart(3, '0')}.bin`);
    console.log(`Image ${k} de l'animation exportée`);
  } else {
    downloadBinary(buildFrameData(makeSampler()), 'volumetric3D_cube.bin');
    console.log("Cube fixe exporté");
  }
}

// Toute l'animation sous forme de poses (300 volumes en binaire feraient plus de 2 Go).
// La carte peut recalculer chaque LED : allumée si sa distance aux arêtes du cube ≤ demi-épaisseur.
function exportAnimationJSON() {
  if (!hasAnimation()) {
    console.warn("Pas d'animation cube_animatio à exporter");
    return;
  }
  const L = animationScale();
  const frames = CUBE_POSES.map((p, k) => {
    const P = animationPose(k, L);
    const r4 = v => Math.round(v * 10000) / 10000;
    return { image: k, interpolee: P.interpolated, centre_cm: [r4(P.cx), r4(P.cy), r4(P.cz)], demi_cote_cm: r4(P.h), rotation: P.R.map(r4) };
  });
  const out = {
    description: "Animation cube_animatio pour l'afficheur volumétrique. Repère du volume : x à droite, y vers le bas, z vers le spectateur, en cm, origine au centre. Une LED est allumée (rouge) si sa distance aux 12 arêtes du cube est inférieure ou égale à demi_epaisseur_aretes_cm. Pour passer d'un point p du volume au repère du cube : q = transposée(rotation) × (p − centre) / demi_cote (rotation en ligne : r0 r1 r2 / r3 r4 r5 / r6 r7 r8).",
    images_par_seconde: params.fps,
    demi_epaisseur_aretes_cm: params.edgeHalf,
    panneaux: { nombre: params.numPanels, colonnes: params.ledsPerRow, rangees: params.rowsPerPanel, pas_led_cm: params.ledPitch, pas_rangees_cm: params.rowPitch, ecart_panneaux_cm: params.panelGap, decalage_deg: 180 / params.numPanels, rafraichissements_par_tour: params.numRefresh },
    images: frames
  };
  downloadBlob(new Blob([JSON.stringify(out, null, 1)], { type: 'application/json' }), 'cube_animatio_poses.json');
  console.log(`Animation exportée : ${frames.length} poses`);
}

// ---------- Simulation ----------

function draw() {
  background(0);
  if (!overGui) orbitControl();

  const now = millis();
  const dt = (now - lastFrameTime) / 1000;
  lastFrameTime = now;

  if (isSimulating) {
    // Rotation des panneaux : params.toursParSeconde tours par seconde
    rotationAngle = (rotationAngle + TWO_PI * params.toursParSeconde * dt) % TWO_PI;

    // Animation : image suivante au rythme choisi. Si le calcul d'une image est trop long,
    // l'animation ralentit d'elle-même pour que la page reste utilisable.
    if (now - lastAnimationTime > Math.max(1000 / params.fps, 2 * lastProcessMs)) {
      if (params.source === 'Animation cube_animatio' && hasAnimation()) {
        params.frame = (Math.round(params.frame) + 1) % CUBE_POSES.length;
        processVolume(true);
      } else if (params.source === 'Images chargées' && volumeCount > 1) {
        currentVolume = (currentVolume + 1) % volumeCount;
        processVolume(true);
      }
      lastAnimationTime = now;
    }
  }

  push();
  // Vue légèrement de biais pour voir le volume (la souris permet de tourner autour)
  rotateX(-0.35);
  rotateY(0.6);
  scale(Math.min(width, height) * 0.42 / halfLength());

  // Les panneaux (contour de la bande de 180 × 8), à leur angle actuel
  const L = halfLength() + params.ledPitch / 2;
  const W = halfWidth() + params.rowPitch / 2;
  strokeWeight(1);
  noFill();
  for (let s = 0; s < params.numPanels; s++) {
    const a = panelOffset(s) + rotationAngle;
    const c = Math.cos(a), sn = Math.sin(a), z = panelZ(s);
    stroke(s === 0 ? 120 : 60);
    beginShape();
    vertex(-L * c + W * sn, -L * sn - W * c, z);
    vertex( L * c + W * sn,  L * sn - W * c, z);
    vertex( L * c - W * sn,  L * sn + W * c, z);
    vertex(-L * c - W * sn, -L * sn + W * c, z);
    endShape(CLOSE);
  }

  // Les LED allumées, dessinées comme des points de « Taille LED » cm.
  // En simulation, chaque point s'éteint progressivement après le passage du panneau
  // (persistance rétinienne simulée). Les points de même couleur sont dessinés ensemble (plus rapide).
  const pxPerCm = Math.min(width, height) * 0.42 / halfLength();
  strokeWeight(Math.max(1.5, params.ledSize * pxPerCm));
  const persistAngle = TWO_PI * params.toursParSeconde * params.persistence;
  const groups = new Map();
  for (const v of drawnVoxels) {
    let b = 1;
    if (isSimulating) {
      let age = (rotationAngle - v.phi) % PI; // angle parcouru depuis le dernier passage d'une demi-bande
      if (age < 0) age += PI;
      b = 1 - age / persistAngle;
      if (b <= 0.03) continue;
    }
    // couleur arrondie (16 niveaux par composante) pour regrouper les points
    const key = (Math.round(v.r * b / 17) * 17 << 16) | (Math.round(v.g * b / 17) * 17 << 8) | (Math.round(v.b * b / 17) * 17);
    let list = groups.get(key);
    if (!list) { list = []; groups.set(key, list); }
    list.push(v);
  }
  for (const [key, list] of groups) {
    stroke((key >> 16) & 255, (key >> 8) & 255, key & 255);
    beginShape(POINTS);
    for (const v of list) vertex(v.x, v.y, v.z);
    endShape();
  }
  pop();
}

function windowResized() {
  resizeCanvas(windowWidth, windowHeight);
}
