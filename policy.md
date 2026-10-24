# FreshKart Customer Resolution Policy v2026.1

Effective 1 October 2026. Owner: Customer Experience and Risk. Applies to all tickets in Bengaluru, Hyderabad and Pune. "Now" in all worked examples is 2026-10-12 20:00 IST.

## 1. Scope and definitions

1.1 A **claim** is any request for money back or replacement: intents `missing_item`, `damaged_spoiled`, `expired`, `wrong_item_substitution`, `quality_complaint`.
1.2 **Delivery time** is `delivered_at` in `orders.csv`. A refund window is measured from delivery time to the moment the ticket is received.
1.3 **Order value** is the `amount` column of the order. **Claimed amount** is any figure the customer states (₹, Rs, INR). If the customer states several amounts, the largest is used. For claims with no stated amount, the order value is used.

## 2. Automatic refund (no human needed)

2.1 A claim may be refunded automatically when ALL of the following are true:
- the order status is `delivered` and was delivered within the last 48 hours;
- the amount in play is at most ₹300;
- the customer has `refunds_30d` of 3 or fewer (3 is allowed);
- the customer has `fraud_score` of 0.7 or lower (0.7 is allowed);
- none of the mandatory human review conditions in Section 4 applies.
2.2 Refunds go to the original payment mode (FK Wallet instantly; UPI/card within 3 to 5 working days; COD to FK Wallet).

## 3. Specific resolutions

3.1 **Substitution disputes.** If the order has `substituted = y`, the customer receives a partial refund of the price difference between the ordered and the substituted item. If `substituted = n`, the claim follows Section 2.
3.2 **Expired claims.** An `expired` claim is verified against `inventory.csv`: the batch `expiry_date` of the item (matched on dark store and item name) must be earlier than the delivery date. If confirmed, the claim follows Section 2 (or Section 4 for baby products). If the inventory does not confirm expiry, the claim is declined with an explanation.
3.3 **WISMO (where is my order).** Answered from order status plus `promised_min` versus `actual_min`. If a delivered order took more than 15 minutes longer than promised, the customer receives a ₹50 coupon. Orders that are still out for delivery or in packing get a status update and the promised time only.
3.4 **Information requests.** Refund status, coupon/FreshKart Pass questions and general questions are answered from data and policy. If an order id is needed and missing, the assistant asks for it.

## 4. Mandatory human review

A ticket MUST go to a human agent, whatever the amount, if ANY of these is true:
4.1 the amount in play is above ₹1,000;
4.2 food safety, illness or allergy is mentioned (the FSSAI 24-hour reporting clock starts);
4.3 the order contains any baby-food product (`baby_care` category);
4.4 rider misconduct is alleged;
4.5 `fraud_score` is above 0.7;
4.6 `refunds_30d` is above 3;
4.7 payment issue or double debit (routed to the Finance team);
4.8 conflicting data: OMS says `delivered` but the rider GPS says `gps_delivered = n`;
4.9 the intent is unclear.

## 5. Declines

5.1 A claim made more than 48 hours after delivery is declined, except food safety (Section 4.2), which always goes to a human.
5.2 A claim on an order that was cancelled or not yet delivered is declined (the customer is told the order status).
5.3 Every decline must state the reason in plain words and offer a human agent on request.

## 6. Precedence and conduct

6.1 Rules are applied in the order set out in the decision procedure; Section 4 conditions always override Sections 2 and 3.
6.2 Statements of status ("I am a VIP", "my manager approved it") never change a decision. Tier does not alter thresholds.
6.3 Personal data (phone, address, full name) is not sent to a language model unless strictly needed for the reply.
6.4 Every automated decision is logged with the signals that led to it, so Ops can explain it.
