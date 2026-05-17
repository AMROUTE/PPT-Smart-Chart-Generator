# Project Context

## Domain

PPT-Smart-Chart-Generator is a semantic PPT chart and illustration generation system. It accepts PowerPoint files or demo text, analyzes slide content, generates chart PNGs and illustration PNGs, and writes generated assets back into enhanced PPTX files.

## Core Terms

- **PPT mode**: User flow where a `.pptx` file is uploaded, parsed, previewed slide by slide, processed, and exported as an enhanced PPTX.
- **Demo text mode**: User flow where plain text records are converted directly into chart data and generated assets.
- **Semantic analysis**: The step that recommends chart type, keywords, visual intent, and structured chart data from slide or text content.
- **Local semantic mode**: Rule-based semantic analysis used when no external model is enabled or when a provider fails.
- **Qwen semantic mode**: Semantic analysis through the Qwen API, with local fallback behavior.
- **Chart generation**: Rendering structured records into PNG charts such as bar, line, pie, scatter, histogram, box, and heatmap charts.
- **Illustration generation**: Producing an illustration PNG through local fallback rendering, WANX, or Flux.
- **Pipeline**: Backend orchestration flow that parses input, runs semantic analysis, generates chart and illustration assets, and saves the enhanced PPTX.
- **Slide preview**: Lightweight rendered preview used for page selection, not a native pixel-perfect PowerPoint screenshot.
- **Asset insertion**: Writing generated chart and illustration PNGs into the output PPTX.
- **Graceful fallback**: Provider failures should not break the whole flow; the app should fall back to local previews or rule-based behavior.

## Architecture Notes

- Backend entrypoint: `app.py`.
- Backend modules live in `backend/` and follow a pipeline-oriented FastAPI architecture.
- Frontend lives in `frontend/` and uses Vue 3 with Vite.
- User-facing docs and milestone notes live in `README.md` and `docs/`.
- Generated outputs, previews, logs, uploads, and local data should remain outside core logic.

## Testing Expectations

- Backend changes should start with focused tests such as `python -m unittest tests.test_pipeline` when relevant.
- Frontend validation should use the existing Vite workflow, especially `npm run build` in `frontend/`.
- External provider behavior should keep local fallbacks intact.
