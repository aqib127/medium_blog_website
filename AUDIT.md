# Code Audit — Medium Blog Website

**Reviewer:** senior engineering review, strict standard
**Scope:** whole repository — `blog_backend/` (Django 4.2 / DRF), `blog_frontend/` (React 19 / Vite), docs, deployment
**Size reviewed:** ~9,600 LOC across 105 Python and 33 JSX files
**Method:** direct line-by-line read. Every finding below carries a `file:line` citation and a verbatim quote so you can verify each one yourself. Do not take any of it on trust — go look.

---

## Verdict

You have built a real, working product with a sensible shape: the settings are split per environment, the apps are cleanly separated by domain, the API is versioned and paginated centrally, and in several places you clearly knew the correct pattern and applied it well. That is not nothing, and I have credited it specifically in the *What you got right* section — read that section, because it is the evidence that you already know how to do most of this.

But the codebase is not shippable in its current state, and I want to be blunt about why. **Any logged-in user can delete any other user's published article.** Not a draft, not their own — anyone's. That is a one-line omission (F-01), and the thing that makes it a *teaching* problem rather than a typo is that you wrote the permission class that prevents it, applied it correctly to comments, and even imported it into a third file without using it. You knew. It just wasn't checked anywhere, because nothing in this repository is checked anywhere.

That is the through-line of this audit. There are **zero tests** in ~9,600 lines of code (F-05). Not "thin coverage" — zero. And you can see the exact shape of the hole that leaves: `comments/views.py:21` raises `serializers.ValidationError` in a module that never imports `serializers`. That line has never once executed. A single test that posted a comment without an article ID would have caught it in the first second of its existence. Instead it sits in `main`, waiting to turn a 400 into a 500 in front of a real user.

There is also a gap between what the code does and what the documentation says it does — `articles_count` is documented as maintained by signals and is maintained by nothing (F-12); the frontend is documented as using CSS Modules and uses zero (F-40); the README diagrams a directory tree that does not exist (F-41). Documentation that lies is worse than absent documentation, because it stops the next person from looking.

Finally, this codebase cannot complete a clean production deploy. Two independent reasons, both at boot: an undeclared dependency (F-03) and a log directory that does not exist (F-04). It works on your machine because your machine has accumulated state that the repository does not describe.

**Bottom line:** the architecture is sound and salvageable. The engineering discipline around it is not yet there. Fix F-01 today. Then write tests, because every other class of finding in this document is downstream of not having them.

### Scorecard

| Area | Grade | One-line justification |
|---|---|---|
| Architecture & layout | **B** | Clean app separation, split settings, `core/` abstractions, central API config. Genuinely good bones. |
| Security | **F** | Broken object-level auth, forgeable JWTs on a default key, unvalidated uploads, public emails, zero rate limiting. |
| Correctness | **D** | A `NameError` on a live error path, a permanently-dead feature, counters that are never updated. |
| Data modelling | **C** | Right constraints in the right places (`unique_together` on both join tables), but counters maintained three different ways and a dead-end state machine. |
| Performance | **D** | 100+ queries to render one 20-item feed page; full article bodies shipped to render cards; unindexed full-text scans. |
| Frontend | **C-** | Correct DOMPurify usage and correct FormData handling, undermined by a refresh queue that hangs forever and no CSS scoping at all. |
| Testing | **F** | Zero. One 3-line boilerplate stub. No frontend test runner installed. |
| Docs & deployment | **D** | Cannot boot clean; docs actively contradict the code in at least four places. |

### Severity legend

| Level | Meaning |
|---|---|
| **Critical** | Exploitable now, or prevents the system from running at all. Fix before anything else. |
| **High** | Data loss, privilege escalation, silent incorrectness, or a user-facing break under normal use. |
| **Medium** | Real defect with a real cost — performance, correctness at the edges, maintainability debt that is already compounding. |
| **Low** | Craft. Individually cheap; collectively they are the difference between code that reads as professional and code that reads as a first draft. |

---

## Critical

### F-01 · CRITICAL · Any authenticated user can edit or delete anyone's article

`blog_backend/articles/views.py:13`

```py
permission_classes = [permissions.IsAuthenticatedOrReadOnly]
```

**What's wrong:** That is the only permission on `ArticleViewSet`. `IsAuthenticatedOrReadOnly` answers exactly one question — "is this person logged in?" — and for unsafe methods that is the *only* gate. It has no `has_object_permission`, so it never asks whether this particular user owns this particular article. Meanwhile `get_queryset` (`:50-58`) admits every published article, so `get_object()` cheerfully resolves a stranger's story and hands it to `update()` and `destroy()`.

Trace it concretely: I sign in as any user, send `DELETE /api/v1/articles/<your article id>/`, and your article is gone. `PATCH` with a new `body` and I have rewritten it under your byline.

**Why it matters:** This is broken object-level authorization — consistently in the OWASP Top 10, and the most common serious flaw in hand-rolled REST APIs. Authentication asks *who are you*; authorization asks *are you allowed to touch this specific row*. DRF makes them separate hooks precisely because conflating them is this easy. `IsAuthenticatedOrReadOnly` is a **view**-level permission; ownership is inherently an **object**-level question.

What makes this a lesson rather than an accident is that you already solved it. `core/permissions.py:3` defines `IsOwnerOrReadOnly` with the correct `has_object_permission`. You applied it correctly at `comments/views.py:9`. You even imported it at `users/views.py:15` and then never used it. The knowledge was present; the verification was not. Nothing told you that the one place you forgot was the one place it mattered most.

**Fix:** Add `IsOwnerOrReadOnly` to the `permission_classes` list on `ArticleViewSet`, exactly as `comments/views.py` does. Then — and this is the part that actually matters — write the test that signs in as user B and asserts a 403 on user A's article. A permission you have not tested is a permission you are hoping for. While you are there, drop the unused import at `users/views.py:15` so the next reader is not misled into thinking that view is protected.

---

### F-02 · CRITICAL · `SECRET_KEY` has an insecure default and signs your JWTs

`blog_backend/config/settings/base.py:9` and `:135`

```py
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default')
...
'SIGNING_KEY': SECRET_KEY,
```

**What's wrong:** If `SECRET_KEY` is not set in the environment, the application does not fail — it boots happily on the string `django-insecure-default`, which is now published in this repository. Because that same value is the HMAC signing key for SimpleJWT, anyone who knows it can mint a valid access token for any `user_id` they like. Full account takeover of every account, with no password and no interaction.

**Why it matters:** The rule for secrets is that a missing one must be a **loud, immediate crash**, never a default. A default converts a configuration mistake — which you would notice in thirty seconds — into a silent, total compromise that you would never notice at all. The fallback exists to make local development convenient, and it buys that convenience by making production failure invisible. That is always the wrong trade for a credential.

Note also what the coupling at `:135` means operationally: rotating `SECRET_KEY` to recover from a leak instantly invalidates every session and every signed value Django derives from it. Worth understanding before you have to do it in an emergency.

**Fix:** Read it with `os.environ['SECRET_KEY']` so a missing value raises at import and the process refuses to start. Give development its own key via the `.env` file that is already wired up, and use a distinct `SIGNING_KEY` for JWTs so rotating one does not force-rotate the other. Then rotate the current key — it is in git history, so treat it as compromised.

---

### F-03 · CRITICAL · Undeclared dependency — production cannot boot

`blog_backend/chatbot/views.py:11`

```py
import anthropic
```

**What's wrong:** `anthropic` appears in **no** requirements file. I checked all of them — `requirements.txt` resolves to `requirements/production.txt`, which resolves to `requirements/base.txt`, and none mentions it. This is not a lazy import buried inside a function either: it is at module scope, and `config/urls.py:23` includes the chatbot URLs, so Django imports this module during startup. A clean `pip install -r requirements.txt` followed by `python manage.py migrate` raises `ModuleNotFoundError`, and the entire API — not just the chatbot — fails to start.

It runs on your machine because at some point you ran `pip install anthropic` in your venv and never wrote it down.

**Why it matters:** The virtualenv is not the manifest. The requirements file is a contract stating "these are the things this code needs in order to exist", and the moment it drifts from reality the project is only reproducible on the one machine that happens to have the missing piece. This is the single most common way a project that "works fine" fails its first real deploy.

**Fix:** Add `anthropic` to `requirements/base.txt` with a pinned version, matching the style of every other line there. Then adopt the habit that kills this class of bug permanently: before committing a new import, install from the requirements file into a *fresh, empty* virtualenv and confirm the app still starts. Anything that survives only in your local venv is a bug you have not noticed yet. (`faker` has the identical problem — see F-42.)

---

### F-04 · CRITICAL · Logging config crashes a fresh deploy

`blog_backend/config/settings/base.py:164-168`

```py
'file': {
    'class': 'logging.FileHandler',
    'filename': BASE_DIR / 'logs' / 'django.log',
    'formatter': 'verbose',
},
```

**What's wrong:** `FileHandler` opens its file eagerly when logging is configured, and it does not create missing parent directories. `logs/` is in `.gitignore`, so it does not exist in a clean checkout, and `start.sh` never creates it. `production.py` does not override `LOGGING` — only `development.py:18` does, and that one narrows the handlers to console, which is exactly why you have never hit this locally.

So: fresh clone, install, run, and Django dies configuring its logger. This is your *second* independent boot-blocker, and it is hidden behind the first one (F-03) — you will fix `anthropic` and walk straight into this.

**Why it matters:** Two boot-blocking defects in one repository is a signal, not a coincidence: nothing in your workflow ever exercises a clean environment. Everything is validated against a developer machine that has accumulated directories, packages and environment variables the repository does not describe.

Separately, the handler is wrong for the target even once the directory exists. `start.sh` runs gunicorn, almost certainly in a container, where the filesystem is ephemeral — so these logs vanish on every redeploy, and three worker processes interleave writes into one unrotated file that grows until it fills the disk.

**Fix:** In containers, log to stdout and let the platform collect it — which is what `development.py:18` already does, so make production do the same and delete the file handler. If you genuinely need file logging somewhere, create the directory in `start.sh` before the server starts and use a rotating handler with a size cap. Either way, prove it by booting from a clean checkout.

---

### F-05 · CRITICAL · There are no tests

`blog_backend/chatbot/tests.py` — the only test file in the repository, quoted in full:

```py
from django.test import TestCase

# Create your tests here.
```

**What's wrong:** Three lines of untouched Django boilerplate, covering ~9,600 lines of application code across nine backend apps and thirty-three React components. The frontend has no test runner in `package.json` at all — no vitest, no jest, no testing-library. There is nothing to run.

Meanwhile `blog_backend/CLAUDE.md` states that backend tests live in per-app test modules and are run with `manage.py test` — describing a convention that has never existed.

