# Last Mile Logistics Auditor: Veridi Logistics

## A. Executive Summary

Veridi's delivery estimates are generally conservative rather than over-optimistic: 93.2% of 96,470 delivered orders arrived on or before the promised date, with a median of 12 days to spare. The 6.8% that arrived late are a regional problem, not a nationwide one: the five worst states (AL, MA, SE, PI and CE) are all in the Northeast and are late 13.8% to 21.4% of the time, and distance from São Paulo explains almost none of the pattern (rank correlation 0.06). Lateness is costly: the average review score falls from 4.29 for on-time orders to 2.99 for late orders and 1.74 for super-late orders, and 69% of super-late reviews give one star. Comparing promised with actual delivery time shows the issue is not simply tight estimates: the remote northern states AC, AP, AM and RO are promised 38 to 48 days and receive orders 20 to 23 days early at the median, while the five worst Northeast states have a median buffer of 10 to 14 days, similar to Paraná's, yet are late three to five times as often. The priority should be carrier and last-mile performance in the Northeast, with delivery estimates there reviewed against the slow end of delivery times rather than the median.

## B. Project Links

- **Link to Notebook:** https://colab.research.google.com/drive/141awNcubpaeYd603ZeWdsoUbG628xOHu
- **Link to Dashboard:** https://deg-veridi-last-mile-audit-01.streamlit.app/


