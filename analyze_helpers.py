# Home Assistant PyScript to Find Helper References - PyScript I/O Compatible
# Place this in /config/pyscript/analyze_helpers.py
# Call with: pyscript.analyze_helpers
#
# Updated to use proper PyScript I/O patterns with @pyscript_executor decorators
# instead of task.executor with helper functions to avoid PyScript I/O limitations

import json
import re
import yaml
import os

# PyScript file I/O functions using @pyscript_executor decorator
# These are compiled to native Python and run in separate threads
@pyscript_executor
def read_text_file(file_path):
    """Read text file using proper PyScript I/O pattern"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(), None
    except Exception as exc:
        return None, exc

@pyscript_executor
def write_text_file(file_path, content):
    """Write text file using proper PyScript I/O pattern"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, None
    except Exception as exc:
        return False, exc

@pyscript_executor
def examine_entity_registry():
    """Examine the entity registry to understand helper patterns using proper PyScript I/O"""
    try:
        import json
        entity_registry_file = '/config/.storage/core.entity_registry'
        
        with open(entity_registry_file, 'r', encoding='utf-8') as f:
            entity_registry = json.load(f)
            
        entities = entity_registry.get('data', {}).get('entities', [])
        print(f"Entity registry contains {len(entities)} entities")
        
        # Look for template-related entries
        template_sensors = []
        helper_entities = []
        
        for entity in entities:
            entity_id = entity.get('entity_id', '')
            platform = entity.get('platform', '')
            config_entry_id = entity.get('config_entry_id')
            
            
            # Traditional helpers - but only if they don't have a config_entry_id (integration-based)
            if entity_id.startswith(('input_', 'counter.', 'timer.')):
                if config_entry_id:
                    print(f"Skipping integration-based entity: {entity_id} (config_entry_id: {config_entry_id})")
                    continue
                
                # Debug specific entities
                if 'ca_' in entity_id:
                    print(f"DEBUG: Adding CA entity {entity_id} (config_entry_id: {config_entry_id}, platform: {platform})")
                    
                helper_entities.append(entity_id)
            
            # FIRST: Skip integration entities with config_entry_id (except template/statistics platforms which are helpers)
            elif config_entry_id and (entity_id.startswith(('sensor.', 'binary_sensor.')) and platform not in ['template', 'statistics']):
                print(f"Skipping integration entity: {entity_id} (config_entry_id: {config_entry_id}, platform: {platform})")
                continue
            
            # Template entities (these are the missing helpers!)
            elif platform == 'template':
                template_sensors.append(entity_id)
                print(f"Template helper found: {entity_id} (platform: {platform})")
            
            # Statistics entities (also helpers!)
            elif platform == 'statistics':
                template_sensors.append(entity_id)
                print(f"Statistics helper found: {entity_id} (platform: {platform})")
            
            # Other helper platforms
            elif platform in ['integral', 'derivative', 'history_stats', 'trend', 'threshold', 'utility_meter', 'group', 'combine', 'times_of_the_day', 'mold_indicator']:
                template_sensors.append(entity_id)
                print(f"Helper found: {entity_id} (platform: {platform})")
            
            # Entities without config entries (could be from configuration.yaml templates)
            elif not config_entry_id and (entity_id.startswith('sensor.') or entity_id.startswith('binary_sensor.')):
                template_sensors.append(entity_id)
                print(f"Potential template helper found: {entity_id} (no config entry)")
        
        print(f"Found {len(template_sensors)} template helpers in registry")
        print(f"Found {len(helper_entities)} traditional helpers in registry")
        
        return template_sensors + helper_entities, None
        
    except Exception as exc:
        print(f"Error examining entity registry: {exc}")
        return None, exc

@pyscript_executor
def read_config_file(file_path):
    """Read a config file using proper PyScript I/O"""
    import builtins
    with builtins.open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def analyze_integration_config_entries():
    """Analyze integration config entries to find helper references using proper PyScript I/O"""
    import json
    
    try:
        config_entries_file = '/config/.storage/core.config_entries'
        print(f"DEBUG: Attempting to read {config_entries_file}")
        
        with open(config_entries_file, 'r', encoding='utf-8') as f:
            config_entries = json.load(f)
        entries = config_entries.get('data', {}).get('entries', [])
        print(f"Found {len(entries)} integration config entries")
        print(f"DEBUG: Integration config analysis starting with {len(entries)} entries")
        
        helper_references = set()
        
        def find_entities_in_value(value, path="", key_name=""):
            """Recursively search for entity references in any value"""
            if isinstance(value, str):
                # Look for entity IDs in strings - improved patterns to catch ca_ entities
                import re
                entity_patterns = [
                    r'\b(input_[a-z_]+\.[a-z0-9_]+)\b',
                    r'\b(counter\.[a-z0-9_]+)\b', 
                    r'\b(timer\.[a-z0-9_]+)\b',
                    r'\b(sensor\.ca_[a-z0-9_]+)\b',  # Specifically for CA sensors
                    r'\b(binary_sensor\.ca_[a-z0-9_]+)\b',  # Specifically for CA binary sensors
                    r'\b(sensor\.[a-z0-9_]+)\b',
                    r'\b(binary_sensor\.[a-z0-9_]+)\b'
                ]
                
                for pattern in entity_patterns:
                    matches = re.findall(pattern, value, re.IGNORECASE)
                    for match in matches:
                        helper_references.add(match)
                        print(f"Found helper reference in integration config: {match} (key: {key_name}, path: {path})")
            
            elif isinstance(value, dict):
                for key, nested_value in value.items():
                    find_entities_in_value(nested_value, f"{path}.{key}" if path else key, key)
            
            elif isinstance(value, list):
                for i, nested_value in enumerate(value):
                    find_entities_in_value(nested_value, f"{path}[{i}]" if path else f"[{i}]", f"[{i}]")
        
        for entry in entries:
            entry_id = entry.get('entry_id', 'unknown')
            domain = entry.get('domain', 'unknown')
            title = entry.get('title', 'unknown')
            
            print(f"Analyzing integration: {domain} - {title} (ID: {entry_id})")
            
            # Debug CA entities specifically
            if 'ca_' in str(entry).lower():
                print(f"DEBUG: Found CA reference in integration {domain} - {title}")
                print(f"DEBUG: Entry data snippet: {str(entry)[:200]}...")
            
            # Check all data in the config entry
            find_entities_in_value(entry, f"integration.{domain}")
        
        print(f"Found {len(helper_references)} helper references in integration configs")
        
        return list(helper_references), None
        
    except Exception as exc:
        print(f"Error analyzing integration config entries: {exc}")
        return None, exc

