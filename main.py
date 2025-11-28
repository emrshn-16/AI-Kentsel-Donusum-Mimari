from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Uygulama nesnesi
app = FastAPI(
    title="AI Kentsel Analiz API",
    description="Kentsel veri analizi, tahmin ve planlama için demo API",
    version="1.0.0",
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Demo için herkese açık
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basit test endpoint (anasayfa)
@app.get("/")
def read_root():
    return {"message": "AI Kentsel Analiz API çalışıyor!"}

# 1) HARİTA VERİSİ YÜKLEME (DEMO)
@app.post("/upload-map")
def upload_map():
    return {
        "status": "success",
        "message": "Harita dosyası başarıyla yüklendi (demo).",
        "map_id": "sample_map_001",
    }

# 2) ANALİZ ÜRETME (DEMO)
@app.get("/analyze")
def analyze():
    analysis_result = {
        "yesil_alan_orani": "%18",
        "nufus_yogunlugu": "yüksek",
        "risk_tespit": ["sel riski", "altyapı zayıf"],
        "oneri": "Yeşil alan %25 seviyesine çıkarılmalı.",
    }
    return {
        "status": "success",
        "analysis": analysis_result,
    }

# 3) TAHMİN / AI KARAR MODELİ (DEMO)
@app.get("/predict")
def predict():
    prediction = {
        "konut_ihtiyaci_2030": "12.400 birim",
        "ulasim_yuk_artisi": "%36",
        "oneri": "Toplu taşıma kapasitesi artırılmalı.",
    }
    return {
        "status": "success",
        "prediction": prediction,
    }
