"""
Test script for Claims Database connection and analytics
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.claims.claims_db import get_claims_db, get_claims_session
from app.services.claims_analytics_service import ClaimsAnalyticsService
from app.models.msig_claims import MSIGClaim
import structlog

logger = structlog.get_logger()


def test_connection():
    """Test basic database connectivity"""
    print("\n" + "="*60)
    print("Test 1: Database Connection")
    print("="*60)
    
    claims_db = get_claims_db()
    success = claims_db.test_connection()
    
    if success:
        print("✅ Connected to PostgreSQL claims database")
    else:
        print("❌ Failed to connect to claims database")
        return False
    
    return True


def test_query_claims():
    """Test basic claims query"""
    print("\n" + "="*60)
    print("Test 2: Query Claims Data")
    print("="*60)
    
    try:
        claims_db = get_claims_db()
        session = claims_db.get_session()
        
        # Count total claims
        total_claims = session.query(MSIGClaim).count()
        print(f"✅ Total claims in database: {total_claims:,}")
        
        # Get sample claims
        sample_claims = session.query(MSIGClaim).limit(5).all()
        print(f"\n📋 Sample Claims (first 5):")
        print("-" * 60)
        
        for claim in sample_claims:
            print(f"  Claim: {claim.claim_number}")
            print(f"  Destination: {claim.destination}")
            print(f"  Type: {claim.claim_type}")
            print(f"  Amount: SGD ${float(claim.net_incurred or 0):,.2f}")
            print(f"  Date: {claim.accident_date}")
            print("-" * 60)
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error querying claims: {e}")
        return False


def test_destination_analysis():
    """Test destination risk analysis"""
    print("\n" + "="*60)
    print("Test 3: Destination Risk Analysis")
    print("="*60)
    
    try:
        claims_db = get_claims_db()
        session = claims_db.get_session()
        
        analytics = ClaimsAnalyticsService(session)
        
        # Test with common destinations
        destinations = ["Japan", "Thailand", "USA", "Australia"]
        
        for destination in destinations:
            print(f"\n🌏 Analyzing: {destination}")
            print("-" * 60)
            
            result = analytics.get_destination_risk_profile(destination)
            
            if result.get("total_claims", 0) > 0:
                print(f"  Total Claims: {result['total_claims']}")
                print(f"  Average Claim: SGD ${result['avg_claim_amount_sgd']:,.2f}")
                print(f"  Risk Level: {result['risk_level'].upper()}")
                print(f"\n  Top Claim Types:")
                for claim_type in result.get("top_claim_types", [])[:3]:
                    print(f"    - {claim_type['type']}: {claim_type['count']} ({claim_type['percentage']}%)")
                print(f"\n  💡 Recommendation:")
                print(f"     {result['recommendation']}")
            else:
                print(f"  ⚠️  No claims data available")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error in destination analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_claim_type_analysis():
    """Test claim type statistics"""
    print("\n" + "="*60)
    print("Test 4: Claim Type Analysis")
    print("="*60)
    
    try:
        claims_db = get_claims_db()
        session = claims_db.get_session()
        
        analytics = ClaimsAnalyticsService(session)
        
        # Test common claim types
        claim_types = ["Medical", "Baggage", "Cancellation", "Delay"]
        
        for claim_type in claim_types:
            print(f"\n🏥 Analyzing: {claim_type} Claims")
            print("-" * 60)
            
            result = analytics.get_claim_type_statistics(claim_type)
            
            if result.get("total_claims", 0) > 0:
                print(f"  Total Claims: {result['total_claims']}")
                print(f"  Average: SGD ${result['avg_claim_amount_sgd']:,.2f}")
                print(f"  Median (P50): SGD ${result['median_claim_sgd']:,.2f}")
                print(f"  75th Percentile: SGD ${result['p75_claim_sgd']:,.2f}")
                print(f"  90th Percentile: SGD ${result['p90_claim_sgd']:,.2f}")
            else:
                print(f"  ⚠️  No data for this claim type")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error in claim type analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_comprehensive_analysis():
    """Test comprehensive risk analysis"""
    print("\n" + "="*60)
    print("Test 5: Comprehensive Risk Analysis")
    print("="*60)
    
    try:
        claims_db = get_claims_db()
        session = claims_db.get_session()
        
        analytics = ClaimsAnalyticsService(session)
        
        # Test with Japan (popular ski destination)
        destination = "Japan"
        claim_types = ["Medical", "Accident"]
        
        print(f"\n🎯 Comprehensive Analysis: {destination}")
        print("-" * 60)
        
        result = analytics.get_comprehensive_risk_analysis(destination, claim_types)
        
        print(f"\n  Overall Risk Level: {result['overall_risk_level'].upper()}")
        
        recommendation = result.get("recommendation", {})
        print(f"\n  💡 Recommendations:")
        print(f"     Medical Limit: SGD ${recommendation.get('recommended_medical_limit_sgd', 0):,.0f}")
        print(f"     Policy Tier: {recommendation.get('policy_tier_suggestion', 'N/A')}")
        
        print(f"\n  📊 Key Considerations:")
        for consideration in recommendation.get("key_considerations", []):
            print(f"     - {consideration}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error in comprehensive analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🏥 MSIG Claims Database - Test Suite")
    print("="*80)
    
    tests = [
        ("Connection Test", test_connection),
        ("Query Test", test_query_claims),
        ("Destination Analysis", test_destination_analysis),
        ("Claim Type Analysis", test_claim_type_analysis),
        ("Comprehensive Analysis", test_comprehensive_analysis),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 Test Summary")
    print("="*80)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print("\n" + "="*80)
    print(f"Overall: {passed}/{total} tests passed")
    print("="*80)
    
    return all(success for _, success in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

