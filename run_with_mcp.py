"""
MCP Integration Wrapper
Runs your existing extraction and adds MCP validation
Does NOT modify test_extraction.py
"""

import json
import re
from pathlib import Path

# Import your existing extraction functions (NO CHANGES TO ORIGINAL)
from test_extraction import (
    extract_pdf_text,
    extract_clinical_data,
    clean_json_response,
    map_to_fhir
)

# Import new MCP validator
from mcp_validator import create_validator


def fix_json(json_text):
    """
    Robust JSON repair function
    Fixes common AI-generated JSON errors
    """
    # Remove trailing commas before closing brackets/braces
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
    
    # Fix multiple consecutive commas
    json_text = re.sub(r',\s*,', ',', json_text)
    
    # Remove newlines within strings (can break JSON)
    # But preserve structure newlines
    json_text = re.sub(r':\s*"([^"]*)\n([^"]*)"', r': "\1 \2"', json_text)
    
    # Fix common escape issues
    json_text = json_text.replace('\\\n', ' ')
    
    return json_text


def parse_json_with_recovery(json_text, max_attempts=3):
    """
    Parse JSON with automatic error recovery
    Attempts multiple repair strategies
    """
    
    for attempt in range(max_attempts):
        try:
            # Attempt 1: Direct parse
            if attempt == 0:
                return json.loads(json_text)
            
            # Attempt 2: Apply basic fixes
            elif attempt == 1:
                print(f"   ⚠️  JSON parse failed, attempting auto-repair (attempt {attempt + 1}/{max_attempts})...")
                fixed_json = fix_json(json_text)
                return json.loads(fixed_json)
            
            # Attempt 3: Aggressive cleanup
            elif attempt == 2:
                print(f"   ⚠️  Attempting aggressive repair (attempt {attempt + 1}/{max_attempts})...")
                # Remove all problematic characters
                fixed_json = json_text.replace('\n', ' ').replace('\r', ' ')
                fixed_json = re.sub(r',\s*([}\]])', r'\1', fixed_json)
                fixed_json = re.sub(r'([{,])\s*,', r'\1', fixed_json)
                return json.loads(fixed_json)
                
        except json.JSONDecodeError as e:
            if attempt == max_attempts - 1:
                # Last attempt failed - provide detailed error
                print(f"\n❌ JSON Parse Error after {max_attempts} attempts:")
                print(f"   Location: Line {e.lineno}, Column {e.colno}")
                print(f"   Error: {e.msg}")
                
                # Show problematic section
                lines = json_text.split('\n')
                if e.lineno > 0 and e.lineno <= len(lines):
                    print(f"\n   Problematic section:")
                    start = max(0, e.lineno - 3)
                    end = min(len(lines), e.lineno + 3)
                    for i in range(start, end):
                        marker = ">>> ERROR" if i == e.lineno - 1 else "   "
                        line_preview = lines[i][:100] + "..." if len(lines[i]) > 100 else lines[i]
                        print(f"   {marker} Line {i+1}: {line_preview}")
                
                # Save broken JSON for debugging
                debug_file = Path("output") / "debug_broken_json.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(json_text)
                print(f"\n   💾 Saved broken JSON to: {debug_file}")
                print(f"   💡 Tip: Check this file for manual inspection\n")
                
                raise  # Re-raise the exception
            
            # Continue to next attempt
            json_text = fix_json(json_text)


