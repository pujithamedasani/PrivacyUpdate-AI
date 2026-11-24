import difflib
import re

class DiffService:
    """
    Diff engine for comparing policy revisions.
    Performs syntactic and structural comparison, isolates added, removed,
    and modified sections, and generates formatted diff representations.
    """

    @staticmethod
    def compute_similarity(old_text: str, new_text: str) -> float:
        """Compute SequenceMatcher similarity ratio (0.0 to 1.0)."""
        if not old_text and not new_text:
            return 1.0
        matcher = difflib.SequenceMatcher(None, old_text, new_text)
        return round(matcher.ratio(), 4)

    @classmethod
    def find_affected_section(cls, lines: list, line_idx: int) -> str:
        """Search backwards from line_idx to find the enclosing markdown or section heading."""
        for i in range(min(line_idx, len(lines) - 1), -1, -1):
            line = lines[i].strip()
            if line.startswith("#"):
                # Clean up heading
                return re.sub(r"^#+\s*", "", line)
            if re.match(r"^(Section|\d+\.|\bArticle\b)", line, re.IGNORECASE) and len(line) < 80:
                return line
        return "General Policy Content"

    @classmethod
    def detect_changes(cls, old_content: str, new_content: str) -> list:
        """
        Compare old and new policy text.
        Returns a list of structured change items:
        [
            {
                "change_type": "Added" | "Removed" | "Modified",
                "affected_section": str,
                "previous_content": str,
                "updated_content": str,
                "old_lines": (start, end),
                "new_lines": (start, end)
            }
        ]
        """
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        opcodes = matcher.get_opcodes()
        changes = []

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                continue

            prev_chunk = "\n".join(old_lines[i1:i2]).strip()
            curr_chunk = "\n".join(new_lines[j1:j2]).strip()

            # Skip trivial whitespace changes
            if not prev_chunk and not curr_chunk:
                continue

            if tag == 'replace':
                change_type = "Modified"
                affected = cls.find_affected_section(new_lines, j1)
            elif tag == 'insert':
                change_type = "Added"
                affected = cls.find_affected_section(new_lines, j1)
            elif tag == 'delete':
                change_type = "Removed"
                affected = cls.find_affected_section(old_lines, i1)
            else:
                change_type = "Modified"
                affected = cls.find_affected_section(new_lines, j1)

            changes.append({
                "change_type": change_type,
                "affected_section": affected,
                "previous_content": prev_chunk,
                "updated_content": curr_chunk,
                "old_lines": (i1 + 1, i2),
                "new_lines": (j1 + 1, j2)
            })

        return changes

    @staticmethod
    def generate_html_diff(old_content: str, new_content: str) -> str:
        """Generate a side-by-side or unified HTML diff table."""
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        differ = difflib.HtmlDiff(wrapcolumn=80)
        table_html = differ.make_table(
            old_lines,
            new_lines,
            fromdesc="Previous Snapshot",
            todesc="Updated Snapshot",
            context=True,
            numlines=3
        )
        return table_html
