# Complete Helper Deletion Script for PyScript - PyScript I/O Compatible
# 
# Updated to use proper PyScript I/O patterns with @pyscript_executor decorators
# instead of direct open() calls to avoid PyScript I/O limitations
#
# Usage:
#   pyscript.delete_helpers_preview - Dry run preview with notifications and files
#   pyscript.delete_helpers_execute - Actually delete helpers (after preview)

import json
import os
import datetime

# PyScript file I/O functions using @pyscript_executor decorator
# These are compiled to native Python and run in separate threads
@pyscript_executor
def read_text_file(file_path):
    """Read text file using proper PyScript I/O pattern"""
    try:
        import builtins
        with builtins.open(file_path, 'r', encoding='utf-8') as f:
            return f.read(), None
    except Exception as exc:
        return None, exc

@pyscript_executor
def write_text_file(file_path, content):
    """Write text file using proper PyScript I/O pattern"""
    try:
        import builtins
        with builtins.open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, None
    except Exception as exc:
        return False, exc

@service
def delete_helpers_preview(**kwargs):
    """Preview helpers that would be deleted (dry run with full features)"""
    task.create(delete_helpers_preview_async())

@service
def delete_helpers_execute(**kwargs):
    """Execute actual helper deletion (use after preview)"""
    task.create(delete_helpers_execute_async())

async def delete_helpers_preview_async():
    """Preview helpers that would be deleted with proper file I/O"""
    
    log.info("=== Helper Deletion Preview ===")
    
    # Find the results directory and truly orphaned helpers file (safe to delete)
    results_dir = '/config/helper_analysis'
    truly_orphaned_file = f"{results_dir}/truly_orphaned_helpers.txt"
    
    if not os.path.exists(results_dir):
        log.error("Results directory not found - run pyscript.analyze_helpers first")
        return
    
    # Check for the new truly orphaned file first
    if os.path.exists(truly_orphaned_file):
        orphaned_file = truly_orphaned_file
        log.info("Using truly_orphaned_helpers.txt (safest - no dashboard references)")
    else:
        # Fallback to old file for backward compatibility
        orphaned_file = f"{results_dir}/orphaned_helpers.txt"
        if not os.path.exists(orphaned_file):
            log.error("No orphaned helpers files found - run pyscript.analyze_helpers first")
            return
        log.warning("Using orphaned_helpers.txt (contains dashboard-only helpers - review carefully!)")
    
    try:
        # Read the orphaned helpers file using proper PyScript I/O
        content, error = read_text_file(orphaned_file)
        if error:
            log.error(f"Error reading orphaned helpers file: {error}")
            return
        
        # Parse helpers to delete
        helpers_to_delete = []
        if content:
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    helpers_to_delete.append(line)
        
        if not helpers_to_delete:
            log.info("No helpers to delete found in file")
            return
        
        log.info(f"Found {len(helpers_to_delete)} helpers in orphaned file")
        
        # Check which ones exist and collect details
        existing_helpers = []
        helper_details = []
        
        for helper in helpers_to_delete:
            helper_state = state.get(helper)
            if helper_state:
                existing_helpers.append(helper)
                # Get helper details
                attributes = state.getattr(helper) or {}
                detail = {
                    'entity_id': helper,
                    'current_value': str(helper_state),
                    'friendly_name': attributes.get('friendly_name', helper),
                    'last_changed': str(attributes.get('last_changed', 'Unknown')),
                    'attributes': dict(attributes)
                }
                helper_details.append(detail)
            else:
                log.info(f"Helper {helper} not found (already deleted?)")
        
        log.info(f"Found {len(existing_helpers)} existing helpers to delete")
        
        if existing_helpers:
            # Generate preview content
            preview_content = "# Helper Deletion Preview\n"
            preview_content += f"# Generated: {datetime.datetime.now()}\n"
            preview_content += f"# {len(existing_helpers)} helpers would be deleted\n\n"
            
            for detail in helper_details:
                preview_content += f"Entity: {detail['entity_id']}\n"
                preview_content += f"  Name: {detail['friendly_name']}\n"
                preview_content += f"  Current Value: {detail['current_value']}\n"
                preview_content += f"  Last Changed: {detail['last_changed']}\n"
                preview_content += "\n"
            
            # Write preview file using proper PyScript I/O
            preview_file = f"{results_dir}/deletion_preview.txt"
            success, error = write_text_file(preview_file, preview_content)
            if error:
                log.error(f"Error writing preview file: {error}")
            else:
                log.info(f"Preview saved to: {preview_file}")
            
            # Write backup file with helper details using proper PyScript I/O
            backup_file = f"{results_dir}/deletion_backup.json"
            backup_content = json.dumps(helper_details, indent=2, ensure_ascii=False)
            success, error = write_text_file(backup_file, backup_content)
            if error:
                log.error(f"Error writing backup file: {error}")
            else:
                log.info(f"Backup saved to: {backup_file}")
            
            # Send notification
            service.call('persistent_notification', 'create',
                title="Helper Deletion Preview Ready",
                message=f"Found {len(existing_helpers)} helpers to delete. Check {preview_file} for details.",
                notification_id="helper_deletion_preview")
            
            log.info("Preview complete - review files before executing deletion")
        else:
            log.info("No existing helpers found to delete")
            
    except Exception as e:
        log.error(f"Error in preview: {e}")

