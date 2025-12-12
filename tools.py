# -*- coding: utf-8 -*-
"""
Tools Module - FIXED VERSION
Fast, reliable action capabilities
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
import time


class ToolBox:
    """Container for all assistant tools"""

    def __init__(self):
        self.tools = {
            # Web tools
            "web_search": self.web_search,
            "google_search": self.google_search,
            "get_current_time": self.get_current_time,
            "get_current_date": self.get_current_date,
            "fetch_webpage": self.fetch_webpage,
            "open_url": self.open_url,
            # File tools
            "read_file": self.read_file,
            "write_file": self.write_file,
            "create_file": self.write_file,
            "append_to_file": self.append_to_file,
            "list_files": self.list_files,
            "delete_file": self.delete_file,
            "rename_file": self.rename_file,
            "move_file": self.move_file,
            "create_folder": self.create_folder,
            "search_files": self.search_files,
            "get_file_info": self.get_file_info,
            "find_all_files": self.find_all_files,
            # System tools
            "open_app": self.open_app,
            "run_command": self.run_command,
            "system_info": self.system_info,
            "execute_python": self.execute_python,
            "list_running_apps": self.list_running_apps,
            # Utility tools
            "calculate": self.calculate,
            "convert_units": self.convert_units,
        }

    def execute_tool(self, tool_name, params):
        """Execute a tool"""
        try:
            if tool_name not in self.tools:
                available = list(self.tools.keys())[:10]
                return {
                    "success": False,
                    "output": f"Tool '{tool_name}' not found. Available: {', '.join(available)}",
                }

            tool_func = self.tools[tool_name]

            if not isinstance(params, list):
                params = [params] if params else []

            result = tool_func(*params)

            return {"success": True, "output": result}

        except TypeError as e:
            import inspect

            sig = inspect.signature(self.tools[tool_name])
            expected = len([p for p in sig.parameters.keys() if p != "self"])
            return {
                "success": False,
                "output": f"Wrong params for {tool_name}. Expected {expected}, got {len(params)}",
            }
        except Exception as e:
            return {
                "success": False,
                "output": f"Error in {tool_name}: {str(e)}",
            }

    # ========== WEB TOOLS ==========

    def google_search(self, query):
        """Search Google"""
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            for g in soup.find_all("div", class_="g")[:6]:
                title_elem = g.find("h3")
                if not title_elem:
                    continue

                title = title_elem.get_text()
                link_elem = g.find("a")
                link = link_elem.get("href") if link_elem else ""

                snippet = ""
                for container in g.find_all(
                    ["div", "span"], class_=["VwiC3b", "lEBKkf"]
                ):
                    text = container.get_text().strip()
                    if len(text) > 20:
                        snippet = text[:200]
                        break

                if title:
                    results.append({"title": title, "snippet": snippet, "link": link})

            if results:
                output = f"🔍 Search '{query}':\n\n"
                for i, r in enumerate(results, 1):
                    output += f"{i}. {r['title']}\n"
                    if r["snippet"]:
                        output += f"   {r['snippet']}\n"
                    output += "\n"
                return output
            else:
                return self.web_search(query)

        except:
            return self.web_search(query)

    def web_search(self, query):
        """DuckDuckGo search"""
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0"}

            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            for result in soup.find_all("div", class_="result")[:6]:
                title_elem = result.find("a", class_="result__a")
                snippet_elem = result.find("a", class_="result__snippet")

                if title_elem:
                    results.append(
                        {
                            "title": title_elem.text.strip(),
                            "snippet": (
                                snippet_elem.text.strip()[:200] if snippet_elem else ""
                            ),
                            "link": title_elem.get("href", ""),
                        }
                    )

            if results:
                output = f"🔍 Search '{query}':\n\n"
                for i, r in enumerate(results, 1):
                    output += f"{i}. {r['title']}\n"
                    if r["snippet"]:
                        output += f"   {r['snippet']}\n"
                    output += "\n"
                return output

            return f"No results for '{query}'"

        except Exception as e:
            return f"Search failed: {str(e)}"

    def fetch_webpage(self, url):
        """Fetch webpage content"""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=8)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            text = "\n".join(line for line in lines if line)

            if len(text) > 3000:
                text = text[:3000] + "\n\n[Truncated...]"

            return f"📄 Content from {url}:\n\n{text}"

        except Exception as e:
            return f"Failed to fetch {url}: {str(e)}"

    def get_current_time(self):
        """Get current time"""
        now = datetime.now()
        return f"🕐 {now.strftime('%I:%M %p on %A, %B %d, %Y')}"

    def get_current_date(self):
        """Get current date"""
        now = datetime.now()
        return f"📅 {now.strftime('%A, %B %d, %Y')}"

    def open_url(self, url):
        """Open URL in browser"""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
            return f"✅ Opened {url}"
        except Exception as e:
            return f"Failed: {str(e)}"

    # ========== FILE TOOLS ==========

    def read_file(self, filepath):
        """Read file contents"""
        try:
            path = Path(filepath).expanduser()

            if not path.is_absolute():
                path = Path.cwd() / path

            path = path.resolve()

            if not path.exists():
                parent = path.parent if path.parent.exists() else Path.cwd()
                if parent.exists():
                    matches = list(parent.glob(f"*{path.name}*"))[:3]
                    if matches:
                        suggestions = "\n".join([f"   → {m}" for m in matches])
                        return f"❌ File not found: {filepath}\n\nDid you mean:\n{suggestions}"

                return f"❌ File not found: {filepath}\n📁 Current: {Path.cwd()}"

            if path.stat().st_size > 2_000_000:
                return f"❌ File too large (>2MB): {filepath}"

            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    with open(path, "r", encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return f"❌ Could not decode: {filepath}"

            size = len(content)
            lines = content.count("\n") + 1

            return f"📄 {path.name} ({size} chars, {lines} lines)\n📁 {path.parent}\n\n{content}"

        except Exception as e:
            return f"❌ Read error: {str(e)}"

    def write_file(self, filepath, content=""):
        """Write to file"""
        try:
            path = Path(filepath).expanduser()

            if not path.is_absolute():
                path = Path.cwd() / path

            path = path.resolve()

            content = str(content) if content is not None else ""

            existed = path.exists()

            try:
                path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                return f"❌ No permission to create directory: {path.parent}"

            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            except PermissionError:
                return f"❌ No permission to write: {path}"
            except Exception as e:
                return f"❌ Write failed: {str(e)}"

            if not path.exists():
                return f"❌ File creation failed: {filepath}"

            try:
                with open(path, "r", encoding="utf-8") as f:
                    written_content = f.read()

                if written_content != content:
                    return f"❌ Content verification failed"
            except:
                pass

            new_size = path.stat().st_size
            action = "✏️ Updated" if existed else "✅ Created"

            preview = content[:100].replace("\n", " ")
            if len(content) > 100:
                preview += "..."

            return f"""{action} file!