@pyscript_executor  
def analyze_template_dependencies():
    """Analyze template helpers to find their dependencies on other helpers using proper PyScript I/O"""
    import json
    import re
    import os
    
    template_dependencies = {}
    
    def extract_template_dependencies(template_text):
        """Extract entity references from template code"""
        if not template_text:
            return set()
        
        dependencies = set()
        
        # Patterns to find entity references in templates
        patterns = [
            r"states\(['\"]([a-z0-9_]+\.[a-z0-9_]+)['\"]\)",  # states('entity.id')
            r"states\('([^']+)'\)",  # states('entity.id') - more permissive
            r'states\("([^"]+)"\)',  # states("entity.id")
            r"is_state\(['\"]([a-z0-9_]+\.[a-z0-9_]+)['\"]",  # is_state('entity.id')
            r"state_attr\(['\"]([a-z0-9_]+\.[a-z0-9_]+)['\"]",  # state_attr('entity.id')
            r"\b(input_[a-z_]+\.[a-z0-9_]+)\b",  # Direct entity references
            r"\b(binary_sensor\.[a-z0-9_]+)\b",
            r"\b(sensor\.[a-z0-9_]+)\b",
            r"\b(timer\.[a-z0-9_]+)\b",
            r"\b(counter\.[a-z0-9_]+)\b",
            r"\b(schedule\.[a-z0-9_]+)\b"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, template_text, re.IGNORECASE)
            for match in matches:
                entity_id = match if isinstance(match, str) else match[0]
                
                # Only include entities that could be helpers
                helper_domains = ['binary_sensor', 'sensor', 'input_boolean', 'input_datetime', 'input_number', 'input_select', 'input_text', 'timer', 'counter', 'schedule']
                is_helper = False
                for domain in helper_domains:
                    if entity_id.startswith(domain + '.'):
                        is_helper = True
                        break
                if is_helper:
                    dependencies.add(entity_id)
        
        return dependencies
    
    try:
        # Get template helpers from config entries (UI-created)
        config_entries_file = '/config/.storage/core.config_entries'
        with open(config_entries_file, 'r', encoding='utf-8') as f:
            config_entries = json.load(f)
        
        entries = config_entries.get('data', {}).get('entries', [])
        for entry in entries:
            if entry.get('domain') == 'template':
                title = entry.get('title', '')
                options = entry.get('options', {})
                template_state = options.get('state', '')
                
                if template_state:
                    dependencies = extract_template_dependencies(template_state)
                    if dependencies:
                        template_dependencies[f"UI Template: {title}"] = dependencies
    
    except Exception as e:
        print(f"Error analyzing UI template dependencies: {e}")
    
    # Dynamically scan ALL configuration files for template dependencies
    # This replaces the stupid hardcoded list with proper discovery
    config_files = get_config_files()
    
    for config_file in config_files:
        try:
            # Use proper PyScript I/O pattern
            content, error = read_text_file(config_file)
            if error:
                continue
            
            # Analyze entire file content for entity references
            file_name = config_file.split('/')[-1]
            dependencies = extract_template_dependencies(content)
            if dependencies:
                template_dependencies[f"File: {file_name}"] = dependencies
                    
        except Exception as e:
            print(f"Error reading {config_file}: {e}")
            continue
    
    return template_dependencies, None

@service
def analyze_helpers(**kwargs):
    """Service wrapper - creates async task"""
    task.create(analyze_helpers_async())

def is_helper_entity(entity_id):
    """Determine if an entity is a helper - expanded to match HA UI definition"""
    # Traditional input helpers
    if (entity_id.startswith('input_') or 
        entity_id.startswith('counter.') or 
        entity_id.startswith('timer.') or
        entity_id.startswith('variable.')):
        return True
    
    # Template helpers and other helper entities created via UI
    # These include template sensors, switches, lights, etc. created through helpers UI
    if (entity_id.startswith('sensor.') or 
        entity_id.startswith('binary_sensor.') or
        entity_id.startswith('switch.') or
        entity_id.startswith('light.') or
        entity_id.startswith('cover.') or
        entity_id.startswith('fan.') or
        entity_id.startswith('climate.') or
        entity_id.startswith('lock.') or
        entity_id.startswith('number.') or
        entity_id.startswith('select.') or
        entity_id.startswith('text.') or
        entity_id.startswith('button.') or
        entity_id.startswith('time.') or
        entity_id.startswith('date.') or
        entity_id.startswith('datetime.')):
        
        # Check if this is actually a helper by examining its attributes
        return is_template_or_helper_entity(entity_id)
    
    return False

