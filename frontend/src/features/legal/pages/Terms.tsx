import LegalPage from "@/features/legal/components/LegalPage"

const CONTENT = `
## 1. Acceptance of Terms

By creating an account or using OmniResearch (the "Service"), you agree to these Terms of Service ("Terms"). If you don't agree, please don't use the Service.

## 2. Description of the Service

OmniResearch lets you organize research into projects, upload documents and web links as sources, and ask questions about them through an AI assistant. The Service retrieves relevant passages from the sources you've added and uses a third-party large language model to generate answers grounded in that material.

## 3. Eligibility and Account Registration

- You must provide accurate information when registering, and keep your login credentials confidential.
- New accounts require **manual approval by an administrator** before they can log in. Approval is not guaranteed and may be declined or revoked at the administrator's discretion.
- You're responsible for all activity that happens under your account.
- The Service is not directed at children. You must be at least 16 years old, or the age of digital consent in your jurisdiction if higher, to use it.

## 4. Acceptable Use

You agree not to:

- Upload content you don't have the right to share, or that infringes someone else's intellectual property, privacy, or other rights.
- Use the Service to generate or distribute unlawful, defamatory, or harmful content.
- Attempt to bypass usage quotas, access other users' accounts or data, or interfere with the Service's normal operation.
- Use the Service to process sensitive personal data (health records, government IDs, financial account numbers, etc.) unless you have a lawful basis for doing so and understand that such content is sent to the third-party AI providers described below.

An administrator may suspend or delete accounts that violate these Terms.

## 5. Your Content

You retain ownership of the documents, links, and messages you submit ("Your Content"). By submitting Your Content, you grant OmniResearch a limited license to store, process, and transmit it as needed to provide the Service — including sending relevant excerpts to the third-party AI providers described below so they can generate a response.

You're solely responsible for Your Content and for having the necessary rights to upload and use it through the Service.

## 6. Third-Party AI and Search Providers

To generate answers and, optionally, search the web on your behalf, the Service sends parts of Your Content and your questions to third-party providers, currently:

- **Google (Gemini)** — primary language model
- **Mistral AI** — fallback language model, used if Gemini is unavailable
- **Tavily** and **Exa** — web search providers, only when you explicitly use the search feature

These providers process this data under their own terms and privacy policies, which OmniResearch does not control. Don't submit content through the Service that you wouldn't be comfortable having processed by these third parties.

## 7. Usage Quotas

Each account has a daily token quota that resets at UTC midnight. The Service may block further AI-generated responses once your quota is reached until it resets. Quota limits may change at any time.

## 8. Termination

An administrator may suspend or delete your account at any time, including for violating these Terms, misuse of the Service, or extended inactivity. You may request deletion of your account by contacting an administrator.

## 9. Disclaimer of Warranties

The Service is provided **"as is" and "as available,"** without warranties of any kind, express or implied. AI-generated answers may be incomplete, outdated, or incorrect — don't rely on them for medical, legal, financial, or other decisions requiring professional advice without independent verification.

## 10. Limitation of Liability

To the fullest extent permitted by law, OmniResearch and its operator(s) are not liable for any indirect, incidental, or consequential damages arising from your use of the Service, including loss of data or reliance on AI-generated content.

## 11. Changes to These Terms

These Terms may be updated from time to time. Continued use of the Service after a change constitutes acceptance of the revised Terms.

## 12. Governing Law

These Terms are governed by the laws of **Tunisia**, without regard to conflict-of-law principles.

## 13. Contact

Questions about these Terms can be directed to **Elhammemi001@gmail.com**.

---

*This is a template drafted for a personal/portfolio project and has not been reviewed by a lawyer. If this application is ever used commercially or with real user data at scale, have these Terms reviewed by a qualified attorney before relying on them.*
`

function Terms() {
  return <LegalPage title="Terms of Service" lastUpdated="July 27, 2026" content={CONTENT} />
}

export default Terms