def main():
    print("=" * 80)
    print("🏥 CLINICAL FHIR EXTRACTION WITH MCP VALIDATION")
    print("=" * 80)
    print()
    
    try:
        # Initialize MCP Validator
        mcp = create_validator()
        
        # STEP 1: Run your existing extraction (unchanged)
        pdf_path = "data/Cynthia-data.pdf"
        print("STEP 1: Extracting data from PDF...")
        text = extract_pdf_text(pdf_path)
        
        # STEP 2: Extract clinical data (unchanged)
        print("\nSTEP 2: Extracting clinical information...")
        raw_response = extract_clinical_data(text)
        json_text = clean_json_response(raw_response)
        
        # IMPROVED: Parse with automatic error recovery
        print("   Parsing JSON response...")
        extracted_data = parse_json_with_recovery(json_text)
        print("✅ Extraction completed!\n")
        
        # STEP 3: NEW - Validate with MCP
        print("STEP 3: Validating with MCP...")
        mcp_validation = mcp.validate_extracted_data(extracted_data)
        
        # Add validation results to extracted data
        extracted_data["mcp_validation"] = mcp_validation
        
        # Save validated extracted data
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        validated_file = output_dir / "extracted_data_with_mcp.json"
        with open(validated_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved validated data: {validated_file}")
        
        # STEP 4: Convert to FHIR (unchanged)
        print("\nSTEP 4: Converting to FHIR...")
        fhir_bundle = map_to_fhir(extracted_data)
        
        # STEP 5: NEW - Validate FHIR with MCP
        print("\nSTEP 5: Validating FHIR bundle...")
        fhir_validation = mcp.validate_fhir_bundle(fhir_bundle)
        
        # Add validation to bundle
        fhir_bundle["mcp_validation"] = fhir_validation
        
        # Save validated FHIR
        fhir_file = output_dir / "fhir_resources_with_mcp.json"
        with open(fhir_file, 'w', encoding='utf-8') as f:
            json.dump(fhir_bundle, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved validated FHIR: {fhir_file}")
        
        # Final Summary
        print("\n" + "=" * 80)
        print("🎉 COMPLETE PIPELINE FINISHED")
        print("=" * 80)
        print("\n📂 Output Files:")
        print(f"   1. Validated Data: {validated_file}")
        print(f"   2. Validated FHIR: {fhir_file}")
        print("\n📊 Validation Summary:")
        print(f"   • Items Validated: {mcp_validation.get('total_validated', 0)}")
        print(f"   • Warnings: {mcp_validation.get('total_warnings', 0)}")
        print(f"   • Status: {mcp_validation.get('overall_status', 'unknown').upper()}")
        print("=" * 80 + "\n")
        
    except json.JSONDecodeError as e:
        print(f"\n❌ CRITICAL ERROR: Unable to parse Gemini response after multiple attempts")
        print(f"\n💡 Troubleshooting steps:")
        print(f"   1. Check output/debug_broken_json.txt for details")
        print(f"   2. This usually means Gemini returned malformed JSON")
        print(f"   3. Try running again (AI responses can vary)")
        print(f"   4. If persistent, reduce max_output_tokens in test_extraction.py\n")
        
    except KeyError as e:
        print(f"\n❌ DATA ERROR: Missing expected field in extraction: {e}")
        print(f"   This means the JSON structure was unexpected")
        print(f"   Check if Gemini changed its output format\n")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        print(f"\n📋 Full error details:")
        import traceback
        traceback.print_exc()
        print()

# ============================================================================
# BACKWARD COMPATIBILITY - For Dashboard Integration
# ============================================================================

def process_clinical_text_to_fhir(clinical_text, patient_id="patient-001"):
    """
    Process clinical text and convert to FHIR format
    
    Args:
        clinical_text: Raw clinical text extracted from PDF/image
        patient_id: Patient identifier
        
    Returns:
        FHIR Bundle dictionary
    """
    try:
        # Extract clinical data using Gemini
        print("🤖 Extracting clinical information...")
        raw_response = extract_clinical_data(clinical_text)
        
        # Clean JSON
        json_text = clean_json_response(raw_response)
        
        # Parse with recovery
        extracted_data = parse_json_with_recovery(json_text)
        
        # Convert to FHIR
        print("🏥 Converting to FHIR...")
        fhir_bundle = map_to_fhir(extracted_data)
        
        print("✅ FHIR conversion complete!")
        return fhir_bundle
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [],
            "error": str(e)
        }

if __name__ == "__main__":
    main()
