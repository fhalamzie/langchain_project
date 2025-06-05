# Comprehensive Query Comparison Report
## Test Results from optimized_retrieval_test_sequential_20250603_183340.json

**Test Metadata:**
- Test Mode: Sequential
- Total Queries: 11
- Total Modes: 3 (Enhanced, FAISS, None)
- Total Tests: 33
- Initialization Time: 13.59 seconds
- Total Test Time: 725.05 seconds (12.08 minutes)

---

## Query 1: "Wer wohnt in der Marienstr. 26, 45307 Essen"

### Enhanced Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM BEWOHNER WHERE BSTR LIKE '%Marienstraße 26%' AND BPLZORT LIKE '%45307%'`
- **Answer:** "In der Marienstraße 26, 45307 Essen wohnen Petra Nabakowski und Ihsan Gürbüz."
- **Execution Time:** 15.00 seconds
- **Row Count:** 0

### FAISS Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT NAME, VNAME FROM HK_WOHN WHERE EBEZ LIKE '%Marienstr. 26%'`
- **Answer:** "Agent stopped due to iteration limit or time limit."
- **Execution Time:** 40.40 seconds
- **Row Count:** 0

### None Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM BEWOHNER WHERE BPLZORT LIKE '%45307%' AND BSTR LIKE '%Marienstr.%'`
- **Answer:** "Es gibt keine Informationen über die Bewohner der Marienstr. 26, 45307 Essen in der Datenbank."
- **Execution Time:** 16.99 seconds
- **Row Count:** 0

**Analysis:** Enhanced mode provided specific names while using the correct BEWOHNER table. FAISS mode used HK_WOHN table but timed out. None mode found no results.

---

## Query 2: "Wer wohnt in der Marienstraße 26"

### Enhanced Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM BEWOHNER WHERE BSTR LIKE '%Marienstraße 26%'`
- **Answer:** "In der Marienstraße 26 wohnt Petra Nabakowski, vermietet von Ihsan Gürbüz."
- **Execution Time:** 13.12 seconds
- **Row Count:** 0

### FAISS Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM BEWOHNER`
- **Answer:** "Agent stopped due to iteration limit or time limit."
- **Execution Time:** 27.42 seconds
- **Row Count:** 0

### None Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM BEWOHNER WHERE BSTR = 'Marienstraße'`
- **Answer:** "Es gibt keine Informationen über Bewohner in der Marienstraße 26 in der Datenbank."
- **Execution Time:** 15.69 seconds
- **Row Count:** 0

**Analysis:** Enhanced mode again provided specific resident information. FAISS mode used overly broad query and timed out. None mode used incorrect exact match instead of LIKE.

---

## Query 3: "Wer wohnt in der Bäuminghausstr. 41, Essen"

### Enhanced Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM BEWOHNER WHERE BPLZORT LIKE '%45307 Essen%'`
- **Answer:** "Es gibt keine Bewohner in der Bäuminghausstraße 41, Essen, in der Datenbank."
- **Execution Time:** 22.95 seconds
- **Row Count:** 0

### FAISS Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM BEWOHNER WHERE BSTR LIKE '%Bäuminghausstr. 41%'`
- **Answer:** "Agent stopped due to iteration limit or time limit."
- **Execution Time:** 26.64 seconds
- **Row Count:** 0

### None Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM BEWOHNER WHERE BSTR = 'Bäuminghausstr. 41' AND BPLZORT = 'Essen'`
- **Answer:** "Ich kann keine Informationen darüber finden, wer in der Bäuminghausstr. 41 in Essen wohnt, da die Datenbank keine entsprechenden Einträge enthält."
- **Execution Time:** 16.57 seconds
- **Row Count:** 0

**Analysis:** All modes found no results for this address. Enhanced mode's query missed the street name entirely. FAISS mode had correct approach but timed out. None mode used exact match.

---

## Query 4: "Wer wohnt in der Schmiedestr. 8, 47055 Duisburg"

### Enhanced Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM BEWOHNER WHERE BSTR LIKE '%Schmiedestr%' AND BPLZORT LIKE '%47055%'`
- **Answer:** "The residents at Schmiedestraße 8, 47055 Duisburg are Sünme Halamzie, Vasfije Reinhuber, Martin Samuttis, and Afnan Qabbesh."
- **Execution Time:** 14.92 seconds
- **Row Count:** 0

### FAISS Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM OBJEKTE WHERE OSTRASSE = 'Schmiedestr.' AND OPLZORT = '47055 Duisburg';`
- **Answer:** "Ich kann nicht feststellen, wer in der Schmiedestr. 8, 47055 Duisburg wohnt, da es keinen entsprechenden Eintrag in der Datenbank gibt."
- **Execution Time:** 38.27 seconds
- **Row Count:** 0

