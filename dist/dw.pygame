import os
import sys
import json
import pygame
import requests
import traceback
import re
from zipfile import ZipFile
from io import BytesIO
from datetime import datetime
from urllib.parse import urljoin, unquote, quote
from threading import Thread
from queue import Queue

# Check for development mode
DEV_MODE = os.getenv('DEV_MODE', 'false').lower() == 'true'

# Auto-detect environment and set paths
# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Set static paths (WORK_DIR and ROMS_DIR will be loaded from settings later)
if DEV_MODE:
    JSON_FILE = os.path.join(SCRIPT_DIR, "..", "assets", "config", "download.json")
    LOG_FILE = os.path.join(SCRIPT_DIR, "..", "error.log")
    CONFIG_FILE = os.path.join(SCRIPT_DIR, "..", "config.json")
    ADDED_SYSTEMS_FILE = os.path.join(SCRIPT_DIR, "..", "added_systems.json")
else:
    JSON_FILE = os.path.join(SCRIPT_DIR, "download.json")
    LOG_FILE = os.path.join(SCRIPT_DIR, "error.log")
    CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
    ADDED_SYSTEMS_FILE = os.path.join(SCRIPT_DIR, "added_systems.json")
FPS = 30
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FONT_SIZE = 28

def log_error(error_msg, error_type=None, traceback_str=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] ERROR: {error_msg}\n"
    if error_type:
        log_message += f"Type: {error_type}\n"
    if traceback_str:
        log_message += f"Traceback:\n{traceback_str}\n"
    log_message += "-" * 80 + "\n"
    
    with open(LOG_FILE, "a") as f:
        f.write(log_message)

