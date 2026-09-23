# Participant Recruiter

Milestones 0 through 3 implement campaign creation, candidate-evidence intake, deterministic qualification, fixture-backed discovery, professional-email proposals, individual email approval, sandbox delivery, and a local reviewer interface. It runs with the Python standard library. Local reviewer data is persisted in `.data/recruiter.db`; set `RECRUITER_DB_PATH` to use another SQLite file.

```powershell
python -m app.server
```

Open `http://127.0.0.1:8000`. Run tests with:

```powershell
python -m unittest discover -s tests -v
```

Run the fixture-only Milestone 2 discovery demonstration with:

```powershell
python -m app.demo_discovery
```

It adds a qualified, contactable fixture candidate to the local database. Refresh the reviewer page to see the ranked candidate and email provenance. It makes no network requests and creates no outreach.
