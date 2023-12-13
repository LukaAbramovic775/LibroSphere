from fastapi import APIRouter, Depends, HTTPException, status
from .models import KorisnikCreate, Korisnik
from .db import get_database
from .models import Knjiga, KorisnikCreate, Korisnik, Narudzba
from .security import get_password_hash, verify_password, create_access_token
from bson import ObjectId
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import requests

router = APIRouter()

# Registracija novog korisnika
@router.post("/registracija", response_model=Korisnik)
async def registriraj_korisnika(korisnik: KorisnikCreate, db=Depends(get_database)):
    # Provjera postoji li već korisnik s tim emailom
    if await db["korisnici"].find_one({"email": korisnik.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email već postoji"
        )

    # Hashiranje lozinke
    hashed_lozinka = get_password_hash(korisnik.lozinka)
    korisnik_dict = korisnik.dict()
    korisnik_dict["hashed_password"] = hashed_lozinka
    del korisnik_dict["lozinka"]  # Uklanjanje obične lozinke

    # Spremanje korisnika u bazu
    result = await db["korisnici"].insert_one(korisnik_dict)
    novi_korisnik = await db["korisnici"].find_one({"_id": result.inserted_id})
    return Korisnik(email=novi_korisnik["email"], id=str(novi_korisnik["_id"]))

# Prijavljivanje korisnika
@router.post("/prijava", response_model=str)
async def prijavi_korisnika(email: str, lozinka: str, db=Depends(get_database)):
    korisnik = await db["korisnici"].find_one({"email": email})
    
    if korisnik is None or not verify_password(lozinka, korisnik["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neispravni kredencijali"
        )

    # Kreiranje JWT tokena
    access_token = create_access_token(data={"sub": korisnik["email"]})
    return access_token

# Narudzbe
@router.post("/narudzbe", response_model=Narudzba)
async def kreiraj_narudzbu(narudzba: Narudzba, db=Depends(get_database)):
    narudzba_doc = narudzba.dict()
    result = await db["narudzbe"].insert_one(narudzba_doc)
    return {**narudzba_doc, "_id": result.inserted_id}

# Knjige 
@router.post("/knjige", response_model=Knjiga)
async def kreiraj_knjigu(knjiga: Knjiga, db=Depends(get_database)):
    knjiga_doc = knjiga.dict()
    result = await db["knjige"].insert_one(knjiga_doc)
    return {**knjiga_doc, "_id": result.inserted_id}

@router.get("/knjige/{knjiga_id}", response_model=Knjiga)
async def dohvati_knjigu(knjiga_id: str, db=Depends(get_database)):
    knjiga = await db["knjige"].find_one({"_id": ObjectId(knjiga_id)})
    if knjiga is None:
        raise HTTPException(status_code=404, detail="Knjiga nije pronađena")
    return knjiga

#dohvacanje knjige sa stranice libristo, naslov knjige
@router.get("/scrape-knjiga/{naslov_knjige}")
async def scrape_knjiga(naslov_knjige: str):
    try:
        url = f"https://www.libristo.hr/hr/knjige-na-engleskom{naslov_knjige}"  # Primjer URL-a
        response = requests.get(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Kasnije implementirati logiku za dohvaćanje podataka o knjizi

            return {"naslov": naslov_knjige, "ostali_podaci": "Podaci o knjizi..."}
        else:
            raise HTTPException(status_code=404, detail="Stranica nije pronađena")
    except RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))