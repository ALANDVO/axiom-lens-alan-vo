"""
Unit tests for the binary analyzer service.
"""
import pytest
import tempfile
import os
from pathlib import Path
import subprocess


class TestBinaryAnalyzer:
    """Tests for the BinaryAnalyzer class."""

    @pytest.fixture(scope="class")
    def test_elf_binary(self):
        """Use a pre-built test ELF binary."""
        # Use the test binary we created earlier
        test_binary = Path("/tmp/test_hello")
        if test_binary.exists():
            yield test_binary
            return
        
        pytest.skip("No test ELF binary available")

    @pytest.fixture
    def test_binary(self):
        """Create a simple binary file with known strings."""
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(b"Hello World! This is a test binary with some strings. /bin/bash /usr/bin/env PATH=/usr/bin")
            yield Path(path)
        finally:
            Path(path).unlink(missing_ok=True)

    @pytest.fixture
    def empty_binary(self):
        """Create an empty binary file."""
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'wb') as f:
                pass
            yield Path(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_analyze_elf_binary(self, test_elf_binary):
        """Test analysis of a real ELF binary."""
        from app.services.binary_analyzer import BinaryAnalyzer
        
        analyzer = BinaryAnalyzer(test_elf_binary)
        result = analyzer.analyze()
        
        assert isinstance(result, dict)
        assert "file_info" in result
        assert "file_type" in result
        assert "strings" in result
        assert "elf_info" in result
        
        # Check file info
        assert result["file_info"]["name"] == test_elf_binary.name
        assert result["file_info"]["size"] > 0
        
        # Check file type
        assert "ELF" in result["file_type"]["type"]
        
        # Check strings were extracted
        strings = result["strings"]
        assert len(strings) > 0
        
        # Check ELF info
        elf_info = result["elf_info"]
        assert "header" in elf_info
        assert "sections" in elf_info
        assert "symbols" in elf_info
        assert isinstance(elf_info["sections"], list)
        assert isinstance(elf_info["symbols"], list)

    def test_analyze_simple_binary(self, test_binary):
        """Test analysis of a simple binary file."""
        from app.services.binary_analyzer import BinaryAnalyzer
        
        analyzer = BinaryAnalyzer(test_binary)
        result = analyzer.analyze()
        
        assert isinstance(result, dict)
        assert "file_info" in result
        assert "file_type" in result
        assert "strings" in result
        
        # Check strings were extracted
        strings = result["strings"]
        assert any("Hello World" in s for s in strings)
        assert any("/bin/bash" in s for s in strings)

    def test_file_info(self, test_binary):
        """Test file info extraction."""
        from app.services.binary_analyzer import BinaryAnalyzer
        
        analyzer = BinaryAnalyzer(test_binary)
        file_info = analyzer._get_file_info()
        
        assert "path" in file_info
        assert "name" in file_info
        assert "size" in file_info
        assert "size_human" in file_info
        assert "modified" in file_info
        assert file_info["size"] > 0

    def test_human_readable_size(self):
        """Test human readable size conversion."""
        from app.services.binary_analyzer import BinaryAnalyzer
        
        analyzer = BinaryAnalyzer(Path("/tmp/test"))
        
        assert analyzer._human_readable_size(500) == "500.00 B"
        assert analyzer._human_readable_size(1024) == "1.00 KB"
        assert analyzer._human_readable_size(1024 * 1024) == "1.00 MB"
        assert analyzer._human_readable_size(1024 * 1024 * 1024) == "1.00 GB"

    def test_extract_strings(self, test_binary):
        """Test string extraction."""
        from app.services.binary_analyzer import BinaryAnalyzer
        
        analyzer = BinaryAnalyzer(test_binary)
        strings = analyzer._extract_strings(min_length=4, max_strings=100)
        
        assert isinstance(strings, list)
        assert len(strings) > 0
        assert any("Hello World" in s for s in strings)
        assert all(len(s) >= 4 for s in strings)

    def test_parse_readelf_header(self):
        """Test ELF header parsing."""
        from app.services.binary_analyzer import BinaryAnalyzer
        
        analyzer = BinaryAnalyzer(Path("/tmp/test"))
        
        sample_output = """ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00
  Class:                             ELF64
  Data:                              2's complement, little endian
  Version:                           0x1
  OS/ABI:                            UNIX - System V
  Type:                              DYN (Position-Independent Executable file)
  Machine:                           Advanced Micro Devices X86-64"""
        
        header = analyzer._parse_readelf_header(sample_output)
        
        assert "Magic" in header
        assert header["Class"] == "ELF64"
        assert header["Machine"] == "Advanced Micro Devices X86-64"

    def test_parse_readelf_sections(self):
        """Test ELF section parsing."""
        from app.services.binary_analyzer import BinaryAnalyzer
        
        analyzer = BinaryAnalyzer(Path("/tmp/test"))
        
        sample_output = """There are 5 section headers, starting at offset 0x1000:

Section Headers:
  [Nr] Name              Type             Address           Offset
       Size              EntSize          Flags  Link  Info  Align
  [ 0]                   NULL             0000000000000000  00000000
       0000000000000000  0000000000000000           0     0     0
  [ 1] .interp           PROGBITS         0000000000000318  00000318
       000000000000001c  0000000000000000   A       0     0     1
  [ 2] .text             PROGBITS         0000000000001000  00001000
       0000000000000100  0000000000000000  AX       0     0     16"""
        
        sections = analyzer._parse_readelf_sections(sample_output)
        
        assert len(sections) == 3
        assert sections[0]["index"] == "0"
        assert sections[0]["name"] == ""
        assert sections[0]["type"] == "NULL"
        assert sections[1]["index"] == "1"
        assert sections[1]["name"] == ".interp"
        assert sections[1]["flags"] == "A"
        assert sections[2]["index"] == "2"
        assert sections[2]["name"] == ".text"
        assert sections[2]["flags"] == "AX"

    def test_parse_readelf_symbols(self):
        """Test ELF symbol parsing."""
        from app.services.binary_analyzer import BinaryAnalyzer
        
        analyzer = BinaryAnalyzer(Path("/tmp/test"))
        
        sample_output = """Symbol table '.dynsym' contains 3 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     0: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT  UND 
     1: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND puts@GLIBC_2.2.5
     2: 0000000000001000    50 FUNC    GLOBAL DEFAULT   14 main"""
        
        symbols = analyzer._parse_readelf_symbols(sample_output)
        
        assert len(symbols) == 3
        assert symbols[0]["index"] == "0"
        assert symbols[1]["index"] == "1"
        assert symbols[1]["name"] == "puts@GLIBC_2.2.5"
        assert symbols[2]["index"] == "2"
        assert symbols[2]["name"] == "main"
        assert symbols[2]["size"] == "50"

    def test_analyze_binary_function(self, test_binary):
        """Test the convenience function works."""
        from app.services.binary_analyzer import analyze_binary
        
        result = analyze_binary(test_binary)
        
        assert isinstance(result, dict)
        assert "file_info" in result
        assert "file_type" in result
        assert "strings" in result

    def test_empty_file(self, empty_binary):
        """Test analysis of empty file."""
        from app.services.binary_analyzer import analyze_binary
        
        result = analyze_binary(empty_binary)
        
        assert isinstance(result, dict)
        assert result["file_info"]["size"] == 0
        assert result["strings"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
