import logging

from app.db.models import GuidelineChunkModel
from app.db.session import Base, SessionLocal, engine

logger = logging.getLogger(__name__)

INITIAL_GUIDELINES = [
    # 1. ADA Standards of Care - Diabetes & Glycemic Control
    {
        "id": "ada-2024-dm-fpg",
        "knowledge_base_id": "clinical-standards-v1",
        "title": "ADA Standards of Care in Diabetes — Diagnostic Criteria",
        "organization": "American Diabetes Association (ADA)",
        "category": "Metabolic & Glycemic",
        "section": "Classification and Diagnosis of Diabetes: Fasting Plasma Glucose",
        "page": 14,
        "recommendation_level": "Grade A",
        "publication_year": 2024,
        "keywords": "glucose fasting blood sugar fbg fpg diabetes prediabetes impaired fasting glucose",
        "text": (
            "Fasting Plasma Glucose (FPG) diagnostic thresholds: Normal fasting glucose is defined as < 100 mg/dL (5.6 mmol/L). "
            "Impaired Fasting Glucose (Prediabetes) is defined as FPG between 100 to 125 mg/dL (5.6 to 6.9 mmol/L). "
            "Diabetes Mellitus is diagnosed when FPG is >= 126 mg/dL (7.0 mmol/L) on repeated testing. "
            "Lifestyle interventions including caloric moderation and 150 minutes/week of moderate physical activity are recommended for prediabetes."
        ),
    },
    {
        "id": "ada-2024-dm-hba1c",
        "knowledge_base_id": "clinical-standards-v1",
        "title": "ADA Standards of Care in Diabetes — Glycated Hemoglobin (HbA1c)",
        "organization": "American Diabetes Association (ADA)",
        "category": "Metabolic & Glycemic",
        "section": "Diagnostic Criteria: Glycated Hemoglobin",
        "page": 15,
        "recommendation_level": "Grade A",
        "publication_year": 2024,
        "keywords": "hba1c a1c glycated hemoglobin diabetes prediabetes average glucose",
        "text": (
            "HbA1c diagnostic cutoffs: Normal is < 5.7% (39 mmol/mol). "
            "Prediabetes category corresponds to HbA1c between 5.7% and 6.4% (39–47 mmol/mol). "
            "A diagnosis of diabetes is confirmed with an HbA1c >= 6.5% (48 mmol/mol) verified by repeat testing in the absence of unequivocal hyperglycemia. "
            "In non-pregnant adults without significant hypoglycemia, the standard general glycemic target is HbA1c < 7.0%."
        ),
    },
    # 2. ACC / AHA Cholesterol & Cardiovascular Risk Guidelines
    {
        "id": "acc-aha-2023-lipid-ldl",
        "knowledge_base_id": "clinical-standards-v1",
        "title": "AHA/ACC Guideline on the Management of Blood Cholesterol",
        "organization": "American College of Cardiology / AHA",
        "category": "Cardiovascular & Lipids",
        "section": "Secondary and Primary Prevention: Low-Density Lipoprotein Cholesterol",
        "page": 32,
        "recommendation_level": "Class I (Level of Evidence A)",
        "publication_year": 2023,
        "keywords": "cholesterol ldl ldl-c bad cholesterol lipids cardiovascular atherosclerotic ascvd",
        "text": (
            "Low-density lipoprotein cholesterol (LDL-C) thresholds: Optimal LDL-C is < 100 mg/dL. "
            "Near optimal is 100–129 mg/dL; Borderline high is 130–159 mg/dL; High is 160–189 mg/dL; Very high is >= 190 mg/dL. "
            "In primary prevention, adults aged 40 to 75 with LDL-C >= 70 mg/dL to < 190 mg/dL should be evaluated with 10-year ASCVD risk estimators. "
            "Initial management includes heart-healthy dietary patterns emphasizing soluble fiber, Mediterranean diet, and saturated fat reduction."
        ),
    },
    {
        "id": "acc-aha-2023-lipid-tg",
        "knowledge_base_id": "clinical-standards-v1",
        "title": "AHA/ACC Guideline on Blood Cholesterol — Hypertriglyceridemia",
        "organization": "American College of Cardiology / AHA",
        "category": "Cardiovascular & Lipids",
        "section": "Hypertriglyceridemia Management and Pancreatitis Prevention",
        "page": 38,
        "recommendation_level": "Class IIa",
        "publication_year": 2023,
        "keywords": "triglycerides tg hypertriglyceridemia lipids pancreatitis metabolic syndrome",
        "text": (
            "Fasting Triglyceride classification: Normal is < 150 mg/dL. "
            "Borderline high is 150–199 mg/dL; High is 200–499 mg/dL; Very high (severe hypertriglyceridemia) is >= 500 mg/dL. "
            "Triglyceride levels >= 500 mg/dL significantly increase the acute risk of pancreatitis and warrant immediate dietary intervention and medical therapy. "
            "Borderline to high levels should prompt screening for metabolic syndrome, alcohol intake, and poorly controlled glycemic status."
        ),
    },
    # 3. KDIGO Chronic Kidney Disease Guidelines
    {
        "id": "kdigo-2024-ckd-creatinine-egfr",
        "knowledge_base_id": "clinical-standards-v1",
        "title": "KDIGO Clinical Practice Guideline for the Evaluation and Management of CKD",
        "organization": "Kidney Disease: Improving Global Outcomes (KDIGO)",
        "category": "Renal & Kidney Function",
        "section": "Evaluation of Kidney Disease: Serum Creatinine, eGFR and BUN",
        "page": 22,
        "recommendation_level": "Level 1A",
        "publication_year": 2024,
        "keywords": "creatinine egfr kidney renal bun blood urea nitrogen ckd glomerular filtration",
        "text": (
            "Serum creatinine reference values typically range between 0.6–1.2 mg/dL for men and 0.5–1.1 mg/dL for women, varying by muscle mass. "
            "CKD is defined as abnormalities of kidney structure or function, present for > 3 months. "
            "eGFR >= 90 mL/min/1.73m2 indicates normal/high GFR (G1); 60–89 indicates mildly decreased GFR (G2); "
            "persistent eGFR < 60 mL/min/1.73m2 (G3a-G5) defines chronic kidney disease. "
            "Out-of-range creatinine requires hydration assessment, urine albumin-to-creatinine ratio (uACR), and nephrotoxic medication review."
        ),
    },
    # 4. WHO & ASH Hematology / Anemia Guidelines
    {
        "id": "who-2024-anemia-hgb",
        "knowledge_base_id": "clinical-standards-v1",
        "title": "WHO Guidelines on Haemoglobin Concentrations for the Diagnosis of Anaemia",
        "organization": "World Health Organization (WHO)",
        "category": "Hematology & CBC",
        "section": "Diagnosis of Anaemia and Assessment of Severity",
        "page": 8,
        "recommendation_level": "Standard",
        "publication_year": 2024,
        "keywords": "hemoglobin hgb hb anaemia anemia cbc rbc hematocrit complete blood count",
        "text": (
            "Haemoglobin diagnostic thresholds for anaemia (sea level): "
            "Adult non-pregnant women: < 12.0 g/dL defines anaemia; Adult men: < 13.0 g/dL defines anaemia. "
            "Mild anaemia: 11.0–11.9 g/dL (women) / 11.0–12.9 g/dL (men); Moderate anaemia: 8.0–10.9 g/dL; Severe anaemia: < 8.0 g/dL. "
            "Evaluation must incorporate red cell indices (MCV, MCH, RDW), serum ferritin, and occult blood screening to distinguish iron deficiency from thalassemia or chronic disease."
        ),
    },
    {
        "id": "ash-2023-hematology-wbc-platelets",
        "knowledge_base_id": "clinical-standards-v1",
        "title": "American Society of Hematology — Complete Blood Count Interpretation",
        "organization": "American Society of Hematology (ASH)",
        "category": "Hematology & CBC",
        "section": "Evaluation of Leukocytosis, Leukopenia, and Thrombocytopenia",
        "page": 45,
        "recommendation_level": "Clinical Practice Guideline",
        "publication_year": 2023,
        "keywords": "wbc white blood cells platelets leukocytosis leukopenia thrombocytopenia neutrophils infection",
        "text": (
            "Reference ranges: Total WBC count typically 4.0–11.0 x 10^3/uL; Platelet count typically 150–450 x 10^3/uL. "
            "Leukocytosis (> 11.0 x 10^3/uL) commonly signifies acute bacterial or viral infection, tissue inflammation, glucocorticoid therapy, or marrow stress. "
            "Thrombocytopenia (< 150 x 10^3/uL) warrants peripheral smear review to exclude EDTA clumping (pseudothrombocytopenia) and monitoring for bleeding risk if < 50 x 10^3/uL."
        ),
    },
    # 5. ACG / AASLD Liver Function Test Guidelines
    {
        "id": "acg-2023-lft-alt-ast",
        "knowledge_base_id": "clinical-standards-v1",
        "title": "ACG Clinical Guideline: Evaluation of Abnormal Liver Chemistries",
        "organization": "American College of Gastroenterology (ACG)",
        "category": "Hepatic & Liver Function",
        "section": "Evaluation of Elevated Aminotransferases (ALT and AST)",
        "page": 19,
        "recommendation_level": "Conditional Recommendation",
        "publication_year": 2023,
        "keywords": "alt ast liver enzymes hepatic transaminases sgpt sgot bilirubin hepatitis fatty liver",
        "text": (
            "Normal ALT levels are defined as 29 to 33 IU/L for males and 19 to 25 IU/L for females. "
            "Elevations exceeding these limits correlate with increased liver-related mortality. "
            "Mild elevations (< 5x upper limit of normal) are frequently observed in metabolic dysfunction-associated steatotic liver disease (MASLD), "
            "alcohol intake, medication effect (e.g. statins, acetaminophen), and viral hepatitis. "
            "Initial follow-up entails complete hepatic panel, abdominal ultrasound, and repeat testing in 4 to 8 weeks."
        ),
    },
]


def init_db():
    """Initializes tables and seeds clinical guideline knowledge base."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if guideline chunks are already seeded
        existing_count = db.query(GuidelineChunkModel).count()
        if existing_count == 0:
            logger.info("Seeding clinical guideline knowledge base...")
            for item in INITIAL_GUIDELINES:
                chunk = GuidelineChunkModel(**item)
                db.add(chunk)
            db.commit()
            logger.info(f"Successfully seeded {len(INITIAL_GUIDELINES)} clinical guidelines.")
    except Exception as e:
        logger.error(f"Error initializing or seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
