# RAG PRD Quality Issues - Diagnostic Report

**Date:** 2025-11-27  
**Status:** ❌ **NOT OPERATIONAL - CRITICAL ISSUES FOUND**

---

## 🚨 CRITICAL ISSUES IDENTIFIED

### **Issue 1: Query Endpoint Failing** ❌
- **Symptom:** Empty reply from server (curl error 52)
- **Impact:** **ZERO queries can be executed**
- **Root Cause:** Multiple cascading failures

### **Issue 2: Embeddings Service 422 Error** ❌
- **Symptom:** `422 Unprocessable Entity` when RAG pipeline calls embeddings
- **Evidence:** 
  ```
  ERROR:main:Embedding generation failed: Client error '422 Unprocessable Entity' 
  for url 'http://intel-embeddings-prd:8000/embed'
  WARNING:main:External service failed, loading local model as fallback
  ```
- **Impact:** RAG falls back to local model loading, causing query failures
- **Status:** Embeddings service works when called directly with correct format

### **Issue 3: ChromaDB Collection Missing** ❌
- **Symptom:** Collection `sap_workspace` does not exist in container ChromaDB
- **Evidence:** 
  ```
  ValueError: Could not connect to tenant default_tenant. Are you sure it exists?
  ```
- **Impact:** **NO DATA TO QUERY** - 0 documents indexed
- **Root Cause:** Indexing script uses `chromadb.Client()` (local), not container

### **Issue 4: RAG Pipeline Instability** ⚠️
- **Symptom:** Container restarted 2 minutes ago
- **Evidence:** `Up 2 minutes (healthy)` - recent restart
- **Impact:** Service may be unstable due to embeddings errors

---

## 📊 CURRENT STATUS

| Component | Status | Quality | Evidence |
|-----------|--------|---------|----------|
| **RAG Pipeline Service** | ⚠️ Running | ❌ **NOT PRD QUALITY** | Restarted 2 min ago, query endpoint fails |
| **ChromaDB Service** | ✅ Running | ✅ OK | Service healthy, but no collections |
| **Embeddings Service** | ✅ Running | ⚠️ **API MISMATCH** | Works directly, fails from RAG pipeline |
| **Document Indexing** | ❌ **FAILED** | ❌ **ZERO** | 0 documents, collection missing |
| **Query Endpoint** | ❌ **FAILING** | ❌ **ZERO** | Empty replies, no queries work |
| **Automatic Indexing** | ❓ Unknown | ❓ **UNVERIFIED** | Cron job status unclear |

---

## 🔍 ROOT CAUSE ANALYSIS

### **Primary Issue: Data Not Indexed**
1. Indexing script (`index_sap_standalone.py`) uses `chromadb.Client()` 
2. This connects to **local ChromaDB**, not container
3. Documents indexed locally are **inaccessible** to RAG pipeline
4. Container ChromaDB has **zero collections**

### **Secondary Issue: Embeddings API Mismatch**
1. RAG pipeline calls embeddings service incorrectly
2. Gets 422 error (format mismatch)
3. Falls back to loading model locally
4. This causes query endpoint to fail

### **Tertiary Issue: Service Instability**
1. Embeddings errors cause RAG pipeline to restart
2. Query endpoint fails during/after restart
3. No graceful error handling

---

## 🔧 REQUIRED FIXES

### **Fix 1: Index Data into Container ChromaDB** (CRITICAL)

**Current Problem:**
- Script uses `chromadb.Client()` → local instance
- Container needs data in Docker volume

**Solution:**
1. Update indexing script to use `chromadb.HttpClient(host='localhost', port=8000)` inside container
2. OR: Run standalone script inside container (already exists)
3. Verify collection exists: `docker exec intel-chromadb-prd python3 -c "import chromadb; client = chromadb.Client(); print([c.name for c in client.list_collections()])"`

**Action:**
```bash
# Re-index using container ChromaDB
cd /Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP
tar czf /tmp/sap_index.tar.gz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' --exclude='archive' --exclude='.DS_Store' .
docker cp /tmp/sap_index.tar.gz intel-chromadb-prd:/tmp/
docker cp docs/05-technical/index_sap_standalone.py intel-chromadb-prd:/tmp/
docker exec intel-chromadb-prd sh -c "cd /tmp && rm -rf sap_index_final && mkdir -p sap_index_final && cd sap_index_final && tar xzf ../sap_index.tar.gz"
docker exec intel-chromadb-prd python3 /tmp/index_sap_standalone.py
```

