import LegalPage from "@/features/legal/components/LegalPage"

const CONTENT = `
## 1. What Are Cookies

Cookies are small pieces of data stored in your browser. They can be used for things like keeping you signed in, remembering preferences, or tracking behavior across sites.

## 2. Cookies We Use

OmniResearch uses exactly **one cookie**, and nothing else:

| Cookie | Purpose | Type |
|---|---|---|
| \`access_token\` | Keeps you signed in between requests | Strictly necessary, first-party, httpOnly |

This cookie is set when you log in and cleared when you log out. It's marked **httpOnly** (not readable by JavaScript, which helps protect it from cross-site scripting attacks) and **SameSite=Lax** (not sent on most cross-site requests, which helps protect against cross-site request forgery). It contains only a signed session token so no tracking identifiers, no advertising data.

## 3. Cookies We Don't Use

OmniResearch does **not** use analytics cookies, advertising cookies, or any third-party tracking cookies. We don't run Google Analytics, ad networks, or similar services on this site.

## 4. Managing Cookies

Because the \`access_token\` cookie is strictly necessary for the Service to function, there's no in-app option to disable it selectively, if you block or clear it (through your browser's cookie settings), you'll simply be signed out and need to log in again.

## 5. Changes to This Policy

If the Service's cookie usage changes in the future, for example, if analytics or additional first-party cookies are introduced, this policy will be updated to reflect that, and the "Last updated" date above will change accordingly.

## 6. Contact

Questions about this Cookie Policy can be directed to **Elhammemi001@gmail.com**.
`

function Cookies() {
  return <LegalPage title="Cookie Policy" lastUpdated="July 27, 2026" content={CONTENT} />
}

export default Cookies
