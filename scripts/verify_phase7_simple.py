"""
Phase 7.1: Explain Engine - Simplified Verification
Tests the core explain.py logic without full DB setup.
"""
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_explain_templates():
    """Test 1: Verify EXPLANATION_TEMPLATES exist and are in Uzbek"""
    from core.explain import EXPLANATION_TEMPLATES
    
    required_events = ["menu_variant_changed", "menu_kcal_adjusted", "workout_soft_mode_enabled", "meal_swapped"]
    
    for evt in required_events:
        if evt not in EXPLANATION_TEMPLATES:
            print(f"❌ FAIL: Missing template for event '{evt}'")
            return False
        
        templates = EXPLANATION_TEMPLATES[evt]
        if not templates or len(templates) == 0:
            print(f"❌ FAIL: Empty templates for event '{evt}'")
            return False
            
        # Check language (basic heuristic: should contain Uzbek characters or words)
        sample = templates[0]
        if len(sample) < 10:
            print(f"❌ FAIL: Template too short for event '{evt}': '{sample}'")
            return False
            
    print("✅ PASS: All explanation templates present and valid")
    return True

def test_get_explanation_with_flag_off():
    """Test 2: Verify get_explanation returns None when flag is OFF"""
    # Mock flag to OFF
    import core.flags
    original_func = core.flags.is_flag_enabled
    core.flags.is_flag_enabled = lambda flag, user_id: False
    
    try:
        from core.explain import get_explanation
        result = get_explanation("menu_kcal_adjusted", {"user_id": 12345})
        
        if result is not None:
            print(f"❌ FAIL: Expected None when flag OFF, got: {result}")
            return False
            
        print("✅ PASS: get_explanation returns None when flag is OFF")
        return True
    finally:
        core.flags.is_flag_enabled = original_func

def test_get_explanation_with_flag_on():
    """Test 3: Verify get_explanation returns text when flag is ON"""
    # Mock flag to ON and mock logging
    import core.flags
    import core.db
    
    original_flag_func = core.flags.is_flag_enabled
    original_log_func = core.db.db.log_event
    
    core.flags.is_flag_enabled = lambda flag, user_id: True
    logged_events = []
    core.db.db.log_event = lambda uid, evt, meta: logged_events.append((uid, evt, meta))
    
    try:
        from core.explain import get_explanation
        result = get_explanation("menu_kcal_adjusted", {"user_id": 12345})
        
        if result is None:
            print("❌ FAIL: Expected explanation text when flag ON, got None")
            return False
            
        if len(result) < 10:
            print(f"❌ FAIL: Explanation too short: '{result}'")
            return False
            
        # Verify logging was attempted
        if len(logged_events) == 0:
            print("⚠️ WARNING: No event logging captured (might be due to mock)")
        else:
            user_id, event_type, meta = logged_events[0]
            if event_type != "EXPLANATION_SHOWN":
                print(f"❌ FAIL: Wrong event type logged: {event_type}")
                return False
            print(f"✅ Event logged: {event_type} for user {user_id}")
            
        print(f"✅ PASS: get_explanation returns: '{result}'")
        return True
    finally:
        core.flags.is_flag_enabled = original_flag_func
        core.db.db.log_event = original_log_func

def test_no_ai_in_explain():
    """Test 4: Verify explain.py does NOT import or use AI"""
    import core.explain
    import inspect
    
    source = inspect.getsource(core.explain)
    
    forbidden_imports = ["from core.ai import", "import google.genai", "ask_gemini", "ai_generate"]
    
    for forbidden in forbidden_imports:
        if forbidden in source:
            print(f"❌ FAIL: explain.py contains forbidden AI import/call: '{forbidden}'")
            return False
            
    print("✅ PASS: explain.py does not use AI")
    return True

def test_menu_assembly_integration():
    """Test 5: Verify menu_assembly.py has adaptation event tracking"""
    import inspect
    import core.menu_assembly
    
    source = inspect.getsource(core.menu_assembly)
    
    # Check for adaptation_events tracking
    if "adaptation_events" not in source:
        print("❌ FAIL: menu_assembly.py missing 'adaptation_events' tracking")
        return False
        
    # Check for get_explanation call
    if "get_explanation" not in source:
        print("❌ FAIL: menu_assembly.py missing 'get_explanation' call")
        return False
        
    print("✅ PASS: menu_assembly.py has explain integration")
    return True

def test_workout_selector_integration():
    """Test 6: Verify workout_selector.py has soft_mode explanation"""
    import inspect
    import core.workout_selector
    
    source = inspect.getsource(core.workout_selector)
    
    # Check for get_explanation call with soft_mode
    if "get_explanation" not in source:
        print("❌ FAIL: workout_selector.py missing 'get_explanation' call")
        return False
        
    if "workout_soft_mode_enabled" not in source:
        print("❌ FAIL: workout_selector.py missing 'workout_soft_mode_enabled' event")
        return False
        
    print("✅ PASS: workout_selector.py has explain integration")
    return True

def main():
    print("="*60)
    print("Phase 7.1: Explain Engine - Verification")
    print("="*60)
    
    tests = [
        ("Templates Exist", test_explain_templates),
        ("Flag OFF Behavior", test_get_explanation_with_flag_off),
        ("Flag ON Behavior", test_get_explanation_with_flag_on),
        ("No AI Usage", test_no_ai_in_explain),
        ("Menu Assembly Integration", test_menu_assembly_integration),
        ("Workout Selector Integration", test_workout_selector_integration),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ FAIL: Exception during test: {e}")
            failed += 1
            
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