Files in this repo: `olist_last_mile_audit.ipynb` (notebook), `olist_last_mile_audit.ipynb - Colab` (export of the notebook with all charts), `app.py` + `requirements.txt` (dashboard), `dashboard_data/` (small CSVs exported by the notebook). The raw Olist CSVs are not included; download them from [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

## C. Technical Explanation

### Data cleaning

- **Files and sizes.** Orders 99,441 rows, reviews 99,224, customers 99,441, products 32,951, order items 112,650, category translation 71.
- **Joins (Story 1).** Customers were joined to orders on `customer_id` and reviews on `order_id`. Customers to orders is one-to-one, enforced with `validate="one_to_one"`. The reviews table is not one row per order: 1,098 review rows belong to orders that were reviewed more than once (547 orders). Joining as-is would have duplicated those orders, so I kept only the most recent review per order (by `review_answer_timestamp`), which dropped 551 rows. The master table has exactly one row per order (99,441), checked with assertions. 768 orders have no review; they stay in the table and are left out of review averages only.
- **Delay calculation (Story 2).** `Days_Difference = order_estimated_delivery_date - order_delivered_customer_date`, so positive means early and negative means late. Both dates were reduced to calendar dates first, because the estimate has no time of day and the delivery does; otherwise an order delivered in the afternoon of the promised day would count as late.
- **Classes.** On Time: 0 or more days early. Late: 1 to 5 days late. Super Late: more than 5 days late.
- **Missing values.** 2,971 orders have no usable delivery and are flagged "Not Delivered (excluded)": shipped 1,107, canceled 625, unavailable 609, invoiced 314, processing 301, created 5, approved 2, plus 8 orders marked `delivered` with no delivery date. That leaves 96,470 orders for the delivery analysis. No order was delivered before it was purchased. 646 of the analysed orders have no review, so review figures use 95,824 orders.
- **Categories (Bonus).** Product categories were translated with `product_category_name_translation.csv`. Two categories have no official translation (`pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`) and keep their Portuguese names; products without a category are labelled "unknown". Orders reach products through `order_items`, and one order can hold several categories, so category figures use one row per distinct order and category pair. This is kept out of the master table so that the master stays one row per order.
- **Remoteness.** The dataset has no distribution-center location. I assumed São Paulo as the hub (the largest seller base) and measured the straight-line distance from São Paulo to each state capital. This is an assumption, and straight-line distance ignores road and river routes.

### Results at a glance

| Question | Result |
|---|---|
| Orders delivered on or before the estimate | 93.2% (96,470 analysed orders), median 12 days early |
| Late / Super Late | 2.87% / 3.90% (6.77% combined) |
| Worst states | AL 21.4%, MA 17.4%, SE 15.2%, PI 13.9%, CE 13.8% (all Northeast) |
| Best of the states reported | AM 2.8%, RO 2.9%, AP 3.0%, AC 3.8% (the farthest from São Paulo) |
| Distance vs late % | Spearman 0.06 across 27 states |
| Average review: On Time / Late / Super Late | 4.29 / 2.99 / 1.74 |
| Share of 1-star reviews | 6.6% / 33.6% / 68.8% |
| Furniture vs electronics | `furniture_decor` 7.1% late (6,307 orders) vs `electronics` 7.6% (2,517): no meaningful difference |

Two caveats. First, late orders account for about 37% of all 1-star reviews, so most bad reviews (about 63%) come from orders that arrived on time and lateness is only part of the review problem. Second, rates for small states such as AC (80 orders) and AP (67 orders) move a lot with a handful of orders, so they should not be over-read. The North region (8.6% late) also hides a split: AC, AP, AM and RO together have 16 late orders out of 535, which implies the rest of the North (PA, RR, TO) is around 11% late.

### Candidate's Choice: promised vs actual delivery time by state

**What I added.** For each state, the median number of days promised (estimated date minus purchase date), the median number of days the delivery actually took (delivery date minus purchase date), the gap between them, and the late %. It is in the notebook and as the "Promised vs actual" tab of the dashboard.

**Why it matters.** The CEO's hunch is that the estimates themselves are wrong. Late % alone cannot say whether the fix is operational (carriers are slow) or about the promise shown to customers (the estimate is too tight). This view separates the two. It shows that the remote northern states are promised 38 to 48 days and get orders 20 to 23 days early, so they are rarely late and blanket padding would add nothing there. The five worst Northeast states have a median buffer of 10 to 14 days, similar to Paraná's, yet are late 3.4 to 5.3 times as often (13.8% to 21.4% vs 4.0%). With the same median buffer and different late rates, the likely culprit is how widely delivery times vary, not the median estimate. Veridi can therefore target carrier and last-mile work at the Northeast and change ETAs state by state, instead of lengthening estimates everywhere.


### Tools

Python (pandas, NumPy, matplotlib, seaborn) in Google Colab; dashboard in Streamlit with Plotly, deployed on Streamlit Community Cloud. All paths are relative: put the Olist CSVs next to the notebook and run all cells.

---

# Project Brief: The "Last Mile" Logistics Auditor

**Client:** Veridi Logistics (Global E-Commerce Aggregator)
**Deliverable:** Public Dashboard, Code Notebook & Insight Presentation

---

## 1. Business Context

**Veridi Logistics** manages shipping for thousands of online sellers. Recently, the CEO has noticed a spike in negative customer reviews. She has a "gut feeling" that the problem isn't just that packages are late, but that the estimated delivery dates provided to customers are wildly inaccurate (i.e., we are over-promising and under-delivering).

She needs you to audit the delivery data to find the root cause. She specifically wants to know: **"Are we failing specific regions, or is this a nationwide problem?"**

Your job is to build a "Delivery Performance" audit tool that connects the dots between **Logistics Data** (when a package arrived) and **Customer Sentiment** (how they rated the experience).

## 2. The Data

You will use the **Olist E-Commerce Dataset**, a real commercial dataset from a Brazilian marketplace. This is a relational database dump, meaning the data is split across multiple CSV files.

- **Source:** [Kaggle - Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- **Key Files to Use:**
  - `olist_orders_dataset.csv` (The central table)
  - `olist_order_reviews_dataset.csv` (Sentiment)
  - `olist_customers_dataset.csv` (Location)
  - `olist_products_dataset.csv` (Categories)

## 3. Tooling Requirements

You have the flexibility to choose your development environment:

- **Option A (Recommended):** Use a cloud-hosted notebook like **Google Colab**, or **Deepnote**, etc.
- **Option B:** Use a local **Jupyter Notebook** or **VS Code**.
  - _Condition:_ If you choose this, you must ensure your code is reproducible. Do not reference local file paths (e.g., `C:/Downloads/...`). Assume the dataset is in the same folder as your notebook.
- **Dashboarding:** The final output must be a **publicly accessible link** (e.g., Tableau Public, Google Looker Studio, Streamlit Cloud, or PowerBI Web, etc.).

---

## 4. User Stories & Acceptance Criteria

### Story 1: The Schema Builder

**As a** Data Engineer,
**I want** to join the Orders, Reviews, and Customers tables into a single master dataset,
**So that** I can analyze a customer's location and their review score in the same row.

- **Acceptance Criteria:**
  - Load the raw CSVs into your notebook.
  - Perform the correct joins (e.g., join Reviews to Orders on `order_id`, join Customers to Orders on `customer_id`).
  - **Check:** Ensure you don't accidentally duplicate rows (a common error with 1-to-many joins).

### Story 2: The "Real" Delay Calculator

**As a** Logistics Manager,
**I want** to know the difference between the "Estimated Delivery Date" and the "Actual Delivery Date,"
**So that** I can see how often we are lying to customers.

- **Acceptance Criteria:**
  - Create a new calculated column: `Days_Difference` = `order_estimated_delivery_date` - `order_delivered_customer_date`.
  - Classify orders into statuses: "On Time", "Late", and "Super Late" (> 5 days late).
  - Handle missing values: Some orders were never delivered (`order_status` = 'canceled' or 'unavailable'). These should be excluded or flagged separately.

### Story 3: The Geographic Heatmap

**As a** Regional Director,
**I want** to see which specific States (`customer_state`) have the highest percentage of late deliveries,
**So that** I can focus my repair efforts on the worst regions.

- **Acceptance Criteria:**
  - Calculate the % of late orders per State.
  - Visualize this on a map or a bar chart.
  - **Insight:** Identify if "Remote" states (far from the distribution center) are disproportionately affected.

### Story 4: The Sentiment Correlation

**As a** Customer Success Lead,
**I want** to see if late deliveries actually cause bad reviews,
**So that** I can prove to the CEO that logistics is the problem.

- **Acceptance Criteria:**
  - Create a visualization comparing "Delivery Delay (Days)" vs "Average Review Score (1-5)".
  - Show the average review score for "On Time" orders vs. "Late" orders.

---

## 5. Bonus User Story: The "Translation" Challenge

**As a** Global Analyst,
**I want** to see product categories in **English**, not Portuguese,
**So that** I can understand if "Furniture" is harder to ship than "Electronics".

- **Acceptance Criteria:**
  - The `product_category_name` is in Portuguese (e.g., `cama_mesa_banho`).
  - Use the `product_category_name_translation.csv` file included in the dataset (or create your own mapping) to translate these into English for your final dashboard.

---

## 6. The "Candidate's Choice" Challenge

**As a** Creative Problem Solver,
**I want** to include one extra feature or analysis that adds specific business value,
**So that** I can demonstrate my ability to think beyond the basic requirements.

- **Instructions:**
  - Add one more metric, chart, or drill-down.
  - **Requirement:** You must justify _why_ this feature matters to the business in your README.

---

## 7. Submission Guidelines

Please edit this `README.md` file in your forked repository to include the following three sections at the top:

### A. The Executive Summary

- A 3-5 sentence summary of your findings.

### B. Project Links

- **Link to Notebook:** (e.g., Google Colab, etc.). _Ensure sharing permissions are set to "Anyone with the link can view"._
- **Link to Dashboard:** (e.g., Tableau Public, etc.).
- **Link to Presentation:** A link to a short slide deck (PDF/PPT) AND (Optional) a 2-minute video walkthrough (YouTube) explaining your results.

### C. Technical Explanation

- Briefly explain how you handled the "Data Cleaning".
- Explain your "Candidate's Choice" addition.

**Important Note on Code Submission:**

- Upload your `.ipynb` notebook file to the repo.
- **Crucial:** Also upload an **HTML or PDF export** of your notebook so we can see your charts even if GitHub fails to render the notebook code.
- Once you are ready, please fill out the [Official Submission Form Here](https://forms.cloud.microsoft/e/CeQN2mCyUr) with your links

---

## 🛑 CRITICAL: Pre-Submission Checklist

**Before you submit your form, you MUST complete this checklist.**

> ⚠️ **WARNING:** If you miss any of these items, your submission will be flagged as "Incomplete" and you will **NOT** be invited to an interview.
>
> **We do not accept "permission error" excuses. Test your links in Incognito Mode.**

### 1. Repository & Code Checks

- [ ] **My GitHub Repo is Public.** (Open the link in a Private/Incognito window to verify).
- [ ] **I have uploaded the `.ipynb` notebook file.**
- [ ] **I have ALSO uploaded an HTML or PDF export** of the notebook.
- [ ] **I have NOT uploaded the massive raw dataset.** (Use `.gitignore` or just don't commit the CSV).
- [ ] **My code uses Relative Paths.**

### 2. Deliverable Checks

- [ ] **My Dashboard link is publicly accessible.** (No login required).
- [ ] **My Presentation link is publicly accessible.** (Permissions set to "Anyone with the link can view").
- [ ] **I have updated this `README.md` file** with my Executive Summary and technical notes.

### 3. Completeness

- [ ] I have completed **User Stories 1-4**.
- [ ] I have completed the **"Candidate's Choice"** challenge and explained it in the README.

**✅ Only when you have checked every box above, proceed to the submission form.**

---
