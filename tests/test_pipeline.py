import os
import tempfile
import unittest
from pathlib import Path

os.environ["ENABLE_QWEN_API"] = "0"
os.environ["DATABASE_PATH"] = str(Path(tempfile.gettempdir()) / "codex-test-app.db")

try:
    from PIL import Image
    from pptx import Presentation
    from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
    from pptx.util import Inches
except ModuleNotFoundError:
    Image = None
    Presentation = None
    MSO_AUTO_SHAPE_TYPE = None
    Inches = None

from fastapi.testclient import TestClient

from backend.app import create_app
from backend.chart_generator import generate_chart
from backend.database import authenticate_or_create_user, init_db
from backend.insert_to_pptx import insert_chart_to_pptx
from backend.pipeline import PIPELINE_NODES, export_pipeline_mermaid, run_pipeline
from backend.ppt_parser import extract_slide_content, table_to_dataframe
from backend.schemas import PipelineInput
from backend.services import (
    allowed_file,
    build_file_metadata,
    build_health_payload,
    build_slide_preview,
    extract_records_from_text,
    normalize_chart_theme,
    normalize_chart_type_override,
    normalize_image_model,
    normalize_illustration_style,
    parse_presentation_slides,
    path_to_asset_url,
    process_demo_text,
    process_ppt_batch,
    process_local_ppt,
    process_local_ppt_batch,
)


class PipelineTests(unittest.TestCase):
    def test_pipeline_nodes_are_defined_for_week_two(self):
        self.assertEqual(PIPELINE_NODES, ["parse_ppt", "semantic_analysis", "generate_chart", "generate_illustration", "save_pptx"])

    def test_mermaid_definition_contains_full_flow(self):
        mermaid = export_pipeline_mermaid()
        self.assertIn("parse_ppt", mermaid)
        self.assertIn("save_pptx", mermaid)

    def test_run_pipeline_returns_expected_placeholders(self):
        result = run_pipeline(PipelineInput(ppt_path="demo.pptx", current_slide=2, request_id="test-run"))
        self.assertIn(result["intent"]["chart_type"], {"bar", "line", "pie", "scatter", "heatmap"})
        self.assertIn("chart_slide_2", result["chart_image"])
        self.assertTrue(result["final_pptx_path"].endswith("demo_enhanced.pptx"))
        self.assertGreaterEqual(len(result["logs"]), 6)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["progress"], 100)
        self.assertEqual(len(result["stage_history"]), 5)


