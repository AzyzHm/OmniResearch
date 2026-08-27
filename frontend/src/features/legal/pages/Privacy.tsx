import LegalPage from "@/features/legal/components/LegalPage"

const CONTENT = `
## 1. Introduction

This Privacy Policy explains what information OmniResearch (the "Service") collects, how it's used, and who it's shared with. It applies to anyone who creates an account or uses the Service.

## 2. Information We Collect

**Account information:** username and password. Passwords are hashed (Argon2id) before storage — the Service never stores or has access to your plaintext password.

**Login activity:** each login is logged with your username, the timestamp, and your IP address. This is used for security monitoring and is visible to administrators.

**Your Content:** the documents, text files, and URLs you add to a project, along with the text extracted and embedded from them, and the messages you send in chat. This content is stored so the Service can retrieve and reference it in future conversations.

**Usage data:** the number of AI calls and tokens used, and (if you use the search feature) the number of web searches and search credits consumed. This is used to enforce daily usage quotas and is visible to administrators in aggregate and per-user form.

## 3. How We Use Your Information

We use the information above to:

- authenticate you and keep your account secure,
- provide the core functionality of the Service (retrieving your sources and generating answers),
- monitor for abuse and enforce usage quotas,
- maintain and improve the Service.

We do not sell your information, and we do not use it for advertising.

## 4. Third-Party Service Providers

Providing the Service requires sharing some data with third parties:

- **Supabase** — hosts the Service's relational database (account records, project/chat metadata, login logs, usage statistics).
- **Google (Gemini)** and **Mistral AI** — process the content of your questions and relevant excerpts of Your Content to generate AI responses.
- **Tavily** and **Exa** — process your search queries if you use the web search feature, and return results which may be added to your project.

Each of these providers handles data under their own privacy policy, which we encourage you to review if you have concerns about a specific provider. The Service does not send your login password to any of these third parties.

## 5. Data Storage and Security

- Passwords are hashed using Argon2id, a modern, memory-hard hashing algorithm designed to resist brute-force attacks.
- Session authentication uses a JSON Web Token stored in an **httpOnly cookie**, which is not readable by JavaScript running on the page — this reduces exposure to cross-site scripting (XSS) attacks.
- Document and text embeddings for retrieval are stored in a locally-hosted vector database, separate from the relational data stored in Supabase.

No method of storage or transmission is 100% secure, and we can't guarantee absolute security of your information.

## 6. Data Retention

We retain your account information and Your Content for as long as your account is active. If your account is deleted by an administrator or at your request, associated projects, collections, chats, and messages are removed from the Service's active database. Some records (such as login logs) may be retained for a limited period afterward for security and audit purposes.

## 7. Your Rights

Depending on your jurisdiction, you may have the right to access, correct, or request deletion of your personal information. To make such a request, contact **Elhammemi001@gmail.com**. Account deletion is currently handled by an administrator rather than through self-service.

## 8. Children's Privacy

The Service is not directed at children under 16, and we do not knowingly collect information from them. If you believe a child has created an account, please contact us so it can be reviewed and, if appropriate, removed.

## 9. Changes to This Policy

This Privacy Policy may be updated from time to time. Material changes will be reflected by updating the "Last updated" date above.

## 10. Contact

Questions about this Privacy Policy can be directed to **Elhammemi001@gmail.com**.

---

*This is a template drafted for a personal/portfolio project and has not been reviewed by a lawyer. If this application is ever used commercially, at scale, or with real user data subject to regulations like GDPR or CCPA, have this policy reviewed by a qualified attorney or privacy professional before relying on it.*
`

function Privacy() {
  return <LegalPage title="Privacy Policy" lastUpdated="July 27, 2026" content={CONTENT} />
}

export default Privacy