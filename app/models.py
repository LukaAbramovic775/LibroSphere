from pydantic import BaseModel, EmailStr,  validator
from typing import List


# Model klase za Knjigu
class Knjiga(BaseModel):
    naslov: str
    autor: str
    zanr: str
    cijena: float
    godina_izdanja: int

    @validator('cijena')
    def cijena_mora_biti_pozitivan_broj(cls, v):
        if v <= 0:
            raise ValueError('Cijena mora biti pozitivan broj')
        return v

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