def is_template_or_helper_entity(entity_id):
    """Check if a sensor/binary_sensor/etc is actually a template helper"""
    # Template sensors/binary_sensors (user-created helpers)
    if entity_id.startswith('sensor.') or entity_id.startswith('binary_sensor.'):
        try:
            # Access entity attributes through PyScript state API
            try:
                attrs = state.getattr(entity_id) or {}
            except:
                attrs = {}
                
                # Now that we can access attributes properly, let's use them for template helper detection
                
                # Template helpers are typically characterized by:
                # 1. Having very few attributes (usually just basic ones like friendly_name, device_class, icon)
                # 2. NOT having complex integration-specific attributes
                # 3. May or may not have unique_id (inconsistent)
                # 4. Should NOT have attributes that clearly indicate integration origin
                
                if attrs:
                    # These attributes strongly suggest an integration entity, not a template helper
                    integration_indicators = [
                        'integration_method', 'flow_sensor_value', 'detectors_flow', 'sampling_active_seconds',
                        'current_session_start', 'last_session_end', 'session_stage', 'volume_unit',
                        'entity_registry_enabled_default', 'entity_registry_visible_default', 'platform',
                        'supported_features', 'assumed_state', 'should_poll', 'state_class', 'last_reset',
                        'attribution', 'source_type', 'restored'  # These often indicate integration/system entities
                    ]
                    
                    # Check if this has integration-specific attributes
                    has_integration_attrs = any(indicator in attrs for indicator in integration_indicators)
                    
                    if has_integration_attrs:
                        # This is clearly from an integration, not a template helper
                        return False
                    
                    # Template helpers typically have minimal attributes and may not have unique_id
                    basic_attrs = {'friendly_name', 'device_class', 'icon', 'unique_id'}
                    attr_keys = set(attrs.keys())
                    
                    # Template helper detection based on actual patterns seen:
                    # Template helpers typically have exactly these attributes:
                    # - friendly_name, device_class, icon (3 attributes)
                    # - Sometimes friendly_name, device_class, icon, unique_id (4 attributes)
                    
                    template_helper_patterns = [
                        # Pattern 1: friendly_name + device_class + icon (no unique_id)
                        {'friendly_name', 'device_class', 'icon'},
                        # Pattern 2: friendly_name + device_class + icon + unique_id
                        {'friendly_name', 'device_class', 'icon', 'unique_id'},
                        # Pattern 3: Just friendly_name + device_class (minimal)
                        {'friendly_name', 'device_class'}
                    ]
                    
                    # Check if the entity matches any template helper pattern
                    for pattern in template_helper_patterns:
                        if (attr_keys == pattern and not has_integration_attrs):
                            return True
                
                # Method 4: Check for integration-specific attributes that indicate it's NOT a template helper
                if attrs:
                    # Integration entities have specific complex attributes that template helpers don't have
                    # These are very specific to integrations, not template helpers
                    definitive_integration_indicators = [
                        'integration_method', 'flow_sensor_value', 'detectors_flow', 'sampling_active_seconds',
                        'current_session_start', 'last_session_end', 'session_stage', 'volume_unit',
                        'supported_features', 'assumed_state', 'should_poll', 'state_class', 'last_reset',
                        'attribution', 'unit_of_measurement', 'options', 'device_id'
                    ]
                    
                    has_integration_attrs = any(indicator in attrs for indicator in definitive_integration_indicators)
                    
                    if has_integration_attrs:
                        # This is clearly from an integration, not a template helper
                        return False
                
                # Method 5: For remaining entities, be more conservative
                # Only identify as template helper if it has the minimal template helper signature:
                # - Basic UI helper attributes (device_class, icon, friendly_name)  
                # - No complex integration attributes
                # - No unique_id (many template helpers don't have them)
                # - Reasonable entity naming (not from obvious integrations)
                
                attr_keys = set(attrs.keys()) if attrs else set()
                
                # Template helpers often have these basic attributes
                basic_template_indicators = {'friendly_name', 'device_class', 'icon'}
                
                # Exclude if it has these attributes (suggests integration origin)
                complex_indicators = {
                    'unique_id', 'supported_features', 'restored', 'state_class', 
                    'unit_of_measurement', 'last_changed', 'last_updated'
                }
                
                has_basic_attrs = bool(attr_keys & basic_template_indicators)
                has_complex_attrs = bool(attr_keys & complex_indicators)
                
                # Very conservative: only flag as template helper if it looks exactly like one
                if (has_basic_attrs and not has_complex_attrs and 
                    len(attr_keys) <= 4 and  # Very few attributes
                    not attrs.get('unique_id')):  # No unique_id
                    
                    # Final check: make sure it's not from obvious integrations
                    obvious_integration_patterns = [
                        'motion', 'person', 'vehicle', 'pet', 'microphone',  # Camera integrations
                        'water_monitor', 'watt_monitor', 'backup', 'mobile_app', 
                        'fully_kiosk', 'reolink', 'sonos', 'ca_', 'sm_g998u1', 
                        'fire_tablet', 'sun_', 'day_night_state'
                    ]
                    
                    is_from_obvious_integration = False
                    for pattern in obvious_integration_patterns:
                        if pattern in entity_id.lower():
                            is_from_obvious_integration = True
                            break
                    
                    if not is_from_obvious_integration:
                        log.info(f"Detected template helper by conservative analysis: {entity_id}")
                        return True
                
                # Method 4: Check if it's explicitly marked as template integration
                integration = attrs.get('integration', '') if attrs else ''
                platform = attrs.get('platform', '') if attrs else ''
                if integration == 'template' or 'template' in str(platform):
                    log.info(f"Detected template helper by integration: {entity_id}")
                    return True
                
                # Method 5: Template helpers created via UI often have minimal attributes
                attr_keys = set(attrs.keys()) if attrs else set()
                
                # Exclude entities that have complex device/integration attributes
                complex_indicators = {
                    'unique_id', 'device_id', 'area_id', 'entity_registry_enabled_default',
                    'entity_registry_visible_default', 'supported_features', 'restored',
                    'state_class', 'unit_of_measurement'
                }
                
                # Template helpers often have these basic attributes
                basic_template_indicators = {
                    'friendly_name', 'device_class', 'icon'
                }
                
                # Check if this looks like a simple template helper
                has_complex_attrs = bool(attr_keys & complex_indicators)
                has_basic_attrs = bool(attr_keys & basic_template_indicators)
                
                # If it has basic attributes but minimal complex attributes, likely a template helper
                if (has_basic_attrs and not attrs.get('unique_id') and 
                    len(attr_keys - basic_template_indicators - {'friendly_name'}) <= 2):
                    log.info(f"Detected template helper by attributes: {entity_id}")
                    return True
                    
        except Exception as e:
            log.warning(f"Error checking entity {entity_id}: {e}")
    
    # For other entity types (switch, light, cover, etc.), check if they're template helpers
    try:
        attrs = state.getattr(entity_id) or {}
        if not attrs:
            return False
            
        # Template helpers typically have minimal attributes and no integration markers
        integration_indicators = [
            'integration_method', 'flow_sensor_value', 'detectors_flow', 'sampling_active_seconds',
            'current_session_start', 'last_session_end', 'session_stage', 'volume_unit',
            'entity_registry_enabled_default', 'entity_registry_visible_default', 'platform',
            'supported_features', 'assumed_state', 'should_poll', 'state_class', 'last_reset',
            'attribution', 'source_type', 'restored'
        ]
        
        has_integration_attrs = any(indicator in attrs for indicator in integration_indicators)
        
        if has_integration_attrs:
            return False
            
        # Template helpers often have minimal attributes
        attr_keys = set(attrs.keys())
        basic_helper_attrs = {'friendly_name', 'device_class', 'icon', 'unique_id', 'entity_category'}
        
        # If it has only basic attributes and no integration markers, likely a template helper
        if len(attr_keys) <= 5 and attr_keys.issubset(basic_helper_attrs):
            return True
            
    except:
        pass
    
    return False

# The examine_entity_registry function is now implemented with @pyscript_executor above

def extract_template_dependencies(template_text):
    """Extract entity references from template code"""
    if not template_text:
        return set()
    
    dependencies = set()
    
    # Patterns to find entity references in templates
    patterns = [
        r"states\(['\"]([a-z0-9_]+\.[a-z0-9_]+)['\"]\)",  # states('entity.id')
        r"states\('([^']+)'\)",  # states('entity.id') - more permissive
        r'states\("([^"]+)"\)',  # states("entity.id")
        r"is_state\(['\"]([a-z0-9_]+\.[a-z0-9_]+)['\"]",  # is_state('entity.id')
        r"state_attr\(['\"]([a-z0-9_]+\.[a-z0-9_]+)['\"]",  # state_attr('entity.id')
        r"\b(input_[a-z_]+\.[a-z0-9_]+)\b",  # Direct entity references
        r"\b(binary_sensor\.[a-z0-9_]+)\b",
        r"\b(sensor\.[a-z0-9_]+)\b",
        r"\b(timer\.[a-z0-9_]+)\b",
        r"\b(counter\.[a-z0-9_]+)\b",
        r"\b(schedule\.[a-z0-9_]+)\b"
    ]
    
    # Debug logging: log first 200 chars of template text being analyzed
    preview = template_text[:200].replace('\n', ' ').replace('\r', '')
    log.info(f"Analyzing template text: {preview}...")
    
    total_matches = 0
    for pattern in patterns:
        matches = re.findall(pattern, template_text, re.IGNORECASE)
        if matches:
            log.info(f"Pattern '{pattern}' found {len(matches)} matches: {matches[:5]}")  # Show first 5 matches
            total_matches += len(matches)
        for match in matches:
            entity_id = match if isinstance(match, str) else match[0]
            
            # Only include entities that could be helpers
            helper_domains = ['binary_sensor', 'sensor', 'input_boolean', 'input_datetime', 'input_number', 'input_select', 'input_text', 'timer', 'counter', 'schedule']
            is_helper = False
            for domain in helper_domains:
                if entity_id.startswith(domain + '.'):
                    is_helper = True
                    break
            if is_helper:
                dependencies.add(entity_id)
    
    if total_matches == 0:
        log.info("No entity references found in template text")
    else:
        log.info(f"Found {len(dependencies)} helper dependencies: {list(dependencies)[:10]}")
    
    return dependencies