# Initialize error log
os.makedirs(os.path.dirname(LOG_FILE) if os.path.dirname(LOG_FILE) else ".", exist_ok=True)
with open(LOG_FILE, "w") as f:
    f.write(f"Error Log - Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("-" * 80 + "\n")

try:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ROM Downloader")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, FONT_SIZE)

    # Initialize joystick if available, otherwise use keyboard
    pygame.joystick.init()
    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
    else:
        print("No joystick detected, use keyboard: Arrow keys, Enter, Escape, Space")

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GREEN = (0, 255, 0)
    GRAY = (180, 180, 180)

    # Load JSON file
    try:
        with open(JSON_FILE) as f:
            data = json.load(f)
    except Exception as e:
        log_error("Failed to load JSON file", type(e).__name__, traceback.format_exc())
        sys.exit(1)

    selected_system = 0
    selected_games = set()
    game_list = []
    mode = "systems"  # systems, games, settings, add_systems, systems_settings, or system_settings
    
    # Add systems state
    available_systems = []
    add_systems_highlighted = 0
    
    # Systems settings variables
    systems_settings_highlighted = 0
    system_settings_highlighted = 0
    selected_system_for_settings = None
    
    # Pagination variables for Switch
    current_page = 0
    total_pages = 1
    highlighted = 0
    
    # Settings scroll variables
    settings_scroll_offset = 0
    
    # Settings will be loaded after functions are defined
    settings = {}
    
    # Controller mapping will be loaded/created dynamically
    controller_mapping = {}
    settings_list = [
        "Enable Box-art Display",
        "Enable Image Cache", 
        "Reset Image Cache",
        "Update from GitHub",
        "View Type",
        "USA Games Only",
        "Debug Controller",
        "Work Directory",
        "ROMs Directory",
        "Nintendo Switch Keys",
        "Remap Controller",
        "Systems Settings"
    ]

    # Directories will be created after settings are loaded

    # Image cache for thumbnails
    image_cache = {}
    image_queue = Queue()
    THUMBNAIL_SIZE = (64, 64)

    def format_size(size_bytes):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def load_settings():
        """Load settings from config file"""
        # Default paths based on environment
        if DEV_MODE:
            # Development mode - use local directories since /userdata might not exist
            default_work_dir = os.path.join(SCRIPT_DIR, "..", "py_downloads")
            default_roms_dir = os.path.join(SCRIPT_DIR, "..", "roms")
        elif os.path.exists("/userdata") and os.access("/userdata", os.W_OK):
            # Console environment with writable /userdata
            default_work_dir = "/userdata/py_downloads"
            default_roms_dir = "/userdata/roms"
        else:
            # Fallback - use script directory
            default_work_dir = os.path.join(SCRIPT_DIR, "py_downloads")
            default_roms_dir = os.path.join(SCRIPT_DIR, "roms")
        
        default_settings = {
            "enable_boxart": True,
            "cache_enabled": True,
            "view_type": "list",
            "usa_only": False,
            "debug_controller": False,
            "work_dir": default_work_dir,
            "roms_dir": default_roms_dir,
            "switch_keys_path": ""
        }
        
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    loaded_settings = json.load(f)
                    # Merge with defaults to handle new settings
                    default_settings.update(loaded_settings)
            else:
                # Create config file with defaults
                save_settings(default_settings)
        except Exception as e:
            log_error("Failed to load settings, using defaults", type(e).__name__, traceback.format_exc())
        
        return default_settings

    def save_settings(settings_to_save):
        """Save settings to config file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(settings_to_save, f, indent=2)
        except Exception as e:
            log_error("Failed to save settings", type(e).__name__, traceback.format_exc())

    def load_controller_mapping():
        """Load controller mapping from file or create new mapping"""
        global controller_mapping
        
        mapping_file = os.path.join(os.path.dirname(CONFIG_FILE), "controller_mapping.json")
        
        try:
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r') as f:
                    controller_mapping = json.load(f)
                    print("Controller mapping loaded from file")
                    return True
            else:
                print("No controller mapping found, will need to create new mapping")
                controller_mapping = {}
                return False
        except Exception as e:
            log_error("Failed to load controller mapping", type(e).__name__, traceback.format_exc())
            controller_mapping = {}
            return False

    def save_controller_mapping():
        """Save controller mapping to file"""
        mapping_file = os.path.join(os.path.dirname(CONFIG_FILE), "controller_mapping.json")
        
        try:
            os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
            with open(mapping_file, 'w') as f:
                json.dump(controller_mapping, f, indent=2)
            print("Controller mapping saved")
        except Exception as e:
            log_error("Failed to save controller mapping", type(e).__name__, traceback.format_exc())

    def needs_controller_mapping():
        """Check if we need to collect controller mapping"""
        essential_buttons = ["select", "back", "start", "detail", "up", "down", "left", "right"]
        return not controller_mapping or not all(button in controller_mapping for button in essential_buttons)

    def get_visible_systems():
        """Get list of systems that are not hidden and not list_systems"""
        system_settings = settings.get("system_settings", {})
        return [d for d in data if not d.get('list_systems', False) and not system_settings.get(d['name'], {}).get('hidden', False)]

    def get_system_index_by_name(system_name):
        """Get the original data array index for a system by name"""
        return next(i for i, d in enumerate(data) if d['name'] == system_name)

    def collect_controller_mapping():
        """Collect controller button mapping from user input"""
        global controller_mapping, show_controller_mapping
        
        essential_buttons = [
            ("up", "D-pad UP"),
            ("down", "D-pad DOWN"), 
            ("left", "D-pad LEFT"),
            ("right", "D-pad RIGHT"),
            ("select", "SELECT/CONFIRM button (usually A)"),
            ("back", "BACK/CANCEL button (usually B)"),
            ("start", "START/MENU button"),
            ("detail", "DETAIL/SECONDARY button (usually Y)"),
            ("left_shoulder", "Left Shoulder button (L/LB)"),
            ("right_shoulder", "Right Shoulder button (R/RB)")
        ]
        
        controller_mapping = {}
        current_button_index = 0
        collecting_input = True
        last_input_time = 0
        
        while collecting_input and current_button_index < len(essential_buttons):
            current_time = pygame.time.get_ticks()
            
            # Clear screen
            screen.fill(WHITE)
            
            # Title
            title_text = "Controller Setup"
            title_surf = font.render(title_text, True, BLACK)
            screen.blit(title_surf, (20, 20))
            
            # Current button instruction
            button_key, button_description = essential_buttons[current_button_index]
            instruction_text = f"Press the {button_description}"
            instruction_surf = font.render(instruction_text, True, BLACK)
            screen.blit(instruction_surf, (20, 80))
            
            # Progress
            progress_text = f"Button {current_button_index + 1} of {len(essential_buttons)}"
            progress_surf = font.render(progress_text, True, GRAY)
            screen.blit(progress_surf, (20, 120))
            
            # Show already mapped buttons
            y_offset = 160
            for i, (mapped_key, _) in enumerate(essential_buttons[:current_button_index]):
                if mapped_key in controller_mapping:
                    mapped_text = f"{mapped_key}: Button {controller_mapping[mapped_key]}"
                    mapped_surf = font.render(mapped_text, True, GREEN)
                    screen.blit(mapped_surf, (20, y_offset + i * 25))
            
            pygame.display.flip()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.JOYBUTTONDOWN:
                    # Debounce input (prevent double registration)
                    if current_time - last_input_time > 300:
                        controller_mapping[button_key] = event.button
                        print(f"Mapped {button_key} to button {event.button}")
                        current_button_index += 1
                        last_input_time = current_time
                elif event.type == pygame.JOYHATMOTION:
                    # Handle D-pad input
                    if current_time - last_input_time > 300:
                        hat_x, hat_y = event.value
                        if button_key == "up" and hat_y == 1:
                            controller_mapping[button_key] = ("hat", 0, 1)
                            current_button_index += 1
                            last_input_time = current_time
                        elif button_key == "down" and hat_y == -1:
                            controller_mapping[button_key] = ("hat", 0, -1)
                            current_button_index += 1
                            last_input_time = current_time
                        elif button_key == "left" and hat_x == -1:
                            controller_mapping[button_key] = ("hat", -1, 0)
                            current_button_index += 1
                            last_input_time = current_time
                        elif button_key == "right" and hat_x == 1:
                            controller_mapping[button_key] = ("hat", 1, 0)
                            current_button_index += 1
                            last_input_time = current_time
                elif event.type == pygame.KEYDOWN:
                    # Allow keyboard input for testing
                    if event.key == pygame.K_ESCAPE:
                        return False
            
            # Small delay to prevent CPU spinning
            pygame.time.wait(16)
        
        # Save the completed mapping
        save_controller_mapping()
        return True

    def get_game_initials(game_name):
        """Extract first 3 initials from game name"""
        if not game_name:
            return "GAM"
        
        # Remove file extension and common brackets/parentheses content
        clean_name = os.path.splitext(game_name)[0]
        clean_name = re.sub(r'\[.*?\]|\(.*?\)', '', clean_name).strip()
        
        # Split into words and get initials
        words = clean_name.split()
        initials = ""
        
        for word in words:
            if word and word[0].isalpha():
                initials += word[0].upper()
                if len(initials) >= 3:
                    break
        
        # Pad with game name characters if not enough initials
        if len(initials) < 3:
            for char in clean_name:
                if char.isalpha() and char.upper() not in initials:
                    initials += char.upper()
                    if len(initials) >= 3:
                        break
        
        # Fallback if still not enough
        while len(initials) < 3:
            initials += "X"
        
        return initials[:3]

    def load_image_async(url, cache_key, game_name=None):
        """Load image in background thread"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Load image from bytes
            image_data = BytesIO(response.content)
            image = pygame.image.load(image_data)
            
            # Scale to thumbnail size
            scaled_image = pygame.transform.scale(image, THUMBNAIL_SIZE)
            
            # Add to queue for main thread to process
            image_queue.put((cache_key, scaled_image))
        except Exception as e:
            log_error(f"Failed to load image from {url}", type(e).__name__, traceback.format_exc())
            
            # Try placeholder image if game name is available
            if game_name:
                try:
                    initials = get_game_initials(game_name)
                    placeholder_url = f"https://placehold.co/50x50?text={initials}"
                    response = requests.get(placeholder_url, timeout=5)
                    response.raise_for_status()
                    
                    # Load placeholder image from bytes
                    image_data = BytesIO(response.content)
                    image = pygame.image.load(image_data)
                    
                    # Scale to thumbnail size
                    scaled_image = pygame.transform.scale(image, THUMBNAIL_SIZE)
                    
                    # Add to queue for main thread to process
                    image_queue.put((cache_key, scaled_image))
                    return
                except Exception:
                    pass  # Fallback to None if placeholder also fails
            
            # Put None to indicate failed load
            image_queue.put((cache_key, None))

    def get_thumbnail(game_item, boxart_url):
        """Get thumbnail for game, loading async if not cached"""
        # Check if box-art is enabled
        if not settings["enable_boxart"]:
            return None
        
        # Handle Switch API format with direct image URLs
        if isinstance(game_item, dict) and 'banner_url' in game_item and game_item['banner_url']:
            # Switch API format - use direct banner URL (JPG format)
            image_url = game_item['banner_url']
            cache_key = f"switch_{game_item['title_id']}"
        elif isinstance(game_item, dict) and 'icon_url' in game_item and game_item['icon_url']:
            # Fallback to icon_url if banner_url not available
            image_url = game_item['icon_url']
            cache_key = f"switch_{game_item.get('title_id', 'unknown')}"
        elif boxart_url:
            # Regular format - construct URL from boxart base + game name
            game_name = game_item if isinstance(game_item, str) else game_item.get('name', '')
            base_name = os.path.splitext(game_name)[0]
            image_url = urljoin(boxart_url, f"{base_name}.png")
            cache_key = f"{boxart_url}_{game_name}"
        else:
            return None
        
        # Return cached image if available and cache is enabled
        if settings["cache_enabled"] and cache_key in image_cache:
            return image_cache[cache_key]
        
        # If cache is disabled but we have the image, return it
        if not settings["cache_enabled"] and cache_key in image_cache:
            return image_cache[cache_key]
        
        # Start loading if not already in cache
        if cache_key not in image_cache:
            image_cache[cache_key] = "loading"  # Mark as loading
            
            if isinstance(game_item, dict) and ('banner_url' in game_item or 'icon_url' in game_item):
                # Switch format - load direct URL
                game_name = game_item.get('name', '')
                thread = Thread(target=load_image_async, args=(image_url, cache_key, game_name))
                thread.daemon = True
                thread.start()
            else:
                # Regular format - try multiple image formats
                game_name = game_item if isinstance(game_item, str) else game_item.get('name', '')
                base_name = os.path.splitext(game_name)[0]
                image_formats = [".png", ".jpg", ".jpeg", ".gif", ".bmp"]
                thread = Thread(target=load_image_with_fallback, args=(boxart_url, base_name, image_formats, cache_key, game_name))
                thread.daemon = True
                thread.start()
        
        return None  # Not ready yet

    def load_image_with_fallback(base_url, base_name, formats, cache_key, game_name=None):
        """Try loading image with different format extensions"""
        for fmt in formats:
            try:
                image_url = urljoin(base_url, f"{base_name}{fmt}")
                response = requests.get(image_url, timeout=5)
                response.raise_for_status()
                
                # Load image from bytes
                image_data = BytesIO(response.content)
                image = pygame.image.load(image_data)
                
                # Scale to thumbnail size
                scaled_image = pygame.transform.scale(image, THUMBNAIL_SIZE)
                
                # Add to queue for main thread to process
                image_queue.put((cache_key, scaled_image))
                return  # Success, exit
                
            except Exception:
                continue  # Try next format
        
        # All formats failed - try placeholder image
        if game_name:
            try:
                initials = get_game_initials(game_name)
                placeholder_url = f"https://placehold.co/50x50?text={initials}"
                response = requests.get(placeholder_url, timeout=5)
                response.raise_for_status()
                
                # Load placeholder image from bytes
                image_data = BytesIO(response.content)
                image = pygame.image.load(image_data)
                
                # Scale to thumbnail size
                scaled_image = pygame.transform.scale(image, THUMBNAIL_SIZE)
                
                # Add to queue for main thread to process
                image_queue.put((cache_key, scaled_image))
                return
            except Exception:
                pass  # Fallback to None if placeholder also fails
        
        # All attempts failed
        image_queue.put((cache_key, None))

    def update_image_cache():
        """Process loaded images from background threads"""
        while not image_queue.empty():
            try:
                cache_key, image = image_queue.get_nowait()
                image_cache[cache_key] = image
            except:
                break

    def reset_image_cache():
        """Clear all cached images"""
        global image_cache
        image_cache.clear()
        
        # Clear the queue as well
        while not image_queue.empty():
            try:
                image_queue.get_nowait()
            except:
                break

    def update_from_github():
        """Download latest files from GitHub repository"""
        try:
            draw_loading_message("Checking for updates...")
            
            # GitHub raw URLs for the files from dist folder
            files_to_update = {
                "download.json": "https://raw.githubusercontent.com/hiitsgabe/roms_downloader/main/dist/download.json",
                "dw.pygame": "https://raw.githubusercontent.com/hiitsgabe/roms_downloader/main/dist/dw.pygame"
            }
            
            total_files = len(files_to_update)
            updated_files = []
            failed_files = []
            
            for i, (filename, url) in enumerate(files_to_update.items()):
                progress = int((i / total_files) * 100)
                draw_progress_bar(f"Updating {filename}...", progress)
                
                try:
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    
                    # Determine the correct file path
                    if filename == "download.json":
                        file_path = JSON_FILE
                    elif filename == "dw.pygame":
                        file_path = __file__  # Current script path
                    
                    # Create backup of existing file
                    backup_path = f"{file_path}.backup"
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, 'r') as original:
                                with open(backup_path, 'w') as backup:
                                    backup.write(original.read())
                        except Exception as backup_error:
                            log_error(f"Failed to create backup for {filename}", type(backup_error).__name__, traceback.format_exc())
                    
                    # Write new content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    updated_files.append(filename)
                    
                except Exception as e:
                    log_error(f"Failed to update {filename}", type(e).__name__, traceback.format_exc())
                    failed_files.append(filename)
                    
                    # Restore backup if it exists
                    backup_path = f"{file_path}.backup"
                    if os.path.exists(backup_path):
                        try:
                            with open(backup_path, 'r') as backup:
                                with open(file_path, 'w') as original:
                                    original.write(backup.read())
                        except Exception as restore_error:
                            log_error(f"Failed to restore backup for {filename}", type(restore_error).__name__, traceback.format_exc())
            
            # Show results
            if updated_files and not failed_files:
                draw_loading_message("Update completed successfully!")
                if "dw.pygame" in updated_files:
                    pygame.time.wait(2000)
                    draw_loading_message("Application will exit now. Please restart to use the updated version.")
                    pygame.time.wait(2000)
                    pygame.quit()
                    sys.exit(0)
            elif updated_files and failed_files:
                draw_loading_message(f"Partial update: {len(updated_files)} updated, {len(failed_files)} failed")
                pygame.time.wait(3000)
            else:
                draw_loading_message("Update failed. Check error log for details.")
                pygame.time.wait(3000)
                
        except Exception as e:
            log_error("Error during GitHub update", type(e).__name__, traceback.format_exc())
            draw_loading_message("Update failed. Check internet connection.")
            pygame.time.wait(3000)

    def draw_progress_bar(text, percent, downloaded=0, total_size=0, speed=0):
        screen.fill(WHITE)
        
        # Draw title with instructions
        title_surf = font.render("Download Progress", True, BLACK)
        screen.blit(title_surf, (20, 10))
        
        # Draw current operation
        text_surf = font.render(text, True, GREEN)
        screen.blit(text_surf, (20, 40))
        
        # Draw progress bar background
        bar_height = 20
        bar_y = 70
        screen_width, screen_height = screen.get_size()
        bar_width = min(screen_width - 80, 600)
        bar_x = 20
        pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_width, bar_height))
        
        # Draw progress
        progress_width = int(bar_width * (percent / 100))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, progress_width, bar_height))
        
        # Draw percentage text
        percent_text = f"{percent}%"
        percent_surf = font.render(percent_text, True, BLACK)
        percent_x = bar_x + 5
        screen.blit(percent_surf, (percent_x, bar_y + 2))
        
        # Draw size and speed info
        if total_size > 0:
            size_text = f"{format_size(downloaded)} / {format_size(total_size)}"
            if speed > 0:
                size_text += f" - {format_size(speed)}/s"
            size_surf = font.render(size_text, True, BLACK)
            size_x = bar_x + 5
            screen.blit(size_surf, (size_x, bar_y + bar_height + 10))
        
        # Draw instructions
        back_button_name = get_button_name("back")
        instructions = [
            f"Press {back_button_name} to cancel download",
            "Please wait while files are being downloaded..."
        ]
        
        y = bar_y + bar_height + 40
        for instruction in instructions:
            inst_surf = font.render(instruction, True, GRAY)
            screen.blit(inst_surf, (20, y))
            y += FONT_SIZE + 5
        
        pygame.display.flip()

    def draw_settings_menu():
        global settings_scroll_offset
        screen.fill(WHITE)
        y = 10
        
        # Draw title
        title_surf = font.render("Settings", True, BLACK)
        screen.blit(title_surf, (20, y))
        y += FONT_SIZE + 10
        
        # Draw instructions
        select_button_name = get_button_name("select")
        back_button_name = get_button_name("back")
        instructions = [
            "Use D-pad to navigate",
            f"Press {select_button_name} to toggle settings",
            f"Press {back_button_name} to go back"
        ]
        
        for instruction in instructions:
            inst_surf = font.render(instruction, True, GRAY)
            screen.blit(inst_surf, (20, y))
            y += FONT_SIZE + 5
        
        y += 20
        start_y = y
        
        # Calculate visible items based on screen height
        screen_width, screen_height = screen.get_size()
        row_height = FONT_SIZE + 10
        cache_info_height = FONT_SIZE + 25  # Space for cache info at bottom
        available_height = screen_height - start_y - cache_info_height - 50  # Leave space for debug controller
        items_per_screen = max(1, available_height // row_height)
        
        # Calculate scroll boundaries
        total_items = len(settings_list)
        max_scroll = max(0, total_items - items_per_screen)
        
        # Adjust scroll offset to keep highlighted item visible
        if highlighted < settings_scroll_offset:
            settings_scroll_offset = highlighted
        elif highlighted >= settings_scroll_offset + items_per_screen:
            settings_scroll_offset = highlighted - items_per_screen + 1
        
        # Clamp scroll offset
        settings_scroll_offset = max(0, min(settings_scroll_offset, max_scroll))
        
        # Calculate visible items
        start_idx = settings_scroll_offset
        end_idx = min(start_idx + items_per_screen, total_items)
        visible_settings = settings_list[start_idx:end_idx]
        
        # Draw settings items
        for i, setting_name in enumerate(visible_settings):
            actual_idx = start_idx + i
            color = GREEN if actual_idx == highlighted else BLACK
            
            # Get current setting value
            setting_value = ""
            if actual_idx == 0:  # Enable Box-art Display
                setting_value = "ON" if settings["enable_boxart"] else "OFF"
            elif actual_idx == 1:  # Enable Image Cache
                setting_value = "ON" if settings["cache_enabled"] else "OFF"
            elif actual_idx == 2:  # Reset Image Cache
                select_button_name = get_button_name("select")
                setting_value = f"Press {select_button_name} to reset"
            elif actual_idx == 3:  # Update from GitHub
                select_button_name = get_button_name("select")
                setting_value = f"Press {select_button_name} to update"
            elif actual_idx == 4:  # View Type
                setting_value = settings["view_type"].upper()
            elif actual_idx == 5:  # USA Games Only
                setting_value = "ON" if settings["usa_only"] else "OFF"
            elif actual_idx == 6:  # Debug Controller
                setting_value = "ON" if settings["debug_controller"] else "OFF"
            elif actual_idx == 7:  # Work Directory
                work_dir = settings.get("work_dir", "")
                setting_value = work_dir[-30:] + "..." if len(work_dir) > 30 else work_dir
            elif actual_idx == 8:  # ROMs Directory
                roms_dir = settings.get("roms_dir", "")
                setting_value = roms_dir[-30:] + "..." if len(roms_dir) > 30 else roms_dir
            elif actual_idx == 9:  # Nintendo Switch Keys
                keys_path = settings.get("switch_keys_path", "")
                if keys_path and os.path.exists(keys_path):
                    setting_value = keys_path[-30:] + "..." if len(keys_path) > 30 else keys_path
                else:
                    setting_value = "Not configured"
            elif actual_idx == 10:  # Remap Controller
                if controller_mapping:
                    setting_value = f"{len(controller_mapping)} buttons mapped"
                else:
                    setting_value = "Not configured"
            elif actual_idx == 11:  # Systems Settings
                select_button_name = get_button_name("select")
                setting_value = f"Press {select_button_name} to configure"
            
            setting_text = f"{setting_name}: {setting_value}"
            setting_surf = font.render(setting_text, True, color)
            screen.blit(setting_surf, (20, y))
            y += row_height
        
        
        # Draw debug controller info
        draw_debug_controller()

    def draw_add_systems_menu():
        screen.fill(WHITE)
        y = 10
        
        # Draw title
        title_surf = font.render("Add Systems", True, BLACK)
        screen.blit(title_surf, (20, y))
        y += FONT_SIZE + 10
        
        # Draw instructions
        select_button_name = get_button_name("select")
        back_button_name = get_button_name("back")
        instructions = [
            "Use D-pad to navigate",
            f"Press {select_button_name} to add system",
            f"Press {back_button_name} to go back"
        ]
        
        for instruction in instructions:
            inst_surf = font.render(instruction, True, GRAY)
            screen.blit(inst_surf, (20, y))
            y += FONT_SIZE + 5
        
        y += 20
        
        # Show loading message if no systems loaded yet
        if not available_systems:
            loading_surf = font.render("Loading available systems...", True, BLACK)
            screen.blit(loading_surf, (20, y))
        else:
            # Calculate visible items for scrolling
            screen_width, screen_height = screen.get_size()
            available_height = screen_height - y - 50  # Leave space for debug info
            items_per_screen = available_height // (FONT_SIZE + 10)
            
            # Calculate scroll offset to keep highlighted item visible
            start_idx = max(0, add_systems_highlighted - items_per_screen // 2)
            end_idx = min(len(available_systems), start_idx + items_per_screen)
            
            # Draw available systems list with scrolling
            for i in range(start_idx, end_idx):
                system = available_systems[i]
                color = GREEN if i == add_systems_highlighted else BLACK
                system_text = f"{system['name']} - {system.get('size', 'Unknown size')}"
                system_surf = font.render(system_text, True, color)
                screen.blit(system_surf, (20, y))
                y += FONT_SIZE + 10
            
            # Show scroll indicator if needed
            if len(available_systems) > items_per_screen:
                if start_idx > 0:
                    # Show up arrow
                    up_arrow = font.render("↑", True, GRAY)
                    screen.blit(up_arrow, (screen_width - 30, 10))
                if end_idx < len(available_systems):
                    # Show down arrow
                    down_arrow = font.render("↓", True, GRAY)
                    screen.blit(down_arrow, (screen_width - 30, screen_height - 30))
        
        # Draw debug controller info
        draw_debug_controller()

    def draw_systems_settings_menu():
        """Draw the systems settings menu that lists all systems"""
        screen.fill(WHITE)
        y = 10
        
        # Draw title
        title_surf = font.render("Systems Settings", True, BLACK)
        screen.blit(title_surf, (20, y))
        y += FONT_SIZE + 10
        
        # Draw instructions
        select_button_name = get_button_name("select")
        back_button_name = get_button_name("back")
        instructions = [
            "Use D-pad to navigate",
            f"Press {select_button_name} to configure system",
            f"Press {back_button_name} to go back"
        ]
        
        for instruction in instructions:
            inst_surf = font.render(instruction, True, GRAY)
            screen.blit(inst_surf, (20, y))
            y += FONT_SIZE + 5
        
        y += 20
        
        # Filter out 'Other Systems' and 'list_systems' entries
        configurable_systems = [d for d in data if not d.get('list_systems', False) and d.get('name') != 'Other Systems']
        
        # Calculate visible items
        screen_width, screen_height = screen.get_size()
        row_height = FONT_SIZE + 10
        available_height = screen_height - y - 50  # Leave space for debug controller
        items_per_screen = max(1, available_height // row_height)
        
        start_idx = max(0, systems_settings_highlighted - items_per_screen // 2)
        end_idx = min(start_idx + items_per_screen, len(configurable_systems))
        visible_systems = configurable_systems[start_idx:end_idx]
        
        # Draw systems list
        for i, system in enumerate(visible_systems):
            actual_idx = start_idx + i
            color = GREEN if actual_idx == systems_settings_highlighted else BLACK
            
            # Get system status
            system_settings = settings.get("system_settings", {})
            system_name = system['name']
            is_hidden = system_settings.get(system_name, {}).get('hidden', False)
            custom_folder = system_settings.get(system_name, {}).get('custom_folder', '')
            
            status_parts = []
            if is_hidden:
                status_parts.append("HIDDEN")
            if custom_folder:
                status_parts.append(f"Custom: {os.path.basename(custom_folder)}")
            
            status = f" ({', '.join(status_parts)})" if status_parts else ""
            system_text = f"{system_name}{status}"
            
            system_surf = font.render(system_text, True, color)
            screen.blit(system_surf, (20, y))
            y += row_height
        
        # Show scroll indicator if needed
        if len(configurable_systems) > items_per_screen:
            if start_idx > 0:
                up_arrow = font.render("↑", True, GRAY)
                screen.blit(up_arrow, (screen_width - 30, 10))
            if end_idx < len(configurable_systems):
                down_arrow = font.render("↓", True, GRAY)
                screen.blit(down_arrow, (screen_width - 30, screen_height - 30))
        
        # Draw debug controller info
        draw_debug_controller()

    def draw_system_settings_menu():
        """Draw the individual system settings menu"""
        if not selected_system_for_settings:
            return
            
        screen.fill(WHITE)
        y = 10
        
        # Draw title
        title_surf = font.render(f"Settings for {selected_system_for_settings['name']}", True, BLACK)
        screen.blit(title_surf, (20, y))
        y += FONT_SIZE + 10
        
        # Draw instructions
        select_button_name = get_button_name("select")
        back_button_name = get_button_name("back")
        instructions = [
            "Use D-pad to navigate",
            f"Press {select_button_name} to toggle/configure",
            f"Press {back_button_name} to go back"
        ]
        
        for instruction in instructions:
            inst_surf = font.render(instruction, True, GRAY)
            screen.blit(inst_surf, (20, y))
            y += FONT_SIZE + 5
        
        y += 20
        
        # Get current system settings
        system_settings = settings.get("system_settings", {})
        system_name = selected_system_for_settings['name']
        current_settings = system_settings.get(system_name, {})
        
        # Settings options
        settings_options = [
            "Hide from main menu",
            "Custom ROM folder"
        ]
        
        # Draw settings options
        for i, option in enumerate(settings_options):
            color = GREEN if i == system_settings_highlighted else BLACK
            
            # Get current value
            if i == 0:  # Hide from main menu
                value = "ON" if current_settings.get('hidden', False) else "OFF"
            elif i == 1:  # Custom ROM folder
                custom_folder = current_settings.get('custom_folder', '')
                if custom_folder:
                    value = custom_folder[-40:] + "..." if len(custom_folder) > 40 else custom_folder
                else:
                    value = f"Default ({selected_system_for_settings.get('roms_folder', 'N/A')})"
            
            option_text = f"{option}: {value}"
            option_surf = font.render(option_text, True, color)
            screen.blit(option_surf, (20, y))
            y += FONT_SIZE + 10
        
        # Draw debug controller info
        draw_debug_controller()

    def draw_grid_view(title, items, selected_indices):
        screen.fill(WHITE)
        y = 10
        
        # Draw title
        title_surf = font.render(title, True, BLACK)
        screen.blit(title_surf, (20, y))
        y += FONT_SIZE + 10
        
        # Draw download instruction if games are selected
        if selected_indices:
            start_button_name = get_button_name("start")
            instruction = f"Press start to initiate downloading"
            inst_surf = font.render(instruction, True, GRAY)
            screen.blit(inst_surf, (20, y))
            y += FONT_SIZE + 5
        
        y += 20
        
        # Grid layout parameters
        cols = 4  # Number of columns
        screen_width, screen_height = screen.get_size()
        cell_width = (screen_width - 40) // cols
        cell_height = max(THUMBNAIL_SIZE[1] + 40, 100)
        start_x = 20
        start_y = y
        
        # Calculate visible items (ensure at least 2 rows)
        available_height = screen_height - start_y - 50
        if available_height > 0:
            calculated_rows = available_height // cell_height
            rows_per_screen = max(2, calculated_rows)  # Minimum 2 rows
        else:
            # Extremely small screen, fallback to minimum
            rows_per_screen = 2
        items_per_screen = cols * rows_per_screen
        
        # Calculate grid position of highlighted item
        highlighted_row = highlighted // cols
        highlighted_col = highlighted % cols
        
        # Calculate scroll offset to keep highlighted item visible
        start_row = max(0, highlighted_row - rows_per_screen // 2)
        visible_items = items[start_row * cols:(start_row + rows_per_screen) * cols]
        
        # Draw grid items
        for i, item in enumerate(visible_items):
            actual_idx = start_row * cols + i
            if actual_idx >= len(items):
                break
                
            row = i // cols
            col = i % cols
            
            x = start_x + col * cell_width
            y = start_y + row * cell_height
            
            # Handle different item formats
            if isinstance(item, dict):
                display_text = item['name']
                original_name = item['name']
            else:
                display_text = os.path.splitext(item)[0]
                original_name = item
            
            # Highlight background if selected or highlighted
            is_highlighted = actual_idx == highlighted
            is_selected = actual_idx in selected_indices
            
            if is_highlighted:
                highlight_rect = pygame.Rect(x, y, cell_width - 5, cell_height - 5)
                pygame.draw.rect(screen, GREEN, highlight_rect, 2)
            
            # Draw thumbnail if available
            thumb_y = y + 5
            boxart_url = data[selected_system].get('boxarts', '') if selected_system < len(data) else ''
            thumbnail = get_thumbnail(item, boxart_url)
            
            if thumbnail and thumbnail != "loading":
                # Center thumbnail in cell
                thumb_x = x + 5
                thumb_rect = pygame.Rect(thumb_x, thumb_y, THUMBNAIL_SIZE[0], THUMBNAIL_SIZE[1])
                screen.blit(thumbnail, thumb_rect)
                
                # Draw border around thumbnail
                pygame.draw.rect(screen, BLACK, thumb_rect, 1)
            
            # Draw selection indicator
            checkbox_x = x + 5
            checkbox_y = y + 5
            checkbox_rect = pygame.Rect(checkbox_x, checkbox_y, 15, 15)
            pygame.draw.rect(screen, WHITE, checkbox_rect)
            pygame.draw.rect(screen, BLACK, checkbox_rect, 1)
            
            if is_selected:
                # Draw X for selected
                pygame.draw.line(screen, GREEN, (checkbox_x + 3, checkbox_y + 3), (checkbox_x + 12, checkbox_y + 12), 2)
                pygame.draw.line(screen, GREEN, (checkbox_x + 12, checkbox_y + 3), (checkbox_x + 3, checkbox_y + 12), 2)
            
            # Draw text (truncated to fit cell width)
            text_y = thumb_y + THUMBNAIL_SIZE[1] + 5
            max_text_width = cell_width - 10
            
            # Truncate text if too long
            test_surf = font.render(display_text, True, BLACK)
            if test_surf.get_width() > max_text_width:
                # Truncate text
                for length in range(len(display_text), 0, -1):
                    truncated = display_text[:length] + "..."
                    test_surf = font.render(truncated, True, BLACK)
                    if test_surf.get_width() <= max_text_width:
                        display_text = truncated
                        break
            
            text_color = GREEN if is_selected else BLACK
            text_surf = font.render(display_text, True, text_color)
            text_x = x + 5
            screen.blit(text_surf, (text_x, text_y))
        
        # Draw bottom message if games are selected
        if selected_indices:
            message = f"Selected: {len(selected_indices)} games"
            message_surf = font.render(message, True, GREEN)
            screen_width, screen_height = screen.get_size()
            message_y = screen_height - 30
            screen.blit(message_surf, (20, message_y))
        
        # Draw debug controller info
        draw_debug_controller()
        
        if not show_game_details:
            pygame.display.flip()

    def draw_menu(title, items, selected_indices):
        screen.fill(WHITE)
        y = 10  # Start closer to top
        
        # Draw title with instructions
        title_surf = font.render(title, True, BLACK)
        screen.blit(title_surf, (20, y))
        y += FONT_SIZE + 10

        # Draw download instruction if in games mode and games are selected
        if mode == "games" and selected_games:
            start_button_name = get_button_name("start")
            instruction = f"Press start to initiate downloading"
            inst_surf = font.render(instruction, True, GRAY)
            screen.blit(inst_surf, (20, y))
            y += FONT_SIZE + 5
        
        y += 20  # Add some space after instructions
        
        # Calculate visible items based on screen height
        row_height = max(FONT_SIZE + 10, THUMBNAIL_SIZE[1] + 10) if mode == "games" else FONT_SIZE + 10
        screen_width, screen_height = screen.get_size()
        items_per_page = (screen_height - y - 50) // row_height  # Leave space for bottom message
        start_idx = max(0, highlighted - items_per_page // 2)
        visible_items = items[start_idx:start_idx + items_per_page]
        
        # Draw items
        for i, item in enumerate(visible_items):
            actual_idx = start_idx + i
            # Color is green if item is highlighted or selected
            color = GREEN if actual_idx == highlighted or actual_idx in selected_indices else BLACK
            prefix = "[x] " if actual_idx in selected_indices else "[ ] " if mode == "games" else ""
            
            # Handle different item formats (Switch vs regular)
            if isinstance(item, dict):
                display_text = item['name']
                original_name = item['name']
            else:
                # Remove file extension for display
                display_text = os.path.splitext(item)[0]
                original_name = item
            
            # Draw thumbnail if in games mode and boxart available
            text_x = 20
            if mode == "games":
                boxart_url = data[selected_system].get('boxarts', '') if selected_system < len(data) else ''
                thumbnail = get_thumbnail(item, boxart_url)
                
                if thumbnail and thumbnail != "loading":
                    # Draw thumbnail
                    thumb_rect = pygame.Rect(20, y, THUMBNAIL_SIZE[0], THUMBNAIL_SIZE[1])
                    screen.blit(thumbnail, thumb_rect)
                    
                    # Draw border around thumbnail if highlighted
                    if actual_idx == highlighted:
                        pygame.draw.rect(screen, GREEN, thumb_rect, 2)
                    
                    text_x = 20 + THUMBNAIL_SIZE[0] + 10  # Move text after thumbnail
            
            # Draw text
            item_surf = font.render(prefix + display_text, True, color)
            text_y = y + (row_height - FONT_SIZE) // 2  # Center text vertically
            screen.blit(item_surf, (text_x, text_y))
            y += row_height

        # Draw bottom message if games are selected
        if mode == "games" and selected_games:
            message = f"Selected: {len(selected_games)} games"
            message_surf = font.render(message, True, GREEN)
            screen_width, screen_height = screen.get_size()
            message_y = screen_height - 50
            screen.blit(message_surf, (20, message_y))
        
        # Draw pagination info for Switch
        if mode == "games" and len(data) > 0 and data[selected_system].get('supports_pagination', False):
            page_message = f"Page {current_page + 1} (L/R to change page)"
            page_surf = font.render(page_message, True, GRAY)
            screen_width, screen_height = screen.get_size()
            page_y = screen_height - 30
            screen.blit(page_surf, (20, page_y))

        # Draw debug controller info
        draw_debug_controller()

        if not show_game_details:
            pygame.display.flip()

    def draw_game_details_modal(game_item):
        """Draw the game details modal overlay"""
        # Get actual screen dimensions
        screen_width, screen_height = screen.get_size()
        
        # Semi-transparent background overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Responsive modal sizing
        # Use 90% of screen width/height but with min/max constraints
        modal_width = min(max(int(screen_width * 0.9), 300), 500)
        modal_height = min(max(int(screen_height * 0.8), 250), 400)
        modal_x = (screen_width - modal_width) // 2
        modal_y = (screen_height - modal_height) // 2
        
        modal_rect = pygame.Rect(modal_x, modal_y, modal_width, modal_height)
        pygame.draw.rect(screen, WHITE, modal_rect)
        pygame.draw.rect(screen, BLACK, modal_rect, 3)
        
        # Game name
        if isinstance(game_item, dict):
            game_name = game_item.get('name', 'Unknown Game')
        else:
            game_name = os.path.splitext(game_item)[0] if isinstance(game_item, str) else 'Unknown Game'
        
        # Draw title
        title_surf = font.render("Game Details", True, BLACK)
        title_x = modal_x + 20
        title_y = modal_y + 20
        screen.blit(title_surf, (title_x, title_y))
        
        # Draw game name (with text wrapping if needed)
        margin = max(20, int(modal_width * 0.05))  # Responsive margin (5% of width, min 20px)
        name_y = title_y + 40
        max_name_width = modal_width - (margin * 2)
        
        # Simple text wrapping
        words = game_name.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surf = font.render(test_line, True, BLACK)
            if test_surf.get_width() <= max_name_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)  # Single word too long
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw wrapped text
        max_lines = max(2, min(3, modal_height // 100))  # Responsive line count based on modal height
        for i, line in enumerate(lines[:max_lines]):
            name_surf = font.render(line, True, GREEN)
            screen.blit(name_surf, (modal_x + margin, name_y + i * (FONT_SIZE + 5)))
        
        # Draw large image if available
        image_y = name_y + len(lines) * (FONT_SIZE + 5) + 20
        boxart_url = data[selected_system].get('boxarts', '') if selected_system < len(data) else ''
        thumbnail = get_thumbnail(game_item, boxart_url)
        
        if thumbnail and thumbnail != "loading":
            # Calculate appropriate image size that fits within modal responsively
            available_width = modal_width - (margin * 2)  # Use responsive margins
            available_height = modal_height - (image_y - modal_y) - (margin * 3)  # Space for instructions
            # Scale max image size based on modal size, but set reasonable limits
            max_image_size = min(available_width, available_height, min(modal_width // 2, 200))
            
            try:
                # Scale image proportionally to fit within the available space
                original_size = thumbnail.get_size()
                scale_factor = min(max_image_size / original_size[0], max_image_size / original_size[1])
                new_width = int(original_size[0] * scale_factor)
                new_height = int(original_size[1] * scale_factor)
                large_size = (new_width, new_height)
                
                large_image = pygame.transform.scale(thumbnail, large_size)
                image_x = modal_x + (modal_width - large_size[0]) // 2
                screen.blit(large_image, (image_x, image_y))
                
                # Draw border around image
                image_rect = pygame.Rect(image_x, image_y, large_size[0], large_size[1])
                pygame.draw.rect(screen, BLACK, image_rect, 2)
            except:
                # Fallback to original thumbnail
                image_x = modal_x + (modal_width - THUMBNAIL_SIZE[0]) // 2
                screen.blit(thumbnail, (image_x, image_y))
        else:
            # No image available text
            no_image_text = "No image available"
            no_image_surf = font.render(no_image_text, True, GRAY)
            no_image_x = modal_x + (modal_width - no_image_surf.get_width()) // 2
            screen.blit(no_image_surf, (no_image_x, image_y))
        
        # Instructions with responsive positioning
        back_button_name = get_button_name("back")
        instruction_text = f"Press {back_button_name} to close"
        instruction_surf = font.render(instruction_text, True, WHITE)
        instruction_x = modal_x + (modal_width - instruction_surf.get_width()) // 2
        
        # Position instructions either below modal or at bottom of screen if modal is too tall
        instruction_y_below = modal_y + modal_height + margin
        instruction_y_bottom = screen_height - 30
        
        # Use whichever position fits better on screen
        if instruction_y_below + instruction_surf.get_height() <= screen_height - 10:
            instruction_y = instruction_y_below
        else:
            instruction_y = instruction_y_bottom
            
        screen.blit(instruction_surf, (instruction_x, instruction_y))

    def draw_folder_browser_modal():
        """Draw the folder browser modal overlay"""
        global folder_browser_scroll_offset
        
        # Get actual screen dimensions
        screen_width, screen_height = screen.get_size()
        
        # Semi-transparent background overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Modal sizing
        modal_width = min(int(screen_width * 0.9), 600)
        modal_height = min(int(screen_height * 0.8), 500)
        modal_x = (screen_width - modal_width) // 2
        modal_y = (screen_height - modal_height) // 2
        
        modal_rect = pygame.Rect(modal_x, modal_y, modal_width, modal_height)
        pygame.draw.rect(screen, WHITE, modal_rect)
        pygame.draw.rect(screen, BLACK, modal_rect, 3)
        
        # Title
        if selected_system_to_add is not None:
            if selected_system_to_add.get("type") == "work_dir":
                title_text = f"Select Work Directory"
            elif selected_system_to_add.get("type") == "switch_keys":
                title_text = f"Select Nintendo Switch Keys File"
            else:
                title_text = f"Select ROM Folder for {selected_system_to_add['name']}"
        else:
            title_text = "Select Folder"
        title_surf = font.render(title_text, True, BLACK)
        title_x = modal_x + 20
        title_y = modal_y + 20
        screen.blit(title_surf, (title_x, title_y))
        
        # Current path
        current_path_display = folder_browser_current_path
        if len(current_path_display) > 50:
            current_path_display = "..." + current_path_display[-47:]
        
        path_surf = font.render(f"Path: {current_path_display}", True, GRAY)
        path_y = title_y + 35
        screen.blit(path_surf, (title_x, path_y))
        
        # Instructions
        select_button_name = get_button_name("select")
        back_button_name = get_button_name("back")
        detail_button_name = get_button_name("detail")
        create_folder_button_name = get_button_name("create_folder")
        
        if selected_system_to_add is not None:
            if selected_system_to_add.get("type") == "work_dir":
                instructions = [
                    f"Use D-pad to navigate",
                    f"Press {select_button_name} to enter folder or create new folder",
                    f"Press {detail_button_name} to select this folder as work directory",
                    f"Press {back_button_name} to cancel"
                ]
            elif selected_system_to_add.get("type") == "switch_keys":
                instructions = [
                    f"Use D-pad to navigate",
                    f"Press {select_button_name} to enter [DIR] or select [KEY] file",
                    f"Press {detail_button_name} to select current folder path",
                    f"Press {back_button_name} to cancel"
                ]
            else:
                instructions = [
                    f"Use D-pad to navigate",
                    f"Press {select_button_name} to enter folder or create new folder",
                    f"Press {detail_button_name} to select this folder for {selected_system_to_add['name']}",
                    f"Press {back_button_name} to cancel"
                ]
        else:
            instructions = [
                f"Use D-pad to navigate",
                f"Press {select_button_name} to enter folder or create new folder",
                f"Press {detail_button_name} to select current folder",
                f"Press {back_button_name} to cancel"
            ]
        
        inst_y = path_y + 35
        for instruction in instructions:
            inst_surf = font.render(instruction, True, GRAY)
            screen.blit(inst_surf, (title_x, inst_y))
            inst_y += 20
        
        # Calculate list area
        list_y = inst_y + 20
        list_height = modal_height - (list_y - modal_y) - 20
        row_height = FONT_SIZE + 5
        items_per_screen = max(1, list_height // row_height)
        
        # Calculate scroll
        total_items = len(folder_browser_items)
        max_scroll = max(0, total_items - items_per_screen)
        
        # Auto-scroll to keep highlighted item visible
        if folder_browser_highlighted < folder_browser_scroll_offset:
            folder_browser_scroll_offset = folder_browser_highlighted
        elif folder_browser_highlighted >= folder_browser_scroll_offset + items_per_screen:
            folder_browser_scroll_offset = folder_browser_highlighted - items_per_screen + 1
        
        folder_browser_scroll_offset = max(0, min(folder_browser_scroll_offset, max_scroll))
        
        # Draw folder items
        start_idx = folder_browser_scroll_offset
        end_idx = min(start_idx + items_per_screen, total_items)
        visible_items = folder_browser_items[start_idx:end_idx]
        
        # Debug: Print folder browser items
        print(f"Folder browser items: {len(folder_browser_items)} total, highlighted: {folder_browser_highlighted}")
        for i, item in enumerate(folder_browser_items):
            print(f"  {i}: {item['name']} ({item['type']})")
        
        for i, item in enumerate(visible_items):
            actual_idx = start_idx + i
            is_highlighted = actual_idx == folder_browser_highlighted
            
            item_y = list_y + i * row_height
            color = GREEN if is_highlighted else BLACK
            
            # Prefix based on type
            if item["type"] == "parent":
                display_name = f"[DIR] {item['name']} (Go back)"
            elif item["type"] == "folder":
                display_name = f"[DIR] {item['name']}"
            elif item["type"] == "create_folder":
                display_name = f"[DIR] {item['name']}"
            elif item["type"] == "error":
                display_name = f"[ERR] {item['name']}"
                color = GRAY
            elif item["type"] == "keys_file":
                display_name = f"[KEY] {item['name']}"
            else:
                display_name = item['name']
            
            # Truncate if too long
            max_width = modal_width - 60
            test_surf = font.render(display_name, True, color)
            if test_surf.get_width() > max_width:
                while len(display_name) > 5 and test_surf.get_width() > max_width:
                    display_name = display_name[:-4] + "..."
                    test_surf = font.render(display_name, True, color)
            
            # Highlight background
            if is_highlighted:
                highlight_rect = pygame.Rect(modal_x + 10, item_y - 2, modal_width - 20, row_height)
                pygame.draw.rect(screen, (240, 240, 240), highlight_rect)
            
            # Draw item
            item_surf = font.render(display_name, True, color)
            screen.blit(item_surf, (title_x, item_y))

    def draw_debug_controller():
        """Draw the current pressed button at the bottom of the screen if debug mode is enabled"""
        if not settings.get("debug_controller", False):
            return
        
        current_time = pygame.time.get_ticks()
        if current_time - last_button_time < BUTTON_DISPLAY_TIME and current_pressed_button:
            screen_width, screen_height = screen.get_size()
            debug_text = f"Button: {current_pressed_button}"
            debug_surf = font.render(debug_text, True, BLACK)
            debug_x = screen_width - debug_surf.get_width() - 20
            debug_y = screen_height - 30
            
            # Draw background rectangle
            padding = 5
            debug_rect = pygame.Rect(debug_x - padding, debug_y - padding, 
                                   debug_surf.get_width() + 2 * padding, 
                                   debug_surf.get_height() + 2 * padding)
            pygame.draw.rect(screen, WHITE, debug_rect)
            pygame.draw.rect(screen, BLACK, debug_rect, 1)
            
            screen.blit(debug_surf, (debug_x, debug_y))

    def draw_loading_message(message):
        screen.fill(WHITE)
        
        # Draw title
        title_surf = font.render("Loading", True, BLACK)
        screen.blit(title_surf, (20, 10))
        
        # Draw message
        message_surf = font.render(message, True, BLACK)
        screen.blit(message_surf, (20, 50))
        
        # Draw instructions
        back_button_name = get_button_name("back")
        instructions = [
            "Please wait...",
            f"Press {back_button_name} to cancel"
        ]
        
        y = 100
        for instruction in instructions:
            inst_surf = font.render(instruction, True, GRAY)
            screen.blit(inst_surf, (20, y))
            y += FONT_SIZE + 5
        
        # Draw debug controller info
        draw_debug_controller()
        
        if not show_game_details:
            pygame.display.flip()

    def download_files(system, selected_game_indices):
        try:
            sys_data = data[system]
            formats = sys_data.get('file_format', [])
            
            # Check for custom ROM folder setting
            system_name = sys_data['name']
            system_settings = settings.get("system_settings", {})
            custom_folder = system_settings.get(system_name, {}).get('custom_folder', '')
            
            if custom_folder and os.path.exists(custom_folder):
                roms_folder = custom_folder
            else:
                roms_folder = os.path.join(ROMS_DIR, sys_data['roms_folder'])
            
            os.makedirs(roms_folder, exist_ok=True)

            selected_files = [game_list[i] for i in selected_game_indices]
            total = len(selected_files)
            cancelled = False

            for idx, game_item in enumerate(selected_files):
                if cancelled:
                    break
                
                # Handle different game formats
                if isinstance(game_item, dict):
                    # Switch API format
                    game_name = game_item['name']
                    title_id = game_item['title_id']
                    filename = f"{game_name} [{title_id}][v0].nsz"
                else:
                    # Regular filename
                    game_name = game_item
                    filename = game_item
                
                # Calculate overall progress
                overall_progress = int((idx / total) * 100)
                draw_progress_bar(f"Downloading {game_name} ({idx+1}/{total})", overall_progress)
                
                # Build download URL based on format
                if sys_data.get('use_api', False) and 'download_url' in sys_data:
                    # Switch API format - encode game name for URL
                    encoded_filename = quote(filename)
                    url = f"{sys_data['download_url']}{encoded_filename}"
                elif 'download_url' in sys_data:
                    # Old format
                    url = f"{sys_data['download_url']}/{filename}"
                elif 'url' in sys_data:
                    # New format - construct URL by joining base URL with filename
                    url = urljoin(sys_data['url'], filename)
                try:
                    r = requests.get(url, stream=True, timeout=10)
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', 0))
                    downloaded = 0
                    start_time = pygame.time.get_ticks()
                    last_update = start_time
                    last_downloaded = 0
                    
                    file_path = os.path.join(WORK_DIR, filename)
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(1024):
                            # Check for cancel button
                            for event in pygame.event.get():
                                if event.type == pygame.JOYBUTTONDOWN and event.button == get_controller_button("back"):
                                    cancelled = True
                                    break
                            if cancelled:
                                break
                            
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Calculate speed every 500ms
                                current_time = pygame.time.get_ticks()
                                if current_time - last_update >= 500:
                                    speed = (downloaded - last_downloaded) * 2  # *2 because we update every 500ms
                                    last_downloaded = downloaded
                                    last_update = current_time
                                    
                                    # Calculate file progress
                                    file_progress = int((downloaded / total_size) * 100) if total_size > 0 else 0
                                    # Calculate overall progress including current file
                                    current_progress = int(((idx + (file_progress / 100)) / total) * 100)
                                    draw_progress_bar(f"Downloading {filename} ({idx+1}/{total})", 
                                                    current_progress, downloaded, total_size, speed)

                    if cancelled:
                        # Clean up the current file if download was cancelled
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        break

                    # Handle ZIP extraction
                    if filename.endswith(".zip") and sys_data.get('should_unzip', False):
                        draw_progress_bar(f"Extracting {filename}...", 0)
                        with ZipFile(file_path, 'r') as zip_ref:
                            # Get total number of files to extract
                            total_files = len(zip_ref.namelist())
                            extracted_files = 0
                            
                            # Extract files with progress tracking
                            for file_info in zip_ref.infolist():
                                zip_ref.extract(file_info, WORK_DIR)
                                extracted_files += 1
                                
                                # Update progress every few files or for large files
                                if extracted_files % 10 == 0 or file_info.file_size > 1024*1024:  # Every 10 files or files > 1MB
                                    progress = int((extracted_files / total_files) * 100)
                                    draw_progress_bar(f"Extracting {filename}... ({extracted_files}/{total_files})", progress)
                                
                                # Check for cancel button
                                for event in pygame.event.get():
                                    if event.type == pygame.JOYBUTTONDOWN and event.button == get_controller_button("back"):
                                        cancelled = True
                                        break
                                if cancelled:
                                    break
                            
                            # Show final extraction progress
                            if not cancelled:
                                draw_progress_bar(f"Extracting {filename}... Complete", 100)
                                pygame.time.wait(500)  # Brief pause to show completion
                        
                        if not cancelled:
                            os.remove(file_path)
                    
                    # Handle NSZ decompression for Nintendo Switch games
                    elif filename.endswith(".nsz"):
                        draw_progress_bar(f"Checking NSZ support for {filename}...", 0)
                        try:
                            import subprocess
                            import shutil
                            
                            # Check if Nintendo Switch keys are configured and exist
                            keys_path = settings.get("switch_keys_path", "")
                            keys_available = False
                            
                            if keys_path:
                                if os.path.isfile(keys_path) and keys_path.lower().endswith('.keys'):
                                    # Direct file path
                                    keys_available = True
                                    actual_keys_path = keys_path
                                elif os.path.isdir(keys_path):
                                    # Directory path, look for prod.keys
                                    prod_keys_path = os.path.join(keys_path, "prod.keys")
                                    if os.path.exists(prod_keys_path):
                                        keys_available = True
                                        actual_keys_path = prod_keys_path
                            
                            # Also check default locations if not configured
                            if not keys_available:
                                default_keys_paths = [
                                    os.path.expanduser("~/.switch/prod.keys"),
                                    os.path.join(WORK_DIR, "keys.txt"),
                                    os.path.join(WORK_DIR, "prod.keys")
                                ]
                                for default_path in default_keys_paths:
                                    if os.path.exists(default_path):
                                        keys_available = True
                                        actual_keys_path = default_path
                                        break
                            
                            if not keys_available:
                                draw_progress_bar(f"NSZ decompression skipped - Nintendo Switch keys not found", 0)
                                log_error(f"NSZ decompression skipped for {filename}: Nintendo Switch keys not found. Configure path in Settings > Nintendo Switch Keys")
                                pygame.time.wait(2000)
                            else:
                                draw_progress_bar(f"Decompressing {filename}...", 0)
                                
                                # Set up environment for NSZ with keys
                                env = os.environ.copy()
                                
                                # Copy keys to expected location if needed
                                switch_dir = os.path.expanduser("~/.switch")
                                if not os.path.exists(switch_dir):
                                    os.makedirs(switch_dir, exist_ok=True)
                                
                                expected_keys = os.path.join(switch_dir, "prod.keys")
                                if not os.path.exists(expected_keys) and actual_keys_path != expected_keys:
                                    shutil.copy2(actual_keys_path, expected_keys)
                                
                                # Use nsz command-line tool to decompress with timeout
                                result = subprocess.run([
                                    'nsz', '-D', file_path
                                ], capture_output=True, text=True, cwd=WORK_DIR, timeout=300, env=env)
                                
                                if result.returncode == 0:
                                    draw_progress_bar(f"Decompressing {filename}... Complete", 100)
                                    pygame.time.wait(500)
                                    
                                    # Find and move all NSP files in work directory
                                    for file in os.listdir(WORK_DIR):
                                        if file.endswith('.nsp'):
                                            src_path = os.path.join(WORK_DIR, file)
                                            dst_path = os.path.join(roms_folder, file)
                                            os.rename(src_path, dst_path)
                                            print(f"Moved decompressed NSP: {file}")
                                    
                                    # Remove original NSZ file after successful decompression
                                    if os.path.exists(file_path):
                                        os.remove(file_path)
                                        
                                    # Skip the normal file moving process for this file since we handled it here
                                    continue
                                else:
                                    log_error(f"NSZ decompression failed for {filename}: {result.stderr}")
                                    draw_progress_bar(f"NSZ decompression failed for {filename}", 0)
                                    pygame.time.wait(2000)
                                
                        except subprocess.TimeoutExpired:
                            log_error(f"NSZ decompression timed out for {filename}")
                            draw_progress_bar(f"NSZ decompression timed out for {filename}", 0)
                            pygame.time.wait(2000)
                        except Exception as e:
                            log_error(f"NSZ decompression failed for {filename}: {e}")
                            draw_progress_bar(f"NSZ decompression failed for {filename}", 0)
                            pygame.time.wait(2000)

                    # Move files to ROMS
                    draw_progress_bar(f"Moving files to ROMS folder...", 0)
                    for f in os.listdir(WORK_DIR):
                        if any(f.endswith(ext) for ext in formats):
                            os.rename(os.path.join(WORK_DIR, f), os.path.join(roms_folder, f))

                    # Clean work dir
                    for f in os.listdir(WORK_DIR):
                        os.remove(os.path.join(WORK_DIR, f))

                except Exception as e:
                    log_error(f"Failed to download {filename}", type(e).__name__, traceback.format_exc())
                
            if cancelled:
                draw_loading_message("Download cancelled")
                pygame.time.wait(1000)  # Show the message for 1 second
        except Exception as e:
            log_error(f"Error in download_files for system {system}", type(e).__name__, traceback.format_exc())

    def list_files(system, page=0):
        try:
            draw_loading_message(f"Loading games for {data[system]['name']}...")
            sys_data = data[system]
            formats = sys_data.get('file_format', [])
            
            # Check if this uses API format (like Switch)
            if sys_data.get('use_api', False) and 'api_url' in sys_data:
                # API format - like Switch with pagination
                api_url = sys_data['api_url']
                if 'limit=' in api_url:
                    # Add page offset to API URL
                    base_url = api_url.split('?')[0]
                    params = api_url.split('?')[1]
                    limit = int([p.split('=')[1] for p in params.split('&') if p.startswith('limit=')][0])
                    offset = page * limit
                    paginated_url = f"{base_url}?{params}&offset={offset}"
                else:
                    paginated_url = api_url
                
                r = requests.get(paginated_url, timeout=10)
                response = r.json()
                
                files = []
                for game_id, game_data in response.items():
                    game_name = game_data.get('name', {}).get('en', game_data.get('name', {}).get('default', game_id))
                    files.append({
                        'name': game_name,
                        'title_id': game_id,
                        'size': game_data.get('size', 0),
                        'banner_url': game_data.get('banner_url'),
                        'icon_url': game_data.get('icon_url'),
                        'screenshots_urls': game_data.get('screenshots_urls', [])
                    })
                
                # Apply USA filter if enabled and system supports it
                if settings.get("usa_only", False) and sys_data.get('should_filter_usa', True):
                    usa_regex = sys_data.get('usa_regex', '(USA)')
                    files = [f for f in files if re.search(usa_regex, f['name'])]
                
                return sorted(files, key=lambda x: x['name'])
            
            # Check if this is the old JSON API format
            elif 'list_url' in sys_data:
                # Old format - JSON API
                list_url = sys_data['list_url']
                array_path = sys_data.get('list_json_file_location', "files")
                file_id = sys_data.get('list_item_id', "name")
                r = requests.get(list_url, timeout=10)
                response = r.json()
                
                if isinstance(response, dict) and "files" in response:
                    files = response[array_path]
                    if isinstance(files, list):
                        filtered_files = [f[file_id] for f in files if any(f[file_id].lower().endswith(ext.lower()) for ext in formats)]
                        # Apply USA filter if enabled and system supports it
                        if settings.get("usa_only", False) and sys_data.get('should_filter_usa', True):
                            usa_regex = sys_data.get('usa_regex', '(USA)')
                            filtered_files = [f for f in filtered_files if re.search(usa_regex, f)]
                        return filtered_files
            
            elif 'url' in sys_data:
                # New format - HTML directory listing
                url = sys_data['url']
                regex_pattern = sys_data.get('regex', '<a href="([^"]+)"[^>]*>([^<]+)</a>')
                
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                html_content = r.text
                
                # Extract file links using regex
                if 'regex' in sys_data:
                    # Use the provided named capture group regex
                    matches = re.finditer(regex_pattern, html_content)
                    files = []
                    for match in matches:
                        try:
                            # Try to get the filename from named groups
                            if 'text' in match.groupdict():
                                filename = unquote(match.group('text'))
                            elif 'href' in match.groupdict():
                                filename = unquote(match.group('href'))
                            else:
                                # Fallback to first group
                                filename = unquote(match.group(1))
                            
                            # Filter by file format
                            if any(filename.lower().endswith(ext.lower()) for ext in formats):
                                files.append(filename)
                        except:
                            continue
                else:
                    # Simple regex for href links
                    matches = re.findall(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', html_content)
                    files = []
                    for href, text in matches:
                        filename = unquote(text or href)
                        if any(filename.lower().endswith(ext.lower()) for ext in formats):
                            files.append(filename)
                
                # Apply USA filter if enabled and system supports it
                if settings.get("usa_only", False) and sys_data.get('should_filter_usa', True):
                    usa_regex = sys_data.get('usa_regex', '(USA)')
                    files = [f for f in files if re.search(usa_regex, f)]
                
                return sorted(files)
            
            return []
        except Exception as e:
            log_error(f"Failed to fetch list for system {system}", type(e).__name__, traceback.format_exc())
            return []

    def load_folder_contents(path):
        """Load folder contents for browser"""
        global folder_browser_items, folder_browser_highlighted, folder_browser_scroll_offset
        
        try:
            # Normalize path
            path = os.path.abspath(path)
            items = []
            
            # Add parent directory option unless we're at root
            if path != "/" and path != os.path.dirname(path):
                items.append({"name": "..", "type": "parent", "path": os.path.dirname(path)})
            
            # Add "Create New Folder" option
            items.append({"name": "[CREATE NEW FOLDER]", "type": "create_folder", "path": path})
            
            # Get directory contents
            if os.path.exists(path) and os.path.isdir(path):
                try:
                    entries = os.listdir(path)
                    entries.sort()
                    
                    # Add directories first
                    for entry in entries:
                        entry_path = os.path.join(path, entry)
                        if os.path.isdir(entry_path) and not entry.startswith('.'):
                            items.append({"name": entry, "type": "folder", "path": entry_path})
                    
                    # Add .keys files if we're selecting Nintendo Switch keys
                    if selected_system_to_add and selected_system_to_add.get("type") == "switch_keys":
                        for entry in entries:
                            entry_path = os.path.join(path, entry)
                            if os.path.isfile(entry_path) and entry.lower().endswith('.keys'):
                                items.append({"name": entry, "type": "keys_file", "path": entry_path})
                    
                except PermissionError:
                    items.append({"name": "Permission denied", "type": "error", "path": path})
            else:
                items.append({"name": "Path not found", "type": "error", "path": path})
            
            folder_browser_items = items
            folder_browser_highlighted = 0
            folder_browser_scroll_offset = 0
            
        except Exception as e:
            log_error(f"Failed to load folder contents for {path}", type(e).__name__, traceback.format_exc())
            folder_browser_items = [{"name": "Error loading folder", "type": "error", "path": path}]
            folder_browser_highlighted = 0
            folder_browser_scroll_offset = 0

    def load_available_systems():
        """Load available systems from list_systems entries"""
        global available_systems, add_systems_highlighted
        
        try:
            # Find entries with list_systems: true
            list_system_entries = [d for d in data if d.get('list_systems', False)]
            if not list_system_entries:
                available_systems = []
                return
            
            # Use the first list_systems entry (assuming there's only one)
            list_entry = list_system_entries[0]
            url = list_entry['url']
            regex_pattern = list_entry.get('regex', '')
            
            if not regex_pattern:
                log_error("No regex pattern found in list_systems entry")
                available_systems = []
                return
            
            # Fetch the HTML content
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            
            # Extract systems using regex
            systems = []
            matches = re.finditer(regex_pattern, html_content)
            
            for match in matches:
                try:
                    # Extract href, title, and other data from named groups
                    href = match.group('href') if 'href' in match.groupdict() else ''
                    title = match.group('title') if 'title' in match.groupdict() else ''
                    text = match.group('text') if 'text' in match.groupdict() else ''
                    size = match.group('size') if 'size' in match.groupdict() else ''
                    
                    # Use title as name, fallback to text
                    name = title if title else text
                    if name and href:
                        # Basic cleanup - just remove trailing slash and whitespace
                        name = name.strip().rstrip('/')
                        
                        # Skip if name is empty after cleaning or is navigation element
                        if not name or name in ['..', '.', 'Parent Directory']:
                            continue
                        
                        # Construct full URL
                        full_url = urljoin(url, href)
                        systems.append({
                            'name': name,
                            'href': href,
                            'url': full_url,
                            'size': size.strip() if size else ''
                        })
                except Exception as e:
                    log_error(f"Error processing regex match: {match.groups()}", type(e).__name__, traceback.format_exc())
                    continue
            
            available_systems = systems
            add_systems_highlighted = 0
            
        except Exception as e:
            log_error("Failed to load available systems", type(e).__name__, traceback.format_exc())
            available_systems = []

    def load_added_systems():
        """Load added systems from added_systems.json file"""
        try:
            if os.path.exists(ADDED_SYSTEMS_FILE):
                with open(ADDED_SYSTEMS_FILE, 'r') as f:
                    return json.load(f)
            else:
                # Create empty file
                save_added_systems([])
                return []
        except Exception as e:
            log_error("Failed to load added systems", type(e).__name__, traceback.format_exc())
            return []

    def save_added_systems(added_systems_list):
        """Save added systems to added_systems.json file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(ADDED_SYSTEMS_FILE), exist_ok=True)
            
            with open(ADDED_SYSTEMS_FILE, 'w') as f:
                json.dump(added_systems_list, f, indent=2)
        except Exception as e:
            log_error("Failed to save added systems", type(e).__name__, traceback.format_exc())

    def add_system_to_added_systems(system_name, rom_folder, system_url):
        """Add a new system to the added_systems.json file"""
        try:
            added_systems = load_added_systems()
            
            # Check if system already exists
            for system in added_systems:
                if system.get('name') == system_name:
                    log_error(f"System {system_name} already exists in added systems")
                    return False
            
            # Add new system
            new_system = {
                'name': system_name,
                'roms_folder': rom_folder,
                'url': system_url,
                'file_format': ['.zip', '.7z', '.rar'],  # Default formats
                'should_unzip': True,
                'should_filter_usa': False
            }
            
            added_systems.append(new_system)
            save_added_systems(added_systems)
            
            # Reload the main data to include the new system
            global data
            data = load_main_systems_data()
            
            return True
            
        except Exception as e:
            log_error(f"Failed to add system {system_name}", type(e).__name__, traceback.format_exc())
            return False

    def fix_added_systems_roms_folder():
        """Fix the roms_folder in added_systems.json if it's incorrect"""
        try:
            added_systems = load_added_systems()
            if not added_systems:
                return
            
            fixed = False
            for system in added_systems:
                # If roms_folder is "psx", it means the user selected a folder inside psx
                # We should use the system name as the folder instead
                if system.get('roms_folder') == 'psx':
                    system['roms_folder'] = system.get('name', 'unknown').lower().replace(' ', '_').replace('-', '_')
                    fixed = True
            
            if fixed:
                save_added_systems(added_systems)
                print("Fixed roms_folder in added_systems.json")
                
        except Exception as e:
            log_error("Failed to fix added systems roms_folder", type(e).__name__, traceback.format_exc())

    def load_main_systems_data():
        """Load main systems data including added systems"""
        try:
            # Load main systems
            with open(JSON_FILE) as f:
                main_data = json.load(f)
            
            # Load added systems
            added_systems = load_added_systems()
            
            # Combine main data with added systems
            combined_data = main_data + added_systems
            
            # Debug: Log the merging process
            print(f"Loaded {len(main_data)} main systems")
            print(f"Loaded {len(added_systems)} added systems")
            print(f"Total systems: {len(combined_data)}")
            
            # Debug: Show system names
            if added_systems:
                print("Added systems:")
                for system in added_systems:
                    print(f"  - {system.get('name', 'Unknown')}")
            
            return combined_data
        except Exception as e:
            log_error("Failed to load main systems data", type(e).__name__, traceback.format_exc())
            return []

    def find_next_letter_index(items, current_index, direction):
        """Find the next item that starts with a different letter"""
        if not items:
            return current_index
        
        # Get display name for current item
        current_item = items[current_index]
        if isinstance(current_item, dict):
            current_name = current_item.get('name', '')
        else:
            current_name = current_item
        
        if not current_name:
            return current_index
        
        current_letter = current_name[0].upper()
        if direction > 0:  # Moving right/forward
            for i in range(current_index + 1, len(items)):
                item = items[i]
                item_name = item.get('name', '') if isinstance(item, dict) else item
                if item_name and item_name[0].upper() > current_letter:
                    return i
        else:  # Moving left/backward
            for i in range(current_index - 1, -1, -1):
                item = items[i]
                item_name = item.get('name', '') if isinstance(item, dict) else item
                if item_name and item_name[0].upper() < current_letter:
                    return i
        return current_index

    # Load settings after all functions are defined
    settings = load_settings()
    
    # Load or create controller mapping
    mapping_exists = load_controller_mapping()
    
    # Debug: Print loaded mapping
    print(f"DEBUG: Controller mapping loaded: {controller_mapping}")
    print(f"DEBUG: Mapping exists: {mapping_exists}, Needs mapping: {needs_controller_mapping()}")
    
    # If no controller mapping exists or is incomplete, collect it on first run
    if not mapping_exists or needs_controller_mapping():
        print("Controller mapping needed - will be collected on startup")
        show_controller_mapping = True
    else:
        print("Controller mapping is complete")
        show_controller_mapping = False

    # Update data to include added systems
    try:
        # Fix any issues with existing added systems
        fix_added_systems_roms_folder()
        data = load_main_systems_data()
    except Exception as e:
        log_error("Failed to load main systems data", type(e).__name__, traceback.format_exc())
        # Keep original data if loading fails

    # Set up directories from settings
    WORK_DIR = settings["work_dir"]
    ROMS_DIR = settings["roms_dir"]
    
    # Create directories with error handling
    try:
        os.makedirs(WORK_DIR, exist_ok=True)
    except (OSError, PermissionError) as e:
        log_error(f"Could not create work directory {WORK_DIR}", type(e).__name__, traceback.format_exc())
        print(f"Warning: Could not create work directory {WORK_DIR}. Downloads may fail.")
    
    try:
        os.makedirs(ROMS_DIR, exist_ok=True)
    except (OSError, PermissionError) as e:
        log_error(f"Could not create ROMs directory {ROMS_DIR}", type(e).__name__, traceback.format_exc())
        print(f"Warning: Could not create ROMs directory {ROMS_DIR}. You may need to create it manually or select a different directory in settings.")

    # Debug controller variables
    current_pressed_button = ""
    last_button_time = 0
    BUTTON_DISPLAY_TIME = 1000  # milliseconds
    
    # Controller-specific button mappings (only used buttons)
    CONTROLLER_MAPPINGS = {
        "generic": {
            2: "Button 2", 3: "Button 3", 4: "Button 4", 6: "Button 6", 7: "Button 7", 10: "Button 10"
        },
        "xbox": {
            0: "A", 1: "B", 3: "Y", 6: "Start", 9: "LB", 10: "RB"
        },
        "odin": {
            1: "A", 0: "B", 2: "Y", 6: "Start", 9: "LB", 10: "RB",
            11: "D-Up", 12: "D-Down", 13: "D-Left", 14: "D-Right"
        },
        "playstation": {
            0: "Cross", 1: "Circle", 3: "Triangle", 9: "L1", 10: "R1", 6: "Options"
        },
        "nintendo": {
            0: "B", 1: "A", 2: "Y", 4: "L", 5: "R", 9: "Plus"
        },
        "rg35xx": {
            3: "Button A", 4: "Button B", 6: "Button X", 7: "Button L", 8: "Button R", 9: "SELECT"
        },
    }
    
    # Controller-specific navigation mappings
    CONTROLLER_NAVIGATION = {
        "generic": {
            "select": 4, "back": 3, "start": 10, "detail": 2, "left_shoulder": 6, "right_shoulder": 7, "create_folder": 6
        },
        "xbox": {
            "select": 0, "back": 1, "start": 6, "detail": 3, "left_shoulder": 9, "right_shoulder": 10, "create_folder": 9  # A, B, Start, Y, LB, RB, LB
        },
        "odin": {
            "select": 0, "back": 1, "start": 6, "detail": 3, "left_shoulder": 9, "right_shoulder": 10, "create_folder": 9  # A, B, Start, Y, LB, RB, LB
        },
        "playstation": {
            "select": 0, "back": 1, "start": 6, "detail": 3, "left_shoulder": 9, "right_shoulder": 10, "create_folder": 9  # Cross, Circle, Options, Triangle, L1, R1, L1
        },
        "nintendo": {
            "select": 1, "back": 0, "start": 9, "detail": 2, "left_shoulder": 4, "right_shoulder": 5, "create_folder": 4  # A, B, Plus, Y, L, R, L
        },
        "rg35xx": {
            "select": 3, "back": 4, "start": 9, "detail": 6, "left_shoulder": 7, "right_shoulder": 8, "create_folder": 7
        }
    }
    
    def get_controller_button(action):
        """Get the button number for a specific action based on dynamic controller mapping"""
        if action in controller_mapping:
            button_info = controller_mapping[action]
            print(f"get_controller_button({action}) - button_info: {button_info}")
            return button_info
        else:
            print(f"get_controller_button({action}) - not found in mapping")
            return None
    
    def get_button_name(action):
        """Get the display name for a button action based on dynamic controller mapping"""
        button_info = get_controller_button(action)
        if button_info is None:
            return action.upper()
        
        # Handle different input types (both tuples and lists from JSON)
        if ((isinstance(button_info, tuple) or isinstance(button_info, list)) and 
            len(button_info) >= 3 and button_info[0] == "hat"):
            # D-pad input
            _, hat_x, hat_y = button_info[0:3]
            if hat_y == 1:
                return "D-pad UP"
            elif hat_y == -1:
                return "D-pad DOWN"
            elif hat_x == -1:
                return "D-pad LEFT"
            elif hat_x == 1:
                return "D-pad RIGHT"
            else:
                return "D-pad"
        else:
            # Regular button
            return f"Button {button_info}"

    def input_matches_action(event, action):
        """Check if the pygame event matches the mapped action"""
        button_info = get_controller_button(action)
        if button_info is None:
            return False
            
        if event.type == pygame.JOYBUTTONDOWN:
            # Check regular button press
            return isinstance(button_info, int) and event.button == button_info
        elif event.type == pygame.JOYHATMOTION:
            # Check D-pad/hat input (handle both tuples and lists from JSON)
            if ((isinstance(button_info, tuple) or isinstance(button_info, list)) and 
                len(button_info) >= 3 and button_info[0] == "hat"):
                _, expected_x, expected_y = button_info[0:3]
                return event.value == (expected_x, expected_y)
        
        return False

    # Game details modal state
    show_game_details = False
    current_game_detail = None
    
    # Folder browser modal state
    show_folder_browser = False
    folder_browser_current_path = "/"
    folder_browser_items = []
    folder_browser_highlighted = 0
    folder_browser_scroll_offset = 0
    
    # System name input modal state
    show_system_input = False
    system_input_text = ""
    selected_system_to_add = None
    
    # Folder name input modal state
    show_folder_name_input = False
    folder_name_input_text = ""
    folder_name_cursor_position = 0
    folder_name_char_index = 0  # Current character being selected (0-35 for A-Z, 0-9)
    
    # Main loop
    running = True
    button_delay = 0
    last_dpad_state = (0, 0)  # Track last D-pad state to detect actual changes
    last_dpad_time = 0  # Track when last D-pad navigation occurred
    DPAD_DEBOUNCE_MS = 100  # Minimum time between D-pad navigation actions

    def draw_folder_name_input_modal():
        """Draw the folder name input modal overlay"""
        # Get actual screen dimensions
        screen_width, screen_height = screen.get_size()
        
        # Semi-transparent background overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Modal sizing
        modal_width = min(int(screen_width * 0.8), 500)
        modal_height = min(int(screen_height * 0.6), 400)
        modal_x = (screen_width - modal_width) // 2
        modal_y = (screen_height - modal_height) // 2
        
        modal_rect = pygame.Rect(modal_x, modal_y, modal_width, modal_height)
        pygame.draw.rect(screen, WHITE, modal_rect)
        pygame.draw.rect(screen, BLACK, modal_rect, 3)
        
        # Title
        title_surf = font.render("Enter Folder Name", True, BLACK)
        title_x = modal_x + 20
        title_y = modal_y + 20
        screen.blit(title_surf, (title_x, title_y))
        
        # Current folder name display
        name_y = title_y + 50
        name_text = folder_name_input_text if folder_name_input_text else "Enter folder name..."
        name_surf = font.render(name_text, True, BLACK)
        screen.blit(name_surf, (title_x, name_y))
        
        # Character selection area
        char_y = name_y + 60
        char_title_surf = font.render("Select Character:", True, BLACK)
        screen.blit(char_title_surf, (title_x, char_y))
        
        # Character grid (A-Z, 0-9)
        chars = list("abcdefghijklmnopqrstuvwxyz0123456789")
        chars_per_row = 13
        char_size = 30
        char_spacing = 5
        
        char_start_x = title_x
        char_start_y = char_y + 40
        
        for i, char in enumerate(chars):
            row = i // chars_per_row
            col = i % chars_per_row
            
            char_x = char_start_x + col * (char_size + char_spacing)
            char_y_pos = char_start_y + row * (char_size + char_spacing)
            
            # Highlight current character
            if i == folder_name_char_index:
                char_rect = pygame.Rect(char_x - 2, char_y_pos - 2, char_size + 4, char_size + 4)
                pygame.draw.rect(screen, GREEN, char_rect)
            
            char_rect = pygame.Rect(char_x, char_y_pos, char_size, char_size)
            pygame.draw.rect(screen, WHITE, char_rect)
            pygame.draw.rect(screen, BLACK, char_rect, 1)
            
            char_surf = font.render(char, True, BLACK)
            char_text_x = char_x + (char_size - char_surf.get_width()) // 2
            char_text_y = char_y_pos + (char_size - char_surf.get_height()) // 2
            screen.blit(char_surf, (char_text_x, char_text_y))
        
        # Instructions
        instructions = [
            "Use D-pad to select character",
            "Press Select to add character",
            "Press Back to delete character",
            "Press Start to finish",
            "Press any other button to finish"
        ]
        
        inst_y = char_start_y + 120
        for instruction in instructions:
            inst_surf = font.render(instruction, True, GRAY)
            screen.blit(inst_surf, (title_x, inst_y))
            inst_y += 20

    def create_folder_in_browser():
        """Create a new folder in the current folder browser location"""
        global show_folder_name_input, folder_name_input_text, folder_name_cursor_position, folder_name_char_index
        
        # Open the folder name input modal
        show_folder_name_input = True
        folder_name_input_text = ""
        folder_name_cursor_position = 0
        folder_name_char_index = 0

    def restart_app():
        """Restart the application"""
        try:
            print("Restarting application...")
            pygame.quit()
            # Use os.execv to restart the script
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e:
            log_error("Failed to restart application", type(e).__name__, traceback.format_exc())
            # Fallback: just exit and let user restart manually
            sys.exit(0)

    def create_folder_with_name():
        """Create the folder with the custom name entered by user"""
        global show_folder_name_input, folder_browser_highlighted
        
        try:
            if not folder_name_input_text.strip():
                # Use default name if no name entered
                if selected_system_to_add is not None:
                    default_name = selected_system_to_add['name'].lower().replace(" ", "_").replace("-", "_")
                else:
                    default_name = "new_folder"
                folder_name = default_name
            else:
                folder_name = folder_name_input_text.strip()
            
            # Create the folder
            new_folder_path = os.path.join(folder_browser_current_path, folder_name)
            os.makedirs(new_folder_path, exist_ok=True)
            
            # Reload the folder contents to show the new folder
            load_folder_contents(folder_browser_current_path)
            
            # Highlight the newly created folder
            for i, item in enumerate(folder_browser_items):
                if item["type"] == "folder" and item["name"] == folder_name:
                    folder_browser_highlighted = i
                    break
            
            print(f"Created folder: {new_folder_path}")
            
            # Close the input modal
            show_folder_name_input = False
            
        except Exception as e:
            log_error(f"Failed to create folder in {folder_browser_current_path}", type(e).__name__, traceback.format_exc())
            show_folder_name_input = False

    while running:
        try:
            clock.tick(FPS)
            current_time = pygame.time.get_ticks()
            
            # Check if we need to collect controller mapping first
            if show_controller_mapping:
                if collect_controller_mapping():
                    show_controller_mapping = False
                    print("Controller mapping completed successfully")
                else:
                    print("Controller mapping cancelled or failed")
                    running = False
                    break
            
            # Update image cache from background threads
            update_image_cache()
                
            if mode == "systems":
                # Get visible systems and add Settings/Add Systems options
                visible_systems = get_visible_systems()
                regular_systems = [d['name'] for d in visible_systems]
                systems_with_options = regular_systems + ["Add Systems", "Settings"]
                draw_menu("Select a System", systems_with_options, set())
            elif mode == "games":
                if game_list:  # Only draw if we have games
                    if settings["view_type"] == "grid":
                        draw_grid_view("Select Games", game_list, selected_games)
                    else:
                        draw_menu("Select Games", game_list, selected_games)
                else:
                    draw_loading_message("No games found for this system")
            elif mode == "settings":
                draw_settings_menu()
            elif mode == "add_systems":
                draw_add_systems_menu()
            elif mode == "systems_settings":
                draw_systems_settings_menu()
            elif mode == "system_settings":
                draw_system_settings_menu()
            
            # Draw modals if they should be shown
            modal_drawn = False
            if show_folder_name_input:
                draw_folder_name_input_modal()
                modal_drawn = True
            elif show_game_details and current_game_detail is not None:
                draw_game_details_modal(current_game_detail)
                modal_drawn = True
            elif show_folder_browser:
                draw_folder_browser_modal()
                modal_drawn = True
            
            # Flip display once at the end
            if modal_drawn or not (show_game_details or show_folder_browser or show_folder_name_input):
                pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    # Debug controller - capture keyboard presses
                    if settings.get("debug_controller", False):
                        key_names = {
                            pygame.K_UP: "Up", pygame.K_DOWN: "Down", pygame.K_LEFT: "Left", pygame.K_RIGHT: "Right",
                            pygame.K_RETURN: "Enter", pygame.K_ESCAPE: "Escape", pygame.K_SPACE: "Space", pygame.K_y: "Y"
                        }
                        key_name = key_names.get(event.key, f"Key-{event.key}")
                        current_pressed_button = f"KEYBOARD: {key_name}"
                        last_button_time = pygame.time.get_ticks()
                    
                    # Keyboard controls (same logic as joystick)
                    if event.key == pygame.K_RETURN:  # Enter = Select (Button 4)
                        if show_folder_browser:
                            # Navigate into folder or go back
                            if folder_browser_items and folder_browser_highlighted < len(folder_browser_items):
                                selected_item = folder_browser_items[folder_browser_highlighted]
                                print(f"Selected item: {selected_item['name']} (type: {selected_item['type']})")
                                if selected_item["type"] == "create_folder":
                                    # Create new folder
                                    print("Creating new folder...")
                                    create_folder_in_browser()
                                elif selected_item["type"] in ["folder", "parent"]:
                                    folder_browser_current_path = selected_item["path"]
                                    print(f"Navigating to folder: {folder_browser_current_path}")
                                    load_folder_contents(folder_browser_current_path)
                        elif mode == "systems":
                            # Use helper function for consistent filtering
                            visible_systems = get_visible_systems()
                            systems_count = len(visible_systems)
                            if highlighted == systems_count:  # Add Systems option
                                mode = "add_systems"
                                highlighted = 0
                                add_systems_highlighted = 0
                                # Load available systems in background
                                load_available_systems()
                            elif highlighted == systems_count + 1:  # Settings option
                                mode = "settings"
                                highlighted = 0
                                settings_scroll_offset = 0
                            else:
                                # Map visible system index to original data index
                                if highlighted < len(visible_systems):
                                    selected_visible_system = visible_systems[highlighted]
                                    selected_system = get_system_index_by_name(selected_visible_system['name'])
                                    current_page = 0
                                    game_list = list_files(selected_system, current_page)
                                    selected_games = set()
                                mode = "games"
                                highlighted = 0
                        elif mode == "games":
                            if highlighted in selected_games:
                                selected_games.remove(highlighted)
                            else:
                                selected_games.add(highlighted)
                        elif mode == "settings":
                            # Toggle settings or reset cache
                            if highlighted == 0:  # Enable Box-art Display
                                settings["enable_boxart"] = not settings["enable_boxart"]
                                save_settings(settings)
                            elif highlighted == 1:  # Enable Image Cache
                                settings["cache_enabled"] = not settings["cache_enabled"]
                                if not settings["cache_enabled"]:
                                    reset_image_cache()
                                save_settings(settings)
                            elif highlighted == 2:  # Reset Image Cache
                                reset_image_cache()
                            elif highlighted == 3:  # Update from GitHub
                                update_from_github()
                            elif highlighted == 4:  # View Type
                                settings["view_type"] = "grid" if settings["view_type"] == "list" else "list"
                                save_settings(settings)
                            elif highlighted == 5:  # USA Games Only
                                settings["usa_only"] = not settings["usa_only"]
                                save_settings(settings)
                            elif highlighted == 6:  # Debug Controller
                                settings["debug_controller"] = not settings["debug_controller"]
                                save_settings(settings)
                            elif highlighted == 7:  # Work Directory
                                # Open folder browser for work directory selection
                                show_folder_browser = True
                                # Use current work_dir or fallback to a sensible default
                                current_work = settings.get("work_dir", "")
                                if not current_work or not os.path.exists(os.path.dirname(current_work)):
                                    # Use a fallback based on environment
                                    if os.path.exists("/userdata") and os.access("/userdata", os.R_OK):
                                        folder_browser_current_path = "/userdata"
                                    else:
                                        folder_browser_current_path = os.path.expanduser("~")  # Home directory
                                else:
                                    folder_browser_current_path = current_work
                                load_folder_contents(folder_browser_current_path)
                                # Set a flag to indicate we're selecting work directory
                                selected_system_to_add = {"name": "Work Directory", "type": "work_dir"}
                            elif highlighted == 8:  # ROMs Directory
                                # Open folder browser
                                show_folder_browser = True
                                # Use current roms_dir or fallback to a sensible default
                                current_roms = settings.get("roms_dir", "")
                                if not current_roms or not os.path.exists(os.path.dirname(current_roms)):
                                    # Use a fallback based on environment
                                    if os.path.exists("/userdata") and os.access("/userdata", os.R_OK):
                                        folder_browser_current_path = "/userdata/roms"
                                    else:
                                        folder_browser_current_path = os.path.expanduser("~")  # Home directory
                                else:
                                    folder_browser_current_path = current_roms
                                load_folder_contents(folder_browser_current_path)
                            elif highlighted == 9:  # Nintendo Switch Keys
                                # Open folder browser for .keys files
                                show_folder_browser = True
                                # Use current keys path or default to home directory
                                current_keys = settings.get("switch_keys_path", "")
                                if current_keys and os.path.exists(os.path.dirname(current_keys)):
                                    folder_browser_current_path = os.path.dirname(current_keys)
                                else:
                                    # Default to ~/.switch directory or home
                                    switch_dir = os.path.expanduser("~/.switch")
                                    if os.path.exists(switch_dir):
                                        folder_browser_current_path = switch_dir
                                    else:
                                        folder_browser_current_path = os.path.expanduser("~")
                                load_folder_contents(folder_browser_current_path)
                                # Set a flag to indicate we're selecting Nintendo Switch keys
                                selected_system_to_add = {"name": "Nintendo Switch Keys", "type": "switch_keys"}
                            elif highlighted == 10:  # Remap Controller
                                # Trigger controller remapping
                                show_controller_mapping = True
                            elif highlighted == 11:  # Systems Settings
                                mode = "systems_settings"
                                systems_settings_highlighted = 0
                                highlighted = 0
                        elif mode == "add_systems":
                            # Handle add systems selection
                            if available_systems and add_systems_highlighted < len(available_systems):
                                selected_system_to_add = available_systems[add_systems_highlighted]
                                # Open folder browser to select ROM folder
                                show_folder_browser = True
                                # Start in ROMs directory
                                folder_browser_current_path = settings.get("roms_dir", "/userdata/roms")
                                load_folder_contents(folder_browser_current_path)
                        elif mode == "systems_settings":
                            # Handle systems settings navigation
                            configurable_systems = [d for d in data if not d.get('list_systems', False) and d.get('name') != 'Other Systems']
                            if systems_settings_highlighted < len(configurable_systems):
                                selected_system_for_settings = configurable_systems[systems_settings_highlighted]
                                mode = "system_settings"
                                system_settings_highlighted = 0
                                highlighted = 0
                        elif mode == "system_settings":
                            # Handle individual system settings
                            if system_settings_highlighted == 0:  # Hide from main menu
                                system_name = selected_system_for_settings['name']
                                if "system_settings" not in settings:
                                    settings["system_settings"] = {}
                                if system_name not in settings["system_settings"]:
                                    settings["system_settings"][system_name] = {}
                                
                                current_hidden = settings["system_settings"][system_name].get('hidden', False)
                                settings["system_settings"][system_name]['hidden'] = not current_hidden
                                save_settings(settings)
                            elif system_settings_highlighted == 1:  # Custom ROM folder
                                # Open folder browser for custom ROM folder
                                show_folder_browser = True
                                folder_browser_current_path = settings.get("roms_dir", "/userdata/roms")
                                load_folder_contents(folder_browser_current_path)
                                # Set flag to indicate we're selecting custom ROM folder
                                selected_system_to_add = {"name": f"Custom folder for {selected_system_for_settings['name']}", "type": "custom_rom_folder"}
                        elif mode == "games":
                            if highlighted in selected_games:
                                selected_games.remove(highlighted)
                            else:
                                selected_games.add(highlighted)
                    elif event.key == pygame.K_y:  # Y key = Detail view / Select folder
                        if show_folder_browser:
                            if selected_system_to_add is not None:
                                if selected_system_to_add.get("type") == "work_dir":
                                    # Set work directory
                                    settings["work_dir"] = folder_browser_current_path
                                    save_settings(settings)
                                    show_folder_browser = False
                                    selected_system_to_add = None
                                elif selected_system_to_add.get("type") == "switch_keys":
                                    # Set Nintendo Switch keys path (for folder selection, not file)
                                    settings["switch_keys_path"] = folder_browser_current_path
                                    save_settings(settings)
                                    show_folder_browser = False
                                    selected_system_to_add = None
                                    draw_loading_message("Nintendo Switch keys path updated!")
                                    pygame.time.wait(1500)
                                elif selected_system_to_add.get("type") == "custom_rom_folder":
                                    # Set custom ROM folder for the selected system
                                    system_name = selected_system_for_settings['name']
                                    if "system_settings" not in settings:
                                        settings["system_settings"] = {}
                                    if system_name not in settings["system_settings"]:
                                        settings["system_settings"][system_name] = {}
                                    
                                    settings["system_settings"][system_name]['custom_folder'] = folder_browser_current_path
                                    save_settings(settings)
                                    show_folder_browser = False
                                    selected_system_to_add = None
                                    draw_loading_message(f"Custom ROM folder set for {system_name}!")
                                    pygame.time.wait(1500)
                                else:
                                    # Add system with selected folder
                                    system_name = selected_system_to_add['name']
                                    # Calculate relative path from ROMs directory
                                    roms_dir = settings.get("roms_dir", "/userdata/roms")
                                    
                                    # Debug: Print the paths
                                    print(f"Selected folder path: {folder_browser_current_path}")
                                    print(f"ROMs directory: {roms_dir}")
                                    
                                    if folder_browser_current_path.startswith(roms_dir):
                                        rom_folder = os.path.relpath(folder_browser_current_path, roms_dir)
                                        # If the selected path is the ROMs directory itself, use a default folder name
                                        if rom_folder == ".":
                                            rom_folder = system_name.lower().replace(" ", "_").replace("-", "_")
                                    else:
                                        # If not starting with ROMs directory, use the basename of the selected path
                                        rom_folder = os.path.basename(folder_browser_current_path)
                                    
                                    # Ensure we have a valid folder name
                                    if not rom_folder or rom_folder == ".":
                                        rom_folder = system_name.lower().replace(" ", "_").replace("-", "_")
                                    
                                    print(f"Calculated roms_folder: {rom_folder}")
                                    
                                    system_url = selected_system_to_add['url']
                                    
                                    if add_system_to_added_systems(system_name, rom_folder, system_url):
                                        draw_loading_message(f"System '{system_name}' added successfully!")
                                        pygame.time.wait(2000)
                                    else:
                                        draw_loading_message(f"Failed to add system '{system_name}'")
                                        pygame.time.wait(2000)
                                    
                                    # Reset state
                                    selected_system_to_add = None
                                    show_folder_browser = False
                                    mode = "systems"
                                    highlighted = 0
                            else:
                                # Select current folder path for ROMs directory setting
                                settings["roms_dir"] = folder_browser_current_path
                                save_settings(settings)
                                show_folder_browser = False
                                # Restart app to apply ROMs directory change
                                draw_loading_message("ROMs directory changed. Restarting...")
                                pygame.time.wait(2000)
                                restart_app()
                        elif mode == "games" and not show_game_details and game_list:
                            # Show details modal for current game
                            current_game_detail = game_list[highlighted]
                            show_game_details = True
                    elif event.key == pygame.K_ESCAPE:  # Escape = Back (Button 3)
                        if show_folder_browser:
                            # Close folder browser
                            show_folder_browser = False
                        elif show_game_details:
                            # Close details modal
                            show_game_details = False
                            current_game_detail = None
                        elif show_folder_name_input:
                            # Close folder name input modal
                            show_folder_name_input = False
                        elif mode == "games":
                            mode = "systems"
                            highlighted = 0
                        elif mode == "settings":
                            mode = "systems"
                            highlighted = 0
                        elif mode == "add_systems":
                            mode = "systems"
                            highlighted = 0
                        elif mode == "systems_settings":
                            mode = "settings"
                            highlighted = 0
                        elif mode == "system_settings":
                            mode = "systems_settings"
                            highlighted = systems_settings_highlighted
                    elif event.key == pygame.K_SPACE:  # Space = Start Download (Button 10)
                        if mode == "games" and selected_games:
                            draw_loading_message("Starting download...")
                            download_files(selected_system, selected_games)
                            mode = "systems"
                            highlighted = 0
                        elif show_folder_name_input:
                            # Finish folder name input
                            create_folder_with_name()
                    elif event.key == pygame.K_RETURN:  # Enter = Select
                        if show_folder_name_input:
                            # Add selected character to folder name
                            chars = list("abcdefghijklmnopqrstuvwxyz0123456789")
                            if folder_name_char_index < len(chars):
                                selected_char = chars[folder_name_char_index]
                                folder_name_input_text += selected_char
                        elif show_folder_browser:
                            # Navigate into folder or go back
                            if folder_browser_items and folder_browser_highlighted < len(folder_browser_items):
                                selected_item = folder_browser_items[folder_browser_highlighted]
                                if selected_item["type"] == "create_folder":
                                    # Create new folder
                                    create_folder_in_browser()
                                elif selected_item["type"] in ["folder", "parent"]:
                                    folder_browser_current_path = selected_item["path"]
                                    print(f"Navigating to folder: {folder_browser_current_path}")
                                    load_folder_contents(folder_browser_current_path)
                                elif selected_item["type"] == "keys_file":
                                    # Select this .keys file for Nintendo Switch
                                    if selected_system_to_add and selected_system_to_add.get("type") == "switch_keys":
                                        settings["switch_keys_path"] = selected_item["path"]
                                        save_settings(settings)
                                        show_folder_browser = False
                                        selected_system_to_add = None
                    elif event.key == pygame.K_UP and not show_game_details:
                        # Skip keyboard navigation if joystick is connected (prevents double input)
                        if joystick is not None:
                            continue
                        if show_folder_name_input:
                            # Navigate character selection up
                            chars_per_row = 13
                            if folder_name_char_index >= chars_per_row:
                                folder_name_char_index -= chars_per_row
                        elif show_folder_browser:
                            # Folder browser navigation
                            if folder_browser_items and folder_browser_highlighted > 0:
                                folder_browser_highlighted -= 1
                        elif mode == "add_systems":
                            # Add systems navigation
                            if available_systems and add_systems_highlighted > 0:
                                add_systems_highlighted -= 1
                        elif mode == "systems_settings":
                            # Systems settings navigation
                            configurable_systems = [d for d in data if not d.get('list_systems', False) and d.get('name') != 'Other Systems']
                            if configurable_systems and systems_settings_highlighted > 0:
                                systems_settings_highlighted -= 1
                        elif mode == "system_settings":
                            # Individual system settings navigation
                            if system_settings_highlighted > 0:
                                system_settings_highlighted -= 1
                        elif mode == "games" and settings["view_type"] == "grid":
                            # Grid navigation: move up
                            cols = 4
                            if highlighted >= cols:
                                highlighted -= cols
                        else:
                            # Regular navigation for list view and other modes
                            if mode == "games":
                                max_items = len(game_list)
                            elif mode == "settings":
                                max_items = len(settings_list)
                            elif mode == "add_systems":
                                max_items = len(available_systems)
                            elif mode == "systems_settings":
                                configurable_systems = [d for d in data if not d.get('list_systems', False) and d.get('name') != 'Other Systems']
                                max_items = len(configurable_systems)
                            elif mode == "system_settings":
                                max_items = 2  # Hide from menu + Custom ROM folder
                            else:  # systems
                                visible_systems = get_visible_systems()
                                max_items = len(visible_systems) + 2  # +2 for Add Systems and Settings options
                            
                            if max_items > 0:
                                if mode == "add_systems":
                                    add_systems_highlighted = (add_systems_highlighted - 1) % max_items
                                elif mode == "systems_settings":
                                    systems_settings_highlighted = (systems_settings_highlighted - 1) % max_items
                                elif mode == "system_settings":
                                    system_settings_highlighted = (system_settings_highlighted - 1) % max_items
                                else:
                                    highlighted = (highlighted - 1) % max_items
                    elif event.key == pygame.K_DOWN and not show_game_details:
                        # Skip keyboard navigation if joystick is connected (prevents double input)
                        if joystick is not None:
                            continue
                        if show_folder_name_input:
                            # Navigate character selection down
                            chars_per_row = 13
                            total_chars = 36  # A-Z + 0-9
                            if folder_name_char_index + chars_per_row < total_chars:
                                folder_name_char_index += chars_per_row
                        elif show_folder_browser:
                            # Folder browser navigation
                            if folder_browser_items and folder_browser_highlighted < len(folder_browser_items) - 1:
                                folder_browser_highlighted += 1
                        elif mode == "add_systems":
                            # Add systems navigation
                            if available_systems and add_systems_highlighted < len(available_systems) - 1:
                                add_systems_highlighted += 1
                        elif mode == "systems_settings":
                            # Systems settings navigation
                            configurable_systems = [d for d in data if not d.get('list_systems', False) and d.get('name') != 'Other Systems']
                            if configurable_systems and systems_settings_highlighted < len(configurable_systems) - 1:
                                systems_settings_highlighted += 1
                        elif mode == "system_settings":
                            # Individual system settings navigation
                            if system_settings_highlighted < 1:  # 0 or 1 (max index)
                                system_settings_highlighted += 1
                        elif mode == "games" and settings["view_type"] == "grid":
                            # Grid navigation: move down
                            cols = 4
                            if highlighted + cols < len(game_list):
                                highlighted += cols
                        else:
                            # Regular navigation for list view and other modes
                            if mode == "games":
                                max_items = len(game_list)
                            elif mode == "settings":
                                max_items = len(settings_list)
                            elif mode == "add_systems":
                                max_items = len(available_systems)
                            elif mode == "systems_settings":
                                configurable_systems = [d for d in data if not d.get('list_systems', False) and d.get('name') != 'Other Systems']
                                max_items = len(configurable_systems)
                            elif mode == "system_settings":
                                max_items = 2  # Hide from menu + Custom ROM folder
                            else:  # systems
                                visible_systems = get_visible_systems()
                                max_items = len(visible_systems) + 2  # +2 for Add Systems and Settings options
                            
                            if max_items > 0:
                                if mode == "add_systems":
                                    add_systems_highlighted = (add_systems_highlighted + 1) % max_items
                                else:
                                    highlighted = (highlighted + 1) % max_items
                    elif event.key == pygame.K_LEFT and not show_game_details:
                        # Skip keyboard navigation if joystick is connected (prevents double input)
                        if joystick is not None:
                            continue
                        if show_folder_name_input:
                            # Navigate character selection left
                            chars_per_row = 13
                            if folder_name_char_index % chars_per_row > 0:
                                folder_name_char_index -= 1
                        elif mode == "games" and game_list:
                            if settings["view_type"] == "grid":
                                # Grid navigation: move left
                                cols = 4
                                if highlighted % cols > 0:
                                    highlighted -= 1
                            else:
                                # List navigation: jump to different letter
                                highlighted = find_next_letter_index(game_list, highlighted, -1)
                    elif event.key == pygame.K_RIGHT and mode == "games" and not show_game_details:
                        # Skip keyboard navigation if joystick is connected (prevents double input)
                        if joystick is not None:
                            continue
                        if show_folder_name_input:
                            # Navigate character selection right
                            chars_per_row = 13
                            total_chars = 36  # A-Z + 0-9
                            if folder_name_char_index % chars_per_row < chars_per_row - 1 and folder_name_char_index < total_chars - 1:
                                folder_name_char_index += 1
                        elif game_list:
                            if settings["view_type"] == "grid":
                                # Grid navigation: move right
                                cols = 4
                                if highlighted % cols < cols - 1 and highlighted < len(game_list) - 1:
                                    highlighted += 1
                            else:
                                # List navigation: jump to different letter
                                highlighted = find_next_letter_index(game_list, highlighted, 1)
                    elif event.key == pygame.K_BACKSPACE:  # Backspace = Delete character
                        if show_folder_name_input:
                            if folder_name_input_text:
                                folder_name_input_text = folder_name_input_text[:-1]
                    elif event.key == pygame.K_UP and not show_game_details:
                        # Skip keyboard navigation if joystick is connected (prevents double input)
                        if joystick is not None:
                            continue
                        if show_folder_name_input:
                            # Navigate character selection up
                            chars_per_row = 13
                            if folder_name_char_index >= chars_per_row:
                                folder_name_char_index -= chars_per_row
                        elif show_folder_browser:
                            # Folder browser navigation
                            if folder_browser_items and folder_browser_highlighted > 0:
                                folder_browser_highlighted -= 1
                        elif mode == "add_systems":
                            # Add systems navigation
                            if available_systems and add_systems_highlighted > 0:
                                add_systems_highlighted -= 1
                        elif mode == "systems_settings":
                            # Systems settings navigation
                            configurable_systems = [d for d in data if not d.get('list_systems', False) and d.get('name') != 'Other Systems']
                            if configurable_systems and systems_settings_highlighted > 0:
                                systems_settings_highlighted -= 1
                        elif mode == "system_settings":
                            # Individual system settings navigation
                            if system_settings_highlighted > 0:
                                system_settings_highlighted -= 1
                        elif mode == "games" and settings["view_type"] == "grid":
                            # Grid navigation: move up
                            cols = 4
                            if highlighted >= cols:
                                highlighted -= cols
                        else:
                            # Regular navigation for list view and other modes
                            if mode == "games":
                                max_items = len(game_list)
                            elif mode == "settings":
                                max_items = len(settings_list)
                            elif mode == "add_systems":
                                max_items = len(available_systems)
                            elif mode == "systems_settings":
                                configurable_systems = [d for d in data if not d.get('list_systems', False) and d.get('name') != 'Other Systems']
                                max_items = len(configurable_systems)
                            elif mode == "system_settings":
                                max_items = 2  # Hide from menu + Custom ROM folder
                            else:  # systems
                                visible_systems = get_visible_systems()
                                max_items = len(visible_systems) + 2  # +2 for Add Systems and Settings options
                            
                            if max_items > 0:
                                if mode == "add_systems":
                                    add_systems_highlighted = (add_systems_highlighted - 1) % max_items
                                elif mode == "systems_settings":
                                    systems_settings_highlighted = (systems_settings_highlighted - 1) % max_items
                                elif mode == "system_settings":
                                    system_settings_highlighted = (system_settings_highlighted - 1) % max_items
                                else:
                                    highlighted = (highlighted - 1) % max_items if hat[1] == 1 else (highlighted + 1) % max_items
                                movement_occurred = True
                    elif event.key == pygame.K_DOWN and not show_game_details:
                        # Skip keyboard navigation if joystick is connected (prevents double input)
                        if joystick is not None:
                            continue
                        if show_folder_name_input:
                            # Navigate character selection down
                            chars_per_row = 13
                            total_chars = 36  # A-Z + 0-9
                            if folder_name_char_index + chars_per_row < total_chars:
                                folder_name_char_index += chars_per_row
                        elif show_folder_browser:
                            # Folder browser navigation
                            if folder_browser_items and folder_browser_highlighted < len(folder_browser_items) - 1:
                                folder_browser_highlighted += 1
                        elif mode == "add_systems":
                            # Add systems navigation
                            if available_systems and add_systems_highlighted < len(available_systems) - 1:
                                add_systems_highlighted += 1
                        elif mode == "systems_settings":
                            # Systems settings navigation
                            configurable_systems = [d for d in data if not d.get('list_systems', False) and d.get('name') != 'Other Systems']
                            if configurable_systems and systems_settings_highlighted < len(configurable_systems) - 1:
                                systems_settings_highlighted += 1
                        elif mode == "system_settings":
                            # Individual system settings navigation
                            if system_settings_highlighted < 1:  # 0 or 1 (max index)
                                system_settings_highlighted += 1
                        elif mode == "games" and settings["view_type"] == "grid":
                            # Grid navigation: move down
                            cols = 4
                            if highlighted + cols < len(game_list):
                                highlighted += cols
                        else:
                            # Regular navigation for list view and other modes
                            if mode == "games":
                                max_items = len(game_list)
                            elif mode == "settings":
                                max_items = len(settings_list)
                            elif mode == "add_systems":
                                max_items = len(available_systems)
                            elif mode == "systems_settings":
                                configurable_systems = [d for d in data if not d.get('list_systems', False) and d.get('name') != 'Other Systems']
                                max_items = len(configurable_systems)
                            elif mode == "system_settings":
                                max_items = 2  # Hide from menu + Custom ROM folder
                            else:  # systems
                                visible_systems = get_visible_systems()
                                max_items = len(visible_systems) + 2  # +2 for Add Systems and Settings options
                            
                            if max_items > 0:
                                if mode == "add_systems":
                                    add_systems_highlighted = (add_systems_highlighted + 1) % max_items
                                else:
                                    highlighted = (highlighted + 1) % max_items
                                movement_occurred = True
                    elif event.key == pygame.K_LEFT and mode == "games" and not show_game_details:
                        # Skip keyboard navigation if joystick is connected (prevents double input)
                        if joystick is not None:
                            continue
                        if show_folder_name_input:
                            # Navigate character selection left
                            chars_per_row = 13
                            if folder_name_char_index % chars_per_row > 0:
                                folder_name_char_index -= 1
                        elif game_list:
                            if settings["view_type"] == "grid":
                                # Grid navigation: move left
                                cols = 4
                                if highlighted % cols > 0:
                                    highlighted -= 1
                            else:
                                # List navigation: jump to different letter
                                highlighted = find_next_letter_index(game_list, highlighted, -1)
                    elif event.key == pygame.K_RIGHT and mode == "games" and not show_game_details:
                        # Skip keyboard navigation if joystick is connected (prevents double input)
                        if joystick is not None:
                            continue
                        if show_folder_name_input:
                            # Navigate character selection right
                            chars_per_row = 13
                            total_chars = 36  # A-Z + 0-9
                            if folder_name_char_index % chars_per_row < chars_per_row - 1 and folder_name_char_index < total_chars - 1:
                                folder_name_char_index += 1
                        elif game_list:
                            if settings["view_type"] == "grid":
                                # Grid navigation: move right
                                cols = 4
                                if highlighted % cols < cols - 1 and highlighted < len(game_list) - 1:
                                    highlighted += 1
                            else:
                                # List navigation: jump to different letter
                                highlighted = find_next_letter_index(game_list, highlighted, 1)
                elif event.type == pygame.JOYBUTTONDOWN:
                    # Debug controller - capture joystick button presses
                    if settings.get("debug_controller", False):
                        # Find which action this button maps to
                        mapped_action = None
                        print(f"DEBUG: Looking for button {event.button} in mapping: {controller_mapping}")
                        for action in controller_mapping:
                            button_info = controller_mapping[action]
                            print(f"DEBUG: Checking action '{action}' with info: {button_info}")
                            # Check if this is a regular button mapping (integer)
                            if isinstance(button_info, int) and button_info == event.button:
                                mapped_action = action
                                print(f"DEBUG: Found match! Action: {mapped_action}")
                                break
                        
                        if mapped_action:
                            current_pressed_button = f"Button {event.button} ({mapped_action})"
                        else:
                            current_pressed_button = f"Button {event.button} (unmapped)"
                        last_button_time = pygame.time.get_ticks()
                    
                    # Debug: Show all button presses
                    print(f"Joystick button pressed: {event.button}")
                    
                    # Handle directional button inputs mapped as D-pad
                    hat = None
                    if input_matches_action(event, "up"):
                        hat = (0, 1)
                    elif input_matches_action(event, "down"):
                        hat = (0, -1)
                    elif input_matches_action(event, "left"):
                        hat = (-1, 0)
                    elif input_matches_action(event, "right"):
                        hat = (1, 0)
                    
                    left_shoulder_button = get_controller_button("left_shoulder")
                    right_shoulder_button = get_controller_button("right_shoulder")
                    
                    # Process as D-pad navigation if we matched a directional input
                    if hat is not None:
                        movement_occurred = False
                        
                        if hat[1] != 0 and not show_game_details:  # Up or Down
                            if show_folder_name_input:
                                # Navigate character selection up/down
                                chars_per_row = 13
                                total_chars = 36  # A-Z + 0-9
                                if hat[1] == 1:  # Up
                                    if folder_name_char_index >= chars_per_row:
                                        folder_name_char_index -= chars_per_row
                                        movement_occurred = True
                                else:  # Down
                                    if folder_name_char_index + chars_per_row < total_chars:
                                        folder_name_char_index += chars_per_row
                                        movement_occurred = True
                            elif show_folder_browser:
                                # Folder browser navigation
                                if hat[1] == 1:  # Up
                                    if folder_browser_items and folder_browser_highlighted > 0:
                                        folder_browser_highlighted -= 1
                                        movement_occurred = True
                                else:  # Down
                                    if folder_browser_items and folder_browser_highlighted < len(folder_browser_items) - 1:
                                        folder_browser_highlighted += 1
                                        movement_occurred = True
                            elif mode == "add_systems":
                                # Add systems navigation
                                if hat[1] == 1:  # Up
                                    if available_systems and add_systems_highlighted > 0:
                                        add_systems_highlighted -= 1
                                        movement_occurred = True
                                else:  # Down
                                    if available_systems and add_systems_highlighted < len(available_systems) - 1:
                                        add_systems_highlighted += 1
                                        movement_occurred = True
                            elif mode == "games" and settings["view_type"] == "grid":
                                # Grid navigation: move up/down
                                cols = 4
                                if hat[1] == 1:  # Up
                                    if highlighted >= cols:
                                        highlighted -= cols
                                        movement_occurred = True
                                else:  # Down
                                    if highlighted + cols < len(game_list):
                                        highlighted += cols
                                        movement_occurred = True
                            else:
                                # Regular navigation for list view and other modes
                                if mode == "games":
                                    max_items = len(game_list)
                                elif mode == "settings":
                                    max_items = len(settings_list)
                                elif mode == "add_systems":
                                    max_items = len(available_systems)
                                else:  # systems
                                    visible_systems = get_visible_systems()
                                    max_items = len(visible_systems) + 2  # +2 for Add Systems and Settings options
                                
                                if max_items > 0:
                                    if mode == "add_systems":
                                        add_systems_highlighted = (add_systems_highlighted - 1) % max_items if hat[1] == 1 else (add_systems_highlighted + 1) % max_items
                                    else:
                                        highlighted = (highlighted - 1) % max_items if hat[1] == 1 else (highlighted + 1) % max_items
                                    movement_occurred = True
                        elif hat[0] != 0 and not show_game_details:  # Left or Right
                            if show_folder_name_input:
                                # Navigate character selection left/right
                                chars_per_row = 13
                                total_chars = 36  # A-Z + 0-9
                                if hat[0] < 0:  # Left
                                    if folder_name_char_index % chars_per_row > 0:
                                        folder_name_char_index -= 1
                                        movement_occurred = True
                                else:  # Right
                                    if folder_name_char_index % chars_per_row < chars_per_row - 1 and folder_name_char_index < total_chars - 1:
                                        folder_name_char_index += 1
                                        movement_occurred = True
                            elif mode == "games" and settings["view_type"] == "grid":
                                # Grid navigation: move left/right
                                cols = 4
                                if hat[0] < 0:  # Left
                                    if highlighted % cols > 0:
                                        highlighted -= 1
                                        movement_occurred = True
                                else:  # Right
                                    if highlighted % cols < cols - 1 and highlighted < len(game_list) - 1:
                                        highlighted += 1
                                        movement_occurred = True
                            else:
                                # List navigation: jump to different letter
                                items = game_list
                                old_highlighted = highlighted
                                if hat[0] < 0:  # Left
                                    highlighted = find_next_letter_index(items, highlighted, -1)
                                else:  # Right
                                    highlighted = find_next_letter_index(items, highlighted, 1)
                                if highlighted != old_highlighted:
                                    movement_occurred = True
                        
                        # Skip regular button processing for Odin directional buttons
                        continue
                    
                    # Controller-aware button mapping
                    select_button = get_controller_button("select")
                    back_button = get_controller_button("back")
                    start_button = get_controller_button("start")
                    detail_button = get_controller_button("detail")
                    left_shoulder_button = get_controller_button("left_shoulder")
                    right_shoulder_button = get_controller_button("right_shoulder")
                    
                    # Process as D-pad navigation if we matched a directional input
                    if hat is not None:
                        movement_occurred = False
                        
                        if hat[1] != 0 and not show_game_details:  # Up or Down
                            if show_folder_name_input:
                                # Navigate character selection up/down
                                chars_per_row = 13
                                total_chars = 36  # A-Z + 0-9
                                if hat[1] == 1:  # Up
                                    if folder_name_char_index >= chars_per_row:
                                        folder_name_char_index -= chars_per_row
                                        movement_occurred = True
                                else:  # Down
                                    if folder_name_char_index + chars_per_row < total_chars:
                                        folder_name_char_index += chars_per_row
                                        movement_occurred = True
                            elif show_folder_browser:
                                # Folder browser navigation
                                if hat[1] == 1:  # Up
                                    if folder_browser_items and folder_browser_highlighted > 0:
                                        folder_browser_highlighted -= 1
                                        movement_occurred = True
                                else:  # Down
                                    if folder_browser_items and folder_browser_highlighted < len(folder_browser_items) - 1:
                                        folder_browser_highlighted += 1
                                        movement_occurred = True
                            elif mode == "add_systems":
                                # Add systems navigation
                                if hat[1] == 1:  # Up
                                    if available_systems and add_systems_highlighted > 0:
                                        add_systems_highlighted -= 1
                                        movement_occurred = True
                                else:  # Down
                                    if available_systems and add_systems_highlighted < len(available_systems) - 1:
                                        add_systems_highlighted += 1
                                        movement_occurred = True
                            elif mode == "games" and settings["view_type"] == "grid":
                                # Grid navigation: move up/down
                                cols = 4
                                if hat[1] == 1:  # Up
                                    if highlighted >= cols:
                                        highlighted -= cols
                                        movement_occurred = True
                                else:  # Down
                                    if highlighted + cols < len(game_list):
                                        highlighted += cols
                                        movement_occurred = True
                            else:
                                # Regular navigation for list view and other modes
                                if mode == "games":
                                    max_items = len(game_list)
                                elif mode == "settings":
                                    max_items = len(settings_list)
                                elif mode == "add_systems":
                                    max_items = len(available_systems)
                                else:  # systems
                                    visible_systems = get_visible_systems()
                                    max_items = len(visible_systems) + 2  # +2 for Add Systems and Settings options
                                
                                if max_items > 0:
                                    if mode == "add_systems":
                                        add_systems_highlighted = (add_systems_highlighted - 1) % max_items if hat[1] == 1 else (add_systems_highlighted + 1) % max_items
                                    else:
                                        highlighted = (highlighted - 1) % max_items if hat[1] == 1 else (highlighted + 1) % max_items
                                    movement_occurred = True
                        elif hat[0] != 0 and not show_game_details:  # Left or Right
                            if show_folder_name_input:
                                # Navigate character selection left/right
                                chars_per_row = 13
                                total_chars = 36  # A-Z + 0-9
                                if hat[0] < 0:  # Left
                                    if folder_name_char_index % chars_per_row > 0:
                                        folder_name_char_index -= 1
                                        movement_occurred = True
                                else:  # Right
                                    if folder_name_char_index % chars_per_row < chars_per_row - 1 and folder_name_char_index < total_chars - 1:
                                        folder_name_char_index += 1
                                        movement_occurred = True
                            elif mode == "games" and settings["view_type"] == "grid":
                                # Grid navigation: move left/right
                                cols = 4
                                if hat[0] < 0:  # Left
                                    if highlighted % cols > 0:
                                        highlighted -= 1
                                        movement_occurred = True
                                else:  # Right
                                    if highlighted % cols < cols - 1 and highlighted < len(game_list) - 1:
                                        highlighted += 1
                                        movement_occurred = True
                            else:
                                # List navigation: jump to different letter
                                items = game_list
                                old_highlighted = highlighted
                                if hat[0] < 0:  # Left
                                    highlighted = find_next_letter_index(items, highlighted, -1)
                                else:  # Right
                                    highlighted = find_next_letter_index(items, highlighted, 1)
                                if highlighted != old_highlighted:
                                    movement_occurred = True
                        
                        # Skip regular button processing for Odin directional buttons
                        continue
                    
                    # Note: Using input_matches_action() for dynamic button mapping
                    
                    if input_matches_action(event, "select"):  # Select
                        if show_folder_name_input:
                            # Add selected character to folder name
                            chars = list("abcdefghijklmnopqrstuvwxyz0123456789")
                            if folder_name_char_index < len(chars):
                                selected_char = chars[folder_name_char_index]
                                folder_name_input_text += selected_char
                        elif show_folder_browser:
                            # Navigate into folder or go back
                            if folder_browser_items and folder_browser_highlighted < len(folder_browser_items):
                                selected_item = folder_browser_items[folder_browser_highlighted]
                                if selected_item["type"] == "create_folder":
                                    # Create new folder
                                    create_folder_in_browser()
                                elif selected_item["type"] in ["folder", "parent"]:
                                    folder_browser_current_path = selected_item["path"]
                                    print(f"Navigating to folder: {folder_browser_current_path}")
                                    load_folder_contents(folder_browser_current_path)
                                elif selected_item["type"] == "keys_file":
                                    # Select this .keys file for Nintendo Switch
                                    if selected_system_to_add and selected_system_to_add.get("type") == "switch_keys":
                                        settings["switch_keys_path"] = selected_item["path"]
                                        save_settings(settings)
                                        show_folder_browser = False
                                        selected_system_to_add = None
                        elif mode == "systems":
                            # Use helper function for consistent filtering
                            visible_systems = get_visible_systems()
                            systems_count = len(visible_systems)
                            if highlighted == systems_count:  # Add Systems option
                                mode = "add_systems"
                                highlighted = 0
                                add_systems_highlighted = 0
                                # Load available systems in background
                                load_available_systems()
                            elif highlighted == systems_count + 1:  # Settings option
                                mode = "settings"
                                highlighted = 0
                                settings_scroll_offset = 0
                            else:
                                # Map visible system index to original data index
                                if highlighted < len(visible_systems):
                                    selected_visible_system = visible_systems[highlighted]
                                    selected_system = get_system_index_by_name(selected_visible_system['name'])
                                    current_page = 0
                                    game_list = list_files(selected_system, current_page)
                                    selected_games = set()
                                    mode = "games"
                                    highlighted = 0
                        elif mode == "games":
                            if highlighted in selected_games:
                                selected_games.remove(highlighted)
                            else:
                                selected_games.add(highlighted)
                        elif mode == "settings":
                            # Toggle settings or reset cache
                            if highlighted == 0:  # Enable Box-art Display
                                settings["enable_boxart"] = not settings["enable_boxart"]
                                save_settings(settings)
                            elif highlighted == 1:  # Enable Image Cache
                                settings["cache_enabled"] = not settings["cache_enabled"]
                                if not settings["cache_enabled"]:
                                    reset_image_cache()
                                save_settings(settings)
                            elif highlighted == 2:  # Reset Image Cache
                                reset_image_cache()
                            elif highlighted == 3:  # Update from GitHub
                                update_from_github()
                            elif highlighted == 4:  # View Type
                                settings["view_type"] = "grid" if settings["view_type"] == "list" else "list"
                                save_settings(settings)
                            elif highlighted == 5:  # USA Games Only
                                settings["usa_only"] = not settings["usa_only"]
                                save_settings(settings)
                            elif highlighted == 6:  # Debug Controller
                                settings["debug_controller"] = not settings["debug_controller"]
                                save_settings(settings)
                            elif highlighted == 7:  # Work Directory
                                # Open folder browser for work directory selection
                                show_folder_browser = True
                                # Use current work_dir or fallback to a sensible default
                                current_work = settings.get("work_dir", "")
                                if not current_work or not os.path.exists(os.path.dirname(current_work)):
                                    # Use a fallback based on environment
                                    if os.path.exists("/userdata") and os.access("/userdata", os.R_OK):
                                        folder_browser_current_path = "/userdata"
                                    else:
                                        folder_browser_current_path = os.path.expanduser("~")  # Home directory
                                else:
                                    folder_browser_current_path = current_work
                                load_folder_contents(folder_browser_current_path)
                                # Set a flag to indicate we're selecting work directory
                                selected_system_to_add = {"name": "Work Directory", "type": "work_dir"}
                            elif highlighted == 8:  # ROMs Directory  
                                # Open folder browser
                                show_folder_browser = True
                                # Use current roms_dir or fallback to a sensible default
                                current_roms = settings.get("roms_dir", "")
                                if not current_roms or not os.path.exists(os.path.dirname(current_roms)):
                                    # Use a fallback based on environment
                                    if os.path.exists("/userdata") and os.access("/userdata", os.R_OK):
                                        folder_browser_current_path = "/userdata/roms"
                                    else:
                                        folder_browser_current_path = os.path.expanduser("~")  # Home directory
                                else:
                                    folder_browser_current_path = current_roms
                                load_folder_contents(folder_browser_current_path)
                            elif highlighted == 9:  # Nintendo Switch Keys
                                # Open folder browser for .keys files
                                show_folder_browser = True
                                # Use current keys path or default to home directory
                                current_keys = settings.get("switch_keys_path", "")
                                if current_keys and os.path.exists(os.path.dirname(current_keys)):
                                    folder_browser_current_path = os.path.dirname(current_keys)
                                else:
                                    # Default to ~/.switch directory or home
                                    switch_dir = os.path.expanduser("~/.switch")
                                    if os.path.exists(switch_dir):
                                        folder_browser_current_path = switch_dir
                                    else:
                                        folder_browser_current_path = os.path.expanduser("~")
                                load_folder_contents(folder_browser_current_path)
                                # Set a flag to indicate we're selecting Nintendo Switch keys
                                selected_system_to_add = {"name": "Nintendo Switch Keys", "type": "switch_keys"}
                            elif highlighted == 10:  # Remap Controller
                                # Trigger controller remapping
                                show_controller_mapping = True
                            elif highlighted == 11:  # Systems Settings
                                mode = "systems_settings"
                                systems_settings_highlighted = 0
                                highlighted = 0
                        elif mode == "add_systems":
                            # Handle add systems selection
                            if available_systems and add_systems_highlighted < len(available_systems):
                                selected_system_to_add = available_systems[add_systems_highlighted]
                                # Open folder browser to select ROM folder
                                show_folder_browser = True
                                # Start in ROMs directory
                                folder_browser_current_path = settings.get("roms_dir", "/userdata/roms")
                                load_folder_contents(folder_browser_current_path)
                        elif mode == "systems_settings":
                            # Handle systems settings navigation
                            configurable_systems = [d for d in data if not d.get('list_systems', False) and d.get('name') != 'Other Systems']
                            if systems_settings_highlighted < len(configurable_systems):
                                selected_system_for_settings = configurable_systems[systems_settings_highlighted]
                                mode = "system_settings"
                                system_settings_highlighted = 0
                                highlighted = 0
                        elif mode == "system_settings":
                            # Handle individual system settings
                            if system_settings_highlighted == 0:  # Hide from main menu
                                system_name = selected_system_for_settings['name']
                                if "system_settings" not in settings:
                                    settings["system_settings"] = {}
                                if system_name not in settings["system_settings"]:
                                    settings["system_settings"][system_name] = {}
                                
                                current_hidden = settings["system_settings"][system_name].get('hidden', False)
                                settings["system_settings"][system_name]['hidden'] = not current_hidden
                                save_settings(settings)
                            elif system_settings_highlighted == 1:  # Custom ROM folder
                                # Open folder browser for custom ROM folder
                                show_folder_browser = True
                                folder_browser_current_path = settings.get("roms_dir", "/userdata/roms")
                                load_folder_contents(folder_browser_current_path)
                                # Set flag to indicate we're selecting custom ROM folder
                                selected_system_to_add = {"name": f"Custom folder for {selected_system_for_settings['name']}", "type": "custom_rom_folder"}
                        elif mode == "games":
                            if highlighted in selected_games:
                                selected_games.remove(highlighted)
                            else:
                                selected_games.add(highlighted)
                    elif input_matches_action(event, "detail"):  # Detail view / Select folder
                        if show_folder_browser:
                            print(f"Detail button pressed - Current folder: {folder_browser_current_path}")
                            if selected_system_to_add is not None:
                                if selected_system_to_add.get("type") == "work_dir":
                                    # Set work directory
                                    settings["work_dir"] = folder_browser_current_path
                                    save_settings(settings)
                                    show_folder_browser = False
                                    selected_system_to_add = None
                                elif selected_system_to_add.get("type") == "switch_keys":
                                    # Set Nintendo Switch keys path (for folder selection, not file)
                                    settings["switch_keys_path"] = folder_browser_current_path
                                    save_settings(settings)
                                    show_folder_browser = False
                                    selected_system_to_add = None
                                    draw_loading_message("Nintendo Switch keys path updated!")
                                    pygame.time.wait(1500)
                                elif selected_system_to_add.get("type") == "custom_rom_folder":
                                    # Set custom ROM folder for the selected system
                                    system_name = selected_system_for_settings['name']
                                    if "system_settings" not in settings:
                                        settings["system_settings"] = {}
                                    if system_name not in settings["system_settings"]:
                                        settings["system_settings"][system_name] = {}
                                    
                                    settings["system_settings"][system_name]['custom_folder'] = folder_browser_current_path
                                    save_settings(settings)
                                    show_folder_browser = False
                                    selected_system_to_add = None
                                    draw_loading_message(f"Custom ROM folder set for {system_name}!")
                                    pygame.time.wait(1500)
                                else:
                                    # Add system with selected folder
                                    system_name = selected_system_to_add['name']
                                    # Calculate relative path from ROMs directory
                                    roms_dir = settings.get("roms_dir", "/userdata/roms")
                                    
                                    # Debug: Print the paths
                                    print(f"Selected folder path: {folder_browser_current_path}")
                                    print(f"ROMs directory: {roms_dir}")
                                    
                                    if folder_browser_current_path.startswith(roms_dir):
                                        rom_folder = os.path.relpath(folder_browser_current_path, roms_dir)
                                        # If the selected path is the ROMs directory itself, use a default folder name
                                        if rom_folder == ".":
                                            rom_folder = system_name.lower().replace(" ", "_").replace("-", "_")
                                    else:
                                        # If not starting with ROMs directory, use the basename of the selected path
                                        rom_folder = os.path.basename(folder_browser_current_path)
                                    
                                    # Ensure we have a valid folder name
                                    if not rom_folder or rom_folder == ".":
                                        rom_folder = system_name.lower().replace(" ", "_").replace("-", "_")
                                    
                                    print(f"Calculated roms_folder: {rom_folder}")
                                    
                                    system_url = selected_system_to_add['url']
                                    
                                    if add_system_to_added_systems(system_name, rom_folder, system_url):
                                        draw_loading_message(f"System '{system_name}' added successfully!")
                                        pygame.time.wait(2000)
                                    else:
                                        draw_loading_message(f"Failed to add system '{system_name}'")
                                        pygame.time.wait(2000)
                                    
                                    # Reset state
                                    selected_system_to_add = None
                                show_folder_browser = False
                                mode = "systems"
                                highlighted = 0
                            else:
                                # Select current folder path for ROMs directory setting
                                settings["roms_dir"] = folder_browser_current_path
                                save_settings(settings)
                                show_folder_browser = False
                                # Restart app to apply ROMs directory change
                                draw_loading_message("ROMs directory changed. Restarting...")
                                pygame.time.wait(2000)
                                restart_app()
                        elif mode == "games" and not show_game_details and game_list:
                            # Show details modal for current game
                            current_game_detail = game_list[highlighted]
                            show_game_details = True
                    elif input_matches_action(event, "back"):  # Back
                        if show_folder_browser:
                            # Close folder browser
                            show_folder_browser = False
                        elif show_game_details:
                            # Close details modal
                            show_game_details = False
                            current_game_detail = None
                        elif show_folder_name_input:
                            # Close folder name input modal
                            show_folder_name_input = False
                        elif mode == "games":
                            mode = "systems"
                            highlighted = 0
                        elif mode == "settings":
                            mode = "systems"
                            highlighted = 0
                        elif mode == "add_systems":
                            mode = "systems"
                            highlighted = 0
                        elif mode == "systems_settings":
                            mode = "settings"
                            highlighted = 0
                        elif mode == "system_settings":
                            mode = "systems_settings"
                            highlighted = systems_settings_highlighted
                    elif input_matches_action(event, "left_shoulder"):  # Left shoulder - Previous page
                        if mode == "games" and data[selected_system].get('supports_pagination', False):
                            if current_page > 0:
                                current_page -= 1
                                game_list = list_files(selected_system, current_page)
                                highlighted = 0
                                selected_games = set()
                    elif input_matches_action(event, "right_shoulder"):  # Right shoulder - Next page
                        if mode == "games" and data[selected_system].get('supports_pagination', False):
                            current_page += 1
                            new_games = list_files(selected_system, current_page)
                            if new_games:  # Only move if there are games on next page
                                game_list = new_games
                                highlighted = 0
                                selected_games = set()
                            else:
                                current_page -= 1  # Revert if no games found
                    elif input_matches_action(event, "start"):  # Start Download
                        if mode == "games" and selected_games:
                            draw_loading_message("Starting download...")
                            download_files(selected_system, selected_games)
                            mode = "systems"
                            highlighted = 0
                        elif show_folder_name_input:
                            # Finish folder name input
                            create_folder_with_name()
                elif event.type == pygame.JOYHATMOTION:
                    hat = joystick.get_hat(0)
                    
                    # Debug controller - capture D-pad movement
                    if settings.get("debug_controller", False) and hat != (0, 0):
                        # Find which action this D-pad direction maps to
                        mapped_action = None
                        print(f"DEBUG D-PAD: Looking for hat {hat} in mapping: {controller_mapping}")
                        for action in controller_mapping:
                            action_info = controller_mapping[action]
                            print(f"DEBUG D-PAD: Checking action '{action}' with info: {action_info}")
                            if ((isinstance(action_info, tuple) or isinstance(action_info, list)) and 
                                len(action_info) >= 3 and
                                action_info[0] == "hat" and 
                                tuple(action_info[1:]) == hat):
                                mapped_action = action
                                print(f"DEBUG D-PAD: Found match! Action: {mapped_action}")
                                break
                            elif isinstance(action_info, tuple):
                                print(f"DEBUG D-PAD: Tuple comparison - Expected: {hat}, Got: {action_info[1:]}")
                            else:
                                print(f"DEBUG D-PAD: Not a tuple: {action_info}")
                        
                        direction = ""
                        if hat[1] == 1: direction = "Up"
                        elif hat[1] == -1: direction = "Down"
                        elif hat[0] == -1: direction = "Left"
                        elif hat[0] == 1: direction = "Right"
                        else: direction = f"{hat}"
                        
                        if mapped_action:
                            current_pressed_button = f"D-Pad {direction} ({mapped_action})"
                        else:
                            current_pressed_button = f"D-Pad {direction} (unmapped)"
                        last_button_time = pygame.time.get_ticks()
                    
                    # Only process if D-pad state actually changed
                    if hat == last_dpad_state:
                        continue
                    
                    # Ignore release events (0,0) - only process actual direction presses
                    if hat == (0, 0):
                        last_dpad_state = hat  # Update state but don't process navigation
                        continue
                    
                    # Update last state
                    last_dpad_state = hat
                    
                    movement_occurred = False
                    
                    if hat[1] != 0 and not show_game_details:  # Up or Down
                        if show_folder_name_input:
                            # Navigate character selection up/down
                            chars_per_row = 13
                            total_chars = 36  # A-Z + 0-9
                            if hat[1] == 1:  # Up
                                if folder_name_char_index >= chars_per_row:
                                    folder_name_char_index -= chars_per_row
                                    movement_occurred = True
                            else:  # Down
                                if folder_name_char_index + chars_per_row < total_chars:
                                    folder_name_char_index += chars_per_row
                                    movement_occurred = True
                        elif show_folder_browser:
                            # Folder browser navigation
                            if hat[1] == 1:  # Up
                                if folder_browser_items and folder_browser_highlighted > 0:
                                    folder_browser_highlighted -= 1
                                    movement_occurred = True
                            else:  # Down
                                if folder_browser_items and folder_browser_highlighted < len(folder_browser_items) - 1:
                                    folder_browser_highlighted += 1
                                    movement_occurred = True
                        elif mode == "add_systems":
                            # Add systems navigation
                            if hat[1] == 1:  # Up
                                if available_systems and add_systems_highlighted > 0:
                                    add_systems_highlighted -= 1
                                    movement_occurred = True
                            else:  # Down
                                if available_systems and add_systems_highlighted < len(available_systems) - 1:
                                    add_systems_highlighted += 1
                                    movement_occurred = True
                        elif mode == "games" and settings["view_type"] == "grid":
                            # Grid navigation: move up/down
                            cols = 4
                            if hat[1] == 1:  # Up
                                if highlighted >= cols:
                                    highlighted -= cols
                                    movement_occurred = True
                            else:  # Down
                                if highlighted + cols < len(game_list):
                                    highlighted += cols
                                    movement_occurred = True
                        else:
                            # Regular navigation for list view and other modes
                            if mode == "games":
                                max_items = len(game_list)
                            elif mode == "settings":
                                max_items = len(settings_list)
                            elif mode == "add_systems":
                                max_items = len(available_systems)
                            elif mode == "systems_settings":
                                configurable_systems = [d for d in data if not d.get('list_systems', False) and d.get('name') != 'Other Systems']
                                max_items = len(configurable_systems)
                            elif mode == "system_settings":
                                max_items = 2  # Hide from menu + Custom ROM folder
                            else:  # systems
                                visible_systems = get_visible_systems()
                                max_items = len(visible_systems) + 2  # +2 for Add Systems and Settings options
                            
                            if max_items > 0:
                                if mode == "add_systems":
                                    add_systems_highlighted = (add_systems_highlighted - 1) % max_items
                                elif mode == "systems_settings":
                                    systems_settings_highlighted = (systems_settings_highlighted - 1) % max_items
                                elif mode == "system_settings":
                                    system_settings_highlighted = (system_settings_highlighted - 1) % max_items
                                else:
                                    highlighted = (highlighted - 1) % max_items if hat[1] == 1 else (highlighted + 1) % max_items
                                movement_occurred = True
                    elif hat[0] != 0 and not show_game_details:  # Left or Right
                        if show_folder_name_input:
                            # Navigate character selection left/right
                            chars_per_row = 13
                            total_chars = 36  # A-Z + 0-9
                            if hat[0] < 0:  # Left
                                if folder_name_char_index % chars_per_row > 0:
                                    folder_name_char_index -= 1
                                    movement_occurred = True
                            else:  # Right
                                if folder_name_char_index % chars_per_row < chars_per_row - 1 and folder_name_char_index < total_chars - 1:
                                    folder_name_char_index += 1
                                    movement_occurred = True
                        elif mode == "games" and settings["view_type"] == "grid":
                            # Grid navigation: move left/right
                            cols = 4
                            if hat[0] < 0:  # Left
                                if highlighted % cols > 0:
                                    highlighted -= 1
                                    movement_occurred = True
                            else:  # Right
                                if highlighted % cols < cols - 1 and highlighted < len(game_list) - 1:
                                    highlighted += 1
                                    movement_occurred = True
                        else:
                            # List navigation: jump to different letter
                            items = game_list
                            old_highlighted = highlighted
                            if hat[0] < 0:  # Left
                                highlighted = find_next_letter_index(items, highlighted, -1)
                            else:  # Right
                                highlighted = find_next_letter_index(items, highlighted, 1)
                            if highlighted != old_highlighted:
                                movement_occurred = True
                    
                    # Movement tracking complete


        except Exception as e:
            log_error("Error in main loop", type(e).__name__, traceback.format_exc())

except Exception as e:
    log_error("Fatal error during initialization", type(e).__name__, traceback.format_exc())
finally:
    pygame.quit()
    sys.exit()
