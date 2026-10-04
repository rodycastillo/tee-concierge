# 8. Meta WhatsApp Cloud API Setup (step by step)

Goal: get a **test phone number**, an **access token** and a **webhook** pointing at the bot. Needed from Phase 2. It is free in the sandbox.

> Meta's UI changes often. If a screen differs, search the same keywords in the Meta docs: "WhatsApp Cloud API get started".

## Step 1: Prerequisites
- A personal **Facebook account**
- A phone with WhatsApp, to receive test messages (you can add up to 5 recipient numbers in the sandbox)

## Step 2: Create a Meta Developer account
1. Go to <https://developers.facebook.com> and log in.
2. Click **Get Started** and complete the developer registration (verify email and phone).

## Step 3: Create a Meta Business portfolio (Business Account)
1. Go to <https://business.facebook.com> and create a business portfolio called "Tee Concierge".
2. You can skip **Business verification** for now. It is only needed to go to production with your own number and higher limits.

## Step 4: Create the app
1. In developers.facebook.com, click **My Apps**, then **Create App**.
2. Use case: **Other** (or **Connect with customers through WhatsApp**), then app type **Business**.
3. Name it "tee-concierge" and link the Business portfolio from Step 3.
4. In the app dashboard, add the product **WhatsApp** and click **Set up**.

## Step 5: Use the free test number
1. Go to **WhatsApp > API Setup**.
2. Meta gives you a **test phone number** and its **Phone number ID**. Copy the Phone number ID and the **WhatsApp Business Account ID**.
3. In **To**, add your personal number as a recipient and confirm the code WhatsApp sends you.
4. Send the sample "hello_world" template to check it works.

## Step 6: Get a token
- The dashboard shows a **temporary access token** (valid 24h). Fine for the first tests.
- For a permanent token: Business settings > **Users > System users** > create a system user (Admin) > **Add assets** (your app, full control) > **Generate token** with permissions `whatsapp_business_messaging` and `whatsapp_business_management`. Store it safely.

## Step 7: Collect the values the bot needs
| Variable | Where it comes from |
|---|---|
| `WHATSAPP_PHONE_NUMBER_ID` | API Setup page |
| `WHATSAPP_ACCESS_TOKEN` | Step 6 |
| `WHATSAPP_APP_SECRET` | App dashboard > **App settings > Basic > App secret** (used to verify webhook signatures) |
| `WHATSAPP_VERIFY_TOKEN` | A random string you invent (used in the webhook handshake) |

Put them in a local `.env` file (never commit it; `.env.example` lists the names).

## Step 8: Expose your local server (Phase 2)
Meta needs a public HTTPS URL. For development, use a tunnel:
- **ngrok** (`ngrok http 8000`) or **cloudflared** (`cloudflared tunnel --url http://localhost:8000`)

## Step 9: Configure the webhook (Phase 2)
1. **WhatsApp > Configuration > Webhook > Edit**.
2. **Callback URL:** `https://<your-tunnel>/webhook`. **Verify token:** your `WHATSAPP_VERIFY_TOKEN`.
3. Click **Verify and save** (the bot must be running).
4. **Webhook fields:** subscribe to **messages**.

## Step 10: Test
Send "Hola" from your personal number to the test number. The webhook should receive it.

## Later (production)
- Add your real number (it must not be tied to a personal WhatsApp account) and complete **Business verification**.
- Create a Meta payment method for conversation charges (user-initiated conversations are free within limits).
- Create a profile (name, photo, description).