class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_allowed_file_only_accepts_pptx(self):
        self.assertTrue(allowed_file("demo.pptx"))
        self.assertFalse(allowed_file("demo.pdf"))

    def test_file_metadata_tracks_slide_number(self):
        with tempfile.NamedTemporaryFile(suffix=".pptx") as tmp:
            metadata = build_file_metadata(Path(tmp.name), 3)
            self.assertEqual(metadata["slide_number"], 3)
            self.assertEqual(metadata["suffix"], ".pptx")

    def test_process_local_ppt_runs_pipeline(self):
        if Presentation is None:
            self.skipTest("python-pptx is not installed")
        tmp_path = Path(tempfile.gettempdir()) / "codex-test-source.pptx"
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.shapes.add_textbox(1000000, 1000000, 4000000, 600000).text_frame.text = "Revenue trend analysis"
        table = slide.shapes.add_table(4, 2, 1000000, 1800000, 4000000, 2000000).table
        table.cell(0, 0).text = "Quarter"
        table.cell(0, 1).text = "Revenue"
        table.cell(1, 0).text = "Q1"
        table.cell(1, 1).text = "120"
        table.cell(2, 0).text = "Q2"
        table.cell(2, 1).text = "150"
        table.cell(3, 0).text = "Q3"
        table.cell(3, 1).text = "180"
        prs.save(tmp_path)
        try:
            payload = process_local_ppt(tmp_path, 1, chart_type_override="line", chart_theme="business", illustration_style="tech", image_model="flux")
            self.assertEqual(payload["file"]["slide_number"], 1)
            self.assertIn("pipeline", payload)
            self.assertIn("chart_image_url", payload["pipeline"])
            self.assertTrue(Path(payload["pipeline"]["final_pptx_path"]).exists())
            self.assertEqual(payload["pipeline"]["chart_spec"]["theme"], "business")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_process_local_ppt_batch_reuses_single_batch_output(self):
        if Presentation is None:
            self.skipTest("python-pptx is not installed")
        tmp_path = Path(tempfile.gettempdir()) / "codex-test-batch-source.pptx"
        prs = Presentation()
        for title, values in [("Revenue trend", [120, 150, 180]), ("Market share", [35, 25, 40])]:
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            slide.shapes.add_textbox(1000000, 1000000, 4000000, 600000).text_frame.text = title
            table = slide.shapes.add_table(4, 2, 1000000, 1800000, 4000000, 2000000).table
            table.cell(0, 0).text = "Label"
            table.cell(0, 1).text = "Value"
            table.cell(1, 0).text = "A"
            table.cell(1, 1).text = str(values[0])
            table.cell(2, 0).text = "B"
            table.cell(2, 1).text = str(values[1])
            table.cell(3, 0).text = "C"
            table.cell(3, 1).text = str(values[2])
        prs.save(tmp_path)
        try:
            payload = process_local_ppt_batch(tmp_path, [1, 2], chart_theme="academic", illustration_style="tech")
            self.assertEqual(payload["processed_count"], 2)
            self.assertEqual(payload["slide_numbers"], [1, 2])
            self.assertTrue(Path(payload["final_pptx_path"]).exists())
            self.assertTrue(all(slide["final_pptx_path"] == payload["final_pptx_path"] for slide in payload["slides"]))
            self.assertTrue(all(slide["chart_spec"]["theme"] == "academic" for slide in payload["slides"]))
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_process_ppt_batch_runs_selected_slide_range(self):
        if Presentation is None:
            self.skipTest("python-pptx is not installed")
        tmp_path = Path(tempfile.gettempdir()) / "codex-test-batch-source.pptx"
        prs = Presentation()
        for slide_index in range(1, 4):
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            slide.shapes.add_textbox(1000000, 700000, 5000000, 700000).text_frame.text = f"第 {slide_index} 页营收趋势"
            table = slide.shapes.add_table(4, 2, 1000000, 1800000, 4000000, 2000000).table
            table.cell(0, 0).text = "季度"
            table.cell(0, 1).text = "营收"
            table.cell(1, 0).text = "Q1"
            table.cell(1, 1).text = str(100 + slide_index)
            table.cell(2, 0).text = "Q2"
            table.cell(2, 1).text = str(140 + slide_index)
            table.cell(3, 0).text = "Q3"
            table.cell(3, 1).text = str(180 + slide_index)
        prs.save(tmp_path)
        try:
            payload = process_ppt_batch(
                tmp_path,
                slide_start=1,
                slide_end=2,
                chart_type_override="line",
                illustration_style="tech",
                image_model="local",
            )
            self.assertEqual(payload["batch"]["total_slides"], 2)
            self.assertEqual(payload["batch"]["success_count"], 2)
            self.assertEqual(payload["batch"]["failure_count"], 0)
            self.assertEqual([item["slide_number"] for item in payload["batch"]["slides"]], [1, 2])
            self.assertTrue(Path(payload["batch"]["final_pptx_path"]).exists())
            self.assertTrue(payload["batch"]["final_pptx_url"].startswith("/assets/outputs/"))
            self.assertTrue(payload["batch"]["slides"][0]["pipeline"]["chart_image_url"].startswith("/assets/outputs/"))
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_build_slide_preview_returns_preview_asset(self):
        if Presentation is None:
            self.skipTest("python-pptx is not installed")
        tmp_path = Path(tempfile.gettempdir()) / "codex-test-preview.pptx"
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.shapes.add_textbox(1000000, 1000000, 5000000, 1200000).text_frame.text = "First slide preview test"
        prs.save(tmp_path)
        try:
            payload = build_slide_preview(1, file_path=tmp_path)
            self.assertEqual(payload["slide_number"], 1)
            self.assertEqual(payload["slide_count"], 1)
            self.assertTrue(Path(payload["preview_image"]).exists())
            self.assertTrue(payload["preview_image_url"].startswith("/assets/outputs/"))
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_parse_presentation_slides_returns_outline(self):
        if Presentation is None:
            self.skipTest("python-pptx is not installed")
        tmp_path = Path(tempfile.gettempdir()) / "codex-test-outline.pptx"
        prs = Presentation()
        prs.slides.add_slide(prs.slide_layouts[6]).shapes.add_textbox(1000000, 1000000, 5000000, 1200000).text_frame.text = "Slide one"
        prs.slides.add_slide(prs.slide_layouts[6]).shapes.add_textbox(1000000, 1000000, 5000000, 1200000).text_frame.text = "Slide two"
        prs.save(tmp_path)
        try:
            payload = parse_presentation_slides(file_path=tmp_path)
            self.assertEqual(payload["slide_count"], 2)
            self.assertEqual(len(payload["slides"]), 2)
            self.assertEqual(payload["slides"][0]["slide_number"], 1)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_extract_records_from_text_supports_demo_mode(self):
        records = extract_records_from_text("Revenue: 120\nProfit: 45")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["category"], "Revenue")

    def test_process_demo_text_returns_preview_assets(self):
        payload = process_demo_text("Q1: 12\nQ2: 18\nQ3: 26", chart_type_override="pie", chart_theme="minimal", illustration_style="business", image_model="wanx")
        self.assertEqual(payload["pipeline"]["status"], "completed")
        self.assertTrue(payload["pipeline"]["chart_image_url"].startswith("/assets/outputs/"))
        self.assertEqual(payload["pipeline"]["intent"]["chart_type"], "pie")
        self.assertIn("clip_score", payload["pipeline"]["illustration_meta"])
        self.assertEqual(payload["pipeline"]["chart_spec"]["theme"], "minimal")
        self.assertIn(payload["pipeline"]["illustration_meta"]["generation_source"], {"local", "wanx", "flux"})

    def test_process_demo_text_falls_back_when_remote_image_model_is_unavailable(self):
        payload = process_demo_text("Revenue: 120\nCost: 80\nProfit: 40", illustration_style="tech", image_model="wanx")
        self.assertEqual(payload["pipeline"]["status"], "completed")
        self.assertEqual(payload["pipeline"]["illustration_meta"]["generation_source"], "local")
        self.assertTrue(Path(payload["pipeline"]["illustration_image"]).exists())

    def test_path_to_asset_url_maps_output_files(self):
        self.assertEqual(path_to_asset_url("outputs/demo.png"), "/assets/outputs/demo.png")

    def test_normalizers_accept_known_values(self):
        self.assertEqual(normalize_chart_theme("business"), "business")
        self.assertEqual(normalize_chart_theme("unknown"), "tech")
        self.assertEqual(normalize_chart_type_override("line"), "line")
        self.assertEqual(normalize_chart_type_override("auto"), "")
        self.assertEqual(normalize_illustration_style("tech"), "tech")
        self.assertEqual(normalize_image_model("wanx"), "wanx")


