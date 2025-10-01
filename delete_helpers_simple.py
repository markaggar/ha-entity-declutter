# Simplified Helper Deletion Script for PyScript
# This version avoids all return statements to prevent PyScript errors

import builtins
import json
import os

@service
def delete_helpers_simple(**kwargs):
    """Simple dry run helper deletion service"""
    task.create(delete_helpers_simple_async())

async def delete_helpers_simple_async():
    """Simple async function that mimics analyze_helpers structure"""
    
    log.info("=== Simple Helper Deletion (DRY RUN) ===")
    
    # Check if results directory exists
    results_dir = '/config/helper_analysis'
    orphaned_file = os.path.join(results_dir, 'orphaned_helpers.txt')
    
    # Only proceed if both directory and file exist
    if os.path.exists(results_dir) and os.path.exists(orphaned_file):
        try:
            # Read the file
            content = await task.executor(lambda path: builtins.open(path, 'r', encoding='utf-8').read(), orphaned_file)
            lines = content.splitlines()
            
            helpers_to_delete = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    entity_id = line.split('#')[0].split()[0].strip()
                    if '.' in entity_id and len(entity_id.split('.')) == 2:
                        helpers_to_delete.append(entity_id)
            
            if helpers_to_delete:
                log.info(f"Found {len(helpers_to_delete)} helpers to review:")
                
                # Check which ones exist
                existing_helpers = []
                for helper in helpers_to_delete:
                    if state.get(helper):
                        existing_helpers.append(helper)
                        # Use state.getattr() like the working analyze_helpers.py
                        attrs = state.getattr(helper) or {}
                        friendly_name = attrs.get('friendly_name', '') if attrs else ''
                        log.info(f"  • {helper} ({friendly_name})")
                
                if existing_helpers:
                    # Send notification
                    notification_message = f"🗑️ Helper Deletion Preview\n\nFound {len(existing_helpers)} existing helpers to delete.\n\nCheck logs for details.\n\nTo create deletion service, use pyscript.delete_helpers_execute"
                    
                    await service.call('persistent_notification', 'create',
                                      message=notification_message,
                                      title="Helper Deletion Preview",
                                      notification_id="helper_deletion_simple")
                else:
                    log.info("No existing helpers found to delete")
            else:
                log.info("No helpers found in file")
                
        except Exception as e:
            log.error(f"Error processing helpers file: {e}")
    else:
        log.error("Results directory or orphaned helpers file not found")
        log.error("Run pyscript.analyze_helpers first")
    
    log.info("=== Simple Helper Deletion Complete ===")