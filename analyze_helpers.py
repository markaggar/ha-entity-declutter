# Home Assistant PyScript to Find Helper References - Fixed for PyScript API
# Place this in /config/pyscript/analyze_helpers.py
# Call with: pyscript.analyze_helpers

import json
import re
import yaml
import os

# Import required modules for task.executor
import builtins

def read_file_sync(file_path):
    """Synchronous file reading for use with task.executor"""
    return builtins.open(file_path, 'r', encoding='utf-8').read()

def write_file_sync(file_path, content):
    """Synchronous file writing for use with task.executor"""
    with builtins.open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

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

def examine_entity_registry():
    """Examine the entity registry to understand helper patterns"""
    try:
        entity_registry_file = '/config/.storage/core.entity_registry'
        with builtins.open(entity_registry_file, 'r', encoding='utf-8') as f:
            import json
            entity_registry = json.load(f)
            
        entities = entity_registry.get('data', {}).get('entities', [])
        log.info(f"Entity registry contains {len(entities)} entities")
        
        # Look for template-related entries
        template_sensors = []
        helper_entities = []
        
        for entity in entities:
            entity_id = entity.get('entity_id', '')
            platform = entity.get('platform', '')
            config_entry_id = entity.get('config_entry_id')
            
            # Traditional helpers
            if entity_id.startswith(('input_', 'counter.', 'timer.')):
                helper_entities.append(entity_id)
            
            # Template entities (these are the missing helpers!)
            elif platform == 'template':
                template_sensors.append(entity_id)
                log.info(f"Template helper found: {entity_id} (platform: {platform})")
            
            # Statistics entities (also helpers!)
            elif platform == 'statistics':
                template_sensors.append(entity_id)
                log.info(f"Statistics helper found: {entity_id} (platform: {platform})")
            
            # Other helper platforms
            elif platform in ['integral', 'derivative', 'history_stats', 'trend', 'threshold', 'utility_meter', 'group', 'combine', 'times_of_the_day', 'mold_indicator']:
                template_sensors.append(entity_id)
                log.info(f"Helper found: {entity_id} (platform: {platform})")
            
            # Entities without config entries (could be from configuration.yaml templates)
            elif not config_entry_id and (entity_id.startswith('sensor.') or entity_id.startswith('binary_sensor.')):
                log.info(f"Potential config-based template: {entity_id} (no config entry)")
        
        log.info(f"Found {len(helper_entities)} traditional helpers")
        log.info(f"Found {len(template_sensors)} template/statistics sensors via entity registry")
        
        # DEBUG: Let's see what platforms exist in the system
        platforms_found = set()
        for entity in entities:
            platform = entity.get('platform', '')
            if platform:
                platforms_found.add(platform)
        
        log.info(f"DEBUG - All platforms found in entity registry: {sorted(platforms_found)}")
        
        # Also examine config entries for additional context
        try:
            config_entries_file = '/config/.storage/core.config_entries'
            with builtins.open(config_entries_file, 'r', encoding='utf-8') as f:
                config_entries = json.load(f)
            
            helper_integration_domains = [
                'template', 'statistics', 'utility_meter', 'history_stats', 'integral', 'derivative',
                'threshold', 'trend', 'group', 'counter', 'timer', 'combine', 'times_of_the_day',
                'mold_indicator', 'manual', 'switch_as_x'
            ]
            config_helper_count = 0
            
            for entry in config_entries.get('data', {}).get('entries', []):
                domain = entry.get('domain', '')
                title = entry.get('title', 'N/A')
                
                if (domain in helper_integration_domains or 
                    'sensor' in title.lower() and any(keyword in title.lower() 
                        for keyword in ['integral', 'derivative', 'threshold', 'trend', 'history', 'combine', 'mold']) or
                    'switch' in title.lower() and 'device type' in title.lower() or
                    'alarm control panel' in title.lower()):
                    config_helper_count += 1
                    log.info(f"Helper integration found - Domain: {domain}, Title: {title}")
            
            log.info(f"Found {config_helper_count} helper integrations in config entries")
            
        except Exception as e:
            log.info(f"Could not examine config entries: {e}")
        
        return template_sensors
            
    except Exception as e:
        log.info(f"Error examining entity registry: {e}")
        return []

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
        with builtins.open(registry_file, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
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
                        with builtins.open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
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

def analyze_template_dependencies():
    """Analyze template helpers to find their dependencies on other helpers"""
    template_dependencies = {}
    
    try:
        # Get template helpers from config entries (UI-created)
        config_entries_file = '/config/.storage/core.config_entries'
        with builtins.open(config_entries_file, 'r', encoding='utf-8') as f:
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
                        dep_list = list(dependencies)
                        dep_list.sort()
                        log.info(f"Template '{title}' depends on: {', '.join(dep_list)}")
    
    except Exception as e:
        log.info(f"Error analyzing UI template dependencies: {e}")
    
    # Automatically discover template files
    template_files = discover_template_files()
    
    if not template_files:
        log.info("No template files discovered, falling back to common locations")
        # Fallback to common paths if discovery failed
        template_files = [
            '/config/ai_image_reminders.yaml',
            '/config/template_sensors.yaml', 
            '/config/water_monitor_package.yaml',
            '/config/water_monitor_simulation_package_integration.yaml',
            '/config/packages/templates.yaml',
            '/config/packages/ai_image_reminders.yaml',
            '/config/packages/water_monitor_package.yaml'
        ]
    
    # Analyze discovered template files - simplified approach
    log.info(f"Analyzing {len(template_files)} discovered template files")
    
    for config_file in template_files:
        try:
            log.info(f"Processing template file: {config_file}")
            with builtins.open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            log.info(f"File size: {len(content)} chars, has template markers: {'{{' in content}")
            
            # Simplified approach: analyze entire file content for entity references
            file_name = config_file.split('/')[-1]
            dependencies = extract_template_dependencies(content)
            if dependencies:
                template_dependencies[f"File: {file_name}"] = dependencies
                dep_list = list(dependencies)
                dep_list.sort()
                log.info(f"File '{file_name}' references {len(dependencies)} helper entities: {', '.join(dep_list[:10])}")
            else:
                log.info(f"File '{file_name}' contains no helper entity references")
                    
        except Exception as e:
            log.info(f"Error reading {config_file}: {e}")
            continue
    
    log.info(f"Template analysis complete: {len(template_dependencies)} templates with dependencies")
    return template_dependencies

def analyze_dashboard_dependencies():
    """Analyze Lovelace dashboards to find entity references"""
    dashboard_dependencies = set()
    
    # Comprehensive list of dashboard file locations
    dashboard_files = [
        '/config/ui-lovelace.yaml',
        '/config/lovelace.yaml',
        '/config/lovelace/main.yaml',
        '/config/dashboards/main.yaml',
        '/config/dashboards/lovelace.yaml',
        '/config/.storage/lovelace',
        '/config/.storage/lovelace.main',
        '/config/.storage/lovelace_dashboards'
    ]
    
    # Also check for dashboard directories
    dashboard_dirs = [
        '/config/dashboards/',
        '/config/lovelace/',
        '/config/ui/'
    ]
    
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
            with builtins.open(dash_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract entities from dashboard content
            entities = extract_dashboard_entities(content)
            if entities:
                dashboard_dependencies.update(entities)
                log.info(f"Dashboard {dash_file.split('/')[-1]} references {len(entities)} helper entities")
                
        except Exception as e:
            log.info(f"Error reading dashboard file {dash_file}: {e}")
            continue
    
    log.info(f"Found {len(dashboard_dependencies)} total entities referenced by dashboards")
    return dashboard_dependencies

def extract_dashboard_entities(dashboard_content):
    """Extract entity references from dashboard YAML content"""
    if not dashboard_content:
        return set()
    
    entities = set()
    
    # Patterns for dashboard entity references
    patterns = [
        r"entity:\s*([a-z0-9_]+\.[a-z0-9_]+)",  # entity: sensor.example
        r"entities:\s*\n(?:\s*-\s*([a-z0-9_]+\.[a-z0-9_]+))+",  # entities list
        r"-\s*entity:\s*([a-z0-9_]+\.[a-z0-9_]+)",  # - entity: sensor.example  
        r"-\s*([a-z0-9_]+\.[a-z0-9_]+)",  # - sensor.example (direct entity)
        r"'([a-z0-9_]+\.[a-z0-9_]+)'",  # 'sensor.example'
        r'"([a-z0-9_]+\.[a-z0-9_]+)"',  # "sensor.example"
        r"sensor:\s*([a-z0-9_]+\.[a-z0-9_]+)",  # sensor: sensor.example
        r"binary_sensor:\s*([a-z0-9_]+\.[a-z0-9_]+)",  # binary_sensor: binary_sensor.example
        r"input_[a-z_]+:\s*([a-z0-9_]+\.[a-z0-9_]+)",  # input_boolean: input_boolean.example
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
    """Extract entity IDs from template strings using full regex"""
    if not isinstance(template_str, str):
        return set()
    
    if not (("{{" in template_str and "}}" in template_str) or 
            ("{%" in template_str and "%}" in template_str)):
        return set()
    
    entities = set()
    
    # Regex patterns for entity detection
    patterns = [
        # Template functions with entity ID as first parameter  
        r'(?:states|is_state|state_attr|is_state_attr|has_value|state_translated|device_id|device_name|area_id|area_name)\s*\(\s*[\'"]([a-z_]+\.[a-z0-9_]+)[\'"]',
        # Direct entity state access (states.domain.entity)
        r'states\.([a-z_]+)\.([a-z0-9_]+)(?:\.state|\.attributes)',
        # Entity ID references in quotes
        r'[\'"]([a-z_]+\.[a-z0-9_]+)[\'"]'
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
    """Analyze YAML content for entity references"""
    entities = set()
    
    try:
        yaml_data = yaml.safe_load(content)
        if yaml_data:
            yaml_str = yaml.dump(yaml_data)
            entities.update(extract_entities_from_template_string(yaml_str))
            
            # Also check individual string values for templates
            def traverse_dict(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, str):
                            entities.update(extract_entities_from_template_string(value))
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
    
    # YAML files in config root
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
                    config_files.append(os.path.join(root, file))
    
    # Blueprint files
    blueprints_dir = os.path.join(config_dir, 'blueprints')
    if os.path.isdir(blueprints_dir):
        for root, dirs, files in os.walk(blueprints_dir):
            for file in files:
                if file.endswith('.yaml') or file.endswith('.yml'):
                    config_files.append(os.path.join(root, file))
    
    return config_files

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
        template_entities_from_registry = await task.executor(lambda: examine_entity_registry())
        if template_entities_from_registry is None:
            template_entities_from_registry = []
    except Exception as e:
        log.info(f"Could not examine entity registry: {e}")
    
    # Filter to just helpers - now including template entities from registry
    helpers = []
    
    # Traditional helpers
    for entity_id in entity_ids:
        if (entity_id.startswith('input_') or 
            entity_id.startswith('counter.') or 
            entity_id.startswith('timer.') or
            entity_id.startswith('variable.')):
            helpers.append(entity_id)
    
    # Template helpers from entity registry (this is the missing piece!)
    for entity_id in template_entities_from_registry:
        if entity_id in entity_ids:  # Make sure it still exists
            helpers.append(entity_id)
    
    # Legacy template sensor detection for any remaining ones
    for entity_id in entity_ids:
        if ((entity_id.startswith('sensor.') or entity_id.startswith('binary_sensor.')) and
            entity_id not in helpers and
            is_template_or_helper_entity(entity_id)):
            helpers.append(entity_id)
    
    # Separate traditional helpers from templated sensors
    templated_sensors = [h for h in helpers if h.startswith(('sensor.', 'binary_sensor.'))]
    
    # Analyze template dependencies
    log.info("=== Analyzing Template Dependencies ===")
    try:
        template_dependencies = await task.executor(lambda: analyze_template_dependencies())
        if template_dependencies is None:
            log.info("Template analysis returned None")
            template_dependencies = {}
        else:
            log.info(f"Template analysis returned {type(template_dependencies)} with {len(template_dependencies)} items")
    except Exception as e:
        log.error(f"Template dependency analysis failed: {e}")
        template_dependencies = {}
    
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
        dashboard_referenced_entities = await task.executor(lambda: analyze_dashboard_dependencies())
        if dashboard_referenced_entities:
            dashboard_ref_list = list(dashboard_referenced_entities)
            dashboard_ref_list.sort()
            log.info(f"Dashboards reference {len(dashboard_referenced_entities)} helper entities: {', '.join(dashboard_ref_list[:10])}")
        else:
            log.info("No entities referenced by dashboards")
    except Exception as e:
        log.error(f"Dashboard dependency analysis failed: {e}")
        dashboard_referenced_entities = set()
    
    # Find all entity references in configuration files
    all_referenced_entities = set()
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
                # Method 1: Direct file reading with task.executor and lambda
                content = await task.executor(lambda path: builtins.open(path, 'r', encoding='utf-8').read(), file_path)
            except:
                try:
                    # Method 2: Use actual built-in open if available
                    with builtins.open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except:
                    # Method 3: Log that file reading is not available
                    log.warning(f"File reading not available for {file_path}")
                    continue
                    
            if content:
                entities_in_file = analyze_yaml_content(content, file_path)
                all_referenced_entities.update(entities_in_file)
                
                # Also check for direct entity ID references (not in templates)
                for helper in helpers:
                    if helper in content:
                        all_referenced_entities.add(helper)
                        
        except Exception as e:
            log.warning(f"Error reading {file_path}: {e}")
    
    log.info(f"Total unique entity references found: {len(all_referenced_entities)}")
    
    # Include template dependencies in the reference check
    all_referenced_entities.update(template_referenced_entities)
    log.info(f"After including template dependencies: {len(all_referenced_entities)} total references")
    
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
    
    # Helper details for debugging
    helper_details = {}
    for helper in helpers:
        try:
            helper_state = state.get(helper)
            helper_details[helper] = {
                'domain': helper.split('.')[0],
                'state': str(helper_state) if helper_state else 'unavailable',
                'referenced': helper in all_referenced_entities
            }
        except Exception as e:
            helper_details[helper] = {
                'domain': helper.split('.')[0],
                'state': 'error',
                'error': str(e),
                'referenced': helper in all_referenced_entities
            }
    
    # Save detailed JSON report
    detailed_report = {
        'analysis': {
            'total_helpers': len(helpers),
            'referenced_count': len(referenced_helpers),
            'orphaned_count': len(unreferenced_helpers),
            'config_files_analyzed': len(config_files)
        },
        'helpers': helper_details,
        'referenced_helpers': referenced_helpers,
        'potentially_orphaned': unreferenced_helpers,
        'config_files': config_files
    }
    
    json_file = os.path.join(results_dir, 'helper_analysis.json')
    try:
        # Use task.executor with lambda for file writing
        json_content = json.dumps(detailed_report, indent=2, ensure_ascii=False)
        await task.executor(lambda path, content: builtins.open(path, 'w', encoding='utf-8').write(content), json_file, json_content)
    except Exception as e:
        log.error(f"Failed to write JSON report: {e}")
    
    # Save orphaned helpers list
    orphaned_file = os.path.join(results_dir, 'orphaned_helpers.txt')
    try:
        orphaned_content = "# Potentially Orphaned Helpers\n"
        orphaned_content += f"# Found {len(unreferenced_helpers)} helpers with no references\n"
        orphaned_content += "# Edit this file to remove helpers you want to keep\n"
        orphaned_content += "# Then use pyscript.delete_helpers to process this file\n\n"
        for helper in sorted(unreferenced_helpers):
            orphaned_content += f"{helper}\n"
        
        await task.executor(lambda path, content: builtins.open(path, 'w', encoding='utf-8').write(content), orphaned_file, orphaned_content)
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
        
        await task.executor(lambda path, content: builtins.open(path, 'w', encoding='utf-8').write(content), summary_file, summary_content)
    except Exception as e:
        log.error(f"Failed to write summary report: {e}")
    
    # Update status sensor
    try:
        sensor.helper_analysis_status = 'complete'
        sensor_attributes = {
            'total_helpers': len(helpers),
            'referenced_count': len(referenced_helpers),
            'orphaned_count': len(unreferenced_helpers),
            'json_report': json_file,
            'orphaned_file': orphaned_file,
            'summary_file': summary_file
        }
        
        # Set attributes using the new PyScript way
        state.set('sensor.helper_analysis_status', value='complete', 
                 new_attributes=sensor_attributes)
                 
    except Exception as e:
        log.warning(f"Failed to update status sensor: {e}")
        
    # Log completion
    log.info("=== HELPER ANALYSIS RESULTS ===")
    log.info(f"Total helpers analyzed: {len(helpers)}")
    log.info(f"Helpers with references: {len(referenced_helpers)}")
    log.info(f"Potentially orphaned: {len(unreferenced_helpers)}")
    
    if unreferenced_helpers:
        log.info("\nPOTENTIALLY ORPHANED HELPERS:")
        for helper in sorted(unreferenced_helpers)[:10]:
            log.info(f"  - {helper}")
        if len(unreferenced_helpers) > 10:
            log.info(f"  ... and {len(unreferenced_helpers) - 10} more")
    
    if referenced_helpers:
        log.info("\nHELPERS WITH REFERENCES (first 10):")
        for helper in sorted(referenced_helpers)[:10]:
            log.info(f"  - {helper}")
        if len(referenced_helpers) > 10:
            log.info(f"  ... and {len(referenced_helpers) - 10} more")
    
    log.info(f"\nReports saved to: {results_dir}")
    log.info("=== HELPER ANALYSIS COMPLETE ===")