**Why it matters:** I am ranking this Critical rather than filing it as debt, because you can read its consequences directly in the rest of this document. F-15 is a `NameError` on a live error path — that line has provably never executed. F-31 is an entire feature (chatbot bookmarks and comments) that cannot work under any circumstances, shipped anyway. F-12 is a counter that is never incremented, so every profile shows zero stories forever. F-01 is a permission you knew how to write and forgot in one place.

Not one of those is a hard bug. Every single one dies to the most basic possible test. They survived because nothing ever asked the code a question.

The deeper cost is that you cannot safely change anything. Every fix in this document is a change, and right now you have no way to know whether a change broke something else — which makes the rational move "touch as little as possible", and that is precisely how a codebase ossifies.

**Fix:** Do not attempt full coverage; you will bounce off it and stop. Start with the tests that pin down the findings here: authorization (user B cannot mutate user A's article), authentication (register, login, refresh), and the counter behaviours. Use DRF's `APITestCase` with a small user factory. On the frontend add `vitest` plus React Testing Library and start with `apiClient`'s refresh logic (F-11), because that is pure logic and its current bug is invisible to manual clicking. Then wire `manage.py test` and `npm test` into CI on every push, so the suite cannot quietly rot back to zero.

---

### F-06 · CRITICAL · The chatbot is open to the internet, unthrottled, and spends money

`blog_backend/chatbot/views.py:412-413`

```py
permission_classes = [AllowAny]
authentication_classes = []
```

**What's wrong:** No authentication, no permission, and — I searched the whole backend — no throttling configured anywhere at all (`base.py:105-124` sets neither `DEFAULT_THROTTLE_CLASSES` nor `DEFAULT_THROTTLE_RATES`). Every request can trigger *two* calls to the Anthropic API, at `:454` and `:499`, each with `max_tokens=4096`. The caller also supplies the conversation history that gets replayed into the prompt (F-29), so they control the input token count too.

A trivial script looping against `/api/v1/chatbot/` bills you until your account limit stops it. There is no per-user attribution, because there are no users — so you cannot even identify who did it.

**Why it matters:** Any endpoint that costs money per call is financially exploitable and should be treated as a payment surface, not a feature. This is cost-denial-of-service, and it is a favourite precisely because it does not look like an attack in your logs — just enthusiastic traffic. The total absence of throttling also makes this bigger than a chatbot problem: your login endpoint will equally accept unlimited password guesses (F-14).

**Fix:** Require authentication here — the tool set is user-scoped anyway, which is the entire point of F-31. Add DRF throttling globally in `REST_FRAMEWORK`, with a strict scoped rate for this endpoint specifically, and cap the accepted history length. Then set a hard spend limit on the Anthropic key itself: rate limiting is your first line of defence, and the billing cap is the one that actually bounds the damage when the first line fails.

---

## High

### F-07 · HIGH · Mass assignment lets any author seize the homepage

`blog_backend/articles/serializers.py:86-88`

```py
fields = (
    'id', 'author', 'title', 'dek', 'body', 'status',
    'published_at', 'scheduled_for', 'featured', 'cover_color',
    'folio', 'read_mins', 'tag_ids', 'tags', 'image',
```

**What's wrong:** `featured`, `published_at`, `status`, `folio` and `read_mins` are all client-writable on the create/update serializer. Only `author` and the counters are locked (`:91`). So:

- `PATCH {"featured": true}` on my own article, and `articles/views.py:108` — which selects the featured article by `featured=True` — now serves my article on the homepage. I have taken the editorial slot with one request.
- `published_at` is writable, so I can set it to next year and sit permanently at the top of every feed sorted by `-published_at`.
- `read_mins` is writable, overriding the value your own signal computes (`articles/signals.py:8`).

**Why it matters:** This is mass assignment. The mental model that causes it is thinking of a serializer as "the shape of my model"; the correct model is "the set of fields I am willing to let an untrusted caller write". Those are different sets, and the second is always smaller. Any field that represents *editorial privilege* (`featured`), *system-derived state* (`read_mins`, `published_at`) or *workflow position* (`status`, when it has side effects) belongs to the server, not the client.

Note that `status` is a genuine judgement call — the author does need to move a draft to published. The right shape is a dedicated action (a `publish` endpoint) that validates the transition, not a free-text field the client can set to anything.

**Fix:** Add `featured`, `published_at`, `read_mins` and `folio` to `read_only_fields`. Set `featured` from an admin-only path. Derive `published_at` server-side, which `_publish_if_needed` (`:93`) already does correctly — the writable field is actively fighting your own logic. Consider replacing the writable `status` with an explicit publish/unpublish action so the transition is validated in one place.

---

### F-08 · HIGH · Every user's email address is publicly readable

`blog_backend/users/serializers.py:14`

```py
'id', 'email', 'name', 'handle', 'bio', 'location',
```

**What's wrong:** `email` is a field on `UserSerializer`. It is listed in `read_only_fields` at `:19-22`, but **read-only is not hidden** — it still serialises on output. And `UserSerializer` backs three public endpoints: the profile (`users/views.py:63`), the followers list (`:80`) and the following list (`:92`). None of them requires authentication.

So `GET /api/v1/users/<handle>/followers/` returns the email address of every follower, to anyone, unauthenticated. One request against a popular account harvests the mailing list.

**Why it matters:** Two distinct lessons here. First, `read_only_fields` controls *writability*, not *visibility* — a very common misreading, and worth fixing in your mental model permanently. Second, and more general: one serializer cannot serve both "me looking at myself" and "a stranger looking at me", because those have different correct field sets. The moment you reuse a serializer across trust boundaries, the widest audience gets the most generous field list.

This is also the kind of finding that carries legal weight. Under GDPR an email address is personal data, and publishing it without a lawful basis is a reportable problem, not just a bug.

**Fix:** Split the serializer. Keep `email` on a private one used only by `MeView` (`users/views.py:39`), and make a public serializer without it for profiles and follower lists. Then audit every other field the same way — ask of each one, "would I be comfortable if a stranger read this?" Do the same for the chatbot's `search_users` (`chatbot/utils.py:156`), which exposes user enumeration by a different route.

---

### F-09 · HIGH · Avatar upload accepts absolutely anything

`blog_backend/users/views.py:215-216`

```py
user.avatar = request.FILES['avatar']
user.save()
```

**What's wrong:** No content-type check, no extension whitelist, no size limit, no image verification. The file goes straight onto the model field and is saved.

Note the specific trap: `avatar` is an `ImageField` (`users/models.py:17`), and you might reasonably expect Django to validate it. It does not — `ImageField` validation runs during *form or serializer* validation, and Django does not call `full_clean()` on `save()`. By assigning directly to the field and calling `save()`, you have bypassed the only layer that would have checked.

Two concrete consequences. An attacker uploads an `.svg` or `.html` file; it is stored under `/media/` and served from your own origin, so opening it executes their JavaScript in your site's security context — stored XSS, which pairs badly with your JWTs being in `localStorage` (F-11 discussion). Separately, nothing caps the size, so a handful of multi-gigabyte uploads fills the disk.

**Why it matters:** File upload is one of the few places where an untrusted user writes directly into your infrastructure, so it needs positive validation — a whitelist of what is allowed, never a blacklist of what is not. And validation must live on a layer that actually runs; "the model field has a type" is not validation if nothing invokes it.

There is a third, quieter bug in the same handler: when a new avatar replaces an old one, the old file is never deleted, so orphaned images accumulate forever.

**Fix:** Route this through a serializer with an explicit `ImageField` so DRF's validation actually runs, and add checks for maximum file size and an allowed extension/content-type whitelist (`png`, `jpeg`, `webp` — not `svg`, which is executable). Verify it really decodes as an image rather than trusting the declared type. Serve user uploads from a separate domain or an object store so that even a malicious file cannot run against your origin. And delete the previous file when replacing it.

---

### F-10 · HIGH · Logout is broken, leaks internals, and is never called

`blog_backend/users/views.py:57-61`

```py
token = RefreshToken(refresh_token)
token.blacklist()
...
except Exception as e:
    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
```

**What's wrong:** Three separate defects stacked on each other.

1. `rest_framework_simplejwt.token_blacklist` is **not** in `INSTALLED_APPS` (`config/settings/base.py:13-36`). Without that app, `blacklist()` cannot work — its backing models do not exist. So logout raises every single time.
2. The bare `except Exception` catches it and returns `str(e)` — a raw internal exception message — straight to the client. That is information disclosure: you are handing an attacker your stack internals as a debugging aid.
3. The frontend never calls this endpoint at all. I searched all of `blog_frontend/src` for "logout" and found nothing; `AuthContext.jsx:87-92` just clears `localStorage`.

Related dead configuration: `base.py:132` sets `BLACKLIST_AFTER_ROTATION: True`, which is inert because `ROTATE_REFRESH_TOKENS` is `False` at `:131`.

**Why it matters:** The security consequence is that **logout does not log you out**. Clearing `localStorage` removes the token from that browser; it does nothing to the token itself, which stays valid server-side for its full 24-hour lifetime (`base.py:130`). If it was captured — shared machine, XSS, a proxy log — "signing out" gives the user a false sense of safety while the credential remains live.

The process lesson is the ordering: a broken endpoint that nobody calls means this was written, never wired up, and never exercised. That is what shipping without tests produces — code that exists but has never run.

**Fix:** Add `rest_framework_simplejwt.token_blacklist` to `INSTALLED_APPS`, run its migrations, and enable `ROTATE_REFRESH_TOKENS` so the blacklist setting you already have becomes meaningful. Have `signOut` in `AuthContext` actually call the endpoint before clearing local state. Replace `str(e)` with a fixed generic message and log the real exception server-side — clients get a stable message, you get the detail.

---

### F-11 · HIGH · The token-refresh queue never drains on failure

`blog_frontend/src/utils/apiClient.js:60-74`

```js
} else {
  // Refresh failed – clear tokens and throw error
  localStorage.removeItem('access');
  ...
  isRefreshing = false;
  throw new Error('Session expired. Please sign in again.');
}
```

**What's wrong:** When a refresh succeeds, `onTokenRefreshed()` is called at `:53` and every queued request is released. When a refresh **fails** — either branch, `:60-67` or the catch at `:68-74` — the tokens are cleared, `isRefreshing` is reset, and the error is thrown. But `onTokenRefreshed()` is never called, and neither is any rejection path.

So every concurrent request parked in `refreshSubscribers` at `:77-95` is left holding a promise that will **never settle**. Not resolved, not rejected — permanently pending.

The user-visible symptom: session expires while three requests are in flight; one shows the error, and the other two components spin forever with no error and no timeout. It is intermittent, load-dependent, and essentially impossible to reproduce by clicking — which is why it is still here. `blog_frontend/CLAUDE.md:9` advertises this queue as a feature.

**Why it matters:** Any time you build a queue, the invariant is that **every path out of the critical section must drain it** — success, failure, and exception alike. The success path is the one you write first and test by hand; the failure path is the one that hangs. This is the standard shape of the bug, and the standard fix is to drain in a `finally`, not in the happy branch.

Two related weaknesses in the same file: `isRefreshing = false` is set at `:52` *before* the retry fires at `:55`, so a second 401 during the retry can start an overlapping refresh; and there is no request timeout anywhere, so a hung network request also never settles.

**Fix:** Give subscribers both a resolve and a reject path, and notify them from a `finally` so the queue drains no matter how the refresh ends — on failure, reject every waiter with the session-expired error so the UI can react. Move the `isRefreshing` reset to after the retry completes. Add an `AbortController` timeout so no request can hang indefinitely. This logic is pure and synchronous in shape: it is the ideal first unit test for the frontend.

---

### F-12 · HIGH · `articles_count` is never updated

`blog_backend/articles/signals.py` — the file in full:

```py
@receiver(pre_save, sender=Article)
def calculate_read_mins(sender, instance, **kwargs):
    word_count = len(instance.body.split())
    instance.read_mins = max(1, round(word_count / 200))
```

**What's wrong:** That is the only signal in the articles app, and `users/signals.py` has no handler for `articles_count` either. Nothing anywhere in the application increments or decrements it — the sole place it is ever written is `core/management/commands/populate_db.py:367`, in the seed script.

Consequence: on a real deployment, every user publishes articles and their profile permanently reports **0 stories**. It looks correct in development only because the seeder back-filled it once.

And `blog_backend/users/CLAUDE.md` states plainly that article creation updates this counter "via signals (see `users/signals.py`)". The documentation describes code that does not exist.

**Why it matters:** Denormalised counters are a performance optimisation that trades correctness for speed, and the entire trade depends on maintaining them rigorously. An unmaintained counter is strictly worse than no counter: you have paid the write-path complexity cost and still display a wrong number, confidently.

This repository currently maintains counters **three different ways**: correctly with `F()` in `comments/signals.py`, incorrectly with read-modify-write in `users/signals.py` (F-13), by recount-in-the-view in `articles/views.py:148`, and not at all here. One problem, four strategies. Pick one.

**Fix:** Add `post_save` and `post_delete` receivers for `Article` that adjust `author.articles_count` with `F()` expressions, modelled exactly on `comments/signals.py:6-19`, which already does this properly. Decide explicitly whether the count means "published articles" or "all articles", because publishing a draft changes the answer and a status transition must then adjust it too. Write a management command that recomputes all counters from source rows, both to repair existing drift and to give you a way to verify the signals are correct.

---

### F-13 · HIGH · Follow counters race and can crash on unfollow

`blog_backend/users/signals.py:13-16`

```py
instance.follower.following_count += 1
instance.follower.save(update_fields=['following_count'])
instance.followed.followers_count += 1
instance.followed.save(update_fields=['followers_count'])
```

**What's wrong:** This is read-modify-write in Python. The current value is read into memory, incremented by the application, then written back. Two concurrent follows of the same user both read `5`, both compute `6`, and both write `6`. One follow is silently lost. The `pre_delete` handler at `:20-23` has the same shape in reverse.

There is a nastier second-order effect. These are `PositiveIntegerField`s, which carry a database check constraint of `>= 0`. Once drift has pushed a counter to `0` while a `Follow` row still exists, the next unfollow attempts `0 - 1`, violates the constraint, and the request 500s. So the race does not merely produce a wrong number — it eventually produces an endpoint that is broken for that user until someone repairs the row by hand.

**Why it matters:** The principle is that a counter update must be a **single atomic database statement**, not a read followed by a write, because anything between those two operations is a window another process can slip through. `F()` expressions exist for exactly this: they push the arithmetic into SQL as `count = count + 1`, which the database applies atomically.

You already know this. `comments/signals.py:10-12` does it correctly, in this same repository, for the same class of problem. That is what makes this worth internalising rather than just patching: the gap is not knowledge, it is consistency.

**Fix:** Rewrite both handlers to use `F()` expressions applied via a queryset `update()`, exactly as `comments/signals.py` does. Note that after an `F()` update the in-memory instance holds a stale value, so refresh it from the database if you need to read it afterwards. Longer term, consider whether these counters are worth denormalising at all — a `COUNT` over an indexed foreign key is fast, and correct by construction.

---

### F-14 · HIGH · No rate limiting anywhere, including on login

`blog_backend/config/settings/base.py:105-124` — the whole `REST_FRAMEWORK` block, with no throttle keys:

```py
'DEFAULT_PERMISSION_CLASSES': (
    'rest_framework.permissions.IsAuthenticatedOrReadOnly',
),
```

**What's wrong:** Neither `DEFAULT_THROTTLE_CLASSES` nor `DEFAULT_THROTTLE_RATES` is configured, and no view sets a throttle of its own. I grepped the entire backend for `THROTTLE`: nothing.

The sharpest consequence is `/api/v1/auth/login/`, which will accept unlimited password attempts from a single IP at whatever rate the attacker can manage. Your password validators (`base.py:80-85`) raise the cost of a *guess*, but nothing bounds the *number* of guesses. Registration is equally unbounded, so an attacker can also mass-create accounts, and the chatbot (F-06) turns unbounded requests directly into unbounded money.

**Why it matters:** Rate limiting is not a hardening nicety, it is a load-bearing control for any endpoint where repetition is itself the attack — credential stuffing, enumeration, resource exhaustion, cost amplification. Validation controls what a single request may contain; throttling controls how many requests may exist. You need both, and you currently have only the first.

**Fix:** Configure DRF's `AnonRateThrottle` and `UserRateThrottle` globally with sane defaults, then add a `ScopedRateThrottle` with a much stricter rate on login, registration, password-reset and the chatbot. Throttle login by both IP and submitted username so distributed attempts against one account are caught too. Remember that throttling by IP alone is weak behind a proxy unless you have correctly configured which forwarded header to trust.

---

### F-15 · HIGH · `NameError` on a live error path

`blog_backend/comments/views.py:21`, with the imports at `:1-4`:

```py
from rest_framework import viewsets, permissions
...
        raise serializers.ValidationError({'article': 'This field is required.'})
```

**What's wrong:** `serializers` is never imported. Line 1 imports `viewsets` and `permissions`; line 3 imports `CommentSerializer` *from* `.serializers`, which binds `CommentSerializer` and nothing else. There is no name `serializers` in this module's namespace.

So the moment a client posts a comment without an `article` field, Python raises `NameError: name 'serializers' is not defined`, and your careful 400-with-a-helpful-message becomes an unhandled 500.

**Why it matters:** I am calling this out at High not because the impact is severe but because of what it proves: **this line has never executed, not once, in the entire life of this project.** It is the validation branch — the first thing any test of this endpoint would hit, and the first thing a developer poking at the API by hand would trigger.

It is the cleanest possible illustration of F-05. Every other finding in this document I had to reason about. This one just needed the code to be run.

It also shows why error paths need tests specifically. Happy paths get exercised constantly by manual clicking; error paths only run when something goes wrong, which is exactly when you least want a second, unrelated failure on top.

**Fix:** Import `serializers` from `rest_framework`. Better, delete the check entirely and let the serializer own it — declare `article` as a required field on `CommentSerializer` and DRF produces the identical 400 with no view-level code at all. Validation belongs in the serializer; a view re-implementing it by hand is duplication that can drift, and here it drifted all the way to a crash.

---

### F-16 · HIGH · HTTPS redirect loop behind a proxy

`blog_backend/config/settings/production.py:5`

```py
SECURE_SSL_REDIRECT = True
```

**What's wrong:** `SECURE_SSL_REDIRECT` makes Django redirect any request it considers insecure to `https://`. Django decides that by inspecting the request it actually received. Behind a TLS-terminating proxy — which is how Railway, Heroku, Fly, and every load balancer works — the proxy handles HTTPS and forwards plain HTTP to gunicorn. Django therefore sees an insecure request, redirects to HTTPS, the proxy terminates TLS again and forwards plain HTTP again, forever. The site is unreachable, typically with `ERR_TOO_MANY_REDIRECTS`.

The missing piece is `SECURE_PROXY_SSL_HEADER`, which tells Django to trust the proxy's forwarded-protocol header. It is not set anywhere.

`CSRF_TRUSTED_ORIGINS` is also unset, which will separately break Django admin logins over HTTPS on Django 4.x.

**Why it matters:** Every security setting here is correct in isolation — `production.py:5-12` is a genuinely good hardening block (I credit it below). This is a *deployment topology* bug: settings that assume Django terminates TLS itself, running in an architecture where it does not. Whenever you put something in front of your application, you have to tell the application what is in front of it.

The corollary matters too: only trust that forwarded header when a proxy you control is guaranteed to set it. If a client can reach gunicorn directly, it can send the header itself and convince Django an insecure request was secure.

**Fix:** Set `SECURE_PROXY_SSL_HEADER` to the forwarded-protocol header your platform sets, and confirm your platform actually strips client-supplied copies of it. Add `CSRF_TRUSTED_ORIGINS` with your real production origins. Then verify against the deployed environment, not locally — this class of bug is invisible in development by definition.

---

### F-17 · HIGH · `''.split(',')` is `['']`, not `[]`

`blog_backend/config/settings/base.py:11` and `:102`

```py
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
...
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
```

**What's wrong:** The intent is clearly "default to an empty list". That is not what happens. In Python, `''.split(',')` returns `['']` — a list containing one empty string. Try it in a REPL; it surprises almost everyone once.

So with the variable unset, `ALLOWED_HOSTS` is `['']`, which matches no host, and every production request fails host validation with a 400 that reads as a mysterious platform problem. `CORS_ALLOWED_ORIGINS` becomes a list containing an invalid empty origin.

**Why it matters:** This is a small bug worth a lot of attention because of its shape: **a default that is wrong in a way that looks right.** Reading the line, "empty string, split, empty list" is the obvious inference, and it is false. The general lesson is to be suspicious of string-splitting as a configuration parser, and to be precise about what your "safe default" actually evaluates to — a default you have not verified is a guess.

There is a design point underneath it too. For production, `ALLOWED_HOSTS` should not have a permissive fallback at all; like `SECRET_KEY` (F-02), a missing value should be loud.

**Fix:** Filter out empty strings after splitting, so an unset variable yields a genuinely empty list. Better still, require the value in production and fail at startup if it is missing, since an empty `ALLOWED_HOSTS` cannot serve traffic anyway — crashing at boot with a clear message beats 400-ing every request. Strip whitespace around entries too, so a comma-space separated list works as anyone would expect.

---

### F-18 · HIGH · Uploaded images are unreachable in production

`blog_backend/config/urls.py:26-27`

```py
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**What's wrong:** Media is only routed when `DEBUG` is true. `production.py:3` sets `DEBUG = False`, and S3 storage is opt-in via `USE_S3`, defaulting to off (`production.py:14`). So in a default production deployment, avatars and article covers are written to local disk at `MEDIA_ROOT` and then served by nothing at all — every image 404s.

Worse, because `start.sh` runs gunicorn in a container, that local disk is ephemeral: uploads do not merely fail to serve, they are **destroyed on every redeploy**. Users upload an avatar, it appears to work (the POST succeeds), and it silently disappears.

**Why it matters:** Django's `static()` helper is deliberately development-only — it is documented as unsuitable for production and is a well-known footgun. The real lesson is about *user data on ephemeral infrastructure*: containers are cattle, and anything written to their local filesystem is temporary by definition. User uploads are durable data and need durable storage, the same way your rows need Postgres rather than SQLite in a container.

The S3 configuration at `production.py:14-24` is already written — it is just switched off by default, so the default deployment is the broken one.

**Fix:** Make object storage the default in production rather than opt-in, and let local disk be the development-only path. The `django-storages` and `boto3` dependencies are already in `requirements/base.txt` and the settings block already exists, so this is mostly flipping which branch is the default. Note that turning it on will expose F-34, where `.path` is used on storage that has no local path — fix that at the same time.

---

### F-19 · HIGH · The seed command can wipe production and ships a known password

`blog_backend/core/management/commands/populate_db.py:105-115` and `:162`

```py
Report.objects.all().delete()
...
User.objects.all().delete()
...
password=make_password('rootroot'),
```

**What's wrong:** Running `populate_db --clean` deletes every row from ten tables, ending with the entire user table. There is no confirmation prompt, no `--noinput`-style gate, and no check on `settings.DEBUG` or the current database. Django management commands run against whatever `DATABASE_URL` is in the environment — so a terminal with production credentials loaded, one mistyped flag, and the user table is gone.

Separately, every seeded user is created with the password `rootroot`, again with no environment guard. If this ever runs anywhere reachable, you have 120 accounts with a published password.

**Why it matters:** Destructive tooling needs a safety interlock proportional to its blast radius, and "I will be careful" is not one — the entire history of production incidents is careful people with a shell. The guard has to live in the code, because that is the only thing present at 2am when the careful person is tired and the environment is not what they assumed.

Note the asymmetry that makes this worth ranking High: the cost of adding a guard is about four lines, and the cost of not having one is unrecoverable data loss.

**Fix:** Refuse to run unless `settings.DEBUG` is true, and additionally require an interactive confirmation for `--clean` that echoes the target database name before proceeding. Generate seed passwords randomly and print them, or read one from an environment variable, so no fixed credential exists in source. As a general rule, any management command that deletes data should state what it is about to destroy and where, then make the operator confirm it.

---

## Medium

### F-20 · MEDIUM · Over 100 database queries to render one feed page

`blog_backend/articles/views.py:11`

```py
queryset = Article.objects.all().order_by('-created_at')
```

**What's wrong:** No `select_related`, no `prefetch_related`, and `ArticleSerializer` then walks a relation for every single row:

- `:27` nests `author` — one query per article
- `:28` nests `tags` — one query per article
- `:29` nests `images` — one query per article
- `:52` `get_image_url` calls `obj.tags.all()` again
- `:59` `get_is_clapped` runs `obj.claps.filter(user=user).exists()` — one query per article
- `:66` `get_is_bookmarked` runs the same against bookmarks

At the default page size of 20 that is one query for the page plus roughly six per article: **well over 100 queries** for a single feed request, most of them identical in shape and differing only by ID.

**Why it matters:** This is the N+1 problem, and it is the most common serious performance defect in ORM code. It is invisible in development — 120 fast local queries feel instant — and it degrades non-linearly in production, where each query carries real network latency and the connection pool is finite. It is also the classic cause of a site that is fine at 50 users and falls over at 500.

The two `SerializerMethodField`s deserve separate mention, because they are the subtler half. They look like cheap computed properties; each is actually a database round trip, executed per row, and no amount of `prefetch_related` on the queryset will help unless you restructure them.

**Fix:** Add `select_related('author')` for the forward foreign key and `prefetch_related('tags', 'images')` for the reverse and many-to-many relations. Replace the two per-row `exists()` checks with `Exists()` subquery annotations on the queryset so the database answers "did this user clap this?" for the whole page in one statement, and have the serializer read the annotated attribute. Then install `django-debug-toolbar` (already in `requirements/development.txt`) and watch the query count — an endpoint whose query count grows with page size is always wrong.

---

### F-21 · MEDIUM · Full article bodies are sent to render article cards

`blog_backend/articles/serializers.py:37`

```py
'id', 'author', 'title', 'dek', 'body', 'status',
```

**What's wrong:** `body` is in the read serializer, and that serializer is used for list responses. The feed renders cards showing a title, a dek and an image — but the payload contains twenty complete articles.

**Why it matters:** The list and detail views of a resource almost never want the same fields, and the field that differs is usually the big one. Every byte here is paid for three times: database read, JSON serialisation, and network transfer to a client that discards it. On mobile connections this is the difference between a feed that feels instant and one that does not.

Note the interaction with F-22: the unconditional `.distinct()` forces the database to compare every selected column, and `body` being in that set makes the comparison dramatically more expensive. Two independent decisions that compound.

**Fix:** Use a lighter list serializer without `body`, and keep the full one for retrieve — you already have the mechanism, since `get_serializer_class` (`:19-30`) switches serializers by action. Add `.defer('body')` on the list queryset so the column is not even read from the database.

---

### F-22 · MEDIUM · `.distinct()` on every list query

`blog_backend/articles/views.py:74`

```py
return queryset.distinct()
```

**What's wrong:** This runs on every list request, but it is only ever needed for the one branch that joins tags (`:72`), which can produce duplicate article rows. Every other path pays for it without benefit.

`SELECT DISTINCT` requires the database to compare **every selected column** across all rows — including the `body` TEXT column (F-21) — typically via a sort or hash of the full row. That is a real cost applied unconditionally to your busiest endpoint.

**Why it matters:** `.distinct()` is often applied as a reflex to make duplicate rows go away without diagnosing where they came from. The habit worth building is the opposite: when duplicates appear, find the join that caused them and decide whether it belongs in that query at all. Reaching for `distinct()` treats the symptom, and hides the join from the next reader.

**Fix:** Apply `.distinct()` only on the branch that filters by tag. Better, avoid the row multiplication entirely by expressing the tag filter as an `Exists()` subquery, which cannot duplicate rows and lets you drop `distinct()` altogether.

---

### F-23 · MEDIUM · Search does a full table scan of every article body

`blog_backend/articles/views.py:16`

```py
search_fields = ['title', 'dek', 'body', 'tags__name', 'author__name', 'author__handle']
```

**What's wrong:** DRF's `SearchFilter` turns these into `icontains` lookups, which compile to SQL `ILIKE '%term%'`. A leading wildcard makes a B-tree index unusable, so the database reads and case-folds every article body on every search. `tags__name` also joins, multiplying rows — which is where the duplicates that motivated F-22 come from. `chatbot/utils.py:11-13` repeats the same pattern.

**Why it matters:** `icontains` is the right tool at small scale and stops working abruptly, not gradually — it is fine for hundreds of rows and unusable at hundreds of thousands, with no warning in between. Worth knowing *why*: an index maps sorted prefixes, and a leading `%` means you have no prefix to look up, so the index cannot participate.

You are on PostgreSQL, which has proper full-text search built in — `SearchVector`, `SearchQuery` and a GIN index — and Django exposes all of it through `django.contrib.postgres.search`. You are paying for a database that solves this and not using the feature.

**Fix:** For now, drop `body` from `search_fields` and search titles, deks and tags — that alone removes the worst of the cost and is usually what users want anyway. When search matters, move to PostgreSQL full-text search with a stored `SearchVector` column kept current by a trigger or signal, and a GIN index over it. That also gives you relevance ranking, which `icontains` cannot do at all.

---

### F-24 · MEDIUM · Archiving an article destroys its publication date

`blog_backend/articles/serializers.py:105-106`

```py
elif new_status != Article.Status.PUBLISHED:
    instance.published_at = None
```

**What's wrong:** Any transition to a non-published status nulls `published_at`. That includes archiving. Archive an article you published two years ago and the original publication date is gone permanently — there is no other record of it.

The unpublish-back-to-draft case is arguably intentional. Archiving is not: archiving means "retired from view", not "never happened".

**Why it matters:** This is destroying a historical fact to represent a current state, and those are different things. `published_at` records *when this was published* — an event that occurred. Visibility is a separate concern, already fully captured by `status`. When you overload one field to mean both, you lose information that cannot be recovered, and silently.

The general rule: prefer deriving current state from recorded facts over mutating the facts to match the state. Facts are append-only; state is a view over them.

**Fix:** Only clear `published_at` when returning to `DRAFT` — an unpublished draft genuinely has no publication date. Leave it intact for `ARCHIVED`, since an archived article was published and that remains true. If you need to know when it was archived, add an `archived_at` field rather than overwriting the one you have.

---

### F-25 · MEDIUM · Authors cannot access their own archived or scheduled articles

`blog_backend/articles/views.py:55-58`

```py
queryset = queryset.filter(
    Q(status='published') |
    Q(author=self.request.user, status='draft')
)
```

**What's wrong:** The visibility filter admits exactly two states: anything published, and the caller's own drafts. But the model defines four (`articles/models.py:22-26`): `DRAFT`, `PUBLISHED`, `SCHEDULED`, `ARCHIVED`.

So an author's own archived or scheduled article is not in their queryset at all. `get_object()` cannot find it, and retrieve, update and delete all 404 — for the owner, on their own content. Once an article reaches either state it is unreachable and cannot be brought back through the API.

`SCHEDULED` is a dead end in a second sense too: nothing in this codebase ever promotes a scheduled article to published. There is no cron job, no Celery task, no management command — I looked. An article set to `scheduled` with a `scheduled_for` date will sit there forever.

`blog_backend/articles/CLAUDE.md:7` documents `status` as `(DRAFT/PUBLISHED)`, omitting both of the states that cause this.

**Why it matters:** Two lessons. First, when you add a state to an enum you have to revisit every query that filters on it — a state machine is only as good as the transitions that are actually implemented, and a state nothing can exit is a trap for your data. Second, filtering by an allowlist of statuses is right, but it must be reviewed whenever the enum grows; nothing here fails loudly when a new state is added, it just becomes invisible.

**Fix:** Decide what these states mean and implement them fully or delete them. If they stay, extend the owner branch to admit all of the author's own articles regardless of status, keeping the public branch restricted to `published`. Implement the scheduled-to-published transition as a periodic job, or drop `SCHEDULED` and `scheduled_for` until you are ready to build it. Update `articles/CLAUDE.md` to match whatever you decide.

---

### F-26 · MEDIUM · Unvalidated tag IDs produce a 500

`blog_backend/articles/serializers.py:77-79` and `:117`

```py
tag_ids = serializers.ListField(
    child=serializers.IntegerField(), required=False, write_only=True
)
...
article.tags.set(tag_ids)
```

**What's wrong:** The field validates that each entry is an integer and nothing more. Nobody checks the tags exist. Post `{"tag_ids": [999999]}` and the failure surfaces from the database layer as an unhandled exception — a 500 where the correct answer is a 400 telling the client which ID was invalid.

**Why it matters:** Validation exists to convert bad input into a clear, actionable client error at the boundary. When it does not, the error still happens — just deeper, later, in a less informative form, and logged as if your server malfunctioned rather than the client sending nonsense. That pollutes your error monitoring with problems that are not yours.

DRF has the right tool: `PrimaryKeyRelatedField` with a queryset checks existence during validation and produces a proper 400 automatically. Hand-rolling an integer list gives up that machinery.

**Fix:** Replace the `ListField` of integers with a `PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)`. It validates existence, returns clean field-level errors, and hands you real `Tag` instances. While you are there, consider a maximum tag count — nothing currently stops a client attaching every tag in the system.

---

### F-27 · MEDIUM · Clap toggle is a race with no transaction

`blog_backend/articles/views.py:139-149`

```py
clap_qs = Clap.objects.filter(user=request.user, article=article)

