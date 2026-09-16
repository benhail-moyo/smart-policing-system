"""
Test script for multi-vehicle routing functionality.
Tests both single-depot and multi-depot scenarios.
"""
import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:5000"

def make_request(url, data):
    """Helper function to make HTTP requests."""
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.getcode(), json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode('utf-8')}
    except Exception as e:
        return 500, {"error": str(e)}

def test_single_vehicle_routing():
    """Test single vehicle routing (regression test)."""
    print("Testing single vehicle routing...")
    
    # Test with vehicle_count=1 (should behave like original system)
    status_code, data = make_request(
        f"{BASE_URL}/api/v1/patrol/optimize",
        {
            "vehicle_count": 1,
            "algorithm": "dijkstra"
        }
    )
    
    if status_code == 200:
        print(f"[PASS] Single vehicle routing successful")
        print(f"  Vehicle count: {data.get('vehicle_count')}")
        print(f"  Number of routes: {len(data.get('routes', []))}")
        print(f"  Partition sizes: {data.get('partition_metadata', {}).get('partition_sizes')}")
        return True
    else:
        print(f"[FAIL] Single vehicle routing failed: {status_code}")
        print(f"  Error: {data.get('error')}")
        return False

def test_multi_vehicle_single_depot():
    """Test multi-vehicle routing with single depot."""
    print("\nTesting multi-vehicle routing with single depot...")
    
    status_code, data = make_request(
        f"{BASE_URL}/api/v1/patrol/optimize",
        {
            "vehicle_count": 3,
            "algorithm": "dijkstra"
        }
    )
    
    if status_code == 200:
        print(f"[PASS] Multi-vehicle single depot routing successful")
        print(f"  Vehicle count: {data.get('vehicle_count')}")
        print(f"  Number of routes: {len(data.get('routes', []))}")
        print(f"  Partition sizes: {data.get('partition_metadata', {}).get('partition_sizes')}")
        print(f"  Load imbalance: {data.get('partition_metadata', {}).get('load_imbalance')}")
        print(f"  Fallback used: {data.get('partition_metadata', {}).get('fallback_used')}")
        return True
    else:
        print(f"[FAIL] Multi-vehicle single depot routing failed: {status_code}")
        print(f"  Error: {data.get('error')}")
        return False

def test_multi_vehicle_multi_depot():
    """Test multi-vehicle routing with multiple depots."""
    print("\nTesting multi-vehicle routing with multiple depots...")
    
    # Harare area coordinates for different sub-depots
    depot_locations = [
        (-17.8292, 31.0522),  # Central Harare
        (-17.8252, 31.0475),  # Mbare area
        (-17.8189, 31.0433)   # Highlands area
    ]
    
    status_code, data = make_request(
        f"{BASE_URL}/api/v1/patrol/optimize",
        {
            "vehicle_count": 3,
            "depot_locations": depot_locations,
            "algorithm": "dijkstra"
        }
    )
    
    if status_code == 200:
        print(f"[PASS] Multi-vehicle multi-depot routing successful")
        print(f"  Vehicle count: {data.get('vehicle_count')}")
        print(f"  Number of routes: {len(data.get('routes', []))}")
        print(f"  Partition sizes: {data.get('partition_metadata', {}).get('partition_sizes')}")
        print(f"  Load imbalance: {data.get('partition_metadata', {}).get('load_imbalance')}")
        print(f"  Fallback used: {data.get('partition_metadata', {}).get('fallback_used')}")
        
        # Check if routes have different vehicle IDs
        vehicle_ids = [route.get('vehicle_id') for route in data.get('routes', [])]
        print(f"  Vehicle IDs: {vehicle_ids}")
        
        return True
    else:
        print(f"[FAIL] Multi-vehicle multi-depot routing failed: {status_code}")
        print(f"  Error: {data.get('error')}")
        return False

def test_invalid_vehicle_count():
    """Test validation of invalid vehicle count."""
    print("\nTesting invalid vehicle count validation...")
    
    status_code, data = make_request(
        f"{BASE_URL}/api/v1/patrol/optimize",
        {
            "vehicle_count": 0,
            "algorithm": "dijkstra"
        }
    )
    
    if status_code == 400:
        print(f"[PASS] Invalid vehicle count properly rejected")
        return True
    else:
        print(f"[FAIL] Invalid vehicle count validation failed: {status_code}")
        return False

def test_invalid_depot_locations():
    """Test validation of invalid depot locations."""
    print("\nTesting invalid depot locations validation...")
    
    status_code, data = make_request(
        f"{BASE_URL}/api/v1/patrol/optimize",
        {
            "vehicle_count": 3,
            "depot_locations": [(-17.8292, 31.0522)],  # Only 1 depot for 3 vehicles
            "algorithm": "dijkstra"
        }
    )
    
    if status_code == 400:
        print(f"[PASS] Invalid depot locations properly rejected")
        return True
    else:
        print(f"[FAIL] Invalid depot locations validation failed: {status_code}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Multi-Vehicle Routing Test Suite")
    print("=" * 60)
    
    results = []
    
    # Wait a moment for server to be ready
    import time
    time.sleep(2)
    
    results.append(("Single Vehicle", test_single_vehicle_routing()))
    results.append(("Multi-Vehicle Single Depot", test_multi_vehicle_single_depot()))
    results.append(("Multi-Vehicle Multi-Depot", test_multi_vehicle_multi_depot()))
    results.append(("Invalid Vehicle Count", test_invalid_vehicle_count()))
    results.append(("Invalid Depot Locations", test_invalid_depot_locations()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! [PASS]")
    else:
        print(f"{total - passed} test(s) failed. [FAIL]")
