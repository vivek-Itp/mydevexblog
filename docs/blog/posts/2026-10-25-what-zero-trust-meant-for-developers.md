---
title: "What zero trust actually meant for our developers"
description: Zero trust is not a product you buy. It is the sum of the controls you can name, and each one costs a developer something specific.
date:
  created: 2026-10-25
authors:
  - vivek
categories:
  - Developer Experience
tags:
  - zero-trust
  - security
  - devex
  - platform-engineering
slug: what-zero-trust-meant-for-developers
---

I have written about signed commits, artifact signing, restricted runners and moving a firewall off the application server. Those were separate posts because they were separate pieces of work. They were also, all of them, the same programme: a zero-trust policy on a high-criticality application, arriving one control at a time.

<!-- more -->

Nobody ever handed us a thing called zero trust. What we got was a sequence of specific requirements, each defensible on its own, and the phrase came afterwards to describe the shape they made. This post is that shape, and what each piece of it costs the person trying to get work done.

## What it actually consisted of

| Control | What it stops assuming | What it costs a developer |
|---|---|---|
| Signed commits, verified in the pipeline | That a commit's author field is true | Key management, and broken verification after a rebase |
| Artifact signing with a KMS key | That a binary came from the build that claims it | No local signing path, ever |
| Restricted runner sets | That any build may reach any secret | Builds land where the tags send them, not where you choose |
| Guarded pipeline configuration | That a project may define its own controls | Those teams wait on the platform team |
| Restricted subnet behind a network firewall | That being on the network means anything | Firewall changes leave the team that needs them |

Read that right-hand column as a whole and you have the honest version of the developer experience under zero trust. Not one hard thing. Five small ones, all the time.

## 1. Identity on every commit, not on the login

The first piece was SSH-signed commits, with the public keys held in parameter store and the pipeline verifying each new commit against the author's registered key. Branch protection required a signature; the pipeline checked it on the merge request and again on promotion, over the full range since the last merge.

The assumption being removed is that the author field in a commit means anything. It does not — it is a string you set yourself.

!!! example "What broke, and what it cost"

    Everything that touches history broke at least once. Rebases produced commits whose signatures no longer matched. Bots committed without signing. Key rotation invalidated anything signed with the old key. New laptops meant new keys and a sudden run of verification failures for someone who had done nothing unusual.

    The fixes were unglamorous: force push on feature branches, hold old and new keys in the store together, and an enforcement date so commits from before the cutoff are ignored rather than retroactively failed.

    The cost to a developer is not any single one of those. It is that a class of failure now exists which has nothing to do with their code, and when it hits they cannot tell from the error whether they have done something wrong.

## 2. Only the build can act

The second piece was artifact signing: the runner signs the JAR with a KMS key on publish, the container image is signed too, and the deploy step refuses anything that does not verify. Access to the key is restricted to the runner's role. No developer has it and there is no break-glass path that puts it on a laptop.

That restriction is the whole security property. If a person can sign, a signature stops meaning "this came from the build".

!!! example "The request I keep turning down"

    The recurring ask is for a way to sign locally, and it is always reasonable in the moment: a release is blocked, the pipeline is red for an unrelated reason, the artifact is fine.

    Saying no is the job, because a signature that might have come from a person in a hurry is not worth the pipeline minutes it costs. But the honest version is that every time I say it, the pipeline's speed becomes a security property. If getting a green build takes long enough, the pressure to build a bypass comes back, and eventually someone builds one.

## 3. Nothing is trusted for being on the network

The third piece moved the application instances into a restricted subnet behind a network firewall, with a load balancer in front, and retired the host firewall that had been configured by connecting to the box. The allow rules are scoped to a specific region on a specific port, with individual entries for known sources.

The assumption removed here is the oldest one in infrastructure: that traffic which has arrived is traffic that belongs.

!!! example "Where the cost lands"

    A host firewall could be changed by anyone with a shell on the host. That was the security problem and, from a developer's point of view, it was also the convenience: a rule change took minutes and needed nobody's agreement.

    Now the rules are infrastructure. They are reviewable, auditable and versioned, which is strictly better — and they are no longer the application team's to change. *The developer-experience read here is mine rather than something I have measured:* that trade is only survivable if the common change stays fast. A control that is correct and slow becomes the thing people design around.

## 4. A project cannot weaken its own controls

The fourth piece was guarded pipeline configuration for a short list of critical projects: runner tags, signing and verification are fixed centrally, and the project cannot override them from its own file.

The assumption removed is that a team may define the controls that apply to itself. The argument is simple — if a team can switch off the check that protects them, the check is a suggestion — and the cost is just as simple: those teams wait on us for changes other teams make themselves.

We keep the list short for exactly that reason. Every project added is a permanent promise to be responsive to that team.

!!! example "The failure that justified it"

    A build was failing on the verification step, and the quickest path to green — the one anybody under pressure reaches for — was to comment the step out and come back to it later.

    On a guarded project that does nothing, because the step does not come from the project's file. The team asked us instead, and the cause turned out to be a stale key reference that took minutes to fix. Being unable to bypass the check is what got the right people looking at it the same day.

## 5. The costs add up in a way no single review catches

Each control above was reviewed on its own and each one is defensible on its own. Nobody ever reviewed the total.

*This section is my reading rather than a measured finding.* A developer on that application does not experience five controls. They experience a day with more steps in it than a developer on an ordinary application, and a larger set of failures that are nobody's fault and still theirs to resolve. The signed-commit failure after a new laptop. The build that queues because the runner it is pinned to is busy. The firewall rule that needs a conversation. The config they cannot change.

The thing I would do differently is measure that total. Time from push to a merge signal, re-run rate, how long a routine access or rule change takes end to end — on the zero-trust application and on an ordinary one, side by side. Without that comparison, every individual control looks cheap, because the cost of each is small and the cost of all of them is invisible.

## 6. What is still unresolved

Two things, and neither is cryptographic.

The first is knowing exactly which commits a pipeline run is responsible for. A first push gives an all-zero before-reference, so there is nothing to compare against, and a branch taken from another branch makes the range either too wide — blocking someone with history they did not write — or too narrow, which lets unverified commits reach a protected branch on a green pipeline. We compare against the mainline and accept that the branch-from-branch case is one we get wrong.

The second is concurrency on the runners. Set the limits high and a busy afternoon has heavy builds fighting over the same hosts. Set them low and jobs queue while capacity sits idle. Developers experience both as "the pipeline is slow", and we have not found the setting that is right at both ten in the morning and four in the afternoon.

## Takeaways

- **Zero trust is not a product.** It is the list of assumptions you have stopped making, and you should be able to name every one.
- **Each control removes one assumption and adds one cost.** Write both down. The right-hand column is the developer experience.
- **The pipeline's speed becomes a security property** once there is no manual path. A slow build is pressure to build a bypass.
- **Keep the centrally-guarded list short**, because every entry is a permanent promise of responsiveness to that team.
- **Measure the total, not each control.** Individually they all look cheap. Nobody reviews the sum.

What I have not solved is the governance version of the same problem: every control was approved by someone, and no single person was ever asked whether the whole set was worth it. I do not know what that review would look like, or who would be in the room, but the absence of it is why the costs only become visible from the developer's chair.
