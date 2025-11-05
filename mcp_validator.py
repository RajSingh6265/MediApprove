"""
MCP Validation Module - Alternative Version
Uses APIs that work globally without restrictions
"""

import requests
from typing import Dict, List, Any
import os
from dotenv import load_dotenv
import time

load_dotenv()

class MCPValidator:
    """Validates extracted clinical data using alternative free APIs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Common medications database (offline validation)
        self.common_medications = {
            "lisinopril": {"rxcui": "29046", "class": "ACE Inhibitor"},
            "albuterol": {"rxcui": "435", "class": "Bronchodilator"},
            "phenytoin": {"rxcui": "8183", "class": "Anticonvulsant"},
            "mannitol": {"rxcui": "6804", "class": "Osmotic Diuretic"},
            "levetiracetam": {"rxcui": "40254", "class": "Anticonvulsant"},
            "multivitamin": {"rxcui": "202421", "class": "Supplement"},
            "aspirin": {"rxcui": "1191", "class": "NSAID"},
            "ibuprofen": {"rxcui": "5640", "class": "NSAID"},
            "acetaminophen": {"rxcui": "161", "class": "Analgesic"},
            "metformin": {"rxcui": "6809", "class": "Antidiabetic"}
        }
        
        # Common ICD-10 codes (offline validation)
        self.common_icd10 = {
            "hypertension": "I10",
            "diabetes": "E11.9",
            "asthma": "J45.909",
            "traumatic brain injury": "S06.9",
            "skull fracture": "S02.9",
            "intracranial hemorrhage": "I62.9",
            "cervical spine injury": "S12.9",
            "respiratory failure": "J96.90",
            "altered mental status": "R41.82",
            "polytrauma": "T07"
        }
        
        print("✅ MCP Validator initialized (Alternative Mode - Offline)")
    
    def validate_medication(self, medication_name: str) -> Dict:
        """Validate medication using offline database"""
        try:
            # Clean and normalize
            clean_name = medication_name.lower().strip().split()[0]
            
            # Check in local database
            if clean_name in self.common_medications:
                med_data = self.common_medications[clean_name]
                return {
                    "valid": True,
                    "medication": medication_name,
                    "rxcui": med_data["rxcui"],
                    "drug_class": med_data["class"],
                    "status": "verified_offline",
                    "source": "local_database"
                }
            
            # Try partial matching
            for known_med, data in self.common_medications.items():
                if known_med in clean_name or clean_name in known_med:
                    return {
                        "valid": True,
                        "medication": medication_name,
                        "rxcui": data["rxcui"],
                        "drug_class": data["class"],
                        "status": "matched_offline",
                        "matched_to": known_med,
                        "source": "local_database"
                    }
            
            return {
                "valid": False,
                "medication": medication_name,
                "status": "not_in_local_database",
                "warning": "Not found in local database (external APIs blocked)"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "medication": medication_name,
                "error": str(e)
            }
    
    def check_drug_interactions(self, medications: List[str]) -> Dict:
        """Check basic drug interactions using offline rules"""
        try:
            if len(medications) < 2:
                return {
                    "has_interactions": False,
                    "message": "Need at least 2 medications"
                }
            
            # Get drug classes
            drug_classes = []
            validated_meds = []
            
            for med in medications:
                result = self.validate_medication(med)
                if result.get("valid"):
                    validated_meds.append(med)
                    drug_classes.append(result.get("drug_class"))
            
            if len(validated_meds) < 2:
                return {
                    "has_interactions": False,
                    "message": f"Only {len(validated_meds)} medications validated",
                    "checked_medications": validated_meds
                }
            
            # Basic interaction rules
            interactions = []
            
            # Check for multiple NSAIDs
            nsaid_count = drug_classes.count("NSAID")
            if nsaid_count > 1:
                interactions.append({
                    "description": "Multiple NSAIDs detected. May increase risk of GI bleeding.",
                    "severity": "moderate"
                })
            
            # Check for multiple anticonvulsants
            anticonvulsant_count = drug_classes.count("Anticonvulsant")
            if anticonvulsant_count > 1:
                interactions.append({
                    "description": "Multiple anticonvulsants. Monitor drug levels and adjust doses.",
                    "severity": "moderate"
                })
            
            return {
                "has_interactions": len(interactions) > 0,
                "interaction_count": len(interactions),
                "interactions": interactions,
                "checked_medications": validated_meds,
                "method": "offline_rules"
            }
            
        except Exception as e:
            return {
                "has_interactions": False,
                "error": str(e)
            }
    
    def validate_icd10_code(self, condition_name: str) -> Dict:
        """Validate ICD-10 using offline database"""
        try:
            # Normalize condition name
            clean_name = condition_name.lower().strip()
            
            # Direct match
            if clean_name in self.common_icd10:
                return {
                    "valid": True,
                    "condition": condition_name,
                    "icd10_codes": [{
                        "code": self.common_icd10[clean_name],
                        "description": condition_name
                    }],
                    "primary_code": self.common_icd10[clean_name],
                    "status": "verified_offline",
                    "source": "local_database"
                }
            
            # Partial matching
            for known_condition, code in self.common_icd10.items():
                if known_condition in clean_name or clean_name in known_condition:
                    return {
                        "valid": True,
                        "condition": condition_name,
                        "icd10_codes": [{
                            "code": code,
                            "description": known_condition
                        }],
                        "primary_code": code,
                        "status": "matched_offline",
                        "matched_to": known_condition,
                        "source": "local_database"
                    }
            
            return {
                "valid": False,
                "condition": condition_name,
                "status": "not_in_local_database",
                "warning": "Not found in local database (external APIs blocked)"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "condition": condition_name,
                "error": str(e)
            }
    
    def validate_fhir_resource(self, resource: Dict) -> Dict:
        """Validate FHIR resource structure (basic checks)"""
        try:
            resource_type = resource.get("resourceType")
            resource_id = resource.get("id", "unknown")
            
            if not resource_type:
                return {
                    "valid": False,
                    "error": "No resourceType specified"
                }
            
            # Basic structural validation
            required_fields = {
                "Patient": ["name", "gender"],
                "Observation": ["code", "subject"],
                "Condition": ["code", "subject"],
                "MedicationRequest": ["medicationCodeableConcept", "subject"],
                "Procedure": ["code", "subject"]
            }
            
            if resource_type in required_fields:
                missing = []
                for field in required_fields[resource_type]:
                    if field not in resource:
                        missing.append(field)
                
                if missing:
                    return {
                        "valid": False,
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "error": f"Missing required fields: {', '.join(missing)}",
                        "validation_method": "offline_structural"
                    }
            
            return {
                "valid": True,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "status": "structurally_valid",
                "validation_method": "offline_structural"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "resource_type": resource.get("resourceType", "Unknown"),
                "error": str(e)
            }
    
    def validate_extracted_data(self, extracted_data: Dict) -> Dict:
        """Main validation function"""
        
        print("\n" + "="*80)
        print("🔍 MCP VALIDATION STARTED (OFFLINE MODE)")
        print("="*80)
        print("ℹ️  Note: Using offline validation due to API restrictions")
        print()
        
        validation_results = {
            "medications": {
                "home": [],
                "hospital": []
            },
            "drug_interactions": {},
            "conditions": [],
            "overall_status": "success",
            "total_validated": 0,
            "total_warnings": 0,
            "validation_mode": "offline"
        }
        
        # Validate Home Medications
        if extracted_data.get("home_medications"):
            print(f"📋 Validating {len(extracted_data['home_medications'])} home medications...")
            for med in extracted_data["home_medications"]:
                med_name = med.get("name")
                if med_name:
                    result = self.validate_medication(med_name)
                    validation_results["medications"]["home"].append(result)
                    
                    if result.get("valid"):
                        print(f"   ✓ {med_name}: {result.get('drug_class')} (RxCUI: {result.get('rxcui')})")
                        validation_results["total_validated"] += 1
                    else:
                        print(f"   ⚠ {med_name}: {result.get('warning', 'Not validated')}")
                        validation_results["total_warnings"] += 1
        
        # Validate Hospital Medications
        if extracted_data.get("hospital_medications"):
            print(f"\n📋 Validating {len(extracted_data['hospital_medications'])} hospital medications...")
            for med in extracted_data["hospital_medications"]:
                med_name = med.get("name")
                if med_name:
                    result = self.validate_medication(med_name)
                    validation_results["medications"]["hospital"].append(result)
                    
                    if result.get("valid"):
                        print(f"   ✓ {med_name}: {result.get('drug_class')} (RxCUI: {result.get('rxcui')})")
                        validation_results["total_validated"] += 1
                    else:
                        print(f"   ⚠ {med_name}: {result.get('warning', 'Not validated')}")
                        validation_results["total_warnings"] += 1
        
        # Check Drug Interactions
        all_meds = []
        if extracted_data.get("home_medications"):
            all_meds.extend([m.get("name") for m in extracted_data["home_medications"] if m.get("name")])
        if extracted_data.get("hospital_medications"):
            all_meds.extend([m.get("name") for m in extracted_data["hospital_medications"] if m.get("name")])
        
        if len(all_meds) >= 2:
            print(f"\n💊 Checking drug interactions for {len(all_meds)} medications...")
            interaction_result = self.check_drug_interactions(all_meds)
            validation_results["drug_interactions"] = interaction_result
            
            if interaction_result.get("has_interactions"):
                count = interaction_result.get("interaction_count", 0)
                print(f"   ⚠ ALERT: {count} potential interactions detected!")
                for idx, interaction in enumerate(interaction_result.get("interactions", []), 1):
                    print(f"      {idx}. {interaction.get('description')}")
                validation_results["overall_status"] = "warning"
            else:
                print(f"   ✓ No obvious drug interactions detected")
        
        # Validate Conditions
        if extracted_data.get("conditions"):
            conditions_to_validate = extracted_data["conditions"][:10]
            print(f"\n🩺 Validating {len(conditions_to_validate)} conditions (ICD-10 codes)...")
            
            for condition in conditions_to_validate:
                cond_name = condition.get("condition_name")
                if cond_name:
                    result = self.validate_icd10_code(cond_name)
                    validation_results["conditions"].append(result)
                    
                    if result.get("valid"):
                        primary_code = result.get("primary_code", "N/A")
                        print(f"   ✓ {cond_name}: {primary_code}")
                        validation_results["total_validated"] += 1
                    else:
                        print(f"   ⚠ {cond_name}: Not in local database")
                        validation_results["total_warnings"] += 1
        
        # Summary
        print("\n" + "="*80)
        print("✅ MCP VALIDATION COMPLETED (OFFLINE MODE)")
        print("="*80)
        print(f"📊 Summary:")
        print(f"   • Successfully Validated: {validation_results['total_validated']}")
        print(f"   • Warnings: {validation_results['total_warnings']}")
        print(f"   • Validation Mode: Offline (Local Database)")
        print(f"   • Overall Status: {validation_results['overall_status'].upper()}")
        print("="*80 + "\n")
        
        return validation_results
    
    def validate_fhir_bundle(self, fhir_bundle: Dict) -> Dict:
        """Validate FHIR bundle resources"""
        
        print("\n" + "="*80)
        print("🔍 FHIR RESOURCE VALIDATION (OFFLINE MODE)")
        print("="*80 + "\n")
        
        validation_summary = {
            "total_resources": len(fhir_bundle.get("entry", [])),
            "validated": 0,
            "failed": 0,
            "sample_validations": [],
            "validation_mode": "offline_structural"
        }
        
        # Validate first 5 resources
        sample_entries = fhir_bundle.get("entry", [])[:5]
        
        print(f"📋 Validating {len(sample_entries)} sample FHIR resources (structural check)...")
        
        for entry in sample_entries:
            resource = entry.get("resource")
            if resource:
                result = self.validate_fhir_resource(resource)
                validation_summary["sample_validations"].append(result)
                
                if result.get("valid"):
                    validation_summary["validated"] += 1
                    print(f"   ✓ {result.get('resource_type')}/{result.get('resource_id')}: Valid")
                else:
                    validation_summary["failed"] += 1
                    error = result.get("error", "Unknown error")[:50]
                    print(f"   ⚠ {result.get('resource_type')}/{result.get('resource_id')}: {error}")
        
        print("\n" + "="*80)
        print("✅ FHIR VALIDATION COMPLETED")
        print("="*80)
        print(f"📊 Summary:")
        print(f"   • Validated: {validation_summary['validated']}/{len(sample_entries)}")
        print(f"   • Failed: {validation_summary['failed']}")
        print(f"   • Method: Structural validation (offline)")
        print("="*80 + "\n")
        
        return validation_summary

def create_validator():
    """Factory function"""
    return MCPValidator()

# ============================================================================
# BACKWARD COMPATIBILITY - For Dashboard Integration
# ============================================================================

def validate_fhir_bundle(fhir_bundle):
    """
    Simple FHIR bundle validation
    
    Args:
        fhir_bundle: FHIR Bundle dictionary
        
    Returns:
        Boolean - True if valid, False otherwise
    """
    try:
        # Basic validation checks
        if not isinstance(fhir_bundle, dict):
            return False
        
        if fhir_bundle.get("resourceType") != "Bundle":
            return False
        
        if "entry" not in fhir_bundle:
            return False
        
        # Check if bundle has resources
        entries = fhir_bundle.get("entry", [])
        if not isinstance(entries, list):
            return False
        
        # If we got here, it's valid
        return len(entries) > 0
    
    except Exception as e:
        print(f"Validation error: {e}")
        return False

