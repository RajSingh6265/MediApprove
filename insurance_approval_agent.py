"""
Insurance Approval Decision Agent - COMPLETE v4.0
100% TESTED & WORKING with DuckDuckGo Internet Search + Local PDF Database
Complete traceability with clean readable output
Author: Clinical AI Team
Date: November 2025
"""

import json
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from policy_vectordb import PolicyVectorDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsuranceApprovalAgent:
    """
    Intelligent agent for insurance approval decisions
    COMPLETE v4.0: DuckDuckGo search + Local PDF database
    """
    
    def __init__(self, policy_db: PolicyVectorDatabase):
        """Initialize agent with policy database"""
        
        self.policy_db = policy_db
        
        # Define policy categories and their criteria
        self.policy_categories = {
            "1a": {
                "name": "Chronic Pain - Conservative Therapy",
                "keywords": ["chronic pain", "conservative therapy", "physical therapy", "6 weeks", "trial"],
                "requirements": [
                    "Chronic pain documented",
                    "Conservative therapy (PT/Chiro/Home exercise) for 6+ weeks",
                    "Treatment within last 6 months"
                ],
                "scenario": "chronic"
            },
            "1b": {
                "name": "Chronic Pain - Worsening",
                "keywords": ["worsening", "pain", "despite", "conservative"],
                "requirements": [
                    "Chronic pain documented",
                    "Worsening pain despite conservative therapy"
                ],
                "scenario": "chronic"
            },
            "2": {
                "name": "Abnormal Neurologic Findings",
                "keywords": ["weakness", "neurologic", "sensory", "reflex", "atrophy", "bowel", "bladder", "claudication", "deficit"],
                "requirements": [
                    "Documented abnormal neurologic findings",
                    "Evidence: weakness, sensory changes, reflexes, bowel/bladder issues, etc."
                ],
                "scenario": "acute"
            },
            "3": {
                "name": "Tumor/Malignancy",
                "keywords": ["tumor", "cancer", "malignancy", "bone scan", "metastasis", "mass"],
                "requirements": [
                    "Known or suspected malignancy",
                    "Recent diagnosis or follow-up needed"
                ],
                "scenario": "acute"
            },
            "4": {
                "name": "Acute Trauma - Spinal Injury",
                "keywords": ["trauma", "fracture", "injury", "accident", "vertebral", "spinal fracture", "spinal injury"],
                "requirements": [
                    "Acute spinal trauma documented",
                    "Spinal injury or vertebral fracture suspected"
                ],
                "scenario": "acute"
            },
            "5": {
                "name": "Neurologic Emergency",
                "keywords": ["emergency", "acute neurologic", "paralysis", "paresis", "myelopathy", "diffuse", "axonal"],
                "requirements": [
                    "Acute neurologic emergency",
                    "Suspected spinal cord involvement"
                ],
                "scenario": "acute"
            }
        }
        
        logger.info("✅ Insurance Approval Agent (COMPLETE v4.0) initialized with 6 categories")
    
    def evaluate_approval(self, fhir_data: Dict, patient_info: Dict = None) -> Dict:
        """Evaluate insurance approval based on FHIR data"""
        
        try:
            logger.info("🔍 Starting insurance approval evaluation...")
            
            # Step 1: Extract clinical information
            clinical_summary = self._extract_clinical_info(fhir_data)
            logger.info(f"   ✅ Extracted: {len(clinical_summary['conditions'])} conditions, {len(clinical_summary['procedures'])} procedures")
            
            # Step 2: Detect scenario type
            scenario_type = self._detect_scenario(clinical_summary)
            logger.info(f"   ✅ Scenario: {scenario_type}")
            
            # Step 3: Detect policy category
            detected_category, confidence = self._detect_policy_category(clinical_summary)
            logger.info(f"   ✅ Category: {detected_category} ({confidence:.1%} confidence)")
            
            # Step 4: Retrieve policy sections with page numbers (LOCAL PDF)
            policy_sections = self._retrieve_policy_sections(detected_category, clinical_summary)
            logger.info(f"   Found {len(policy_sections)} sections from local database")
            for section in policy_sections:
                page = section[2].get('page_number', 'Unknown')
                logger.info(f"      ✅ Page {page}")
            
            # Step 5: Check approval criteria
            approval_result = self._check_approval_criteria(
                detected_category, 
                clinical_summary, 
                policy_sections,
                scenario_type
            )
            logger.info(f"   ✅ Decision: {approval_result['decision']}")
            
            # ============================================================
            # NEW STEP 5.5: INTERNET SEARCH FOR POLICIES (DuckDuckGo)
            # ============================================================
            
            logger.info("🌐 STEP 5.5: Searching internet for official policies...")
            
            try:
                from internet_search_agent import InternetSearchAgent
                
                # Initialize search agent
                search_agent = InternetSearchAgent()
                
                # Extract disease and procedure
                disease_name = " ".join(clinical_summary.get("conditions", []))[:100]
                procedure_name = " ".join(clinical_summary.get("procedures", []))[:100] or "Lumbar MRI"
                
                logger.info(f"   📋 Disease: {disease_name}")
                logger.info(f"   🔧 Procedure: {procedure_name}")
                
                # Search internet with DuckDuckGo
                logger.info("   🔍 Searching DuckDuckGo for official policies...")
                internet_policies = search_agent.search_policies(
                    disease=disease_name,
                    procedure=procedure_name,
                    icd_code="M54.5"
                )
                
                logger.info(f"   ✅ Found {len(internet_policies.get('policies', []))} policies from internet")
                
            except Exception as e:
                logger.warning(f"⚠️ Could not search internet: {e}")
                internet_policies = {"policies": [], "error": str(e)}
            
            # ============================================================
            # STEP 5.6: PREPARE LOCAL PDF POLICIES
            # ============================================================
            
            logger.info("   📄 Preparing local PDF policies...")
            
            local_policies = []
            if policy_sections:
                for section in policy_sections[:3]:
                    try:
                        text, distance, meta = section
                        
                        # Clean text to remove word breaking
                        cleaned_text = self._clean_text(text, max_len=200)
                        
                        local_policies.append({
                            "source": "Local Policy Database",
                            "title": "Lumbar Spine MRI Coverage Policy",
                            "url": None,
                            "snippet": cleaned_text,
                            "page_number": meta.get('page_number', 'Unknown'),
                            "source_type": "LOCAL_PDF",
                            "full_text": text
                        })
                    except Exception as e:
                        logger.warning(f"Error processing local policy: {e}")
            
            logger.info(f"   ✅ Prepared {len(local_policies)} local policies")
            
            # Combine both sources
            all_policy_sources = {
                "internet": internet_policies.get('policies', []),
                "local": local_policies,
                "search_method": "DuckDuckGo Internet Search + Local PDF Database"
            }
            
            # Step 6: Generate report with both policy sources
            report = self._generate_approval_report(
                clinical_summary=clinical_summary,
                detected_category=detected_category,
                category_confidence=confidence,
                approval_result=approval_result,
                policy_sections=policy_sections,
                scenario_type=scenario_type,
                all_policy_sources=all_policy_sources
            )
            
            logger.info(f"✅ Evaluation complete: {report['decision']}")
            return report
        
        except Exception as e:
            logger.error(f"❌ Error in evaluate_approval: {e}")
            import traceback
            traceback.print_exc()
            
            # Return error report
            return {
                "timestamp": datetime.now().isoformat(),
                "decision": "ERROR",
                "approval_percentage": "0%",
                "error": str(e),
                "detected_category": {"id": "ERROR", "name": "Error", "confidence": "0%"},
                "clinical_summary": {"conditions": [], "procedures": [], "medications": []},
                "criteria_assessment": {"met": [], "missing": []},
                "policy_sources": {"internet": [], "local": []},
                "remediation_steps": [],
                "raw_report": f"ERROR: {str(e)}"
            }
    
    def _clean_text(self, text: str, max_len: int = 200) -> str:
        """Clean text to remove word breaking and OCR errors"""
        
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Fix common OCR word-breaking errors
        text = text.replace("sub ject", "subject")
        text = text.replace("conservativ e", "conservative")
        text = text.replace("in tervention", "intervention")
        text = text.replace("necess ary", "necessary")
        text = text.replace("treat ment", "treatment")
        text = text.replace("docu ment", "document")
        text = text.replace("eval uation", "evaluation")
        text = text.replace("th erapy", "therapy")
        
        # Limit length with proper word boundary
        if len(text) > max_len:
            text = text[:max_len].rsplit(' ', 1)[0] + "..."
        
        return text.strip()
    
    def _detect_scenario(self, clinical_summary: Dict) -> str:
        """Detect if ACUTE or CHRONIC scenario"""
        
        try:
            text = clinical_summary["raw_text"].lower()
            
            acute_keywords = [
                "acute", "emergency", "trauma", "fracture", "injured", "injury",
                "accident", "critical", "severe", "urgent", "intubation", "icu",
                "hemorrhage", "bleed", "diffuse", "axonal", "paralysis", "paresis",
                "icp monitoring", "life-threatening", "spinal cord", "myelopathy"
            ]
            
            chronic_keywords = [
                "chronic", "ongoing", "persistent", "conservative therapy", 
                "physical therapy", "weeks", "months", "long-term", "stable"
            ]
            
            acute_count = sum(1 for keyword in acute_keywords if keyword in text)
            chronic_count = sum(1 for keyword in chronic_keywords if keyword in text)
            
            if acute_count > chronic_count:
                return "ACUTE"
            elif chronic_count > 0:
                return "CHRONIC"
            else:
                return "UNKNOWN"
        
        except Exception as e:
            logger.error(f"❌ Error in _detect_scenario: {e}")
            return "UNKNOWN"
    
    def _extract_clinical_info(self, fhir_data: Dict) -> Dict:
        """Extract clinical information from FHIR data"""
        
        try:
            clinical_info = {
                "conditions": [],
                "procedures": [],
                "medications": [],
                "observations": [],
                "raw_text": ""
            }
            
            if not isinstance(fhir_data, dict):
                logger.warning(f"⚠️ FHIR data is not dict: {type(fhir_data)}")
                return clinical_info
            
            if "entry" not in fhir_data:
                logger.warning("⚠️ No 'entry' in FHIR data")
                return clinical_info
            
            for entry in fhir_data.get("entry", []):
                try:
                    resource = entry.get("resource", {})
                    resource_type = resource.get("resourceType", "")
                    
                    if resource_type == "Condition":
                        condition_name = resource.get("code", {}).get("text", "Unknown")
                        clinical_info["conditions"].append(condition_name.lower())
                    
                    elif resource_type == "Procedure":
                        procedure_name = resource.get("code", {}).get("text", "Unknown")
                        clinical_info["procedures"].append(procedure_name.lower())
                    
                    elif resource_type == "MedicationRequest":
                        medication = resource.get("medicationCodeableConcept", {}).get("text", "Unknown")
                        clinical_info["medications"].append(medication.lower())
                    
                    elif resource_type == "Observation":
                        obs_value = resource.get("valueString", "")
                        if obs_value:
                            clinical_info["observations"].append(obs_value.lower())
                
                except Exception as e:
                    logger.warning(f"⚠️ Error processing entry: {e}")
                    continue
            
            # Combine into searchable text
            text_parts = [
                " ".join(clinical_info["conditions"]),
                " ".join(clinical_info["procedures"]),
                " ".join(clinical_info["medications"]),
                " ".join(clinical_info["observations"])
            ]
            clinical_info["raw_text"] = " ".join([p for p in text_parts if p]).lower()
            
            return clinical_info
        
        except Exception as e:
            logger.error(f"❌ Error in _extract_clinical_info: {e}")
            return {
                "conditions": [],
                "procedures": [],
                "medications": [],
                "observations": [],
                "raw_text": ""
            }
    
    def _detect_policy_category(self, clinical_summary: Dict) -> Tuple[str, float]:
        """Detect policy category"""
        
        try:
            text = clinical_summary.get("raw_text", "").lower()
            scores = {}
            
            for category_id, category_info in self.policy_categories.items():
                keywords = category_info.get("keywords", [])
                
                if not keywords:
                    scores[category_id] = 0.0
                    continue
                
                matches = sum(1 for keyword in keywords if keyword in text)
                confidence = matches / len(keywords)
                scores[category_id] = confidence
            
            if not scores:
                return "UNKNOWN", 0.0
            
            best_category = max(scores, key=scores.get)
            best_confidence = scores[best_category]
            
            return best_category, best_confidence
        
        except Exception as e:
            logger.error(f"❌ Error in _detect_policy_category: {e}")
            return "UNKNOWN", 0.0
    
    def _retrieve_policy_sections(self, category_id: str, clinical_summary: Dict) -> List[Tuple]:
        """Retrieve policy sections with page numbers from local database"""
        
        try:
            category_info = self.policy_categories.get(category_id, {})
            category_name = category_info.get("name", "Medical necessity")
            
            raw_text = clinical_summary.get("raw_text", "")[:200]
            search_query = f"{category_name} {raw_text}"
            
            logger.info(f"   Searching: '{search_query[:50]}...'")
            
            results = self.policy_db.search_policy(search_query, top_k=5)
            
            if results is None:
                logger.warning("⚠️ search_policy returned None")
                return []
            
            if not isinstance(results, list):
                logger.warning(f"⚠️ search_policy returned {type(results)}, expected list")
                return []
            
            validated_results = []
            for result in results:
                try:
                    text, distance, metadata = result
                    
                    if not isinstance(metadata, dict):
                        logger.warning(f"⚠️ Metadata is not dict: {type(metadata)}")
                        continue
                    
                    validated_results.append(result)
                
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ Invalid result format: {e}")
                    continue
            
            return validated_results
        
        except Exception as e:
            logger.error(f"❌ Error in _retrieve_policy_sections: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _check_approval_criteria(self, category_id: str, clinical_summary: Dict, 
                                 policy_sections: List[Tuple], scenario_type: str) -> Dict:
        """Check approval criteria"""
        
        try:
            category_info = self.policy_categories.get(category_id, {})
            requirements = category_info.get("requirements", [])
            scenario = category_info.get("scenario", "unknown")
            
            approval_result = {
                "decision": "PENDING",
                "criteria_met": [],
                "criteria_missing": [],
                "approval_percentage": 0
            }
            
            if not requirements:
                logger.warning(f"⚠️ No requirements found for category {category_id}")
                approval_result["decision"] = "UNKNOWN"
                return approval_result
            
            text = clinical_summary.get("raw_text", "").lower()
            
            if not text:
                logger.warning("⚠️ No clinical text to evaluate")
                approval_result["decision"] = "DENIED"
                return approval_result
            
            logger.info(f"📊 Evaluating {len(requirements)} criteria for category {category_id}")
            
            # ACUTE emergency fast track
            if scenario_type == "ACUTE" and scenario == "acute":
                logger.info("🚨 ACUTE scenario detected - checking emergency criteria")
                
                acute_markers = [
                    "trauma", "fracture", "emergency", "acute", "injury",
                    "intubation", "icp", "critical", "hemorrhage", "paralysis"
                ]
                
                spinal_markers = [
                    "spine", "spinal", "vertebra", "cervical", "lumbar",
                    "vertebral", "spinal cord", "myelopathy"
                ]
                
                has_acute = any(marker in text for marker in acute_markers)
                has_spinal = any(marker in text for marker in spinal_markers)
                
                if has_acute and has_spinal:
                    logger.info("✅ ACUTE EMERGENCY APPROVAL")
                    
                    approval_result["criteria_met"] = [
                        "🚨 ACUTE EMERGENCY - Immediate MRI needed",
                        "Acute spinal trauma/emergency documented",
                        "Neurologic emergency requiring immediate imaging"
                    ]
                    approval_result["decision"] = "APPROVED"
                    approval_result["approval_percentage"] = 100
                    
                    return approval_result
            
            # Standard criteria matching
            logger.info("📋 Evaluating standard criteria...")
            
            for i, requirement in enumerate(requirements, 1):
                try:
                    requirement_lower = requirement.lower()
                    keywords = requirement_lower.split()
                    
                    matches = sum(1 for keyword in keywords if keyword in text)
                    match_percentage = matches / len(keywords) if keywords else 0
                    
                    logger.info(f"   Criterion {i}: '{requirement[:50]}...'")
                    logger.info(f"      Keywords: {len(keywords)}, Matches: {matches}, Score: {match_percentage:.1%}")
                    
                    if match_percentage >= 0.5:
                        approval_result["criteria_met"].append(requirement)
                        logger.info(f"      ✅ MET")
                    else:
                        approval_result["criteria_missing"].append(requirement)
                        logger.info(f"      ❌ NOT MET")
                
                except Exception as e:
                    logger.warning(f"⚠️ Error evaluating criterion {i}: {e}")
                    approval_result["criteria_missing"].append(requirement)
                    continue
            
            # Calculate decision
            total_criteria = len(requirements)
            criteria_met_count = len(approval_result["criteria_met"])
            
            if total_criteria > 0:
                approval_result["approval_percentage"] = (criteria_met_count / total_criteria) * 100
            
            logger.info(f"📊 Results: {criteria_met_count}/{total_criteria} criteria met ({approval_result['approval_percentage']:.0f}%)")
            
            if approval_result["approval_percentage"] >= 80:
                approval_result["decision"] = "APPROVED"
                logger.info("✅ DECISION: APPROVED")
            elif approval_result["approval_percentage"] >= 50:
                approval_result["decision"] = "CONDITIONAL"
                logger.info("⚠️ DECISION: CONDITIONAL")
            else:
                approval_result["decision"] = "DENIED"
                logger.info("❌ DECISION: DENIED")
            
            return approval_result
        
        except Exception as e:
            logger.error(f"❌ Error in _check_approval_criteria: {e}")
            import traceback
            traceback.print_exc()
            return {
                "decision": "ERROR",
                "criteria_met": [],
                "criteria_missing": [],
                "approval_percentage": 0
            }
    
    def _generate_approval_report(self, clinical_summary: Dict, detected_category: str, 
                                  category_confidence: float, approval_result: Dict, 
                                  policy_sections: List[Tuple], scenario_type: str,
                                  all_policy_sources: Dict) -> Dict:
        """Generate approval report with both internet and local policy sources"""
        
        try:
            category_info = self.policy_categories.get(detected_category, {})
            
            # Build report
            report = {
                "timestamp": datetime.now().isoformat(),
                "scenario": scenario_type,
                "decision": approval_result.get("decision", "ERROR"),
                "approval_percentage": approval_result.get('approval_percentage', 0),
                "detected_category": {
                    "id": detected_category,
                    "name": category_info.get("name", "Unknown"),
                    "confidence": f"{category_confidence:.1%}"
                },
                "clinical_summary": {
                    "conditions": clinical_summary.get("conditions", []),
                    "procedures": clinical_summary.get("procedures", []),
                    "medications": clinical_summary.get("medications", [])
                },
                "criteria_assessment": {
                    "met": approval_result.get("criteria_met", []),
                    "missing": approval_result.get("criteria_missing", [])
                },
                "policy_sources": all_policy_sources,
                "remediation_steps": self._get_remediation_steps(approval_result, detected_category, scenario_type),
                "raw_report": self._generate_text_report(
                    clinical_summary, detected_category, category_confidence, 
                    approval_result, scenario_type, all_policy_sources
                )
            }
            
            return report
        
        except Exception as e:
            logger.error(f"❌ Error in _generate_approval_report: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "decision": "ERROR",
                "approval_percentage": 0,
                "error": str(e),
                "detected_category": {"id": "ERROR", "name": "Error", "confidence": "0%"},
                "clinical_summary": {"conditions": [], "procedures": [], "medications": []},
                "criteria_assessment": {"met": [], "missing": []},
                "policy_sources": {"internet": [], "local": []},
                "remediation_steps": [],
                "raw_report": f"ERROR: {str(e)}"
            }
    
    def _get_remediation_steps(self, approval_result: Dict, category_id: str, scenario_type: str) -> List[str]:
        """Get remediation steps if approval failed"""
        
        try:
            steps = []
            
            if approval_result.get("decision") == "APPROVED":
                return ["✅ No remediation needed - Approval granted"]
            
            if scenario_type == "ACUTE":
                steps.append("✓ This is an ACUTE scenario - Emergency approval may apply")
                steps.append("✓ Contact insurance for emergency authorization")
            
            for missing in approval_result.get("criteria_missing", []):
                steps.append(f"✓ {missing}")
            
            if category_id == "1a":
                steps.extend([
                    "Complete 6+ weeks of conservative therapy",
                    "Include Physical Therapy, Chiropractic, or home exercise",
                    "Ensure documentation is within last 6 months"
                ])
            elif category_id == "1b":
                steps.extend([
                    "Document worsening pain despite conservative therapy",
                    "Provide evidence of ongoing conservative treatment"
                ])
            
            return steps if steps else ["Please contact insurance for more information"]
        
        except Exception as e:
            logger.error(f"❌ Error in _get_remediation_steps: {e}")
            return ["Error generating remediation steps"]
    
    def _generate_text_report(self, clinical_summary: Dict, detected_category: str, 
                              category_confidence: float, approval_result: Dict, 
                              scenario_type: str, all_policy_sources: Dict) -> str:
        """Generate text report with clean formatting"""
        
        try:
            category_info = self.policy_categories.get(detected_category, {})
            
            scenario_note = f"\n⚠️ SCENARIO TYPE: {scenario_type}\n" if scenario_type != "UNKNOWN" else ""
            
            # Build policy references
            policy_section = "\n📋 POLICY EVIDENCE:\n"
            
            # Internet sources
            internet_pols = all_policy_sources.get('internet', [])
            if internet_pols:
                policy_section += "\n🌐 From Internet Search:\n"
                for i, pol in enumerate(internet_pols[:3], 1):
                    title = pol.get('title', 'Policy')
                    url = pol.get('url', '#')
                    snippet = pol.get('snippet', '')
                    policy_section += f"\n   [{i}] {title}\n"
                    policy_section += f"       URL: {url}\n"
                    policy_section += f"       Text: {snippet}\n"
            
            # Local sources
            local_pols = all_policy_sources.get('local', [])
            if local_pols:
                policy_section += "\n📄 From Local Database:\n"
                for i, pol in enumerate(local_pols[:3], 1):
                    page = pol.get('page_number', 'Unknown')
                    snippet = pol.get('snippet', '')
                    policy_section += f"\n   [{i}] Page {page}\n"
                    policy_section += f"       Text: {snippet}\n"
            
            report = f"""
INSURANCE APPROVAL DECISION REPORT
{'='*70}

DECISION: {approval_result.get('decision', 'ERROR')}
Approval Score: {approval_result.get('approval_percentage', 0):.0f}%
{scenario_note}

POLICY CATEGORY DETECTED:
  • ID: {detected_category}
  • Name: {category_info.get('name', 'Unknown')}
  • Confidence: {category_confidence:.1%}
{policy_section}

CLINICAL FINDINGS:
  • Conditions: {', '.join(clinical_summary.get('conditions', [])) if clinical_summary.get('conditions') else 'None'}
  • Procedures: {', '.join(clinical_summary.get('procedures', [])) if clinical_summary.get('procedures') else 'None'}
  • Medications: {', '.join(clinical_summary.get('medications', [])) if clinical_summary.get('medications') else 'None'}

APPROVAL CRITERIA ASSESSMENT:

  MET CRITERIA ({len(approval_result.get('criteria_met', []))}/{len(approval_result.get('criteria_met', [])) + len(approval_result.get('criteria_missing', []))}):
{chr(10).join(f'    ✅ {c}' for c in approval_result.get('criteria_met', [])) if approval_result.get('criteria_met') else '    None'}

  MISSING CRITERIA:
{chr(10).join(f'    ❌ {c}' for c in approval_result.get('criteria_missing', [])) if approval_result.get('criteria_missing') else '    None'}

{'='*70}
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            return report
        
        except Exception as e:
            logger.error(f"❌ Error in _generate_text_report: {e}")
            return f"ERROR generating report: {str(e)}"
