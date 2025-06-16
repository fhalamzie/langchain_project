# WINCASA Key Tables Schema Reference

## BEWOHNER Table (Tenants/Residents)
**Total columns:** 198  
**Primary Keys:** ONR, KNR, ENR, ID

### Key Columns:
- **ONR**: SMALLINT(2) - Object number (links to OBJEKTE)
- **KNR**: INTEGER(4) - Account number
- **ENR**: SMALLINT(2) - Unit number (links to WOHNUNG)
- **ID**: INTEGER(4) - Unique identifier

### Person Information:
- **BANREDE**: VARCHAR(20) - Salutation
- **BANREDE2**: VARCHAR(20) - Salutation person 2
- **BTITEL**: VARCHAR(20) - Title
- **BTITEL2**: VARCHAR(20) - Title person 2
- **BVNAME**: VARCHAR(30) - First name
- **BVNAME2**: VARCHAR(30) - First name person 2
- **BNAME**: VARCHAR(30) - Last name
- **BNAME2**: VARCHAR(30) - Last name person 2
- **GEBURTSDATUM**: DATE(4) - Birth date
- **GEBURTSDATUM2**: DATE(4) - Birth date person 2

### Address:
- **BSTR**: VARCHAR(30) - Street
- **BSTR2**: VARCHAR(30) - Street line 2
- **BPLZORT**: VARCHAR(30) - ZIP and city
- **BPLZORT2**: VARCHAR(30) - ZIP and city line 2

### Contact:
- **BTEL**: VARCHAR(20) - Phone
- **BTEL2**: VARCHAR(20) - Phone 2
- **BHANDY**: VARCHAR(30) - Mobile
- **BEMAIL**: VARCHAR(255) - Email
- **BFAX**: VARCHAR(20) - Fax

### Contract Information:
- **BABNMIETER**: DATE(4) - Tenant move-out date
- **BABNVERMIETER**: DATE(4) - Landlord termination date
- **MIETE1-10**: NUMERIC(2)(8) - Rent components
- **MIETDATUM**: DATE(4) - Rent date
- **BEWSTATUS**: SMALLINT(2) - Tenant status

---

## EIGADR Table (Owner Addresses)
**Total columns:** 59  
**Primary Key:** EIGNR

### Key Columns:
- **EIGNR**: INTEGER(4) - Owner number (unique identifier)

### Person Information:
- **EANREDE**: VARCHAR(20) - Salutation
- **EANREDE2**: VARCHAR(20) - Salutation person 2
- **ETITEL**: VARCHAR(20) - Title
- **ETITEL2**: VARCHAR(20) - Title person 2
- **EVNAME**: VARCHAR(80) - First name
- **EVNAME2**: VARCHAR(80) - First name person 2
- **ENAME**: VARCHAR(80) - Last name
- **ENAME2**: VARCHAR(80) - Last name person 2
- **EBRIEFAN**: VARCHAR(40) - Letter recipient
- **EBRIEFAN2**: VARCHAR(40) - Letter recipient 2

### Address:
- **EZUSATZ**: VARCHAR(80) - Address supplement
- **EZUSATZ2**: VARCHAR(80) - Address supplement 2
- **ESTR**: VARCHAR(100) - Street
- **EPLZORT**: VARCHAR(35) - ZIP and city
- **ELAND**: CHAR(3) - Country code

### Contact:
- **ETEL1**: VARCHAR(20) - Phone 1
- **ETEL2**: VARCHAR(20) - Phone 2
- **EFAX**: VARCHAR(20) - Fax
- **EEMAIL**: VARCHAR(255) - Email
- **EHANDY**: VARCHAR(30) - Mobile

### Banking:
- **EBLZ**: VARCHAR(10) - Bank code
- **EKONTO**: VARCHAR(16) - Account number
- **EKONTOINH**: VARCHAR(50) - Account holder
- **EBANK**: VARCHAR(27) - Bank name

### Other:
- **ENOTIZ**: BLOB SUB_TYPE TEXT - Notes
- **EMAIL_JA**: CHAR(1) - Email allowed flag
- **FAX_JA**: CHAR(1) - Fax allowed flag

---

## OBJEKTE Table (Properties/Buildings)
**Total columns:** 356  
**Primary Key:** ONR

### Key Columns:
- **ONR**: SMALLINT(2) - Object number (unique identifier)

### Basic Information:
- **OBEZ**: VARCHAR(100) - Object designation/name
- **OSTRASSE**: VARCHAR(100) - Street
- **OPLZORT**: VARCHAR(35) - ZIP and city
- **OANZEINH**: SMALLINT(2) - Number of units

### Financial Arrays (GA1-GA30):
- **GA1-GA30**: NUMERIC(4)(8) - General allocation keys

### Management:
- Multiple administrative and financial fields for property management

---

## WOHNUNG Table (Apartments/Units)
**Total columns:** 20  
**Primary Keys:** ONR, ENR

### Key Columns:
- **ONR**: SMALLINT(2) - Object number (links to OBJEKTE)
- **ENR**: SMALLINT(2) - Unit number (unique within object)

### Basic Information:
- **EBEZ**: VARCHAR(25) - Unit designation
- **ART**: VARCHAR(20) - Type of unit
- **WNOTIZ**: BLOB SUB_TYPE TEXT - Notes

### Tenant History:
- **FRINH1-FRINH12**: VARCHAR(60) - Previous tenants (history)

### References:
- **BKNR**: INTEGER(4) - Tenant account number (links to BEWOHNER.KNR)
- **EKNR**: INTEGER(4) - Owner account number

### Other:
- **DRUCKWAS**: SMALLINT(2) - Print flag

---

## Relationships Between Tables:

1. **OBJEKTE ↔ WOHNUNG**: 
   - One-to-many relationship via ONR
   - One property can have multiple units

2. **WOHNUNG ↔ BEWOHNER**:
   - Links via ONR + ENR
   - WOHNUNG.BKNR → BEWOHNER.KNR (current tenant)

3. **WOHNUNG ↔ EIGADR**:
   - WOHNUNG.EKNR → EIGADR.EIGNR (owner reference)

4. **BEWOHNER ↔ OBJEKTE**:
   - BEWOHNER.ONR → OBJEKTE.ONR (which property)

## Important Notes:

1. Many columns are nullable, indicating optional data
2. The BEWOHNER table has extensive financial fields (MIETE1-10, Z1-8)
3. OBJEKTE has 30 general allocation keys (GA1-GA30) for cost distribution
4. WOHNUNG maintains tenant history in FRINH1-12 fields
5. Date fields use DATE(4) format
6. Character encodings may require attention for German umlauts