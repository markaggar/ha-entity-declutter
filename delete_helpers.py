# Home Assistant PyScript to Delete Helpers - Event Loop Safe Version
# Place this in /config/pyscript/delete_helpers.py
# Call with: pyscript.delete_helpers
# This script reads the orphaned helpers file and safely deletes the listed helpers

import json
import os

# Import required modules for task.executor
import builtins

@service
def delete_helpers(**kwargs):
    """Service version - creates async task"""
    dry_run = kwargs.get('dry_run', True)
    orphaned_file = kwargs.get('orphaned_file', None)
    
    # Don't return anything from service functions - just start the task
    task.create(delete_helpers_async(dry_run, orphaned_file))

async def delete_helpers_async(dry_run=True, orphaned_file=None):
    """
    Delete helpers listed in the orphaned helpers file
    
    Args:
        dry_run (bool): If True, only log what would be deleted without actually deleting
        orphaned_file (str): Path to the orphaned helpers file. If None, uses the most recent file.
    """
    
    log.info("=== Starting Helper Deletion Process ===")
    
    # Find the orphaned helpers file
    results_dir = '/config/helper_analysis'
    
    if not os.path.exists(results_dir):
        log.error(f"Results directory not found: {results_dir}")
        log.error("Run pyscript.analyze_helpers first to generate the analysis files")
        return {'success': False, 'error': 'No analysis files found'}
    
    if orphaned_file is None:
        # Use the standard orphaned helpers file
        orphaned_file = os.path.join(results_dir, 'orphaned_helpers.txt')
        
        if not os.path.exists(orphaned_file):
            log.error("Orphaned helpers file not found: " + orphaned_file)
            log.error("Run pyscript.analyze_helpers first")
            return {'success': False, 'error': 'Orphaned helpers file not found'}
    
    log.info(f"Using orphaned helpers file: {orphaned_file}")
    
    # Read the file and parse helper entities
    helpers_to_delete = []
    
    try:
        # Use task.executor for file operations in PyScript
        content = await task.executor(lambda path: builtins.open(path, 'r', encoding='utf-8').read(), orphaned_file)
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Extract entity ID (everything before the first # or space)
            entity_id = line.split('#')[0].split()[0].strip()
            
            # Validate entity ID format
            if '.' in entity_id and len(entity_id.split('.')) == 2:
                domain, entity_name = entity_id.split('.', 1)
                if domain.isalpha() and all(c.isalnum() or c == '_' for c in entity_name):
                    helpers_to_delete.append(entity_id)
                else:
                    log.warning(f"Line {line_num}: Invalid entity ID format: {entity_id}")
            else:
                log.warning(f"Line {line_num}: Skipping invalid line: {line}")
    
    except Exception as e:
        log.error(f"Error reading orphaned helpers file: {e}")
        return {'success': False, 'error': str(e)}
    
    if not helpers_to_delete:
        log.info("No helpers to delete found in file")
        return {'success': True, 'deleted_count': 0, 'message': 'No helpers to delete'}
    
    log.info(f"Found {len(helpers_to_delete)} helpers to delete")
    
    # Verify helpers exist before deletion
    existing_helpers = []
    missing_helpers = []
    
    for helper in helpers_to_delete:
        if state.get(helper):
            existing_helpers.append(helper)
        else:
            missing_helpers.append(helper)
    
    if missing_helpers:
        log.warning(f"The following helpers no longer exist: {', '.join(missing_helpers)}")
    
    if not existing_helpers:
        log.info("No existing helpers to delete")
        return {'success': True, 'deleted_count': 0, 'message': 'All helpers already removed'}
    
    # Create backup before deletion
    backup_file = f"{results_dir}/deletion_backup.json"
    backup_data = {
        'dry_run': dry_run,
        'source_file': orphaned_file,
        'helpers_to_delete': existing_helpers,
        'helper_states': {}
    }
    
    # Backup current states
    for helper in existing_helpers:
        helper_state = state.get(helper)
        if helper_state:
            backup_data['helper_states'][helper] = {
                'state': helper_state.state,
                'attributes': dict(helper_state.attributes),
                'last_changed': helper_state.last_changed.isoformat() if helper_state.last_changed else None,
                'last_updated': helper_state.last_updated.isoformat() if helper_state.last_updated else None
            }
    
    # Use task.executor for file writing
    backup_content = json.dumps(backup_data, indent=2, ensure_ascii=False)
    await task.executor(lambda path, content: builtins.open(path, 'w', encoding='utf-8').write(content), backup_file, backup_content)
    
    log.info(f"Backup created: {backup_file}")
    
    if dry_run:
        log.info("=== DRY RUN MODE - NO ACTUAL DELETION ===")
        log.info("The following helpers WOULD be deleted:")
        for helper in existing_helpers:
            helper_state = state.get(helper)
            friendly_name = helper_state.attributes.get('friendly_name', '') if helper_state else ''
            log.info(f"  • {helper} ({friendly_name})")
        
        log.info("")
        log.info("To actually delete these helpers, call:")
        log.info("  pyscript.delete_helpers(dry_run=False)")
        
        return {
            'success': True,
            'dry_run': True,
            'would_delete_count': len(existing_helpers),
            'helpers_to_delete': existing_helpers,
            'backup_file': backup_file
        }
    
    # Actual deletion
    log.info("=== PERFORMING ACTUAL DELETION ===")
    deleted_helpers = []
    failed_deletions = []
    
    for helper in existing_helpers:
        try:
            # Use the appropriate service based on helper type
            domain = helper.split('.')[0]
            
            if domain == 'input_boolean':
                await service.call('input_boolean', 'delete', entity_id=helper)
            elif domain == 'input_text':
                await service.call('input_text', 'delete', entity_id=helper)
            elif domain == 'input_number':
                await service.call('input_number', 'delete', entity_id=helper)
            elif domain == 'input_select':
                await service.call('input_select', 'delete', entity_id=helper)
            elif domain == 'input_datetime':
                await service.call('input_datetime', 'delete', entity_id=helper)
            elif domain == 'counter':
                await service.call('counter', 'delete', entity_id=helper)
            elif domain == 'timer':
                await service.call('timer', 'delete', entity_id=helper)
            elif domain in ['sensor', 'binary_sensor']:
                # Template sensors require different approach
                log.warning(f"Cannot auto-delete template sensor {helper} - manual removal from configuration required")
                failed_deletions.append(f"{helper} - requires manual config removal")
                continue
            else:
                log.warning(f"Unknown helper type for {helper} - skipping")
                failed_deletions.append(f"{helper} - unknown type")
                continue
            
            deleted_helpers.append(helper)
            log.info(f"✓ Deleted: {helper}")
            
        except Exception as e:
            log.error(f"✗ Failed to delete {helper}: {e}")
            failed_deletions.append(f"{helper} - {str(e)}")
    
    # Create deletion report
    report_file = f"{results_dir}/deletion_report.txt"
    report_content = "HELPER DELETION REPORT\n"
    report_content += "=" * 30 + "\n\n"
    report_content += f"Source File: {orphaned_file}\n"
    report_content += f"Backup File: {backup_file}\n\n"
    
    report_content += f"SUMMARY:\n"
    report_content += f"  Requested Deletions: {len(existing_helpers)}\n"
    report_content += f"  Successful Deletions: {len(deleted_helpers)}\n"
    report_content += f"  Failed Deletions: {len(failed_deletions)}\n\n"
    
    if deleted_helpers:
        report_content += "SUCCESSFULLY DELETED:\n"
        for helper in deleted_helpers:
            report_content += f"  ✓ {helper}\n"
        report_content += "\n"
    
    if failed_deletions:
        report_content += "FAILED DELETIONS:\n"
        for failure in failed_deletions:
            report_content += f"  ✗ {failure}\n"
        report_content += "\n"
    
    # Use task.executor for file writing
    await task.executor(lambda path, content: builtins.open(path, 'w', encoding='utf-8').write(content), report_file, report_content)
    
    log.info("=== Deletion Complete ===")
    log.info(f"Successfully deleted: {len(deleted_helpers)} helpers")
    if failed_deletions:
        log.info(f"Failed deletions: {len(failed_deletions)}")
        log.info("Check deletion report for details")
    log.info(f"Deletion report: {report_file}")
    
    return {
        'success': True,
        'dry_run': False,
        'deleted_count': len(deleted_helpers),
        'failed_count': len(failed_deletions),
        'deleted_helpers': deleted_helpers,
        'failed_deletions': failed_deletions,
        'backup_file': backup_file,
        'report_file': report_file
    }

@service
def restore_helpers(**kwargs):
    """Service version - creates async task"""
    backup_file = kwargs.get('backup_file', None)
    
    # Don't return anything from service functions - just start the task
    task.create(restore_helpers_async(backup_file))

async def restore_helpers_async(backup_file=None):
    """
    Restore helpers from a backup file (emergency recovery)
    
    Args:
        backup_file (str): Path to backup file. If None, uses the most recent backup.
    """
    
    log.info("=== Helper Restore Process ===")
    
    results_dir = '/config/helper_analysis'
    
    if backup_file is None:
        # Find the most recent backup file
        backup_files = []
        for file in os.listdir(results_dir):
            if file.startswith('deletion_backup_') and file.endswith('.json'):
                backup_files.append(os.path.join(results_dir, file))
        
        if not backup_files:
            log.error("No backup files found")
            return {'success': False, 'error': 'No backup files found'}
        
        backup_file = max(backup_files, key=os.path.getmtime)
    
    log.info(f"Using backup file: {backup_file}")
    
    try:
        # Use task.executor for file reading
        content = await task.executor(lambda path: builtins.open(path, 'r', encoding='utf-8').read(), backup_file)
        backup_data = json.loads(content)
        
        helpers_to_restore = backup_data.get('helpers_to_delete', [])
        helper_states = backup_data.get('helper_states', {})
        
        log.info(f"Found {len(helpers_to_restore)} helpers to potentially restore")
        log.warning("IMPORTANT: This restore function can only recreate helper entities.")
        log.warning("It cannot restore the original configuration values.")
        log.warning("You will need to manually reconfigure each helper after restoration.")
        
        # Note: Full restoration would require recreating helpers via their respective services
        # This is complex and would need the original configuration parameters
        # For now, just log what was backed up
        
        for helper in helpers_to_restore:
            if helper in helper_states:
                state_info = helper_states[helper]
                log.info(f"Backup info for {helper}:")
                log.info(f"  State: {state_info['state']}")
                log.info(f"  Attributes: {state_info['attributes']}")
        
        return {
            'success': True,
            'message': 'Backup info logged. Manual reconfiguration required.',
            'helpers_in_backup': helpers_to_restore
        }
        
    except Exception as e:
        log.error(f"Error reading backup file: {e}")
        return {'success': False, 'error': str(e)}