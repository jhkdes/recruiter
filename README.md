# Participant Recruiter

Milestones 0 and 1 implement campaign creation, candidate-evidence intake, deterministic qualification, lifecycle policy, a local durable repository, provider ports/fakes, and a minimal reviewer interface. It runs with the Python standard library. Local reviewer data is persisted in `.data/recruiter.db`; set `RECRUITER_DB_PATH` to use another SQLite file.

```powershell
python -m app.server
```

Open `http://127.0.0.1:8000`. Run tests with:

```powershell
python -m unittest discover -s tests -v
```
