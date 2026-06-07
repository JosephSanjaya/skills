#!/usr/bin/env python3
import os
import re
import sys
import platform
import shutil
import subprocess
import fnmatch

def parse_gitignore(gitignore_path):
    """Parses a .gitignore file and returns a list of (pattern, is_dir) tuples."""
    patterns = []
    if not os.path.exists(gitignore_path):
        return patterns
    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                is_dir = line.endswith('/')
                pattern = line.rstrip('/')
                patterns.append((pattern, is_dir))
    except Exception as e:
        print(f"Warning: Failed to read .gitignore: {e}")
    return patterns

def is_ignored(path, gitignore_patterns, repo_root):
    """Determines if a given path should be ignored based on common folders and .gitignore patterns."""
    rel_path = os.path.relpath(path, repo_root)
    if rel_path == '.':
        return False
        
    parts = rel_path.split(os.sep)
    
    # Always ignore system, IDE, and tool-specific directories
    ignored_names = {'.git', '.github', '.idea', '.DS_Store', 'node_modules'}
    for part in parts:
        if part in ignored_names:
            return True
            
    # Check against gitignore patterns
    for pattern, is_dir_pattern in gitignore_patterns:
        for i in range(len(parts)):
            subpath = os.sep.join(parts[:i+1])
            # Match either the full relative subpath or the individual part
            if fnmatch.fnmatch(subpath, pattern) or fnmatch.fnmatch(parts[i], pattern):
                if is_dir_pattern:
                    if os.path.isdir(os.path.join(repo_root, subpath)):
                        return True
                else:
                    return True
    return False