def discover_template_files():
    """Automatically discover files containing template sensor definitions"""
    template_files = []
    
    # Get list of template entities from entity registry to guide our search
    try:
        registry_file = '/config/.storage/core.entity_registry'
        content = read_text_file(registry_file)
        registry = json.loads(content)
        
        template_entity_names = set()
        entities = registry.get('data', {}).get('entities', [])
        for entity in entities:
            if entity.get('platform') == 'template':
                # Extract the friendly name or original name to search for
                name = entity.get('name') or entity.get('original_name', '')
                unique_id = entity.get('unique_id', '')
                entity_id = entity.get('entity_id', '')
                
                if name:
                    template_entity_names.add(name)
                if unique_id:
                    template_entity_names.add(unique_id)
                if entity_id:
                    # Add just the entity name part
                    entity_name = entity_id.split('.', 1)[-1] if '.' in entity_id else entity_id
                    template_entity_names.add(entity_name)
        
        log.info(f"Searching for {len(template_entity_names)} template entities in configuration files")
        
    except Exception as e:
        log.info(f"Error reading entity registry for template discovery: {e}")
        template_entity_names = set()
    
    # Search common locations for YAML files - use simple directory listing instead of os.walk
    search_paths = [
        '/config',
        '/config/packages'
    ]
    
    import os
    for search_path in search_paths:
        try:
            if not os.path.exists(search_path):
                continue
                
            # Get all files in directory (not recursive to avoid PyScript issues)
            items = os.listdir(search_path)
            for item in items:
                if item.endswith(('.yaml', '.yml')):
                    file_path = os.path.join(search_path, item)
                    
                    # Skip certain files that are unlikely to contain templates
                    skip_files = ['secrets.yaml', 'known_devices.yaml']
                    should_skip = False
                    for skip_file in skip_files:
                        if skip_file in file_path:
                            should_skip = True
                            break
                    if should_skip:
                        continue
                    
                    try:
                        content = read_text_file(file_path)
                        
                        # Check if file contains template definitions
                        content_lower = content.lower()
                        has_template_section = False
                        template_patterns = ['template:', 'platform: template', '- platform: template']
                        for pattern in template_patterns:
                            if pattern in content_lower:
                                has_template_section = True
                                break
                        
                        # Check if file contains any of our known template entity names
                        has_template_entities = False
                        for name in template_entity_names:
                            if name and name.lower() in content_lower:
                                has_template_entities = True
                                break
                        
                        if has_template_section or has_template_entities:
                            template_files.append(file_path)
                            log.info(f"Found template definitions in: {file_path}")
                            
                    except Exception as e:
                        # Skip files that can't be read
                        continue
                        
        except Exception as e:
            log.info(f"Error searching {search_path}: {e}")
            continue
    
    return template_files

# The analyze_template_dependencies function is now implemented with @pyscript_executor above

async def analyze_dashboard_dependencies():
    """Analyze Lovelace dashboards to find entity references"""
    dashboard_dependencies = set()
    dashboard_file_mapping = {}  # Track which file each entity was found in
    
    # Focus on actual dashboard storage locations where UI dashboards are stored
    dashboard_files = []
    
    # Primary focus: .storage/lovelace* files (where UI-controlled dashboards live)
    try:
        storage_dir = '/config/.storage'
        if os.path.isdir(storage_dir):
            storage_files = os.listdir(storage_dir)
            for filename in storage_files:
                if filename.startswith('lovelace'):
                    full_path = os.path.join(storage_dir, filename)
                    if os.path.isfile(full_path):
                        dashboard_files.append(full_path)
                        log.info(f"Found dashboard storage file: {filename}")
    except Exception as e:
        log.info(f"Could not scan .storage directory: {e}")
    
    # Also check traditional YAML dashboard files
    yaml_dashboard_files = [
        '/config/ui-lovelace.yaml',
        '/config/lovelace.yaml',
        '/config/dashboards/main.yaml',
        '/config/dashboards/lovelace.yaml'
    ]
    
    for yaml_file in yaml_dashboard_files:
        if os.path.isfile(yaml_file):
            dashboard_files.append(yaml_file)
            log.info(f"Found YAML dashboard file: {yaml_file}")
    
    # Check dashboard directories for additional files
    dashboard_dirs = ['/config/dashboards/', '/config/lovelace/']
    for dash_dir in dashboard_dirs:
        try:
            if os.path.isdir(dash_dir):
                filenames = os.listdir(dash_dir)
                for filename in filenames:
                    if filename.endswith(('.yaml', '.yml')):
                        full_path = os.path.join(dash_dir, filename)
                        if full_path not in dashboard_files:
                            dashboard_files.append(full_path)
        except Exception as e:
            log.info(f"Could not list directory {dash_dir}: {e}")
    
    log.info(f"Checking {len(dashboard_files)} potential dashboard files")
    
    for dash_file in dashboard_files:
        try:
            if not os.path.isfile(dash_file):
                continue
                
            log.info(f"Analyzing dashboard file: {dash_file}")
            # Use proper PyScript I/O pattern
            content, error = read_text_file(dash_file)
            if error:
                log.info(f"Error reading {dash_file}: {error}")
                continue
            
            # Extract entities from dashboard content
            entities = extract_dashboard_entities(content)
            if entities:
                dashboard_dependencies.update(entities)
                
                # Track which file each entity was found in
                dashboard_filename = dash_file.split('/')[-1]  # Get just the filename
                for entity in entities:
                    if entity not in dashboard_file_mapping:
                        dashboard_file_mapping[entity] = []
                    dashboard_file_mapping[entity].append(dashboard_filename)
                
                log.info(f"Dashboard {dashboard_filename} references {len(entities)} helper entities")
                
        except Exception as e:
            log.info(f"Error reading dashboard file {dash_file}: {e}")
            continue
    
    log.info(f"Found {len(dashboard_dependencies)} total entities referenced by dashboards")
    return dashboard_dependencies, dashboard_file_mapping

