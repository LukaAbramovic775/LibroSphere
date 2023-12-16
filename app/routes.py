from fastapi import APIRouter, Depends, HTTPException, status
from .models import KorisnikCreate, Korisnik
from .db import get_database
from .models import Knjiga, KorisnikCreate, Korisnik, Narudzba
from .security import get_password_hash, verify_password, create_access_token
from bson import ObjectId
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import requests
from .db import db

router = APIRouter()
def get_database():
    return db.mongodb

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

# scrappanje html-a sa stranice libristo, kako bi se prikupili podaci o knjigama
@router.get("/scrape-and-save", response_model=list)
async def scrape_and_save_to_db():
    scraped_and_saved_data = []

    for stranica in range(1, 6):
    # Kreiranje URL-a za svaku stranicu, nije isti kao na #1 stranici jer se mijenja broj stranica ovisno o broju stranice koji se nalazi
        url = f"https://www.libristo.hr/hr/knjige-na-engleskom#form=B/stranica={stranica}"

        try:
            # Dohvacanje HTML stranicu
            response = requests.get(url)
            response.raise_for_status()  # Provjera jesu li dohvaćeni podaci uspješno

            #BeautifulSoup objekt za analizu HTML-a
            soup = BeautifulSoup(response.text, 'html.parser')

            # Pronalaze se elementi koji predstavljaju knjige na stranici
            knjige = soup.find_all("div", class_="c-product-preview")

                # Iteriraj kroz pronađene knjige i izdvoji informacije
            for knjiga in knjige:

                # Pronađi naslov knjige
                naslov_element = knjiga.find("h3").find("a")
                naslov = naslov_element.text.strip() if naslov_element else None

                # Pronađi ime autora
                autor_element = knjiga.find("p", class_="c-product-preview--content").find("i")
                autor = autor_element.text.strip() if autor_element else None

                # Pronađi cijenu
                cijena_element = knjiga.find("p", class_="c-price ")
                cijena = cijena_element.text.strip() if cijena_element else None
                # Create a dictionary for the book information
                knjiga_info = {"naslov": naslov, "autor": autor, "cijena": cijena}

                # Napravljeno spremanje informacije knjiga u bazu
                await db["knjige"].insert_one(knjiga_info)
                scraped_and_saved_data.append(knjiga_info)

        except requests.exceptions.RequestException as e:
            print(f"Greška pri dohvaćanju stranice {url}: {str(e)}")

    return scraped_and_saved_data



