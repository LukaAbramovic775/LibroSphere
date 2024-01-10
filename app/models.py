from pydantic import BaseModel, EmailStr,  validator
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

    @validator('cijena')
    def cijena_mora_biti_pozitivan_broj(cls, v):
        if v <= 0:
            raise ValueError('Cijena mora biti pozitivan broj')
        return v
    
    @validator('godina_izdanja')
    def godina_izdanja_ne_smije_biti_u_buducnosti(cls, v):
        if v > 2025:  # Zamijenite 2024 sa stvarnom trenutnom godinom
            raise ValueError('Godina izdanja ne smije biti u budućnosti')
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