# OptiRule Customer Discovery: Targeting and Outreach Findings

## Objective

Identify people at companies likely to experience the shipping-management problems addressed by OptiRule, find appropriate contacts without relying heavily on LinkedIn search, obtain professional email addresses, and recruit them for customer-discovery interviews.

## 1. Ideal Company Profile

The strongest prospects are likely to be **shippers rather than logistics providers**, especially mid-market distributors and manufacturers with operationally complex shipping.

Useful company signals include:

- Roughly $50M–$1B in revenue or comparable mid-market scale
- Multiple warehouses, branches, or distribution locations
- Mix of parcel, LTL, FTL, oversized, or expedited shipments
- Multiple carriers (UPS/FedEx plus regional parcel or LTL carriers)
- Large SKU catalogs or products with widely varying sizes/weights
- Employees making manual carrier, rate, routing, pickup, BOL, or exception decisions
- ERP/WMS plus point shipping tools, spreadsheets, email, or other fragmented workflows rather than a highly automated enterprise TMS

Promising verticals include:

- Industrial and MRO distribution
- HVAC and plumbing distribution
- Building materials
- Electrical supply
- Automotive and equipment parts
- Restaurant/commercial equipment
- Machinery
- Furniture
- Medical supplies
- Specialty manufacturing and distribution

## 2. Initial Companies to Investigate

Examples identified for further qualification:

1. Global Industrial
2. Uline
3. Zoro
4. McMaster-Carr
5. Northern Tool + Equipment
6. Motion
7. Applied Industrial Technologies
8. MSC Industrial Supply
9. Ferguson
10. SiteOne Landscape Supply
11. Gemaire
12. Watsco
13. Imperial Supplies
14. WebstaurantStore
15. Restaurant Equippers
16. School Specialty
17. Parts Town
18. Replacements, Ltd.
19. Build.com
20. Summit Racing Equipment

Large companies such as Uline may have sophisticated internal systems, so smaller companies with similar operational characteristics may be better early discovery targets.

## 3. People to Target

For operational pain, prioritize people who work directly with transportation and shipping:

- Shipping Manager
- Transportation Manager
- Logistics Manager
- Director of Transportation
- Director of Logistics
- Distribution Manager
- Fulfillment Manager
- Warehouse Operations Director
- Supply Chain Director
- VP Supply Chain
- Director/VP Operations
- COO (especially at smaller companies)

Finance can provide a complementary perspective:

- Controller
- Corporate Controller
- VP Finance
- CFO

Operations interviews can reveal **where the workflow is painful**, while finance interviews can reveal **how much the problems cost** through freight spend, accessorials, invoice reconciliation, margin leakage, and poor freight-cost visibility.

## 4. Finding Candidates Without Heavy LinkedIn Searching

Use Google as the discovery layer and LinkedIn primarily for identity verification, mutual connections, and outreach.

### Search within a specific company

```text
site:linkedin.com/in "Global Industrial"
("shipping manager" OR "transportation manager" OR "logistics manager")
```

```text
site:linkedin.com/in "Global Industrial"
("director of logistics" OR "director of transportation" OR "supply chain director")
```

```text
site:linkedin.com/in "Global Industrial"
("warehouse manager" OR "distribution manager" OR "fulfillment manager")
```

### Search across an industry

```text
site:linkedin.com/in
("shipping manager" OR "transportation manager")
("industrial distribution" OR "industrial supply")
```

```text
site:linkedin.com/in
("logistics manager" OR "transportation manager")
("HVAC" OR "plumbing" OR "building materials")
```

```text
site:linkedin.com/in
("transportation manager" OR "logistics manager")
("automotive parts" OR "industrial parts" OR "MRO")
```

### Search for evidence of the actual problem

Rather than relying solely on titles, look for candidates whose profiles mention relevant shipping responsibilities or systems.

```text
site:linkedin.com/in
("LTL" OR "less than truckload")
("shipping manager" OR "transportation manager")
```

```text
site:linkedin.com/in
("carrier management" OR "carrier selection")
("logistics manager" OR "transportation manager")
```

```text
site:linkedin.com/in
("freight audit" OR "freight spend")
("transportation manager" OR "logistics manager")
```

```text
site:linkedin.com/in
("TMS" OR "transportation management system")
("shipping manager" OR "logistics manager")
```

```text
site:linkedin.com/in
("parcel" AND "LTL")
("logistics manager" OR "transportation manager")
```

### Search by technology

```text
site:linkedin.com/in
("ShipStation" OR "Pacejet" OR "ShipHawk")
("logistics" OR "shipping" OR "transportation")
```

```text
site:linkedin.com/in
("UPS WorldShip" OR "FedEx Ship Manager")
("shipping manager" OR "warehouse manager")
```