def is_template_skill(file_path):
    """
    Checks if a SKILL.md file is a template rather than a concrete skill.
    Identifies template-specific frontmatter or placeholder markers.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # File is too short to be a real skill
        if len(content.strip()) < 100:
            return True
            
        # Common patterns used for template placeholders
        placeholders = [
            r'\[\s*skill\s*name\s*\]',
            r'\[\s*your-skill-name\s*\]',
            r'<\s*your-skill-name\s*>',
            r'\[\s*insert\s+[^\]]+\]',
            r'<\s*insert\s+[^>]+>',
            r'\[\s*describe\s+[^\]]+\]',
            r'name:\s*skill-template',
            r'name:\s*template-skill',
            r'name:\s*template\b',
        ]
        
        for pattern in placeholders:
            if re.search(pattern, content, re.IGNORECASE):
                return True
                
        # Look for explicit generic placeholder instructions
        if "[Detailed instructions" in content or "your-skill-name" in content:
            return True
            
        return False
    except Exception as e:
        print(f"Warning: Failed to read {file_path}: {e}")
        return True

def get_symlink_name(rel_path):
    """
    Generates a symlink name based on the naming convention:
    android(first section of the first folder)-(secondfolder)-name of skills
    
    Special handling:
    - Skips "skills" subfolder in the path to avoid redundancy
    - Removes duplicate prefix if skill name starts with the same word
    
    Examples:
      android-official-skills/jetpack-compose/adaptive -> android-jetpack-compose-adaptive
      compose-performance-skills/stability/stabilizing-compose-types -> compose-stability-stabilizing-compose-types
      anthropics-skills/skills/theme-factory -> anthropics-theme-factory (skips "skills")
      kotlin-official-skills/skills/kotlin-tooling-agp9-migration -> kotlin-tooling-agp9-migration (removes duplicate "kotlin")
      optimize-prompt -> optimize-prompt
    """
    parts = rel_path.split(os.sep)
    if not parts:
        return ""
        
    if len(parts) == 1:
        return parts[0]
        
    first_folder = parts[0]
    first_section = first_folder.split('-')[0]
    
    middle_folders = parts[1:-1]
    # Filter out "skills" subfolder to avoid redundancy
    middle_folders = [folder for folder in middle_folders if folder.lower() != "skills"]
    
    last_folder = parts[-1]
    
    # Check if the last folder starts with the first section
    # If so, don't include the first section to avoid duplication
    last_folder_parts = last_folder.split('-')
    if last_folder_parts[0].lower() == first_section.lower():
        # The skill name already starts with the prefix, skip the first section
        name_parts = middle_folders + [last_folder]
    else:
        # Normal case: include first section
        name_parts = [first_section] + middle_folders + [last_folder]
    
    return '-'.join(name_parts)

def remove_link(link_path):
    """Safely removes a link (symlink or junction) on any platform."""
    try:
        if os.path.islink(link_path) or os.path.lexists(link_path):
            if os.path.isdir(link_path):
                # On Windows, directory junctions/symlinks must be removed with os.rmdir
                os.rmdir(link_path)
            else:
                os.remove(link_path)
            return True
    except OSError:
        try:
            os.remove(link_path)
            return True
        except OSError:
            pass
    return False

def create_link(target_abs, link_abs, dry_run=False):
    """
    Creates a directory symlink or Windows directory junction at link_abs pointing to target_abs.
    Calculates and uses a relative path for the symlink when possible to keep it portable.
    """
    link_dir = os.path.dirname(link_abs)
    target_rel = os.path.relpath(target_abs, link_dir)
    
    if dry_run:
        return True, "dry-run"

    # Remove any existing link/file at the path
    remove_link(link_abs)
            
    try:
        # Standard relative symlink
        os.symlink(target_rel, link_abs, target_is_directory=True)
        return True, "symlink"
    except OSError:
        # Fallback for Windows if Developer Mode is not enabled (requires absolute path for junction)
        if platform.system() == "Windows":
            try:
                cmd = ["cmd", "/c", "mklink", "/J", os.path.normpath(link_abs), os.path.normpath(target_abs)]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return True, "junction"
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                return False, str(e)
        else:
            return False, "Failed to create symlink"

def update_gitignore(repo_root, active_symlinks, dry_run=False):
    """Updates .gitignore file with the list of generated symlinks."""
    gitignore_path = os.path.join(repo_root, ".gitignore")
    start_marker = "# BEGIN GENERATED SKILL SYMLINKS"
    end_marker = "# END GENERATED SKILL SYMLINKS"
    
    content = ""
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Failed to read .gitignore for updating: {e}")
            return
            
    # Clean up any reference to flat_skills/ since we don't use it anymore
    if "flat_skills/" in content:
        content = content.replace("flat_skills/\n", "").replace("flat_skills/", "")
        
    pattern = re.compile(rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}\n?", re.DOTALL)
    
    if not active_symlinks:
        # If there are no active symlinks, we remove the block entirely
        if pattern.search(content):
            new_content = pattern.sub("", content)
        else:
            new_content = content
    else:
        # Prepare the list of symlinks sorted alphabetically
        symlink_lines = [start_marker] + sorted(list(active_symlinks)) + [end_marker]
        symlink_block = "\n".join(symlink_lines) + "\n"
        
        # Check if markers already exist
        if pattern.search(content):
            new_content = pattern.sub(symlink_block, content)
        else:
            # Append to the end of the file
            if content and not content.endswith("\n"):
                content += "\n"
            new_content = content + symlink_block
            
    if dry_run:
        if not active_symlinks:
            print("[DRY-RUN] Would remove generated symlink block from .gitignore.")
        else:
            print(f"[DRY-RUN] Would update .gitignore with {len(active_symlinks)} symlink entries.")
    else:
        try:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            if not active_symlinks:
                print("[+] Removed generated symlink block from .gitignore.")
            else:
                print("[+] Updated .gitignore with generated symlinks.")
        except Exception as e:
            print(f"Error: Failed to write to .gitignore: {e}")

def get_agent_paths():
    home = os.path.expanduser("~")
    system = platform.system()
    
    agents_map = {
        "claude code": [os.path.join(home, ".claude", "skills")],
        "gemini": [os.path.join(home, ".gemini", "config", "skills")],
        "antigravity": [
            os.path.join(home, ".agent", "skills"),
            os.path.join(home, ".agents", "skills")
        ],
        "kilocode": [
            os.path.join(home, ".kilocode", "globalStorage", "kilo code.kilo-code", "skills"),
            os.path.join(home, ".kilocode", "skills"),
            os.path.join(home, ".kilo", "skills")
        ],
        "opencode": [os.path.join(home, ".opencode", "skills")],
        "qwencode": [
            os.path.join(home, ".qwencode", "skills"),
            os.path.join(home, ".qwen", "skills")
        ],
        "aionui": [
            os.path.join(home, "Library", "Application Support", "AionUi", "config", "skills") if system == "Darwin" else
            os.path.join(os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming")), "AionUi", "config", "skills") if system == "Windows" else
            os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(home, ".config")), "AionUi", "config", "skills")
        ],
        "kiro": [os.path.join(home, ".kiro", "skills")]
    }
    return agents_map

def interactive_agent_selection(agents, agent_status):
    """
    Interactive checkbox-style selection using keyboard controls.
    Returns a list of selected agent names.
    """
    import sys
    import tty
    import termios
    
    # Check if we're in a TTY (terminal with keyboard input)
    if not sys.stdin.isatty():
        print("Not running in interactive terminal. Using fallback selection.")
        return fallback_agent_selection(agents, agent_status)
    
    selections = {agent: False for agent in agents}
    current_index = 0
    
    def get_char():
        """Read a single character from stdin."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            char = sys.stdin.read(1)
            # Handle escape sequences (arrow keys)
            if char == '\x1b':
                char += sys.stdin.read(2)
            return char
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def display_menu():
        """Display the selection menu."""
        # Clear screen and move cursor to top
        print("\033[2J\033[H", end='')
        
        print("=" * 60)
        print("Select agents to configure (use arrow keys to navigate):")
        print("=" * 60)
        print("Controls:")
        print("  ↑/↓ or k/j  : Move selection")
        print("  SPACE       : Toggle checkbox")
        print("  a           : Select all")
        print("  c           : Clear all selections")
        print("  ENTER       : Confirm and continue")
        print("  q or ESC    : Cancel")
        print("=" * 60)
        print()
        
        for i, agent in enumerate(agents):
            status, _ = agent_status[agent]
            checkbox = "[✓]" if selections[agent] else "[ ]"
            cursor = "→ " if i == current_index else "  "
            highlight = "\033[1;36m" if i == current_index else ""
            reset = "\033[0m" if i == current_index else ""
            print(f"{cursor}{highlight}{checkbox} {agent:<15} ({status}){reset}")
        
        print()
        selected_count = sum(selections.values())
        print(f"Selected: {selected_count} agent(s)")
    
    # Main interaction loop
    try:
        while True:
            display_menu()
            
            char = get_char()
            
            # Handle arrow keys and vim-style navigation
            if char == '\x1b[A' or char == 'k':  # Up arrow or k
                current_index = (current_index - 1) % len(agents)
            elif char == '\x1b[B' or char == 'j':  # Down arrow or j
                current_index = (current_index + 1) % len(agents)
            elif char == ' ':  # Space - toggle current selection
                current_agent = agents[current_index]
                selections[current_agent] = not selections[current_agent]
            elif char == 'a':  # Select all
                for agent in agents:
                    selections[agent] = True
            elif char == 'c':  # Clear all
                for agent in agents:
                    selections[agent] = False
            elif char == '\r' or char == '\n':  # Enter - confirm
                break
            elif char == 'q' or char == '\x1b':  # q or ESC - cancel
                print("\nCancelled.")
                return []
            elif char == '\x03':  # Ctrl+C
                print("\nCancelled.")
                return []
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return []
    
    # Return list of selected agents
    return [agent for agent in agents if selections[agent]]

