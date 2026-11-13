# Case file: รวยฉับ Credit 10

> Automated triage output for human review. Not a finding of illegality.
> Verify every item against the stored snapshot before any action.

- Artefact: `gp:com.bahtduan254x36.loan2` (google_play)
- URL: https://play.google.com/store/apps/details?id=com.bahtduan254x36.loan2
- Developer / seller: Bahtduan Tech Studio 64
- Operator cluster: `OP-e8d0a64aa5` (5 artefacts)
- Licence match: unmatched
- Risk score: 100 (high)

## Red flags
- offers credit, no licence match (+25)
- annualised rate ~730% above every ceiling (+25)
- tenor from 14 days (+10)
- advertises no credit-bureau check (+8)
- no documents needed (+3)
- instant approval (+2)
- lending app outside Finance category (+5)
- developer uses free e-mail (+4)
- privacy policy on free hosting (+3)
- 3% of reviews report harm (+8)
- operator controls 5 artefacts (+10)

## Parsed terms (verify against snapshot)
- Highest annualised rate parsed: about 730% (simple annualisation)
- Rate text:  ระยะเวลากู้ 14 วัน ค่าบริการ 15% ดอกเบี้ย 2% ต่อ || 14 วัน ค่าบริการ 15% ดอกเบี้ย 2% ต่อวัน
- Tenor (days): 14 to 14
- Sensitive permissions: none
- Reviews reporting harm: 3.3% of 30

## Legal hooks to consider
- Lending as a business without a licence (Revolutionary Council Announcement No. 58; MOF notifications)
- Act Prohibiting Excessive Interest B.E. 2560
- App-store personal-loan policies (60-day rule)
- Debt Collection Act B.E. 2558; PDPA; Criminal Code (threats, defamation)

## Evidence integrity
- Collected at (UTC): 2026-11-01T00:00:00Z
- Snapshot file: raw/gp_com.bahtduan254x36.loan2_2026-11-01T00_00_00Z_8534d23c.json
- SHA-256: `8534d23c99849040c09747019f293c0bd1971b92aa68a380d2cf78546f1e8f88`
