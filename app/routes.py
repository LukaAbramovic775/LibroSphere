from fastapi import APIRouter, Depends, HTTPException
from .models import KorisnikCreate, Korisnik
from .db import get_database
from .security import get_password_hash, verify_password, create_access_token

router = APIRouter()


# Route korisnika kod registracije
@router.post("/korisnici/registracija", response_model=Korisnik)
async def registriraj_korisnika(korisnik: KorisnikCreate, db=Depends(get_database)):
    hashed_password = get_password_hash(korisnik.lozinka)
    korisnik_dict = korisnik.dict(exclude={"lozinka"})
    korisnik_dict["hashed_password"] = hashed_password
    result = await db["korisnici"].insert_one(korisnik_dict)
    return {**korisnik_dict, "id": str(result.inserted_id)}

# Route korisnika kod prijave
@router.post("/korisnici/prijava")
async def prijavi_korisnika(email: str, lozinka: str, db=Depends(get_database)):
    korisnik = await db["korisnici"].find_one({"email": email})
    if not korisnik or not verify_password(lozinka, korisnik.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Neispravni kredencijali")
    access_token = create_access_token(data={"sub": korisnik["email"]})
    return {"access_token": access_token, "token_type": "bearer"}