@unittest.skipUnless(Presentation is not None, "python-pptx is not installed")
class PptModuleTests(unittest.TestCase):
    def _build_sample_ppt(self) -> Path:
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(4.5), Inches(0.6)).text_frame.text = "Quarterly Revenue"
        slide.shapes.add_textbox(Inches(0.5), Inches(1.1), Inches(5.0), Inches(0.8)).text_frame.text = "Summary slide for chart insertion testing."
        slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(6.2), Inches(0.6), Inches(2.0), Inches(0.8)).text_frame.text = "Highlight"
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
            result = insert_chart_to_pptx(ppt_path=ppt_path, chart_image_path=chart.output_path, slide_number=1, chart_title=chart.title, chart_spec=chart.to_dict(), shapes=parsed.shapes, output_path=output_ppt)
            self.assertTrue(Path(result.output_path).exists())
            self.assertTrue(result.replaced_table)
            enhanced = Presentation(result.output_path)
            self.assertEqual(len(enhanced.slides), 1)
            self.assertFalse(any(getattr(shape, "has_table", False) for shape in enhanced.slides[0].shapes))
        finally:
            ppt_path.unlink(missing_ok=True)
            output_chart.unlink(missing_ok=True)
            output_ppt.unlink(missing_ok=True)


class ChartThemeTests(unittest.TestCase):
    def test_generate_chart_uses_tech_theme_background(self):
        if Image is None:
            self.skipTest("Pillow is not installed")
        output_chart = Path(tempfile.gettempdir()) / "tech_theme_chart.png"
        try:
            chart = generate_chart(
                [
                    {"month": "Jan", "sales": 120},
                    {"month": "Feb", "sales": 150},
                    {"month": "Mar", "sales": 180},
                ],
                "bar",
                output_path=output_chart,
                title="Theme Check",
            )
            image = Image.open(chart.output_path)
            self.assertEqual(image.getpixel((10, 10)), (7, 17, 31))
        finally:
            output_chart.unlink(missing_ok=True)


    def test_generate_chart_supports_business_theme(self):
        if Image is None:
            self.skipTest("Pillow is not installed")
        output_chart = Path(tempfile.gettempdir()) / "business_theme_chart.png"
        try:
            chart = generate_chart(
                [
                    {"month": "Jan", "sales": 120},
                    {"month": "Feb", "sales": 150},
                    {"month": "Mar", "sales": 180},
                ],
                "bar",
                output_path=output_chart,
                title="Business Theme Check",
                theme="business",
            )
            image = Image.open(chart.output_path)
            self.assertEqual(chart.theme, "business")
            self.assertEqual(image.getpixel((10, 10)), (244, 247, 251))
        finally:
            output_chart.unlink(missing_ok=True)


