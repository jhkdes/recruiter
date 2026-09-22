# Participant Recruiting Agent Scope and Definitions

## Purpose

This document defines the first product scope for a participant recruiting agent named Riley. Riley helps an internal Discover First researcher recruit suitable professionals for research conversations. The first version is an approval-first assistant: it researches candidates, explains its recommendations, prepares outreach, and takes only the actions the reviewer has approved. The reviewer may later grant broader approval within defined limits.

The first business outcome is a completed introductory conversation between a qualified participant and a live human researcher. It is not an automated interview system in this phase.

## Product user and sender

The initial product user is a single internal Discover First researcher. The product should be designed so that it can later support external customers, without expanding this MVP's operating scope.

Riley is a recruiting and interview specialist at Discover First. It sends from `riley@discoverfirst.co`; its role is to recruit interview participants, arrange live conversations, and conduct discovery and feedback interviews with participants. Its messages must accurately identify Discover First and provide a link that lets recipients verify the sender's identity.

## Campaign input

A **campaign** is one bounded effort to recruit people for a research objective. A campaign begins with a **study brief**. The MVP study brief includes:

- Research goal and topic
- Interview format: introductory live call with a human researcher
- Target number of completed conversations
- Campaign duration and deadline
- Target participant criteria
- Expected call duration
- Calendly scheduling link
- Public sender-identity link
- Any campaign-specific exclusions or messaging guidance

Target participant criteria initially include industry, job title, seniority, and U.S. region. The schema must allow additional criteria later.

Each campaign defines its own success target in the form: **X completed participant conversations within Y days**.

## Definitions

| Term | Definition for the MVP |
|---|---|
| Candidate | A person surfaced through approved web research or an uploaded candidate list. |
| Uploaded candidate | A candidate supplied by the reviewer, for example through a LinkedIn profile URL. |
| Candidate source | The method and source URL through which a candidate was found. |
| Professional credential | The name, employer, role, industry, seniority, region, or equivalent work-related information displayed on a qualifying public source. |
| Verified candidate | A candidate whose identity and relevant professional credentials are supported by a LinkedIn profile URL. A publication URL or webinar link that visibly associates the person with their credential is an acceptable fallback. |
| Qualified candidate | A verified candidate who satisfies the campaign's target participant criteria. |
| High-propensity candidate | A qualified candidate with public professional evidence suggesting they may be open to research conversations, such as panel participation, published writing, webinars, video interviews, or relevant public technical activity. This is a ranking signal, not a qualification criterion. |
| Transition signal | Public professional evidence that a candidate may be between roles or otherwise in a job transition. This may influence ranking when relevant but must not replace qualification evidence. |
| Contactable candidate | A qualified candidate with a professional email address obtained and verified through the approved discovery and enrichment flow, ready for reviewer consideration. |
| Outreach plan | Riley's proposed set of candidate actions, including evidence, recommended priority, draft messages, follow-up schedule, and expected outcomes. |
| Individual-send approval | Reviewer approval required for each email before Riley sends it. This is the default autonomy level. |
| Approval level | The scope of action the reviewer has authorized Riley to execute without another review. Examples include individual sends, a named batch, or a daily send plan. |
| Autonomy level | The configured approval level plus the policies and limits that constrain Riley's actions. Autonomy does not permit Riley to bypass campaign policy. |
| Exception | A case Riley cannot resolve within policy, including missing or conflicting qualification evidence, uncertainty about contact-data eligibility, candidate requests outside approved information, complaints, opt-outs, privacy questions, legal threats, or unrelated messages. |
| Unresponsive candidate | A contactable candidate who has received the defined outreach sequence without a meaningful reply. |
| Recruiting conversion | A qualified candidate agrees to and schedules a live introductory call with the human researcher. |
| Completed participant conversation | A scheduled live call that takes place and is joined by the participant. The human researcher records whether it occurred. |
| Not interested | A candidate response declining the current invitation or indicating that they do not wish to participate. The response and timestamp are retained. |
| Recontact cooldown | The minimum period after an opt-out or not-interested response before Riley may propose another invitation. For the MVP, it is six months. |