```text
site:linkedin.com/in
("NetSuite" OR "Sage" OR "Epicor")
("shipping manager" OR "logistics manager")
```

### Search for candidates who may be more willing to participate

```text
site:linkedin.com/in
("transportation manager" OR "logistics manager")
("open to work" OR "seeking new opportunities")
```

```text
site:linkedin.com/posts
("logistics manager" OR "transportation manager")
("laid off" OR "open to work" OR "job search")
```

Former transportation/logistics employees can be particularly useful discovery participants because they retain detailed domain knowledge while potentially having fewer concerns about discussing prior workflows.

### General-purpose starting query

```text
site:linkedin.com/in
("shipping manager" OR "transportation manager" OR "logistics manager")
("LTL" OR "parcel" OR "carrier" OR "freight")
("distribution" OR "manufacturing" OR "industrial")
```

Vary the final industry term to test different verticals.

## 5. Finding Professional Email Addresses

Once a candidate has been identified:

```text
Google / external discovery
        ↓
Name + title + company + LinkedIn URL
        ↓
Determine company domain
        ↓
Email enrichment
        ↓
Verify professional email
        ↓
Research invitation
```

Focus on professional/company addresses rather than trying to uncover private personal addresses.

### Hunter

Hunter's Email Finder can identify a likely professional email from a person's identity/company information, and its API supports LinkedIn handles as identifiers.

Useful characteristics:

- Straightforward email-finding workflow
- 1 credit when Email Finder successfully finds an email
- No Email Finder credit consumed when no email is found
- Verification capabilities
- Suitable when the candidate has already been identified

Current pricing discussed:

| Plan | Credits/month | Annual-billing equivalent |
|---|---:|---:|
| Free | 50 | $0 |
| Starter | 2,000 | ~$34/month |
| Growth | 10,000 | ~$104/month |
| Scale | 25,000 | ~$209/month |

Pricing and credit rules can change, so verify them before purchasing.

### Apollo

Apollo's People Enrichment API accepts a LinkedIn profile URL (`linkedin_url`) and can return a matched person's business information, including email when available.

Conceptual workflow:

```text
LinkedIn URL
     ↓
Apollo People Enrichment
     ↓
Email + email status
```

Apollo's credit model is more complex than Hunter's. Standard enrichment can consume credits based on the information returned, while waterfall enrichment and mobile-phone enrichment can consume additional credits.

Apollo is more attractive when the system needs broader prospecting/enrichment capabilities in addition to email discovery.

## 6. Recommended Enrichment Strategy

For this discovery project, a practical waterfall is:

```text
Candidate identified
        ↓
Check available professional contact information
        ↓
Hunter Email Finder
        ↓
If unsuccessful → Apollo enrichment
        ↓
Email verification
        ↓
Store source + confidence + verification status
        ↓
Outreach
```

Alternatively, Apollo can be placed first if broader prospect enrichment is important.

A candidate record could include:

```text
name
title
company
industry
company_size
linkedin_url
company_domain
email
email_source
email_confidence
verification_status
mutual_connection
research_topic
employment_status
outreach_status
interview_status
referral_source
```

## 7. Recommended Discovery Funnel

Do not initially optimize for hundreds or thousands of contacts. Start with a small, highly qualified sample and learn which characteristics predict interview participation.

Example:

```text
30 highly qualified candidates
        ↓
Outreach
        ↓
Measure response/interview conversion
        ↓
Identify strongest:
  industry
  company size
  title
  shipping pain signal
  employment status
  outreach message
        ↓
Expand to 100–300 candidates
```

After each successful interview, ask:

> Who are one or two other people working with shipping or transportation operations whom you think I should talk to?

This can gradually replace cold prospecting with referral-based recruiting.

## 8. Longer-Term Recruiting-Agent Workflow

The process could eventually be automated as:

```text
Study ICP
   ↓
Company discovery
   ↓
Candidate discovery via Google/public sources
   ↓
Candidate qualification
   ↓
LinkedIn identity/profile URL
   ↓
Professional email enrichment
   ↓
Email verification
   ↓
Personalized research invitation
   ↓
Follow-up
   ↓
AI interview
   ↓
Completion tracking
   ↓
Referral request
   ↓
Experiment results feed future targeting
```

The key optimization metric should ultimately be **completed qualified interviews per unit of recruiting cost/time**, rather than simply the number of contacts or emails discovered.

## Useful Resources

- OptiRule: https://www.optirule.com/
- Hunter: https://hunter.io/
- Hunter API: https://hunter.io/api-documentation
- Apollo: https://www.apollo.io/
- Apollo API documentation: https://docs.apollo.io/