if clap_qs.exists():
    clap_qs.delete()
    clapped = False
else:
    Clap.objects.create(user=request.user, article=article)
    clapped = True

article.claps_count = article.claps.count()
article.save(update_fields=['claps_count'])
```

**What's wrong:** Check-then-act with no transaction and no locking. Two concurrent claps from the same user — a double-click, or a retried request — both evaluate `exists()` as false, and both call `create()`. The `unique_together` constraint on `Clap` (`articles/models.py:81`) correctly stops the duplicate row, but the resulting `IntegrityError` is unhandled, so the second request 500s.

The counter update has the same shape: recount, then write. Better than a blind increment, because it recomputes from source rather than compounding drift, but still a read followed by a separate write with a window between them.

None of it is wrapped in `transaction.atomic`, so a failure between the clap write and the counter write leaves them inconsistent.

**Why it matters:** This is time-of-check to time-of-use. Any "look, then act" sequence against shared state is racy unless the database enforces the invariant or you hold a lock. Your saving grace is the unique constraint — which is exactly why constraints belong in the database rather than in application logic. Application checks are advisory; database constraints are guarantees.

The right instinct: express the intent as a single atomic operation rather than a sequence you hope is not interrupted.

**Fix:** Use `get_or_create` and branch on the `created` flag — that pushes the check-and-insert into one atomic statement, exactly as `FollowToggleView` (`users/views.py:120`) already does correctly. Wrap the clap mutation and the counter update in `transaction.atomic` so they succeed or fail together. Consider moving counter maintenance into signals on `Clap` with `F()` expressions, so all four counters in this project finally work the same way (see F-12).

---

### F-28 · MEDIUM · Comment replies are unreachable, and the article filter can 500

`blog_backend/comments/views.py:7` and `:13-15`

```py
queryset = Comment.objects.filter(parent__isnull=True)
...
article_id = self.request.query_params.get('article')
if article_id:
    qs = qs.filter(article_id=article_id)
