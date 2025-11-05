import os
import json
import PyPDF2
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel(os.getenv("MODEL_NAME", "gemini-2.5-flash"))

def extract_pdf_text(pdf_path):
    """Extract text from PDF"""
    print("📄 Reading PDF file...")
    text = ""
    
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        print(f"   Total pages: {len(pdf_reader.pages)}")
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            text += page.extract_text() + "\n"
            print(f"   ✓ Extracted page {page_num}")
    
    print(f"✅ Total characters extracted: {len(text)}\n")
    return text

def extract_clinical_data(text):
    """Extract COMPREHENSIVE clinical data using Gemini"""
    
    print("🤖 Extracting ALL clinical information with Gemini...")
    print(f"   Model: {os.getenv('MODEL_NAME')}\n")
    
    prompt = f"""
Extract COMPREHENSIVE clinical information from this medical document and return ONLY valid JSON.

CRITICAL: Extract ALL of the following information if present in the document:

{{
  "patient_demographics": {{
    "name": "",
    "dob": "YYYY-MM-DD",
    "age": "",
    "gender": "",
    "mrn": "",
    "admission_id": "",
    "address": "",
    "city": "",
    "state": "",
    "zip": ""
  }},
  "social_history": {{
    "occupation": "",
    "marital_status": "",
    "smoking": "",
    "alcohol": "",
    "exercise": "",
    "living_situation": ""
  }},
  "admission": {{
    "chief_complaint": "",
    "history_present_illness": "",
    "date_admission": "",
    "date_discharge": "",
    "initial_gcs": "",
    "mechanism_of_injury": ""
  }},
  "medical_history": {{
    "past_medical_history": [],
    "surgical_history": [],
    "family_history": []
  }},
  "home_medications": [
    {{
      "name": "",
      "dosage": "",
      "frequency": "",
      "route": ""
    }}
  ],
  "hospital_medications": [
    {{
      "name": "",
      "dosage": "",
      "frequency": "",
      "route": "",
      "indication": ""
    }}
  ],
  "allergies": [
    {{
      "substance": "",
      "reaction": "",
      "severity": ""
    }}
  ],
  "vital_signs": [
    {{
      "date": "",
      "type": "",
      "value": "",
      "unit": ""
    }}
  ],
  "lab_results": [
    {{
      "date": "",
      "test_name": "",
      "value": "",
      "unit": "",
      "reference_range": ""
    }}
  ],
  "imaging": [
    {{
      "date": "",
      "type": "CT/MRI/X-ray",
      "body_part": "",
      "findings": "",
      "impression": ""
    }}
  ],
  "procedures": [
    {{
      "date": "",
      "procedure_name": "",
      "indication": "",
      "provider": "",
      "details": ""
    }}
  ],
  "conditions": [
    {{
      "condition_name": "",
      "status": "active/resolved",
      "onset_date": ""
    }}
  ],
  "progress_notes": [
    {{
      "date": "",
      "day_number": "",
      "gcs_score": "",
      "neurological_status": "",
      "respiratory_status": "",
      "cardiovascular_status": "",
      "changes_in_condition": "",
      "plan": ""
    }}
  ],
  "consultations": [
    {{
      "specialty": "",
      "date": "",
      "recommendations": ""
    }}
  ],
  "physical_exam": {{
    "general": "",
    "heent": "",
    "cardiovascular": "",
    "respiratory": "",
    "neurological": "",
    "musculoskeletal": "",
    "other": ""
  }},
  "assessment_plan": {{
    "primary_diagnosis": "",
    "secondary_diagnoses": [],
    "treatment_plan": "",
    "goals_of_care": ""
  }},
  "discharge": {{
    "disposition": "",
    "discharge_medications": [],
    "discharge_instructions": "",
    "follow_up_appointments": [],
    "activity_restrictions": "",
    "warning_signs": ""
  }}
}}

Medical Document (Complete):
{text}

Extract EVERY piece of information. Return ONLY the JSON object. No markdown, no extra text.
"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=16000,
                top_p=1,
                top_k=40
            )
        )
        
        return response.text
        
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")

def clean_json_response(response_text):
    """Clean and extract JSON from response"""
    text = response_text.strip()
    
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("``````")[0].strip()
    
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    
    if first_brace != -1 and last_brace != -1:
        text = text[first_brace:last_brace + 1]
    
    return text

def map_to_fhir(data):
    """Convert extracted data to COMPREHENSIVE FHIR Bundle"""
    
    print("\n🏥 Converting to COMPREHENSIVE FHIR resources...")
    
    fhir_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": []
    }
    
    # ========== PATIENT RESOURCE ==========
    if data.get("patient_demographics"):
        demo = data["patient_demographics"]
        patient = {
            "resourceType": "Patient",
            "id": "patient-001",
            "identifier": [
                {
                    "system": "http://hospital.org/mrn",
                    "value": demo.get("mrn", "")
                }
            ],
            "name": [{"text": demo.get("name", "Unknown")}],
            "gender": demo.get("gender", "unknown"),
            "birthDate": demo.get("dob", ""),
            "address": [{
                "line": [demo.get("address", "")],
                "city": demo.get("city", ""),
                "state": demo.get("state", ""),
                "postalCode": demo.get("zip", "")
            }]
        }
        fhir_bundle["entry"].append({"resource": patient})
        print("   ✓ Created Patient resource")
    
    # ========== ENCOUNTER RESOURCE (Admission) ==========
    if data.get("admission"):
        adm = data["admission"]
        encounter = {
            "resourceType": "Encounter",
            "id": "encounter-001",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "IMP",
                "display": "inpatient encounter"
            },
            "subject": {"reference": "Patient/patient-001"},
            "period": {
                "start": adm.get("date_admission", ""),
                "end": adm.get("date_discharge", "")
            },
            "reasonCode": [
                {"text": adm.get("chief_complaint", "")}
            ],
            "hospitalization": {
                "dischargeDisposition": {
                    "text": data.get("discharge", {}).get("disposition", "")
                }
            }
        }
        fhir_bundle["entry"].append({"resource": encounter})
        print("   ✓ Created Encounter resource")
    
    # ========== CONDITION RESOURCES ==========
    if data.get("conditions"):
        for idx, condition in enumerate(data["conditions"]):
            fhir_condition = {
                "resourceType": "Condition",
                "id": f"condition-{idx+1}",
                "subject": {"reference": "Patient/patient-001"},
                "encounter": {"reference": "Encounter/encounter-001"},
                "code": {"text": condition.get("condition_name", "Unknown")},
                "clinicalStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active" if condition.get("status", "active") == "active" else "resolved"
                    }]
                },
                "onsetDateTime": condition.get("onset_date", "")
            }
            fhir_bundle["entry"].append({"resource": fhir_condition})
        print(f"   ✓ Created {len(data['conditions'])} Condition resource(s)")
    
    # ========== PROCEDURE RESOURCES ==========
    if data.get("procedures"):
        for idx, proc in enumerate(data["procedures"]):
            fhir_procedure = {
                "resourceType": "Procedure",
                "id": f"procedure-{idx+1}",
                "status": "completed",
                "subject": {"reference": "Patient/patient-001"},
                "encounter": {"reference": "Encounter/encounter-001"},
                "code": {"text": proc.get("procedure_name", "Unknown")},
                "performedDateTime": proc.get("date", ""),
                "reasonCode": [{"text": proc.get("indication", "")}],
                "note": [{"text": proc.get("details", "")}]
            }
            if proc.get("provider"):
                fhir_procedure["performer"] = [
                    {"actor": {"display": proc.get("provider", "")}}
                ]
            fhir_bundle["entry"].append({"resource": fhir_procedure})
        print(f"   ✓ Created {len(data['procedures'])} Procedure resource(s)")
    
    # ========== DIAGNOSTIC REPORT (Imaging) ==========
    if data.get("imaging"):
        for idx, img in enumerate(data["imaging"]):
            diagnostic_report = {
                "resourceType": "DiagnosticReport",
                "id": f"imaging-{idx+1}",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "RAD",
                        "display": "Radiology"
                    }]
                }],
                "code": {"text": f"{img.get('type', '')} {img.get('body_part', '')}"},
                "subject": {"reference": "Patient/patient-001"},
                "encounter": {"reference": "Encounter/encounter-001"},
                "effectiveDateTime": img.get("date", ""),
                "conclusion": img.get("findings", ""),
                "conclusionCode": [{"text": img.get("impression", "")}]
            }
            fhir_bundle["entry"].append({"resource": diagnostic_report})
        print(f"   ✓ Created {len(data['imaging'])} DiagnosticReport resource(s)")
    
    # ========== MEDICATION REQUESTS (Home + Hospital) ==========
    med_count = 0
    if data.get("home_medications"):
        for idx, med in enumerate(data["home_medications"]):
            fhir_med = {
                "resourceType": "MedicationRequest",
                "id": f"home-med-{idx+1}",
                "status": "active",
                "intent": "order",
                "category": [{"text": "Home Medication"}],
                "subject": {"reference": "Patient/patient-001"},
                "medicationCodeableConcept": {"text": med.get("name", "Unknown")},
                "dosageInstruction": [{
                    "text": f"{med.get('dosage', '')} {med.get('route', '')} {med.get('frequency', '')}".strip()
                }]
            }
            fhir_bundle["entry"].append({"resource": fhir_med})
            med_count += 1
    
    if data.get("hospital_medications"):
        for idx, med in enumerate(data["hospital_medications"]):
            fhir_med = {
                "resourceType": "MedicationRequest",
                "id": f"hospital-med-{idx+1}",
                "status": "active",
                "intent": "order",
                "category": [{"text": "Hospital Medication"}],
                "subject": {"reference": "Patient/patient-001"},
                "encounter": {"reference": "Encounter/encounter-001"},
                "medicationCodeableConcept": {"text": med.get("name", "Unknown")},
                "dosageInstruction": [{
                    "text": f"{med.get('dosage', '')} {med.get('route', '')} {med.get('frequency', '')}".strip()
                }],
                "reasonCode": [{"text": med.get("indication", "")}]
            }
            fhir_bundle["entry"].append({"resource": fhir_med})
            med_count += 1
    
    if med_count > 0:
        print(f"   ✓ Created {med_count} MedicationRequest resource(s)")
    
    # ========== OBSERVATIONS (Vitals + Labs) ==========
    obs_count = 0
    if data.get("vital_signs"):
        for idx, vital in enumerate(data["vital_signs"]):
            fhir_obs = {
                "resourceType": "Observation",
                "id": f"vital-{idx+1}",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs"
                    }]
                }],
                "subject": {"reference": "Patient/patient-001"},
                "encounter": {"reference": "Encounter/encounter-001"},
                "effectiveDateTime": vital.get("date", ""),
                "code": {"text": vital.get("type", "Unknown")},
                "valueString": f"{vital.get('value', '')} {vital.get('unit', '')}".strip()
            }
            fhir_bundle["entry"].append({"resource": fhir_obs})
            obs_count += 1
    
    if data.get("lab_results"):
        for idx, lab in enumerate(data["lab_results"]):
            fhir_obs = {
                "resourceType": "Observation",
                "id": f"lab-{idx+1}",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory"
                    }]
                }],
                "subject": {"reference": "Patient/patient-001"},
                "encounter": {"reference": "Encounter/encounter-001"},
                "effectiveDateTime": lab.get("date", ""),
                "code": {"text": lab.get("test_name", "Unknown")},
                "valueString": f"{lab.get('value', '')} {lab.get('unit', '')}".strip(),
                "referenceRange": [{
                    "text": lab.get("reference_range", "")
                }]
            }
            fhir_bundle["entry"].append({"resource": fhir_obs})
            obs_count += 1
    
    if obs_count > 0:
        print(f"   ✓ Created {obs_count} Observation resource(s)")
    
    # ========== ALLERGY INTOLERANCE ==========
    if data.get("allergies"):
        for idx, allergy in enumerate(data["allergies"]):
            fhir_allergy = {
                "resourceType": "AllergyIntolerance",
                "id": f"allergy-{idx+1}",
                "clinicalStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                        "code": "active"
                    }]
                },
                "patient": {"reference": "Patient/patient-001"},
                "code": {"text": allergy.get("substance", "Unknown")},
                "reaction": [{
                    "severity": allergy.get("severity", "moderate"),
                    "manifestation": [{"text": allergy.get("reaction", "")}]
                }]
            }
            fhir_bundle["entry"].append({"resource": fhir_allergy})
        print(f"   ✓ Created {len(data['allergies'])} AllergyIntolerance resource(s)")
    
    # ========== CLINICAL IMPRESSIONS (Progress Notes) ==========
    if data.get("progress_notes"):
        for idx, note in enumerate(data["progress_notes"]):
            clinical_impression = {
                "resourceType": "ClinicalImpression",
                "id": f"progress-note-{idx+1}",
                "status": "completed",
                "subject": {"reference": "Patient/patient-001"},
                "encounter": {"reference": "Encounter/encounter-001"},
                "effectiveDateTime": note.get("date", ""),
                "summary": f"Day {note.get('day_number', '')}: GCS {note.get('gcs_score', '')}. Neuro: {note.get('neurological_status', '')}. Resp: {note.get('respiratory_status', '')}. CV: {note.get('cardiovascular_status', '')}. Changes: {note.get('changes_in_condition', '')}",
                "note": [{"text": note.get("plan", "")}]
            }
            fhir_bundle["entry"].append({"resource": clinical_impression})
        print(f"   ✓ Created {len(data['progress_notes'])} ClinicalImpression resource(s)")
    
    # ========== SERVICE REQUESTS (Consultations) ==========
    if data.get("consultations"):
        for idx, consult in enumerate(data["consultations"]):
            service_request = {
                "resourceType": "ServiceRequest",
                "id": f"consult-{idx+1}",
                "status": "completed",
                "intent": "order",
                "category": [{
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "11429006",
                        "display": "Consultation"
                    }]
                }],
                "code": {"text": f"{consult.get('specialty', '')} Consultation"},
                "subject": {"reference": "Patient/patient-001"},
                "encounter": {"reference": "Encounter/encounter-001"},
                "authoredOn": consult.get("date", ""),
                "note": [{"text": consult.get("recommendations", "")}]
            }
            fhir_bundle["entry"].append({"resource": service_request})
        print(f"   ✓ Created {len(data['consultations'])} ServiceRequest resource(s)")
    
    # ========== CARE PLAN (Discharge Planning) ==========
    if data.get("discharge"):
        discharge = data.get("discharge", {})
        care_plan = {
            "resourceType": "CarePlan",
            "id": "discharge-plan-001",
            "status": "completed",
            "intent": "plan",
            "title": "Discharge Care Plan",
            "subject": {"reference": "Patient/patient-001"},
            "encounter": {"reference": "Encounter/encounter-001"},
            "activity": [],
            "note": [
                {"text": f"Disposition: {discharge.get('disposition', '')}"},
                {"text": f"Instructions: {discharge.get('discharge_instructions', '')}"},
                {"text": f"Activity Restrictions: {discharge.get('activity_restrictions', '')}"},
                {"text": f"Warning Signs: {discharge.get('warning_signs', '')}"}
            ]
        }
        
        # Add follow-up appointments
        for followup in discharge.get("follow_up_appointments", []):
            care_plan["activity"].append({
                "detail": {
                    "kind": "Appointment",
                    "code": {"text": "Follow-up"},
                    "description": followup,
                    "status": "scheduled"
                }
            })
        
        fhir_bundle["entry"].append({"resource": care_plan})
        print("   ✓ Created CarePlan resource")
    
    print(f"\n✅ Total FHIR resources created: {len(fhir_bundle['entry'])}")
    
    return fhir_bundle

def main():
    print("=" * 80)
    print("🏥 COMPREHENSIVE CLINICAL FHIR EXTRACTION PIPELINE")
    print("=" * 80)
    print()
    
    try:
        # Step 1: Extract PDF text
        pdf_path = os.getenv("PDF_PATH", "data/Cynthia-data.pdf")
        text = extract_pdf_text(pdf_path)
        
        preview = text[:300]
        print(f"📝 Text Preview:\n{preview}...\n")
        
        # Step 2: Extract ALL clinical data
        raw_response = extract_clinical_data(text)
        
        # Clean and parse JSON
        json_text = clean_json_response(raw_response)
        extracted_data = json.loads(json_text)
        
        print("✅ Extraction completed successfully!\n")
        
        # Save extracted data
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        extracted_file = output_dir / "extracted_data_complete.json"
        with open(extracted_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved extracted data to: {extracted_file}")
        
        # Print summary
        print(f"\n📊 COMPREHENSIVE Extraction Summary:")
        print(f"   • Patient: {extracted_data.get('patient_demographics', {}).get('name', 'N/A')}")
        print(f"   • Home Medications: {len(extracted_data.get('home_medications', []))}")
        print(f"   • Hospital Medications: {len(extracted_data.get('hospital_medications', []))}")
        print(f"   • Conditions: {len(extracted_data.get('conditions', []))}")
        print(f"   • Procedures: {len(extracted_data.get('procedures', []))}")
        print(f"   • Imaging Studies: {len(extracted_data.get('imaging', []))}")
        print(f"   • Vital Signs: {len(extracted_data.get('vital_signs', []))}")
        print(f"   • Lab Results: {len(extracted_data.get('lab_results', []))}")
        print(f"   • Progress Notes: {len(extracted_data.get('progress_notes', []))}")
        print(f"   • Consultations: {len(extracted_data.get('consultations', []))}")
        print(f"   • Allergies: {len(extracted_data.get('allergies', []))}")
        
        # Step 3: Convert to COMPREHENSIVE FHIR
        fhir_resources = map_to_fhir(extracted_data)
        
        fhir_file = output_dir / "fhir_resources_complete.json"
        with open(fhir_file, 'w', encoding='utf-8') as f:
            json.dump(fhir_resources, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved FHIR resources to: {fhir_file}\n")
        
        print("=" * 80)
        print("✅ COMPREHENSIVE EXTRACTION COMPLETED!")
        print("=" * 80)
        print()
        print(f"📂 Output files:")
        print(f"   • Extracted Data: {extracted_file}")
        print(f"   • FHIR Resources: {fhir_file}")
        print()
        
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Parse Error: {e}")
        print(f"   Check the cleaned JSON output above")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
# Add this function (backward compatibility wrapper)
def extract_text_from_pdf(pdf_path):
    """Wrapper for dashboard compatibility"""
    return extract_pdf_text(pdf_path)


if __name__ == "__main__":
    main()
