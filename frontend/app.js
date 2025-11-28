const API_BASE = "http://127.0.0.1:8001";

window.addEventListener("DOMContentLoaded", () => {
  // Butonlar, seçimler
  const analyzeBtn = document.getElementById("analyzeBtn");
  const predictBtn = document.getElementById("predictBtn");
  const scenarioSelect = document.getElementById("scenarioSelect");

  // Analiz kartı
  const yesilOran = document.getElementById("yesilOran");
  const nufusYogunlugu = document.getElementById("nufusYogunlugu");
  const analizOneri = document.getElementById("analizOneri");
  const riskListe = document.getElementById("riskListe");
  const analyzeStatus = document.getElementById("analyzeStatus");
  const analyzeRaw = document.getElementById("analyzeRaw");

  // Tahmin kartı
  const konutIhtiyaci = document.getElementById("konutIhtiyaci");
  const ulasimArtis = document.getElementById("ulasimArtis");
  const tahminOneri = document.getElementById("tahminOneri");
  const predictStatus = document.getElementById("predictStatus");
  const predictRaw = document.getElementById("predictRaw");

  // Simülasyon kartı
  const simCurrentGreen = document.getElementById("simCurrentGreen");
  const greenSlider = document.getElementById("greenSlider");
  const simTargetGreen = document.getElementById("simTargetGreen");
  const simRiskChip = document.getElementById("simRiskChip");
  const simEffectText = document.getElementById("simEffectText");

  // Proje kaydetme
  const projectNameInput = document.getElementById("projectName");
  const saveProjectBtn = document.getElementById("saveProjectBtn");
  const projectList = document.getElementById("projectList");
  const projectStatus = document.getElementById("projectStatus");

  // AI Risk kartı
  const aiPopDensity = document.getElementById("aiPopDensity");
  const aiFlood = document.getElementById("aiFlood");
  const aiFloodLabel = document.getElementById("aiFloodLabel");
  const aiInfra = document.getElementById("aiInfra");
  const aiInfraLabel = document.getElementById("aiInfraLabel");
  const aiRiskBtn = document.getElementById("aiRiskBtn");
  const aiRiskScore = document.getElementById("aiRiskScore");
  const aiRiskLevel = document.getElementById("aiRiskLevel");
  const aiRiskExplanation = document.getElementById("aiRiskExplanation");

  // Grafik için
  const riskChartCanvas = document.getElementById("riskChart");
  let riskChart = null;

  // Heatmap butonu
  const heatToggleBtn = document.getElementById("heatToggleBtn");

  let lastBaseGreen = 18;

  // ---------------------------
  //  HARİTA / SENARYO BÖLGELERİ
  // ---------------------------

  const SCENARIOS = {
    merkez: {
      center: [41.015, 28.979],
      area: [
        [41.02, 28.96],
        [41.03, 28.99],
        [41.01, 29.01],
        [40.99, 28.99],
        [40.99, 28.96]
      ],
      label: "Yoğun Merkez Bölgesi (temsili)"
    },
    gelisen: {
      center: [40.99, 29.13],
      area: [
        [41.00, 29.10],
        [41.02, 29.14],
        [40.99, 29.18],
        [40.97, 29.15],
        [40.97, 29.11]
      ],
      label: "Gelişen Bölge (temsili)"
    },
    yesil: {
      center: [41.03, 28.95],
      area: [
        [41.05, 28.93],
        [41.06, 28.96],
        [41.04, 28.99],
        [41.02, 28.97],
        [41.02, 28.93]
      ],
      label: "Yeşil Odaklı Bölge (temsili)"
    }
  };

  function getScenarioColor(key) {
    if (key === "merkez") return "#ef4444";
    if (key === "gelisen") return "#eab308";
    if (key === "yesil") return "#22c55e";
    return "#3b82f6";
  }

  // Isı haritası için örnek yoğunluk noktaları (lat, lng, intensity)
  const HEAT_POINTS = {
    merkez: [
      [41.015, 28.979, 0.9],
      [41.02, 28.97, 0.8],
      [41.01, 28.99, 0.7],
      [41.00, 28.98, 0.6]
    ],
    gelisen: [
      [40.99, 29.13, 0.6],
      [41.00, 29.15, 0.7],
      [40.98, 29.16, 0.5],
      [40.97, 29.14, 0.4]
    ],
    yesil: [
      [41.03, 28.95, 0.3],
      [41.04, 28.96, 0.25],
      [41.02, 28.94, 0.2],
      [41.05, 28.97, 0.15]
    ]
  };

  const defaultScenario = "merkez";
  const defaultData = SCENARIOS[defaultScenario];

  let map = L.map("map").setView(defaultData.center, 11);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap katkıcıları"
  }).addTo(map);

  let scenarioMarker = L.marker(defaultData.center)
    .addTo(map)
    .bindPopup(defaultData.label)
    .openPopup();

  let scenarioPolygon = L.polygon(defaultData.area, {
    color: getScenarioColor(defaultScenario),
    weight: 2,
    fillColor: getScenarioColor(defaultScenario),
    fillOpacity: 0.25
  }).addTo(map);

  // GeoJSON katmanı + heat layer
  let geoLayer = null;
  let heatLayer = null;
  let heatOn = false;

  function updateHeatLayerForScenario(scenarioKey) {
    if (!window.L || !L.heatLayer) return;

    const points = HEAT_POINTS[scenarioKey] || [];
    if (!heatOn) {
      // Açık değilse hiç dokunma
      return;
    }

    if (!points.length) {
      if (heatLayer) {
        map.removeLayer(heatLayer);
        heatLayer = null;
      }
      return;
    }

    if (!heatLayer) {
      heatLayer = L.heatLayer(points, {
        radius: 25,
        blur: 15
      }).addTo(map);
    } else {
      heatLayer.setLatLngs(points);
    }
  }

  function loadGeoJsonLayer() {
    fetch("geo/scenarios.geojson")
      .then((res) => res.json())
      .then((data) => {
        if (geoLayer) {
          map.removeLayer(geoLayer);
        }
        geoLayer = L.geoJSON(data, {
          style: (feature) => {
            const scen = feature.properties?.scenario || "merkez";
            const color = getScenarioColor(scen);
            return {
              color,
              weight: 2,
              fillColor: color,
              fillOpacity: 0.15
            };
          },
          onEachFeature: (feature, layer) => {
            const name = feature.properties?.name || "Bölge";
            const scen = feature.properties?.scenario || "merkez";
            const risk = feature.properties?.risk || "-";

            // Popup yine kalsın
            layer.bindPopup(
              `<b>${name}</b><br/>Senaryo: ${scen}<br/>Risk: ${risk}`
            );

            // Poligona tıklayınca senaryoyu seç + analiz + tahmin
            layer.on("click", () => {
              scenarioSelect.value = scen;
              updateMapForScenario(scen);
              analyzeBtn.click();
              predictBtn.click();
            });
          }
        }).addTo(map);
      })
      .catch((err) => {
        console.error("GeoJSON yüklenirken hata:", err);
      });
  }

  function updateMapForScenario(scenarioKey) {
    const data = SCENARIOS[scenarioKey] || SCENARIOS[defaultScenario];
    const color = getScenarioColor(scenarioKey);

    scenarioMarker.setLatLng(data.center);
    scenarioMarker.bindPopup(data.label);

    scenarioPolygon.setLatLngs(data.area);
    scenarioPolygon.setStyle({
      color,
      fillColor: color
    });

    map.setView(data.center, 12);

    // Isı haritasını da güncelle
    updateHeatLayerForScenario(scenarioKey);
  }

  scenarioSelect.addEventListener("change", () => {
    updateMapForScenario(scenarioSelect.value);
  });

  // Isı haritası aç/kapat
  if (heatToggleBtn) {
    heatToggleBtn.addEventListener("click", () => {
      heatOn = !heatOn;
      if (!heatOn) {
        if (heatLayer) {
          map.removeLayer(heatLayer);
          heatLayer = null;
        }
        heatToggleBtn.textContent = "Isı Haritasını Aç/Kapat";
      } else {
        updateHeatLayerForScenario(scenarioSelect.value);
        heatToggleBtn.textContent = "Isı Haritasını Aç/Kapat";
      }
    });
  }

  // ---------------------------
  //  YARDIMCI FONKSİYONLAR
  // ---------------------------

  function parsePercent(str) {
    if (!str) return null;
    return parseInt(String(str).replace("%", "").trim(), 10);
  }

  // Grafik başlatma
  function initRiskChart() {
    if (!riskChartCanvas || !window.Chart) return;

    riskChart = new Chart(riskChartCanvas, {
      type: "line",
      data: {
        labels: ["Mevcut Yeşil (%)", "Hedef Yeşil (%)"],
        datasets: [
          {
            label: "Yeşil Alan Oranı",
            data: [lastBaseGreen, parseInt(greenSlider.value, 10)],
            tension: 0.3
          }
        ]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            max: 60
          }
        }
      }
    });
  }

  function updateRiskChart(current, target) {
    if (!riskChart) return;
    riskChart.data.datasets[0].data = [current, target];
    riskChart.update();
  }

  function updateSimulation() {
    const target = parseInt(greenSlider.value, 10);
    simTargetGreen.textContent = `${target}%`;

    const base = lastBaseGreen;
    simCurrentGreen.textContent = base ? `${base}%` : "-";

    const diff = target - base;

    let level = "Orta";
    let chipClass = "chip-mid";
    let text = "Mevcut duruma göre önemli değişiklik beklenmiyor.";

    if (diff <= -3) {
      level = "Yüksek Risk";
      chipClass = "chip-high";
      text =
        "Yeşil alan azaltılırsa ısı adası etkisi ve çevresel riskler artacaktır.";
    } else if (diff >= 8) {
      level = "Düşük Risk";
      chipClass = "chip-low";
      text =
        "Yeşil alan ciddi oranda artırılırsa ısı adası etkisi azalır, hava kalitesi ve yaşam konforu artar.";
    } else if (diff >= 3) {
      level = "Azalan Risk";
      chipClass = "chip-mid";
      text =
        "Yeşil alan bir miktar artırılırsa çevresel koşullar ve sosyal yaşam kademeli olarak iyileşir.";
    }

    simRiskChip.textContent = level;
    simRiskChip.className = `chip ${chipClass}`;
    simEffectText.textContent = text;

    updateRiskChart(base, target);
  }

  greenSlider.addEventListener("input", updateSimulation);

  // AI slider label güncelleme
  aiFlood.addEventListener("input", () => {
    aiFloodLabel.textContent = aiFlood.value;
  });
  aiInfra.addEventListener("input", () => {
    aiInfraLabel.textContent = aiInfra.value;
  });

  // ---------------------------
  //  ANALİZ
  // ---------------------------

  analyzeBtn.addEventListener("click", async () => {
    try {
      const scenario = scenarioSelect.value;

      analyzeStatus.textContent = "Analiz yapılıyor...";
      analyzeStatus.classList.remove("error");
      analyzeRaw.textContent = "";
      riskListe.innerHTML = "";
      yesilOran.textContent = "-";
      nufusYogunlugu.textContent = "-";
      analizOneri.textContent = "-";

      const res = await fetch(
        `${API_BASE}/analyze?scenario=${encodeURIComponent(scenario)}`
      );
      const data = await res.json();

      analyzeRaw.textContent = JSON.stringify(data, null, 2);

      if (data && data.analysis) {
        yesilOran.textContent = data.analysis.yesil_alan_orani || "-";
        nufusYogunlugu.textContent = data.analysis.nufus_yogunlugu || "-";
        analizOneri.textContent = data.analysis.oneri || "-";

        if (Array.isArray(data.analysis.risk_tespit)) {
          data.analysis.risk_tespit.forEach((risk) => {
            const li = document.createElement("li");
            li.textContent = risk;
            riskListe.appendChild(li);
          });
        }

        const parsed = parsePercent(data.analysis.yesil_alan_orani);
        if (!Number.isNaN(parsed)) {
          lastBaseGreen = parsed;
          greenSlider.value = parsed;
        }
      }

      analyzeStatus.textContent = "Analiz başarıyla tamamlandı.";
      updateSimulation();
    } catch (err) {
      console.error(err);
      analyzeStatus.textContent = "Analiz isteğinde hata oluştu.";
      analyzeStatus.classList.add("error");
    }
  });

  // ---------------------------
  //  TAHMİN
  // ---------------------------

  predictBtn.addEventListener("click", async () => {
    try {
      const scenario = scenarioSelect.value;

      predictStatus.textContent = "Tahmin hesaplanıyor...";
      predictStatus.classList.remove("error");
      predictRaw.textContent = "";
      konutIhtiyaci.textContent = "-";
      ulasimArtis.textContent = "-";
      tahminOneri.textContent = "-";

      const res = await fetch(
        `${API_BASE}/predict?scenario=${encodeURIComponent(scenario)}`
      );
      const data = await res.json();

      predictRaw.textContent = JSON.stringify(data, null, 2);

      if (data && data.prediction) {
        konutIhtiyaci.textContent =
          data.prediction.konut_ihtiyaci_2030 || "-";
        ulasimArtis.textContent = data.prediction.ulasim_yuk_artisi || "-";
        tahminOneri.textContent = data.prediction.oneri || "-";
      }

      predictStatus.textContent = "Tahmin başarıyla hesaplandı.";
    } catch (err) {
      console.error(err);
      predictStatus.textContent = "Tahmin isteğinde hata oluştu.";
      predictStatus.classList.add("error");
    }
  });

  // ---------------------------
  //  PROJELERİ LİSTELE
  // ---------------------------

  async function refreshProjects() {
    try {
      const res = await fetch(`${API_BASE}/projects`);
      const data = await res.json();

      projectList.innerHTML = "";

      if (data && Array.isArray(data.projects)) {
        data.projects.forEach((p) => {
          const li = document.createElement("li");

          const text = document.createElement("span");
          text.textContent = `#${p.id} • ${p.name} • Senaryo: ${p.scenario} • Hedef yeşil: %${p.target_green}`;

          const link = document.createElement("a");
          link.href = `${API_BASE}/projects/${p.id}/report`;
          link.textContent = " Rapor";
          link.target = "_blank";
          link.style.marginLeft = "8px";
          link.style.color = "#60a5fa";
          link.style.textDecoration = "underline";

          li.appendChild(text);
          li.appendChild(link);

          projectList.appendChild(li);
        });
      }

      projectStatus.textContent = `Toplam proje: ${
        data.projects ? data.projects.length : 0
      }`;
      projectStatus.classList.remove("error");
    } catch (err) {
      console.error(err);
      projectStatus.textContent = "Projeler listelenirken hata oluştu.";
      projectStatus.classList.add("error");
    }
  }

  // ---------------------------
  //  PROJE KAYDET
  // ---------------------------

  saveProjectBtn.addEventListener("click", async () => {
    try {
      const name = projectNameInput.value.trim();
      if (!name) {
        alert("Önce proje adı gir.");
        return;
      }

      const payload = {
        name,
        scenario: scenarioSelect.value,
        target_green: parseInt(greenSlider.value, 10),
        notes: tahminOneri.textContent || analizOneri.textContent || ""
      };

      projectStatus.textContent = "Proje kaydediliyor...";
      projectStatus.classList.remove("error");

      const res = await fetch(`${API_BASE}/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (data.status === "success") {
        projectNameInput.value = "";
        await refreshProjects();
        projectStatus.textContent = "Proje kaydedildi.";
      } else {
        projectStatus.textContent = "Proje kaydedilemedi.";
        projectStatus.classList.add("error");
      }
    } catch (err) {
      console.error(err);
      projectStatus.textContent = "Proje kaydında hata oluştu.";
      projectStatus.classList.add("error");
    }
  });

  // ---------------------------
  //  AI RİSK BUTONU
  // ---------------------------

  aiRiskBtn.addEventListener("click", async () => {
    try {
      const payload = {
        scenario: scenarioSelect.value,
        green_ratio: parseInt(greenSlider.value, 10),
        population_density: aiPopDensity.value,
        flood_risk: parseInt(aiFlood.value, 10),
        infrastructure_score: parseInt(aiInfra.value, 10)
      };

      aiRiskScore.textContent = "-";
      aiRiskLevel.textContent = "-";
      aiRiskExplanation.textContent = "Hesaplanıyor...";

      const res = await fetch(`${API_BASE}/ai/risk-score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (data.status === "success") {
        aiRiskScore.textContent = data.score;
        aiRiskLevel.textContent = data.level;
        aiRiskExplanation.textContent = data.explanation;
      } else {
        aiRiskExplanation.textContent = "AI risk skoru alınamadı.";
      }
    } catch (err) {
      console.error(err);
      aiRiskExplanation.textContent = "AI risk skoru hesaplanırken hata oluştu.";
    }
  });

  // ---------------------------
  //  SAYFA AÇILIŞI
  // ---------------------------

  updateSimulation();
  refreshProjects();
  updateMapForScenario(defaultScenario);
  aiFloodLabel.textContent = aiFlood.value;
  aiInfraLabel.textContent = aiInfra.value;
  initRiskChart();
  updateRiskChart(lastBaseGreen, parseInt(greenSlider.value, 10));
  loadGeoJsonLayer();
});