### **Fix 2: Fix Embeddings Service API Call** (CRITICAL)

**Current Problem:**
- RAG pipeline sends wrong format to embeddings service
- Gets 422 error

**Solution:**
1. Check RAG pipeline code for embeddings API call format
2. Verify embeddings service expects: `{"texts": ["text1", "text2"]}`
3. Fix RAG pipeline to match expected format
4. Test: `docker exec intel-rag-pipeline-prd curl -X POST http://intel-embeddings-prd:8000/embed -H "Content-Type: application/json" -d '{"texts": ["test"]}'`

**Action:**
- Locate RAG pipeline embeddings call code
- Update to match embeddings service API
- Restart RAG pipeline
- Verify no more 422 errors in logs

### **Fix 3: Verify Query Endpoint** (CRITICAL)

**After Fixes 1 & 2:**
1. Test query endpoint with actual data
2. Verify results returned
3. Check response times
4. Document working queries

**Action:**
```bash
# After indexing and embeddings fix
curl -X POST http://localhost:8020/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "k": 5}'
```

### **Fix 4: Verify Automatic Indexing** (IMPORTANT)

**Current Status:** Unknown

**Action:**
1. Check cron job status
2. Verify auto-index script works
3. Test with new file
4. Document automatic indexing process

---

## 📋 PRD QUALITY STANDARDS CHECKLIST

| Requirement | Status | Notes |
|-------------|--------|-------|
| ✅ Service Running | ⚠️ **UNSTABLE** | Restarts due to errors |
| ✅ Query Endpoint Works | ❌ **FAILING** | Empty replies |
| ✅ Data Indexed | ❌ **ZERO** | 0 documents |
| ✅ Embeddings Service Works | ⚠️ **API MISMATCH** | 422 errors |
| ✅ Automatic Updates | ❓ **UNKNOWN** | Not verified |
| ✅ Error Handling | ❌ **POOR** | No graceful degradation |
| ✅ Documentation | ⚠️ **INCOMPLETE** | Status docs outdated |
| ✅ Monitoring | ❓ **UNKNOWN** | No alerts configured |

**PRD Quality Score: 2/8 = 25%** ❌

---

## 🎯 IMMEDIATE ACTIONS REQUIRED

### **Priority 1: Fix Data Indexing** (Blocks everything)
1. Re-index into container ChromaDB
2. Verify collection exists
3. Verify document count > 0

### **Priority 2: Fix Embeddings API** (Blocks queries)
1. Fix RAG pipeline embeddings call
2. Test embeddings service directly
3. Verify no 422 errors

### **Priority 3: Test Query Endpoint** (Verify fix)
1. Run test queries
2. Verify results returned
3. Document working examples

### **Priority 4: Verify Automatic Indexing** (Sustainment)
1. Check cron job
2. Test auto-index
3. Document process

---

## 📊 EXPECTED OUTCOMES

### **After Fixes:**
- ✅ Query endpoint returns results
- ✅ Embeddings service works without errors
- ✅ 705+ documents indexed and searchable
- ✅ Automatic indexing verified
- ✅ PRD quality score: 8/8 = 100%

### **Success Criteria:**
1. Query endpoint returns results (not empty)
2. No 422 errors in logs
3. Collection exists with > 0 documents
4. Test query works: "What did Oliver say about performance?"
5. Automatic indexing runs successfully

---

## 🚨 CURRENT REALITY

**RAG is NOT operational for PRD use.**

**What works:**
- Services are running
- Infrastructure is healthy

**What doesn't work:**
- ❌ **ZERO queries can be executed**
- ❌ **ZERO documents indexed**
- ❌ **Embeddings API failing**
- ❌ **Query endpoint broken**

**Status:** ❌ **NOT PRD QUALITY - REQUIRES IMMEDIATE FIX**

---

**Next Steps:** Execute fixes in priority order, verify each step, document results.

