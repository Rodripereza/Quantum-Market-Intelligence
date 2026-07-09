from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import hashlib
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import Column, Float, Integer, String, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "qmi_foundation.db"

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
TOKENS: dict[str, dict] = {}


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)
    workspace = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)


class Position(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    company = Column(String, nullable=False)
    sector = Column(String, default="Unclassified")
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    notes = Column(String, default="")


class LoginRequest(BaseModel):
    email: str
    password: str


class PositionCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=12)
    company: Optional[str] = None
    sector: Optional[str] = "Unclassified"
    quantity: float = Field(..., gt=0)
    average_price: float = Field(..., gt=0)
    current_price: Optional[float] = Field(default=None, gt=0)
    currency: str = "USD"
    notes: Optional[str] = ""


class PositionUpdate(BaseModel):
    ticker: Optional[str] = Field(default=None, min_length=1, max_length=12)
    company: Optional[str] = None
    sector: Optional[str] = None
    quantity: Optional[float] = Field(default=None, gt=0)
    average_price: Optional[float] = Field(default=None, gt=0)
    current_price: Optional[float] = Field(default=None, gt=0)
    currency: Optional[str] = None
    notes: Optional[str] = None


app = FastAPI(title="Quantum Market Intelligence API", version="Foundation v1.3")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def migrate_database() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(positions)")).fetchall()}
        if "sector" not in cols:
            conn.execute(text("ALTER TABLE positions ADD COLUMN sector VARCHAR DEFAULT 'Unclassified'"))
        if "notes" not in cols:
            conn.execute(text("ALTER TABLE positions ADD COLUMN notes VARCHAR DEFAULT ''"))
        conn.commit()


def seed_database() -> None:
    migrate_database()
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add(User(name="Rodri", email="rodripereza8@gmail.com", role="Founder / Investor", workspace="Quantum Market Intelligence", password_hash=hash_password("qmi123")))
        if db.query(Position).count() == 0:
            db.add_all([
                Position(ticker="NIO", company="NIO Inc.", sector="EV / China", quantity=4020, average_price=12.88, current_price=4.87, notes="Core recovery position"),
                Position(ticker="SPY", company="S&P 500 ETF", sector="ETF", quantity=10, average_price=560.00, current_price=625.42),
                Position(ticker="QQQ", company="Nasdaq 100 ETF", sector="ETF", quantity=8, average_price=490.00, current_price=548.21),
            ])
        db.commit()
    finally:
        db.close()


seed_database()


def current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.replace("Bearer ", "", 1).strip()
    session = TOKENS.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    if datetime.utcnow() > session["expires_at"]:
        TOKENS.pop(token, None)
        raise HTTPException(status_code=401, detail="Session expired")
    return session["user"]


def serialize_user(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "workspace": user.workspace}


def serialize_position(position: Position, total_value: float) -> dict:
    value = position.quantity * position.current_price
    cost = position.quantity * position.average_price
    pl = value - cost
    pl_pct = (pl / cost * 100) if cost else 0
    weight = (value / total_value * 100) if total_value else 0
    return {
        "id": position.id, "ticker": position.ticker, "company": position.company,
        "sector": position.sector or "Unclassified", "quantity": position.quantity,
        "average_price": position.average_price, "current_price": position.current_price,
        "currency": position.currency, "notes": position.notes or "",
        "value": round(value, 2), "cost": round(cost, 2), "pl": round(pl, 2),
        "pl_pct": round(pl_pct, 2), "weight": round(weight, 2),
    }