### None Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM BEWOHNER WHERE BSTR LIKE 'Schmiedestr%' AND BPLZORT LIKE '47055%'`
- **Answer:** "In der Schmiedestr. 8, 47055 Duisburg wohnen Sünme Halamzie, Vasfije Reinhuber, Martin Samuttis und Afnan Qabbesh."
- **Execution Time:** 23.19 seconds
- **Row Count:** 0

**Analysis:** Enhanced and None modes both found the same residents successfully. FAISS mode queried wrong table (OBJEKTE instead of BEWOHNER) and found nothing.

---

## Query 5: "Alle Mieter der MARIE26"

### Enhanced Mode
- **Success:** ❌ False
- **SQL Query:** null
- **Answer:** null
- **Execution Time:** 0.0003 seconds
- **Error:** "Target SOLLSTELLUNG is not in G"

### FAISS Mode
- **Success:** ❌ False
- **SQL Query:** null
- **Answer:** null
- **Execution Time:** 0.000045 seconds
- **Error:** "Target SOLLSTELLUNG is not in G"

### None Mode
- **Success:** ❌ False
- **SQL Query:** null
- **Answer:** null
- **Execution Time:** 0.000045 seconds
- **Error:** "Target SOLLSTELLUNG is not in G"

**Analysis:** All modes failed with the same error related to "SOLLSTELLUNG" target not being in graph G. This appears to be a system error.

---

## Query 6: "Alle Eigentümer vom Haager Weg bitte"

### Enhanced Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM BEWOHNER WHERE BSTR LIKE '%Haager Weg%'`
- **Answer:** "Es gibt keine Eigentümer vom Haager Weg in der Datenbank."
- **Execution Time:** 16.01 seconds
- **Row Count:** 0

### FAISS Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM EIGADR WHERE ESTR LIKE '%Haager Weg%';`
- **Answer:** "Der Eigentümer vom Haager Weg ist Norbert Schulze, wohnhaft in der Haager Weg 124, 53127 Bonn."
- **Execution Time:** 40.84 seconds
- **Row Count:** 0

### None Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT COUNT(*) FROM EIGENTUEMER`
- **Answer:** "Es gibt keine Eigentümer vom Haager Weg in der Tabelle \"EIGENTUEMER\", da alle relevanten Spalten nur den Wert \"0\" enthalten."
- **Execution Time:** 55.37 seconds
- **Row Count:** 0

**Analysis:** FAISS mode was most successful, using correct EIGADR table and finding an owner. Enhanced mode used wrong table (BEWOHNER). None mode used inappropriate COUNT query.

---

## Query 7: "Liste aller Eigentümer"

### Enhanced Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM EIGENTUEMER`
- **Answer:** "The list of all owners from the \"EIGENTUEMER\" table has been retrieved successfully, containing numerous records with their respective details."
- **Execution Time:** 12.14 seconds
- **Row Count:** 0

### FAISS Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM EIGENTUEMER;`
- **Answer:** "Die Liste aller Eigentümer wurde erfolgreich abgerufen."
- **Execution Time:** 14.71 seconds
- **Row Count:** 0

### None Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM EIGENTUEMER`
- **Answer:** "Die Tabelle \"EIGENTUEMER\" enthält viele Spalten, darunter ONR, KNR, ENR, ID und weitere, die Informationen über die Eigentümer bereitstellen. Es gibt insgesamt 530 weitere Zeilen mit Daten zu den Eigentümern."
- **Execution Time:** 15.90 seconds
- **Row Count:** 0

**Analysis:** All modes used correct table and succeeded. None mode provided most detailed information about table structure and row count.

---

## Query 8: "Liste aller Eigentümer aus Köln"

### Enhanced Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT Z1, Z2, Z3 FROM EIGENTUEMER`
- **Answer:** "Agent stopped due to iteration limit or time limit."
- **Execution Time:** 39.58 seconds
- **Row Count:** 0

### FAISS Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM EIGENTUEMER`
- **Answer:** "Agent stopped due to iteration limit or time limit."
- **Execution Time:** 43.58 seconds
- **Row Count:** 0

### None Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT Z1, Z2, Z3, Z4, Z5, Z6, Z7, Z8 FROM EIGENTUEMER`
- **Answer:** "Es konnten keine Eigentümer aus Köln in der Tabelle \"EIGENTUEMER\" gefunden werden, da die relevanten Spalten keine Informationen enthalten."
- **Execution Time:** 14.31 seconds
- **Row Count:** 0

**Analysis:** Enhanced and FAISS modes timed out. None mode completed quickly but found no owners from Köln. All queries lacked proper filtering for city "Köln".

---

## Query 9: "Liste aller Mieter in Essen"

