from app.services.analysis_agent import AnalysisAgent


def test_parse_response_reads_valid_json():
    agent = AnalysisAgent()
    raw = """
    {
      "summary": "Looks good",
      "quality_score": 88,
      "issues": [
        {
          "file_path": "src/app.py",
          "line_start": 12,
          "line_end": 12,
          "severity": "high",
          "category": "security",
          "message": "Unsafe eval",
          "recommendation": "Remove eval"
        }
      ]
    }
    """
    parsed = agent._parse_response(raw)
    assert parsed is not None
    assert parsed.summary == "Looks good"
    assert parsed.quality_score == 88
    assert len(parsed.issues) == 1


def test_parse_response_handles_code_fence_wrapping():
    agent = AnalysisAgent()
    raw = """```json
{"summary":"x","quality_score":50,"issues":[]}
```"""
    parsed = agent._parse_response(raw)
    assert parsed is not None
    assert parsed.summary == "x"
    assert parsed.quality_score == 50


def test_parse_response_returns_none_for_non_json_text():
    agent = AnalysisAgent()
    parsed = agent._parse_response("not a json payload")
    assert parsed is None
