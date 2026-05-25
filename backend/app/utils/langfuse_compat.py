"""LangFuse API 字段名兼容层

将 LangFuse 的 camelCase 字段映射到 AgentDevInsight 内部字段名。
"""

LANG_FUSE_TO_INTERNAL_TRACE = {
    "id": "trace_id",
    "name": "name",
    "userId": "user_id",
    "sessionId": "session_id",
    "tags": "tags",
    "metadata": "metadata",
    "release": "release",
    "version": "version",
    "timestamp": "started_at",
    "projectId": "project_id",
}

LANG_FUSE_TO_INTERNAL_SPAN = {
    "id": "span_id",
    "traceId": "trace_id",
    "parentObservationId": "parent_span_id",
    "name": "name",
    "type": "type",
    "input": "input",
    "output": "output",
    "metadata": "metadata",
    "model": "model",
    "startTime": "started_at",
    "endTime": "ended_at",
    "usage": "usage",
    "statusMessage": "error_message",
    "level": "level",
}

LANG_FUSE_TO_INTERNAL_GENERATION = {
    "id": "id",
    "traceId": "trace_id",
    "spanId": "span_id",
    "name": "name",
    "model": "model",
    "input": "prompt",
    "output": "completion",
    "usage": "usage",
    "startTime": None,  # Generation uses Span's timing
    "modelParameters": None,
    "usageDetails": None,
    "costDetails": None,
    "level": "level",
    "statusMessage": None,
    "version": None,
}

LANG_FUSE_TO_INTERNAL_SCORE = {
    "id": "id",
    "traceId": "trace_id",
    "observationId": "span_id",
    "name": "name",
    "value": "value",
    "comment": "comment",
    "configId": "config_id",
}


def _translate(data: dict, mapping: dict) -> dict:
    """将 LangFuse 格式数据转换为内部格式"""
    result: dict = {}
    for lf_key, internal_key in mapping.items():
        if lf_key in data:
            if internal_key is not None:
                result[internal_key] = data[lf_key]
    return result


def trace_from_langfuse(data: dict) -> dict:
    return _translate(data, LANG_FUSE_TO_INTERNAL_TRACE)


def span_from_langfuse(data: dict) -> dict:
    result = _translate(data, LANG_FUSE_TO_INTERNAL_SPAN)
    # Map parent_span_id from parentObservationId
    if "parent_span_id" in result and not result["parent_span_id"]:
        del result["parent_span_id"]
    return result


def generation_from_langfuse(data: dict) -> dict:
    return _translate(data, LANG_FUSE_TO_INTERNAL_GENERATION)


def score_from_langfuse(data: dict) -> dict:
    return _translate(data, LANG_FUSE_TO_INTERNAL_SCORE)
