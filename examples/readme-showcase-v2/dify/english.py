"""English copy keyed by canonical IDs; topology and evidence are never translated."""
import copy

ENTITIES = {
    "web": ("Web console", "Browser client\nUpload · create"),
    "nginx": ("Nginx", "Reverse proxy\nURL routing"),
    "caller": ("API client", "Chat requests\nStreamed replies"),
    "api": ("API service", "Chat · RAG\nIn-process thread"),
    "worker": ("Indexer", "Celery worker\nExtract · split"),
    "plugin": ("Plugins", "Plugin Daemon\nModel boundary"),
    "files": ("File store", "Original files\nLocal by default"),
    "redis": ("Redis", "Task broker\nQuery vector cache"),
    "sql": ("SQL store", "Metadata · chunks\nPostgreSQL here"),
    "vector": ("Vector DB", "Document vectors\nWeaviate here"),
}
RELATIONS = {
    "web-nginx": "Upload / create", "caller-nginx": "Ask / SSE",
    "nginx-api": "API request / reply", "api-files": "Store file",
    "api-sql": "Store metadata", "api-redis": "Tasks / query cache",
    "redis-worker": "Consume index job", "worker-files": "Read source file",
    "worker-sql": "Store chunks", "worker-vector": "Write index",
    "api-vector": "Semantic search", "worker-plugin": "Embed documents",
    "api-plugin": "Embedding / LLM",
}
GROUPS = {"access": "01  Access · Requests",
          "services": "02  Execution · API and indexing",
          "data": "03  Data · Files, tasks and vectors"}
FLOWS = {"index-path": "Index dispatch and write", "retrieval-path": "Retrieval within chat"}
VIEWS = {"ingest": "Document ingestion", "query": "Online chat"}
BEHAVIORS = {
    "thread-not-celery": "Basic CHAT uses ChatAppGenerator to create a threading.Thread and call ChatAppRunner. This worker thread lives in the API process; it is not a Celery Worker.",
    "separate-storage": "storage.save stores uploaded file bytes; SQL stores UploadFile metadata.",
    "commit-before-queue": "Document creation commits SQL before dispatching an indexing task through DocumentIndexingTaskProxy.delay.",
    "cache-condition": "A Redis query-embedding cache hit returns the cached vector. Not every retrieval calls an embedding model.",
    "retrieval-condition": "Retrieval here requires a configured and selected internal dataset. Single-dataset routing may call an LLM first; this is not a strict sequence diagram.",
    "plugin-boundary": "The main repository calls Plugin Daemon model endpoints over HTTP. This review does not cover the daemon implementation or specific model-provider plugins.",
}


def localize_plan(plan: dict) -> dict:
    result = copy.deepcopy(plan)
    semantic = result["semantic"]
    semantic.update(language="en", title="Dify · From documents to answers",
                    subtitle="1.17.0 · Three layers · Knowledge ingestion and basic Chat",
                    summary="Blue: document ingestion. Green: online chat. Gray: shared interfaces. Arrows show selected calls or task delivery, not timing, all dependencies, or one global execution order.")
    semantic["intent"].update(
        primary_question="Which services handle indexing and online chat, and what does each read or write?",
        audience=["Developers new to Dify architecture"],
        scope="Self-hosted Dify 1.17.0; local text uploads; high_quality paragraph indexing; basic AppMode.CHAT; a configured and selected internal dataset with semantic_search; successful paths.",
        exclusions=[
            "Not all of Dify: Workflow, Chatflow, Agent, knowledge pipelines, multimodal processing, reranking, errors and retries are excluded.",
            "Three logical layers are not three deployed services. Chat and RAG are internal API code, not separate microservices. Other app modes may use asynchronous queues.",
            "Model calls are traced only to the Plugin Daemon HTTP interface. Plugin execution and downstream providers were not reviewed, so downstream edges are not drawn.",
            "Other SQL/Redis consumers, Web server hosting, authentication, callback details and cache-hit branches are omitted from the overview.",
            "Dify has not been run and no real model calls were made. Independent semantic review is pending.",
        ])
    for entity in semantic["entities"]:
        entity["label"], entity["description"] = ENTITIES[entity["id"]]
    for field, labels in (("relations", RELATIONS), ("groups", GROUPS), ("flows", FLOWS)):
        for item in semantic[field]:
            item["label"] = labels[item["id"]]
    for view in result["reader"]["views"]:
        view["label"] = VIEWS[view["id"]]
    return result


def localize_facts(facts: dict) -> dict:
    result = copy.deepcopy(facts)
    for claim in result["claims"]:
        if claim["predicate"] == "behavior":
            claim["object"] = BEHAVIORS[claim["id"]]
    return result
