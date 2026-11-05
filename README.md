# Last Mile Logistics Auditor: Veridi Logistics

## A. Executive Summary

Veridi's delivery estimates are generally conservative rather than over-optimistic: 93.2% of 96,470 delivered orders arrived on or before the promised date, with a median of 12 days to spare. The 6.8% that arrived late are a regional problem, not a nationwide one: the five worst states (AL, MA, SE, PI and CE) are all in the Northeast and are late 13.8% to 21.4% of the time, and distance from São Paulo explains almost none of the pattern (rank correlation 0.06). Lateness is costly: the average review score falls from 4.29 for on-time orders to 2.99 for late orders and 1.74 for super-late orders, and 69% of super-late reviews give one star. Comparing promised with actual delivery time shows the issue is not simply tight estimates: the remote northern states AC, AP, AM and RO are promised 38 to 48 days and receive orders 20 to 23 days early at the median, while the five worst Northeast states have a median buffer of 10 to 14 days, similar to Paraná's, yet are late three to five times as often. The priority should be carrier and last-mile performance in the Northeast, with delivery estimates there reviewed against the slow end of delivery times rather than the median.

## B. Project Links

- **Link to Notebook:** https://colab.research.google.com/drive/141awNcubpaeYd603ZeWdsoUbG628xOHu
- **Link to Dashboard:** https://deg-veridi-last-mile-audit-01.streamlit.app/
- **Link to Presentation:** https://github.com/benjamina03/DEG-veridi-last-mile-audit/blob/main/Veridi%20Last-Mile%20Audit%20Presentation%20Deck.pdf


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











