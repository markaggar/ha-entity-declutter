# Simple test script for delete_helpers
# Place this in /config/pyscript/test_delete_helpers.py

import builtins
import os

@service
def test_file_operations():
    """Test if file operations work in PyScript"""
    task.create(test_file_operations_async())

async def test_file_operations_async():
    """Test file reading capability"""
    
    log.info("=== Testing File Operations ===")
    
    test_file = '/config/helper_analysis/helper_analysis.json'
    
    if not os.path.exists(test_file):
        log.error(f"Test file not found: {test_file}")
        return
    
    try:
        # Test file reading with task.executor
        content = await task.executor(lambda path: builtins.open(path, 'r', encoding='utf-8').read(), test_file)
        
        if content:
            log.info(f"✓ Successfully read {len(content)} characters from {test_file}")
            
            # Test JSON parsing
            import json
            data = json.loads(content)
            log.info(f"✓ Successfully parsed JSON with {len(data)} keys")
            
            if 'analysis' in data:
                analysis = data['analysis']
                log.info(f"✓ Found analysis data: {analysis.get('total_helpers', 0)} total helpers")
            
        else:
            log.error("✗ File content was empty")
            
    except Exception as e:
        log.error(f"✗ File operation failed: {e}")
    
    log.info("=== File Operations Test Complete ===")