📄 Name: {path.name}
📁 Location: {path.parent}
📊 Size: {new_size} bytes
📝 Preview: {preview}"""

        except Exception as e:
            import traceback

            error_detail = traceback.format_exc()
            return f"❌ Write failed: {str(e)}\n\nDetails: {error_detail[:200]}"

    def append_to_file(self, filepath, content):
        """Append to file"""
        try:
            path = Path(filepath).expanduser()

            if not path.is_absolute():
                path = Path.cwd() / path

            path = path.resolve()

            if not path.exists():
                return (
                    f"❌ File not found: {filepath}\n💡 Use write_file() to create it"
                )

            old_size = path.stat().st_size

            with open(path, "a", encoding="utf-8") as f:
                f.write(content)

            new_size = path.stat().st_size
            added = new_size - old_size

            return f"✅ Appended {added} bytes to {path.name}\n📊 New size: {new_size} bytes"

        except Exception as e:
            return f"❌ Append failed: {str(e)}"

    def rename_file(self, old_filepath, new_filename):
        """Rename file"""
        try:
            old_path = Path(old_filepath).expanduser()

            if not old_path.is_absolute():
                old_path = Path.cwd() / old_path

            old_path = old_path.resolve()

            if not old_path.exists():
                return f"❌ File not found: {old_filepath}\n📁 Current: {Path.cwd()}"

            if "\\" in new_filename or "/" in new_filename:
                new_path = Path(new_filename).expanduser().resolve()
            else:
                new_path = old_path.parent / new_filename

            if new_path.exists():
                return f"❌ Target already exists: {new_path.name}"

            try:
                old_path.rename(new_path)
            except OSError:
                shutil.move(str(old_path), str(new_path))

            if not new_path.exists():
                return f"❌ Rename failed"

            return f"""✅ Renamed!
