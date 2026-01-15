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


class DocumentUploadItem(BaseModel):
    name: str = Field(min_length=1)
    doc_type: str = Field(min_length=1)


class DocumentUploadRequest(BaseModel):
    documents: list[DocumentUploadItem]


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
    content: str
    title_path: str
    source_doc_id: str
    source_doc_name: str | None = None


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


class RagQaResponse(BaseModel):
    answer: str
    citations: list[RagCitation]


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
