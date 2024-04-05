from fastapi import APIRouter, Depends, HTTPException, status, Query
from .models import KorisnikCreate, Korisnik
from .db import get_database
from .models import Knjiga, KorisnikCreate, Korisnik, Narudzba
from bson import ObjectId
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import requests
from typing import List
from .db import db
from bson import ObjectId
from pymongo import MongoClient

router = APIRouter()
username = "admin"
password = "admin"
auth_source = "admin"
custom_endpoint_url = "mongodb://mongodb:27017"


client = MongoClient(custom_endpoint_url,
                     username=username,
                     password=password,
                     authSource=auth_source)

def get_database():
    return db.mongodb

# Narudzbe izmjena 12.01
@router.post("/narudzbe", response_model=Narudzba)
async def kreiraj_narudzbu(narudzba: Narudzba, db=Depends(get_database)):

    # Provjera dostupnosti knjiga
    for naslov_knjige in narudzba.knjige:
        knjiga = await db["knjige"].find_one({"naslov": naslov_knjige})
        if not knjiga:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Knjiga s naslovom {naslov_knjige} nije pronađena.")
        
    if narudzba.ukupna_cijena <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ukupna cijena mora biti pozitivan broj")

    narudzba_doc = narudzba.model_dump()
    result = await db["narudzbe"].insert_one(narudzba_doc)
    return {**narudzba_doc, "_id": result.inserted_id}

@router.get("/narudzbe", response_model=List[Narudzba])
async def dohvati_narudzbe(db=Depends(get_database)):
    narudzbe = await db["narudzbe"].find().to_list(length=None)
    return narudzbe


# postanje knjiga
@router.post("/knjige/unesi-po-imenu", response_model=Knjiga)
async def unesi_knjigu_po_imenu(knjiga: Knjiga, db=Depends(get_database)):
    result = await db["knjige"].insert_one(knjiga.model_dump())
    return {**knjiga.model_dump(), "_id": result.inserted_id}


@router.post("/knjige/unesi-po-autoru", response_model=Knjiga)
async def unesi_knjigu_po_autoru(knjiga: Knjiga, db=Depends(get_database)):
    result = await db["knjige"].insert_one(knjiga.model_dump())
    return {**knjiga.model_dump(), "_id": result.inserted_id}

@router.post("/knjige/unesi-po-cijeni", response_model=Knjiga)
async def unesi_knjigu_po_cijeni(knjiga: Knjiga, db=Depends(get_database)):
    result = await db["knjige"].insert_one(knjiga.model_dump())
    return {**knjiga.model_dump(), "_id": result.inserted_id}


# dohvacanje knjiga 
@router.get("/knjige/scraped", response_model=List[Knjiga])
async def dohvati_scraped_knjige(db=Depends(get_database)):
    knjiga_info = await db["knjige"].find().to_list(length=None)
    return knjiga_info

#dohvacanje top 10 najjeftinijih knjiga
@router.get("/knjige/najjeftinije", response_model=List[str])
async def dohvati_najjeftinije_knjige(db=Depends(get_database)):
    najjeftinije_knjige = await db["knjige"].find().sort("cijena", 1).limit(10).to_list(length=None)
    top_jeftine_knjige = [knjiga["naslov"] for knjiga in najjeftinije_knjige]
    return top_jeftine_knjige

@router.get("/knjige/autor", response_model=List[Knjiga])
async def dohvati_knjige_po_autoru(autor: str, db=Depends(get_database)):
    knjige = await db["knjige"].find({"autor": autor}).to_list(length=None)
    return knjige

#dohvacanje 10 nasjkupljih
@router.get("/knjige/najskuplje", response_model=List[Knjiga])
async def dohvati_najskuplje_knjige(db=Depends(get_database)):
    najskuplje_knjige = await db["knjige"].find().sort("cijena", -1).limit(10).to_list(length=None)
    return najskuplje_knjige

# Nova ruta za dohvaćanje knjiga o bazama podataka
@router.get("/knjige-baza-podataka", response_model=List[Knjiga])
async def dohvati_knjige_baza_podataka(db=Depends(get_database)):
    kolekcija_baza_podataka = db["knjige_baza_podataka"]
    knjige_baza_podataka = await kolekcija_baza_podataka.find().to_list(length=None)
    return knjige_baza_podataka

#Route za brisanje odredjene knjige 

@router.delete("/knjige/obrisi-po-imenu", response_model=dict)
async def obrisi_knjigu_po_imenu(naslov: str, db=Depends(get_database)):

    knjiga = await db["knjige"].find_one({"naslov": naslov})
    
    if knjiga:
        await db["knjige"].delete_one({"naslov": naslov})

        return {"message": f"Knjiga s naslovom {naslov} je uspješno obrisana."}
    else:
        raise HTTPException(status_code=404, detail=f"Knjiga s naslovom {naslov} nije pronađena.")
    

# scrappanje html-a sa stranice libristo, kako bi se prikupili podaci o opcenitim knjigama
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

                # ObjectId za jedinstveni ID knjige
                knjiga_id = str(ObjectId())
                
                # Create a dictionary for the book information
                knjiga_info = {"_id": knjiga_id,"naslov": naslov, "autor": autor, "cijena": cijena}

                # Napravljeno spremanje informacije knjiga u bazu
                await db["knjige"].insert_one(knjiga_info)
                scraped_and_saved_data.append(knjiga_info)

        except requests.exceptions.RequestException as e:
            print(f"Greška pri dohvaćanju stranice {url}: {str(e)}")

    return scraped_and_saved_data



# Nova ruta za scrapiranje knjiga sa temom bazama podataka
@router.get("/scrape-book-databases", response_model=List[Knjiga])
async def scrape_databases_and_save_to_db(db=Depends(get_database)):
    scraped_books_database = []

    # Kolekcija za knjige o bazama podataka
    kolekcija_baza_podataka = db["knjige_baza_podataka"]

    for stranica in range(1, 4):  #  prve 3 stranice
        # Kreiranje URL-a za svaku stranicu
        url = f"https://www.libristo.hr/hr/knjige-na-engleskom/databases#form=B/stranica={stranica}"

        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            knjige = soup.find_all("div", class_="c-product-preview")

            for knjiga in knjige:
                naslov_element = knjiga.find("h3").find("a")
                naslov = naslov_element.text.strip() if naslov_element else None

                autor_element = knjiga.find("p", class_="c-product-preview--content").find("i")
                autor = autor_element.text.strip() if autor_element else None

                cijena_element = knjiga.find("p", class_="c-price ")
                cijena = cijena_element.text.strip() if cijena_element else None

                knjiga_info = {"naslov": naslov, "autor": autor, "cijena": cijena}

                await kolekcija_baza_podataka.insert_one(knjiga_info)
                scraped_books_database.append(knjiga_info)

        except requests.exceptions.RequestException as e:
            print(f"Greška pri dohvaćanju stranice {url}: {str(e)}")

    return scraped_books_database
