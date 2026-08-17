"""Extract caller-callee occurrences from srcML XML documents."""

import xml.etree.ElementTree as ET

from call_occurrence import CallOccurrence
from exceptions import SrcMLParseError

SRCML_NAMESPACE = "http://www.srcML.org/srcML/src"


def qualified_name(local_name: str) -> str:
    """Build a tag name qualified with the srcML source namespace."""

    return f"{{{SRCML_NAMESPACE}}}{local_name}"


class SrcMLCallParser:
    """Extract every syntactic call occurrence from srcML XML."""

    def parse(
        self,
        xml_content: bytes,
        project: str,
        file: str,
    ) -> tuple[CallOccurrence, ...]:
        """Return calls assigned to their nearest lexical function."""

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as exc:
            raise SrcMLParseError(f"invalid srcML XML for '{file}': {exc}") from exc

        occurrences: list[CallOccurrence] = []
        function_tag = qualified_name("function")
        call_tag = qualified_name("call")
        name_tag = qualified_name("name")

        # Carry the nearest lexical function through the XML tree. Iterating
        # over every function and then all of its descendants would count a
        # call in a GNU C nested function once for the nested function and
        # again for each enclosing function.
        stack: list[tuple[ET.Element, str | None]] = [(root, None)]
        while stack:
            element, caller = stack.pop()

            if element.tag == function_tag:
                caller_element = element.find(name_tag)
                caller = self._element_text(caller_element) or "<anonymous>"

            if element.tag == call_tag and caller is not None:
                callee_element = element.find(name_tag)
                callee = self._element_text(callee_element) or "<unknown>"
                occurrences.append(
                    CallOccurrence(
                        project=project,
                        file=file,
                        caller=caller,
                        callee=callee,
                    )
                )

            # A LIFO stack needs reversed children to retain srcML document
            # order in the resulting CSV.
            stack.extend((child, caller) for child in reversed(element))

        return tuple(occurrences)

    @staticmethod
    def _element_text(element: ET.Element | None) -> str:
        """Join text fragments from simple and compound srcML names."""

        if element is None:
            return ""
        return "".join(
            text.strip()
            for text in element.itertext()
            if text.strip()
        )
