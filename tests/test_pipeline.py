import tempfile
import unittest
from pathlib import Path

from backend.app import create_app
from backend.pipeline import PIPELINE_NODES, export_pipeline_mermaid, run_pipeline
from backend.schemas import PipelineInput
from backend.services import (
    allowed_file,
    build_file_metadata,
    extract_records_from_text,
    path_to_asset_url,
    process_demo_text,
    process_local_ppt,
)


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
        self.assertIn(result["intent"]["chart_type"], {"bar", "line", "pie"})
        self.assertIn("chart_slide_2", result["chart_image"])
        self.assertTrue(result["final_pptx_path"].endswith("demo_enhanced.pptx"))
        self.assertGreaterEqual(len(result["logs"]), 6)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["progress"], 100)
        self.assertEqual(len(result["stage_history"]), 5)


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
            self.assertIn("chart_image_url", payload["pipeline"])
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_extract_records_from_text_supports_demo_mode(self):
        records = extract_records_from_text("营收: 120\n利润: 45")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["category"], "营收")

    def test_process_demo_text_returns_preview_assets(self):
        payload = process_demo_text("Q1: 12\nQ2: 18\nQ3: 26")
        self.assertEqual(payload["pipeline"]["status"], "completed")
        self.assertTrue(payload["pipeline"]["chart_image_url"].startswith("/assets/outputs/"))

    def test_path_to_asset_url_maps_output_files(self):
        self.assertEqual(path_to_asset_url("outputs/demo.png"), "/assets/outputs/demo.png")


class AppTests(unittest.TestCase):
    def test_create_app_registers_expected_routes(self):
        app = create_app()
        route_paths = {route.path for route in app.routes}
        self.assertIn("/api/health", route_paths)
        self.assertIn("/api/pipeline", route_paths)
        self.assertIn("/api/process", route_paths)
        self.assertIn("/api/demo-chart", route_paths)


if __name__ == "__main__":
    unittest.main()