def extract_dashboard_entities(dashboard_content):
    """Extract entity references from dashboard YAML content"""
    if not dashboard_content:
        return set()
    
    entities = set()
    
    # Comprehensive patterns for dashboard entity references (including complex names)
    patterns = [
        r"entity:\s*['\"]?([a-z0-9_]+\.[a-z0-9_]+)['\"]?",  # entity: sensor.example or entity: "sensor.example"
        r"entities:\s*\n(?:\s*-\s*['\"]?([a-z0-9_]+\.[a-z0-9_]+)['\"]?)+",  # entities list
        r"-\s*entity:\s*['\"]?([a-z0-9_]+\.[a-z0-9_]+)['\"]?",  # - entity: sensor.example  
        r"-\s*['\"]?([a-z0-9_]+\.[a-z0-9_]+)['\"]?",  # - sensor.example (direct entity)
        r"'([a-z0-9_]+\.[a-z0-9_]+)'",  # 'sensor.example'
        r'"([a-z0-9_]+\.[a-z0-9_]+)"',  # "sensor.example"
        r"sensor:\s*['\"]?([a-z0-9_]+\.[a-z0-9_]+)['\"]?",  # sensor: sensor.example
        r"binary_sensor:\s*['\"]?([a-z0-9_]+\.[a-z0-9_]+)['\"]?",  # binary_sensor: binary_sensor.example
        r"input_[a-z_]+:\s*['\"]?([a-z0-9_]+\.[a-z0-9_]+)['\"]?",  # input_boolean: input_boolean.example
        r"card_config.*?entity.*?['\"]([a-z0-9_]+\.[a-z0-9_]+)['\"]",  # card config entity references
        r"tap_action.*?entity.*?['\"]([a-z0-9_]+\.[a-z0-9_]+)['\"]",  # tap action entity references
        r"hold_action.*?entity.*?['\"]([a-z0-9_]+\.[a-z0-9_]+)['\"]",  # hold action entity references
        r"action.*?service_data.*?entity_id.*?['\"]([a-z0-9_]+\.[a-z0-9_]+)['\"]",  # service action entity_id
        # More flexible pattern for any entity ID in quotes (catches complex names like lock_code_slot_x_name)
        r"['\"]([a-z_]+\.[a-z0-9_]+)['\"]"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, dashboard_content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            entity_id = match if isinstance(match, str) else match[0]
            
            # Only include entities that could be helpers
            helper_domains = ['binary_sensor', 'sensor', 'input_boolean', 'input_datetime', 'input_number', 'input_select', 'input_text', 'timer', 'counter', 'schedule']
            is_helper = False
            for domain in helper_domains:
                if entity_id.startswith(domain + '.'):
                    is_helper = True
                    break
            if is_helper:
                entities.add(entity_id)
    
    return entities

def extract_entities_from_template_string(template_str):
    """Extract entity IDs from template strings AND regular YAML strings"""
    if not isinstance(template_str, str):
        return set()
    
    entities = set()
    
    # Regex patterns for entity detection
    patterns = [
        # Template functions with entity ID as first parameter  
        r'(?:states|is_state|state_attr|is_state_attr|has_value|state_translated|device_id|device_name|area_id|area_name)\s*\(\s*[\'"]([a-z_]+\.[a-z0-9_]+)[\'"]',
        # Direct entity state access (states.domain.entity)
        r'states\.([a-z_]+)\.([a-z0-9_]+)(?:\.state|\.attributes)',
        # Entity ID references in quotes
        r'[\'"]([a-z_]+\.[a-z0-9_]+)[\'"]',
        # CRITICAL FIX: Direct entity IDs without quotes (like entity_id: input_boolean.sim_auto_busy_calm)
        r'\b([a-z_]+\.[a-z0-9_]+)\b'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, template_str, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) == 2:
                # Pattern with domain and entity parts
                entity_id = f"{match.group(1)}.{match.group(2)}"
                entities.add(entity_id)
            else:
                # Single entity ID
                entity_id = match.group(1)
                # Basic validation
                if '.' in entity_id and len(entity_id.split('.')) == 2:
                    entities.add(entity_id)
    
    return entities

def analyze_yaml_content(content, file_path):
    """Analyze YAML content for entity references - both templates AND direct entity_id references"""
    entities = set()
    
    try:
        yaml_data = yaml.safe_load(content)
        if yaml_data:
            # Check templates in the serialized YAML
            yaml_str = yaml.dump(yaml_data)
            entities.update(extract_entities_from_template_string(yaml_str))
            
            # Enhanced traversal to find direct entity_id references
            def traverse_dict(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, str):
                            # Check for template references
                            entities.update(extract_entities_from_template_string(value))
                            
                            # CRITICAL: Check for entity references in ALL string values
                            # This catches entity_id: input_boolean.sim_auto_busy_calm patterns
                            if isinstance(value, str) and '.' in value:
                                # Check if it looks like an entity ID (domain.entity_name)
                                parts = value.split('.')
                                if len(parts) == 2:
                                    domain, entity_name = parts
                                    # Basic validation - domain should be letters, entity_name alphanumeric with underscores
                                    if (domain.replace('_', '').isalpha() and 
                                        entity_name.replace('_', '').replace('-', '').isalnum() and
                                        len(domain) > 0 and len(entity_name) > 0):
                                        entities.add(value)
                                    
                        elif isinstance(value, list):
                            # Handle lists - check all items for entity IDs
                            for item in value:
                                if isinstance(item, str) and '.' in item:
                                    parts = item.split('.')
                                    if len(parts) == 2:
                                        domain, entity_name = parts
                                        if (domain.replace('_', '').isalpha() and 
                                            entity_name.replace('_', '').replace('-', '').isalnum() and
                                            len(domain) > 0 and len(entity_name) > 0):
                                            entities.add(item)
                                elif isinstance(item, (dict, list)):
                                    traverse_dict(item)
                            # Also traverse the list structure
                            traverse_dict(value)
                        elif isinstance(value, (dict, list)):
                            traverse_dict(value)
                            
                elif isinstance(obj, list):
                    for item in obj:
                        if isinstance(item, str):
                            entities.update(extract_entities_from_template_string(item))
                        elif isinstance(item, (dict, list)):
                            traverse_dict(item)
            
            traverse_dict(yaml_data)
            
    except yaml.YAMLError as e:
        log.warning(f"Could not parse YAML file {file_path}: {e}")
    except Exception as e:
        log.warning(f"Error analyzing file {file_path}: {e}")
    
    return entities

def get_config_files():
    """Get list of relevant configuration files"""
    config_dir = '/config'
    config_files = []
    
    # ALL YAML files in config root (not just the basic 4!)
    # This was the bug - we were missing package files in root directory
    try:
        for file in os.listdir(config_dir):
            if file.endswith('.yaml') or file.endswith('.yml'):
                full_path = os.path.join(config_dir, file)
                if os.path.isfile(full_path):
                    config_files.append(full_path)
    except Exception as e:
        # Fallback to the original 4 files if directory listing fails
        for filename in ['configuration.yaml', 'automations.yaml', 'scripts.yaml', 'scenes.yaml']:
            full_path = os.path.join(config_dir, filename)
            if os.path.isfile(full_path):
                config_files.append(full_path)
    
    # Package files
    packages_dir = os.path.join(config_dir, 'packages')
    if os.path.isdir(packages_dir):
        for root, dirs, files in os.walk(packages_dir):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    full_path = os.path.join(root, file)
                    config_files.append(full_path)
                    # Write debug info to file if we find the specific water monitor package
                    if 'water_monitor_simulation' in file:
                        try:
                            with open('/config/scan_debug.txt', 'a', encoding='utf-8') as f:
                                f.write(f"Found water monitor package: {full_path}\n")
                        except:
                            pass
    else:
        try:
            with open('/config/scan_debug.txt', 'a', encoding='utf-8') as f:
                f.write(f"Packages directory does not exist: {packages_dir}\n")
        except:
            pass
    
    # Blueprint files
    blueprints_dir = os.path.join(config_dir, 'blueprints')
    if os.path.isdir(blueprints_dir):
        for root, dirs, files in os.walk(blueprints_dir):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    config_files.append(os.path.join(root, file))
    
    return config_files

def generate_lovelace_cards(truly_orphaned_helpers, dashboard_only_helpers, helper_details=None):
    """Generate Lovelace YAML for horizontal stack with entities cards for helper review"""
    
    # Sort the lists for consistent output
    orphaned_sorted = sorted(truly_orphaned_helpers) if truly_orphaned_helpers else []
    dashboard_sorted = sorted(dashboard_only_helpers) if dashboard_only_helpers else []
    
    # Split long lists into chunks for better UI display (max 20 entities per card)
    def chunk_list(lst, chunk_size=20):
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    orphaned_chunks = chunk_list(orphaned_sorted, 20)
    dashboard_chunks = chunk_list(dashboard_sorted, 20)
    
    yaml_content = "# Auto-generated Helper Review Cards\n"
    yaml_content += "# Copy this YAML into a dashboard to review orphaned and dashboard-only helpers\n"
    yaml_content += "# Generated by PyScript Helper Analysis\n\n"
    
    # Create single column layout with wider cards
    yaml_content += "type: vertical-stack\n"
    yaml_content += "card_mod:\n"
    yaml_content += "  style: |\n"
    yaml_content += "    ha-card {\n"
    yaml_content += "      width: 200% !important;\n"
    yaml_content += "      max-width: none !important;\n"
    yaml_content += "    }\n"
    yaml_content += "cards:\n"
    
    # Truly Orphaned Helpers section
    yaml_content += "  # === TRULY ORPHANED HELPERS ===\n"
    
    if orphaned_chunks:
        for i, chunk in enumerate(orphaned_chunks):
            card_title = f"🗑️ Truly Orphaned Helpers"
            if len(orphaned_chunks) > 1:
                card_title += f" ({i+1}/{len(orphaned_chunks)})"
            
            yaml_content += f"  - type: entities\n"
            yaml_content += f"    title: \"{card_title}\"\n"
            yaml_content += f"    state_color: true\n"
            yaml_content += f"    show_header_toggle: false\n"
            yaml_content += f"    card_mod:\n"
            yaml_content += f"      style: |\n"
            yaml_content += f"        ha-card {{\n"
            yaml_content += f"          width: 200% !important;\n"
            yaml_content += f"          max-width: none !important;\n"
            yaml_content += f"        }}\n"
            yaml_content += f"    entities:\n"
            
            for entity in chunk:
                yaml_content += f"      - entity: {entity}\n"
            
            yaml_content += f"    footer:\n"
            yaml_content += f"      type: graph\n"
            yaml_content += f"      entity: sensor.helper_analysis_status\n"
            yaml_content += f"      detail: 1\n"
    else:
        yaml_content += "  - type: entities\n"
        yaml_content += "    title: \"🎉 No Truly Orphaned Helpers\"\n"
        yaml_content += "    entities:\n"
        yaml_content += "      - type: custom:text-element\n"
        yaml_content += "        text: \"All helpers are being used!\"\n"
    
    # Dashboard-Only Helpers section
    yaml_content += "  # === DASHBOARD-ONLY HELPERS ===\n"
    
    if dashboard_chunks:
        for i, chunk in enumerate(dashboard_chunks):
            card_title = f"📊 Dashboard-Only Helpers"
            if len(dashboard_chunks) > 1:
                card_title += f" ({i+1}/{len(dashboard_chunks)})"
            
            yaml_content += f"  - type: entities\n"
            yaml_content += f"    title: \"{card_title}\"\n"
            yaml_content += f"    state_color: true\n"
            yaml_content += f"    show_header_toggle: false\n"
            yaml_content += f"    card_mod:\n"
            yaml_content += f"      style: |\n"
            yaml_content += f"        ha-card {{\n"
            yaml_content += f"          width: 200% !important;\n"
            yaml_content += f"          max-width: none !important;\n"
            yaml_content += f"        }}\n"
            yaml_content += f"    entities:\n"
            
            for entity in chunk:
                # Get dashboard source info for dashboard-only helpers
                dashboard_info = ""
                if helper_details and entity in helper_details:
                    details = helper_details[entity]
                    dashboard_sources = details.get('reference_sources', {}).get('dashboards', [])
                    if dashboard_sources:
                        # Show up to 2 dashboard files, truncate if more
                        if len(dashboard_sources) <= 2:
                            dashboard_info = f" ({', '.join(dashboard_sources)})"
                        else:
                            dashboard_info = f" ({', '.join(dashboard_sources[:2])} +{len(dashboard_sources)-2} more)"
                
                yaml_content += f"      - entity: {entity}\n"
                if dashboard_info:
                    yaml_content += f"        name: \"{entity}{dashboard_info}\"\n"
            
            yaml_content += f"    footer:\n"
            yaml_content += f"      type: graph\n"
            yaml_content += f"      entity: sensor.helper_analysis_status\n"
            yaml_content += f"      detail: 1\n"
    else:
        yaml_content += "  - type: entities\n"
        yaml_content += "    title: \"📊 No Dashboard-Only Helpers\"\n"
        yaml_content += "    entities:\n"
        yaml_content += "      - type: custom:text-element\n"
        yaml_content += "        text: \"No helpers are dashboard-only!\"\n"
    
    # Add summary card at the bottom
    yaml_content += "\n# Summary Information Card (add separately if desired)\n"
    yaml_content += "# type: entities\n"
    yaml_content += "# title: \"📈 Helper Analysis Summary\"\n"
    yaml_content += "# entities:\n"
    yaml_content += "#   - sensor.helper_analysis_status\n"
    yaml_content += f"#   - type: custom:text-element\n"
    yaml_content += f"#     text: \"Truly Orphaned: {len(orphaned_sorted)} | Dashboard-Only: {len(dashboard_sorted)}\"\n"
    
    return yaml_content


@time_trigger("startup")
def analyze_helpers_startup():
    """Run analysis at startup"""
    task.create(analyze_helpers_async())

async def analyze_helpers_async():
    """
    Analyze all helpers and find which ones are referenced in configuration
    """
    
    log.info("=== Starting Enhanced Helper Analysis with PyScript ===")
    
    # Get all entities
    try:
        entity_ids = list(state.names())
    except Exception as e:
        log.error(f"Failed to get entity names: {e}")
        return
    
    # DEBUG: Let's see what entity domains we have
    domain_counts = {}
    for entity_id in entity_ids:
        domain = entity_id.split('.')[0]
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    log.info("Entity domains in system:")
    for domain, count in sorted(domain_counts.items()):
        log.info(f"  {domain}: {count}")
    
    # Let's examine the entity registry to understand helper patterns
    template_entities_from_registry = []
    try:
        registry_result, error = examine_entity_registry()
        if error:
            log.info(f"Could not examine entity registry: {error}")
            template_entities_from_registry = []
        else:
            template_entities_from_registry = registry_result or []
    except Exception as e:
        log.info(f"Could not examine entity registry: {e}")
    
    # Filter to just helpers - now including template entities from registry
    # Use set to prevent duplicates automatically
    helpers_set = set()
    
    # Traditional helpers
    for entity_id in entity_ids:
        if (entity_id.startswith('input_') or 
            entity_id.startswith('counter.') or 
            entity_id.startswith('timer.') or
            entity_id.startswith('variable.')):
            helpers_set.add(entity_id)
    
    # Template helpers from entity registry (this is the missing piece!)
    for entity_id in template_entities_from_registry:
        if entity_id in entity_ids:  # Make sure it still exists
            helpers_set.add(entity_id)
    
    # Legacy template sensor detection for any remaining ones
    for entity_id in entity_ids:
        if ((entity_id.startswith('sensor.') or entity_id.startswith('binary_sensor.')) and
            entity_id not in helpers_set and
            is_template_or_helper_entity(entity_id)):
            helpers_set.add(entity_id)
    
    # Convert back to list for compatibility with rest of code
    helpers = list(helpers_set)
    
    # Separate traditional helpers from templated sensors
    templated_sensors = [h for h in helpers if h.startswith(('sensor.', 'binary_sensor.'))]
    
    # Analyze template dependencies
    log.info("=== Analyzing Template Dependencies ===")
    try:
        template_result, error = analyze_template_dependencies()
        if error:
            log.info(f"Template analysis error: {error}")
            template_dependencies = {}
        else:
            template_dependencies = template_result or {}
            log.info(f"Template analysis returned {type(template_dependencies)} with {len(template_dependencies)} items")
    except Exception as e:
        log.error(f"Template dependency analysis failed: {e}")
        template_dependencies = {}
    
    # Analyze integration config entries for helper references
    log.info("=== Analyzing Integration Config Entries ===")
    try:
        integration_referenced_entities, error = analyze_integration_config_entries()
        if error:
            log.info(f"Integration config analysis error: {error}")
            integration_referenced_entities = []
        else:
            integration_referenced_entities = integration_referenced_entities or []
            log.info(f"Integration configs reference {len(integration_referenced_entities)} helper entities")
    except Exception as e:
        log.info(f"Integration config analysis error: {e}")
        integration_referenced_entities = []
    
    log.info(f"Found {len(helpers)} total helpers to analyze:")
    log.info(f"  - Traditional helpers: {len(helpers) - len(templated_sensors)}")
    log.info(f"  - Templated sensors: {len(templated_sensors)}")
    
    # Create a set of all entities referenced by templates
    template_referenced_entities = set()
    if template_dependencies:
        log.info(f"Processing {len(template_dependencies)} template analysis results:")
        for template_name, dependencies in template_dependencies.items():
            if dependencies:
                template_referenced_entities.update(dependencies)
                dep_list = list(dependencies)
                dep_list.sort()
                log.info(f"  {template_name}: {', '.join(dep_list)}")
            else:
                log.info(f"  {template_name}: No dependencies found")
    else:
        log.info("No template dependencies returned")
    
    if template_referenced_entities:
        template_ref_list = list(template_referenced_entities)
        template_ref_list.sort()
        log.info(f"Template helpers reference {len(template_referenced_entities)} total entities: {', '.join(template_ref_list)}")
    else:
        log.info("No entities referenced by templates")
    
    # Analyze dashboard dependencies
    log.info("=== Analyzing Dashboard Dependencies ===")
    try:
        dashboard_referenced_entities, dashboard_file_mapping = await analyze_dashboard_dependencies()
        if dashboard_referenced_entities:
            dashboard_ref_list = list(dashboard_referenced_entities)
            dashboard_ref_list.sort()
            log.info(f"Dashboards reference {len(dashboard_referenced_entities)} helper entities: {', '.join(dashboard_ref_list[:10])}")
        else:
            log.info("No entities referenced by dashboards")
            dashboard_file_mapping = {}
    except Exception as e:
        log.error(f"Dashboard dependency analysis failed: {e}")
        dashboard_referenced_entities = set()
        dashboard_file_mapping = {}
    
    # Find all entity references in configuration files
    all_referenced_entities = set()
    config_referenced_entities = set()
    config_entity_file_mapping = {}  # Maps entity -> list of files
    config_files = get_config_files()
    
    # Also check for lovelace configuration
    lovelace_files = [
        '/config/ui-lovelace.yaml',
        '/config/lovelace.yaml',
        '/config/dashboards/lovelace.yaml'
    ]
    for lovelace_file in lovelace_files:
        if os.path.isfile(lovelace_file):
            config_files.append(lovelace_file)
    
    log.info(f"Analyzing {len(config_files)} configuration files")
    

    
    for file_path in config_files:
        try:
            # Try different approaches for file reading in PyScript
            content = None
            try:
                # Use proper PyScript I/O with @pyscript_executor
                content = read_config_file(file_path)
            except Exception as e:
                print(f"Failed to read file {file_path}: {e}")
                continue
                    
            if content:
                entities_in_file = analyze_yaml_content(content, file_path)
                all_referenced_entities.update(entities_in_file)
                config_referenced_entities.update(entities_in_file)
                
                # Track which file each entity came from
                filename = os.path.basename(file_path) if file_path else 'unknown'
                for entity in entities_in_file:
                    if entity not in config_entity_file_mapping:
                        config_entity_file_mapping[entity] = []
                    if filename not in config_entity_file_mapping[entity]:
                        config_entity_file_mapping[entity].append(filename)

                # Also check for direct entity ID references (not in templates)
                direct_matches = []
                for helper in helpers:
                    if helper in content:
                        all_referenced_entities.add(helper)
                        config_referenced_entities.add(helper)
                        direct_matches.append(helper)
                        
                        # Track the file reference for direct matches too
                        if helper not in config_entity_file_mapping:
                            config_entity_file_mapping[helper] = []
                        if filename not in config_entity_file_mapping[helper]:
                            config_entity_file_mapping[helper].append(filename)
                

                        
        except Exception as e:
            log.warning(f"Error reading {file_path}: {e}")
    
    log.info(f"Total unique entity references found: {len(all_referenced_entities)}")
    
    # Include template dependencies in the reference check
    all_referenced_entities.update(template_referenced_entities)
    log.info(f"After including template dependencies: {len(all_referenced_entities)} total references")
    
    # Include integration config dependencies in the reference check
    all_referenced_entities.update(integration_referenced_entities)
    log.info(f"After including integration config dependencies: {len(all_referenced_entities)} total references")
    
    # Include dashboard dependencies in the reference check
    all_referenced_entities.update(dashboard_referenced_entities)
    log.info(f"After including dashboard dependencies: {len(all_referenced_entities)} total references")
    
    # Find which helpers are referenced
    referenced_helpers = []
    unreferenced_helpers = []
    
    for helper in helpers:
        if helper in all_referenced_entities:
            referenced_helpers.append(helper)
        else:
            unreferenced_helpers.append(helper)
    
    # Prepare results
    results_dir = '/config/helper_analysis'
    
    # Create results directory
    try:
        os.makedirs(results_dir, exist_ok=True)
    except Exception as e:
        log.error(f"Failed to create results directory: {e}")
        return
    
    # Helper details with reference tracking
    helper_details = {}
    dashboard_only_helpers = []
    
    for helper in helpers:
        try:
            helper_state = state.get(helper)
            
            # Track where this helper is referenced
            reference_sources = {
                'config_files': [],
                'templates': [],
                'dashboards': [],
                'total_references': 0
            }
            
            # Check config file references
            if helper in config_referenced_entities:
                # Use actual filenames from the mapping
                if helper in config_entity_file_mapping:
                    reference_sources['config_files'].extend(config_entity_file_mapping[helper])
                else:
                    reference_sources['config_files'].append('configuration_files')
                reference_sources['total_references'] += 1
            
            # Check template references  
            if template_dependencies:
                for template_file, entities in template_dependencies.items():
                    if helper in entities:
                        reference_sources['templates'].append(template_file)
                        reference_sources['total_references'] += 1
            
            # Check dashboard references
            if dashboard_referenced_entities and helper in dashboard_referenced_entities:
                # Use specific dashboard filenames instead of generic "lovelace_dashboards"
                if helper in dashboard_file_mapping:
                    reference_sources['dashboards'].extend(dashboard_file_mapping[helper])
                else:
                    reference_sources['dashboards'].append('lovelace_dashboards')
                reference_sources['total_references'] += 1
            
            # Determine helper category
            helper_category = 'orphaned'
            if reference_sources['total_references'] > 0:
                if reference_sources['dashboards'] and not reference_sources['config_files'] and not reference_sources['templates']:
                    helper_category = 'dashboard_only'
                    dashboard_only_helpers.append(helper)
                else:
                    helper_category = 'actively_used'
            
            helper_details[helper] = {
                'domain': helper.split('.')[0],
                'state': str(helper_state) if helper_state else 'unavailable',
                'referenced': helper in all_referenced_entities,
                'category': helper_category,
                'reference_sources': reference_sources
            }
        except Exception as e:
            helper_details[helper] = {
                'domain': helper.split('.')[0],
                'state': 'error',
                'error': str(e),
                'referenced': helper in all_referenced_entities,
                'category': 'error',
                'reference_sources': {'config_files': [], 'templates': [], 'dashboards': [], 'total_references': 0}
            }
    
    # Count helpers by category
    actively_used_helpers = [h for h, details in helper_details.items() if details['category'] == 'actively_used']
    truly_orphaned_helpers = [h for h, details in helper_details.items() if details['category'] == 'orphaned']
    
    # Save detailed JSON report
    detailed_report = {
        'analysis': {
            'total_helpers': len(helpers),
            'actively_used': len(actively_used_helpers),
            'dashboard_only': len(dashboard_only_helpers),
            'truly_orphaned': len(truly_orphaned_helpers),
            'config_files_analyzed': len(config_files),
            'template_files_analyzed': len(template_dependencies) if template_dependencies else 0,
            'dashboards_analyzed': 1 if dashboard_referenced_entities else 0
        },
        'helpers': helper_details,
        'helper_categories': {
            'actively_used': actively_used_helpers,
            'dashboard_only': dashboard_only_helpers,
            'truly_orphaned': truly_orphaned_helpers
        },
        'config_files': config_files
    }
    
    json_file = os.path.join(results_dir, 'helper_analysis.json')
    try:
        # Use proper PyScript I/O pattern
        json_content = json.dumps(detailed_report, indent=2, ensure_ascii=False)
        success, error = write_text_file(json_file, json_content)
        if error:
            log.error(f"Failed to write JSON report: {error}")
    except Exception as e:
        log.error(f"Failed to write JSON report: {e}")
    
    # Save TRULY ORPHANED helpers list (for actual cleanup)
    truly_orphaned_file = os.path.join(results_dir, 'truly_orphaned_helpers.txt')
    try:
        orphaned_content = "# Truly Orphaned Helpers (SAFE TO DELETE)\n"
        orphaned_content += f"# Found {len(truly_orphaned_helpers)} helpers with NO references anywhere\n"
        orphaned_content += "# These helpers are not used in config files, templates, or dashboards\n"
        orphaned_content += "# Edit this file to remove helpers you want to keep\n"
        orphaned_content += "# Then use pyscript.delete_helpers to process this file\n\n"
        for helper in sorted(truly_orphaned_helpers):
            orphaned_content += f"{helper}\n"
        
        success, error = write_text_file(truly_orphaned_file, orphaned_content)
        if error:
            log.error(f"Failed to write truly orphaned helpers file: {error}")
    except Exception as e:
        log.error(f"Failed to write truly orphaned helpers file: {e}")
    
    # Save DASHBOARD-ONLY helpers list (for review, not deletion)
    dashboard_only_file = os.path.join(results_dir, 'dashboard_only_helpers.txt')
    try:
        dashboard_content = "# Dashboard-Only Helpers (REVIEW BEFORE DELETING)\n"
        dashboard_content += f"# Found {len(dashboard_only_helpers)} helpers used ONLY in dashboards\n"
        dashboard_content += "# These helpers are not used in config files or templates\n"
        dashboard_content += "# They may be legitimately used for dashboard display purposes\n"
        dashboard_content += "# Review carefully before considering for deletion\n\n"
        for helper in sorted(dashboard_only_helpers):
            dashboard_content += f"{helper}\n"
        
        success, error = write_text_file(dashboard_only_file, dashboard_content)
        if error:
            log.error(f"Failed to write dashboard-only helpers file: {error}")
    except Exception as e:
        log.error(f"Failed to write dashboard-only helpers file: {e}")
    
    # Keep the old orphaned_helpers.txt for backward compatibility (all unreferenced)
    orphaned_file = os.path.join(results_dir, 'orphaned_helpers.txt')
    try:
        orphaned_content = "# All Unreferenced Helpers (DEPRECATED - use truly_orphaned_helpers.txt)\n"
        orphaned_content += f"# This file contains both truly orphaned AND dashboard-only helpers\n"
        orphaned_content += f"# Use 'truly_orphaned_helpers.txt' for safe cleanup instead\n"
        orphaned_content += f"# Use 'dashboard_only_helpers.txt' for dashboard review\n\n"
        for helper in sorted(unreferenced_helpers):
            orphaned_content += f"{helper}\n"
        
        success, error = write_text_file(orphaned_file, orphaned_content)
        if error:
            log.error(f"Failed to write orphaned helpers file: {error}")
    except Exception as e:
        log.error(f"Failed to write orphaned helpers file: {e}")
    
    # Save summary report
    summary_file = os.path.join(results_dir, 'helper_summary.txt')
    try:
        summary_content = "Helper Analysis Summary\n"
        summary_content += "=" * 50 + "\n\n"
        summary_content += f"Total helpers analyzed: {len(helpers)}\n"
        summary_content += f"Helpers with references: {len(referenced_helpers)}\n"
        summary_content += f"Potentially orphaned: {len(unreferenced_helpers)}\n"
        summary_content += f"Configuration files analyzed: {len(config_files)}\n\n"
        
        if unreferenced_helpers:
            summary_content += "POTENTIALLY ORPHANED HELPERS:\n"
            for helper in sorted(unreferenced_helpers):
                summary_content += f"  - {helper}\n"
            summary_content += "\n"
        
        if referenced_helpers:
            summary_content += "HELPERS WITH REFERENCES (first 10):\n"
            for helper in sorted(referenced_helpers)[:10]:
                summary_content += f"  - {helper}\n"
            if len(referenced_helpers) > 10:
                summary_content += f"  ... and {len(referenced_helpers) - 10} more\n"
        
        success, error = write_text_file(summary_file, summary_content)
        if error:
            log.error(f"Failed to write summary report: {error}")
    except Exception as e:
        log.error(f"Failed to write summary report: {e}")
    
    # Generate Lovelace entities cards YAML
    lovelace_file = os.path.join(results_dir, 'helper_review_cards.yaml')
    try:
        lovelace_content = generate_lovelace_cards(truly_orphaned_helpers, dashboard_only_helpers, helper_details)
        success, error = write_text_file(lovelace_file, lovelace_content)
        if error:
            log.error(f"Failed to write Lovelace cards file: {error}")
        else:
            log.info(f"Generated Lovelace review cards: {lovelace_file}")
    except Exception as e:
        log.error(f"Failed to write Lovelace cards file: {e}")
    
    # Update status sensor
    try:
        sensor_attributes = {
            'total_helpers': len(helpers),
            'referenced_count': len(referenced_helpers),
            'unreferenced_count': len(unreferenced_helpers),
            'truly_orphaned_count': len(truly_orphaned_helpers),
            'dashboard_only_count': len(dashboard_only_helpers),
            'json_report': json_file,
            'truly_orphaned_file': truly_orphaned_file,
            'dashboard_only_file': dashboard_only_file,
            'orphaned_file': orphaned_file,
            'summary_file': summary_file
        }
        
        # Set attributes using the proper PyScript way
        state.set('sensor.helper_analysis_status', value='complete', 
                 new_attributes=sensor_attributes)
                 
    except Exception as e:
        log.warning(f"Failed to update status sensor: {e}")
        
    # Log completion
    log.info("=== HELPER ANALYSIS RESULTS ===")
    log.info(f"Total helpers analyzed: {len(helpers)}")
    log.info(f"Actively used (in config/templates): {len(actively_used_helpers)}")
    log.info(f"Dashboard only: {len(dashboard_only_helpers)}")
    log.info(f"Truly orphaned: {len(truly_orphaned_helpers)}")
    
    if dashboard_only_helpers:
        log.info("\nDASHBOARD-ONLY HELPERS (potential cleanup candidates):")
        for helper in sorted(dashboard_only_helpers)[:10]:
            log.info(f"  - {helper}")
        if len(dashboard_only_helpers) > 10:
            log.info(f"  ... and {len(dashboard_only_helpers) - 10} more")
    
    if truly_orphaned_helpers:
        log.info("\nTRULY ORPHANED HELPERS:")
        for helper in sorted(truly_orphaned_helpers)[:10]:
            log.info(f"  - {helper}")
        if len(truly_orphaned_helpers) > 10:
            log.info(f"  ... and {len(truly_orphaned_helpers) - 10} more")
    
    log.info(f"\nReports saved to: {results_dir}")
    log.info("=== HELPER ANALYSIS COMPLETE ===")