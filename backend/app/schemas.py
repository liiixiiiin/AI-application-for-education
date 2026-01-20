from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str
    password: str = Field(min_length=6)
    role: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class CourseCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)


class CourseResponse(BaseModel):
    id: str
    title: str
    description: str
    creator_id: str
    created_at: str


class KnowledgePointResponse(BaseModel):
    id: str
    course_id: str
    point: str
    created_at: str


class KnowledgePointCreateRequest(BaseModel):
    point: str = Field(min_length=1)


class KnowledgePointsSyncRequest(BaseModel):
    points: list[str]
    mode: str = Field(default="append")  # "append" or "replace"


class DocumentUploadItem(BaseModel):
    name: str = Field(min_length=1)
    doc_type: str = Field(min_length=1)


class DocumentUploadRequest(BaseModel):
    documents: list[DocumentUploadItem]
    use_llm_chunking: bool | None = None


class DocumentWebUploadRequest(BaseModel):
    urls: list[str] = Field(min_length=1)
    parse_classes: list[str] | None = None
    use_llm_chunking: bool | None = None


class DocumentMetadata(BaseModel):
    id: str
    name: str
    doc_type: str
    status: str
    created_at: str


class DocumentSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    filters: dict | None = None


class DocumentSearchResult(BaseModel):
    chunk_id: str
    score: float
    rerank_score: float | None = None
    bm25_score: float | None = None
    hybrid_score: float | None = None
    content: str
    title_path: str
    source_doc_id: str
    source_doc_name: str | None = None


class DocumentChunk(BaseModel):
    chunk_id: str
    content: str
    title_path: str
    order_index: int | None = None
    char_count: int | None = None


class DocumentUpdateRequest(BaseModel):
    name: str | None = None
    doc_type: str | None = None
    content: str | None = None
    use_llm_chunking: bool | None = None


class RagQaRequest(BaseModel):
    course_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class RagCitation(BaseModel):
    chunk_id: str
    source_doc_id: str
    source_doc_name: str
    title_path: str
    excerpt: str
    score: float | None = None
    rerank_score: float | None = None
    bm25_score: float | None = None
    hybrid_score: float | None = None


class RagQaResponse(BaseModel):
    answer: str
    citations: list[RagCitation]


class RagEvaluationRequest(BaseModel):
    course_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    answer: str | None = None
    ground_truth: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    metrics: list[str] | None = None


class RagEvaluationResponse(BaseModel):
    answer: str
    contexts: list[str]
    citations: list[RagCitation]
    scores: dict[str, float]
    metrics: list[str]


class ExerciseGenerationRequest(BaseModel):
    course_id: str = Field(min_length=1)
    count: int = Field(default=5, ge=1, le=50)
    types: list[str] = Field(default_factory=list)
    difficulty: str = Field(default="easy")
    knowledge_scope: list[str] | None = None


class ExerciseOption(BaseModel):
    key: str
    text: str


class ExerciseRubricItem(BaseModel):
    point: str
    score: float


class ExerciseItem(BaseModel):
    exercise_id: str
    course_id: str
    type: str
    question: str
    knowledge_points: list[str]
    source_chunks: list[str]
    difficulty: str
    options: list[ExerciseOption] | None = None
    answer: str | bool | None = None
    analysis: str | None = None
    rubric: list[ExerciseRubricItem] | None = None


class ExerciseGenerationResponse(BaseModel):
    generated: list[ExerciseItem]


class ExerciseBatchSaveRequest(BaseModel):
    title: str | None = None
    exercises: list[ExerciseItem]


class ExerciseBatchResponse(BaseModel):
    batch_id: str
    course_id: str
    title: str
    created_at: str
    exercises: list[ExerciseItem]
    updated_at: str | None = None


class ExerciseBatchListItem(BaseModel):
    batch_id: str
    title: str
    created_at: str
    count: int


class ExerciseBatchUpdateRequest(BaseModel):
    title: str | None = None
    exercises: list[ExerciseItem] | None = None


class ExerciseGradingRequest(BaseModel):
    exercise_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    answer: str | bool


class ExerciseGradingResponse(BaseModel):
    exercise_id: str
    correct: bool
    score: float = Field(ge=0, le=1)
    feedback: str
    suggestion: str
    matched_points: list[str] | None = None
    missing_points: list[str] | None = None
