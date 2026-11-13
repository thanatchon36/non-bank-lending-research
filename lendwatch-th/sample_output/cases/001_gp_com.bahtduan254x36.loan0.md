# Case file: รวยฉับ Loan 63

> Automated triage output for human review. Not a finding of illegality.
> Verify every item against the stored snapshot before any action.

- Artefact: `gp:com.bahtduan254x36.loan0` (google_play)
- URL: https://play.google.com/store/apps/details?id=com.bahtduan254x36.loan0
- Developer / seller: Bahtduan Tech Studio 7
- Operator cluster: `OP-e8d0a64aa5` (5 artefacts)
- Licence match: unmatched
- Risk score: 100 (high)

## Red flags
- offers credit, no licence match (+25)
- annualised rate ~782% above every ceiling (+25)
- tenor from 14 days (+10)
- advertises no credit-bureau check (+8)
- no documents needed (+3)
- instant approval (+2)
- contact via messaging app (+5)
- lending app outside Finance category (+5)
- developer uses free e-mail (+4)
- no privacy policy (+5)
- sensitive permissions: call_log;sms;media_storage (+15)
- 9% of reviews report harm (+15)
- operator controls 5 artefacts (+10)

## Parsed terms (verify against snapshot)
- Highest annualised rate parsed: about 782% (simple annualisation)
- Rate text:  ระยะเวลากู้ 14 วัน ค่าบริการ 30% แอดไลน์ @bahtdu
- Tenor (days): 14 to 14
- Sensitive permissions: call_log;sms;media_storage
- Reviews reporting harm: 8.7% of 46

## Legal hooks to consider
- Lending as a business without a licence (Revolutionary Council Announcement No. 58; MOF notifications)
- Act Prohibiting Excessive Interest B.E. 2560
- App-store personal-loan policies (60-day rule)
- Personal Data Protection Act B.E. 2562; app-store permission rules
- Debt Collection Act B.E. 2558; PDPA; Criminal Code (threats, defamation)

## Evidence integrity
- Collected at (UTC): 2026-11-01T00:00:00Z
- Snapshot file: raw/gp_com.bahtduan254x36.loan0_2026-11-01T00_00_00Z_cdfb410d.json
- SHA-256: `cdfb410d22b0c098e26f033f8819679a16ccc0ac1c640bfbbf3f2aa07666fcd2`