def portfolio_payload(db) -> dict:
    positions = db.query(Position).order_by(Position.id.asc()).all()
    total_value = sum(p.quantity * p.current_price for p in positions)
    total_cost = sum(p.quantity * p.average_price for p in positions)
    total_pl = total_value - total_cost
    total_pl_pct = (total_pl / total_cost * 100) if total_cost else 0
    serialized = [serialize_position(p, total_value) for p in positions]
    sectors = {}
    for p in serialized:
        sectors[p["sector"]] = sectors.get(p["sector"], 0) + p["value"]
    sector_allocation = [{"sector": k, "value": round(v, 2), "weight": round((v / total_value * 100) if total_value else 0, 2)} for k, v in sectors.items()]
    return {
        "currency": "USD", "total_value": round(total_value, 2), "total_cost": round(total_cost, 2),
        "total_pl": round(total_pl, 2), "total_pl_pct": round(total_pl_pct, 2),
        "positions": serialized, "sector_allocation": sector_allocation,
        "position_count": len(serialized), "largest_position_weight": max([p["weight"] for p in serialized], default=0),
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "Foundation v1.3", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> dict:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
        if not user or user.password_hash != hash_password(payload.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = secrets.token_urlsafe(32)
        user_data = serialize_user(user)
        TOKENS[token] = {"user": user_data, "expires_at": datetime.utcnow() + timedelta(hours=12)}
        return {"access_token": token, "token_type": "bearer", "user": user_data}
    finally:
        db.close()


@app.get("/api/auth/me")
def me(user: dict = Depends(current_user)) -> dict:
    return user


@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(default=None)) -> dict:
    if authorization and authorization.startswith("Bearer "):
        TOKENS.pop(authorization.replace("Bearer ", "", 1).strip(), None)
    return {"status": "logged_out"}


@app.get("/api/user")
def user(user: dict = Depends(current_user)) -> dict:
    return user


@app.get("/api/market")
def market(user: dict = Depends(current_user)) -> dict:
    return {"source": "foundation_seed_data", "assets": [
        {"ticker": "SPY", "name": "S&P 500 ETF", "price": 625.42, "change_pct": 0.42},
        {"ticker": "QQQ", "name": "Nasdaq 100 ETF", "price": 548.21, "change_pct": 0.76},
        {"ticker": "NIO", "name": "NIO Inc.", "price": 4.87, "change_pct": -1.18},
    ]}


@app.get("/api/portfolio")
def portfolio(user: dict = Depends(current_user)) -> dict:
    db = SessionLocal()
    try:
        return portfolio_payload(db)
    finally:
        db.close()


@app.post("/api/portfolio/positions")
def create_position(payload: PositionCreate, user: dict = Depends(current_user)) -> dict:
    db = SessionLocal()
    try:
        ticker = payload.ticker.upper().strip()
        position = Position(ticker=ticker, company=payload.company or ticker, sector=payload.sector or "Unclassified", quantity=payload.quantity, average_price=payload.average_price, current_price=payload.current_price or payload.average_price, currency=payload.currency.upper(), notes=payload.notes or "")
        db.add(position)
        db.commit()
        return {"status": "created", "portfolio": portfolio_payload(db)}
    finally:
        db.close()


@app.put("/api/portfolio/positions/{position_id}")
def update_position(position_id: int, payload: PositionUpdate, user: dict = Depends(current_user)) -> dict:
    db = SessionLocal()
    try:
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")
        updates = payload.model_dump(exclude_unset=True)
        for key, value in updates.items():
            if value is None:
                continue
            if key in {"ticker", "currency"}:
                value = str(value).upper().strip()
            setattr(position, key, value)
        db.commit()
        return {"status": "updated", "portfolio": portfolio_payload(db)}
    finally:
        db.close()


@app.delete("/api/portfolio/positions/{position_id}")
def delete_position(position_id: int, user: dict = Depends(current_user)) -> dict:
    db = SessionLocal()
    try:
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")
        db.delete(position)
        db.commit()
        return {"status": "deleted", "portfolio": portfolio_payload(db)}
    finally:
        db.close()


@app.get("/api/ai/status")
def ai_status(user: dict = Depends(current_user)) -> dict:
    return {"status": "ready", "layer": "foundation", "modules": ["Prediction Engine", "Consensus Engine", "Explainable AI"], "message": "AI infrastructure prepared for future implementation."}
