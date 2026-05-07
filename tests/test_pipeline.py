import tempfile
import unittest
from pathlib import Path
import os

os.environ["ENABLE_QWEN_API"] = "0"
os.environ["DATABASE_PATH"] = str(Path(tempfile.gettempdir()) / "codex-test-app.db")

from backend.app import create_app
from backend.database import authenticate_or_create_user, init_db
from backend.pipeline import PIPELINE_NODES, export_pipeline_mermaid, run_pipeline
from backend.schemas import PipelineInput
from backend.services import (
    allowed_file,
    parse_presentation_slides,
    build_slide_preview,
    build_file_metadata,
    build_health_payload,
    extract_records_from_text,
    normalize_chart_type_override,
    normalize_image_model,
    normalize_illustration_style,
    path_to_asset_url,
    process_demo_text,
    process_local_ppt,
)

try:
    from pptx import Presentation
except ModuleNotFoundError:  # pragma: no cover
    Presentation = None


class PipelineTests(unittest.TestCase):
    def test_pipeline_nodes_are_defined_for_week_two(self):
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
        textbox = slide.shapes.add_textbox(1000000, 1000000, 4000000, 600000)
        textbox.text_frame.text = "营收趋势分析"
        rows, cols = 4, 2
        table = slide.shapes.add_table(rows, cols, 1000000, 1800000, 4000000, 2000000).table
        table.cell(0, 0).text = "季度"
        table.cell(0, 1).text = "营收"
        table.cell(1, 0).text = "Q1"
        table.cell(1, 1).text = "120"
        table.cell(2, 0).text = "Q2"
        table.cell(2, 1).text = "150"
        table.cell(3, 0).text = "Q3"
        table.cell(3, 1).text = "180"
        prs.save(tmp_path)
        try:
            payload = process_local_ppt(
                tmp_path,
                1,
                chart_type_override="line",
                illustration_style="tech",
                image_model="flux",
            )
            self.assertEqual(payload["file"]["slide_number"], 1)
            self.assertIn("pipeline", payload)
            self.assertIn("chart_image_url", payload["pipeline"])
            self.assertTrue(Path(payload["pipeline"]["final_pptx_path"]).exists())
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_build_slide_preview_returns_preview_asset(self):
        if Presentation is None:
            self.skipTest("python-pptx is not installed")
        tmp_path = Path(tempfile.gettempdir()) / "codex-test-preview.pptx"
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        textbox = slide.shapes.add_textbox(1000000, 1000000, 5000000, 1200000)
        textbox.text_frame.text = "第一页预览测试"
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
        slide_one = prs.slides.add_slide(prs.slide_layouts[6])
        slide_one.shapes.add_textbox(1000000, 1000000, 5000000, 1200000).text_frame.text = "第一页标题"
        slide_two = prs.slides.add_slide(prs.slide_layouts[6])
        slide_two.shapes.add_textbox(1000000, 1000000, 5000000, 1200000).text_frame.text = "第二页内容"
        prs.save(tmp_path)
        try:
            payload = parse_presentation_slides(file_path=tmp_path)
            self.assertEqual(payload["slide_count"], 2)
            self.assertEqual(len(payload["slides"]), 2)
            self.assertEqual(payload["slides"][0]["slide_number"], 1)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_extract_records_from_text_supports_demo_mode(self):
        records = extract_records_from_text("营收: 120\n利润: 45")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["category"], "营收")

    def test_process_demo_text_returns_preview_assets(self):
        payload = process_demo_text(
            "Q1: 12\nQ2: 18\nQ3: 26",
            chart_type_override="pie",
            illustration_style="business",
            image_model="wanx",
        )
        self.assertEqual(payload["pipeline"]["status"], "completed")
        self.assertTrue(payload["pipeline"]["chart_image_url"].startswith("/assets/outputs/"))
        self.assertEqual(payload["pipeline"]["intent"]["chart_type"], "pie")
        self.assertIn("clip_score", payload["pipeline"]["illustration_meta"])
        self.assertIn(payload["pipeline"]["illustration_meta"]["generation_source"], {"local", "wanx", "flux"})

    def test_process_demo_text_falls_back_when_remote_image_model_is_unavailable(self):
        payload = process_demo_text(
            "营收: 120\n成本: 80\n利润: 40",
            illustration_style="tech",
            image_model="wanx",
        )
        self.assertEqual(payload["pipeline"]["status"], "completed")
        self.assertEqual(payload["pipeline"]["illustration_meta"]["generation_source"], "local")
        self.assertTrue(Path(payload["pipeline"]["illustration_image"]).exists())

    def test_path_to_asset_url_maps_output_files(self):
        self.assertEqual(path_to_asset_url("outputs/demo.png"), "/assets/outputs/demo.png")

    def test_normalizers_accept_known_values(self):
        self.assertEqual(normalize_chart_type_override("line"), "line")
        self.assertEqual(normalize_chart_type_override("auto"), "")
        self.assertEqual(normalize_illustration_style("tech"), "tech")
        self.assertEqual(normalize_image_model("wanx"), "wanx")


class AppTests(unittest.TestCase):
    def test_create_app_registers_expected_routes(self):
        app = create_app()
        route_paths = {route.path for route in app.routes}
        self.assertIn("/api/health", route_paths)
        self.assertIn("/api/pipeline", route_paths)
        self.assertIn("/api/process", route_paths)
        self.assertIn("/api/demo-chart", route_paths)
        self.assertIn("/api/slide-preview", route_paths)
        self.assertIn("/api/parse-slides", route_paths)
        self.assertIn("/api/auth/login", route_paths)
        self.assertIn("/api/jobs", route_paths)

    def test_health_payload_exposes_image_provider_flags(self):
        payload = build_health_payload()
        self.assertIn("wanx_enabled", payload)
        self.assertIn("flux_enabled", payload)
        self.assertEqual(payload["database_engine"], "sqlite")

    def test_authenticate_or_create_user_persists_user(self):
        user = authenticate_or_create_user("codex-demo", "demo123")
        self.assertEqual(user["username"], "codex-demo")
        same_user = authenticate_or_create_user("codex-demo", "demo123")
        self.assertEqual(user["id"], same_user["id"])


if __name__ == "__main__":
    unittest.main()
