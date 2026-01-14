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
