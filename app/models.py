from pydantic import BaseModel, EmailStr
from typing import List

# Model klase za Knjigu
class Knjiga(BaseModel):
    naziv: str
    autor: str
    zanr: str
    cijena: float
    isbn: str
    godina_izdanja: int
    broj_stranica: int
    opis: str

# Modelklase za Korisnika
class KorisnikCreate(BaseModel):
    email: EmailStr
    lozinka: str

class Korisnik(BaseModel):
    email: EmailStr
    id: str

# Model klase za Narudžbu
class Narudzba(BaseModel):
    korisnik_id: str
    knjige: List[str]  # Lista ID-ova knjiga
    ukupna_cijena: float

# Model klase za knjige o bazama podataka
class KnjigaBazaPodataka(BaseModel):
    naslov: str
    autor: str
    cijena: float