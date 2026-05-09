from pydantic import BaseModel, EmailStr

# --- Request schemas ---


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfessorLoginRequest(BaseModel):
    email: EmailStr
    password: str


class INSLoginRequest(BaseModel):
    student_number: str
    password: str


class ManualStartRequest(BaseModel):
    student_number: str
    full_name: str
    email: EmailStr
    password: str


# --- Response schemas ---


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class INSLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "student"
    profile_source: str = "ins_verified"
    student_number: str
    full_name: str
    department: str
    major: str
    current_gpa: float
    gpa_is_verified: bool = True


class ManualStartResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "student"
    profile_source: str = "manual"
    requires_profile_completion: bool = True