## Candidate discovery and evidence

Riley may research candidates through web search and uploaded candidate lists. The initial repeatable discovery method searches for public LinkedIn profiles using campaign criteria such as job title, region, industry, and seniority. It may use other approved discovery methods later, provided their provenance and permitted use are recorded.

For every recommended candidate, Riley must present the reviewer with:

- Name and relevant professional credentials
- Verification URL or URLs
- Candidate-source method and source URL
- Evidence for each campaign criterion
- Reasons for the qualification and priority recommendation
- Public engagement or transition signals, clearly identified as ranking signals
- Email-address source, enrichment provider, confidence, and verification status

If LinkedIn, publication, or webinar evidence cannot verify the person's identity and relevant credentials, Riley must create an exception for reviewer decision. It must not infer missing industry, seniority, title, or region.

For the MVP, the contact-discovery flow is: identify a candidate through web research or an uploaded list; establish name, title, company, and LinkedIn URL; determine the company domain; retrieve a professional email address through Hunter Email Finder; if that fails, try Apollo People Enrichment; then verify the address and store the source, confidence, and verification status. Riley focuses on professional or company email addresses and does not seek private personal addresses. Contact-data eligibility review is out of scope for this first U.S.-focused phase.

The MVP does not include automated age verification. Candidate discovery is intended for adults represented in public professional contexts; cases suggesting another audience must be routed for review.

## Outreach scope

Email is the only outreach channel in the MVP. Riley sends candidate-approved email from `riley@discoverfirst.co`.

The initial email should use a friendly, business-focused tone and include:

- The research topic
- Why the individual was selected
- What the individual may gain from participating, without a monetary incentive
- Expected call duration
- A link to verify the sender's identity
- A Calendly link to schedule a call with the human researcher to learn more
- A clear method to decline or opt out

Riley should never make claims it cannot substantiate. Campaign messaging must avoid references to politics, race, ethnicity, gender, age, disability, sexual orientation, or sexually explicit material. Riley must not infer or use protected characteristics when discovering, qualifying, ranking, or contacting candidates.

Riley must classify clear messages such as "I'm not interested," "please take me off the list," and "no thanks" as not-interested or opt-out responses, as appropriate. It must also escalate clearly frustrated or emotional responses to the reviewer and stop the active outreach sequence. The system should support this intent-based handling rather than relying on a fixed, exhaustive list of phrases.

The approved outreach cadence is:

| Message | Timing from original email | Purpose |
|---|---:|---|
| Initial email | Day 0 | Introduce the research opportunity and provide the Calendly link. |
| First reminder | 3 business days | Brief, relevant follow-up. |
| Second reminder | 7 business days | Brief, relevant follow-up. |
| Final reminder | 14 business days | Final respectful invitation. |

After the final reminder, Riley marks the candidate as unresponsive and stops outreach for that campaign. A reply, decline, opt-out, bounce, scheduled call, or completed conversation stops the remaining sequence as applicable.

When a candidate replies with an opt-out or not-interested message, Riley records the response classification and timestamp, stops the active outreach sequence, and applies a six-month recontact cooldown. Once the cooldown has elapsed, Riley may propose a new invitation using a materially different message for reviewer approval. It may not recontact the candidate before then.

## Review and execution model

Riley must first present an outreach plan to the reviewer. At the default autonomy level, it may send each email only after individual-send approval.

As confidence grows, the reviewer may explicitly authorize broader approval levels, such as a named candidate batch or a daily send plan. Every approval must have a defined campaign, candidates or action set, maximum sends, and expiration or review point. Riley may recommend actions at any time, but it may execute only actions covered by an active approval and all deterministic policy checks.

The reviewer interface is a simple web page listing all pending actions, candidate evidence, exception cases, proposed messages, scheduled calls, and past calls. If pending actions exist, it sends the human reviewer an email alert every six hours asking them to review and approve them.

