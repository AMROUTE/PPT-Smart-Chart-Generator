import pytest
from main_pipeline import app

def test_pipeline_structure():
    assert app is not None
    print("✅ Pipeline 结构测试通过")