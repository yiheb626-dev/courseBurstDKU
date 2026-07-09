from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CartCourse:
    name: str = ""
    class_nbr: Optional[int] = None
    component: str = ""
    section: str = ""
    instructor: str = ""
    note: str = ""
    source_text: str = ""


class CartReader:
    def read(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        cdp_url = str(raw.get("cdp_url") or "http://127.0.0.1:9222").strip()
        page_url_keyword = str(raw.get("page_url_keyword") or "dkuhub.dku.edu.cn").strip()

        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            return {
                "ok": False,
                "message": "Playwright is not installed or cannot load.",
                "details": str(exc),
                "courses": [],
            }

        try:
            with sync_playwright() as p:
                browser = p.chromium.connect_over_cdp(cdp_url)
                page = self._select_page(browser, page_url_keyword)
                if page is None:
                    browser.close()
                    return {
                        "ok": False,
                        "message": "No matching browser tab found. Open the shopping cart page first.",
                        "courses": [],
                    }

                candidates, preview = self._collect_candidates(page)
                courses = self._parse_courses(candidates)
                browser.close()
        except Exception as exc:
            return {
                "ok": False,
                "message": f"Failed to read shopping cart: {exc}",
                "courses": [],
            }

        message = "Shopping cart courses loaded." if courses else (
            "No course rows were recognized. Stay on the Shopping Cart page and try again."
        )
        return {
            "ok": True,
            "message": message,
            "courses": [asdict(course) for course in courses],
            "candidate_count": len(candidates),
            "preview": preview[:3000],
            "attached_url": page.url,
        }

    def _select_page(self, browser: Any, page_url_keyword: str) -> Any:
        pages = []
        for context in browser.contexts:
            pages.extend(context.pages)

        if page_url_keyword:
            for page in pages:
                if page_url_keyword in page.url:
                    return page

        for page in pages:
            if page.url and page.url != "about:blank":
                return page

        return pages[0] if pages else None

    def _collect_candidates(self, page: Any) -> Tuple[List[str], str]:
        script = r"""
        () => {
          const normalize = (value) => (value || '').replace(/\s+/g, ' ').trim();
          const rows = [];
          const selectors = [
            'tr',
            '[role="row"]',
            'li',
            '[class*="cart" i]',
            '[id*="cart" i]',
            '[class*="class" i]',
            '[id*="class" i]',
            '[class*="course" i]',
            '[id*="course" i]',
            '.ps_box-group',
            '.psc_rowact'
          ];

          for (const selector of selectors) {
            for (const el of Array.from(document.querySelectorAll(selector))) {
              const text = normalize(el.innerText || el.textContent || '');
              if (text && text.length >= 8 && text.length <= 1200) rows.push(text);
            }
          }

          const bodyText = normalize(document.body ? document.body.innerText : '');
          return { rows, bodyText };
        }
        """
        all_rows: List[str] = []
        previews: List[str] = []

        for frame in page.frames:
            try:
                result = frame.evaluate(script)
            except Exception:
                continue
            rows = result.get("rows", []) if isinstance(result, dict) else []
            body_text = result.get("bodyText", "") if isinstance(result, dict) else ""
            if isinstance(rows, list):
                all_rows.extend(str(row) for row in rows if str(row).strip())
            if body_text:
                previews.append(str(body_text))
                all_rows.extend(self._windowed_lines(str(body_text)))

        deduped: List[str] = []
        seen = set()
        for row in all_rows:
            normalized = re.sub(r"\s+", " ", row).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)

        return deduped, "\n".join(previews)

    def _windowed_lines(self, text: str) -> List[str]:
        lines = [line.strip() for line in re.split(r"[\r\n]+", text) if line.strip()]
        windows: List[str] = []
        for index, line in enumerate(lines):
            if self._looks_course_related(line):
                start = max(0, index - 2)
                end = min(len(lines), index + 5)
                windows.append(" ".join(lines[start:end]))
        return windows

    def _parse_courses(self, candidates: List[str]) -> List[CartCourse]:
        courses: List[CartCourse] = []
        seen = set()
        for text in candidates:
            if not self._looks_course_related(text):
                continue
            if len(re.findall(r"\(\s*\d{3,6}\s*\)", text)) > 1:
                continue
            course = self._parse_course_text(text)
            key = course.class_nbr or (course.name, course.section, course.source_text[:80])
            if not course.name and not course.class_nbr:
                continue
            if key in seen:
                continue
            seen.add(key)
            courses.append(course)
        return courses

    def _looks_course_related(self, text: str) -> bool:
        return bool(
            re.search(r"\b[A-Z]{2,6}\s*\d{3,4}[A-Z]?\b", text)
            or re.search(r"\bClass\s*(?:Nbr|Number|No\.?|#)?\s*:?\s*\d{3,6}\b", text, re.I)
            or re.search(r"\bclassNbr\b", text, re.I)
            or re.search(r"\(\s*\d{3,6}\s*\)", text)
        )

    def _parse_course_text(self, text: str) -> CartCourse:
        normalized = re.sub(r"\s+", " ", text).strip()
        name = self._first_match(r"\b([A-Z]{2,6}\s*\d{3,4}[A-Z]?)\b", normalized)
        section = self._first_match(
            r"\b[A-Z]{2,6}\s*\d{3,4}[A-Z]?\s+([A-Z0-9]{3,6}-[A-Z]{2,4})\s*\(",
            normalized,
        )
        class_text = (
            self._first_match(r"\bClass\s*(?:Nbr|Number|No\.?|#)?\s*:?\s*(\d{3,6})\b", normalized, re.I)
            or self._first_match(r"\bclassNbr[\"'\s:=]+(\d{3,6})\b", normalized, re.I)
            or self._first_match(r"\(\s*(\d{3,6})\s*\)", normalized)
        )
        section = section or self._first_match(r"\bSection\s*:?\s*([A-Z0-9-]{1,12})\b", normalized, re.I)
        component = self._component_from_section(section) or self._first_match(
            r"\b(LEC|LAB|REC|SEM|DIS|IND|RSC)\b",
            normalized,
            re.I,
        ).upper()
        instructor = (
            self._first_match(
                r"\b\d{1,2}:\d{2}\s*(?:am|pm)\s+([A-Z][A-Za-z .'-]{2,80})\s+\d+\s+(?:Open|Closed|Wait|Full)",
                normalized,
                re.I,
            )
            or self._first_match(
                r"\b\d{1,2}:\d{2}\s*(?:am|pm)\s+([A-Z][A-Za-z .'-]{2,80})\s+(?:Open|Closed|Wait|Full)",
                normalized,
                re.I,
            )
            or self._first_match(
                r"\bInstructor\s*:?\s*([A-Z][A-Za-z .'-]{2,80})(?=\s+(?:Units|Class|Section|Status|Days|Room|$))",
                normalized,
                re.I,
            )
        )
        status = self._first_match(r"\b(Open|Closed|Wait\s*List|Full)\b", normalized, re.I)

        return CartCourse(
            name=name or "",
            class_nbr=int(class_text) if class_text else None,
            component=component,
            section=section or "",
            instructor=instructor.strip() if instructor else "",
            note=status.title() if status else "",
            source_text=normalized[:600],
        )

    def _component_from_section(self, section: str) -> str:
        if not section:
            return ""
        match = re.search(r"-(LEC|LAB|REC|SEM|DIS|IND|RSC)\b", section, re.I)
        return match.group(1).upper() if match else ""

    def _first_match(self, pattern: str, text: str, flags: int = 0) -> str:
        match = re.search(pattern, text, flags)
        return match.group(1).strip() if match else ""
