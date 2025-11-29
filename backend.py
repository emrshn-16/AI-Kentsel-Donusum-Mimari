from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict
import sqlite3
from pathlib import Path

# =========================
#  UYGULAMA TANIMI
# =========================

app = FastAPI(
    title="AI Kentsel Analiz API",
    description="Kentsel veri analizi, tahmin, simülasyon ve proje raporlama için demo API",
    version="2.0.0",
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
    return {"message": "AI Kentsel Analiz API çalışıyor! (v2.0 – SQLite proje kaydı ile)"}


# =========================
#  SENARYO VERİLERİ
# =========================

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


# =========================
#  DATABASE (SQLite)
# =========================

DB_PATH = Path(__file__).parent / "projects.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # satırları sözlük gibi kullanabilmek için
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            scenario TEXT NOT NULL,
            target_green INTEGER NOT NULL,
            notes TEXT
        )
        """
    )
    conn.commit()
    conn.close()


@app.on_event("startup")
def on_startup():
    init_db()


# =========================
#  HARİTA / ANALİZ / TAHMİN
# =========================

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


# =========================
#  PROJE KAYIT SİSTEMİ – SQLite
# =========================

class ProjectCreate(BaseModel):
    name: str
    scenario: str
    target_green: int
    notes: str | None = None


class Project(ProjectCreate):
    id: int


def row_to_project(row: sqlite3.Row) -> Project:
    return Project(
        id=row["id"],
        name=row["name"],
        scenario=row["scenario"],
        target_green=row["target_green"],
        notes=row["notes"],
    )


@app.post("/projects")
def create_project(project: ProjectCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO projects (name, scenario, target_green, notes)
        VALUES (?, ?, ?, ?)
        """,
        (project.name, project.scenario, project.target_green, project.notes),
    )
    conn.commit()
    pid = cur.lastrowid
    cur.execute("SELECT * FROM projects WHERE id = ?", (pid,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=500, detail="Proje kaydedilemedi")

    proj = row_to_project(row)
    return {"status": "success", "project": proj}


@app.get("/projects")
def list_projects():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    projects = [row_to_project(r) for r in rows]
    return {"status": "success", "projects": projects}


@app.get("/projects/{project_id}")
def get_project(project_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")

    proj = row_to_project(row)
    return {"status": "success", "project": proj}


@app.get("/projects/{project_id}/report", response_class=HTMLResponse)
def project_report(project_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")

    proj = row_to_project(row)

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
                <p class="chip">Demo Rapor v2.0</p>
            </div>

            <div class="footer">
                Otomatik oluşturulmuş demo rapor – sunum ve fikir geliştirme amaçlıdır.
            </div>
        </div>
    </body>
    </html>
    """
    return html


# =========================
#  PROJE KARŞILAŞTIRMA
# =========================

@app.get("/compare-projects")
def compare_projects(a: int, b: int):
    """
    İki projeyi ID bazında karşılaştırır:
    - Projelerin temel bilgileri
    - Senaryo bazlı analiz ve 2030 projeksiyonu
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE id IN (?, ?)", (a, b))
    rows = cur.fetchall()
    conn.close()

    if len(rows) < 2:
        raise HTTPException(status_code=404, detail="Proje(ler) bulunamadı")

    proj_map: Dict[int, Project] = {r["id"]: row_to_project(r) for r in rows}
    if a not in proj_map or b not in proj_map:
        raise HTTPException(status_code=404, detail="Proje(ler) bulunamadı")

    def build_summary(p: Project):
        analysis = ANALYZE_SCENARIOS.get(p.scenario, ANALYZE_SCENARIOS["merkez"])
        prediction = PREDICT_SCENARIOS.get(p.scenario, PREDICT_SCENARIOS["merkez"])
        return {
            "id": p.id,
            "name": p.name,
            "scenario": p.scenario,
            "target_green": p.target_green,
            "analysis": analysis,
            "prediction": prediction,
        }

    return {
        "status": "success",
        "a": build_summary(proj_map[a]),
        "b": build_summary(proj_map[b]),
    }


# =========================
#  AI RİSK SKORU (DEMO MODEL)
# =========================

class AIRiskRequest(BaseModel):
  scenario: str
  green_ratio: int          # 0-100
  population_density: str   # "dusuk", "orta", "yuksek", "cok_yuksek"
  flood_risk: int           # 0-10
  infrastructure_score: int # 0-10 (10 iyi, 0 çok kötü)


@app.post("/ai/risk-score")
def ai_risk_score(req: AIRiskRequest):
    base_map = {
        "dusuk": 20,
        "orta": 40,
        "yuksek": 65,
        "cok_yuksek": 80,
    }
    score = base_map.get(req.population_density, 50)

    score -= (req.green_ratio - 20) * 0.7
    score += req.flood_risk * 3
    score += (10 - req.infrastructure_score) * 2

    if req.scenario == "merkez":
        score += 5
    elif req.scenario == "yesil":
        score -= 5

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