def fallback_agent_selection(agents, agent_status):
    """
    Fallback selection method for non-interactive terminals.
    Uses simple text input.
    """
    print("Select the agents you want to configure:")
    for i, agent in enumerate(agents, 1):
        status, _ = agent_status[agent]
        print(f"  {i}) [ ] {agent:<15} ({status})")
        
    print("\nEnter numbers separated by commas (e.g. 1,3,5), 'all' to select all, or press Enter to skip:")
    try:
        user_input = input("> ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nSkipping agent links setup.")
        return []
        
    if not user_input:
        print("Skipping agent links setup.")
        return []
        
    selected_indices = []
    if user_input == "all":
        selected_indices = list(range(len(agents)))
    else:
        for val in user_input.split(","):
            val = val.strip()
            if val.isdigit():
                idx = int(val) - 1
                if 0 <= idx < len(agents):
                    selected_indices.append(idx)
                    
    if not selected_indices:
        print("No valid agents selected. Skipping.")
        return []
        
    return [agents[idx] for idx in selected_indices]

def setup_agent_links(repo_root, all_skill_folders, dry_run=False, auto_select_all=False):
    import time
    agents_map = get_agent_paths()
    
    print("\n" + "=" * 60)
    print("AI Agent Global Skills Symlink Setup")
    print("=" * 60)
    print("This utility can link this repository to the global skills directory of your AI agents.")
    print("When linked, the agent will automatically discover all the skills in this repository.")
    print("=" * 60)
    
    # For agent installation, include all skill folders except 'cooking'
    agent_skills = {name: path for name, path in all_skill_folders.items() if name != "cooking"}
    
    if not dry_run:
        print(f"\nPreparing to copy {len(agent_skills)} skills to agents")
        print(f"  (Excluding 'cooking' folder if present)")
        print(f"  Skills will be copied as actual directories")
    
    agent_status = {}
    ordered_agents = ["claude code", "gemini", "antigravity", "kilocode", "opencode", "qwencode", "aionui", "kiro"]
    
    for agent in ordered_agents:
        paths = agents_map.get(agent, [])
        linked_count = 0
        colliding_count = 0
        total_paths_checked = 0
        
        for p in paths:
            if os.path.exists(p) and os.path.isdir(p):
                total_paths_checked += 1
                for skill in agent_skills.keys():
                    skill_path = os.path.join(p, skill)
                    if os.path.exists(skill_path) or os.path.islink(skill_path):
                        if os.path.islink(skill_path):
                            try:
                                target = os.readlink(skill_path)
                                target_abs = os.path.abspath(os.path.join(os.path.dirname(skill_path), target))
                                # Check if target resolves inside repo_root
                                if target_abs.startswith(repo_root):
                                    linked_count += 1
                                else:
                                    colliding_count += 1
                            except OSError:
                                colliding_count += 1
                        else:
                            colliding_count += 1
                            
        if total_paths_checked == 0:
            status = "Not Created"
        elif agent_skills and linked_count == len(agent_skills) * total_paths_checked:
            status = "All Linked"
        elif linked_count > 0 or colliding_count > 0:
            parts = []
            if linked_count > 0:
                parts.append(f"{linked_count} Linked")
            if colliding_count > 0:
                parts.append(f"{colliding_count} Colliding")
            status = f"Partial ({', '.join(parts)})"
        else:
            status = "Exists (Folder)"
            
        agent_status[agent] = (status, paths)
        
    # Agent selection (automatic or interactive)
    if auto_select_all:
        selected_agents = [agent for agent in ordered_agents if agent_status[agent][0] != "Not Created"]
        print(f"Auto-selected active agents: {', '.join(selected_agents)}")
    else:
        selected_agents = interactive_agent_selection(ordered_agents, agent_status)
    
    if not selected_agents:
        print("No agents selected. Skipping agent links setup.")
        return
        
    print(f"\nYou selected: {', '.join(selected_agents)}")
    
    print("\n" + "!" * 60)
    print("DISCLAIMER / WARNING:")
    print("This operation will symlink the individual skills from this repository")
    print("into the global 'skills' directory of the selected agent(s):")
    print(f"  Target Repository: {repo_root}")
    print("If any of these skills already exist in the agent's folder, they will be replaced.")
    print("!" * 60)
    
    if auto_select_all:
        do_backup = True
    else:
        try:
            backup_input = input("\nDo you want to backup any colliding skill folders into .bak files first? (y/n) [y]: ").strip().lower()
            do_backup = backup_input != 'n'
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            return
        
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    for agent in selected_agents:
        status, paths = agent_status[agent]
        print(f"\nConfiguring {agent}...")
        
        for p in paths:
            p_dir = os.path.dirname(p)
            
            # If the folder itself is a symlink (legacy behavior), remove it and make it a real directory
            if os.path.islink(p):
                print(f"  [-] Removing legacy agent folder symlink: {p}")
                if not dry_run:
                    remove_link(p)
                    os.makedirs(p, exist_ok=True)
            elif not os.path.exists(p):
                print(f"  [+] Creating agent skills folder: {p}")
                if not dry_run:
                    os.makedirs(p, exist_ok=True)
            
            # Copy each individual skill
            for skill_name, skill_src in agent_skills.items():
                skill_dest = os.path.join(p, skill_name)
                
                if os.path.exists(skill_dest):
                    # Check if it's already a directory (from previous copy)
                    if os.path.isdir(skill_dest) and not os.path.islink(skill_dest):
                        # Already exists as a directory, skip or update
                        continue
                    
                    # Collision!
                    print(f"  [!] Collision: Skill '{skill_name}' already exists in {p}")
                    if do_backup and not os.path.islink(skill_dest):
                        backup_base = f"{skill_dest}_{timestamp}.bak"
                        print(f"    [*] Backing up existing skill to {backup_base}.bak...")
                        if not dry_run:
                            try:
                                if os.path.isdir(skill_dest):
                                    zip_file = shutil.make_archive(backup_base, 'zip', skill_dest)
                                    bak_file = backup_base + ".bak"
                                    if os.path.exists(bak_file):
                                        os.remove(bak_file)
                                    os.rename(zip_file, bak_file)
                                    print(f"    [+] Backup created: {bak_file}")
                                else:
                                    bak_file = backup_base + ".bak"
                                    shutil.copy2(skill_dest, bak_file)
                                    print(f"    [+] Backup created: {bak_file}")
                            except Exception as e:
                                print(f"    [!] Failed to create backup: {e}")
                                print("    [!] Skipping this skill to prevent data loss.")
                                continue
                                
                    print(f"    [-] Removing existing skill: {skill_dest}")
                    if not dry_run:
                        try:
                            if os.path.islink(skill_dest):
                                remove_link(skill_dest)
                            elif os.path.isdir(skill_dest):
                                shutil.rmtree(skill_dest)
                            else:
                                os.remove(skill_dest)
                        except Exception as e:
                            print(f"    [!] Failed to remove existing skill: {e}")
                            continue
                
                # Copy the directory
                print(f"  [+] Copying: {skill_name} <- {os.path.relpath(skill_src, repo_root)}")
                if not dry_run:
                    try:
                        shutil.copytree(skill_src, skill_dest, symlinks=False, ignore=shutil.ignore_patterns('.git', '.DS_Store', '__pycache__', '*.pyc'))
                        print(f"    [✓] Copied successfully!")
                    except Exception as e:
                        print(f"    [!] Failed to copy: {e}")