```

**What's wrong:** Two separate problems.

The base queryset excludes every reply. That is reasonable for the list action — you want top-level comments and their nested replies — but `get_queryset` feeds *every* action, including retrieve, update and destroy. So a user cannot edit or delete their own reply: `get_object()` filters it out and returns 404. Half the commenting feature is read-only by accident.

Second, `article_id` goes into the filter unvalidated. `?article=abc` makes Django try to adapt `'abc'` to an integer column, which raises `ValueError` and returns a 500 rather than a 400.

**Why it matters:** The first is about scope: `get_queryset` in a `ModelViewSet` is shared across all actions, so a filter that is correct for one is silently applied to the rest. When a constraint is action-specific, it belongs in that action or in `filter_queryset`, not in the base queryset.

The second is the same lesson as F-26 — untrusted input reaching the ORM without validation converts a client mistake into a server error.

**Fix:** Make the base queryset all comments, and apply the `parent__isnull=True` restriction only for the list action. Move the article filter into a proper `django-filter` `FilterSet` — the backend is already configured globally at `base.py:112-116`, so you get type coercion and clean 400s for free instead of hand-rolling query-param parsing.

---

### F-29 · MEDIUM · The client controls the entire LLM conversation

`blog_backend/chatbot/views.py:419` and `:450-451`

```py
history = data.get('history', [])
...
for msg in history:
    messages.append({"role": msg["role"], "content": msg["content"]})
