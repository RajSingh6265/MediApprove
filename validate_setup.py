

from pathlib import Path
from policy_vectordb import PolicyVectorDatabase
from insurance_approval_agent import InsuranceApprovalAgent

print("=" * 80)
print("🔍 VALIDATING SETUP")
print("=" * 80)
print()

# Check 1: Policy database
print("1️⃣  Checking Policy Database...")
db_path = Path("policy_db")

if not db_path.exists():
    print("❌ Policy database does not exist")
    print("FIX: Run: python policy_vectordb.py")
    exit(1)

try:
    db = PolicyVectorDatabase(db_path="policy_db")
    summary = db.get_policy_summary()
    
    print(f"✅ Database loaded successfully")
    print(f"   Total chunks: {summary['total_chunks']}")
    print(f"   Pages covered: {summary['pages_covered']}")
    
    if summary['total_chunks'] == 0:
        print("❌ ERROR: No chunks in database!")
        print("FIX: Run: python policy_vectordb.py")
        exit(1)
    
except Exception as e:
    print(f"❌ Error loading database: {e}")
    print("FIX: Delete and rebuild:")
    print("   rm -r policy_db")
    print("   python policy_vectordb.py")
    exit(1)

print()

# Check 2: Search functionality
print("2️⃣  Testing Search Functionality...")

try:
    test_query = "chronic pain conservative therapy"
    results = db.search_policy(test_query, top_k=3)
    
    if results is None:
        print("❌ ERROR: search_policy returned None!")
        exit(1)
    
    if len(results) == 0:
        print("⚠️ WARNING: No search results found")
    else:
        print(f"✅ Search working - found {len(results)} results")
        
        # Validate result format
        for i, result in enumerate(results):
            try:
                text, distance, metadata = result
                page = metadata.get('page_number', 'Unknown')
                print(f"   Result {i+1}: Page {page}, Distance {distance:.4f}")
            except ValueError as e:
                print(f"❌ ERROR: Result format invalid at index {i}: {e}")
                exit(1)

except Exception as e:
    print(f"❌ Error testing search: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()

# Check 3: Insurance Agent
print("3️⃣  Testing Insurance Agent...")

try:
    agent = InsuranceApprovalAgent(db)
    
    # Test with sample FHIR data
    test_fhir = {
        "entry": [
            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {"text": "Chronic lower back pain"}
                }
            },
            {
                "resource": {
                    "resourceType": "Procedure",
                    "code": {"text": "Physical therapy"}
                }
            }
        ]
    }
    
    report = agent.evaluate_approval(test_fhir)
    
    if report is None:
        print("❌ ERROR: evaluate_approval returned None!")
        exit(1)
    
    print(f"✅ Agent working")
    print(f"   Decision: {report['decision']}")
    print(f"   Category: {report['detected_category']['name']}")
    print(f"   Policy refs: {len(report['policy_references'])}")

except Exception as e:
    print(f"❌ Error testing agent: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("=" * 80)
print("✅ ALL VALIDATIONS PASSED!")
print("=" * 80)
print()
print("Your system is ready to use!")
