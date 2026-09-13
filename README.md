
  This repository contains a Proof of Concept for discovering and validating UK VAT numbers from the open web.   The core focus of this project was not just scraping, but evaluating the feasibility, cost, and challenges of scaling this to 4.2 million UK companies.

    Part 1: Research & The Discovery Trail
  My initial thesis was that e-commerce regulations require online businesses to publish their VAT numbers. However, getting from a company name to a verified VAT number revealed several structural roadblocks.
  
      The Strategy
  To prevent spamming the HMRC API and getting rate-limited, I implemented a mathematical filter. UK VAT numbers are 9 digits, but they follow a specific Modulo 97 checksum. My pipeline extracts 9-digit strings using Regex, strips the formatting, and applies the Modulo 97 algorithm. If the math fails, the string is dropped instantly.
  
      Dead Ends & Pivot Points
  Third-Party B2B Directories: I initially tried to solve Domain Discovery by querying third-party directories , like Endole, on a sample of recently incorporated companies.
  
      Why it failed: 
  The coverage for newly incorporated entities and micro-businesses (e.g., single-person IT contractors) is exceptionally poor. Buying or scraping B2B directory data is a trailing indicator and highly susceptible to data poisoning.
  
      The "Ghost Company" Problem: 
  The I drew a purely random sample from the Companies House bulk data.
  
      Why it failed: 
  A random sample yielded holding companies, dormant entities, and RTMs (e.g., 1 -4 JOSEPHINE CLOSE RTM COMPANY LTD). These do not have websites or VAT numbers. I had to pivot and write a programmatic filter (better_extractor.py) to sample only "Active" companies with specific e-commerce/tech SIC codes.
  
      The JavaScript Problems: 
  Then I pointed my scraper at the hompages of target companies.
  
      Why it failed: 
  Enterprise retailers do not put tax info on marketing homepages; it lives on /terms-and-conditions or /company-information. Furthermore, modern sites use JavaScript to render footers. A standard Python HTTP GET request sees only blank HTML.
  
    Part 2: Proof of Concept
      Methodology
      Sample Generation: 
Using better_extractor.py, I parsed the 4GB Companies House bulk dataset, filtering for active companies in retail/software SIC categories, generating a targeted sample of businesses highly likely to trade online. I manually curated the domains for these targets in business_sample.csv.

      The Pipeline (final_run.py): 
  The script navigates to the target URLs, extracts text, applies the Regex and Modulo 97 checksum, and isolates valid numbers.
  
      Verification Pivot: 
  During testing, the HMRC API silently rejected validation requests. To prove the Proof of Concept works, I bypassed the API and manually verified the extracted, mathematically valid numbers (e.g., Brewdog PLC) via the official GOV.UK web interface. (See proof_of_verification.png in repo).
  
    Results & Metrics
      Coverage Limitations: 
  My current text-based requests scraper does not capture VAT numbers embedded in images/PDFs. Furthermore, enterprise sites (like ASOS or Gymshark) use Cloudflare bot protection, which blocked the basic Python scraper entirely.
  
      False-Positive Rate:  
  The mathematical precision (Modulo 97) is near 100% for isolating valid VAT formats. However, the entity resolution false-positive rate (finding a valid VAT that belongs to a web agency rather than the target company) requires API resolution to calculate perfectly. Based on manual GOV.UK checks of the extracted numbers, my estimated entity false-positive rate is ~10-15% when relying solely on footer scraping without fuzzy name-matching validation.
  
    Part 3: Scaling Up with Real Resources
  Running this on a personal laptop relies on sequential HTTP requests. To scale this to 4.2 million companies, the pipeline requires enterprise architecture.
  
      Infrastructure & Proxies: 
  The primary bottleneck is bot-protection (WAFs like Cloudflare). The pipeline must utilize a distributed Kubernetes cluster running headless browsers (like Playwright) to execute JavaScript, routed through rotating residential proxies (e.g., BrightData) to avoid IP bans.
  
      Domain Discovery: 
  We cannot manually Google 4.2 million domains. We would need to ingest the Common Crawl web archive or license a commercial Domain-to-Company mapping dataset.
  
      Estimated Cost: 
  Assuming residential proxies cost ~$15/GB and rendering a headless legal page takes ~2MB, proxy costs are roughly $0.03 per scrape. Factoring in AWS compute, a rough estimate is $0.04 - $0.05 per company. Processing 4.2 million companies would cost roughly $168,000 to $210,000, making targeted scraping (filtering by SIC code/revenue size) economically necessary.

      What Breaks First: 
  The HMRC API. Even with an OAuth token, checking millions of scraped numbers will trigger rate limits. The Modulo 97 checksum is absolutely critical in production to ensure we only send perfect candidates to the API.

    Part 4: Debate Topics
        Brute-forcing the Modulo 97 Checksum: 
  UK VAT numbers are 9 digits, meaning there are 1 billion combinations. Because of the Modulo 97 rule, roughly 10 million are mathematically valid. Pointing all 10 million at HMRC is a terrible idea. It constitutes a DDoS attack, will result in immediate API revocation, and knowing a number is valid doesn't tell you who it belongs to.
  
      Keeping the dataset current: 
  Companies House publishes daily update feeds. I would ingest this feed to immediately flag companies that go into liquidation or change names. For active companies, I would schedule a background job to re-verify their VAT against HMRC every 6 months.

      Monitoring accuracy without a ground truth: 
  Statistical sampling. Every month, a random sample of 500 automated matches must be sent to a human annotation team. If human QA determines that 5% of the automated matches are incorrect, we know pipeline precision is 95%. When that drops, we adjust fuzzy-matching thresholds.
  
      Risky Sources: 
  I would strictly avoid scraping other commercial data brokers or B2B directories. Doing so violates Terms of Service (legal risk), and more importantly, it causes "data poisoning." If they hallucinated a VAT match, we ingest their error, creating a closed loop of false positives that is impossible to debug.
  
      Part 5: Beyond the UK
  Germany is a significantly harder market for this problem because the bottleneck shifts from Discovery to Verification.
  In Germany, the company registration number is separate from the VAT number. While discovering the VAT via scraping legal pages is actually easier due to strict German transparency laws, verifying it is incredibly difficult.
  Unlike HMRC, the German Federal Central Tax Office API does not allow open public verification. To query their API, you must provide your own valid German VAT number to prove you are a registered European entity conducting a B2B transaction. Therefore, a foreign data company cannot build this dataset at scale without establishing a local corporate proxy entity to run the API validations.
