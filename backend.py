from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict
from itertools import count

app = FastAPI(
    title="AI Kentsel Analiz API",
    description="Kentsel veri analizi, tahmin, simülasyon ve proje raporlama için demo API",
    version="1.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "AI Kentsel Analiz API çalışıyor! (v1.3 – AI risk skoru ile)"}


# -------------------------
#  SENARYO VERİLERİ
# -------------------------

ANALYZE_SCENARIOS: Dict[str, Dict] = {
    "merkez": {
        "yesil_alan_orani": "%8",
        "nufus_yogunlugu": "çok yüksek",
        "risk_tespit": ["ısı adası etkisi", "trafik sıkışıklığı", "yeşil alan yetersiz"],
        "oneri": "Otopark katları azaltılıp, çatı ve ara sokaklarda yeşil alan artırılmalı.",
    },
    "gelisen": {
        "yesil_alan_orani": "%15",
        "nufus_yogunlugu": "orta",
        "risk_tespit": ["altyapı kapasitesi sınırlı", "plansız büyüme riski"],
        "oneri": "Altyapı güçlendirilip, imar planına bağlı kademeli gelişim önerilmeli.",
    },
    "yesil": {
        "yesil_alan_orani": "%32",
        "nufus_yogunlugu": "düşük",
        "risk_tespit": ["kamu ulaşımı zayıf"],
        "oneri": "Toplu taşıma bağlantıları güçlendirilerek erişilebilirlik artırılmalı.",
    },
}

PREDICT_SCENARIOS: Dict[str, Dict] = {
    "merkez": {
        "konut_ihtiyaci_2030": "18.500 birim",
        "ulasim_yuk_artisi": "%52",
        "oneri": "Toplu taşıma + yaya odaklı tasarıma geçilmezse trafik kilitlenecek.",
    },
    "gelisen": {
        "konut_ihtiyaci_2030": "9.200 birim",
        "ulasim_yuk_artisi": "%28",
        "oneri": "Yeni konut alanları ile birlikte çevre yoluna paralel ikinci hat planlanmalı.",
    },
    "yesil": {
        "konut_ihtiyaci_2030": "4.300 birim",
        "ulasim_yuk_artisi": "%14",
        "oneri": "Yeşil kimliği korumak için yoğunluk kontrollü gelişim önerilmeli.",
    },
}


@app.post("/upload-map")
def upload_map():
    return {
        "status": "success",
        "message": "Harita dosyası başarıyla yüklendi (demo).",
        "map_id": "sample_map_001",
    }


@app.get("/analyze")
def analyze(scenario: str = "merkez"):
    data = ANALYZE_SCENARIOS.get(scenario, ANALYZE_SCENARIOS["merkez"])
    return {
        "status": "success",
        "scenario": scenario,
        "analysis": data,
    }


@app.get("/predict")
def predict(scenario: str = "merkez"):
    data = PREDICT_SCENARIOS.get(scenario, PREDICT_SCENARIOS["merkez"])
    return {
        "status": "success",
        "scenario": scenario,
        "prediction": data,
    }


# -------------------------
#  PROJE KAYIT SİSTEMİ (DEMO)
# -------------------------

class ProjectCreate(BaseModel):
    name: str
    scenario: str
    target_green: int
    notes: str | None = None


class Project(ProjectCreate):
    id: int


PROJECTS: Dict[int, Project] = {}
_project_id_counter = count(1)


@app.post("/projects")
def create_project(project: ProjectCreate):
    pid = next(_project_id_counter)
    proj = Project(id=pid, **project.dict())
    PROJECTS[pid] = proj
    return {"status": "success", "project": proj}


@app.get("/projects")
def list_projects():
    return {
        "status": "success",
        "projects": list(PROJECTS.values()),
    }


@app.get("/projects/{project_id}")
def get_project(project_id: int):
    proj = PROJECTS.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
    return {"status": "success", "project": proj}


@app.get("/projects/{project_id}/report", response_class=HTMLResponse)
def project_report(project_id: int):
    proj = PROJECTS.get(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")

    analysis = ANALYZE_SCENARIOS.get(proj.scenario, ANALYZE_SCENARIOS["merkez"])
    prediction = PREDICT_SCENARIOS.get(proj.scenario, PREDICT_SCENARIOS["merkez"])

    safe_notes = (proj.notes or "").replace("<", "&lt;")

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8" />
        <title>Proje Raporu #{proj.id}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f3f4f6;
                color: #111827;
                margin: 0;
                padding: 32px;
            }}
            .report {{
                max-width: 800px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 8px;
                padding: 24px 28px;
                box-shadow: 0 10px 25px rgba(15,23,42,0.15);
                border: 1px solid #e5e7eb;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #e5e7eb;
                padding-bottom: 12px;
                margin-bottom: 16px;
            }}
            .logo-box {{
                font-weight: 700;
                font-size: 18px;
                color: #1f2937;
            }}
            .meta {{
                font-size: 11px;
                color: #6b7280;
                text-align: right;
            }}
            h1 {{
                font-size: 20px;
                margin: 0 0 4px 0;
                color: #111827;
            }}
            h2 {{
                font-size: 16px;
                margin: 0 0 8px 0;
                color: #111827;
            }}
            .section {{
                margin-bottom: 16px;
                padding: 12px 14px;
                border-radius: 6px;
                background: #f9fafb;
                border: 1px solid #e5e7eb;
            }}
            .label {{
                color: #6b7280;
            }}
            .value {{
                font-weight: 600;
                color: #111827;
            }}
            ul {{
                margin-top: 4px;
            }}
            .chip {{
                display:inline-block;
                padding:2px 8px;
                border-radius:999px;
                border:1px solid #9ca3af;
                font-size:11px;
                color:#374151;
                background:#f3f4f6;
            }}
            .footer {{
                margin-top: 20px;
                font-size: 10px;
                color: #9ca3af;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="report">
            <div class="header">
                <div class="logo-box">
                    AI Kentsel Dönüşüm Mimarı
                </div>
                <div class="meta">
                    Proje Raporu #{proj.id}<br />
                    Senaryo: {proj.scenario}<br />
                    Hedef yeşil alan: %{proj.target_green}
                </div>
            </div>

            <h1>{proj.name}</h1>

            <div class="section">
                <h2>1. Proje Bilgileri</h2>
                <p><span class="label">Senaryo:</span> <span class="value">{proj.scenario}</span></p>
                <p><span class="label">Hedef Yeşil Alan Oranı:</span> <span class="value">%{proj.target_green}</span></p>
                <p><span class="label">Notlar:</span> <span class="value">{safe_notes}</span></p>
            </div>

            <div class="section">
                <h2>2. Alan Analizi</h2>
                <p><span class="label">Yeşil Alan Oranı:</span> <span class="value">{analysis["yesil_alan_orani"]}</span></p>
                <p><span class="label">Nüfus Yoğunluğu:</span> <span class="value">{analysis["nufus_yogunlugu"]}</span></p>
                <p><span class="label">Öneri:</span> <span class="value">{analysis["oneri"]}</span></p>
                <p><span class="label">Riskler:</span></p>
                <ul>
                    {''.join(f'<li>{r}</li>' for r in analysis["risk_tespit"])}
                </ul>
            </div>

            <div class="section">
                <h2>3. 2030 Projeksiyonu</h2>
                <p><span class="label">Konut İhtiyacı 2030:</span> <span class="value">{prediction["konut_ihtiyaci_2030"]}</span></p>
                <p><span class="label">Ulaşım Yük Artışı:</span> <span class="value">{prediction["ulasim_yuk_artisi"]}</span></p>
                <p><span class="label">Öneri:</span> <span class="value">{prediction["oneri"]}</span></p>
            </div>

            <div class="section">
                <h2>4. Genel Değerlendirme</h2>
                <p>
                    Bu rapor, seçilen senaryo ve hedef yeşil alan oranı için
                    AI Kentsel Dönüşüm Mimarı demo sistemi tarafından üretilmiştir.
                    Gerçek proje aşamasında bu yapı; gerçek CBS verileri, nüfus projeksiyonları
                    ve gelişmiş yapay zekâ modelleriyle zenginleştirilebilir.
                </p>
                <p class="chip">Demo Rapor v1.1</p>
            </div>

            <div class="footer">
                Otomatik oluşturulmuş demo rapor – sunum ve fikir geliştirme amaçlıdır.
            </div>
        </div>
    </body>
    </html>
    """
    return html


# -------------------------
#  AI RİSK SKORU (DEMO MODEL)
# -------------------------

class AIRiskRequest(BaseModel):
    scenario: str
    green_ratio: int          # 0-100
    population_density: str   # "dusuk", "orta", "yuksek", "cok_yuksek"
    flood_risk: int           # 0-10
    infrastructure_score: int # 0-10 (10 iyi, 0 çok kötü)


@app.post("/ai/risk-score")
def ai_risk_score(req: AIRiskRequest):
    # 1) Nüfus yoğunluğuna göre başlangıç risk
    base_map = {
        "dusuk": 20,
        "orta": 40,
        "yuksek": 65,
        "cok_yuksek": 80,
    }
    score = base_map.get(req.population_density, 50)

    # 2) Yeşil alan etkisi: yeşil alan arttıkça risk azalsın
    # referans yeşil %20 gibi düşünelim
    score -= (req.green_ratio - 20) * 0.7

    # 3) Sel riski 0-10 → max +30 puan
    score += req.flood_risk * 3

    # 4) Altyapı kötü ise risk artsın
    # infrastructure_score 0-10, 10 iyi, 0 kötü
    score += (10 - req.infrastructure_score) * 2

    # 5) Senaryoya göre küçük bir ayar
    if req.scenario == "merkez":
        score += 5
    elif req.scenario == "yesil":
        score -= 5

    # Skoru 0-100 aralığına sıkıştır
    score = int(round(max(0, min(100, score))))

    if score < 35:
        level = "Düşük Risk"
        explanation = (
            "Bölge genel olarak düşük risk seviyesinde görünüyor. "
            "Yeşil alan oranı ve altyapı koşulları kabul edilebilir düzeyde."
        )
    elif score < 70:
        level = "Orta Risk"
        explanation = (
            "Bölgede dikkat edilmesi gereken bazı riskler var. "
            "Yeşil alan artırımı ve altyapı güçlendirmesi ile risk azaltılabilir."
        )
    else:
        level = "Yüksek Risk"
        explanation = (
            "Bölge yüksek risk grubunda. Nüfus yoğunluğu, sel riski veya altyapı "
            "kaynaklı ciddi sorunlar oluşabilir, öncelikli müdahale önerilir."
        )

    return {
        "status": "success",
        "score": score,
        "level": level,
        "explanation": explanation,
    }
