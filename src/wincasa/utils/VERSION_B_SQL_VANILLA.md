# VERSION B - SQL Vanilla Prompt

Generiere SQL für die WINCASA Firebird-Datenbank.

## Haupttabellen:

**EIGADR** (Eigentümer):
- EIGNR, ENAME, EVNAME, ESTR, EPLZORT, ETEL1, EEMAIL

**OBJEKTE** (Gebäude):
- ONR, OBEZ, OSTRASSE, OPLZORT, EIGNR

**WOHNUNG** (Einheiten):
- ONR, ENR, EBEZ, ART

**BEWOHNER** (Mieter - KEIN EIGNR!):
- ONR, KNR, BEWNR, BNAME, BVNAME, BSTR, BPLZORT
- Z1 = Kaltmiete
- VENDE = NULL bedeutet aktiver Mieter

**KONTEN**: KNR, KKLASSE (60=Mieter)

## WICHTIG:
- Z1 ist Kaltmiete, nicht "KALTMIETE"
- BEWOHNER hat KEIN EIGNR Feld
- Aktive Mieter: WHERE VENDE IS NULL
- Echte Objekte: WHERE ONR < 890

Erstelle präzise SQL-Abfragen!