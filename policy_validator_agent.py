"""
Policy Validator Agent - COMPLETE v1.0
Compares local PDF policies with scraped official policies
Validates alignment and reports differences
"""

import logging
from typing import Dict, List
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class PolicyValidatorAgent:
    """
    Agent to validate and compare policies
    Checks if local PDF policy matches official scraped policies
    """
    
    def validate_policies(self, 
                         pdf_policy_text: str,
                         scraped_policies: Dict) -> Dict:
        """
        Validate if PDF policy matches scraped policies
        
        Args:
            pdf_policy_text: Text from local PDF policy
            scraped_policies: Policies scraped from web
            
        Returns:
            Validation result with match percentage
        """
        
        try:
            logger.info("🔍 Starting policy validation...")
            
            validation_result = {
                "pdf_policy": pdf_policy_text[:500] + "...",  # First 500 chars
                "scraped_policies": scraped_policies,
                "matches": [],
                "differences": [],
                "overall_match_percentage": 0,
                "validation_status": "UNKNOWN",
                "details": []
            }
            
            # Calculate similarity with each scraped policy
            if scraped_policies.get("ncd_policies"):
                logger.info(f"📊 Comparing with {len(scraped_policies['ncd_policies'])} NCD policies...")
                
                for policy in scraped_policies["ncd_policies"]:
                    similarity = self._calculate_similarity(
                        pdf_policy_text,
                        policy.get("text", "")
                    )
                    
                    logger.info(f"   NCD Policy '{policy.get('name')}': {similarity:.1%} match")
                    
                    match_info = {
                        "policy_type": "NCD",
                        "policy_name": policy.get("name"),
                        "similarity_percentage": similarity,
                        "source": policy.get("source"),
                        "url": policy.get("url")
                    }
                    
                    if similarity >= 0.70:
                        validation_result["matches"].append(match_info)
                    else:
                        validation_result["differences"].append(match_info)
            
            # Calculate overall match
            if validation_result["matches"]:
                total_similarity = sum(m["similarity_percentage"] for m in validation_result["matches"])
                avg_similarity = total_similarity / len(validation_result["matches"])
                validation_result["overall_match_percentage"] = avg_similarity
                
                if avg_similarity >= 0.80:
                    validation_result["validation_status"] = "ALIGNED"
                    logger.info("✅ Policies are ALIGNED (80%+ match)")
                elif avg_similarity >= 0.70:
                    validation_result["validation_status"] = "PARTIALLY_ALIGNED"
                    logger.info("⚠️ Policies are PARTIALLY ALIGNED (70%+ match)")
                else:
                    validation_result["validation_status"] = "NOT_ALIGNED"
                    logger.info("❌ Policies are NOT ALIGNED")
            else:
                validation_result["validation_status"] = "NO_MATCH"
                logger.warning("❌ No matching policies found")
            
            validation_result["details"] = {
                "pdf_text_preview": pdf_policy_text[:300],
                "total_matches": len(validation_result["matches"]),
                "total_differences": len(validation_result["differences"]),
                "validation_timestamp": str(__import__('datetime').datetime.now().isoformat())
            }
            
            return validation_result
        
        except Exception as e:
            logger.error(f"❌ Error in policy validation: {e}")
            return {
                "error": str(e),
                "validation_status": "ERROR"
            }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using SequenceMatcher"""
        
        try:
            if not text1 or not text2:
                return 0.0
            
            # Clean and normalize text
            text1_clean = text1.lower().strip()
            text2_clean = text2.lower().strip()
            
            # Calculate similarity
            matcher = SequenceMatcher(None, text1_clean, text2_clean)
            similarity = matcher.ratio()
            
            return similarity
        
        except Exception as e:
            logger.warning(f"⚠️ Error calculating similarity: {e}")
            return 0.0
