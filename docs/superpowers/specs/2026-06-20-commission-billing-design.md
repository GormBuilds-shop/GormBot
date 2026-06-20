# Commission System & Billing Design

## Overview

Extend the commission tracking system with full lifecycle management, multi-member assignment, and integrated billing with Stripe and crypto payment support.

## Schema Changes

### CommissionAssignment (new)

Links members to commissions (many-to-many).

| Column | Type | Notes |
|--------|------|-------|
| id | Integer | PK, auto-increment |
| commission_id | Integer | FK → Commission.id |
| member_id | BigInteger | Discord user ID |
| member_name | String | Display name at assignment time |
| assigned_at | DateTime | UTC timestamp |

### Bill (new)

Tracks payment for a commission.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer | PK, auto-increment |
| commission_id | Integer | FK → Commission.id |
| total_amount | Numeric(10,2) | Total bill amount |
| currency | String | e.g. "USD" |
| deposit_percent | Integer | 0-100, default 50 |
| deposit_paid | Boolean | Default False |
| final_paid | Boolean | Default False |
| stripe_deposit_id | String | Nullable, Stripe PaymentIntent ID |
| stripe_final_id | String | Nullable |
| crypto_deposit_id | String | Nullable, your gateway's payment ID |
| crypto_final_id | String | Nullable |
| created_at | DateTime | UTC timestamp |

### BotConfig (new)

Key-value store for runtime configuration.

| Column | Type | Notes |
|--------|------|-------|
| key | String | PK, e.g. "stripe_enabled" |
| value | String | e.g. "true", "false" |

Initial keys:
- `stripe_enabled` (default: "true")
- `crypto_enabled` (default: "true")

## Commands

### Commission Lifecycle

| Command | Description | Validation |
|---------|-------------|------------|
| `/commission start` | Set status to `in_progress` | Must be `open` |
| `/commission complete` | Set status to `completed` | All bills must be fully paid |
| `/commission cancel` | Set status to `cancelled` | Any state |
| `/commission assign @member` | Add member to commission | In ticket channel with commission |
| `/commission unassign @member` | Remove member | Member must be assigned |
| `/commission info` | Show details, members, bill status | In ticket channel |

### Billing

| Command | Description | Notes |
|---------|-------------|-------|
| `/bill create <amount> [deposit_percent]` | Create bill | Default 50% deposit. Posts payment embed. |
| `/bill status` | Show payment status | Deposit/final, amounts, paid state |
| `/bill confirm deposit` | Manual mark deposit paid | Admin/staff only |
| `/bill confirm final` | Manual mark final paid | Admin/staff only |

### Configuration (Admin)

| Command | Description |
|---------|-------------|
| `/config payments stripe enable` | Enable Stripe payments |
| `/config payments stripe disable` | Disable Stripe payments |
| `/config payments crypto enable` | Enable crypto payments |
| `/config payments crypto disable` | Disable crypto payments |
| `/config payments status` | Show current toggle states |

## Payment Flow

### Bill Creation (`/bill create 500 50`)

1. Validate: ticket has commission, no unpaid bill exists
2. Create Bill record (total: $500, deposit: $250)
3. If Stripe enabled: create Stripe payment link for deposit
4. If crypto enabled: generate crypto payment request
5. Post embed in ticket with available payment options
6. Store payment IDs in Bill record

### Payment Confirmation

**Polling (automatic):**
- Background task runs every 60 seconds
- Queries Stripe API for unpaid bills with `stripe_deposit_id` or `stripe_final_id`
- Queries crypto gateway for unpaid bills with crypto IDs
- On payment detected:
  - Update Bill (`deposit_paid` or `final_paid`)
  - Post confirmation embed in ticket channel
  - If deposit just paid, generate final payment links

**Manual fallback:**
- `/bill confirm deposit` or `/bill confirm final`
- For: offline payments, API issues, custom arrangements

### Completion Validation

`/commission complete` checks:
- Bill exists for commission
- `deposit_paid` is True
- `final_paid` is True

If not, rejects with message showing what's unpaid.

## File Structure

```
db/
├── DatabaseSchema.py      # +CommissionAssignment, Bill, BotConfig
├── CommissionConnection.py # +assignment CRUD, bill queries
├── BillingConnection.py    # (new) Bill CRUD, payment status updates
├── ConfigConnection.py     # (new) BotConfig CRUD

modules/
├── CommissionTracking.py   # +lifecycle commands, assign/unassign, info
├── BillingSystem.py        # (new) /bill commands, polling task, payment embeds
├── ConfigSystem.py         # (new) /config commands
```

## Payment Provider Integration

### Stripe

- Use Stripe API to create Payment Links or Checkout Sessions
- Poll via `stripe.PaymentIntent.retrieve()` or list recent payments
- Store `payment_intent_id` in Bill

### Crypto Gateway

- Interface TBD (your custom gateway)
- Abstract behind `CryptoGateway` class with methods:
  - `create_payment(amount, currency) -> payment_id, payment_url`
  - `check_payment(payment_id) -> PaymentStatus`
- Supports both webhook callback and polling

## Error Handling

- Missing commission in ticket: "No commission found for this ticket"
- Bill already exists and unpaid: "Unpaid bill already exists. Use `/bill status`"
- Payment method disabled: Skip that option in embed, don't error
- Both methods disabled: "No payment methods available. Contact admin."
- Stripe/crypto API errors: Log error, continue polling next cycle

## Permissions

- `/commission start/complete/cancel`: Assigned members or admin
- `/commission assign/unassign`: Admin only
- `/bill create`: Assigned members or admin
- `/bill confirm`: Admin only
- `/config`: Admin only
