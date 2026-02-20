BTP Exploration Findings - SAP Project 

Date: 2025-11-19 
Explored By: Mark Carey 
Status: Complete - All accessible subaccounts explored 

📊 SUMMARY 

Access Status: 

ESX (Netherlands): 3/3 subaccounts accessible, blocked by Cloud Foundry org membership 

ESY (Germany): 0/3 subaccounts accessible, need subaccount-level access 

Cloud Foundry Environments Found: 

CAS_ESX_DEV: cas-dev 

CAS_ESX_QAS: cas-qas 

CAS_ESX_PRD: cas-prd 

CAS_ESY_DEV: No access 

CAS_ESY_QAS: No access 

CAS_ESY_PRD: No access 

🔍 DETAILED FINDINGS 

CAS_ESX_DEV (Azure Netherlands - Development) 

Cloud Foundry Environment: 

Environment Name: cas-dev  

API Endpoint: https://api.cf.eu20-001.hana.ondemand.com  

Org ID: b4dd7aed-a256-4878-9cbd-7f0a15683c76 

Org Memory Limit: 9,216MB 

Status: Created - Last Changed: 17 Nov 2025 

Permission Status: 

Subaccount Access: ✅ Yes 

Cloud Foundry Org Access: ❌ Blocked - “You must be an org member”  

Spaces Visible: No - “No spaces defined in this subaccount” 

Number of Spaces: 0 

Service Instances: - HANA Cloud: CAS_AI_D (Created) 

Subscriptions (7): 

Web access for ABAP - SAP AI Launchpad - Joule - SAP HANA Cloud - SAP Build Process Automation - SAP Business Application Studio - SAP Build Work Zone, standard edition 

Shape 

CAS_ESX_QAS (Azure Netherlands - Quality Assurance) 

Cloud Foundry Environment:  

Environment Name: cas-qas  

API Endpoint: https://api.cf.eu20-001.hana.ondemand.com  

Org ID: 7ebe69ca-826f-4cf3-9bf4-b0315f17148f  

Org Memory Limit: 7,168MB  

Status: Created - Last Changed: 26 Sept 2025 

Permission Status:  

Subaccount Access: ✅ Yes  

Cloud Foundry Org Access: ❌ Blocked - “You must be an org member”  

Spaces Visible: No - “No spaces defined in this subaccount”  

Number of Spaces: 0 

Service Instances: - HANA Cloud: CAS_AI_Q (Created) - HANA Cloud: cas-qa (Created) 

Subscriptions (5): - Web access for ABAP - SAP AI Launchpad - SAP HANA Cloud - SAP Build Process Automation - SAP Build Work Zone, standard edition 

Shape 

CAS_ESX_PRD (Azure Netherlands - Production) 

Cloud Foundry Environment: 

Environment Name: cas-prd  

API Endpoint: https://api.cf.eu20-001.hana.ondemand.com  

Org ID: 857c036b-0ca7-4f6d-af31-db96a1e9b83d  

Org Memory Limit: 10,240MB  

Status: Created - Last Changed: 19 Sept 2025 

Permission Status: 

Subaccount Access: ✅ Yes  

Cloud Foundry Org Access: ❌ Blocked - “You must be an org member”  

Spaces Visible: No - “No spaces defined in this subaccount”  

Number of Spaces: 0 

Service Instances: - HANA Cloud: CAS_AI_P (Created) 

Subscriptions (6): - Web access for ABAP - SAP AI Launchpad - SAP HANA Cloud - SAP Build Process Automation - SAP Cloud ALM - SAP Build Work Zone, standard edition 

Shape 

CAS_ESY_DEV (AWS Frankfurt - Development) 

Access Status: - Subaccount Access: ❌ No - “Missing Authorisation” - Error Message: “You don’t have the necessary authorisation to access the subaccount CAS_ESY_DEV. Please contact your administrator.” - Cloud Foundry Environment: Unknown (cannot access) - Notes: Requires administrator to grant subaccount-level access. 

Shape 

CAS_ESY_QAS (AWS Frankfurt - Quality Assurance) 

Access Status: - Subaccount Access: ❌ No - “Missing Authorisation” - Error Message: “You don’t have the necessary authorisation to access the subaccount CAS_ESY_QAS. Please contact your administrator.” - Cloud Foundry Environment: Unknown (cannot access) - Notes: Requires administrator to grant subaccount-level access, 

Shape 

CAS_ESY_PRD (AWS Frankfurt - Production) 

Access Status: - Subaccount Access: ❌ No - “Missing Authorisation” - Error Message: “You don’t have the necessary authorisation to access the subaccount CAS_ESY_PRD. Please contact your administrator.” - Cloud Foundry Environment: Unknown (cannot access) - Notes: Requires administrator to grant subaccount-level access. 

Shape 

🎯 KEY OBSERVATIONS 

Architecture Patterns: 

All ESX environments use the same API endpoint: https://api.cf.eu20-001.hana.ondemand.com 

Consistent naming: Cloud Foundry org names follow pattern: cas-dev, cas-qas, cas-prd 

Memory allocation: Varies by environment (DEV: 9GB, QAS: 7GB, PRD: 10GB) 

Permission barrier: All ESX environments have same permission requirement (org membership) 

Access Patterns: 

ESX (Netherlands): Can see subaccounts and Cloud Foundry environments, but blocked by org membership 

ESY (Germany): Cannot access subaccounts at all (need subaccount-level authorization first) 

Service Instances: 

HANA Cloud instances present in all accessible ESX environments 

Naming pattern: CAS_AI_D (DEV), CAS_AI_Q (QAS), CAS_AI_P (PRD) 

ESP AI Proxy: Cannot determine location due to permission barriers 

Shape 

📋 ACCESS REQUIREMENTS 

To View Cloud Foundry Applications: 

Cloud Foundry org membership required for: 

cas-dev (CAS_ESX_DEV) 

cas-qas (CAS_ESX_QAS) 

cas-prd (CAS_ESX_PRD) 

To Access ESY Environments: 

Subaccount-level authorization required for: 

CAS_ESY_DEV 

CAS_ESY_QAS 

CAS_ESY_PRD 

Administrator action required 

Shape 

🔗 RELATED INFORMATION 

From Channel Intelligence: - ESP AI Proxy endpoint: https://esp_ai_proxy.cfapps.eu20-001.hana.ondemand.com/push_ticket - Landscape: eu20-001 (matches API endpoint found) - Application likely deployed in Cloud Foundry (not BTP service) 

Architecture: - ESP → Cloud Foundry (AI Proxy) → AI Core - Multi-environment: DEV/QAS/PRD - Vector DB in HANA Cloud - Gemini LLM for sentiment analysis 