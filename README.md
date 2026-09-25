# MATHutrice

LLM-based tutor that helps EPF first-year students practise mathematical tools through notions, competences and training.

Students sign in, pick a notion (for example, trigonometry), see their progress on each competence, and train on exercises generated and corrected by an LLM. A chat answers their questions. Teachers upload course documents.

The application is a FastAPI server with Jinja2 templates, in the `mathutrice` package. The vocabulary used here and in the code is defined in [`CONTEXT.md`](CONTEXT.md), and design decisions are recorded in [`docs/adr/`](docs/adr/).

## Run it locally

You need:

- [uv](https://docs.astral.sh/uv/). It installs the Python version pinned in `.python-version` (3.14.7) and the dependency versions locked in `uv.lock`. Plain `pip` in a Python 3.14 virtual environment works too.
- A key for an **LLM endpoint**. The default endpoint is Mistral: get a key at <https://console.mistral.ai> (a free account works).

No Microsoft Entra credentials and no database server are needed: a local clone signs in with the **connexion de développement** and stores its data in a SQLite file.

In short, from a clone of the `course-2026` branch:

```sh
uv sync
cp .env.example .env    # then set LLM_API_KEY in .env
uv run uvicorn mathutrice.app:app --port 8000
```

At startup, the application seeds the database: it inserts the notions and competences of the referentiel, which modules and training need, and brings an existing database in line with the referentiel, keeping existing identifiers. With `AUTH_MODE=dev`, it also creates one user per role (Student, Teacher, Admin) if they are missing, so `/dev/login` lists ready-made users to sign in as. Signing in as any other address still works.

Then open <http://localhost:8000/>. The other values in `.env.example` work as they are for a local clone. That file also lists and explains every variable the application reads. The application fails to start if a required one is missing.

The [smoke test](docs/smoke-test.md) gives the exact commands, what to expect at each step, and how to check that the clone works end to end. Follow it for a first run.

## Sign-in

`AUTH_MODE` chooses how users sign in:

- **`entra`** (the default when `AUTH_MODE` is unset): sign-in through Microsoft Entra ID. It needs `CLIENT_ID`, `CLIENT_SECRET` and `TENANT_ID`, plus `REDIRECT_URL` (the `/auth` callback registered in Entra) and `POST_LOGOUT_REDIRECT_URL` (where Entra sends users after logout). Session cookies are only sent over HTTPS.
- **`dev`**: the **connexion de développement**. There is no identity provider: you pick an email address and a role (Student, Teacher or Admin) and are signed in as that user, with no proof of identity. Use it on local clones and non-Entra environments, and never in production.

Only addresses ending in `@epfedu.fr` or `@epf.fr` can sign in, in either mode.

### Connexion de développement

With `AUTH_MODE=dev`, the application prints a `WARNING: AUTH_MODE=dev` line at startup and shows a red banner on the application's pages. `/dev/login` lists existing users by role and lets you sign in as any of them, or as a new address.

If `DEV_LOGIN_KEY` is set, `/dev/login` requires it, and a wrong or missing key gets a `401`. That key only stops people from using the sign-in form. It does not protect sessions:

> **`SESSION_SECRET` must be a random secret on any environment others can reach.** Session cookies are signed with it. While it keeps the placeholder value from `.env.example`, anyone can forge a session cookie for any user and role without going through `/dev/login`, so `DEV_LOGIN_KEY` is skipped entirely. Generate a secret with:
>
> ```sh
> python -c "import secrets; print(secrets.token_urlsafe(32))"
> ```

#### Scripted sign-in

`POST /dev/login` takes a form with these fields:

- `email` (required)
- `role`: `student`, `teacher` or `admin`. Omit it to keep an existing user's role, or to create a new user as Student.
- `name` (optional)
- `key` (only when `DEV_LOGIN_KEY` is set)

It answers with a `303` redirect and sets the session cookie. Store the cookie in a cookie jar with `-c`, then send it with `-b` on the requests that follow. Replace `<key>` with the value of `DEV_LOGIN_KEY` from `.env`, or drop `-d key=<key>` when it is empty:

```sh
curl -s -c cookies.txt -o /dev/null \
  -d email=alice.martin@epfedu.fr -d role=student -d key=<key> \
  http://localhost:8000/dev/login

curl -s -b cookies.txt http://localhost:8000/
```

The session lasts one hour.

## Deployment checklist

Before a deployment is reachable by real users:

- [ ] `AUTH_MODE` unset or `entra`.
- [ ] `CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`, `REDIRECT_URL` and `POST_LOGOUT_REDIRECT_URL` set for that environment.
- [ ] `SESSION_SECRET` set to a random secret, not the `.env.example` placeholder.
- [ ] `DEV_LOGIN_KEY` unset. It is ignored outside `dev` mode, and the application warns at startup if it is set.
- [ ] Served over HTTPS, because session cookies are only sent over HTTPS when `AUTH_MODE=entra`.
- [ ] `DATABASE_URL` points at PostgreSQL.
- [ ] `LLM_API_KEY` set for the **LLM endpoint**. On Mistral's free plan, turn off training on your requests (admin panel, Privacy) before using real data.

## Development

Package boundaries are machine-checked. Read [`mathutrice/README.md`](mathutrice/README.md), which also gives the commands that run the check, before adding a package or importing across one.

Run the tests with:

```sh
uv run pytest
```

### Keeping a fork in sync with `course-2026`

The reference `course-2026` branch lives on [`xavxyz/MATHutrice`](https://github.com/xavxyz/MATHutrice). To rebase a fork's `course-2026` on it:

```bash
# Once: add the reference fork as a remote
git remote add xavier https://github.com/xavxyz/MATHutrice.git

# Each time: fetch and replay your commits on top of the reference branch
git fetch xavier
git switch course-2026
git rebase xavier/course-2026
# On conflict: fix the files, `git add` them, then `git rebase --continue` (or `git rebase --abort`)

# The rebase rewrites history, so the push must be forced
git push --force-with-lease origin course-2026
```

If the reference branch's history was rewritten after you based your work on it, a plain rebase replays its old commits too. Replay only your own commits instead, where `<old-base>` is the last reference commit your branch was built on (see `git log --oneline course-2026`):

```bash
git rebase --onto xavier/course-2026 <old-base> course-2026
```

If your `course-2026` has no commits of its own, reset it instead. This discards anything on it that is not on the reference branch:

```bash
git fetch xavier
git switch course-2026
git reset --hard xavier/course-2026
git push --force-with-lease origin course-2026
```

`git config rerere.enabled true` makes git remember conflict resolutions, so the same conflict is not solved twice across rebases.

## License

[MIT](LICENSE)
