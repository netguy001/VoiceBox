"""
Fixed Tools Module - Full Windows Control
All critical issues resolved:
✅ File operations work correctly
✅ Better parameter parsing
✅ Enhanced error handling
✅ Improved file system access
✅ Better app launching
"""

import os
import subprocess
import shutil
from pathlib import Path
import webbrowser
import platform
import psutil
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import urllib.parse
import re


class ToolBox:
    """Enhanced toolbox with full Windows control"""

    def __init__(self):
        self.tools = {
            # Web tools
            "web_search": self.web_search,
            "google_search": self.google_search,
            "get_current_time": self.get_current_time,
            "get_current_date": self.get_current_date,
            "fetch_webpage": self.fetch_webpage,
            "open_url": self.open_url,
            # File tools - FIXED
            "read_file": self.read_file,
            "write_file": self.write_file,
            "create_file": self.write_file,
            "append_to_file": self.append_to_file,
            "list_files": self.list_files,
            "delete_file": self.delete_file,
            "move_file": self.move_file,
            "rename_file": self.rename_file,
            "create_folder": self.create_folder,
            "search_files": self.search_files,
            "get_file_info": self.get_file_info,
            "find_all_files": self.find_all_files,
            # Windows-specific tools
            "open_app": self.open_windows_app,
            "list_installed_apps": self.list_installed_apps,
            "get_quick_access": self.get_quick_access_folders,
            # System tools
            "run_command": self.run_command,
            "system_info": self.system_info,
            "execute_python": self.execute_python,
            # Utility tools
            "calculate": self.calculate,
        }

    def get_tool_descriptions(self):
        """Return formatted tool descriptions"""
        return """
WEB TOOLS:
- web_search(query): Search DuckDuckGo
- google_search(query): Search Google
- get_current_time(): Current time
- get_current_date(): Current date
- fetch_webpage(url): Read webpage content
- open_url(url): Open URL in browser

FILE TOOLS (FULL PC ACCESS):
- write_file(filepath, content): Create/overwrite file
- create_file(filepath, content): Same as write_file
- read_file(filepath): Read file contents
- append_to_file(filepath, content): Add to file
- list_files(directory): List files in folder
- delete_file(filepath): Delete a file
- move_file(source, destination): Move file
- rename_file(filepath, new_name): Rename file
- create_folder(path): Create new folder
- search_files(directory, pattern): Search by name
- find_all_files(filename): Search entire PC
- get_file_info(filepath): Get file details

WINDOWS TOOLS:
- open_app(app_name): Open Windows application
- list_installed_apps(): List installed programs
- get_quick_access(): Show user folders

SYSTEM TOOLS:
- run_command(command): Execute Windows command
- system_info(): Get PC information
- execute_python(code): Run Python code

UTILITY:
- calculate(expression): Math calculations
"""

    def execute_tool(self, tool_name, params):
        """Execute a tool with enhanced error handling"""
        try:
            if tool_name not in self.tools:
                return {
                    "success": False,
                    "output": f"Tool '{tool_name}' not found. Available: {', '.join(list(self.tools.keys())[:10])}...",
                }

            tool_func = self.tools[tool_name]

            # Ensure params is a list
            if not isinstance(params, list):
                params = [params] if params else []

            # Clean parameters - remove empty strings
            params = [p for p in params if p != ""]

            print(
                f"🔧 Executing: {tool_name}({', '.join([str(p)[:50] for p in params])})"
            )

            # Call the tool
            result = tool_func(*params)

            return {"success": True, "output": result}

        except TypeError as e:
            import inspect

            sig = inspect.signature(self.tools[tool_name])
            expected_params = list(sig.parameters.keys())
            return {
                "success": False,
                "output": f"❌ {tool_name} expects {len(expected_params)} parameter(s): {expected_params}. Got {len(params)}. Error: {str(e)}",
            }
        except Exception as e:
            import traceback

            return {
                "success": False,
                "output": f"❌ {tool_name} failed: {str(e)}\n{traceback.format_exc()[:300]}",
            }

    # ========== WEB TOOLS ==========

    def google_search(self, query):
        """Search Google with better parsing"""
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            results = []

            # Try multiple selectors for better results
            for g in soup.find_all("div", class_="g")[:6]:
                title_elem = g.find("h3")
                if not title_elem:
                    continue

                title = title_elem.get_text()

                # Try multiple snippet selectors
                snippet = ""
                for class_name in ["VwiC3b", "yXK7lf", "s", "st"]:
                    snippet_elem = g.find("div", class_=class_name)
                    if snippet_elem:
                        snippet = snippet_elem.get_text()
                        break

                link_elem = g.find("a")
                link = link_elem["href"] if link_elem else ""

                if title:
                    results.append(
                        {"title": title, "snippet": snippet[:200], "link": link}
                    )

            if results:
                output = f"🔍 Google Results for '{query}':\n\n"
                for i, r in enumerate(results, 1):
                    output += f"{i}. {r['title']}\n"
                    if r["snippet"]:
                        output += f"   {r['snippet']}\n"
                    if r["link"]:
                        output += f"   🔗 {r['link']}\n"
                    output += "\n"
                return output
            else:
                return self.web_search(query)

        except Exception as e:
            print(f"Google search error: {e}")
            return self.web_search(query)

    def web_search(self, query):
        """Fallback DuckDuckGo search"""
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0"}

            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            results = []
            for result in soup.find_all("div", class_="result")[:6]:
                title_elem = result.find("a", class_="result__a")
                snippet_elem = result.find("a", class_="result__snippet")

                if title_elem:
                    title = title_elem.text.strip()
                    snippet = snippet_elem.text.strip() if snippet_elem else ""
                    link = title_elem.get("href", "")
                    results.append({"title": title, "snippet": snippet, "link": link})

            if results:
                output = f"🔍 Search Results for '{query}':\n\n"
                for i, r in enumerate(results, 1):
                    output += f"{i}. {r['title']}\n"
                    if r["snippet"]:
                        output += f"   {r['snippet'][:150]}\n"
                    output += "\n"
                return output
            else:
                return f"No results found for '{query}'"

        except Exception as e:
            return f"Search failed: {str(e)}"

    def fetch_webpage(self, url):
        """Fetch webpage content"""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove unwanted elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            text = "\n".join(line for line in lines if line)

            if len(text) > 4000:
                text = text[:4000] + "\n\n... (truncated)"

            return f"📄 Content from {url}:\n\n{text}"

        except Exception as e:
            return f"Failed to fetch: {str(e)}"

    def get_current_time(self):
        """Get current time"""
        now = datetime.now()
        return now.strftime("Current time: %I:%M %p on %A, %B %d, %Y")

    def get_current_date(self):
        """Get current date"""
        now = datetime.now()
        return now.strftime("Today is %A, %B %d, %Y")

    def open_url(self, url):
        """Open URL in browser"""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
            return f"✅ Opened {url}"
        except Exception as e:
            return f"Failed: {str(e)}"

    # ========== FIXED FILE TOOLS ==========

    def read_file(self, filepath):
        """Read file contents - FIXED"""
        try:
            # Expand user paths
            if filepath.startswith("~"):
                filepath = os.path.expanduser(filepath)

            path = Path(filepath).resolve()

            if not path.exists():
                # Try to find similar files
                parent = path.parent
                if parent.exists():
                    similar = [
                        f.name
                        for f in parent.iterdir()
                        if path.stem.lower() in f.name.lower()
                    ]
                    if similar:
                        return f"❌ File not found: {filepath}\n💡 Similar files: {', '.join(similar[:5])}"
                return f"❌ File not found: {filepath}"

            # Check file size
            if path.stat().st_size > 2_000_000:
                return f"❌ File too large (>2MB): {filepath}"

            # Try reading with multiple encodings
            for encoding in ["utf-8", "latin-1", "cp1252", "utf-16"]:
                try:
                    with open(path, "r", encoding=encoding) as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            else:
                return f"❌ Could not decode file: {filepath}"

            # Truncate if very long
            if len(content) > 5000:
                content = content[:5000] + "\n\n... (truncated, file has more content)"

            return f"📄 {filepath}:\n\n{content}"

        except Exception as e:
            return f"❌ Failed to read: {str(e)}"

    def write_file(self, filepath, content=""):
        """Write/create file - COMPLETELY FIXED"""
        try:
            # Expand user paths
            if filepath.startswith("~"):
                filepath = os.path.expanduser(filepath)

            path = Path(filepath).resolve()

            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)

            # Ensure content is string
            if content is None:
                content = ""
            content = str(content)

            # Write file
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            # Get file info
            size = len(content)
            lines = content.count("\n") + 1
            preview = content[:100].replace("\n", " ")[:50]

            return f"✅ Created: {path}\n📊 Size: {size} chars, {lines} lines\n👁 Preview: {preview}..."

        except Exception as e:
            import traceback

            return f"❌ Failed to write: {str(e)}\n{traceback.format_exc()[:200]}"

    def append_to_file(self, filepath, content):
        """Append to existing file - FIXED"""
        try:
            if filepath.startswith("~"):
                filepath = os.path.expanduser(filepath)

            path = Path(filepath).resolve()

            if not path.exists():
                return f"❌ File not found: {filepath}\n💡 Use write_file to create it first"

            # Ensure content is string
            content = str(content)

            with open(path, "a", encoding="utf-8") as f:
                f.write(content)

            return f"✅ Appended {len(content)} characters to {filepath}"

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def list_files(self, directory="."):
        """List files in directory - ENHANCED"""
        try:
            # Handle special paths
            if directory == "~":
                directory = str(Path.home())
            elif directory.startswith("~"):
                directory = os.path.expanduser(directory)

            path = Path(directory).resolve()

            if not path.exists():
                # Suggest common folders
                suggestions = [
                    str(Path.home()),
                    str(Path.home() / "Documents"),
                    str(Path.home() / "Downloads"),
                    str(Path.home() / "Desktop"),
                    str(Path.cwd()),
                ]
                return f"❌ Directory not found: {directory}\n💡 Try: {', '.join(suggestions[:3])}"

            if not path.is_dir():
                return f"❌ Not a directory: {directory}"

            files = []
            folders = []

            try:
                for item in sorted(path.iterdir()):
                    try:
                        if item.is_file():
                            size = self._format_size(item.stat().st_size)
                            modified = datetime.fromtimestamp(
                                item.stat().st_mtime
                            ).strftime("%Y-%m-%d")
                            files.append(f"   📄 {item.name} ({size}, {modified})")
                        elif item.is_dir():
                            folders.append(f"   📁 {item.name}/")
                    except (PermissionError, OSError):
                        continue
            except PermissionError:
                return f"❌ Permission denied: {directory}"

            output = f"📂 {path}:\n\n"

            if folders:
                output += "Folders:\n" + "\n".join(folders[:40]) + "\n\n"

            if files:
                output += "Files:\n" + "\n".join(files[:40])

            total = len(files) + len(folders)
            if total > 40:
                output += f"\n\n... and {total - 40} more items"
            elif total == 0:
                output += "Empty directory"

            return output

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def rename_file(self, filepath, new_name):
        """Rename a file - FIXED"""
        try:
            if filepath.startswith("~"):
                filepath = os.path.expanduser(filepath)

            src = Path(filepath).resolve()

            if not src.exists():
                return f"❌ File not found: {filepath}"

            # If new_name is full path, use it; otherwise put in same directory
            if "/" in new_name or "\\" in new_name:
                dst = Path(new_name).resolve()
            else:
                dst = src.parent / new_name

            src.rename(dst)
            return f"✅ Renamed: {src.name} → {dst.name}"

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def delete_file(self, filepath):
        """Delete a file - FIXED"""
        try:
            if filepath.startswith("~"):
                filepath = os.path.expanduser(filepath)

            path = Path(filepath).resolve()

            if not path.exists():
                return f"❌ File not found: {filepath}"

            if path.is_file():
                path.unlink()
                return f"✅ Deleted: {filepath}"
            elif path.is_dir():
                return f"❌ Cannot delete directory with delete_file. Use system command or manually delete: {filepath}"
            else:
                return f"❌ Not a file: {filepath}"

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def move_file(self, source, destination):
        """Move a file - FIXED"""
        try:
            if source.startswith("~"):
                source = os.path.expanduser(source)
            if destination.startswith("~"):
                destination = os.path.expanduser(destination)

            src = Path(source).resolve()
            dst = Path(destination).resolve()

            if not src.exists():
                return f"❌ Source not found: {source}"

            # If destination is directory, keep original filename
            if dst.is_dir():
                dst = dst / src.name

            shutil.move(str(src), str(dst))
            return f"✅ Moved: {source} → {destination}"

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def create_folder(self, path):
        """Create a new folder - FIXED"""
        try:
            if path.startswith("~"):
                path = os.path.expanduser(path)

            folder = Path(path).resolve()
            folder.mkdir(parents=True, exist_ok=True)
            return f"✅ Created folder: {folder}"
        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def search_files(self, directory, pattern):
        """Search for files in directory"""
        try:
            if directory.startswith("~"):
                directory = os.path.expanduser(directory)

            path = Path(directory).resolve()

            if not path.exists():
                return f"❌ Directory not found: {directory}"

            matches = list(path.rglob(pattern))[:50]

            if not matches:
                return f"No files matching '{pattern}' in {directory}"

            output = f"🔍 Found {len(matches)} file(s) matching '{pattern}':\n\n"
            for i, match in enumerate(matches[:30], 1):
                try:
                    rel_path = match.relative_to(path)
                except:
                    rel_path = match
                size = (
                    self._format_size(match.stat().st_size)
                    if match.is_file()
                    else "folder"
                )
                output += f"{i}. {rel_path} ({size})\n"

            if len(matches) > 30:
                output += f"\n... and {len(matches) - 30} more"

            return output

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def find_all_files(self, filename):
        """Search entire PC for a file"""
        try:
            print(f"🔍 Searching PC for '{filename}'...")
            results = []

            # Search common locations
            search_paths = [
                Path.home(),
                Path("C:/Users"),
                Path("C:/Program Files"),
                Path("C:/Program Files (x86)"),
            ]

            for search_path in search_paths:
                if not search_path.exists():
                    continue

                try:
                    for item in search_path.rglob(f"*{filename}*"):
                        if len(results) >= 50:
                            break
                        try:
                            if item.is_file():
                                results.append(str(item))
                        except:
                            continue
                except:
                    continue

                if len(results) >= 50:
                    break

            if results:
                output = f"🔍 Found {len(results)} file(s) matching '{filename}':\n\n"
                for i, path in enumerate(results[:30], 1):
                    output += f"{i}. {path}\n"

                if len(results) > 30:
                    output += f"\n... and {len(results) - 30} more files"

                return output
            else:
                return f"❌ No files found matching '{filename}'"

        except Exception as e:
            return f"❌ Search failed: {str(e)}"

    def get_file_info(self, filepath):
        """Get detailed file info"""
        try:
            if filepath.startswith("~"):
                filepath = os.path.expanduser(filepath)

            path = Path(filepath).resolve()

            if not path.exists():
                return f"❌ File not found: {filepath}"

            stat = path.stat()

            info = [
                f"📄 File Information: {path}",
                f"",
                f"Type: {'File' if path.is_file() else 'Directory'}",
                f"Size: {self._format_size(stat.st_size)}",
                f"Created: {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}",
                f"Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
                f"Accessed: {datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')}",
            ]

            if path.is_file():
                suffix = path.suffix.lower()
                info.append(f"Extension: {suffix if suffix else 'None'}")

            return "\n".join(info)

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    # ========== WINDOWS TOOLS ==========

    def open_windows_app(self, app_name):
        """Open Windows application"""
        try:
            app_name_lower = app_name.lower()

            # Common Windows apps
            windows_apps = {
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "calc": "calc.exe",
                "explorer": "explorer.exe",
                "cmd": "cmd.exe",
                "command": "cmd.exe",
                "powershell": "powershell.exe",
                "paint": "mspaint.exe",
                "wordpad": "write.exe",
                "snipping": "SnippingTool.exe",
                "settings": "ms-settings:",
                "control": "control.exe",
                "taskmgr": "taskmgr.exe",
                "task": "taskmgr.exe",
            }

            # Check Windows built-in apps
            if app_name_lower in windows_apps:
                subprocess.Popen(windows_apps[app_name_lower], shell=True)
                return f"✅ Opening {app_name}..."

            # Try browsers
            browsers = {
                "chrome": [
                    "C:/Program Files/Google/Chrome/Application/chrome.exe",
                    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
                ],
                "firefox": [
                    "C:/Program Files/Mozilla Firefox/firefox.exe",
                    "C:/Program Files (x86)/Mozilla Firefox/firefox.exe",
                ],
                "edge": [
                    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
                ],
            }

            for browser_name, paths in browsers.items():
                if browser_name in app_name_lower:
                    for path in paths:
                        if os.path.exists(path):
                            subprocess.Popen([path])
                            return f"✅ Opening {browser_name}..."

            # Try Office apps
            office_apps = {
                "word": [
                    "C:/Program Files/Microsoft Office/root/Office16/WINWORD.EXE",
                    "C:/Program Files (x86)/Microsoft Office/root/Office16/WINWORD.EXE",
                ],
                "excel": [
                    "C:/Program Files/Microsoft Office/root/Office16/EXCEL.EXE",
                    "C:/Program Files (x86)/Microsoft Office/root/Office16/EXCEL.EXE",
                ],
                "powerpoint": [
                    "C:/Program Files/Microsoft Office/root/Office16/POWERPNT.EXE",
                    "C:/Program Files (x86)/Microsoft Office/root/Office16/POWERPNT.EXE",
                ],
            }

            for office_name, paths in office_apps.items():
                if office_name in app_name_lower:
                    for path in paths:
                        if os.path.exists(path):
                            subprocess.Popen([path])
                            return f"✅ Opening {office_name}..."

            # Try Windows 'start' command as fallback
            subprocess.Popen(["start", "", app_name], shell=True)
            return f"✅ Trying to open {app_name}..."

        except Exception as e:
            return f"❌ Failed to open {app_name}: {str(e)}"

    def list_installed_apps(self):
        """List some common installed applications"""
        try:
            apps = []

            # Check common installation directories
            program_paths = [
                Path("C:/Program Files"),
                Path("C:/Program Files (x86)"),
            ]

            for prog_path in program_paths:
                if prog_path.exists():
                    try:
                        for item in prog_path.iterdir():
                            if item.is_dir():
                                apps.append(item.name)
                    except PermissionError:
                        continue

            if apps:
                apps = sorted(set(apps))[:50]
                output = f"💻 Installed Applications ({len(apps)} shown):\n\n"
                for i, app in enumerate(apps, 1):
                    output += f"{i}. {app}\n"
                return output
            else:
                return "❌ Could not retrieve applications list"

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def get_quick_access_folders(self):
        """Get Windows quick access folders"""
        try:
            user_home = Path.home()

            folders = {
                "Home": str(user_home),
                "Desktop": str(user_home / "Desktop"),
                "Documents": str(user_home / "Documents"),
                "Downloads": str(user_home / "Downloads"),
                "Pictures": str(user_home / "Pictures"),
                "Videos": str(user_home / "Videos"),
                "Music": str(user_home / "Music"),
            }

            output = "📁 Quick Access Folders:\n\n"
            for name, path in folders.items():
                exists = "✅" if Path(path).exists() else "❌"
                output += f"{exists} {name}: {path}\n"

            return output

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    # ========== SYSTEM TOOLS ==========

    def run_command(self, command):
        """Execute Windows command"""
        try:
            # Safety check
            dangerous = ["rm -rf", "del /f /q /s", "format", "deltree"]
            if any(d in command.lower() for d in dangerous):
                return "❌ Blocked: Potentially dangerous command"

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=20,
                encoding="utf-8",
                errors="replace",
            )

            output = result.stdout if result.stdout else result.stderr

            if not output:
                output = "✅ Command executed (no output)"

            if len(output) > 2000:
                output = output[:2000] + "\n\n... (truncated)"

            return f"💻 Command output:\n{output}"

        except subprocess.TimeoutExpired:
            return "⏱️ Command timed out after 20 seconds"
        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def system_info(self):
        """Get system information"""
        try:
            info = []

            # System basics
            info.append(f"💻 System: {platform.system()} {platform.release()}")
            info.append(f"🖥️ Machine: {platform.machine()}")
            info.append(f"🏠 Computer: {platform.node()}")

            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            info.append(f"⚡ CPU: {cpu_count} cores, {cpu_percent}% usage")

            # Memory
            mem = psutil.virtual_memory()
            info.append(
                f"🧠 RAM: {self._format_size(mem.used)} / {self._format_size(mem.total)} ({mem.percent}%)"
            )

            # Disk
            disk = psutil.disk_usage("/")
            info.append(
                f"💾 Disk C: {self._format_size(disk.free)} free of {self._format_size(disk.total)} ({disk.percent}% used)"
            )

            # Time
            info.append(
                f"🕐 Time: {datetime.now().strftime('%I:%M %p on %A, %B %d, %Y')}"
            )

            return "\n".join(info)

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def execute_python(self, code):
        """Execute Python code safely"""
        try:
            # Restrict dangerous imports
            if any(
                dangerous in code
                for dangerous in [
                    "os.system",
                    "subprocess",
                    "eval",
                    "exec",
                    "__import__",
                ]
            ):
                return "❌ Blocked: Potentially dangerous code"

            # Create safe environment
            safe_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "sum": sum,
                    "max": max,
                    "min": min,
                }
            }

            # Capture output
            from io import StringIO
            import sys

            old_stdout = sys.stdout
            sys.stdout = StringIO()

            try:
                exec(code, safe_globals)
                output = sys.stdout.getvalue()
            finally:
                sys.stdout = old_stdout

            if not output:
                output = "✅ Code executed (no output)"

            return f"🐍 Python output:\n{output[:1000]}"

        except Exception as e:
            return f"❌ Python error: {str(e)}"

    def calculate(self, expression):
        """Perform mathematical calculation"""
        try:
            # Safety check
            if any(
                dangerous in expression
                for dangerous in ["import", "__", "eval", "exec"]
            ):
                return "❌ Invalid expression"

            # Allow only math operations
            allowed_chars = set("0123456789+-*/().%** ")
            if not all(c in allowed_chars for c in expression.replace(" ", "")):
                return "❌ Invalid characters in expression"

            result = eval(expression, {"__builtins__": {}}, {})
            return f"🔢 {expression} = {result}"

        except Exception as e:
            return f"❌ Calculation error: {str(e)}"

    # ========== UTILITY FUNCTIONS ==========

    def _format_size(self, bytes):
        """Format bytes to human readable size"""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} TB"