```

**What's wrong:** The full conversation history arrives from the request body and is replayed into the model context with no validation at all. Three consequences:

1. `msg["role"]` and `msg["content"]` use direct key access, so a single malformed entry raises `KeyError` and returns a 500.
2. The caller can forge `assistant` turns — writing words the model never said, then asking it to continue. That is a well-known way to walk a model past its system prompt, and your system prompt at `:446` is doing real work ("Do not expose private information of other users").
3. There is no length cap, so a caller decides how many input tokens each request costs. Combined with the endpoint being unauthenticated (F-06), that is an open cost amplifier.

There is a fourth, subtler exposure: `chatbot/utils.py:36` feeds the first 500 characters of article bodies into the model as tool results. Article bodies are attacker-authored. Someone can publish an article containing instructions aimed at the model and wait for the chatbot to ingest them.

**Why it matters:** The governing principle is that a system prompt is guidance, not a security boundary. Anything reaching the model — user turns, forged assistant turns, retrieved documents — is untrusted input, and the defences that actually hold are the ones outside the model: validate structure, cap size, authenticate the caller, and scope what the tools can reach so a successful injection still cannot read data the user is not entitled to.

**Fix:** Validate `history` with a serializer — a bounded list, `role` restricted to `user` or `assistant`, `content` a string with a maximum length — and reject anything else with a 400. Cap the number of turns you replay. Treat retrieved article text as data rather than instructions by clearly delimiting it in the tool result. Most importantly, enforce authorization in the tool functions themselves, so injection cannot reach anything the caller could not already access.

---

### F-30 · MEDIUM · Failures are silently converted into fake answers

`blog_backend/chatbot/views.py:512-515`

```py
except Exception as e:
    logger.error(f"Anthropic error: {e}")
    answer = get_mock_response(message, user)
    return Response({'answer': answer, 'function_called': 'mock-fallback'})
```

**What's wrong:** Every exception — expired API key, rate limit, network failure, or a genuine bug in your own tool code — is caught and answered with a canned regex response, returned as HTTP 200.

The same pattern appears at startup. `:158-159` computes `USE_MOCK = ... or not ANTHROPIC_API_KEY` at import time, so deploying without the key silently puts the chatbot into permanent mock mode. Users get keyword-matched canned text that looks like a real assistant, indefinitely, and the only trace is one log line at boot.

**Why it matters:** This is silent degradation, and it is worse than an outage. An outage is visible and gets fixed; a system that quietly serves plausible-looking wrong answers keeps its dashboards green while users lose trust in it. Returning 200 also means no monitoring, no alert and no error-rate graph will ever show a problem.

There is a real distinction between a *fallback* and *masking*. A fallback is a deliberate degraded mode that the system knows it is in and reports. Masking is catching everything so nothing looks broken. This is masking.

**Fix:** Catch the specific exceptions you can actually handle — API errors, timeouts — and let unexpected ones propagate to DRF's handler so they are logged and surfaced as 500s. If you keep a degraded mode, signal it honestly in the response so the frontend can tell the user, and count it as a metric you alert on. Make mock mode an explicit configuration choice rather than something inferred from a missing key: absence of a required secret in production should fail loudly, exactly as in F-02.

---

### F-31 · MEDIUM · Two chatbot features can never work

`blog_backend/chatbot/views.py:413` and `:416`

```py
authentication_classes = []
...
user = request.user if request.user.is_authenticated else None
```

**What's wrong:** With `authentication_classes = []`, DRF has no authenticator to run, so `request.user` is always `AnonymousUser` regardless of what the caller sends. `is_authenticated` is therefore always false, and `user` is always `None`.

Which means `get_user_bookmarks` and `get_user_comments` (`chatbot/utils.py:84`, `:99`) can only ever return `{'error': 'Authentication required.'}`. Not sometimes — always, for everyone, including a correctly logged-in user with a valid token.

Both tools are nonetheless advertised to the model as working features at `:81` and `:86` ("Requires authentication"), so the model will confidently call them and then explain to a signed-in user that they need to sign in.

**Why it matters:** Two features were written end-to-end — tool definitions, implementations, error handling — and dispatched to production in a state where they cannot function under any input. That is only possible without tests, and it is the same root cause as F-15.

There is a specific DRF lesson too: `permission_classes` and `authentication_classes` are independent. Setting `AllowAny` does not require emptying the authenticator list, and emptying it does not merely make auth optional — it makes authentication *impossible*, discarding the credentials the client sent.

**Fix:** Remove `authentication_classes = []` so the default JWT authenticator runs and `request.user` reflects the real caller. Given F-06, the better move is to require authentication on this endpoint outright. Then test it: one test that calls the endpoint as a logged-in user and asserts the bookmarks tool returns bookmarks.

---

### F-32 · MEDIUM · Only one tool call is possible, and the response is indexed blindly

`blog_backend/chatbot/views.py:464-469`, `:499` and `:506`

```py
for block in content_blocks:
    if block.type == "tool_use":
        tool_use_block = block
        break