def main():
    # Parse arguments
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    clean_mode = "--clean" in sys.argv or "-c" in sys.argv
    
    repo_root = os.path.abspath(os.path.dirname(__file__))
    
    # Handle clean mode immediately
    if clean_mode:
        print("=" * 60)
        if dry_run:
            print("RUNNING IN DRY-RUN MODE (No changes will be written)")
            print("=" * 60)
        print("Cleaning up all generated symlinks...")
        print("=" * 60)
        
        cleaned_count = 0
        for item in os.listdir(repo_root):
            item_path = os.path.join(repo_root, item)
            if os.path.islink(item_path):
                try:
                    target = os.readlink(item_path)
                    target_abs = os.path.abspath(os.path.join(repo_root, target))
                    is_internal = target_abs.startswith(repo_root) and target_abs != repo_root
                except OSError:
                    is_internal = False
                    
                if is_internal:
                    if dry_run:
                        print(f"[DRY-RUN] Would remove symlink: {item}")
                        cleaned_count += 1
                    else:
                        if remove_link(item_path):
                            print(f"[x] Removed symlink: {item}")
                            cleaned_count += 1
                        else:
                            print(f"[!] Failed to remove symlink: {item}")
                            
        # Also clean up legacy flat_skills directory if it exists
        legacy_dir = os.path.join(repo_root, "flat_skills")
        if os.path.exists(legacy_dir):
            if dry_run:
                print("[DRY-RUN] Would remove legacy flat_skills/ directory.")
            else:
                try:
                    shutil.rmtree(legacy_dir)
                    print("[+] Removed legacy flat_skills/ directory.")
                except Exception as e:
                    print(f"[!] Warning: Failed to remove legacy flat_skills/ directory: {e}")
        # Clean up agent symlinks if any
        agents_map = get_agent_paths()
        agent_cleaned_count = 0
        for agent, paths in agents_map.items():
            for p in paths:
                # Check if the folder itself is a symlink pointing to repo_root (legacy compatibility)
                if os.path.islink(p):
                    try:
                        target = os.readlink(p)
                        target_abs = os.path.abspath(os.path.join(os.path.dirname(p), target))
                        if target_abs == repo_root:
                            if dry_run:
                                print(f"[DRY-RUN] Would remove agent folder symlink: {p}")
                                agent_cleaned_count += 1
                            else:
                                if remove_link(p):
                                    print(f"[x] Removed agent folder symlink: {p}")
                                    agent_cleaned_count += 1
                                else:
                                    print(f"[!] Failed to remove agent folder symlink: {p}")
                    except OSError:
                        pass
                # Otherwise, if it's a directory, clean up individual skill symlinks inside it
                elif os.path.exists(p) and os.path.isdir(p):
                    try:
                        for item in os.listdir(p):
                            item_path = os.path.join(p, item)
                            if os.path.islink(item_path):
                                target = os.readlink(item_path)
                                target_abs = os.path.abspath(os.path.join(p, target))
                                # Use case-insensitive comparison for macOS compatibility
                                if target_abs.lower().startswith(repo_root.lower()):
                                    if dry_run:
                                        print(f"[DRY-RUN] Would remove agent skill symlink: {item_path}")
                                        agent_cleaned_count += 1
                                    else:
                                        if remove_link(item_path):
                                            print(f"[x] Removed agent skill symlink: {item_path}")
                                            agent_cleaned_count += 1
                                        else:
                                            print(f"[!] Failed to remove agent skill symlink: {item_path}")
                    except Exception as e:
                        print(f"[!] Error scanning {p} for cleanup: {e}")
                        
        update_gitignore(repo_root, set(), dry_run=dry_run)
        
        print("=" * 60)
        print("Cleanup Summary:")
        if dry_run:
            print(f"  Local links to remove: {cleaned_count}")
            print(f"  Agent links to remove: {agent_cleaned_count}")
        else:
            print(f"  Local links removed:   {cleaned_count}")
            print(f"  Agent links removed:   {agent_cleaned_count}")
        print("=" * 60)
        sys.exit(0)
        
    # Read .gitignore patterns
    gitignore_path = os.path.join(repo_root, ".gitignore")
    gitignore_patterns = parse_gitignore(gitignore_path)
    
    print("=" * 60)
    if dry_run:
        print("RUNNING IN DRY-RUN MODE (No changes will be written)")
        print("=" * 60)
    print("Scanning repository for skills...")
    print("=" * 60)
    
    # Scan for all SKILL.md files
    skills_found = []
    for root, dirs, files in os.walk(repo_root):
        # Filter dirs in-place to avoid traversing ignored directories and existing symlinks
        dirs[:] = [
            d for d in dirs 
            if not os.path.islink(os.path.join(root, d)) 
            and not is_ignored(os.path.join(root, d), gitignore_patterns, repo_root)
        ]
        
        for file in files:
            if file.upper() == "SKILL.MD":
                file_path = os.path.join(root, file)
                parent_dir = os.path.dirname(file_path)
                
                # Check if this file itself is in an ignored folder
                if is_ignored(parent_dir, gitignore_patterns, repo_root):
                    continue
                    
                skills_found.append((parent_dir, file_path))
                
    if not skills_found:
        print("No SKILL.md files found in the project.")
        sys.exit(0)
        
    print(f"Found {len(skills_found)} SKILL.md file(s). Evaluating...")
    
    all_skill_folders = {}  # Map skill name to source path
    templates_skipped = 0
    
    for skill_dir, skill_file in skills_found:
        rel_skill_dir = os.path.relpath(skill_dir, repo_root)
        
        # Check if it's a template
        if is_template_skill(skill_file):
            print(f"[-] Skipping template: {rel_skill_dir}")
            templates_skipped += 1
            continue
            
        # Determine skill name
        path_parts = rel_skill_dir.split(os.sep)
        if len(path_parts) == 1:
            # Root-level skill
            skill_name = rel_skill_dir
        else:
            # Nested skill - generate flattened name
            skill_name = get_symlink_name(rel_skill_dir)
        
        if not skill_name:
            continue
            
        all_skill_folders[skill_name] = skill_dir
        print(f"[✓] Found skill: {skill_name} ({rel_skill_dir})")
    
    print("=" * 60)
    print("Scan Summary:")
    print(f"  Total SKILL.md found:  {len(skills_found)}")
    print(f"  Templates skipped:     {templates_skipped}")
    print(f"  Valid skills:          {len(all_skill_folders)}")
    print(f"\n  Skills available for agent installation: {len(all_skill_folders)}")
    print(f"  (All skills except 'cooking')")
    print("=" * 60)

    # Prompt user to link global agent skill directories if running interactively
    if sys.stdin.isatty() and not ("--non-interactive" in sys.argv or "--yes" in sys.argv):
        setup_agent_links(repo_root, all_skill_folders, dry_run=dry_run)
    elif "--yes" in sys.argv or "--non-interactive" in sys.argv:
        setup_agent_links(repo_root, all_skill_folders, dry_run=dry_run, auto_select_all=True)

if __name__ == "__main__":
    main()
