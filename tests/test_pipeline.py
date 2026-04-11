import tempfile
import unittest
from pathlib import Path

from app import allowed_file, build_file_metadata, process_local_ppt
from main_pipeline import PIPELINE_NODES, PipelineInput, export_pipeline_mermaid, run_pipeline


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


class AppHelpersTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