...
final_response = client.messages.create(
    model=model_name,
    system=system_prompt,
    messages=messages,
    max_tokens=4096,
...
final_answer = final_response.content[0].text
```

**What's wrong:** Three defects in one flow.

The loop takes the **first** `tool_use` block and stops. The follow-up call at `:499` omits the `tools` parameter entirely, so the model has no tools available on its second turn and cannot chain a lookup. Any question needing two steps — "how many articles has the author of X written?" — silently returns a partial answer.

If the model emits **parallel** tool calls in one turn, `:490` appends all the content blocks to the message history but only one `tool_result` is supplied at `:493-497`. The Messages API requires a matching result for every tool use, so the next request is rejected — and by F-30, that rejection is swallowed and returned as a canned mock answer.

Finally `:506` and `:509` both do `.content[0].text`, assuming the first block is text. Any response whose first block is not text raises `AttributeError` or `IndexError`.

**Why it matters:** A tool-use integration is a loop, not a single round trip: call the model, execute any tools it asked for, feed **all** results back, and repeat until it stops asking. Implementing only the first iteration works in demos and fails on real questions. And when you consume a structured response, find the block you want by type rather than trusting position — position is not part of the contract.

**Fix:** Restructure as a loop that continues while the response `stop_reason` indicates tool use, passing `tools` on every call, executing every `tool_use` block in the turn, and appending a `tool_result` for each — with an iteration cap so it cannot spin. Extract text by filtering blocks on type instead of indexing `[0]`. Also move the hardcoded model id at `:167` into settings; pinning a specific model version in source means changing it requires a code deploy.

---

### F-33 · MEDIUM · Handle generation races, mangles non-Latin names, and reserves nothing

`blog_backend/core/utils.py:4-14`

```py
slug = slugify(value) or 'untitled'
if not model.objects.filter(**{field: slug}).exists():
    return slug
```

**What's wrong:** Three issues.

It is check-then-insert: two concurrent registrations both find the handle free, both return it, and the second `INSERT` violates the unique constraint and 500s. The loop also issues one query per collision attempt.

`slugify()` strips non-ASCII by default, so a name written entirely in Arabic, Chinese, Cyrillic or Devanagari slugifies to an empty string and falls through to `'untitled'`. Those users become `untitled`, `untitled-1`, `untitled-2` — each collision costing another query, and none of them getting a usable handle.

There is no reserved-word list, which matters because of F-35: handles share a URL namespace with your static routes, so a user who ends up with the handle `settings` or `drafts` has a permanently unreachable profile.

**Why it matters:** The uniqueness race is the same TOCTOU shape as F-27, and the same fix applies: let the database enforce the constraint and handle the failure, rather than checking first and hoping.

The slugify issue is worth internalising separately. Defaults encode assumptions, and this one assumes ASCII names. It will pass every test written by an English-speaking developer and fail for a large fraction of real users — a failure mode that only appears once you have users unlike yourself.

**Fix:** Pass `allow_unicode=True` to `slugify` so non-Latin names produce meaningful handles. Replace check-then-return with an insert that catches `IntegrityError` and retries with a new suffix, or append a short random suffix so collisions are rare and bounded rather than sequential. Add a reserved-word list covering every static route in `App.jsx` plus the usual suspects (`admin`, `api`, `me`, `static`), and reject those at registration.

---

### F-34 · MEDIUM · `User.save()` does an extra query and deletes files mid-transaction

`blog_backend/users/models.py:37-44`

```py
if self.pk:
    try:
        old_instance = User.objects.get(pk=self.pk)
        if old_instance.avatar and old_instance.avatar != self.avatar:
            if os.path.isfile(old_instance.avatar.path):
                os.remove(old_instance.avatar.path)
```

**What's wrong:** Every save of an existing user issues an extra `SELECT` to re-read the row. That includes the two counter saves per follow (`users/signals.py:14`, `:16`), so a single follow now costs four queries instead of two — and each one also hits the filesystem with `isfile`.

More seriously, `os.remove()` is an **irreversible side effect inside a database transaction**. If the transaction rolls back after this point, the row reverts and the file is still gone. You now have a database referencing an avatar that no longer exists.

And `.path` is only implemented for local filesystem storage. It raises `NotImplementedError` on S3 — so the moment `USE_S3=True` (which F-18 recommends), **every user save breaks**, not just avatar changes. `users/views.py:198` has the same problem in the avatar-removal path.

**Why it matters:** Two principles. First, `save()` should persist state, not perform I/O against other systems; overriding it to do filesystem work means every caller pays that cost whether relevant or not, including callers that only touched an unrelated counter. Second, transactional and non-transactional operations do not mix — the database can roll back, the filesystem cannot. External side effects belong after the commit, where you know the transaction actually succeeded.

**Fix:** Move avatar cleanup out of `save()` into a `post_delete` signal for user deletion and an explicit step in the avatar-update view for replacement, and hook it to transaction commit so it only runs once the write is durable. Never use `.path`; use the storage API (`default_storage.delete(name)`), which works for both local and remote backends. If you keep a check in `save()`, guard it with `update_fields` so counter-only saves skip it entirely.

---

### F-35 · MEDIUM · Catch-all route, no 404 page, and handles collide with real routes

`blog_frontend/src/App.jsx:29`

```jsx
<Route path="/:handle" element={<Profile />} />
```

**What's wrong:** A single-segment dynamic route at the top level, and there is no `path="*"` fallback anywhere. Any URL that does not match something more specific — a typo, a stale link, `/about` — renders the Profile page and fires a user lookup for a handle that does not exist. Users never see a 404; they see a broken profile.

The collision is the sharper half. `/write`, `/search`, `/signin`, `/signup`, `/saved`, `/drafts`, `/settings` and `/articles` all occupy the same single-segment namespace as `/:handle`. React Router v7 ranks static segments above dynamic ones, so those pages win — correct behaviour, but by the router's ranking rules rather than by your design. The consequence is that **no user can ever hold one of those handles**, and nothing in the backend reserves them (F-33). A user named "Drafts" gets the handle `drafts` and their profile is permanently shadowed by your drafts page.

There is also no error boundary anywhere in the tree, so any render exception blanks the whole application.

**Why it matters:** Putting user-controlled identifiers in the root URL namespace means every future static route you add can silently steal an existing user's profile. This is a real problem for real platforms — it is why GitHub and Twitter maintain long reserved-name lists. The design decision belongs at the start, because migrating handles later breaks every link.

**Fix:** Add a `path="*"` route rendering a proper 404. Add an error boundary around the routes. Then decide the namespace question: either prefix profiles (`/u/:handle`, which removes the collision class permanently) or keep the root namespace and enforce a reserved-word list at registration covering every current and plausible future static route. Prefixing is the more robust choice; the reserved list needs maintaining forever.

---

### F-36 · MEDIUM · Registration performs a pointless second login round trip

`blog_frontend/src/context/AuthContext.jsx:81`

```js
return await signIn(email, password);
```

**What's wrong:** After a successful registration, the frontend immediately calls `signIn`, sending the credentials again and doing a second full authentication.

It does not need to. `RegisterView` (`blog_backend/users/views.py:30-34`) already returns `access`, `refresh` and the serialised user in the registration response. The frontend reads none of it — `:70` parses the body, `:71-79` inspects it only for errors, and then the tokens are discarded and re-requested.

**Why it matters:** The backend and frontend disagree about the contract. Someone deliberately made registration return tokens so the client would not need a second call; the client was written as if it does not. Nobody noticed, because it still works — the user gets logged in, just twice as slowly.

That is the interesting part: an integration mismatch that produces correct behaviour is invisible without someone reading both sides. It also doubles the failure surface — a network blip between the two calls leaves the user with an account they appear not to be logged into.

**Fix:** Use the tokens the registration response already provides — store them and set the user directly, the same way `signIn` does at `:53-56`. Extract that token-storing logic into a shared helper so both paths use one implementation.

---

### F-37 · MEDIUM · Two inconsistent error extractors, and an unguarded JSON parse

`blog_frontend/src/context/AuthContext.jsx:47-50` and `:72-78`

```js
let errorMsg = data.detail || data.message || 'Invalid credentials.';
if (data.non_field_errors) errorMsg = data.non_field_errors.join(' ');
if (data.email) errorMsg = data.email.join(' ');
if (data.password) errorMsg = data.password.join(' ');
```

**What's wrong:** In `signIn` these are sequential `if`s, so each overwrites the last and only the final matching field is ever shown. Submit a form with both an invalid email and a weak password and the user sees only the password error, fixes it, submits again, and then discovers the email problem.

`signUp` at `:72-78` solves the identical problem with `else if` and a different field order — so the two functions have genuinely different precedence for the same API error shape. Neither is documented as intentional; they simply drifted.

Separately, `:45` calls `await res.json()` with no guard. When a proxy or load balancer returns an HTML error page, this throws, gets caught at `:58`, and the user is shown a raw JSON parse error as if it were a login failure.

**Why it matters:** DRF returns field errors as a predictable object — a map of field name to a list of messages. Handling that shape ad hoc in two places guarantees they diverge, and both discard information the API took care to provide. Displaying one error at a time when the server told you about three is a needlessly frustrating form.

**Fix:** Write one `extractErrors(data)` helper that walks the DRF error object generically and returns all field errors, and use it in both places. Render errors against their fields rather than as a single string. Guard `res.json()` by checking the content type, or wrap it and fall back to a generic message keyed on the HTTP status.

---

### F-38 · MEDIUM · Production can silently ship a bundle pointed at localhost

`blog_frontend/src/config/api.js:1-2`

```js
// Use environment variable, fallback to localhost:8000
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1/';
```

**What's wrong:** Vite inlines `import.meta.env` values at **build time**. If `VITE_API_BASE_URL` is not present in the build environment, the fallback is compiled into the bundle permanently — and the deployed site tries to reach `127.0.0.1:8000`, which resolves to the *visitor's own machine*. Every request fails with a connection error, and the build that produced it succeeded without a warning.

**Why it matters:** This is the same anti-pattern as F-02, in a different language: a convenience default that turns a missing configuration value into a silent, confusing runtime failure instead of a loud build-time one. It is worse in a frontend build, because the mistake is baked into an artifact and shipped to a CDN — you cannot fix it with an environment variable at run time, you have to rebuild.

The failure is also maximally confusing to debug: it works perfectly for the developer, whose machine really does have a server on port 8000.

**Fix:** Fail the build when the variable is missing for a production build — throw during config resolution so CI stops. Keep the localhost value in a committed `.env.development` file, where it is a development default rather than a universal fallback, and document the variable as required for deployment.

---

### F-39 · MEDIUM · Debug output ships to production, including user data

`blog_frontend/src/pages/SignUp.jsx:14`

```js
console.log(user);
```

**What's wrong:** There are **38** `console.*` calls across `blog_frontend/src`, and this one logs the entire user object — including the email address — to the browser console on the signup page. Vite does not strip `console` calls by default, so all of them are in the production bundle.

**Why it matters:** Three costs. Leftover logging is noise that makes the console useless for actual debugging. Logging user objects puts personal data somewhere you did not intend, where browser extensions and error-reporting tools can pick it up. And a console full of debug output signals to anyone who opens devtools that nobody is minding the shop.

The underlying habit is what matters: `console.log` is a debugging tool, not a logging strategy. If a message is worth keeping, it belongs in a logger you can switch off by environment; if it is not, it should be deleted when the bug is fixed.

**Fix:** Delete the debug logs, starting with this one. Keep deliberate `console.error` calls in genuine error handlers. Configure the build to drop `console` and `debugger` statements in production, and enable the lint rule that flags `console` so new ones are caught in review rather than in production.

---

### F-40 · MEDIUM · No CSS scoping at all, despite the docs claiming otherwise

`blog_frontend/src/styles/global.css:59` and `blog_frontend/src/styles/navbar.css:227` — byte-for-byte identical:

```css
.btn {
  display: inline-flex;
  align-items: center;
  ...
}
```

**What's wrong:** `blog_frontend/CLAUDE.md:3` and the README both state the project uses CSS Modules. There are **zero** `.module.css` files. All 23 stylesheets are plain global CSS, imported for side effects.

The result is one flat global namespace in which **75 class selectors are defined in more than one file** — `.btn`, `.btn-ghost`, `.article-card`, `.comment-item`, `.auth-card`, `.avatar-image` and many others. Which definition wins depends on the bundler's import order, not on anything you wrote. Above, a *navbar* stylesheet redefines the global `.btn`, restyling every button in the application.

Import hygiene compounds it: `global.css` is imported twice (`main.jsx:6` and `App.jsx:17`) and `chatbot.css` three times (`App.jsx:18`, `Chatbot.jsx:4`, `ChatbotButton.jsx:3`).

**Why it matters:** This is the specific problem CSS Modules exist to solve. Without scoping, a stylesheet is not a component's private business — it is a global mutation, and any file can silently override any other. Symptoms are the classic ones: fixing a button in one place breaks it somewhere unrelated, and the fix is another `!important`. The duplication above is worse than an override, because it is an exact copy: changing `global.css` now changes nothing, since `navbar.css` reasserts the same values afterwards.

The documentation claiming otherwise is the compounding failure — it tells the next developer their styles are scoped when they are not.

**Fix:** Rename component stylesheets to `.module.css` and import them as objects; Vite supports this with no configuration. Migrate incrementally, starting with the files that already collide. Keep genuinely global concerns — resets, design tokens in `variables.css` — as plain global CSS, imported exactly once in `main.jsx`. Then correct `CLAUDE.md` and the README to describe what the code actually does.

---

### F-41 · MEDIUM · The README documents a project that does not exist

`README.md`, project structure section:

```
├── blog_backend/               # Django REST API
│   ├── config/                 # Project settings (base, dev, prod)
│   ├── apps/                   # All Django apps
```

**What's wrong:** There is no `blog_backend/apps/` directory. The Django apps live directly under `blog_backend/`. The diagram also lists `TODO.md` and `LICENSE`, neither of which is tracked in git — while the header displays an MIT licence badge, so the project advertises a licence it does not contain. The file ends with a stray duplicate `# medium_blog_website` heading left over from repository initialisation.

Elsewhere the README claims "Full-text search" (it is `icontains` — F-23) and "Real-time alerts" for notifications (they are polled).

**Why it matters:** The README is the first thing a new contributor reads and the only artifact they have no way to check against reality yet. When it describes a directory layout that does not exist, they lose confidence in the entire document — and then stop reading the parts that were accurate.

This is the same failure as F-12 and F-40, and by now it is a pattern worth naming: **documentation written from intention rather than observation.** It describes what the project was going to be. Nothing keeps it honest afterwards.

The missing licence is a practical problem too: no `LICENSE` file means the code is under exclusive copyright by default, whatever the badge says.

**Fix:** Correct the tree to match reality, remove the entries for files that do not exist, and delete the duplicate heading. Add an actual `LICENSE` file or remove the badge. Soften "full-text search" and "real-time" to describe what is implemented. Then adopt the rule that keeps documentation true: when a change makes a document wrong, the document is part of that change.

---

### F-42 · MEDIUM · Seed data is inconsistent by construction and pathologically slow

`blog_backend/core/management/commands/populate_db.py:259` and `:13`

```py
article.claps_count = random.randint(0, 200)
...
from faker import Faker
```

**What's wrong:** Several problems in one command.

The counter is fabricated. `claps_count` is set to a random number while **no `Clap` rows are created at all**. The denormalised counter and its source table disagree from the moment the database is seeded. So `is_clapped` is false for everyone, the clap toggle behaves oddly against a fictional count, and any bug in counter maintenance is invisible because the counters were never trustworthy.

`faker` (`:13`) is a second undeclared dependency (see F-03) — the command cannot run on a clean checkout.

The whole command is wrapped in a single `@transaction.atomic` (`:101`) around thousands of writes, holding locks and accumulating memory for the entire run.

And it is full of per-iteration queries: `.exists()` checks inside nested loops at `:179`, `:274` and `:328` (roughly 3,600, 10,800 and 1,800 queries respectively); `.order_by('?')` at `:241`, a full random sort of the comments table, inside a loop; a `COUNT` per article at `:260`; and `:347` re-fetching the entire `Comment` table on every iteration.

Nothing calls `random.seed()`, so no two runs produce the same dataset.

**Why it matters:** Seed data should exercise the same code paths as production. When you write to a denormalised counter directly instead of creating the rows that produce it, you build a database in a state your application can never legitimately reach — so testing against it proves nothing about the real write path, and actively hides F-12 and F-13.

The performance issues matter less in a dev tool, but the patterns are the same ones that are wrong in request handlers, and habits transfer.

**Fix:** Create real `Clap` rows and let the counters be derived, so the seeder exercises your actual clap logic. Add `faker` to the dev requirements. Batch inserts with `bulk_create`, replace the `.exists()` loops with `get_or_create` or pre-computed sets, and drop `.order_by('?')` in favour of sampling IDs in Python. Break the single giant transaction into per-phase transactions. Call `random.seed()` with a fixed, overridable value so runs are reproducible.

---

### F-43 · MEDIUM · Dead code and dead configuration

Verified unused across the repository:

- `blog_frontend/src/pages/ArticleDetail.jsx` — imported by nothing; `App.jsx` routes `/article/:id` to `Article.jsx` instead.
- `blog_frontend/src/components/RelatedArticleCard.jsx` — imported by nothing, along with its 100-line `related-article-card.css`.
- `blog_backend/core/utils.py:16` — `validate_hex_color` is defined and never called, while `avatar_color` and `cover_color` accept any 7-character string.
- `blog_backend/users/views.py:15` — `IsOwnerOrReadOnly` imported, never used (see F-01).
- `blog_backend/chatbot/models.py` and `chatbot/admin.py` — untouched Django boilerplate.
- `blog_backend/core/management/commands/populate_db.py:7-8` — `uuid` and `datetime` imported, neither used.
- `blog_backend/articles/views.py:158` — `TagViewSet` annotates `Count('articles')` as `num_articles`, but `TagSerializer` never exposes it, so every request pays for a JOIN and GROUP BY that is discarded.
- Repository root — a 92-byte orphan `package-lock.json` naming `blog-frontend` with an empty package set, unaccompanied by any `package.json`.

**Why it matters:** Dead code is not free. Every reader has to determine whether it matters, every refactor has to consider it, and every search returns it. `ArticleDetail.jsx` and `RelatedArticleCard.jsx` are both listed in `blog_frontend/CLAUDE.md:6-7` as live components — so the documentation is actively steering people toward files that do nothing.

`validate_hex_color` is the most instructive of these. Someone identified that hex colours need validating and wrote the function, and then never connected it — so the project contains both the awareness of a problem and its unused solution. That is a wiring failure, not a knowledge gap, and it is the same shape as F-01.

**Fix:** Delete all of it — git remembers anything you need back. Wire `validate_hex_color` into the two colour fields as a validator, since that gap is real. Drop the unused annotation from `TagViewSet` or expose it in the serializer. Enable the unused-import and unused-variable lint rules on both sides so this does not re-accumulate.

---

### F-44 · MEDIUM · "Trending" means two different things

`blog_backend/articles/views.py:127` versus `blog_backend/chatbot/utils.py:113`

```py
trending_articles = self.get_queryset().filter(status='published').order_by('-view_count')[:5]
```

```py
articles = Article.objects.filter(status='published').order_by('-claps_count')[:limit]
```

**What's wrong:** The API's trending endpoint ranks by view count. The chatbot's trending tool ranks by clap count. Ask the site and ask the assistant on the same page and you get two different lists, both labelled trending.

`blog_backend/articles/CLAUDE.md:3` describes the articles app as handling "featured, trending" without defining either.

**Why it matters:** Business definitions must live in exactly one place. "Trending" is a product decision — is it views, claps, recency-weighted engagement? — and once it is implemented twice, the two copies diverge the moment anyone refines one. Here they were already born different, so nobody ever decided; two people each made a local choice.

The fix is not merely to pick one, but to make it *impossible* to have two. If both call sites are forced through one function, the definition can only be changed in one place.

**Fix:** Define trending once — a queryset method or a manager on `Article` — and have both the viewset and the chatbot tool call it. Write down what it means, and note the magic `[:5]` at `:127` should be a named constant or a query parameter rather than a hardcoded literal.

---

## Low · Craft

None of these will page you at 3am. Collectively they are what separates code that reads as professional from code that reads as a first draft, and several of them are symptoms of the larger patterns above.

### F-45 · Defensive code that defends nothing

`blog_backend/config/settings/development.py:6-16`

```py
try:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
```

Appending a string to a list cannot raise `ImportError`. The `try/except ImportError` wrapping this catches nothing — if `debug_toolbar` is genuinely absent, the failure happens later during app loading, outside this block, uncaught. The guard reads as safety and provides none. Either import the module here so the check is real, or drop the pretence.

### F-46 · Unreachable error handling

`blog_backend/users/views.py:170-174`

```py
user = super().get_object()
if user != self.request.user:
    raise PermissionDenied('You can only update your own profile.')
```

`get_queryset` at `:167-168` already restricts the queryset to `request.user`, so a mismatched handle produces a 404 from `get_object()` and this `PermissionDenied` can never fire. Harmless, but it misleads: a reader assumes it protects something. Pick one mechanism — either scope the queryset or check ownership explicitly — and delete the other.

### F-47 · HTTP 204 with a response body

`blog_backend/users/views.py:156-158`

```py
return Response(
    {'detail': f'Unfollowed @{target.handle}.'},
    status=status.HTTP_204_NO_CONTENT
)
```

204 means "no content" and the specification forbids a body. Some proxies strip it, some clients error. Use 200 if you want to return a message, or 204 with nothing.

### F-48 · Overriding `validate()` silently disabled a setting

`blog_backend/users/serializers.py:86` never calls `super().validate()`. SimpleJWT's parent implementation is what honours `UPDATE_LAST_LOGIN`, which you enabled at `base.py:133` — so `last_login` is never written, and the setting is inert. When you override a framework method, know what you are replacing; the parent usually does more than the one thing you were looking at.

### F-49 · A 200-line regex chain as the fallback brain

`blog_backend/chatbot/views.py:176-388` is a single function of sequential regex matches. Note the copy-paste artefact at `:229-230`:

```py
author_match = None
if not author_match:
```

Six more `if not author_match:` blocks follow, ending in catch-alls that swallow almost anything. This is unmaintainable and untestable in its current shape, and per F-30 it is what users actually get whenever the real path fails. If the mock is a genuine fallback, reduce it to a handful of intent handlers in a lookup table. If it is a development stand-in, gate it behind an explicit setting and stop serving it in production.

### F-50 · Bare `except:`

`blog_backend/chatbot/utils.py:136` uses a bare `except:`, which catches `KeyboardInterrupt` and `SystemExit` too — meaning this code can swallow your attempt to stop the process. Always catch `Exception` at minimum, and preferably the specific exception you expect.

### F-51 · Product copy hardcoded in Python

`blog_backend/chatbot/utils.py:168-203` embeds UI instructions ("Go to the Write page…") in backend source. It is guaranteed to drift the moment the UI changes, and `:185` already ships the phrase "(if implemented)" to end users. Move this to configuration or documentation the chatbot can read.

### F-52 · Stale hardcoded model identifier

`blog_backend/chatbot/views.py:167` pins `"claude-3-5-sonnet-20241022"` in source. Model choice is configuration: changing it should not require a code deploy. Move it to settings alongside `ANTHROPIC_API_KEY`, and check the current model list — this one is several generations behind.

### F-53 · Enum defined, strings used

`blog_backend/core/management/commands/populate_db.py:197` and `:208` use raw `'published'` / `'draft'` / `'archived'` strings even though `Article.Status` exists (`articles/models.py:22-26`) — and the same file uses an enum correctly at `:287` (`Notification.Type.FOLLOW`). The same inconsistency appears at `articles/views.py:42,51,53` and `users/views.py:78`. Enums exist so a typo is an error rather than a silently empty queryset. Use them everywhere or nowhere.

### F-54 · Comments that record confusion instead of intent

Three examples worth contrasting.

`blog_frontend/src/utils/apiClient.js:105`:

```js
// CRITICAL LINE: This must be here!
export default apiClient;
```

That is an ordinary default export. The comment records a moment of debugging panic and tells the next reader nothing true.

`blog_backend/articles/models.py:43` — `# NEW: Added primary cover image…` — git already records what is new; a comment claiming novelty is stale the day after it is written.

`blog_backend/articles/serializers.py:93` and `articles/views.py:20` both open with `FIX:` and then explain, clearly and correctly, *why* the code is shaped the way it is. **Those are good comments** — keep writing those. The difference is that they explain reasoning a reader could not recover from the code, rather than narrating history or expressing feelings about it.

### F-55 · Small hygiene

- `blog_backend/config/settings/base.py:126` places `from datetime import timedelta` in the middle of the file. Imports go at the top.
- `blog_backend/requirements/base.txt` has no trailing newline, so concatenating it with another file corrupts the last entry.
- `blog_backend/start.sh` runs `migrate` on every boot with three gunicorn workers; concurrent instance starts race on the migration lock. Run migrations as a separate release step. Its comment also describes "the ASGI-capable WSGI app" while running WSGI under sync workers — pick one and say it accurately.
- `blog_frontend/src/context/AuthContext.jsx:100` constructs a new context value object on every render, re-rendering every consumer. Memoise it.
- `AuthContext.jsx:11-28` has no cleanup or abort, so an unmount mid-request sets state on a dead component.
- `AuthContext.jsx:40` and `:65` call `fetch` directly, violating the rule stated in your own `blog_frontend/CLAUDE.md:15` ("always go through `utils/apiClient.js`, never raw `fetch`"). Defensible for pre-auth calls — but then the documented rule should say so.
- `blog_frontend/src/utils/apiClient.js` returns raw `Response` objects, leaving every caller to remember `res.ok`. Some do, some do not. Centralise error handling so callers get data or an exception.

---

## What you got right

I want this section read as carefully as the findings, because it is the evidence that the problems above are gaps in process rather than gaps in ability. These are all cited so you can see exactly what "correct" looked like when you did it.

**The one XSS-sensitive render is properly defended.** `blog_frontend/src/pages/Article.jsx:168` wraps user-authored article HTML in `DOMPurify.sanitize`, and it is the *only* `dangerouslySetInnerHTML` in the entire frontend. I went looking for stored XSS specifically, expecting to find it, and you had already handled it. Sanitising rich text is the single most commonly botched thing in a blogging platform. (The remaining gap is that sanitisation happens at render time only — nothing sanitises on write, so any other API consumer receives raw stored HTML. Worth adding server-side sanitisation as defence in depth, but the immediate risk is closed.)

**`comments/signals.py:6-19` is the textbook counter implementation.** `F()` expressions, atomic at the database level, with handlers for *both* `post_save` and `post_delete`. This is exactly right, and it is the reference the other three counter implementations in this project should be rewritten against (F-12, F-13, F-27).

**Database constraints are in the right places.** `Clap` (`articles/models.py:81`) and `Follow` (`users/models.py:67`) both carry `unique_together`. Because of those constraints, the race conditions in F-27 and F-33 produce ugly 500s instead of corrupt data. Constraints at the database layer are what makes application-level races survivable — you got the important half right.

**`FollowToggleView` (`users/views.py:104-159`) is the best-written view in the project.** It blocks self-follows, uses `get_or_create` instead of check-then-create, catches `IntegrityError` as a belt-and-braces guard, and returns a considered 409 on a duplicate with a comment explaining that the frontend uses it to resync. That is genuinely thoughtful API design. Compare it with the clap toggle (F-27), which solves the same problem badly — you already know the better pattern.

**Draft visibility is correct, and correctly explained.** `articles/views.py:32-58` gets the tricky part right: a user sees published articles plus their own drafts, and no one else's. The comment explains *why* the status check has to come first, which is precisely the kind of reasoning that is invisible in code and expensive to rediscover. The read/write serializer split at `:19-30` is likewise well reasoned and documented.

**Password handling is done properly.** `users/serializers.py:48` wires Django's `validate_password` into registration, so the validator stack at `base.py:80-85` actually runs. And `:96` returns an identical error for unknown-user and wrong-password — deliberate or not, that is the correct behaviour, and it prevents account enumeration at the login endpoint.

**Production security headers are real.** `production.py:5-12` sets HSTS with a one-year max-age plus subdomains and preload, secure session and CSRF cookies, and content-type nosniff. This is a genuinely solid hardening block — F-16 is a deployment-topology bug, not a failure of intent.

**`apiClient.js:25-27` handles `FormData` correctly** by not forcing a `Content-Type`, letting the browser set the multipart boundary. This trips up a lot of people and produces upload bugs that are miserable to diagnose.

**The project skeleton is sound.** Settings split cleanly across base/development/production. Signals registered properly through `AppConfig.ready()` in all four apps that need them. Reusable abstractions collected in `core/`. Pagination, filtering, versioning and drf-spectacular configured centrally rather than repeated per view (`base.py:105-124`). Counters correctly marked read-only on `UserSerializer` (`:19-22`). The router-ordering gotcha documented *and* respected. The four `CLAUDE.md` files, where they are accurate, are better internal documentation than most projects this size have at all.

---

## Fix in this order

1. **F-01** — add the owner permission to `ArticleViewSet`. One line. Anyone can currently delete anyone's work. Do this before you read the rest of this list.
2. **F-02** — remove the `SECRET_KEY` fallback, rotate the key. Every account is forgeable until you do.
3. **F-06 / F-14** — authenticate the chatbot and configure global throttling. Open wallet, open login.
4. **F-03 / F-04** — declare `anthropic`, fix logging. Verify by deploying from a clean checkout; until this passes you cannot ship any of the other fixes.
5. **F-07, F-08, F-09** — mass assignment, public emails, unvalidated uploads. The remaining directly exploitable issues.
6. **F-05** — start the test suite. Write the F-01 authorization test first, then tests covering F-12, F-15 and F-31 as you fix them. Everything after this point is safer once tests exist.
7. **F-15, F-31, F-12, F-10** — the things that are simply broken: the `NameError`, the two dead chatbot tools, the counter nobody updates, logout.
8. **F-11** — the hanging refresh queue. Highest user-visible impact on the frontend.
9. **F-13, F-27** — unify counter maintenance on the `comments/signals.py` pattern.
10. **F-16, F-17, F-18** — deployment correctness: proxy headers, config parsing, media storage.
11. **F-20 through F-23** — performance. Not urgent at current scale; the first thing that hurts as you grow.
12. Everything else, opportunistically. **F-41 and F-40's documentation half are ten-minute fixes** — do them next time you touch those files.

---

## Habits to change

Six findings are individual mistakes. Forty-five is a process. These are the patterns underneath them.

**1. You write correct code and then do not verify it is wired up.** `IsOwnerOrReadOnly` — written, applied to comments, imported into a third file, forgotten on articles (F-01). `validate_hex_color` — written, never called (F-43). `BLACKLIST_AFTER_ROTATION` — set, inert (F-10). `UPDATE_LAST_LOGIN` — set, overridden away (F-48). `TagViewSet`'s annotation — computed, discarded (F-43). This is the dominant pattern in this audit, and it is not a knowledge problem. Every one of these dies to running the code once and checking the result.

**2. No tests, so nothing ever asks the code a question.** F-15 is a `NameError` that has never executed. F-31 is a feature that cannot work. F-12 is a counter that is never incremented. All three shipped. This is habit 1's root cause: you have no mechanism that tells you when something you wrote is not connected to anything.

**3. Defaults that hide failure instead of exposing it.** `SECRET_KEY` falling back to a published string (F-02). `''.split(',')` producing `['']` (F-17). `VITE_API_BASE_URL` falling back to localhost in a production bundle (F-38). Silent mock mode when the API key is missing (F-30). Every one trades a loud failure you would fix in a minute for a silent one you might never find. **Make missing configuration crash.** Convenience defaults belong on things that are genuinely optional, never on credentials or endpoints.

**4. Catching exceptions to make problems disappear.** `except Exception` returning a fake answer (F-30). `except Exception` leaking `str(e)` to clients (F-10). A bare `except:` (F-50). A `try/except` that cannot catch anything (F-45). Catch what you can *handle*; let everything else reach your error reporting. An error you swallowed is an error you will debug later with no information.

**5. The same problem solved differently in different places.** Counters maintained four ways (F-12). Two definitions of trending (F-44). Two different error extractors in one file (F-37). Status as an enum in one place and a string in another (F-53). Each local choice was reasonable; collectively they mean no reader can learn how this codebase does anything, because it does everything several ways. When you solve a problem twice, extract it.

**6. Documentation written from intention rather than observation.** CSS Modules that do not exist (F-40). An `apps/` directory that does not exist (F-41). Signals maintaining a counter they do not maintain (F-12). Components documented as live that nothing imports (F-43). Docs that lie are worse than no docs, because they stop people looking. When a change makes a document wrong, the document is part of that change.

---

The architecture here is better than the execution, which is the good version of this problem — bad structure is expensive to fix, and discipline is a habit you can build starting with the next commit. Fix F-01 today. Then write the test that proves it stays fixed, and you will have addressed the root cause of most of this document.