class AppTests(unittest.TestCase):
    def test_create_app_registers_expected_routes(self):
        app = create_app()
        route_paths = {route.path for route in app.routes}
        self.assertIn("/api/health", route_paths)
        self.assertIn("/api/pipeline", route_paths)
        self.assertIn("/api/process", route_paths)
        self.assertIn("/api/process-batch", route_paths)
        self.assertIn("/api/demo-chart", route_paths)
        self.assertIn("/api/slide-preview", route_paths)
        self.assertIn("/api/parse-slides", route_paths)
        self.assertIn("/api/auth/login", route_paths)
        self.assertIn("/api/jobs", route_paths)

    def test_health_payload_exposes_image_provider_flags(self):
        payload = build_health_payload()
        self.assertIn("wanx_enabled", payload)
        self.assertIn("flux_enabled", payload)
        self.assertIn("batch-processing", payload["features"])
        self.assertEqual(payload["database_engine"], "sqlite")

    def test_health_endpoint_returns_structured_payload(self):
        client = TestClient(create_app())
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("batch-processing", payload["features"])
        self.assertIsInstance(payload["database_enabled"], bool)

    def test_authenticate_or_create_user_persists_user(self):
        user = authenticate_or_create_user("codex-demo", "demo123")
        self.assertEqual(user["username"], "codex-demo")
        same_user = authenticate_or_create_user("codex-demo", "demo123")
        self.assertEqual(user["id"], same_user["id"])


if __name__ == "__main__":
    unittest.main()
