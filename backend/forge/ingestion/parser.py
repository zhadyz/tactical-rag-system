"""
Forge - Structure-Aware Document Parser

Parses PDF, DOCX, TXT, MD into a DocumentTree preserving heading hierarchy,
tables, and lists.  Uses the `unstructured` library for rich format extraction.
"""

import logging
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Section:
    """Recursive section node in a document tree."""
    heading: str
    content: str = ""
    level: int = 1  # heading depth (1 = top, 2 = sub, ...)
    subsections: List["Section"] = field(default_factory=list)


@dataclass
class DocumentTree:
    """Parsed document with heading hierarchy."""
    title: str
    file_name: str
    file_type: str
    raw_text: str = ""
    sections: List[Section] = field(default_factory=list)


class DocumentParser:
    """
    Parse documents into a hierarchical DocumentTree.

    Supported formats: PDF, DOCX, TXT, MD.
    """

    SUPPORTED = {".pdf", ".docx", ".txt", ".md"}

    def parse(self, file_path: str) -> DocumentTree:
        """Parse a file into a DocumentTree."""
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in self.SUPPORTED:
            raise ValueError(f"Unsupported file type: {ext}")

        logger.info(f"Parsing {path.name} ({ext})")

        if ext == ".pdf":
            return self._parse_pdf(path)
        elif ext == ".docx":
            return self._parse_docx(path)
        elif ext == ".md":
            return self._parse_markdown(path)
        else:
            return self._parse_text(path)

    # ------------------------------------------------------------------
    # Format-specific parsers
    # ------------------------------------------------------------------

    def _parse_pdf(self, path: Path) -> DocumentTree:
        """Parse PDF using unstructured for structure-aware extraction."""
        try:
            from unstructured.partition.pdf import partition_pdf
            elements = partition_pdf(str(path), strategy="fast")
        except Exception as e:
            logger.warning(f"unstructured PDF failed ({e}), falling back to pypdf")
            return self._parse_pdf_fallback(path)

        return self._elements_to_tree(elements, path)

    def _parse_pdf_fallback(self, path: Path) -> DocumentTree:
        """Fallback PDF parser using pypdf."""
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        raw = "\n\n".join(pages)
        return self._raw_text_to_tree(raw, path)

    def _parse_docx(self, path: Path) -> DocumentTree:
        """Parse DOCX using unstructured."""
        try:
            from unstructured.partition.docx import partition_docx
            elements = partition_docx(str(path))
            return self._elements_to_tree(elements, path)
        except Exception as e:
            logger.warning(f"unstructured DOCX failed ({e}), falling back to python-docx")
            return self._parse_docx_fallback(path)

    def _parse_docx_fallback(self, path: Path) -> DocumentTree:
        from docx import Document as DocxDocument
        doc = DocxDocument(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        raw = "\n\n".join(paragraphs)
        return self._raw_text_to_tree(raw, path)

    def _parse_markdown(self, path: Path) -> DocumentTree:
        """Parse Markdown using heading patterns."""
        raw = path.read_text(encoding="utf-8", errors="replace")
        sections = self._md_headings_to_sections(raw)
        return DocumentTree(
            title=path.stem,
            file_name=path.name,
            file_type="md",
            raw_text=raw,
            sections=sections,
        )

    def _parse_text(self, path: Path) -> DocumentTree:
        raw = path.read_text(encoding="utf-8", errors="replace")
        return self._raw_text_to_tree(raw, path)

    # ------------------------------------------------------------------
    # Converters
    # ------------------------------------------------------------------

    def _elements_to_tree(self, elements, path: Path) -> DocumentTree:
        """Convert unstructured Element list into a DocumentTree."""
        sections: List[Section] = []
        current_section: Optional[Section] = None
        content_buffer: List[str] = []
        raw_parts: List[str] = []

        for el in elements:
            category = getattr(el, "category", "NarrativeText")
            text = str(el).strip()
            if not text:
                continue

            raw_parts.append(text)

            if category == "Title" or category == "Header":
                # Flush previous section
                if current_section is not None:
                    current_section.content = "\n".join(content_buffer).strip()
                    sections.append(current_section)
                    content_buffer = []
                current_section = Section(heading=text, level=1)
            else:
                content_buffer.append(text)

        # Flush final section
        if current_section is not None:
            current_section.content = "\n".join(content_buffer).strip()
            sections.append(current_section)
        elif content_buffer:
            sections.append(Section(
                heading="Document Content",
                content="\n".join(content_buffer).strip(),
            ))

        raw_text = "\n\n".join(raw_parts)

        tree = DocumentTree(
            title=path.stem,
            file_name=path.name,
            file_type=path.suffix.lstrip("."),
            raw_text=raw_text,
            sections=self._nest_sections(sections),
        )
        logger.info(f"Parsed {path.name}: {len(tree.sections)} top-level sections")
        return tree

    def _raw_text_to_tree(self, raw: str, path: Path) -> DocumentTree:
        """Best-effort section splitting from plain text."""
        # Try to detect headings by ALL-CAPS lines or numbered patterns
        lines = raw.split("\n")
        sections: List[Section] = []
        current_heading = "Document Content"
        content_lines: List[str] = []

        heading_re = re.compile(
            r"^(?:"
            r"(?:CHAPTER|SECTION|PART|ARTICLE)\s+\d+"    # CHAPTER 1, SECTION 2
            r"|(?:\d+\.)+\s+[A-Z]"                        # 1.2 Something
            r"|[A-Z][A-Z\s]{5,}$"                          # ALL CAPS LINE (6+ chars)
            r")"
        )

        for line in lines:
            stripped = line.strip()
            if stripped and heading_re.match(stripped):
                if content_lines:
                    sections.append(Section(
                        heading=current_heading,
                        content="\n".join(content_lines).strip(),
                    ))
                    content_lines = []
                current_heading = stripped
            else:
                content_lines.append(line)

        if content_lines:
            sections.append(Section(
                heading=current_heading,
                content="\n".join(content_lines).strip(),
            ))

        return DocumentTree(
            title=path.stem,
            file_name=path.name,
            file_type=path.suffix.lstrip("."),
            raw_text=raw,
            sections=sections if sections else [Section(heading="Full Document", content=raw)],
        )

    def _md_headings_to_sections(self, text: str) -> List[Section]:
        """Parse Markdown headings into flat Section list then nest."""
        heading_re = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)
        sections: List[Section] = []
        last_end = 0

        for match in heading_re.finditer(text):
            level = len(match.group(1))
            heading = match.group(2).strip()

            # Content between previous heading and this one
            if sections and last_end < match.start():
                sections[-1].content = text[last_end:match.start()].strip()

            sections.append(Section(heading=heading, level=level))
            last_end = match.end()

        # Trailing content
        if sections:
            sections[-1].content = text[last_end:].strip()
        else:
            sections.append(Section(heading="Full Document", content=text.strip()))

        return self._nest_sections(sections)

    @staticmethod
    def _nest_sections(flat: List[Section]) -> List[Section]:
        """Nest flat sections into a tree based on level."""
        if not flat:
            return flat

        root: List[Section] = []
        stack: List[Section] = []

        for sec in flat:
            while stack and stack[-1].level >= sec.level:
                stack.pop()
            if stack:
                stack[-1].subsections.append(sec)
            else:
                root.append(sec)
            stack.append(sec)

        return root
