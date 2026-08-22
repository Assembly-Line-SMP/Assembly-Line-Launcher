# Microsoft Sign-In Setup

The launcher needs an Azure AD "public client" application registration
to let players sign in with a real Microsoft/Xbox account (premium/online
mode). This document explains where the current client ID comes from, how
to swap in your own, and how to register one when you're able to.

## Current state

`MS_CLIENT_ID` in [`src/launcher/constants.py`](../src/launcher/constants.py)
is currently set to Prism Launcher's public client ID:

```
c36a9fb6-4f2a-41ff-90bd-ae7cc92031eb
```

This value comes directly from Prism Launcher's own `CMakeLists.txt`
(https://github.com/PrismLauncher/PrismLauncher/blob/develop/CMakeLists.txt),
where it's published deliberately, alongside a comment inviting forks and
rebrands to reuse it. It is **a stand-in, not a permanent choice** — it
works today, but it's someone else's registration, not this project's own,
and Microsoft could rate-limit or revoke it at any time for reasons that
have nothing to do with this launcher.

Switch to your own client ID the moment you're able to register one.

## How to swap the client ID

This is a one-line change, wherever the new ID comes from:

1. Open `src/launcher/constants.py`.
2. Replace the value of `MS_CLIENT_ID` with your new GUID.
3. That's it — every auth call reads from this one constant. Nothing else
   in the codebase needs to change.

To disable Microsoft sign-in entirely instead (cracked-only build), set
`MS_CLIENT_ID` back to the placeholder:

```python
MS_CLIENT_ID = "00000000-0000-0000-0000-000000000000"
```

The launcher detects this exact value and shows a clean "not configured"
message in the Accounts dialog instead of attempting to authenticate and
failing with a confusing error.

## Registering your own Azure AD application

When you have access to an Azure AD tenant that allows creating app
registrations (a work/school Microsoft 365 tenant, an Azure free-tier
subscription, or once Microsoft's personal-tenant restrictions permit it
again):

1. Go to [portal.azure.com](https://portal.azure.com) → **App registrations**
   → **New registration**.
2. Name it something that clearly identifies your launcher and does **not**
   imply it's an official Mojang/Microsoft product (e.g. "Assembly Line SMP
   Launcher").
3. Under **Supported account types**, choose
   **Personal Microsoft accounts only** (this launcher only ever
   authenticates individual players' personal accounts, not organizational
   accounts).
4. Leave **Redirect URI** blank — the device-code flow this launcher uses
   doesn't need one.
5. After creation, go to **Authentication**:
   - Under **Advanced settings**, set **Allow public client flows** to
     **Yes**. This is required — without it, the device-code flow (step 1
     in `src/launcher/auth/microsoft.py`) will be rejected.
6. Do **not** create a client secret. Public clients (like a desktop
   launcher) authenticate without one; a secret embedded in distributed
   application code isn't actually secret, and Microsoft's public client
   flows are designed around not needing one.
7. Copy the **Application (client) ID** from the app's Overview page.
8. Paste it into `MS_CLIENT_ID` in `constants.py` as described above.

This is free on any tenant that allows app registrations at all — there's
no cost tied to the registration itself, only to certain premium Azure AD
tiers/features this launcher doesn't use.

## Why a client ID is needed at all

Minecraft: Java Edition's login chain (documented at
https://wiki.vg/Microsoft_Authentication_Scheme, which this launcher's
`auth/microsoft.py` follows) requires an OAuth2 flow against Microsoft's
identity platform before it will hand back an Xbox Live token, which in
turn is exchanged for a Minecraft access token. Every third-party launcher
(Prism Launcher, MultiMC forks, etc.) registers its own Azure AD app for
exactly this reason — there's no way to skip this step and still support
real Microsoft account sign-in.

## What happens if the shared client ID stops working

If Prism Launcher's client ID is ever revoked, rate-limited, or otherwise
stops working for this launcher, players will see a sign-in failure when
trying to add a Microsoft account. Cracked (offline) accounts are
unaffected either way — they never touch this code path at all.
