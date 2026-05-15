import tempfile
import unittest
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
    from pptx.util import Inches
except ModuleNotFoundError:
    Presentation = None
    MSO_AUTO_SHAPE_TYPE = None
    Inches = None

from backend.app import create_app
from backend.chart_generator import generate_chart
from backend.insert_to_pptx import insert_chart_to_pptx
from backend.pipeline import PIPELINE_NODES, export_pipeline_mermaid, run_pipeline
from backend.ppt_parser import extract_slide_content, table_to_dataframe
from backend.schemas import PipelineInput
from backend.services import allowed_file, build_file_metadata, process_local_ppt


class PipelineTests(unittest.TestCase):
    def test_pipeline_nodes_are_defined_for_week_one(self):
        self.assertEqual(
            PIPELINE_NODES,
            [
                "parse_ppt",
                "semantic_analysis",
                "generate_chart",
                "generate_illustration",
                "save_pptx",
            ],
        )

    def test_mermaid_definition_contains_full_flow(self):
        mermaid = export_pipeline_mermaid()
        self.assertIn("parse_ppt", mermaid)
        self.assertIn("save_pptx", mermaid)

    def test_run_pipeline_returns_expected_placeholders(self):
        result = run_pipeline(PipelineInput(ppt_path="demo.pptx", current_slide=2))
        self.assertEqual(result["intent"]["chart_type"], "bar")
        self.assertTrue(result["chart_image"].endswith("chart_slide_2.png"))
        self.assertTrue(result["final_pptx_path"].endswith("demo_enhanced.pptx"))
        self.assertGreaterEqual(len(result["logs"]), 5)


class ServiceTests(unittest.TestCase):
    def test_allowed_file_only_accepts_pptx(self):
        self.assertTrue(allowed_file("demo.pptx"))
        self.assertFalse(allowed_file("demo.pdf"))

    def test_file_metadata_tracks_slide_number(self):
        with tempfile.NamedTemporaryFile(suffix=".pptx") as tmp:
            metadata = build_file_metadata(Path(tmp.name), 3)
            self.assertEqual(metadata["slide_number"], 3)
            self.assertEqual(metadata["suffix"], ".pptx")

    def test_process_local_ppt_runs_pipeline(self):
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            tmp.write(b"placeholder")
            tmp_path = Path(tmp.name)
        try:
            payload = process_local_ppt(tmp_path, 1)
            self.assertEqual(payload["file"]["slide_number"], 1)
            self.assertIn("pipeline", payload)
        finally:
            tmp_path.unlink(missing_ok=True)


@unittest.skipUnless(Presentation is not None, "python-pptx is not installed")
class PptModuleTests(unittest.TestCase):
    def _build_sample_ppt(self) -> Path:
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])

        title = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(4.5), Inches(0.6))
        title.text_frame.text = "Quarterly Revenue"

        note = slide.shapes.add_textbox(Inches(0.5), Inches(1.1), Inches(5.0), Inches(0.8))
        note.text_frame.text = "Summary slide for chart insertion testing."

        slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            Inches(6.2),
            Inches(0.6),
            Inches(2.0),
            Inches(0.8),
        ).text_frame.text = "Highlight"

        table = slide.shapes.add_table(4, 3, Inches(0.5), Inches(2.0), Inches(5.5), Inches(2.0)).table
        table.cell(0, 0).text = "month"
        table.cell(0, 1).text = "sales"
        table.cell(0, 2).text = "profit"
        table.cell(1, 0).text = "Jan"
        table.cell(1, 1).text = "120"
        table.cell(1, 2).text = "20"
        table.cell(2, 0).text = "Feb"
        table.cell(2, 1).text = "150"
        table.cell(2, 2).text = "35"
        table.cell(3, 0).text = "Mar"
        table.cell(3, 1).text = "180"
        table.cell(3, 2).text = "40"

        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            presentation.save(tmp.name)
            return Path(tmp.name)

    def _build_merged_table_ppt(self) -> Path:
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        table = slide.shapes.add_table(4, 3, Inches(0.5), Inches(1.0), Inches(5.5), Inches(2.0)).table

        table.cell(0, 0).text = "Region"
        table.cell(0, 1).text = "Revenue"
        table.cell(0, 2).text = "Profit"
        table.cell(1, 0).text = "North"
        table.cell(2, 0).text = "South"
        table.cell(1, 1).text = "120"
        table.cell(1, 2).text = "20"
        table.cell(2, 1).text = "150"
        table.cell(2, 2).text = "35"
        table.cell(3, 0).text = "Total"
        table.cell(3, 1).text = "270"
        table.cell(3, 2).text = "55"

        table.cell(1, 0).merge(table.cell(2, 0))

        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            presentation.save(tmp.name)
            return Path(tmp.name)

    def test_table_to_dataframe_resolves_merged_cells(self):
        ppt_path = self._build_merged_table_ppt()
        try:
            parsed = extract_slide_content(ppt_path, 1)
            dataframe = table_to_dataframe(Presentation(str(ppt_path)).slides[0].shapes[0].table)
            self.assertEqual(dataframe.columns.tolist(), ["Region", "Revenue", "Profit"])
            self.assertEqual(dataframe.iloc[0].to_dict(), {"Region": "North", "Revenue": "120", "Profit": "20"})
            self.assertEqual(dataframe.iloc[1].to_dict(), {"Region": "North", "Revenue": "150", "Profit": "35"})
            self.assertTrue(parsed.tables[0]["cell_matrix"][1][0]["is_merge_origin"])
            self.assertTrue(parsed.tables[0]["cell_matrix"][2][0]["is_spanned"])
        finally:
            ppt_path.unlink(missing_ok=True)

    def test_insert_chart_to_pptx_replaces_table_region(self):
        ppt_path = self._build_sample_ppt()
        output_chart = Path(tempfile.gettempdir()) / "insert_test_chart.png"
        output_ppt = Path(tempfile.gettempdir()) / "insert_test_output.pptx"
        try:
            parsed = extract_slide_content(ppt_path, 1)
            table = parsed.tables[0]
            records = [dict(zip(table["columns"], row)) for row in table["rows"]]
            chart = generate_chart(records, "bar", output_path=output_chart, title="Revenue Overview")
            result = insert_chart_to_pptx(
                ppt_path=ppt_path,
                chart_image_path=chart.output_path,
                slide_number=1,
                chart_title=chart.title,
                chart_spec=chart.to_dict(),
                shapes=parsed.shapes,
                output_path=output_ppt,
            )
            self.assertTrue(Path(result.output_path).exists())
            self.assertTrue(result.replaced_table)
            enhanced = Presentation(result.output_path)
            self.assertEqual(len(enhanced.slides), 1)
            self.assertFalse(any(getattr(shape, "has_table", False) for shape in enhanced.slides[0].shapes))
        finally:
            ppt_path.unlink(missing_ok=True)
            output_chart.unlink(missing_ok=True)
            output_ppt.unlink(missing_ok=True)


class AppTests(unittest.TestCase):
    def test_create_app_registers_expected_routes(self):
        app = create_app()
        route_paths = {route.path for route in app.routes}
        self.assertIn("/api/health", route_paths)
        self.assertIn("/api/pipeline", route_paths)
        self.assertIn("/api/process", route_paths)


if __name__ == "__main__":
    unittest.main()