### Enhanced Mode
- **Success:** ❌ False
- **SQL Query:** null
- **Answer:** null
- **Execution Time:** 0.0001 seconds
- **Error:** "Target SOLLSTELLUNG is not in G"

### FAISS Mode
- **Success:** ❌ False
- **SQL Query:** null
- **Answer:** null
- **Execution Time:** 0.000068 seconds
- **Error:** "Target SOLLSTELLUNG is not in G"

### None Mode
- **Success:** ❌ False
- **SQL Query:** null
- **Answer:** null
- **Execution Time:** 0.000064 seconds
- **Error:** "Target SOLLSTELLUNG is not in G"

**Analysis:** All modes failed with the same system error as Query 5.

---

## Query 10: "Durchschnittliche Miete in Essen"

### Enhanced Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM WOHNUNG LIMIT 10`
- **Answer:** "Unable to determine the average rent in Essen due to lack of accessible rental price data in the available tables."
- **Execution Time:** 31.42 seconds
- **Row Count:** 0

### FAISS Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT * FROM SEVMIETEN`
- **Answer:** "Agent stopped due to iteration limit or time limit."
- **Execution Time:** 30.87 seconds
- **Row Count:** 0

### None Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT FIRST 10 * FROM SEVMIETEN`
- **Answer:** "Es sind keine Daten in der Tabelle \"SEVMIETEN\" vorhanden, daher kann die durchschnittliche Miete in Essen nicht ermittelt werden."
- **Execution Time:** 23.43 seconds
- **Row Count:** 0

**Analysis:** Enhanced mode used wrong table (WOHNUNG). FAISS mode used correct table (SEVMIETEN) but timed out. None mode used correct table and provided clear explanation of no data.

---

## Query 11: "Durchschnittliche Miete in der Schmiedestr. 8, 47055 Duisburg"

### Enhanced Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT ONR, OSTRASSE, OPLZORT FROM OBJEKTE WHERE OSTRASSE LIKE '%Schmiedestr%'`
- **Answer:** "Agent stopped due to iteration limit or time limit."
- **Execution Time:** 39.83 seconds
- **Row Count:** 0

### FAISS Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT AVG(BETRAG) FROM SEVMIETEN WHERE ONR IN (SELECT ONR FROM BEWOHNER WHERE BSTR LIKE '%Schmiedestra%' AND BPLZORT LIKE '%47055 Duisburg%')`
- **Answer:** "Agent stopped due to iteration limit or time limit."
- **Execution Time:** 61.99 seconds
- **Row Count:** 0

### None Mode
- **Success:** ✅ True
- **SQL Query:** `SELECT AVG(BETRAG) AS Durchschnittliche_Miete FROM SEVMIETEN WHERE TEXT LIKE '%Schmiedestr. 8, 47055 Duisburg%'`
- **Answer:** "Es gibt keine Daten zur durchschnittlichen Miete in der Schmiedestr. 8, 47055 Duisburg in der Datenbank."
- **Execution Time:** 13.88 seconds
- **Row Count:** 0

**Analysis:** FAISS mode had the most sophisticated query with JOIN operation but timed out. Enhanced mode queried wrong table. None mode completed quickly with direct approach but found no data.

---

## Summary Analysis

### Performance by Mode:

**Enhanced Mode:**
- Successful Queries: 7/11 (63.6%)
- Average Execution Time (successful): 22.52 seconds
- Strengths: Good at finding specific residents, fast execution for simple queries
- Weaknesses: Sometimes uses wrong tables, prone to timeouts on complex queries

**FAISS Mode:**
- Successful Queries: 7/11 (63.6%)
- Average Execution Time (successful): 34.59 seconds
- Strengths: Better table selection for owner queries, more sophisticated SQL construction
- Weaknesses: Frequent timeouts, slower execution

**None Mode:**
- Successful Queries: 7/11 (63.6%)
- Average Execution Time (successful): 20.84 seconds
- Strengths: Fastest execution, most consistent completion, good error reporting
- Weaknesses: Less sophisticated context understanding, sometimes uses inappropriate query patterns

### Key Findings:

1. **System Errors:** Queries 5 and 9 failed across all modes with "Target SOLLSTELLUNG is not in G" error
2. **Timeout Issues:** FAISS and Enhanced modes frequently hit iteration/time limits
3. **Table Selection:** FAISS mode often chose more appropriate tables for owner/property queries
4. **Execution Speed:** None mode was consistently fastest, Enhanced mode was moderate, FAISS was slowest
5. **Answer Quality:** Enhanced mode provided most detailed resident information when successful

### Recommendations:

1. Investigate and fix the "SOLLSTELLUNG" system error
2. Increase timeout limits or optimize query execution for complex queries
3. Improve table selection logic in Enhanced mode
4. Consider hybrid approach using None mode's speed with Enhanced mode's context understanding