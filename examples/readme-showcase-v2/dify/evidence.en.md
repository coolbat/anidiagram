# Dify case study draft: from documents to answers

[English](evidence.en.md) · [中文](evidence.md)

Status: source-reading draft. Independent semantic review is pending. Dify and real model calls have not been run.

- Pinned version: 1.17.0, `09a855dcef24c0edc7431c46c0cfaa494481daf5`.
- Repository: https://github.com/langgenius/dify
- Scope: self-hosted, local text files, high_quality paragraph indexing, basic CHAT with a configured and selected internal dataset, semantic retrieval, successful paths.
- Excluded: Workflow, Chatflow, Agent, knowledge pipelines, multimodal processing, reranking and failure branches. This is not all of Dify.
- The target repository is not executed. Compose establishes deployment boundaries/configuration, not runtime calls; call relationships are supported by specific implementations.

## Two paths

Document ingestion: the console reaches the API through Nginx. File bytes go to storage; file/document metadata is committed to SQL. Creating a document then dispatches a Celery task. The Worker consumes the task, loads the file, extracts and splits it, and stores chunks. A document-embedding cache miss invokes a model interface before vectors are written to the vector database.

Online chat: Service API requests reach the API through Nginx. Basic CHAT runs a worker thread inside the API process. Once configuration/routing selects an internal dataset, the code performs semantic retrieval, assembles context, invokes the model and streams the answer back. Query embeddings have a Redis cache. Single-dataset routing may also call an LLM first; the diagram is not a strict execution sequence.

The three layers are logical groups, not a container count. API and Celery Worker may share an image but are separate services. The overview shows selected interactions, not every SQL/Redis consumer. The shared “Tasks / query cache” edge represents task dispatch in the ingestion view and cache access in the chat view.

## Key evidence at the pinned SHA

| Claim | Source |
| --- | --- |
| Nginx routes console/API/v1 requests | [default.conf.template L8–45](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/docker/nginx/conf.d/default.conf.template#L8-L45) |
| File bytes and SQL metadata are stored separately | [file_service.py L99–125](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/services/file_service.py#L99-L125) |
| Document commit precedes indexing dispatch | [dataset_service.py L2482–2499](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/services/dataset_service.py#L2482-L2499) |
| Self-hosted dispatch uses the priority queue | [proxy/base.py L79–111](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/services/document_indexing_proxy/base.py#L79-L111) |
| Worker extracts, transforms, stores chunks and loads the index | [indexing_runner.py L81–159](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/core/indexing_runner.py#L81-L159) |
| Embedding precedes vector-index writes | [vector_factory.py L168–189](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/core/rag/datasource/vdb/vector_factory.py#L168-L189) |
| The CHAT worker thread is not a Celery Worker | [chat/app_generator.py L208–272](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/core/app/apps/chat/app_generator.py#L208-L272) |
| Retrieved context feeds the final LLM prompt | [chat/app_runner.py L160–256](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/core/app/apps/chat/app_runner.py#L160-L256) |
| A query-embedding cache hit returns immediately | [cached_embedding.py L194–241](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/core/rag/embedding/cached_embedding.py#L194-L241) |
| Model calls reach a plugin-service HTTP boundary | [plugin/impl/model.py L170–217](https://github.com/langgenius/dify/blob/09a855dcef24c0edc7431c46c0cfaa494481daf5/api/core/plugin/impl/model.py#L170-L217) |

All 32 references and full edge conditions are in `dify-en.plan.json`. All 23 required claims are in `facts.en.json`. Definition existence and pending semantic review are separate states in `accuracy.en.json`. Authored relation facts matching the diagram establish consistency, not an independently measured accuracy rate.

Plugin Daemon internals and model-provider code are outside this review. No extra provider node is drawn to imply that those implementations have been examined.

## Reproduce both languages

Run from the AniDiagram repository with Python 3.10+, Pillow, Playwright and its existing GSAP dependency. The animated preview needs a browser: use Playwright Chromium, or pass `--browser-channel chrome` to reuse an installed Chrome. No dependency is installed automatically. Do not install Dify dependencies.

```bash
git clone --branch 1.17.0 --depth 1 https://github.com/langgenius/dify.git outputs/readme-showcase-v2/source/dify-1.17.0
python3 examples/readme-showcase-v2/dify/build.py --source outputs/readme-showcase-v2/source/dify-1.17.0
python3 -m unittest discover -s examples/readme-showcase-v2/dify -p 'test_*.py'
python3 -I scripts/run_anidiagram.py visual-check outputs/readme-showcase-v2/dify/dify-en.html --strict-labels --viewports 1440x1100,1920x1320 --outdir outputs/readme-showcase-v2/dify/visual-en
python3 -m http.server 8769 --bind 127.0.0.1 --directory outputs/readme-showcase-v2/dify
```

Skip cloning if the checkout exists. The builder rejects a dirty source tree or a different full SHA. Open `index.en.html` for English or `index.html` for Chinese.

Both languages are derived from the same canonical topology. Stable IDs, endpoints, direction, conditions, grouping, path selection and source references remain identical; English copy is keyed by IDs in `english.py`. Each language has its own fact report and delivery receipts; a review of one artifact is not silently reused for the other.

The static variant disables motion without changing meaning. The animated WebP is captured from the delivered readable HTML, preserving all labels and using the existing ten icon performances. Its motion receipt binds the HTML and image hashes; tests check changes inside every icon region, not only moving edges. The case page can pause to a static SVG and defaults to static for reduced-motion preferences or without JavaScript. Presentation uses explicit aliases to public icons while retaining semantic kinds. A 900×1130 vertical layout preserves legibility at an 840 px README content width; narrow screens should use the interactive viewer for details.

## Acceptance boundaries

- Source references: checked during build; inspect the delivery and accuracy reports.
- Semantics: based on the author's prior source reading; independent review remains pending. Translation does not add semantic validation.
- Runtime: Dify has not been started; no provider API calls were made.
- Rendering: inspect each language's quality, visual and preview reports. Rendering does not prove architecture accuracy.
- Publication: the repository includes this bilingual draft under `gallery/cases/dify/`. GitHub Pages deployment is a separate gate; publication does not change the pending semantic-review status.

## Publish the frozen bundle

After building, run `python3 examples/readme-showcase-v2/dify/publish.py` from the repository root. It verifies the build manifest before copying its allowlisted files to `gallery/cases/dify/`. Rendered SVG/HTML bytes and evidence are preserved. Only local path locators in delivery receipts are made portable; the publication manifest records the original receipt hashes and the new file hashes. Temporary screenshots and the Dify checkout are not copied.
