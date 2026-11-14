"""
Axiom Lens - Binary file analyzer for basic metadata extraction.
"""
import os
import magic
from pathlib import Path
from typing import Optional, Dict, Any, List
import subprocess
import json

import re

class BinaryAnalyzer:
    """Basic binary file analyzer for metadata extraction."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
    
    def analyze(self) -> Dict[str, Any]:
        """Perform basic binary analysis and return results."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        results = {
            "file_info": self._get_file_info(),
            "file_type": self._get_file_type(),
            "strings": self._extract_strings(),
        "ai_insights": self._get_ai_insights(),
        }
        
        # Try to get more detailed info for ELF/PE/Mach-O
        file_type = results["file_type"].get("type", "").lower()
        if "elf" in file_type:
            results["elf_info"] = self._analyze_elf()
        elif "pe" in file_type or "executable" in file_type and "microsoft" in file_type:
            results["pe_info"] = self._analyze_pe()
        elif "mach-o" in file_type or "mach" in file_type:
            results["macho_info"] = self._analyze_macho()
        
        return results
    
    def _get_file_info(self) -> Dict[str, Any]:
        """Get basic file information."""
        stat = self.file_path.stat()
        return {
            "path": str(self.file_path),
            "name": self.file_path.name,
            "size": stat.st_size,
            "size_human": self._human_readable_size(stat.st_size),
            "modified": stat.st_mtime,
        }
    
    def _human_readable_size(self, size: int) -> str:
        """Convert bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def _get_file_type(self) -> Dict[str, Any]:
        """Get file type using python-magic."""
        try:
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(str(self.file_path))
            
            desc = magic.Magic()
            description = desc.from_file(str(self.file_path))
            
            return {
                "mime_type": mime_type,
                "description": description,
                "type": description.split(",")[0] if description else "unknown",
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_strings(self, min_length: int = 4, max_strings: int = 1000) -> List[str]:
        """Extract printable strings from binary."""
        strings = []
        try:
            with open(self.file_path, 'rb') as f:
                content = f.read()
            
            current_string = []
            for byte in content:
                if 32 <= byte <= 126:  # Printable ASCII
                    current_string.append(chr(byte))
                else:
                    if len(current_string) >= min_length:
                        strings.append(''.join(current_string))
                        if len(strings) >= max_strings:
                            break
                    current_string = []
            
            # Check last string
            if len(current_string) >= min_length:
                strings.append(''.join(current_string))
            
        except Exception as e:
            strings.append(f"Error extracting strings: {e}")
        
        return strings[:max_strings]
    
    def _analyze_elf(self) -> Dict[str, Any]:
        """Analyze ELF binary using readelf."""
        info = {}
        try:
            # Get ELF header
            result = subprocess.run(
                ['readelf', '-h', str(self.file_path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                info["header"] = self._parse_readelf_header(result.stdout)
            
            # Get sections
            result = subprocess.run(
                ['readelf', '-S', str(self.file_path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                info["sections"] = self._parse_readelf_sections(result.stdout)
            
            # Get symbols
            result = subprocess.run(
                ['readelf', '-s', str(self.file_path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                info["symbols"] = self._parse_readelf_symbols(result.stdout)
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            info["error"] = str(e)
        
        return info
    
    def _parse_readelf_header(self, output: str) -> Dict[str, str]:
        """Parse readelf -h output."""
        header = {}
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                header[key.strip()] = value.strip()
        return header
    
    def _parse_readelf_sections(self, output: str) -> List[Dict[str, str]]:
        """Parse readelf -S output."""
        sections = []
        lines = output.split('\n')
        in_table = False
        i = 0
        # Regex to match section lines: "  [ 0] name type address offset"
        # or "  [10] name type address offset"
        section_line_re = re.compile(r'^\s*\[\s*(\d+)\s*\]\s+(\S+)?\s+(\S+)\s+(\S+)\s+(\S+)')
        # Regex to match the continuation line with flags: "       size entsize flags link info align"
        cont_line_re = re.compile(r'^\s*\S+\s+\S+\s+(\S+)')
        
        while i < len(lines):
            line = lines[i]
            if 'Section Headers:' in line:
                in_table = True
                i += 1
                continue
            if in_table and line.strip():
                match = section_line_re.match(line)
                if match:
                    index = match.group(1)
                    name = match.group(2) or ""
                    type_ = match.group(3)
                    address = match.group(4)
                    offset = match.group(5)
                    
                    # Get flags from next line if available
                    flags = ""
                    if i + 1 < len(lines):
                        next_match = cont_line_re.match(lines[i + 1])
                        if next_match:
                            flags = next_match.group(1)
                    
                    sections.append({
                        "index": index,
                        "name": name,
                        "type": type_,
                        "address": address,
                        "offset": offset,
                        "flags": flags,
                    })
                    i += 2  # Skip the next line too
                    continue
                i += 1  # Move to next line if not a section line
            else:
                i += 1
        return sections[:50]  # Limit to 50 sections
    
    def _parse_readelf_symbols(self, output: str) -> List[Dict[str, str]]:
        """Parse readelf -s output."""
        symbols = []
        lines = output.split('\n')
        in_table = False
        for line in lines:
            if 'Symbol table' in line:
                in_table = True
                continue
            if in_table and line.strip():
                parts = line.split()
                # Symbol lines look like: "     0: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT  UND "
                # parts[0] is like "0:" (with trailing colon), so strip it
                if len(parts) >= 7 and parts[0].rstrip(':').isdigit():
                    symbols.append({
                        "index": parts[0].rstrip(':'),
                        "value": parts[1],
                        "size": parts[2],
                        "type": parts[3],
                        "bind": parts[4],
                        "vis": parts[5],
                        "ndx": parts[6],
                        "name": parts[7] if len(parts) >= 8 else "",
                    })
        return symbols[:100]  # Limit to 100 symbols
    
    def _analyze_pe(self) -> Dict[str, Any]:
        """Analyze PE binary using pefile or objdump."""
        info = {}
        try:
            # Try pefile first (Python library)
            try:
                import pefile
                pe = pefile.PE(str(self.file_path))
                info["header"] = {
                    "machine": hex(pe.FILE_HEADER.Machine),
                    "sections": pe.FILE_HEADER.NumberOfSections,
                    "timestamp": pe.FILE_HEADER.TimeDateStamp,
                    "characteristics": hex(pe.FILE_HEADER.Characteristics),
                }
                info["sections"] = [
                    {
                        "name": s.Name.decode().rstrip('\x00'),
                        "virtual_address": hex(s.VirtualAddress),
                        "virtual_size": hex(s.Misc_VirtualSize),
                        "raw_size": hex(s.SizeOfRawData),
                        "characteristics": hex(s.Characteristics),
                    }
                    for s in pe.sections
                ]
                if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                    info["imports"] = [
                        {
                            "dll": entry.dll.decode(),
                            "functions": [imp.name.decode() if imp.name else f"ordinal_{imp.ordinal}" for imp in entry.imports]
                        }
                        for entry in pe.DIRECTORY_ENTRY_IMPORT[:20]
                    ]
                if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
                    info["exports"] = [
                        {
                            "name": exp.name.decode() if exp.name else "",
                            "address": hex(exp.address),
                            "ordinal": exp.ordinal,
                        }
                        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols[:50]
                    ]
            except ImportError:
                # Fallback to objdump
                result = subprocess.run(
                    ['objdump', '-f', str(self.file_path)],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    info["objdump_header"] = result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            info["error"] = str(e)
        
        return info
    
    def _analyze_macho(self) -> Dict[str, Any]:
        """Analyze Mach-O binary using otool."""
        info = {}
        try:
            result = subprocess.run(
                ['otool', '-h', str(self.file_path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                info["header"] = result.stdout
            
            result = subprocess.run(
                ['otool', '-L', str(self.file_path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                info["libraries"] = result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            info["error"] = str(e)
        
        return info


    def _get_ai_insights(self) -> List[Dict[str, Any]]:
        """Get AI-assisted function insights based on strings and symbols.

        Provides labeled advisory insights about functions based on
        extracted strings, symbol names, and binary patterns.
        Opt-in: results are included only when explicitly requested.
        """
        insights = []

        # Extract function-like insights from strings
        strings = self._extract_strings(min_length=8, max_strings=50)

        # Label strings that look like function names or API calls
        for s in strings:
            lower = s.lower()
            # System call patterns
            if any(pattern in lower for pattern in ["open", "read", "write", "close", "exit", "fork"]):
                insights.append({
                    "type": "function_label",
                    "label": s,
                    "confidence": "high",
                    "category": "system_call",
                })
            # Memory allocation patterns
            elif any(keyword in lower for keyword in ["malloc", "calloc", "free", "alloc"]):
                insights.append({
                    "type": "function_label",
                    "label": s,
                    "confidence": "medium",
                    "category": "memory_management",
                })
            # String literals that might be format strings or messages
            elif s.startswith('"') and s.endswith('"'):
                insights.append({
                    "type": "function_label",
                    "label": s[1:-1],
                    "confidence": "low",
                    "category": "string_literal",
                })

        # Insights from ELF symbols
        elf_info = self._analyze_elf()
        if "symbols" in elf_info and "error" not in elf_info.get("summary", {}):
            symbols = elf_info["symbols"]
            # Label common symbol patterns
            for sym in symbols[:30]:  # Limit to first 30 symbols
                name = sym.get("name", "").lower()
                if "init" in name or "start" in name:
                    insights.append({
                        "type": "function_label",
                        "label": sym.get("name", ""),
                        "confidence": "medium",
                        "category": "entry_point",
                    })
                if "fini" in name or "end" in name:
                    insights.append({
                        "type": "function_label",
                        "label": sym.get("name", ""),
                        "confidence": "medium",
                        "category": "exit_point",
                    })

        return insights


def analyze_binary(file_path: Path) -> Dict[str, Any]:
    """Convenience function to analyze a binary file."""
    analyzer = BinaryAnalyzer(file_path)
    return analyzer.analyze()