The detailed reviewer-page design remains an implementation workstream. The MVP must at minimum support the review and approval flow defined here; its information architecture, interaction design, and visual treatment will be designed separately.

Riley must notify the reviewer and pause the affected candidate when it encounters an exception. At every approval level, the following require reviewer handling:

- Missing or conflicting qualification evidence
- Uncertain contact-data eligibility
- Incentive or compensation negotiation
- Questions about personal data, privacy, or data deletion
- Complaints, legal threats, or opt-outs
- Unusual, sensitive, adversarial, or unrelated replies
- Any request or promise outside approved campaign information

## Candidate lifecycle

The MVP uses these business states:

```text
DISCOVERED
-> VERIFIED
-> QUALIFIED
-> CONTACTABLE
-> PROPOSED_FOR_REVIEW
-> APPROVED_FOR_OUTREACH
-> CONTACTED
-> RESPONDED
-> INTERESTED
-> CALL_SCHEDULED
-> CALL_COMPLETED
```

Alternate or terminal outcomes are:

```text
NOT_QUALIFIED
REVIEW_REQUIRED
DECLINED
OPTED_OUT
BOUNCED
UNRESPONSIVE
CAMPAIGN_CLOSED
```

`OPTED_OUT` and `DECLINED` retain the response and timestamp and enter the six-month recontact cooldown. `UNRESPONSIVE` ends the current campaign sequence without a follow-up send.

## Deterministic operating rules

The application, rather than Riley's reasoning model, must enforce the following rules:

- Do not send unless the action is within an active reviewer approval.
- Do not send to a candidate with a bounce, an unexpired recontact cooldown, another terminal state, or campaign closure.
- Do not recontact an opted-out or not-interested candidate until the six-month cooldown has elapsed and a new, materially different message has been approved.
- Do not exceed the outreach sequence or its business-day timing.
- Do not contact candidates with unresolved verification or contact-data exceptions.
- Record the evidence, proposed action, approval, message version, send result, reply, scheduling event, and final outcome.
- Prevent duplicate sends and duplicate processing of email, calendar, or webhook events.
- Give the reviewer a way to pause a candidate or an entire campaign immediately.
- Allow the human researcher to mark each scheduled call as completed or not completed from the reviewer web page.
- Allow the human researcher to add a short commentary to each call and mark the participant as suitable or not suitable.
- Retain campaign, candidate, communication, scheduling, and call records indefinitely.

## MVP included scope

- Internal individual researcher workflow
- Campaign study brief and target-criteria definition
- Web research and uploaded candidate-list intake
- Public professional evidence collection and reviewer presentation
- Candidate qualification and priority recommendations
- Email-only, approval-first outreach from Riley
- Calendly link for scheduling a live conversation with the human researcher
- Configurable Calendly integration with 30-minute booking slots for the human reviewer
- Defined reminder sequence and unresponsive handling
- Exception notification and reviewer queue
- Reviewer web page and six-hour pending-action email alerts
- Human call-completion recording through the reviewer web page
- Human call commentary and suitability assessment through the reviewer web page
- Tracking of candidate, outreach, scheduling, and completed-conversation outcomes
- Per-campaign success target of X completed conversations within Y days

## Deferred scope

- External customer access and multi-tenant administration
- SMS, WhatsApp, social messaging, and other channels
- Monetary incentives
- Automated age verification
- Autonomous action outside reviewer-approved bounds
- Automated adjudication of incomplete or uncertain qualification evidence
- Automated handling of sensitive, legal, privacy, or complaint replies
- Automated interview conduct or assessment
- Meeting transcription-agent integration
- Self-modifying prompts, policies, or outreach strategy

## Decisions still needed before implementation

## Configuration and future design work

- Riley references `discoverfirst.co` as its public sender-identity page. Discover First needs a dedicated page describing its interview-recruiting work and services before outreach begins.
- The Calendly link is a configurable environment variable. Calendly owns cancellation and rescheduling behavior.
- The reviewer web page requires a dedicated design pass to define its fields, approval controls, activity grouping, exceptions, and overdue-action behavior.