async def delete_helpers_execute_async():
    """Execute actual helper deletion"""
    
    log.info("=== Helper Deletion Execution ===")
    
    results_dir = '/config/helper_analysis'
    backup_file = f"{results_dir}/deletion_backup.json"
    
    if not os.path.exists(backup_file):
        log.error("Backup file not found - run preview first")
        return
    
    try:
        # Read backup file using proper PyScript I/O
        content, error = read_text_file(backup_file)
        if error:
            log.error(f"Error reading backup file: {error}")
            return
        
        helper_details = json.loads(content)
        
        log.info(f"Executing deletion of {len(helper_details)} helpers")
        
        deleted_count = 0
        failed_deletions = []
        
        for detail in helper_details:
            entity_id = detail['entity_id']
            try:
                # Delete the helper entity based on type
                if entity_id.startswith(('input_', 'counter.', 'timer.')):
                    # Traditional helpers - use domain.remove service
                    domain = entity_id.split('.')[0]
                    service.call(domain, 'remove', entity_id=entity_id)
                    log.info(f"✓ Deleted {entity_id}")
                    deleted_count += 1
                elif entity_id.startswith(('sensor.', 'binary_sensor.')):
                    # Template/statistics helpers - these are often defined in YAML
                    # They can't be deleted via service calls, need manual removal
                    log.warning(f"⚠ Template/sensor helper {entity_id} - remove from YAML configuration manually")
                    failed_deletions.append(entity_id)
                else:
                    # Unknown helper type
                    log.warning(f"⚠ Unknown helper type {entity_id} - manual removal required")
                    failed_deletions.append(entity_id)
                    
            except Exception as e:
                log.error(f"✗ Failed to delete {entity_id}: {e}")
                failed_deletions.append(entity_id)
        
        # Generate execution report
        report_content = f"# Helper Deletion Report\n"
        report_content += f"# Generated: {datetime.datetime.now()}\n"
        report_content += f"# Successfully deleted: {deleted_count}\n"
        report_content += f"# Failed deletions: {len(failed_deletions)}\n\n"
        
        if deleted_count > 0:
            report_content += "## Successfully Deleted:\n"
            for detail in helper_details:
                if detail['entity_id'] not in failed_deletions:
                    report_content += f"- {detail['entity_id']} ({detail['friendly_name']})\n"
            report_content += "\n"
        
        if failed_deletions:
            report_content += "## Failed Deletions (Manual Action Required):\n"
            for entity_id in failed_deletions:
                report_content += f"- {entity_id}\n"
            report_content += "\n"
        
        # Write report using proper PyScript I/O
        report_file = f"{results_dir}/deletion_report.txt"
        success, error = write_text_file(report_file, report_content)
        if error:
            log.error(f"Error writing report file: {error}")
        else:
            log.info(f"Execution report saved to: {report_file}")
        
        # Send notification
        service.call('persistent_notification', 'create',
            title="Helper Deletion Complete",
            message=f"Deleted {deleted_count} helpers. {len(failed_deletions)} failed. Check {report_file}",
            notification_id="helper_deletion_complete")
        
        log.info(f"Deletion complete: {deleted_count} deleted, {len(failed_deletions)} failed")
        
    except Exception as e:
        log.error(f"Error in execution: {e}")