📄 Old: {old_path.name}
📄 New: {new_path.name}
📁 Location: {new_path.parent}"""

        except Exception as e:
            return f"❌ Rename failed: {str(e)}"

    def list_files(self, directory="."):
        """List directory contents"""
        try:
            path = Path(directory).expanduser()

            if not path.is_absolute():
                path = Path.cwd() / path

            path = path.resolve()

            if not path.exists():
                return f"❌ Directory not found: {directory}\n📁 Current: {Path.cwd()}"

            if not path.is_dir():
                return f"❌ Not a directory: {directory}"

            files = []
            folders = []

            for item in sorted(path.iterdir()):
                try:
                    if item.is_file():
                        size = self._format_size(item.stat().st_size)
                        modified = datetime.fromtimestamp(
                            item.stat().st_mtime
                        ).strftime("%Y-%m-%d %H:%M")
                        files.append(f"   📄 {item.name:<40} {size:>10}  {modified}")
                    elif item.is_dir():
                        folders.append(f"   📁 {item.name}/")
                except PermissionError:
                    continue

            output = f"📁 Directory: {path}\n\n"

            if folders:
                output += (
                    f"📁 Folders ({len(folders)}):\n" + "\n".join(folders[:30]) + "\n\n"
                )

            if files:
                output += f"📄 Files ({len(files)}):\n" + "\n".join(files[:30])

            total = len(files) + len(folders)
            if total > 30:
                output += f"\n\n... and {total - 30} more items"

            if total == 0:
                output += "🔭 Empty directory"

            return output

        except Exception as e:
            return f"❌ List failed: {str(e)}"

    def delete_file(self, filepath):
        """Delete file"""
        try:
            path = Path(filepath).expanduser()

            if not path.is_absolute():
                path = Path.cwd() / path

            path = path.resolve()

            if not path.exists():
                return f"❌ File not found: {filepath}"

            if not path.is_file():
                return f"❌ Not a file: {filepath}"

            name = path.name
            size = self._format_size(path.stat().st_size)

            path.unlink()

            if path.exists():
                return f"❌ Deletion failed"

            return f"✅ Deleted: {name} ({size})"

        except Exception as e:
            return f"❌ Delete failed: {str(e)}"

    def _format_size(self, bytes):
        """Format bytes to human readable"""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"

    # ========== SYSTEM TOOLS ==========

    def open_app(self, app_name):
        """Open application"""
        try:
            system = platform.system()
            app_lower = app_name.lower()

            print(f"[*] Opening: {app_name}")

            if system == "Windows":
                return self._open_windows_app(app_name, app_lower)
            elif system == "Darwin":
                return self._open_macos_app(app_name)
            else:
                return self._open_linux_app(app_name)

        except Exception as e:
            return f"❌ Failed to open {app_name}: {str(e)}"

    def _open_windows_app(self, app_name, app_lower):
        """Open Windows app"""

        app_map = {
            "chrome": ["chrome.exe", "chrome"],
            "google chrome": ["chrome.exe", "chrome"],
            "firefox": ["firefox.exe", "firefox"],
            "edge": ["msedge.exe", "msedge"],
            "notepad": ["notepad.exe", "notepad"],
            "calculator": ["calc.exe", "calc"],
            "calc": ["calc.exe", "calc"],
            "explorer": ["explorer.exe", "explorer"],
            "cmd": ["cmd.exe", "cmd"],
            "terminal": ["cmd.exe", "cmd"],
            "powershell": ["powershell.exe", "powershell"],
            "paint": ["mspaint.exe", "mspaint"],
            "word": ["WINWORD.EXE", "winword.exe"],
            "excel": ["EXCEL.EXE", "excel.exe"],
            "powerpoint": ["POWERPNT.EXE", "powerpnt.exe"],
            "vscode": ["Code.exe", "code.exe"],
            "vs code": ["Code.exe", "code.exe"],
        }

        commands_to_try = []
        for key, variations in app_map.items():
            if key in app_lower:
                commands_to_try = variations
                break

        if not commands_to_try:
            commands_to_try = [app_name, f"{app_name}.exe"]

        # METHOD 1: Windows start command
        for cmd in commands_to_try:
            try:
                result = subprocess.Popen(
                    f'start "" "{cmd}"',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                time.sleep(0.3)

                if result.poll() is None or result.returncode == 0:
                    print(f"   ✅ Launched via start command")
                    return f"✅ Opening {app_name}"

            except Exception as e:
                print(f"   ⚠️  Start failed: {e}")
                continue

        # METHOD 2: Search Program Files
        print("   🔍 Searching...")

        search_paths = [
            Path(os.environ.get("ProgramFiles", "C:/Program Files")),
            Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs",
            Path(os.environ.get("APPDATA", "")),
        ]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            try:
                for cmd in commands_to_try:
                    direct_path = search_path / cmd
                    if direct_path.exists():
                        try:
                            subprocess.Popen([str(direct_path)])
                            print(f"   ✅ Opened from: {direct_path.parent}")
                            return f"✅ Opening {app_name}"
                        except:
                            continue

                    for exe_file in search_path.rglob(cmd):
                        if len(exe_file.parts) - len(search_path.parts) > 4:
                            continue

                        try:
                            subprocess.Popen([str(exe_file)])
                            print(f"   ✅ Opened from: {exe_file.parent}")
                            return f"✅ Opening {app_name}"
                        except:
                            continue

            except Exception as e:
                print(f"   ⚠️  Search error: {e}")
                continue

        # METHOD 3: Start Menu
        print("   🔍 Searching Start Menu...")

        start_menu_paths = [
            Path(os.environ.get("APPDATA", ""))
            / "Microsoft/Windows/Start Menu/Programs",
            Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs"),
        ]

        for start_path in start_menu_paths:
            if not start_path.exists():
                continue

            try:
                for shortcut in start_path.rglob("*.lnk"):
                    if app_lower in shortcut.stem.lower():
                        try:
                            os.startfile(str(shortcut))
                            print(f"   ✅ Opened shortcut: {shortcut.name}")
                            return f"✅ Opening {app_name}"
                        except:
                            continue
            except:
                continue

        # METHOD 4: os.startfile
        print("   🔍 Trying os.startfile...")
        for cmd in commands_to_try:
            try:
                os.startfile(cmd)
                print(f"   ✅ Opened via os.startfile")
                return f"✅ Opening {app_name}"
            except:
                continue

        return f"❌ Could not find '{app_name}'\n💡 Try exact name from Start Menu"

    def _open_macos_app(self, app_name):
        """Open macOS app"""
        try:
            subprocess.Popen(["open", "-a", app_name])
            return f"✅ Opening {app_name}"
        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def _open_linux_app(self, app_name):
        """Open Linux app"""
        try:
            subprocess.Popen([app_name])
            return f"✅ Opening {app_name}"
        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def list_running_apps(self):
        """List running applications"""
        try:
            processes = []
            for proc in psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_percent"]
            ):
                try:
                    info = proc.info
                    if info["name"] and info["memory_percent"] > 0.1:
                        processes.append(info)
                except:
                    continue

            processes.sort(key=lambda x: x["memory_percent"], reverse=True)
            processes = processes[:15]

            output = "🖥️ Running Apps (Top 15):\n\n"
            for proc in processes:
                output += (
                    f"   {proc['name']:<30} | RAM: {proc['memory_percent']:.1f}%\n"
                )

            return output

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def run_command(self, command):
        """Execute system command"""
        try:
            dangerous = [
                "rm -rf /",
                "del /f /s /q",
                "format",
                "mkfs",
                "dd if=",
                "shutdown",
                "restart",
            ]

            cmd_lower = command.lower()
            if any(d in cmd_lower for d in dangerous):
                return "❌ Blocked: Dangerous command"

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15,
            )

            output = result.stdout if result.stdout else result.stderr

            if not output:
                output = "✅ Command executed (no output)"

            if len(output) > 1500:
                output = output[:1500] + "\n\n[Truncated...]"

            return f"💻 Output:\n{output}"

        except subprocess.TimeoutExpired:
            return "❌ Command timeout (15s)"
        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def system_info(self):
        """Get system information"""
        try:
            info = []

            info.append(f"💻 System: {platform.system()} {platform.release()}")
            info.append(f"🖥️ Machine: {platform.machine()}")
            info.append(f"🏷️ Computer: {platform.node()}")

            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_count = psutil.cpu_count()
            info.append(f"⚡ CPU: {cpu_count} cores | Usage: {cpu_percent}%")

            mem = psutil.virtual_memory()
            info.append(
                f"💾 RAM: {self._format_size(mem.used)} / {self._format_size(mem.total)} ({mem.percent}%)"
            )

            disk = psutil.disk_usage("/")
            info.append(
                f"💿 Disk: {self._format_size(disk.used)} / {self._format_size(disk.total)} ({disk.percent}%)"
            )

            info.append(
                f"🕐 Time: {datetime.now().strftime('%I:%M %p on %A, %B %d, %Y')}"
            )

            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            days = uptime.days
            hours = uptime.seconds // 3600
            info.append(f"⏰ Uptime: {days}d {hours}h")

            return "\n".join(info)

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def execute_python(self, code):
        """Execute Python code"""
        try:
            dangerous = [
                "import os",
                "import subprocess",
                "__import__",
                "exec(",
                "eval(",
                "open(",
                "file(",
                "compile(",
            ]

            if any(d in code for d in dangerous):
                return "❌ Blocked: Dangerous code"

            if len(code) > 1000:
                return "❌ Code too long (1000 char limit)"

            safe_builtins = {
                "abs": abs,
                "all": all,
                "any": any,
                "chr": chr,
                "len": len,
                "list": list,
                "max": max,
                "min": min,
                "print": print,
                "range": range,
                "str": str,
                "sum": sum,
                "type": type,
            }

            from io import StringIO
            import sys

            old_stdout = sys.stdout
            sys.stdout = StringIO()

            try:
                local_vars = {}
                exec(code, {"__builtins__": safe_builtins}, local_vars)

                output = sys.stdout.getvalue()
                sys.stdout = old_stdout

                if output:
                    return f"✅ Output:\n{output}"
                elif local_vars:
                    return f"✅ Variables: {local_vars}"
                else:
                    return "✅ Code executed"

            finally:
                sys.stdout = old_stdout

        except Exception as e:
            return f"❌ Python error: {str(e)}"

    # ========== UTILITY TOOLS ==========

    def calculate(self, expression):
        """Calculate math expression"""
        try:
            expression = str(expression).replace(" ", "")

            allowed = set("0123456789+-*/().^%")
            if not all(c in allowed for c in expression):
                return "❌ Invalid characters"

            expression = expression.replace("^", "**")
            result = eval(expression, {"__builtins__": {}})

            return f"🔢 {expression} = {result}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def convert_units(self, value, from_unit, to_unit):
        """Convert units"""
        try:
            value = float(value)
            from_unit = from_unit.lower()
            to_unit = to_unit.lower()

            length_units = {
                "m": 1,
                "meter": 1,
                "km": 1000,
                "kilometer": 1000,
                "cm": 0.01,
                "centimeter": 0.01,
                "mm": 0.001,
                "millimeter": 0.001,
                "mi": 1609.34,
                "mile": 1609.34,
                "ft": 0.3048,
                "foot": 0.3048,
                "in": 0.0254,
                "inch": 0.0254,
            }

            weight_units = {
                "g": 1,
                "gram": 1,
                "kg": 1000,
                "kilogram": 1000,
                "mg": 0.001,
                "milligram": 0.001,
                "lb": 453.592,
                "pound": 453.592,
                "oz": 28.3495,
                "ounce": 28.3495,
            }

            temp_units = ["celsius", "c", "fahrenheit", "f", "kelvin", "k"]

            if from_unit in temp_units:
                result = self._convert_temperature(value, from_unit, to_unit)
            elif from_unit in length_units and to_unit in length_units:
                base = value * length_units[from_unit]
                result = base / length_units[to_unit]
            elif from_unit in weight_units and to_unit in weight_units:
                base = value * weight_units[from_unit]
                result = base / weight_units[to_unit]
            else:
                return f"❌ Unknown conversion: {from_unit} to {to_unit}"

            return f"🔄 {value} {from_unit} = {result:.4f} {to_unit}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def _convert_temperature(self, value, from_unit, to_unit):
        """Convert temperature"""
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()

        if from_unit in ["celsius", "c"]:
            celsius = value
        elif from_unit in ["fahrenheit", "f"]:
            celsius = (value - 32) * 5 / 9
        elif from_unit in ["kelvin", "k"]:
            celsius = value - 273.15
        else:
            return value

        if to_unit in ["celsius", "c"]:
            return celsius
        elif to_unit in ["fahrenheit", "f"]:
            return celsius * 9 / 5 + 32
        elif to_unit in ["kelvin", "k"]:
            return celsius + 273.15
        else:
            return value

    def move_file(self, source, destination):
        """Move file"""
        try:
            src = Path(source).expanduser()
            dst = Path(destination).expanduser()

            if not src.is_absolute():
                src = Path.cwd() / src
            if not dst.is_absolute():
                dst = Path.cwd() / dst

            src = src.resolve()
            dst = dst.resolve()

            if not src.exists():
                return f"❌ Source not found: {source}"

            shutil.move(str(src), str(dst))

            return f"✅ Moved!\n📤 From: {src.name}\n📥 To: {dst}"

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def create_folder(self, path):
        """Create folder"""
        try:
            folder = Path(path).expanduser()

            if not folder.is_absolute():
                folder = Path.cwd() / folder

            folder = folder.resolve()

            folder.mkdir(parents=True, exist_ok=True)

            return f"✅ Created folder: {folder}"
        except PermissionError:
            return f"❌ No permission: {path}"
        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def search_files(self, directory, pattern):
        """Search for files"""
        try:
            path = Path(directory).expanduser()

            if not path.is_absolute():
                path = Path.cwd() / path

            path = path.resolve()

            if not path.exists():
                return f"❌ Directory not found: {directory}"

            matches = list(path.rglob(pattern))[:50]

            if not matches:
                return f"❌ No files matching '{pattern}'"

            output = f"🔍 Found {len(matches)} file(s) matching '{pattern}':\n\n"
            for match in matches[:30]:
                try:
                    rel_path = match.relative_to(path)
                    size = (
                        self._format_size(match.stat().st_size)
                        if match.is_file()
                        else "[folder]"
                    )
                    output += f"   📄 {rel_path} ({size})\n"
                except:
                    continue

            if len(matches) > 30:
                output += f"\n... and {len(matches) - 30} more"

            return output

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def find_all_files(self, filename):
        """Search PC for file"""
        try:
            search_paths = [
                Path.cwd(),
                Path.home() / "Desktop",
                Path.home() / "Documents",
                Path.home() / "Downloads",
            ]

            matches = []
            for search_path in search_paths:
                if not search_path.exists():
                    continue

                try:
                    for match in search_path.rglob(filename):
                        matches.append(match)
                        if len(matches) >= 20:
                            break
                except:
                    continue

                if len(matches) >= 20:
                    break

            if not matches:
                return f"❌ File '{filename}' not found"

            output = f"🔍 Found {len(matches)} match(es) for '{filename}':\n\n"
            for i, match in enumerate(matches[:15], 1):
                size = (
                    self._format_size(match.stat().st_size)
                    if match.is_file()
                    else "[folder]"
                )
                output += f"{i}. {match}\n   Size: {size}\n"

            if len(matches) > 15:
                output += f"\n... and {len(matches) - 15} more"

            return output

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    def get_file_info(self, filepath):
        """Get file info"""
        try:
            path = Path(filepath).expanduser()

            if not path.is_absolute():
                path = Path.cwd() / path

            path = path.resolve()

            if not path.exists():
                return f"❌ File not found: {filepath}"

            stat = path.stat()

            info = [
                f"📄 File: {path.name}",
                f"",
                f"📁 Location: {path.parent}",
                f"🔧 Type: {'File' if path.is_file() else 'Directory'}",
                f"📊 Size: {self._format_size(stat.st_size)} ({stat.st_size:,} bytes)",
                f"📅 Created: {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}",
                f"✏️ Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
            ]

            return "\n".join(info)

        except Exception as e:
            return f"❌ Failed: {str(e)}"
