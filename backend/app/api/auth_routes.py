from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_current_user, require_role, hash_password
from app.models.auth_models import User

router = APIRouter(prefix="/auth", tags=["auth"])

ALLOWED_ROLES = ("admin", "technician")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    expires_in_minutes: int


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    # Deliberately identical error for "no such user" and "wrong password" —
    # distinguishing them lets an attacker enumerate valid usernames.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password.")

    from app.core.config import settings
    token = create_access_token(user.username)
    return LoginResponse(access_token=token, username=user.username, expires_in_minutes=settings.JWT_EXPIRE_MINUTES)


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    """Lets the frontend verify a stored token is still valid on page load,
    without needing to hit a protected data endpoint just to check."""
    return {"username": current_user.username, "role": current_user.role}


class RegisterRequest(BaseModel):
    username: str
    password: str


@router.post("/register", response_model=LoginResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Public self-service signup — always creates a "technician" account,
    NEVER "admin". This is the one deliberate safety boundary: anyone can
    sign themselves up to use the app, but nobody can sign themselves up
    to manage other users' accounts (see create_user() above, which stays
    admin-only for that reason). Returns an access token immediately
    (auto-login) so a new user lands straight in the app instead of having
    to log in a second time right after registering.
    """
    username = payload.username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username must be at least 3 characters.")
    if len(payload.password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters.")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Username '{username}' is already taken.")

    user = User(username=username, password_hash=hash_password(payload.password), role="technician")
    db.add(user)
    db.commit()
    db.refresh(user)

    from app.core.config import settings
    token = create_access_token(user.username)
    return LoginResponse(access_token=token, username=user.username, expires_in_minutes=settings.JWT_EXPIRE_MINUTES)


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "technician"


class UserOut(BaseModel):
    id: int
    username: str
    role: str

    model_config = ConfigDict(from_attributes=True)


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    """Admin-only — lets the seeded admin see who else has access (this is
    a single-tenant demo, so this list is short by design, not paginated)."""
    return db.query(User).order_by(User.id).all()


@router.post("/users", response_model=UserOut)
def create_user(payload: CreateUserRequest, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    """
    Admin-only. This is different from the public POST /auth/register
    above — that one always creates a "technician" account for
    self-service signup; THIS is how an admin creates an account with a
    role OF THEIR CHOOSING (including another "admin"), which is why it
    stays admin-gated: letting anyone self-assign a role would make "admin"
    meaningless as a permission boundary.
    """
    if payload.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"role must be one of {ALLOWED_ROLES}.")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Username '{payload.username}' already exists.")

    user = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    """Admin-only. Can't delete your own account — otherwise a lone admin
    could accidentally lock everyone (including themselves) out."""
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You can't delete your own account while logged in as it.")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    db.delete(user)
    db.commit()
    return {"deleted": True, "id": user_id}
