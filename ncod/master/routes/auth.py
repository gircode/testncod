from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from ncod.core.db.database import get_db
from ncod.master.models.user import User, UserStatus
from ncod.master.models.organization import Organization
from ncod.master.schemas.auth import TokenResponse, UserCreate, UserResponse
from ncod.master.auth.security import get_password_hash

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

# 配置
SECRET_KEY = "your-secret-key"  # 请更改为安全的密钥
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 验证用户名格式
    if not User.validate_username(user_data.username):
        raise HTTPException(status_code=400, detail="用户名只能包含字母和数字")

    # 验证密码格式
    if not User.validate_password(user_data.password):
        raise HTTPException(status_code=400, detail="密码长度至少6位")

    # 验证手机号格式
    if not User.validate_phone(user_data.phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")

    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 如果未指定组织,使用"其他"组织
    if not user_data.organization_id:
        org = Organization.get_or_create_other(db)
        user_data.organization_id = org.id

    # 创建用户
    user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        name=user_data.name,
        phone=user_data.phone,
        email=user_data.email,
        organization_id=user_data.organization_id,
        status=UserStatus.PENDING,  # 新用户需要审批
        created_at=datetime.utcnow(),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # 验证用户
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # 检查用户状态
    if user.status != UserStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account not approved"
        )

    # 创建访问令牌
    access_token = create_access_token(data={"sub": user.username})

    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}


def authenticate_user(username: str, password: str, db: Session) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        return None
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
