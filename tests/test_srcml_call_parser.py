"""Test srcML XML parsing and caller-to-callee assignment."""

import unittest
from pathlib import Path

from exceptions import SrcMLParseError
from srcml_call_parser import SrcMLCallParser

FIXTURE = Path(__file__).parent / "fixtures" / "sample_srcml.xml"


class SrcMLCallParserTests(unittest.TestCase):
    """Verify extraction rules for srcML call elements."""

    def test_extracts_every_call_occurrence_without_deduplication(self) -> None:
        """Preserve order, repeated calls, and compound callee names."""

        occurrences = SrcMLCallParser().parse(
            FIXTURE.read_bytes(),
            project="sample",
            file="src/sample.c",
        )

        self.assertEqual(
            [
                ("sample", "src/sample.c", "caller", "callee"),
                ("sample", "src/sample.c", "caller", "callee"),
                ("sample", "src/sample.c", "caller", "callbacks->run"),
                ("sample", "src/sample.c", "caller", "outer"),
                ("sample", "src/sample.c", "caller", "inner"),
                ("sample", "src/sample.c", "second_caller", "callee"),
            ],
            [occurrence.to_csv_row() for occurrence in occurrences],
        )

    def test_rejects_malformed_xml(self) -> None:
        """Wrap malformed XML errors in SrcMLParseError."""

        with self.assertRaises(SrcMLParseError):
            SrcMLCallParser().parse(b"<unit>", "project", "file.c")

    def test_assigns_calls_only_to_the_nearest_nested_function(self) -> None:
        """Do not attribute nested-function calls to enclosing functions."""

        xml_content = b"""\
        <unit xmlns="http://www.srcML.org/srcML/src">
          <call><name>global_initializer</name><argument_list>()</argument_list></call>
          <function>
            <type><name>void</name></type>
            <name>outer</name>
            <block><block_content>
              <call><name>before</name><argument_list>()</argument_list></call>
              <function>
                <type><name>void</name></type>
                <name>nested</name>
                <block><block_content>
                  <call><name>inside</name><argument_list>()</argument_list></call>
                </block_content></block>
              </function>
              <call><name>after</name><argument_list>()</argument_list></call>
            </block_content></block>
          </function>
        </unit>
        """

        occurrences = SrcMLCallParser().parse(
            xml_content,
            project="sample",
            file="nested.c",
        )

        self.assertEqual(
            [
                ("sample", "nested.c", "outer", "before"),
                ("sample", "nested.c", "nested", "inside"),
                ("sample", "nested.c", "outer", "after"),
            ],
            [occurrence.to_csv_row() for occurrence in occurrences],
        )


if __name__ == "__main__":
    unittest.main()
